#!/usr/bin/env python3
"""Read-only GitHub check-run verification through authenticated gh CLI.

This is an observation obtained from GitHub at query time, not a signed attestation,
and not a substitute for branch protection, trusted workflow design, or permissions.
"""
from __future__ import annotations
import argparse, json, re, shutil, subprocess
from pathlib import Path
from tools.repo_readiness_v44 import repository_root, _git_text, SAFE_NAME
from orchestrator.github_ci import _repo_from_origin, _call_gh

SHA=re.compile(r'[a-f0-9]{40}\Z')
PASS={'success','neutral','skipped'}

def verify(project:Path, *, expected_head:str, required_checks:list[str], execute:bool=False)->dict:
    root=repository_root(project)
    if not isinstance(expected_head,str) or not SHA.fullmatch(expected_head):
        raise ValueError('require full 40-character Git commit SHA')
    if _git_text(root,'rev-parse','HEAD')!=expected_head:
        raise ValueError('local HEAD no longer matches pinned commit')
    if not required_checks or len(required_checks)>32 or any(not isinstance(n,str) or not SAFE_NAME.fullmatch(n) for n in required_checks):
        raise ValueError('1 to 32 explicit, safe check names required')
    if len(set(required_checks))!=len(required_checks):raise ValueError('duplicate required check')
    repo=_repo_from_origin(root)
    endpoint=f'repos/{repo}/commits/{expected_head}/check-runs?per_page=100'
    args=['api','--hostname','github.com','-X','GET',endpoint]
    if not execute:
        return {'schema_version':1,'mode':'preview','repository':repo,'commit':expected_head,
                'required_checks':required_checks,'network_access':False,'verified':False,
                'command':['gh',*args]}
    # gh uses authenticated GitHub REST API. Never expose credentials or full API response.
    data=_call_gh(args)
    if not isinstance(data,dict) or not isinstance(data.get('total_count'),int) or not isinstance(data.get('check_runs'),list):
        raise ValueError('invalid GitHub check-runs response')
    runs=data['check_runs']
    if data['total_count']>len(runs):
        raise ValueError('more than 100 check runs; incomplete response, refusing to attest checks')
    observed={}
    for item in runs:
        if not isinstance(item,dict):continue
        name=item.get('name')
        if name not in required_checks:continue
        if item.get('head_sha')!=expected_head:
            raise ValueError('check-run SHA mismatches requested commit')
        observed.setdefault(name,[]).append(item)
    statuses={}
    for name in required_checks:
        entries=observed.get(name,[])
        # Duplicate names can hide a failing check; fail closed rather than choose latest.
        if len(entries)!=1:statuses[name]='missing' if not entries else 'ambiguous'
        else:
            entry=entries[0]
            status=entry.get('status')
            conclusion=entry.get('conclusion')
            statuses[name]='passed' if status=='completed' and conclusion in PASS else 'not_passed'
    ok=all(v=='passed' for v in statuses.values())
    return {'schema_version':1,'mode':'observed','source':'authenticated-gh-api',
            'repository':repo,'commit':expected_head,'required_checks':required_checks,
            'check_results':statuses,'verified':ok,'network_access':True,
            'note':'Live GitHub API observation, not cryptographic proof, branch-protection enforcement, or approval to merge.'}

def main(argv=None):
    p=argparse.ArgumentParser(description='Explicit GitHub CI check-run observation, no remote writes')
    p.add_argument('--project',type=Path,required=True);p.add_argument('--expected-head',required=True)
    p.add_argument('--required-check',action='append',required=True);p.add_argument('--execute',action='store_true')
    a=p.parse_args(argv)
    try:
        result=verify(a.project,expected_head=a.expected_head,required_checks=a.required_check,execute=a.execute)
        print(json.dumps(result,indent=2))
        return 0 if not a.execute or result['verified'] else 1
    except (OSError,ValueError,subprocess.TimeoutExpired) as ex:p.exit(2,f'error: {ex}\n')
if __name__=='__main__':raise SystemExit(main())
