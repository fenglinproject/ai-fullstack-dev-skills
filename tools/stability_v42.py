#!/usr/bin/env python3
"""V4.2 dashboard reliability benchmark. All writes in a disposable fixture.

A caller can optionally inspect an EXISTING project read-only with --project;
this never starts that project's tests, its language servers, or a model.
"""
from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import threading
import time
from pathlib import Path

# Support both `python tools/stability_v42.py` and package imports.
if __package__ in (None, ''):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.snapshot import snapshot
from orchestrator.cli import _atomic_write


def create_fixture(root: Path, tasks: int = 900, reports: int = 120, loops: int = 80):
    """Create synthetic (not real-world) logs without source or private data."""
    if not (0 <= tasks <= 10_000 and 0 <= reports <= 3_000 and 0 <= loops <= 400):
        raise ValueError('fixture counts exceed bounded safety limits')
    ai = root / '.ai'
    (ai / 'reports').mkdir(parents=True, exist_ok=True)
    (ai / 'loops').mkdir(parents=True, exist_ok=True)
    statuses = ['todo', 'in_progress', 'blocked', 'done']
    entries = []
    for i in range(tasks):
        entries.append({'id': f'BENCH-{i:05d}', 'title': f'Synthetic work item {i}',
                        'status': statuses[i % 4], 'skill_id': None, 'evidence': [],
                        'updated_at': f'2026-11-{1 + i%7:02d}T{(i//7)%24:02d}:00:00+00:00'})
    _atomic_write(ai / 'task_state.json', {'schema_version': 1, 'tasks': entries})
    for i in range(reports):
        data = {'schema_version': 2, 'project': str(root),
                'actually_executed': True, 'timestamp': '2026-11-08T10:00:00+00:00',
                'checks': [{'name': 'synthetic-validation', 'status': 'failed' if i%10 == 0 else 'passed'}],
                'warning': 'synthetic record, not an actual test run'}
        (ai / 'reports' / f'checks-bench-{i:05d}.json').write_text(json.dumps(data), encoding='utf-8')
    for i in range(loops):
        folder = ai / 'loops' / f'loop-bench-{i:05d}'
        folder.mkdir()
        data = {'schema_version': 1, 'run_id': folder.name,
                'stage': 'completed' if i % 3 else 'exhausted',
                'created_at': '2026-11-08T10:00:00+00:00',
                'updated_at': '2026-11-08T10:01:00+00:00',
                'attempts': [{'status': 'passed' if i % 3 else 'failed'}]}
        (folder / 'state.json').write_text(json.dumps(data), encoding='utf-8')


def evaluate(project: Path, reads: int = 10) -> dict:
    """Evaluate read-only snapshots and bound returned data size."""
    if not 1 <= reads <= 100:
        raise ValueError('reads must be 1..100')
    timings = []
    samples = []
    for _ in range(reads):
        start = time.perf_counter()
        data = snapshot(project)
        timings.append((time.perf_counter() - start) * 1000)
        samples.append((data['stats']['tasks'], data['coverage']['tasks_displayed'],
                        len(data['reports']), data['loops']['runs']))
        if len(json.dumps(data).encode('utf-8')) > 1_000_000:
            raise AssertionError('dashboard response exceeds 1 MB safety budget')
    result = {'reads': reads, 'min_ms': round(min(timings), 2),
              'median_ms': round(statistics.median(timings), 2),
              'max_ms': round(max(timings), 2),
              'last_sample': {'tasks_total': samples[-1][0], 'tasks_displayed': samples[-1][1],
                              'reports_displayed': samples[-1][2], 'repair_runs': samples[-1][3]},
              'consistent_counts': len(set(samples)) == 1,
              'note': 'Observed local timings only; not an SLA, real-project benchmark or model success rate.'}
    return result


def concurrent_probe(root: Path, rounds: int = 20) -> dict:
    """Exercise the dashboard reader concurrently with atomic task updates.

    Modifies only a disposable fixture created by this script. Replacements
    can race with reads but must never expose partially written JSON.
    """
    if not 1 <= rounds <= 100:
        raise ValueError('rounds must be 1..100')
    ai = root / '.ai'
    state_file = ai / 'task_state.json'
    data = json.loads(state_file.read_text('utf-8'))
    errors = []
    counts = []
    def writer():
        try:
            for step in range(rounds):
                data['tasks'][0]['status'] = 'done' if step % 2 else 'blocked'
                _atomic_write(state_file, data)
        except Exception as error:
            errors.append(type(error).__name__)
    t = threading.Thread(target=writer, daemon=True)
    t.start()
    try:
        for _ in range(rounds):
            read = snapshot(root)
            counts.append(read['stats']['tasks'])
            if any('任务状态文件不可读取' in w for w in read['warnings']):
                errors.append('partial-task-read')
    except Exception as error:
        errors.append(type(error).__name__)
    finally:
        t.join(timeout=10)
    return {'rounds': rounds, 'errors': errors, 'all_counts_correct':
            all(count == len(data['tasks']) for count in counts),
            'writer_finished': not t.is_alive()}


def main(argv=None):
    p = argparse.ArgumentParser(description='V4.2 bounded local project reliability benchmark')
    p.add_argument('--project', type=Path, help='read-only existing project; no test execution')
    p.add_argument('--tasks', type=int, default=900)
    p.add_argument('--reports', type=int, default=120)
    p.add_argument('--loops', type=int, default=80)
    p.add_argument('--reads', type=int, default=10)
    p.add_argument('--output', type=Path)
    a = p.parse_args(argv)
    try:
        if a.project is not None:
            # --project never writes, including benchmark reports.
            result = {'schema_version': 1, 'mode': 'existing-project-read-only',
                      'timings': evaluate(a.project.resolve(strict=True), a.reads)}
        else:
            with tempfile.TemporaryDirectory(prefix='fullstack-v42-') as d:
                root = Path(d)
                create_fixture(root, a.tasks, a.reports, a.loops)
                result = {'schema_version': 1, 'mode': 'synthetic-disposable-fixture',
                          'fixture': {'tasks': a.tasks, 'reports': a.reports, 'loops': a.loops},
                          'timings': evaluate(root, a.reads),
                          'concurrent': concurrent_probe(root, rounds=min(20, a.reads * 2))
                          if a.tasks else {'rounds': 0, 'errors': [], 'all_counts_correct': True, 'writer_finished': True}}
                expected_visible = min(a.tasks, 300)
                if result['timings']['last_sample']['tasks_total'] != a.tasks or result['timings']['last_sample']['tasks_displayed'] != expected_visible:
                    raise AssertionError('task metrics mismatch')
                if result['concurrent']['errors'] or not result['concurrent']['all_counts_correct']:
                    raise AssertionError('concurrent consistency check failed')
        if a.output:
            dest = a.output.resolve()
            if a.project is not None:
                raise ValueError('when --project is provided, --output is not supported (strict read-only)')
            if not dest.parent.is_dir() or dest.is_symlink():
                raise ValueError('output parent must exist and not be a symlink')
            dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, AssertionError) as error:
        p.exit(2, f'error: {error}\n')


if __name__ == '__main__':
    main()
