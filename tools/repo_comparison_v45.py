#!/usr/bin/env python3
"""Repeatable, bounded read-only comparison of trusted local Git repositories.

Does not install dependencies, run arbitrary project code, clone remotes, or
claim that a short sampling run demonstrates production availability.
"""
from __future__ import annotations
import argparse, json, statistics, time
from pathlib import Path
from tools.repo_readiness_v44 import readiness, repository_root


def compare(projects:list[Path],*,samples:int=3)->dict:
    if not 1<=len(projects)<=8 or not 1<=samples<=20:raise ValueError('invalid projects/samples limit')
    roots=[repository_root(p) for p in projects]
    if len(set(roots))!=len(roots):raise ValueError('duplicate repository')
    results=[]
    for i,root in enumerate(roots):
        observations=[]
        for _ in range(samples):
            start=time.perf_counter()
            report=readiness(root,require_clean=False)
            observations.append({'head':report['git']['head'],'status':report['status'],
                'blockers':len(report['blockers']), 'duration_ms':round((time.perf_counter()-start)*1000,3)})
        results.append({'repository_index':i+1,'samples':samples,
            'stable_head':len({r['head'] for r in observations})==1,
            'stable_status':len({r['status'] for r in observations})==1,
            'reviewable_count':sum(r['status']=='reviewable' for r in observations),
            'blocker_count_max':max(r['blockers'] for r in observations),
            'duration_median_ms':round(statistics.median(r['duration_ms'] for r in observations),3),
            'observations':observations})
    return {'schema_version':1,'results':results,
            'note':'Short read-only local snapshots; no production soak test, no model execution, no CI authenticity claim.'}

def main(argv=None):
    p=argparse.ArgumentParser(description='Read-only, bounded cross-repository reliability sampling')
    p.add_argument('--project',action='append',required=True,type=Path)
    p.add_argument('--samples',type=int,default=3)
    a=p.parse_args(argv)
    try:
        r=compare(a.project,samples=a.samples)
        print(json.dumps(r,indent=2));return 0
    except (ValueError,OSError) as ex:p.exit(2,f'error: {ex}\n')
if __name__=='__main__':raise SystemExit(main())
