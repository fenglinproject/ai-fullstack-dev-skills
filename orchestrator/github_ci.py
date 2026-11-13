#!/usr/bin/env python3
"""Opt-in GitHub CLI adapter: offline previews, read-only checks, approved PR creation.

No implicit login, push, merge or deployment. The local repo and gh CLI must
be trusted. gh calls are never made without --execute, PR publication also
requires a separate --approve. Github's server response is not locally verified.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

try:
    from orchestrator.git_collab import _root, _git, _checks_evidence
    from orchestrator.workflow import _load_change, _drift
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from orchestrator.git_collab import _root, _git, _checks_evidence
    from orchestrator.workflow import _load_change, _drift

REPO = re.compile(r'([A-Za-z0-9][A-Za-z0-9-]{0,99})/([A-Za-z0-9_.-]{1,100})\Z')
BASE = re.compile(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,79}\Z')
GH_URL = re.compile(r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?\Z', re.I)
GH_SSH = re.compile(r'(?:git@github\.com:|ssh://git@github\.com/)([^/]+)/([^/]+?)(?:\.git)?\Z', re.I)


def _repo_from_origin(project: Path) -> str:
    url = _git(project, 'remote', 'get-url', 'origin')
    m = GH_URL.fullmatch(url) or GH_SSH.fullmatch(url)
    if not m:
        raise ValueError('origin must be an explicit github.com HTTPS or SSH repository')
    name = m.group(1) + '/' + m.group(2)
    if not REPO.fullmatch(name):
        raise ValueError('unsafe GitHub repository name')
    return name


def _call_gh(args: list[str]) -> object:
    if shutil.which('gh') is None:
        raise ValueError('GitHub CLI gh not installed')
    env = {k:v for k,v in os.environ.items() if k in ('PATH','HOME','USERPROFILE','GH_TOKEN','GITHUB_TOKEN','XDG_CONFIG_HOME','LANG','LC_ALL','SYSTEMROOT','WINDIR')}
    env['GH_HOST'] = 'github.com'
    env['GH_PROMPT_DISABLED'] = '1'
    env['GIT_TERMINAL_PROMPT'] = '0'
    try:
        proc = subprocess.run(['gh', *args], env=env, capture_output=True, timeout=40, check=False)
    except subprocess.TimeoutExpired as e:
        raise ValueError('GitHub CLI timed out; action outcome is unknown, check remote before retry') from e
    if len(proc.stdout)>128_000 or len(proc.stderr)>32_000:
        raise ValueError('GitHub CLI output too large')
    if proc.returncode:
        # Never echo stderr: could contain URL, credentials, or repository data.
        raise ValueError('GitHub CLI request failed; inspect gh authentication, network and permissions separately')
    try:return json.loads(proc.stdout.decode('utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError) as e:
        raise ValueError('GitHub CLI response was not valid JSON; verify remote outcome before retry') from e


def checks(project:Path,pr:int,*,execute:bool=False) -> dict:
    project = _root(project)
    if isinstance(pr,bool) or not isinstance(pr,int) or pr<1 or pr>2_000_000_000:
        raise ValueError('PR number must be positive')
    repo=_repo_from_origin(project)
    args=['pr','view',str(pr),'--repo',repo,'--json','number,url,state,statusCheckRollup']
    if not execute:
        return {'mode':'preview','repo':repo,'pr':pr,'command':['gh',*args],
                'network_access':False,'note':'No GitHub request made.'}
    data=_call_gh(args)
    if not isinstance(data,dict) or data.get('number')!=pr:
        raise ValueError('GitHub CLI returned unexpected PR data')
    rows=data.get('statusCheckRollup')
    if not isinstance(rows,list):rows=[]
    state=[]
    for row in rows[:300]:
        if not isinstance(row,dict):continue
        label=row.get('conclusion') or row.get('state') or row.get('status') or 'UNKNOWN'
        state.append({'name':str(row.get('name') or row.get('context') or 'unnamed')[:120],
                      'state':str(label)[:80]})
    return {'mode':'observed','repo':repo,'pr':pr,'url':data.get('url'),
            'pr_state':data.get('state'),'checks':state,
            'all_checks_successful':bool(state) and all(c['state'] in ('SUCCESS','NEUTRAL','SKIPPED') for c in state),
            'note':'Read-only remote observation; no merge, push, or deployment. Missing check results are NOT success.'}


def _create_remote_draft(args:list[str], repo:str)->str:
    """Run the only remote-writing operation after preflight and caller approval."""
    # gh pr create prints a URL rather than JSON; keep output validation narrow.
    if shutil.which('gh') is None:raise ValueError('GitHub CLI gh not installed')
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','USERPROFILE','GH_TOKEN','GITHUB_TOKEN','XDG_CONFIG_HOME','LANG','LC_ALL','SYSTEMROOT','WINDIR')}
    env.update({'GH_HOST':'github.com','GH_PROMPT_DISABLED':'1','GIT_TERMINAL_PROMPT':'0'})
    try:r=subprocess.run(['gh',*args],env=env,capture_output=True,timeout=40,check=False)
    except subprocess.TimeoutExpired as e:
        raise ValueError('PR publication timed out; remote outcome unknown; check GitHub before retry') from e
    if len(r.stdout)>8192 or r.returncode:
        raise ValueError('PR publication failed or returned unexpected output; check GitHub before retry')
    url=r.stdout.decode('utf-8','replace').strip()
    # Avoid treating non-GitHub URLs / arbitrary CLI text as success.
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/pull/[0-9]+/?',url):
        raise ValueError('PR request finished but returned no valid GitHub PR URL; inspect remote manually')
    if not url.lower().startswith('https://github.com/'+repo.lower()+'/pull/'):
        raise ValueError('unexpected remote PR repository; inspect manually')
    return url


def publish(project:Path,change_id:str,*,title:str,base:str='main',execute:bool=False,approved:bool=False)->dict:
    project=_root(project)
    repo=_repo_from_origin(project)
    if not isinstance(title,str) or not 6<=len(title)<=140 or any(ord(c)<32 for c in title):
        raise ValueError('invalid PR title')
    if not isinstance(base,str) or not BASE.fullmatch(base) or '..' in base or base.endswith(('/','.lock')):
        raise ValueError('invalid base')
    _,record=_load_change(project,change_id)
    if record['status'] not in ('applied','committed') or not all(x['unchanged_since_apply'] for x in _drift(project,record)):
        raise ValueError('change is not applied or has drifted')
    if record['status']=='committed' and record.get('git_commit')!=_git(project,'rev-parse','HEAD'):
        raise ValueError('Git HEAD no longer matches the reviewed committed change')
    report=_checks_evidence(project,change_id)
    branch = _git(project,'branch','--show-current')
    if not branch.startswith('ai/') or not BASE.fullmatch(branch):
        raise ValueError('PR publication requires ai/* branch')
    if _git(project,'status','--porcelain','--untracked-files=all','--','.',':(exclude).ai'):
        raise ValueError('working tree must be clean')
    committed=set(_git(project,'diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines())
    expected={f['path'] for f in record['files']}
    if committed!=expected:
        raise ValueError('HEAD commit paths do not match approved change')
    path=project/'.ai/pr-drafts'/(change_id+'.md')
    if path.is_symlink() or not path.is_file() or path.stat().st_size>100_000:
        raise ValueError('valid local PR draft required')
    args=['pr','create','--repo',repo,'--base',base,'--head',branch,'--title',title,
          '--body-file',str(path),'--draft']
    preview={'repo':repo,'branch':branch,'base':base,'change_id':change_id,'evidence':report,
             'command':['gh',*args],'note':'Requires that branch has already been pushed manually; no implicit push.'}
    if not execute:
        return {**preview,'mode':'preview','published':False,'network_access':False}
    if not approved:
        raise ValueError('publishing a remote draft PR requires explicit --approve')
    url = _create_remote_draft(args, repo)
    return {'mode':'published','repo':repo,'change_id':change_id,'url':url,'published':True,
            'note':'A draft GitHub PR was created, not merged or deployed.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Opt-in GitHub PR/CI bridge; no automatic push or merge')
    sub=p.add_subparsers(dest='action',required=True)
    for act in ('checks','publish'):
        a=sub.add_parser(act);a.add_argument('--project',required=True);a.add_argument('--execute',action='store_true')
        if act=='checks':a.add_argument('--pr',type=int,required=True)
        else:
            a.add_argument('--change-id',required=True)
            a.add_argument('--title',required=True)
            a.add_argument('--base',default='main')
            a.add_argument('--approve',action='store_true')
    args=p.parse_args(argv)
    try:
        res=(checks(Path(args.project),args.pr,execute=args.execute) if args.action=='checks' else
             publish(Path(args.project),args.change_id,title=args.title,base=args.base,
                     execute=args.execute,approved=args.approve))
        print(json.dumps(res,ensure_ascii=False,indent=2))
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
