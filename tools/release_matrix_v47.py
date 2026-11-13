#!/usr/bin/env python3
"""V4.7 bounded, isolated, auditable TEST-ONLY release matrix.

Runs only enumerated test modules from this trusted toolkit. No arbitrary project
scripts or shell. Every module runs in a separate Python interpreter to avoid
leaking state across suites. This is a runner, NOT a sandbox.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARDS = {
    'core': ('test_agent_bridge', 'test_loop', 'test_loop_cli', 'test_orchestrator',
             'test_v21', 'test_workflow', 'test_workflow_demo'),
    'analysis': ('test_v33', 'test_v34', 'test_v35', 'test_v36', 'test_v37',
                 'test_v38', 'test_v39'),
    'platform': ('test_v40', 'test_v41', 'test_v42'),
    'collaboration': ('test_v43', 'test_v44', 'test_v45', 'test_v46', 'test_v47', 'test_v48', 'test_v49', 'test_v50'),
}
MAX_OUTPUT = 1000
COUNTS = re.compile(r'Ran\s+(\d+)\s+tests?')


def listed_modules(shard: str) -> tuple[str, ...]:
    if shard == 'all':
        return tuple(n for group in SHARDS.values() for n in group)
    if shard not in SHARDS:
        raise ValueError('unknown shard')
    return SHARDS[shard]


def validate_matrix() -> None:
    names = listed_modules('all')
    if len(names) != len(set(names)):
        raise ValueError('duplicate test module in release matrix')
    existing = {p.stem for p in (ROOT / 'tests').glob('test_*.py')}
    if set(names) != existing:
        raise ValueError('release matrix does not match test modules: missing=' +
                         str(sorted(existing - set(names))) + ', unknown=' +
                         str(sorted(set(names) - existing)))


def _terminate_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == 'posix':
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        # On Windows, taskkill is best effort. No claim of secure sandboxing.
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                           capture_output=True, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
    proc.wait(timeout=6)


def _execute(name: str, timeout: float) -> dict:
    script = ROOT / 'tests' / (name + '.py')
    cmd = [sys.executable, '-m', 'unittest', 'tests.' + name, '-q']
    row = {'module': name, 'source_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
           'status': 'planned', 'tests_reported': None}
    # Limit inherited environment to avoid unintended injected Python modules.
    env = {k: v for k, v in os.environ.items()
           if k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'HOME', 'TMP', 'TEMP', 'TMPDIR',
                    'LANG', 'LC_ALL', 'USERPROFILE')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    start = time.monotonic()
    try:
        args = dict(cwd=ROOT, env=env, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, errors='replace')
        if os.name == 'posix':
            args['start_new_session'] = True
        elif os.name == 'nt':
            args['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(cmd, **args)
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_tree(proc)
            out, err = proc.communicate()
            row.update(status='timeout', reason='module exceeded execution budget')
        else:
            row['status'] = 'passed' if proc.returncode == 0 else 'failed'
            row['exit_code'] = proc.returncode
        match = COUNTS.search(err + '\n' + out)
        if match:
            row['tests_reported'] = int(match.group(1))
        if row['status'] != 'passed':
            row['diagnostic_tail'] = (err or out)[-MAX_OUTPUT:]
    except OSError as exc:
        row.update(status='failed', reason='could not start test interpreter: ' + type(exc).__name__)
    row['elapsed_seconds'] = round(time.monotonic() - start, 3)
    return row


def run_matrix(shard='all', *, execute=False, max_total_seconds=600.0,
               module_timeout_seconds=90.0) -> dict:
    validate_matrix()
    if not (1 <= max_total_seconds <= 3600):
        raise ValueError('total time budget must be within 1..3600 seconds')
    if not (1 <= module_timeout_seconds <= 600):
        raise ValueError('module timeout must be within 1..600 seconds')
    modules = listed_modules(shard)
    started = time.monotonic()
    rows = []
    for name in modules:
        elapsed = time.monotonic() - started
        available = max_total_seconds - elapsed
        if not execute:
            rows.append({'module': name, 'status': 'planned'})
        elif available < 1:
            rows.append({'module': name, 'status': 'not_run', 'reason': 'total budget exhausted'})
        else:
            rows.append(_execute(name, min(module_timeout_seconds, available)))
    summary = {status: sum(r['status'] == status for r in rows)
               for status in ('passed', 'failed', 'timeout', 'not_run', 'planned')}
    return {'schema_version': 1, 'toolkit_version': '5.0', 'shard': shard,
            'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
            'actually_executed': bool(execute),
            'modules': rows, 'summary': summary,
            'tests_reported': sum(r.get('tests_reported') or 0 for r in rows),
            'elapsed_seconds': round(time.monotonic() - started, 3),
            'note': 'Trusted bundled tests only. These are NOT sandboxed. '
                    'Failed, timed-out or unrun modules never count as passed.'}


def validate_output(output: Path) -> None:
    folder = ROOT / 'benchmarks' / 'reports'
    if (ROOT / 'benchmarks').is_symlink() or folder.is_symlink():
        raise ValueError('unsafe report directory (symlink)')
    if folder.exists() and not folder.is_dir():
        raise ValueError('unsafe report directory (not directory)')
    output = output.absolute()
    if (output.parent != folder.resolve() or not re.fullmatch(r'[a-zA-Z0-9_\-]{1,70}\.json', output.name)
            or output.is_symlink()):
        raise ValueError('report must be a new .json path directly under benchmarks/reports')
    if output.exists():
        raise ValueError('refusing to overwrite an existing release report')


def save(result: dict, output: Path) -> None:
    validate_output(output)
    folder = ROOT / 'benchmarks' / 'reports'
    folder.mkdir(parents=True, exist_ok=True)
    output = output.absolute()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(output, flags, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
        fh.flush()
        os.fsync(fh.fileno())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shard', choices=(*SHARDS, 'all'), default='all')
    p.add_argument('--execute', action='store_true', help='explicitly execute trusted bundled tests')
    p.add_argument('--module-timeout', type=float, default=90)
    p.add_argument('--max-total-seconds', type=float, default=600)
    p.add_argument('--output', type=Path, help='write a new JSON report in benchmarks/reports/')
    a = p.parse_args()
    if a.output and not a.execute:
        p.error('--output requires --execute')
    try:
        if a.output:
            validate_output(a.output)
        result = run_matrix(a.shard, execute=a.execute,
                            max_total_seconds=a.max_total_seconds,
                            module_timeout_seconds=a.module_timeout)
        if a.output:
            save(result, a.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not a.execute or result['summary']['passed'] == len(result['modules']) else 1
    except (OSError, ValueError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
