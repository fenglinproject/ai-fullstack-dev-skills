#!/usr/bin/env python3
"""V4.8 explicit CI suite runner and fail-closed, cross-platform evidence collector.

Local JSON is unsigned self-reported data, NOT independent GitHub attestation.
Only the GitHub Actions download-artifact context links artifacts to a run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SUITES = ('smoke', 'core', 'analysis', 'platform', 'collaboration', 'locks')
PLATFORMS = ('linux', 'windows', 'macos')
REQUIRED = {(s, 'linux') for s in SUITES} | {('locks', 'windows'), ('locks', 'macos')}
HEX_SHA = re.compile(r'^[a-f0-9]{40}$')
SAFE_NUMBER = re.compile(r'^[1-9][0-9]{0,18}$')
MAX_EVIDENCE_BYTES = 350_000


def current_platform() -> str:
    name = platform.system()
    return {'Linux':'linux', 'Windows':'windows', 'Darwin':'macos'}.get(name, 'unsupported')


def canonical(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def context_from_environment() -> dict:
    sha = os.getenv('GITHUB_SHA', '').lower()
    run = os.getenv('GITHUB_RUN_ID', '')
    attempt = os.getenv('GITHUB_RUN_ATTEMPT', '')
    origin = 'github-actions' if os.getenv('GITHUB_ACTIONS') == 'true' else 'local'
    if origin == 'github-actions':
        if not HEX_SHA.fullmatch(sha) or not SAFE_NUMBER.fullmatch(run) or not SAFE_NUMBER.fullmatch(attempt):
            raise ValueError('invalid GitHub Actions run context')
        runner = os.getenv('RUNNER_OS', '').lower()
        if {'linux':'linux','windows':'windows','macos':'macos'}.get(runner) != current_platform():
            raise ValueError('RUNNER_OS does not match actual operating system')
    else:
        sha, run, attempt = 'unverified-local', 'unverified-local', 'unverified-local'
    return {'origin':origin, 'commit_sha':sha, 'run_id':run, 'attempt':attempt}


def run_suite(suite: str, *, execute: bool, context: dict | None = None) -> dict:
    if suite not in SUITES:
        raise ValueError('unknown fixed CI suite')
    system = current_platform()
    if system not in PLATFORMS:
        raise ValueError('unsupported platform')
    if system != 'linux' and suite != 'locks':
        raise ValueError('only locks suite is supported on non-Linux runners')
    ctx = context if context is not None else context_from_environment()
    started = time.monotonic()
    result = {'schema_version':1, 'toolkit_version':'4.8', 'suite':suite,
              'platform':system, 'executed':False, 'status':'planned',
              'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(), **ctx}
    if not execute:
        return result
    if suite in ('core', 'analysis', 'platform', 'collaboration'):
        from tools.release_matrix_v47 import run_matrix
        raw = run_matrix(suite, execute=True, max_total_seconds=630.0,
                         module_timeout_seconds=90.0)
        passed = (raw['actually_executed'] and raw['summary']['passed'] == len(raw['modules'])
                  and all(x['status'] == 'passed' and x.get('tests_reported', 0) > 0
                          for x in raw['modules']))
        count = raw['tests_reported']
    elif suite == 'smoke':
        from tools.release_gate import verify
        raw = verify(profile='smoke', execute=True)
        passed = (raw['actually_executed'] and raw['summary']['passed'] == len(raw['steps'])
                  and not raw['summary']['skipped'])
        count = len(raw['steps'])
    else:
        commands = [
            [sys.executable, '-m', 'unittest', 'tests.test_v45', 'tests.test_v46', 'tests.test_v47', '-q'],
            [sys.executable, 'tools/fault_injection_v47.py', '--execute'],
        ]
        steps = []
        for cmd in commands:
            try:
                cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                                    timeout=150, check=False, errors='replace')
                steps.append({'name':'unittest' if '-m' in cmd else 'fault-injection',
                              'status':'passed' if cp.returncode == 0 else 'failed',
                              'exit_code':cp.returncode,
                              'diagnostic_tail':(cp.stderr or cp.stdout)[-600:] if cp.returncode else ''})
            except (subprocess.TimeoutExpired, OSError) as ex:
                steps.append({'name':'unittest' if '-m' in cmd else 'fault-injection',
                              'status':'failed', 'reason':type(ex).__name__})
        raw = {'schema_version':1, 'steps':steps, 'executed':True}
        passed = len(steps) == 2 and all(s['status'] == 'passed' for s in steps)
        count = len(steps) if passed else sum(s['status'] == 'passed' for s in steps)
    result.update(executed=True, status='passed' if passed else 'failed',
                  checks_count=count, elapsed_seconds=round(time.monotonic()-started, 3),
                  details=raw, details_sha256=hashlib.sha256(canonical(raw)).hexdigest())
    return result


def _safe_evidence_file(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_EVIDENCE_BYTES:
        raise ValueError('invalid or oversized evidence file')
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('evidence directory uses a symbolic link')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_evidence(record: dict, *, sha: str, run_id: str, attempt: str,
                      require_ci: bool = True) -> tuple[str, str]:
    if not isinstance(record, dict) or set(record) != {
        'schema_version','toolkit_version','suite','platform','executed','status',
        'timestamp','origin','commit_sha','run_id','attempt','checks_count',
        'elapsed_seconds','details','details_sha256'}:
        raise ValueError('invalid evidence schema')
    suite, system = record['suite'], record['platform']
    if (suite, system) not in REQUIRED:
        raise ValueError('unexpected platform/suite combination')
    if (record['schema_version'] != 1 or record['toolkit_version'] != '4.8'
            or record['origin'] != ('github-actions' if require_ci else 'local')
            or record['commit_sha'] != sha or record['run_id'] != run_id
            or record['attempt'] != attempt):
        raise ValueError('release context mismatch')
    if record['executed'] is not True or record['status'] != 'passed':
        raise ValueError('suite not actually executed and passed')
    if (not isinstance(record['checks_count'], int) or isinstance(record['checks_count'], bool)
            or record['checks_count'] < 1):
        raise ValueError('missing checks count')
    if not isinstance(record['details'], dict):
        raise ValueError('invalid nested report')
    if hashlib.sha256(canonical(record['details'])).hexdigest() != record['details_sha256']:
        raise ValueError('nested report hash mismatch')
    raw = record['details']
    if suite in ('core','analysis','platform','collaboration'):
        from tools.release_matrix_v47 import SHARDS
        if (raw.get('shard') != suite or raw.get('actually_executed') is not True
                or [r.get('module') for r in raw.get('modules', [])] != list(SHARDS[suite])
                or any(r.get('status') != 'passed' or (r.get('tests_reported') or 0) < 1
                       for r in raw['modules'])
                or record['checks_count'] != sum(r['tests_reported'] for r in raw['modules'])):
            raise ValueError('invalid suite module report')
        # Reject evidence referencing a different source tree than the summary job.
        for r in raw['modules']:
            path = ROOT / 'tests' / (r['module'] + '.py')
            if hashlib.sha256(path.read_bytes()).hexdigest() != r.get('source_sha256'):
                raise ValueError('test file digest differs from source checkout')
    elif suite == 'smoke':
        from tools.release_gate import _matrix
        expected = [row[0] for row in _matrix('smoke')]
        if (raw.get('actually_executed') is not True
                or [r.get('name') for r in raw.get('steps', [])] != expected
                or any(r.get('status') != 'passed' for r in raw['steps'])
                or record['checks_count'] != len(expected)):
            raise ValueError('invalid smoke report')
    elif suite == 'locks':
        if (raw.get('executed') is not True
                or [r.get('name') for r in raw.get('steps', [])] != ['unittest','fault-injection']
                or any(r.get('status') != 'passed' or r.get('exit_code') != 0 for r in raw['steps'])
                or record['checks_count'] != 2):
            raise ValueError('invalid lock report')
    return suite, system


def aggregate(folder: Path, *, sha: str, run_id: str, attempt: str,
              require_ci: bool = True) -> dict:
    if not HEX_SHA.fullmatch(sha) or not SAFE_NUMBER.fullmatch(run_id) or not SAFE_NUMBER.fullmatch(attempt):
        raise ValueError('expected GitHub commit and run context are required')
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('invalid evidence directory')
    expected_files = {f'ci_v48_{system}_{suite}.json' for suite, system in REQUIRED}
    files = [x for x in folder.iterdir() if x.is_file() or x.is_symlink()]
    if {x.name for x in files} != expected_files or len(files) != len(expected_files):
        raise ValueError('missing, duplicate or unexpected CI evidence')
    items = []
    seen = set()
    for path in sorted(files):
        record = _safe_evidence_file(path)
        identity = validate_evidence(record, sha=sha, run_id=run_id, attempt=attempt,
                                     require_ci=require_ci)
        if identity in seen or path.name != f'ci_v48_{identity[1]}_{identity[0]}.json':
            raise ValueError('duplicated or incorrectly named evidence')
        seen.add(identity)
        items.append({'platform':identity[1], 'suite':identity[0],
                      'checks_count':record['checks_count'],
                      'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if seen != REQUIRED:
        raise ValueError('incomplete CI matrix')
    return {'schema_version':1, 'toolkit_version':'4.8', 'verified_consistency':True,
            'externally_signed':False, 'commit_sha':sha, 'run_id':run_id,
            'attempt':attempt, 'suites':items, 'checks_total':sum(x['checks_count'] for x in items),
            'limitations':'JSON hashes and context consistency do not authenticate origin; '
                          'GitHub artifact access and provenance must be assessed separately.'}


def _write_new(path: Path, value: dict) -> None:
    if not path.name.startswith('ci_v48_') or not path.name.endswith('.json'):
        raise ValueError('invalid evidence filename')
    allowed = (ROOT / 'benchmarks' / 'reports').resolve()
    if path.absolute().parent != allowed:
        raise ValueError('output must be directly under benchmarks/reports')
    for parent in (ROOT / 'benchmarks', ROOT / 'benchmarks' / 'reports'):
        if parent.is_symlink():
            raise ValueError('unsafe evidence directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os,'O_NOFOLLOW',0), 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run')
    run.add_argument('--suite', choices=SUITES, required=True)
    run.add_argument('--execute', action='store_true')
    run.add_argument('--output', type=Path)
    agg = sub.add_parser('aggregate')
    agg.add_argument('--folder', type=Path, required=True)
    agg.add_argument('--expected-sha', required=True)
    agg.add_argument('--run-id', required=True)
    agg.add_argument('--attempt', required=True)
    agg.add_argument('--output', type=Path)
    sub.add_parser('plan')
    args = p.parse_args()
    try:
        if args.command == 'plan':
            result = {'required': sorted([{'suite':s,'platform':o} for s,o in REQUIRED],
                                         key=lambda x:(x['platform'],x['suite'])),
                      'note':'plan only; no CI platform has been verified'}
        elif args.command == 'run':
            if args.output and not args.execute:
                raise ValueError('output requires --execute')
            if args.output:
                _validate_destination(args.output)
            result = run_suite(args.suite, execute=args.execute)
            if args.output:
                expected = f'ci_v48_{result["platform"]}_{args.suite}.json'
                if args.output.name != expected:
                    raise ValueError('output name does not match suite and platform')
                _write_new(args.output, result)
        else:
            result = aggregate(args.folder, sha=args.expected_sha.lower(),
                               run_id=args.run_id, attempt=args.attempt)
            if args.output:
                _validate_destination(args.output)
                _write_new(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == 'run' and args.execute and result['status'] != 'passed':
            return 1
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, TypeError) as exc:
        p.error(str(exc))


def _validate_destination(path: Path) -> None:
    allowed = (ROOT / 'benchmarks' / 'reports').resolve()
    if (path.absolute().parent != allowed or path.is_symlink() or path.exists()
            or not path.name.startswith('ci_v48_') or not path.name.endswith('.json')):
        raise ValueError('evidence output must be a new file in benchmarks/reports')


if __name__ == '__main__':
    raise SystemExit(main())
