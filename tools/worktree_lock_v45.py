#!/usr/bin/env python3
"""Shared Git common-dir advisory writer lease across linked worktrees.

Voluntary coordination for tools that opt in; not a mandatory OS or Git lock.
No automatic stale lock stealing. Lock owner must explicitly release its token.
"""
from __future__ import annotations
import argparse, json, os, re, secrets, subprocess, time
from pathlib import Path
from tools.repo_readiness_v44 import repository_root, _git_text
from orchestrator.write_guard_v46 import write_guard, serialized

TOKEN=re.compile(r'[0-9a-f]{64}\Z')
NAME='ai-fullstack-v45-write.lock'

def _location(project:Path)->Path:
    root=repository_root(project)
    common=Path(_git_text(root,'rev-parse','--path-format=absolute','--git-common-dir')).resolve(strict=True)
    if not common.is_dir() or common.is_symlink():raise ValueError('invalid shared git dir')
    return common/NAME

def status(project:Path)->dict:
    path=_location(project)
    if not path.exists() and not path.is_symlink():return {'locked':False}
    if path.is_symlink() or not path.is_file():raise ValueError('unsafe lock file')
    raw=path.read_bytes()
    if len(raw)>4096:raise ValueError('oversized lock')
    try:data=json.loads(raw)
    except (UnicodeError,json.JSONDecodeError) as e:raise ValueError('corrupt lock; manual inspection required') from e
    if not isinstance(data,dict) or data.get('schema_version')!=1 or not TOKEN.fullmatch(str(data.get('token',''))):
        raise ValueError('corrupt lock; manual inspection required')
    return {'locked':True,'created_at':data.get('created_at'),'note':'Advisory lock only; token deliberately hidden.'}

def acquire(project:Path,*,approved:bool=False)->dict:
    with write_guard(project, reservation_admin=True):
        return _acquire_locked(project,approved=approved)

def _acquire_locked(project:Path,*,approved:bool=False)->dict:
    if not approved:raise ValueError('explicit --approve required for lock acquisition')
    path=_location(project)
    value={'schema_version':1,'token':secrets.token_hex(32),'created_at':int(time.time())}
    payload=(json.dumps(value,separators=(',',':'))+'\n').encode()
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as e:raise ValueError('a worktree write reservation already exists') from e
    try:
        with os.fdopen(fd,'wb') as out:
            out.write(payload);out.flush();os.fsync(out.fileno())
    except BaseException:
        path.unlink(missing_ok=True);raise
    return {'acquired':True,'release_token':value['token'],
            'note':'Store token securely; separate worktrees share this advisory lock; lock is not an automatic code-write enforcement mechanism.'}

def release(project:Path,token:str)->dict:
    with write_guard(project, reservation_admin=True):
        return _release_locked(project,token)

def _release_locked(project:Path,token:str)->dict:
    if not isinstance(token,str) or not TOKEN.fullmatch(token):raise ValueError('invalid release token')
    path=_location(project)
    if path.is_symlink() or not path.is_file():raise ValueError('lock not present or unsafe')
    # Avoid a read-then-unlink race with another process that replaced the file.
    fd=os.open(path,os.O_RDONLY | getattr(os,'O_NOFOLLOW',0))
    try:
        st=os.fstat(fd)
        if st.st_size>4096:raise ValueError('invalid lock size')
        data=json.loads(os.read(fd,4097))
        if not isinstance(data,dict) or data.get('token')!=token:raise ValueError('incorrect lock token')
        cur=path.stat(follow_symlinks=False)
        if (cur.st_dev,cur.st_ino)!=(st.st_dev,st.st_ino):raise ValueError('lock changed during release')
        path.unlink()
    finally:os.close(fd)
    return {'released':True}

def main(argv=None):
    p=argparse.ArgumentParser(description='Advisory writer reservation across Git worktrees')
    p.add_argument('action',choices=('status','acquire','release'));p.add_argument('--project',required=True,type=Path)
    p.add_argument('--approve',action='store_true');p.add_argument('--token')
    a=p.parse_args(argv)
    try:
        data=status(a.project) if a.action=='status' else acquire(a.project,approved=a.approve) if a.action=='acquire' else release(a.project,a.token)
        print(json.dumps(data,indent=2));return 0
    except (ValueError,OSError,subprocess.TimeoutExpired) as ex:p.exit(2,f'error: {ex}\n')
if __name__=='__main__':raise SystemExit(main())
