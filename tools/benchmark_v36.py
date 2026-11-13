#!/usr/bin/env python3
"""Repeatable local-fixture AST and traceback-hint benchmark, no model calls.

Reported dev/holdout are fixed named slices, NOT concealed or truly blind sets.
No source is executed; synthetic projects are shipped with the package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from tools.ast_symbols import search
    from tools.evidence_context import analyze
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.ast_symbols import search
    from tools.evidence_context import analyze

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'benchmarks' / 'v36_cases.json'


def _safe_project(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('unsafe benchmark project path')
    base = root.resolve(strict=True)
    path = (base / value).resolve(strict=True)
    if base not in path.parents or not path.is_dir():
        raise ValueError('benchmark project must be a subdirectory')
    return path


def _stats(cases: list[dict]) -> dict:
    n = len(cases)
    correct = sum(bool(c['correct']) for c in cases)
    return {'cases': n, 'correct': correct, 'accuracy': round(correct / n, 4) if n else None}


def evaluate(root: Path = ROOT, fixtures: Path = FIXTURES, top_k: int = 3) -> dict:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 12:
        raise ValueError('top_k must be 1..12')
    raw = fixtures.read_bytes()
    data = json.loads(raw)
    if data.get('schema_version') != 1:
        raise ValueError('unsupported fixture version')
    symbol_cases = []
    trace_cases = []
    ids = set()
    for kind, entries in [('symbol', data['symbol_cases']), ('trace', data['trace_cases'])]:
        if not isinstance(entries, list):
            raise ValueError('benchmark cases must be lists')
        for case in entries:
            ident = (kind, case['id'])
            if ident in ids or case.get('split') not in ('dev','holdout'):
                raise ValueError('duplicate case or invalid split')
            ids.add(ident)
            project = _safe_project(root, case['project'])
            if kind == 'symbol':
                matches = search(project, case['task'], limit=top_k, include_references=False)['matches']
                expected = case['expected_path']
                expected_symbol = case['expected_symbol']
                top = matches[0] if matches else None
                # Positive cases must match both path and qualified symbol.
                # Negative cases must return no match at all.
                position = next((i+1 for i, m in enumerate(matches)
                                 if m['path'] == expected and m['qualified_name'] == expected_symbol), None)
                correct = (not matches) if expected is None else (position is not None)
                symbol_cases.append({'id':case['id'],'project':case['project'],'split':case['split'],
                    'correct':correct,'rank':position,'top1': position==1,'has_candidate':bool(top)})
            else:
                hints = analyze(project, [case['diagnostic']], limit=top_k)['hints']
                paths = [m['path'] for m in hints]
                expected = case['expected_path']
                correct = (not paths) if expected is None else expected in paths
                trace_cases.append({'id':case['id'],'project':case['project'],'split':case['split'],
                    'correct':correct,'top1':bool(paths) and paths[0]==expected,
                    'hints_count':len(paths)})
    by_split={}
    for split in ('dev','holdout'):
        by_split[split] = {'symbols':_stats([c for c in symbol_cases if c['split']==split]),
                           'traces':_stats([c for c in trace_cases if c['split']==split])}
    by_project={}
    for project in sorted({x['project'] for x in symbol_cases+trace_cases}):
        by_project[project]={'symbols':_stats([c for c in symbol_cases if c['project']==project]),
                             'traces':_stats([c for c in trace_cases if c['project']==project])}
    return {'schema_version':1,'fixture_sha256':hashlib.sha256(raw).hexdigest(),
            'top_k':top_k,'symbols':{'summary':_stats(symbol_cases),
                       'top1':sum(c['top1'] for c in symbol_cases), 'cases_detail':symbol_cases},
            'traces':{'summary':_stats(trace_cases),
                       'top1':sum(c['top1'] for c in trace_cases), 'cases_detail':trace_cases},
            'by_split':by_split,'by_project':by_project,
            'note':'Curated, visible dev/holdout fixtures, including synthetic projects and package examples. These are not unseen real-repository or live-model repair results.'}


def compare(current:dict, baseline:dict) -> dict:
    same = (current.get('fixture_sha256') == baseline.get('fixture_sha256') and
            current.get('top_k') == baseline.get('top_k'))
    return {'comparable':same,'delta':(
        {'symbols':round(current['symbols']['summary']['accuracy']-baseline['symbols']['summary']['accuracy'],4),
         'traces':round(current['traces']['summary']['accuracy']-baseline['traces']['summary']['accuracy'],4)}
        if same else None), 'note':'If fixture hash or top_k differs, no numerical comparison is made.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Offline AST and diagnostic context fixture evaluation')
    p.add_argument('--fixtures',type=Path,default=FIXTURES)
    p.add_argument('--top-k',type=int,default=3)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--min-holdout',type=float,default=0.75)
    args=p.parse_args(argv)
    try:
        if not 0 <= args.min_holdout <= 1:
            raise ValueError('min-holdout must be within [0,1]')
        result=evaluate(ROOT,args.fixtures,args.top_k)
        if args.baseline:
            if args.baseline.is_symlink() or args.baseline.stat().st_size > 1024*1024:
                raise ValueError('unsafe baseline report')
            result['comparison']=compare(result,json.loads(args.baseline.read_text('utf-8')))
        body=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
        if args.output:
            if args.output.is_symlink() or not args.output.parent.is_dir():
                raise ValueError('unsafe report path')
            args.output.write_text(body,'utf-8')
        print(body)
        for category in ('symbols','traces'):
            value=result['by_split']['holdout'][category]['accuracy']
            if value is None or value < args.min_holdout:
                raise SystemExit(1)
    except (OSError,ValueError,KeyError,TypeError,UnicodeDecodeError,json.JSONDecodeError) as exc:
        p.exit(2, f'error: {exc}\n')

if __name__=='__main__': main()
