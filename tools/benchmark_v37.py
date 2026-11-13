#!/usr/bin/env python3
"""Visible, deterministic V3.7 four-project offline fixture benchmark.
No model calls or real outside repositories. Expected paths are human-curated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
try:
    from tools.incremental_index import build, search
    from tools.test_selection import select
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import build, search
    from tools.test_selection import select

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/'benchmarks/v37_cases.json'

def evaluate(fixtures:Path=CASES)->dict:
    raw=fixtures.read_bytes();data=json.loads(raw)
    if data.get('schema_version')!=1:raise ValueError('unsupported benchmark schema')
    project_base=(ROOT/'benchmarks/projects').resolve(strict=True)
    project_names=set(x['project'] for key in ('symbol_cases','test_cases') for x in data[key])
    cache={}
    for name in sorted(project_names):
        if not isinstance(name,str) or not name or name in ('.','..') or '/' in name or '\\' in name:
            raise ValueError('unsafe project name')
        project=(project_base/name).resolve(strict=True)
        if project_base not in project.parents:raise ValueError('project escaped fixtures')
        cache[name]=build(project,use_cache=False)
    symbol=[]
    for c in data['symbol_cases']:
        result=search(cache[c['project']],c['task'],limit=5)['matches']
        rank=next((i+1 for i,x in enumerate(result) if x['path']==c['expected_path'] and x['qualified_name']==c['expected_symbol']),None)
        symbol.append({'id':c['id'],'project':c['project'],'hit':rank is not None,'rank':rank})
    tests=[]
    for c in data['test_cases']:
        result=select(cache[c['project']],c['changed'])
        candidates=[x['path'] for x in result['tests']]
        hit=(c['expected_test'] in candidates if c['expected_test'] is not None else not candidates)
        hit=hit and (not c.get('expect_full') or result['full_suite_required'])
        tests.append({'id':c['id'],'project':c['project'],'hit':hit,'full_suite_required':result['full_suite_required']})
    return {'schema_version':1,'fixture_sha256':hashlib.sha256(raw).hexdigest(),
            'projects':sorted(project_names),
            'symbols':{'cases':len(symbol),'hit':sum(x['hit'] for x in symbol),'details':symbol},
            'test_selection':{'cases':len(tests),'hit':sum(x['hit'] for x in tests),'details':tests},
            'note':'Visible four-project synthetic/teaching fixtures, no hidden real-world repos, no external LLM. Test selection is not completeness proof.'}

def main(argv=None):
    p=argparse.ArgumentParser(description='Offline reproducible V3.7 fixture checks')
    p.add_argument('--output',type=Path)
    p.add_argument('--min-accuracy',type=float,default=0.8)
    a=p.parse_args(argv)
    try:
        if not 0<=a.min_accuracy<=1:raise ValueError('min accuracy must be 0..1')
        result=evaluate()
        raw=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
        if a.output:
            if a.output.is_symlink() or not a.output.parent.is_dir():raise ValueError('unsafe output path')
            a.output.write_text(raw,'utf-8')
        print(raw)
        if any(part['cases']==0 or part['hit']/part['cases']<a.min_accuracy for part in (result['symbols'],result['test_selection'])):raise SystemExit(1)
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,json.JSONDecodeError) as e:p.exit(2,f'error: {e}\n')
if __name__=='__main__':main()
