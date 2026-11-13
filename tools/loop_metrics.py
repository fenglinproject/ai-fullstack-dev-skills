#!/usr/bin/env python3
"""Offline aggregate of local V3.2+ repair journals. Does not emit task/source text."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path

STAGES = {'awaiting_approval','applying','awaiting_test','testing','awaiting_repair',
          'completed','exhausted','unverified','aborted','rollback_blocked','recovery_needed'}
ATTEMPT_STATUS = {'awaiting_approval','applied','passed','failed','unverified'}


def _seconds(a: str, b: str) -> float | None:
    try:
        start = dt.datetime.fromisoformat(a)
        end = dt.datetime.fromisoformat(b)
        if not start.tzinfo or not end.tzinfo: return None
        delta = (end - start).total_seconds()
        return round(delta, 2) if delta >= 0 else None
    except (TypeError, ValueError):
        return None


def summarize(project: Path, max_runs: int = 500) -> dict:
    root = project.resolve(strict=True)
    if not root.is_dir() or not 1 <= max_runs <= 2000:
        raise ValueError('invalid project or max_runs')
    if (root / '.ai').is_symlink():
        raise ValueError('unsafe .ai folder')
    loops = root / '.ai' / 'loops'
    if loops.is_symlink():
        raise ValueError('unsafe loop directory')
    if not loops.exists():
        return {'runs': 0, 'completed': 0, 'exhausted': 0, 'total_attempts': 0,
                'tested_attempts': 0, 'passed_attempts': 0, 'failed_attempts': 0,
                'completion_rate': None, 'first_pass_success_runs':0, 'repaired_success_runs':0,
                'first_pass_success_rate':None, 'exhaustion_rate':None, 'attempt_distribution':{str(i):0 for i in range(1,6)},
                'p50_elapsed_seconds':None, 'p95_elapsed_seconds':None, 'mean_attempts': None, 'mean_elapsed_seconds': None,
                'warnings': [], 'items': []}
    items, warnings = [], []
    dirs = sorted(loops.iterdir())
    if len(dirs) > max_runs:raise ValueError('run count exceeds limit')
    for folder in dirs:
        if folder.is_symlink() or not folder.is_dir() or not folder.name.startswith('loop-'):
            warnings.append('Skipped invalid run entry')
            continue
        f = folder / 'state.json'
        if f.is_symlink() or not f.is_file() or f.stat().st_size > 512000:
            warnings.append('Skipped missing/unsafe state in ' + folder.name)
            continue
        try:
            s = json.loads(f.read_text('utf-8'))
            if s['schema_version'] != 1 or s['run_id'] != folder.name or s['stage'] not in STAGES:
                raise ValueError('invalid run schema')
            attempts = s['attempts']
            if not isinstance(attempts, list) or len(attempts) > 5:
                raise ValueError('invalid attempts count')
            if any(not isinstance(a, dict) or a.get('status') not in ATTEMPT_STATUS for a in attempts):
                raise ValueError('invalid attempt status')
            counts = {k: sum(a.get('status') == k for a in attempts) for k in ('passed','failed','unverified')}
            items.append({'run_id': folder.name, 'stage': s['stage'], 'attempts': len(attempts),
                          'passed_attempts': counts['passed'], 'failed_attempts': counts['failed'],
                          'unverified_attempts': counts['unverified'],
                          'elapsed_seconds': _seconds(s.get('created_at'), s.get('updated_at'))})
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            warnings.append('Skipped invalid state in ' + folder.name)
    runs = len(items)
    total_attempts = sum(x['attempts'] for x in items)
    elapsed = [x['elapsed_seconds'] for x in items if x['elapsed_seconds'] is not None]
    complete = sum(x['stage'] == 'completed' for x in items)
    first_pass = sum(x['stage'] == 'completed' and x['attempts'] == 1 for x in items)
    repaired = sum(x['stage'] == 'completed' and x['attempts'] > 1 for x in items)
    ordered_elapsed = sorted(elapsed)
    def percentile(p):
        if not ordered_elapsed:return None
        import math
        return ordered_elapsed[max(0, math.ceil(len(ordered_elapsed)*p)-1)]
    failed = sum(x['failed_attempts'] for x in items)
    passed = sum(x['passed_attempts'] for x in items)
    return {'runs': runs, 'completed': complete, 'exhausted': sum(x['stage'] == 'exhausted' for x in items),
            'total_attempts': total_attempts, 'tested_attempts': failed + passed + sum(x['unverified_attempts'] for x in items),
            'passed_attempts': passed, 'failed_attempts': failed,
            'completion_rate': round(complete/runs, 4) if runs else None,
            'first_pass_success_runs': first_pass, 'repaired_success_runs': repaired,
            'first_pass_success_rate': round(first_pass/runs,4) if runs else None,
            'exhaustion_rate': round(sum(x['stage'] == 'exhausted' for x in items)/runs,4) if runs else None,
            'attempt_distribution': {str(i):sum(x['attempts'] == i for x in items) for i in range(1,6)},
            'p50_elapsed_seconds': percentile(0.5), 'p95_elapsed_seconds': percentile(0.95),
            'mean_attempts': round(total_attempts/runs, 2) if runs else None,
            'mean_elapsed_seconds': round(sum(elapsed)/len(elapsed), 2) if elapsed else None,
            'warnings': warnings, 'items': items,
            'note': 'Counts reflect saved journal status, not independently verified code quality or security. '
                    'Current elapsed time includes user review pauses. No task text or project source is exported.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Aggregate local bounded repair-session journals')
    p.add_argument('--project',required=True)
    p.add_argument('--max-runs',type=int,default=500)
    a=p.parse_args(argv)
    try:print(json.dumps(summarize(Path(a.project),a.max_runs),ensure_ascii=False,indent=2))
    except (OSError,ValueError) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__': main()
