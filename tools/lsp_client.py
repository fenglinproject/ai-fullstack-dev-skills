#!/usr/bin/env python3
"""Opt-in local LSP JSON-RPC 2.0 stdio client (V3.9).

NO sandbox: launching a language server is executing a third-party program.
No shell, no package installation, no automatic discovery, no network API calls.
User must explicitly approve a trusted absolute executable with --allow-start.
Workspace/symbol and textDocument/definition are read-only LSP requests.
Only project-indexed source locations are returned; no source text is printed.
"""
from __future__ import annotations
import argparse
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    from tools.incremental_index import _candidates
    from tools.lsp_import import _relative
    from tools.context_retrieval import SKIP_DIRS, SENSITIVE_NAMES, SENSITIVE_TEXT
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import _candidates
    from tools.lsp_import import _relative
    from tools.context_retrieval import SKIP_DIRS, SENSITIVE_NAMES, SENSITIVE_TEXT

MAX_MESSAGE = 2 * 1024 * 1024
MAX_HEADER = 8192
MAX_EVENTS = 150
C_FAMILY = {'.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.hxx'}
SAFE_ENV = ('PATH', 'HOME', 'USERPROFILE', 'SYSTEMROOT', 'WINDIR', 'TMP', 'TEMP', 'TMPDIR', 'LANG', 'LC_ALL')


def _validate_command(command: list[str]) -> list[str]:
    if not isinstance(command, list) or not command or len(command) > 16:
        raise ValueError('explicit server executable and up to 15 arguments required')
    for arg in command:
        if not isinstance(arg, str) or not arg or '\0' in arg or len(arg) > 4096:
            raise ValueError('invalid server argument')
    binary = Path(command[0])
    if not binary.is_absolute() or not binary.is_file():
        raise ValueError('server must be an existing absolute executable path')
    return command


def _read_one(stream):
    """Framed LSP reader. All input sizes are bounded before allocation."""
    total = 0
    size = None
    while True:
        line = stream.readline(MAX_HEADER - total + 1)
        total += len(line)
        if not line or total > MAX_HEADER:
            raise ValueError('oversized, truncated or missing LSP header')
        if line == b'\r\n':
            break
        if not line.endswith(b'\r\n'):
            raise ValueError('invalid LSP line ending')
        if line.lower().startswith(b'content-length:'):
            value = line.split(b':', 1)[1].strip()
            if size is not None or not re.fullmatch(rb'[0-9]{1,8}', value):
                raise ValueError('invalid content-length')
            size = int(value)
    if size is None or not 1 <= size <= MAX_MESSAGE:
        raise ValueError('missing or oversized LSP message')
    body = stream.read(size)
    if len(body) != size:
        raise ValueError('truncated LSP body')
    try:
        obj = json.loads(body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError('invalid LSP JSON') from e
    if not isinstance(obj, dict):
        raise ValueError('LSP message must be object')
    return obj


def _extra_language_files(root: Path) -> set[str]:
    """Bounded, symlink-avoiding C/C++ candidates for local LSP ONLY.

    The existing AST index stays Python/JS/TS only. No binary, overlarge,
    symlinked or obvious credential-bearing content is exposed to a server.
    """
    allowed=set()
    size_total=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')
                 and not (Path(parent)/d).is_symlink()]
        for name in files:
            path=Path(parent)/name
            if (path.suffix.lower() not in C_FAMILY or path.is_symlink()
                    or SENSITIVE_NAMES.search(name) or not path.is_file()):
                continue
            size=path.stat().st_size
            if size<1 or size>256*1024:continue
            size_total+=size
            if size_total>12*1024*1024 or len(allowed)>=1500:
                raise ValueError('LSP C-family source discovery resource cap exceeded')
            raw=path.read_bytes()
            if b'\x00' in raw:continue
            try:source=raw.decode('utf-8')
            except UnicodeDecodeError:continue
            if SENSITIVE_TEXT.search(source):continue
            allowed.add(path.relative_to(root).as_posix())
    return allowed


