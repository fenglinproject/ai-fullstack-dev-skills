#!/usr/bin/env python3
"""V4.6 recoverable prepared source edits and uncertain local Git commits.

All inspections are read-only by default. Approval modifies ONLY local .ai
records or restores hash-matched files. Recovery never resets Git, stages,
commits, pushes, or replaces user edits made after an interrupted operation.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

from orchestrator.cli import _task_lock
from orchestrator.write_guard_v46 import write_guard
from orchestrator.workflow import (_load_change, _hash, _json_write, _atomic_bytes,
                                   _utc, safe_relative)
from orchestrator.git_collab import _root, _git
from orchestrator.git_review import git


def inspect_prepared(project: Path, change_id: str) -> dict:
    project=Path(project).resolve(strict=True)
    _, record=_load_change(project,change_id)
    if record.get('status')!='prepared':
        raise ValueError('source recovery only supports an interrupted prepared change')
    statuses=[];blocked=[];restore_bytes={}
    files=record.get('files')
    if not isinstance(files,list) or not 1<=len(files)<=20:
        raise ValueError('invalid interrupted change file list')
    for item in files:
        if not isinstance(item,dict) or item.get('action') not in ('create','replace'):
            raise ValueError('invalid recovery file metadata')
        rel=item.get('path')
        path=safe_relative(project,rel,allow_missing=True)
        expected_after=item.get('after_sha256')
        expected_before=item.get('before_sha256')
        if not isinstance(expected_after,str) or not re.fullmatch(r'[a-f0-9]{64}',expected_after):
            raise ValueError('invalid recovery target hash')
        old=None
        if item['action']=='replace':
            if not isinstance(expected_before,str) or not re.fullmatch(r'[a-f0-9]{64}',expected_before):
                raise ValueError('invalid recovery backup hash')
            try:old=base64.b64decode(item.get('backup_base64'),validate=True)
            except (ValueError,TypeError) as exc:raise ValueError('corrupt interrupted backup') from exc
            if len(old)>256*1024 or _hash(old)!=expected_before:
                raise ValueError('interrupted backup integrity mismatch')
        elif expected_before is not None or item.get('backup_base64') is not None:
            raise ValueError('unexpected backup for created file')
        current=_hash(path.read_bytes()) if path.is_file() else None
        if item['action']=='create':
            state='after' if current==expected_after else 'before' if current is None else 'drift'
        else:
            state='after' if current==expected_after else 'before' if current==expected_before else 'drift'
        if state=='drift':blocked.append(rel)
        statuses.append({'path':rel,'state':state})
        restore_bytes[rel]=old
    return {'change_id':change_id,'status':'prepared','files':statuses,
            'safe_to_restore':not blocked, 'blockers':blocked,
            'note':'No source bytes shown; file hashes are compared before any rollback.'}


def recover_prepared(project:Path,change_id:str,*,approved:bool=False,
                     worktree_token:str|None=None)->dict:
    project=Path(project).resolve(strict=True)
    if not approved:
        return inspect_prepared(project,change_id)
    with write_guard(project,token=worktree_token), _task_lock(project):
        state=inspect_prepared(project,change_id)
        if not state['safe_to_restore']:
            raise ValueError('files changed outside interrupted operation; refuse recovery')
        path,manifest=_load_change(project,change_id)
        bypath={f['path']:f for f in manifest['files']}
        # All backups were validated during preflight; no writes unless every
        # file is still exactly its before/after hash. File operations are
        # idempotent; a second interruption can be diagnosed and retried.
        for entry in reversed(state['files']):
            if entry['state']=='before':continue
            item=bypath[entry['path']]
            dest=safe_relative(project,entry['path'],allow_missing=True)
            if item['action']=='create':
                dest.unlink()
            else:
                raw=base64.b64decode(item['backup_base64'],validate=True)
                _atomic_bytes(dest,raw)
        manifest['status']='aborted'
        manifest['recovered_at']=_utc()
        manifest['recovery_kind']='prepared_rollback'
        _json_write(path,manifest)
        return {'change_id':change_id,'status':'aborted','source_rollback':True,
                'files_checked':len(state['files'])}


def inspect_commit(project:Path,change_id:str)->dict:
    project=_root(Path(project))
    _,record=_load_change(project,change_id)
    txn=record.get('commit_transaction')
    if (record.get('status')!='applied' or not isinstance(txn,dict)
            or txn.get('schema_version')!=1 or txn.get('state')!='prepared'):
        raise ValueError('no pending Git commit transaction')
    base=txn.get('base_head')
    if not isinstance(base,str) or not re.fullmatch(r'[a-f0-9]{40,64}',base):
        raise ValueError('invalid commit transaction baseline')
    if txn.get('branch')!=_git(project,'branch','--show-current'):
        raise ValueError('feature branch changed since commit preparation')
    if txn.get('source_hashes')!={x['path']:x['after_sha256'] for x in record['files']}:
        raise ValueError('commit transaction file list mismatch')
    report=txn.get('verified_report')
    if not isinstance(report,str) or not re.fullmatch(r'checks-[0-9a-f]{32}\.json',report):
        raise ValueError('invalid commit verification pointer')
    report_path=project/'.ai/reports'/report
    if (report_path.is_symlink() or not report_path.is_file() or
            _hash(report_path.read_bytes())!=txn.get('verified_report_sha256')):
        raise ValueError('commit verification evidence changed')
    index=_git(project,'diff','--cached','--name-only')
    if index:raise ValueError('Git index has staged changes; manual recovery required')
    head=_git(project,'rev-parse','HEAD')
    if head==base:
        # A pending prepared transaction might have staged and then unstaged,
        # but its commit definitely was not added to this branch's HEAD.
        return {'change_id':change_id,'state':'not_committed','recoverable':True,
                'note':'Git HEAD unchanged; only clears the prepared transaction.'}
    parents=_git(project,'rev-list','--parents','-n','1',head).split()
    if len(parents)!=2 or parents[1]!=base:
        raise ValueError('commit parent no longer matches prepared baseline')
    message=_git(project,'log','-1','--format=%B',head)
    if message!=txn.get('message'):
        raise ValueError('commit message differs from recorded intent')
    if set(txn.get('paths',[]))!=set(txn['source_hashes']):
        raise ValueError('commit path manifest mismatch')
    for rel,digest in txn['source_hashes'].items():
        safe_relative(project,rel,allow_missing=True)
        obj=git(project,'show',f'{head}:{rel}',max_bytes=300_000)
        if obj.returncode or _hash(obj.stdout)!=digest:
            raise ValueError('Git commit tree does not match reviewed source')
    if _git(project,'status','--porcelain','--untracked-files=all','--','.',':(exclude).ai'):
        raise ValueError('working tree changed since interrupted commit')
    return {'change_id':change_id,'state':'committed_unrecorded','recoverable':True,
            'commit':head,'note':'Validated local Git commit; no new commit will be created.'}


def recover_commit(project:Path,change_id:str,*,approved:bool=False,
                   worktree_token:str|None=None)->dict:
    project=Path(project).resolve(strict=True)
    if not approved:return inspect_commit(project,change_id)
    with write_guard(project,token=worktree_token),_task_lock(project):
        state=inspect_commit(project,change_id)
        path,record=_load_change(project,change_id)
        if state['state']=='not_committed':
            record['commit_transaction']['state']='no_commit'
        else:
            record['status']='committed'
            record['committed_at']=_utc()
            record['git_commit']=state['commit']
            record['commit_transaction']['state']='committed'
            record['commit_transaction']['commit']=state['commit']
        record['commit_transaction']['reconciled_at']=_utc()
        _json_write(path,record)
        return {'change_id':change_id,'status':record['status'],
                'resolution':state['state'],'git_commit':record.get('git_commit')}


def main(argv=None):
    p=argparse.ArgumentParser(description='V4.6 read-only diagnosis or approved interruption recovery')
    sub=p.add_subparsers(dest='action',required=True)
    for action in ('prepared','commit'):
        q=sub.add_parser(action)
        q.add_argument('--project',required=True,type=Path)
        q.add_argument('--change-id',required=True)
        q.add_argument('--approve',action='store_true')
        q.add_argument('--worktree-token',help='required if a manual worktree reservation exists')
    a=p.parse_args(argv)
    try:
        result=(recover_prepared(a.project,a.change_id,approved=a.approve,worktree_token=a.worktree_token)
            if a.action=='prepared' else recover_commit(a.project,a.change_id,approved=a.approve,worktree_token=a.worktree_token))
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as ex:
        p.exit(2,f'error: {ex}\n')
if __name__=='__main__':raise SystemExit(main())
