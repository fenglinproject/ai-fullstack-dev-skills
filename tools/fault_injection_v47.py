#!/usr/bin/env python3
"""Explicitly opted-in local fault injection against an EPHEMERAL Git fixture.

No user repository is modified. Abrupt worker death and lock contention are
real OS subprocess events; this is not an application/production chaos test.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from orchestrator.write_guard_v46 import write_guard


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                               text=True, check=False, timeout=12)
    if completed.returncode:
        raise RuntimeError('could not create trusted temporary Git fixture')


def _worker(repo: Path, marker: Path, seconds: float) -> None:
    with write_guard(repo, timeout=2):
        marker.write_text('locked', encoding='ascii')
        time.sleep(seconds)


def run_faults() -> dict:
    with tempfile.TemporaryDirectory(prefix='v47-fault-') as td:
        base = Path(td)
        repo = base / 'repo'
        repo.mkdir()
        _git(repo, 'init', '-q')
        marker = base / 'locked'
        cmd = [sys.executable, str(Path(__file__).resolve()), '--worker',
               '--repo', str(repo), '--marker', str(marker), '--hold', '15']
        worker = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.PIPE, text=True)
        events = []
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and time.monotonic() < deadline and worker.poll() is None:
                time.sleep(.025)
            if not marker.exists():
                raise RuntimeError('fault worker did not acquire lock')
            try:
                with write_guard(repo, timeout=.15):
                    raise AssertionError('second writer acquired a live lock')
            except ValueError as exc:
                if 'holds the write gate' not in str(exc):
                    raise
            events.append('concurrent_write_rejected')
            worker.kill()  # simulated abrupt worker death: bypasses graceful context exit
            worker.communicate(timeout=5)
            with write_guard(repo, timeout=2):
                events.append('lock_recovered_after_process_death')
            # Fail-closed if lock gate path is replaced by a symlink.
            common = repo / '.git'
            from orchestrator.write_guard_v46 import GATE_NAME
            gate = common / GATE_NAME
            gate.unlink()
            other = base / 'sentinel'
            other.write_text('safe', encoding='utf-8')
            try:
                gate.symlink_to(other)
            except (OSError, NotImplementedError):
                events.append('symlink_test_unavailable')
            else:
                try:
                    with write_guard(repo, timeout=.1):
                        raise AssertionError('symlink gate accepted')
                except ValueError as exc:
                    if 'unsafe write gate path' not in str(exc):
                        raise
                if other.read_text('utf-8') != 'safe':
                    raise AssertionError('sentinel was modified')
                events.append('symlink_gate_rejected')
        finally:
            if worker.poll() is None:
                worker.kill()
            worker.communicate(timeout=5)
    return {'schema_version': 1, 'actually_executed': True, 'events': events,
            'passed': all(v in events for v in
                          ('concurrent_write_rejected', 'lock_recovered_after_process_death')),
            'scope': 'temporary local Git fixture; cooperative toolkit writers only'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--repo', type=Path, help=argparse.SUPPRESS)
    p.add_argument('--marker', type=Path, help=argparse.SUPPRESS)
    p.add_argument('--hold', type=float, default=15, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.worker:
        if not (a.repo and a.marker) or a.hold > 30:
            p.error('worker requires trusted fixture arguments')
        _worker(a.repo, a.marker, a.hold)
        return 0
    result = run_faults() if a.execute else {
        'schema_version': 1, 'actually_executed': False,
        'planned': ['contended_lock_rejected', 'worker_kill_releases_lock', 'symlink_gate_rejected'],
        'scope': 'temporary local Git fixture; no existing project touched'}
    print(json.dumps(result, indent=2))
    return 0 if result.get('passed', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