class LSPClient:
    def __init__(self, project: Path, command: list[str], *, timeout: float = 8.0):
        self.root = project.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError('project must be a directory')
        self.command = _validate_command(command)
        if not 0.1 <= timeout <= 60:
            raise ValueError('timeout must be 0.1..60 seconds')
        self.timeout = timeout
        self.proc = None
        self.inbox = queue.Queue(maxsize=MAX_EVENTS + 2)
        self.id = 0
        self.allowed = {rel for rel, _sha, _source in _candidates(self.root)} | _extra_language_files(self.root)

    def __enter__(self):
        env = {key: value for key in SAFE_ENV if (value := os.environ.get(key)) is not None}
        self.proc = subprocess.Popen(self.command, cwd=self.root, env=env,
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                 start_new_session=(os.name != 'nt'))
        threading.Thread(target=self._reader, daemon=True).start()
        self.request('initialize', {
            'processId': os.getpid(), 'rootUri': self.root.as_uri(),
            'workspaceFolders': [{'uri': self.root.as_uri(), 'name': self.root.name}],
            'capabilities': {'textDocument': {'synchronization': {'didSave': False}}}, 'clientInfo': {'name': 'ai-fullstack-skills', 'version': '4.0'}
        })
        self.notify('initialized', {})
        return self

    def _reader(self):
        try:
            while True:
                item = _read_one(self.proc.stdout)
                try:
                    self.inbox.put(item, timeout=.1)
                except queue.Full:
                    raise ValueError('too many server events')
        except Exception as exc:
            try:
                self.inbox.put({'_fatal': str(exc)}, timeout=.1)
            except queue.Full:
                pass

    def _send(self, message: dict):
        data = json.dumps(message, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        if len(data) > MAX_MESSAGE:
            raise ValueError('outgoing LSP payload too large')
        if self.proc.poll() is not None:
            raise RuntimeError('language server exited')
        self.proc.stdin.write(b'Content-Length: ' + str(len(data)).encode('ascii') + b'\r\n\r\n' + data)
        self.proc.stdin.flush()

    def notify(self, method: str, params: dict):
        self._send({'jsonrpc': '2.0', 'method': method, 'params': params})

    def request(self, method: str, params: dict):
        self.id += 1
        request_id = self.id
        self._send({'jsonrpc': '2.0', 'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + self.timeout
        for _ in range(MAX_EVENTS):
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError('LSP request timed out')
            try:
                msg = self.inbox.get(timeout=left)
            except queue.Empty:
                raise TimeoutError('LSP request timed out') from None
            if '_fatal' in msg:
                raise RuntimeError('language server transport error: ' + msg['_fatal'])
            if msg.get('id') == request_id:
                if 'error' in msg:
                    raise RuntimeError('language server returned an error')
                return msg.get('result')
            if 'method' in msg and 'id' in msg:
                # Server-initiated requests are NOT authorized or executed.
                self._send({'jsonrpc': '2.0', 'id': msg['id'],
                            'error': {'code': -32601, 'message': 'client operation unsupported'}})
        raise RuntimeError('LSP event limit exceeded')

    def locations(self, response, *, query: str | None = None, limit: int = 20):
        if not isinstance(response, list):
            return {'matches': [], 'rejected': 0, 'warning': 'unsupported-or-empty-lsp-response'}
        matches = []
        rejected = 0
        for row in response[:1000]:
            if not isinstance(row, dict):
                rejected += 1
                continue
            loc = row.get('location', row)
            if not isinstance(loc, dict):
                rejected += 1
                continue
            uri = loc.get('uri', loc.get('targetUri'))
            range_value = loc.get('range', loc.get('targetSelectionRange', {}))
            start = range_value.get('start') if isinstance(range_value, dict) else None
            line = start.get('line') if isinstance(start, dict) else None
            name = row.get('name')
            if (not isinstance(uri, str) or not isinstance(line, int) or isinstance(line, bool)
                    or not 0 <= line <= 10_000_000 or (name is not None and not isinstance(name, str))):
                rejected += 1
                continue
            rel = _relative(self.root, uri)
            if rel not in self.allowed:
                rejected += 1
                continue
            if query and name is not None and query.casefold() not in name.casefold():
                continue
            matches.append({'name': name or '', 'path': rel, 'line': line + 1,
                            'source': 'live-lsp-candidate'})
            if len(matches) >= limit:
                break
        if len(response) > 1000:
            rejected += len(response) - 1000
        return {'matches': matches, 'rejected': rejected,
                'warning': 'language server results are untrusted candidates; not proof of correctness'}

    def workspace_symbols(self, query: str, limit: int = 20):
        if not isinstance(query, str) or not 1 <= len(query) <= 200 or not 1 <= limit <= 100:
            raise ValueError('invalid query/limit')
        return self.locations(self.request('workspace/symbol', {'query': query}), query=query, limit=limit)

    def definition(self, rel: str, line: int, character: int, limit: int = 20):
        if rel not in self.allowed or not isinstance(line, int) or not isinstance(character, int) or not 0 <= line <= 10_000_000 or not 0 <= character <= 100_000 or not 1 <= limit <= 100:
            raise ValueError('file must be indexed and position must be nonnegative')
        file_path = self.root / rel
        if file_path.is_symlink() or not file_path.is_file() or file_path.stat().st_size > 256*1024:
            raise ValueError('LSP document must be a safe indexed source file')
        source = file_path.read_text(encoding='utf-8')
        if SENSITIVE_TEXT.search(source):
            raise ValueError('LSP document contains potential secret text')
        file_uri = file_path.as_uri()
        languages={'.py':'python','.c':'c','.cc':'cpp','.cpp':'cpp','.cxx':'cpp',
                   '.h':'cpp','.hh':'cpp','.hpp':'cpp','.hxx':'cpp',
                   '.ts':'typescript','.tsx':'typescriptreact','.js':'javascript','.jsx':'javascriptreact'}
        # Real LSP servers commonly require didOpen before definition queries.
        self.notify('textDocument/didOpen', {'textDocument': {
            'uri':file_uri,'languageId':languages.get(file_path.suffix.lower(),'plaintext'),
            'version':1,'text':source}})
        result = self.request('textDocument/definition', {'textDocument': {'uri': file_uri}, 'position': {'line': line, 'character': character}})
        if isinstance(result, dict):
            result = [result]
        return self.locations(result, limit=limit)

    def __exit__(self, exc_type, exc, tb):
        if self.proc is None:
            return
        try:
            if self.proc.poll() is None and exc_type is None:
                self.request('shutdown', {})
                self.notify('exit', {})
                self.proc.wait(timeout=min(2.0, self.timeout))
        except (OSError, TimeoutError, RuntimeError, ValueError, subprocess.TimeoutExpired):
            pass
        finally:
            if self.proc.poll() is None:
                if os.name != 'nt':
                    try:
                        os.killpg(self.proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    self.proc.kill()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
            if self.proc.stdin:
                self.proc.stdin.close()
            if self.proc.stdout:
                self.proc.stdout.close()


def main(argv=None):
    p = argparse.ArgumentParser(description='Explicitly start a trusted local language server; NO sandbox or auto startup')
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--server', required=True, help='absolute path to trusted language server executable')
    p.add_argument('--server-arg', action='append', default=[], help='additional argument to local server')
    p.add_argument('--allow-start', action='store_true', help='required: local server can execute project configuration and access files/network')
    p.add_argument('--query', help='workspace symbol query')
    p.add_argument('--definition', help='indexed source relative path')
    p.add_argument('--line', type=int, default=0, help='0-based LSP line')
    p.add_argument('--character', type=int, default=0, help='0-based UTF-16 character')
    p.add_argument('--timeout', type=float, default=8)
    args = p.parse_args(argv)
    if not args.allow_start:
        p.error('language server startup requires explicit --allow-start')
    if (args.query is None) == (args.definition is None):
        p.error('choose exactly one of --query and --definition')
    try:
        with LSPClient(args.project, [args.server, *args.server_arg], timeout=args.timeout) as client:
            result = client.workspace_symbols(args.query) if args.query is not None else client.definition(args.definition, args.line, args.character)
        print(json.dumps({'schema_version': 1, **result,
              'note': 'Local server executed with explicit permission; NOT sandboxed. No tests or model calls.'}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError, TimeoutError) as e:
        p.exit(2, 'error: ' + str(e) + '\n')


if __name__ == '__main__':
    main()
