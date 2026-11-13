#!/usr/bin/env python3
"""Conservative candidate test selection from local import graph (no execution).

Do not treat selected tests as a proof of complete coverage. Dynamic/ambiguous
imports, syntax errors, unknown files and zero matches demand a full suite.
"""
from __future__ import annotations
import argparse
import json
import posixpath
import re
import sys
from collections import deque
from pathlib import Path
try:
    from tools.incremental_index import build
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import build

TEST_NAME=re.compile(r'(?:^|/)(?:test_[^/]+\.py|[^/]+_test\.py|[^/]+\.(?:test|spec)\.(?:js|jsx|ts|tsx|mjs|cjs))$')
TEST_DIRS={'test','tests','__tests__','spec','specs'}

def is_test(path:str)->bool:
    return bool(TEST_NAME.search(path)) or (any(x in TEST_DIRS for x in path.split('/')[:-1]) and path.endswith(('.py','.js','.jsx','.ts','.tsx')))


def select(index:dict,changed:list[str],max_depth:int=12)->dict:
    if not isinstance(changed,list) or not changed or len(changed)>100 or any(not isinstance(x,str) or not x or x.startswith('/') or '..' in x.split('/') or '\\' in x for x in changed):
        raise ValueError('1..100 safe relative changed file paths required')
    if not isinstance(max_depth,int) or isinstance(max_depth,bool) or not 1<=max_depth<=30:raise ValueError('max_depth 1..30')
    records=index['files']; names=set(records)
    changed=sorted(set(changed))
    unknown=[path for path in changed if path not in names]
    reverse={key:[] for key in names}
    for path,row in records.items():
        for dep in row['dependencies']:
            if dep in reverse:reverse[dep].append(path)
    seen={p:0 for p in changed if p in names};q=deque(seen)
    while q:
        path=q.popleft()
        if seen[path]>=max_depth:continue
        for parent in sorted(reverse[path]):
            if parent in seen:continue
            seen[parent]=seen[path]+1;q.append(parent)
    tests=sorted(({'path':p,'depth':d,'reason':'changed-test' if d==0 else 'import-dependent'} for p,d in seen.items() if is_test(p)),key=lambda x:(x['depth'],x['path']))
    warnings=[]
    if unknown:warnings.append('unknown-or-unindexed-changed-file')
    if any(d>=max_depth and any(p not in seen for p in reverse.get(path,[])) for path,d in seen.items()):
        warnings.append('impact-depth-limit-reached')
    if any(r['parse_errors'] for r in records.values()):warnings.append('parser-errors-exist')
    if any(r.get('dynamic_imports') for r in records.values()):warnings.append('dynamic-imports-present')
    if any(r['unresolved_local_imports'] for r in records.values()):warnings.append('unresolved-local-imports')
    if index.get('project_config_warnings'):warnings.append('incomplete-project-configuration')
    if not tests:warnings.append('no-statically-related-tests')
    return {'schema_version':1,'changed':changed,'tests':tests,
            'affected_source_files':sorted(p for p in seen if p not in {t['path'] for t in tests}),
            'unknown_changed_files':unknown,'full_suite_required':bool(warnings),
            'caution_flags':warnings,'scanned_files':len(records),
            'note':'Candidate tests only: dependency reachability is not complete coverage. Run full suite before merging even when full_suite_required=false. No tests executed.'}

def main(argv=None):
    p=argparse.ArgumentParser(description='Suggest tests potentially affected by source changes; does not execute tests')
    p.add_argument('--project',required=True,type=Path)
    p.add_argument('--changed',nargs='+',required=True)
    p.add_argument('--save-cache',action='store_true')
    p.add_argument('--max-depth',type=int,default=12)
    a=p.parse_args(argv)
    try:
        idx=build(a.project,save_cache=a.save_cache)
        print(json.dumps(select(idx,a.changed,max_depth=a.max_depth),indent=2,ensure_ascii=False))
    except (OSError,ValueError,RuntimeError) as e:p.exit(2,f'error: {e}\n')
if __name__=='__main__':main()
