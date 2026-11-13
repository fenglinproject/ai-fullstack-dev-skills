#!/usr/bin/env python3
"""Read-only, bounded Git review of an existing V3 change manifest.

Does NOT stage, commit, check out, clean, reset or push. No hooks or custom
commands are invoked. A review alone is not a proof that tests passed.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
from pathlib import Path

try:
    from orchestrator.workflow import _drift, _load_change
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from orchestrator.workflow import _drift, _load_change


def git(project:Path, *args:str, max_bytes:int=256_000)->subprocess.CompletedProcess:
    env={k:v for k,v in os.environ.items() if k in ('PATH','SYSTEMROOT','WINDIR','LANG','LC_ALL')}
    env.update({'GIT_PAGER':'cat','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'})
    result=subprocess.run(['git','--no-pager','-C',str(project),*args],
            capture_output=True,timeout=8,check=False,env=env)
    if len(result.stdout)>max_bytes or len(result.stderr)>max_bytes:
        raise ValueError('Git output exceeded review size limit')
    return result


def review_git(project:Path,change_id:str)->dict:
    project=project.resolve(strict=True)
    _,manifest=_load_change(project,change_id)
    root=git(project,'rev-parse','--show-toplevel')
    if root.returncode!=0 or Path(os.fsdecode(root.stdout).strip()).resolve()!=project:
        raise ValueError('project must be the top-level Git repository')
    paths=[f['path'] for f in manifest['files']]
    status=git(project,'status','--short','--untracked-files=normal','--',*paths)
    diff=git(project,'diff','--no-ext-diff','--no-color','--',*paths)
    diff_cached=git(project,'diff','--cached','--no-ext-diff','--no-color','--',*paths)
    check=git(project,'diff','--check','--',*paths)
    if any(x.returncode not in (0,) for x in [status,diff,diff_cached]):
        raise ValueError('Git review command failed')
    if check.returncode not in (0,2):
        raise ValueError('Git diff --check failed unexpectedly')
    return {'change_id':change_id,'change_status':manifest['status'],'paths':paths,
            'source_hashes':_drift(project,manifest),
            'status':status.stdout.decode('utf-8','replace'),
            'unstaged_diff':diff.stdout.decode('utf-8','replace'),
            'staged_diff':diff_cached.stdout.decode('utf-8','replace'),
            'whitespace_warnings':check.stdout.decode('utf-8','replace'),
            'note':'Read-only Git review only. No branch, stage, commit or push was made. Untracked file contents are not included in git diff.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Review V3 changes in Git, without modifying repository')
    p.add_argument('--project',required=True)
    p.add_argument('--change-id',required=True)
    args=p.parse_args(argv)
    try:print(json.dumps(review_git(Path(args.project),args.change_id),ensure_ascii=False,indent=2))
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
