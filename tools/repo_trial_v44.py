#!/usr/bin/env python3
"""Bounded, repeatable READ-ONLY reliability sampling of a trusted local Git repo.

A quick sample series is not a multi-day soak test. Never runs project tests.
It writes no files and makes no remote Git/API/model calls.
"""
from __future__ import annotations
import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

from tools.repo_readiness_v44 import readiness


def sample(project:Path, *, repeats:int=5,expected_head:str|None=None,
           require_clean:bool=False,require_ci:bool=False,ci_receipt:Path|None=None,
           required_checks:list[str]|None=None)->dict:
    if not isinstance(repeats,int) or not 1<=repeats<=30:
        raise ValueError('repeats must be from 1 to 30')
    snapshots=[]
    for index in range(repeats):
        start=time.perf_counter()
        result=readiness(project,expected_head=expected_head,require_clean=require_clean,
                         require_ci=require_ci,ci_receipt=ci_receipt,required_checks=required_checks)
        snapshots.append({'sample':index+1,'duration_ms':round((time.perf_counter()-start)*1000,3),
                          'status':result['status'],'head':result['git']['head'],
                          'blocker_count':len(result['blockers']),
                          'active_changes':result['change_conflicts']['active_change_count']})
    durations=[s['duration_ms'] for s in snapshots]
    statuses={s['status'] for s in snapshots}
    heads={s['head'] for s in snapshots}
    return {'schema_version':1,'samples':repeats,'stable_head':len(heads)==1,
            'stable_status':len(statuses)==1,
            'all_reviewable':all(s['status']=='reviewable' for s in snapshots),
            'duration_ms':{'min':min(durations),'median':round(statistics.median(durations),3),
                           'max':max(durations)},
            'snapshots':snapshots,
            'note':'Short read-only repeated snapshots of the same repository, not a continuous long-term test or evidence of production readiness.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Bounded V4.4 read-only repository reliability samples')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--samples',type=int,default=5)
    p.add_argument('--expected-head')
    p.add_argument('--require-clean',action='store_true')
    p.add_argument('--require-ci',action='store_true')
    p.add_argument('--ci-receipt',type=Path)
    p.add_argument('--required-check',action='append',default=[])
    a=p.parse_args(argv)
    try:
        result=sample(a.project,repeats=a.samples,expected_head=a.expected_head,
                      require_clean=a.require_clean,require_ci=a.require_ci,
                      ci_receipt=a.ci_receipt,required_checks=a.required_check)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['all_reviewable'] else 1
    except (OSError,ValueError,subprocess.TimeoutExpired) as ex:
        p.exit(2,'error: '+str(ex)+'\n')

if __name__=='__main__':raise SystemExit(main())
