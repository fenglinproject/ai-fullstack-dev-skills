#!/usr/bin/env python3
"""Explicitly approved local Git branch/commit and offline PR drafting.

Never pushes, contacts GitHub, creates a remote PR, or runs user Git hooks.
Use only trusted repositories: malicious Git filters/configs can execute on add.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

try:
    from orchestrator.workflow import _load_change,_drift,_hash,_json_write,_utc,_utc
    from orchestrator.git_review import git
    from orchestrator.code_review import review as code_review
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from orchestrator.workflow import _load_change,_drift,_hash,_json_write,_utc,_utc
    from orchestrator.git_review import git
    from orchestrator.code_review import review as code_review

BRANCH_RE=re.compile(r'ai/[a-zA-Z0-9][a-zA-Z0-9._/-]{0,69}\Z')

def _git(project:Path,*args:str)->str:
    r=git(project,*args,max_bytes=200000)
    if r.returncode:raise ValueError(f'git command failed: {" ".join(args[:2])}: {r.stderr.decode("utf-8","replace")[:250]}')
    return r.stdout.decode('utf-8','replace').strip()


def _root(project:Path)->Path:
    project=project.resolve(strict=True)
    if _git(project,'rev-parse','--show-toplevel')!=str(project):
        raise ValueError('project must be a Git repository root')
    if not (project/'.ai').is_dir() or (project/'.ai').is_symlink():
        raise ValueError('initialize .ai first')
    return project


def branch(project:Path,name:str,*,approved:bool=False)->dict:
    if not approved:raise ValueError('branch creation requires explicit --approve')
    project=_root(project)
    if not isinstance(name,str) or not BRANCH_RE.fullmatch(name) or '..' in name or name.endswith(('/','.lock')) or '// ' in name:
        raise ValueError('branch name must use safe ai/<name> syntax')
    if _git(project,'status','--porcelain','--untracked-files=all','--','.',':(exclude).ai'):
        raise ValueError('working tree must be clean before creating a branch')
    if git(project,'show-ref','--verify','--quiet','refs/heads/'+name).returncode==0:
        raise ValueError('branch already exists')
    base=_git(project,'rev-parse','HEAD')
    _git(project,'switch','-c',name)
    return {'branch':name,'base_head':base,'status':'created','note':'Local branch only; no remote action.'}


def _checks_evidence(project:Path,change_id:str)->str:
    """Require the *latest* executed passing check to match the applied files.

    The .ai records are local integrity hints, NOT tamper-proof attestations.
    """
    _,record=_load_change(project,change_id)
    if record.get('status') not in ('applied','committed'):
        raise ValueError('change is not applied or committed')
    verified=record.get('last_verification')
    if not isinstance(verified,dict) or verified.get('executed') is not True or verified.get('passed') is not True:
        raise ValueError('no executed passing test report tied to this change_id')
    name=verified.get('report')
    if not isinstance(name,str) or not re.fullmatch(r'checks-[0-9a-f]{32}\.json',name):
        raise ValueError('invalid verified test report')
    folder=project/'.ai/reports'
    if not folder.is_dir() or folder.is_symlink():raise ValueError('no valid test reports folder')
    path=folder/name
    if not path.is_file() or path.is_symlink() or path.stat().st_size>500_000:
        raise ValueError('missing or unsafe verified test report')
    raw=path.read_bytes()
    if _hash(raw)!=verified.get('sha256'):
        raise ValueError('test report integrity mismatch')
    obj=json.loads(raw)
    checks=obj.get('checks')
    if (obj.get('workflow_change_id')!=change_id or obj.get('actually_executed') is not True
        or not isinstance(checks,list) or not checks
        or any(not isinstance(c,dict) or c.get('status')!='passed' for c in checks)):
        raise ValueError('verified test report has no passing execution')
    after={f['path']:f['after_sha256'] for f in record['files']}
    if verified.get('source_hashes')!=after or any(not x['unchanged_since_apply'] for x in _drift(project,record)):
        raise ValueError('verified source hashes do not match current change')
    verified_head=verified.get('git_head')
    current_head=_git(project,'rev-parse','HEAD')
    if record.get('status')=='applied' and verified_head is not None and current_head!=verified_head:
        raise ValueError('Git HEAD changed since verification; rerun tests')
    if record.get('status')=='committed' and record.get('git_commit')!=current_head:
        raise ValueError('Git HEAD no longer matches verified committed change')
    return name


def commit(project:Path,change_id:str,message:str,*,approved:bool=False)->dict:
    if not approved:raise ValueError('commit requires explicit --approve')
    project=_root(project)
    if not isinstance(message,str) or not 6<=len(message)<=160 or any(c in message for c in '\r\n\x00'):
        raise ValueError('invalid commit message')
    branch_name=_git(project,'branch','--show-current')
    if not BRANCH_RE.fullmatch(branch_name):raise ValueError('must first switch to an ai/* feature branch')
    _,record=_load_change(project,change_id)
    if record['status']!='applied' or not all(x['unchanged_since_apply'] for x in _drift(project,record)):
        raise ValueError('change has drifted or is not applied')
    report=_checks_evidence(project,change_id)
    paths={f['path'] for f in record['files']}
    if _git(project,'diff','--cached','--name-only'):
        raise ValueError('pre-staged changes are not permitted')
    # All modified/untracked source files must belong to the reviewed manifest.
    entries=git(project,'status','--porcelain','-z','--untracked-files=all','--','.',':(exclude).ai')
    if entries.returncode:raise ValueError('git status failed')
    status_paths=set()
    for row in entries.stdout.split(b'\x00'):
        if not row:continue
        if len(row)<4 or b' -> ' in row:raise ValueError('renamed or malformed Git status refused')
        status_paths.add(os.fsdecode(row[3:]))
    if not status_paths or status_paths!=paths:
        raise ValueError('working tree includes unrelated files or does not match manifest paths')
    for p in sorted(paths):
        if not (project/p).is_file() or (project/p).is_symlink():raise ValueError('source file vanished or became symlink')
    # Git hooks disabled; Git index operations still require a trusted repository.
    hooks=project/'.ai'/'empty-git-hooks';hooks.mkdir(mode=0o700,exist_ok=True)
    if hooks.is_symlink() or any(hooks.iterdir()):raise ValueError('hook override directory is unsafe')
    # Durable intent *before* touching the index: crash recovery can determine
    # whether Git actually committed, without repeating an uncertain commit.
    manifest_path, intent=_load_change(project,change_id)
    if intent.get('commit_transaction',{}).get('state')=='prepared':
        raise ValueError('pending Git commit transaction; run recover-commit first')
    base_head=_git(project,'rev-parse','HEAD')
    intent['commit_transaction']={
        'schema_version':1,'state':'prepared','base_head':base_head,
        'branch':branch_name,'message':message,'verified_report':report,
        'verified_report_sha256':_hash((project/'.ai/reports'/report).read_bytes()),
        'paths':sorted(paths), 'source_hashes':{e['path']:e['after_sha256'] for e in intent['files']},
        'prepared_at':_utc(),
    }
    _json_write(manifest_path,intent)
    _git(project,'-c','core.hooksPath='+str(hooks),'add','--',*sorted(paths))
    _git(project,'-c','core.hooksPath='+str(hooks),'-c','commit.gpgsign=false','commit','-m',message,'--',*sorted(paths))
    head=_git(project,'rev-parse','HEAD')
    # An applied change becomes historical after commit. Future changes to the
    # same files must not make this committed snapshot look like a live drift.
    manifest_path, latest=_load_change(project,change_id)
    if latest.get('status')!='applied':
        raise ValueError('change record changed during Git commit')
    latest['status']='committed'
    latest['committed_at']=_utc()
    latest['git_commit']=head
    latest['commit_transaction']['state']='committed'
    latest['commit_transaction']['commit']=head
    _json_write(manifest_path,latest)
    return {'change_id':change_id,'branch':branch_name,'commit':head,'verified_report':report,
            'status':'committed','note':'Local commit only. No push and no GitHub PR.'}


def draft_pr(project:Path,change_id:str,title:str,*,base:str='main')->dict:
    project=_root(project)
    if not isinstance(title,str) or not 6<=len(title)<=140 or '\n' in title:
        raise ValueError('invalid pull request title')
    if not re.fullmatch(r'[A-Za-z0-9._/-]{1,80}',base) or '..' in base:raise ValueError('invalid base label')
    _,record=_load_change(project,change_id)
    review=code_review(project,change_id)
    verified='not available'
    try:verified=_checks_evidence(project,change_id)
    except ValueError:pass
    branch_name=_git(project,'branch','--show-current')
    head=_git(project,'rev-parse','HEAD')
    paths=[x['path'] for x in record['files']]
    lines=['# '+title,'','## Summary',record['summary'],'','## Changed files',
           *[f'- `{p}`' for p in paths],'','## Verification',f'- Local test evidence: `{verified}`',
           f'- Review findings: {review["counts"]}',
           f'- File hashes still match applied change: {review["all_files_match"]}',
           '','## Git metadata',f'- Feature branch: `{branch_name}`',f'- Intended base: `{base}`',
           f'- HEAD at draft time: `{head}`','','## Reviewer checklist',
           '- [ ] Inspect all changed lines and dependency impact',
           '- [ ] Confirm tests in the target CI environment',
           '- [ ] Review credentials, auth and production changes separately',
           '','> Draft only. No GitHub or GitLab API request was made.']
    out=project/'.ai/pr-drafts'
    if out.is_symlink():raise ValueError('unsafe PR draft directory')
    out.mkdir(mode=0o700,exist_ok=True)
    path=out/(change_id+'.md')
    if path.exists() or path.is_symlink():raise ValueError('PR draft already exists')
    path.write_text('\n'.join(lines)+'\n','utf-8')
    return {'draft':str(path.relative_to(project)),'branch':branch_name,'base':base,
            'review_counts':review['counts'],'published':False}


def main(argv=None):
    p=argparse.ArgumentParser(description='V3.3 local Git collaboration (no remote PR or push)')
    sub=p.add_subparsers(dest='action',required=True)
    for action in ('branch','commit','draft-pr'):
        x=sub.add_parser(action);x.add_argument('--project',required=True)
        if action in ('branch','commit'):x.add_argument('--approve',action='store_true')
        if action in ('branch','commit'):x.add_argument('--worktree-token',help='required for human worktree reservation')
        if action=='branch':x.add_argument('--name',required=True)
        if action!='branch':x.add_argument('--change-id',required=True)
        if action=='commit':x.add_argument('--message',required=True)
        if action=='draft-pr':x.add_argument('--title',required=True);x.add_argument('--base',default='main')
    a=p.parse_args(argv)
    try:
        if a.action=='branch':res=branch(Path(a.project),a.name,approved=a.approve,worktree_token=a.worktree_token)
        elif a.action=='commit':res=commit(Path(a.project),a.change_id,a.message,approved=a.approve,worktree_token=a.worktree_token)
        else:res=draft_pr(Path(a.project),a.change_id,a.title,base=a.base)
        print(json.dumps(res,ensure_ascii=False,indent=2))
    except (OSError,ValueError,json.JSONDecodeError,subprocess.TimeoutExpired) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
