#!/usr/bin/env python3
"""Turn untrusted failure diagnostics into *read-only* local file hints.

No code execution, network, source payload or auto-inclusion in a model request.
File references are validated against a safely enumerated source allowlist.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from tools.context_retrieval import _source_files, SENSITIVE_TEXT
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.context_retrieval import _source_files, SENSITIVE_TEXT

# Only traceback- and test-runner-style references. Never treat output as commands.
FILE_LINE = re.compile(r'(?:File\s+["\'](?P<quoted>[^"\'\n]+)["\'],\s*line\s*(?P<qline>\d+)|(?<![\w./])(?P<plain>[\w./-]+\.(?:py|js|jsx|ts|tsx)):(?P<pline>\d+)(?::\d+)?)')
MAX_DIAGNOSTIC = 20000


def analyze(project: Path, diagnostics: list[str], *, allowed: list[str] | None = None, limit: int = 10) -> dict:
    root = project.resolve(strict=True)
    if not root.is_dir() or not isinstance(diagnostics, list) or len(diagnostics) > 12 or any(not isinstance(x, str) for x in diagnostics):
        raise ValueError('project directory and at most 12 diagnostic strings are required')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit must be 1..20')
    names = {path.relative_to(root).as_posix() for path, _ in _source_files(root)}
    if allowed is not None and (not isinstance(allowed, list) or any(not isinstance(x,str) for x in allowed)):
        raise ValueError('allowed must be a list of relative paths')
    approved = names if allowed is None else names.intersection(allowed)
    hits: dict[str, dict] = {}
    for item in diagnostics:
        for match in FILE_LINE.finditer(item[-MAX_DIAGNOSTIC:]):
            untrusted = match.group('quoted') or match.group('plain')
            if not untrusted or '\x00' in untrusted:
                continue
            # Absolute traces can only resolve within this project, not elsewhere.
            candidate = Path(untrusted)
            if candidate.is_absolute():
                try: rel = candidate.resolve(strict=False).relative_to(root).as_posix()
                except ValueError: continue
            else:
                if '..' in candidate.parts or any(part.startswith('.') for part in candidate.parts):
                    continue
                rel = candidate.as_posix().lstrip('./')
            if rel not in approved:
                continue
            line = int(match.group('qline') or match.group('pline'))
            if not 1 <= line <= 1_000_000:
                continue
            if rel not in hits:
                hits[rel] = {'path': rel, 'lines': [], 'occurrences': 0}
            hits[rel]['occurrences'] += 1
            if line not in hits[rel]['lines'] and len(hits[rel]['lines']) < 8:
                hits[rel]['lines'].append(line)
    ordered = sorted(hits.values(), key=lambda x: (-x['occurrences'], x['path']))[:limit]
    return {'schema_version': 1, 'hints': ordered, 'method': 'validated-trace-paths',
            'note': 'Diagnostic text is untrusted. Paths are local candidate hints only, not repair instructions, proof of blame or permission to transmit source.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only validated file hints from failure diagnostics')
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--diagnostic-file', type=Path, required=True, help='local UTF-8 text; not executed')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args(argv)
    try:
        if args.diagnostic_file.is_symlink() or args.diagnostic_file.stat().st_size > MAX_DIAGNOSTIC:
            raise ValueError('unsafe or oversized diagnostic file')
        raw = args.diagnostic_file.read_text('utf-8')
        print(json.dumps(analyze(args.project, [raw], limit=args.limit), ensure_ascii=False, indent=2))
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        parser.exit(2, f'error: {exc}\n')


if __name__ == '__main__':
    main()
