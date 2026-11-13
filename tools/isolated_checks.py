#!/usr/bin/env python3
"""Opt-in Docker-based check runner; no host execution of project test code.

Requires an independently secured Docker daemon and a trusted pinned image. A
Docker container reduces exposure; it is NOT a VM or a guarantee of containment.
No Docker invocation occurs in preview mode. Never run this against a privileged
Docker daemon exposed to untrusted users.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from tools.run_checks import validate_check
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.run_checks import validate_check

SKIP_DIR={'.git','.ai','node_modules','.venv','venv','__pycache__','dist','build','.next','coverage','.pytest_cache'}
SECRET_NAMES={'.env','.npmrc','.pypirc','id_rsa','id_ed25519','credentials.json','secrets.json'}
SECRET_STEMS={'credentials','secrets','private_key','access_token','api_key'}
SECRET_SUFFIX={'.pem','.key','.p12','.pfx','.sqlite','.sqlite3','.db'}
MAX_FILES=5000
MAX_FILE_BYTES=2*1024*1024
MAX_TOTAL_BYTES=32*1024*1024
IMAGE_PATTERN=re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._/:@-]*@sha256:[0-9a-f]{64}$')


def check_image(image:str)->str:
    if not isinstance(image,str) or not IMAGE_PATTERN.fullmatch(image):
        raise ValueError('image must be pinned by immutable @sha256:<64 lowercase hex> digest')
    return image


def snapshot(project:Path,destination:Path)->dict:
    """Copy only regular nonsecret files to a capped temporary directory."""
    project=project.resolve(strict=True)
    if not project.is_dir() or project==Path('/'):
        raise ValueError('invalid project directory')
    files=0;size=0;skipped=0
    for base,dirs,names in os.walk(project,followlinks=False):
        source=Path(base)
        dirs[:]=sorted(d for d in dirs if d not in SKIP_DIR and not d.startswith('.'))
        for d in dirs:
            if (source/d).is_symlink():raise ValueError('source symlinks are forbidden in isolated snapshot')
        for name in sorted(names):
            path=source/name
            if path.is_symlink():raise ValueError('source symlinks are forbidden in isolated snapshot')
            if (name.startswith('.') or name.casefold() in SECRET_NAMES or path.stem.casefold() in SECRET_STEMS or path.suffix.lower() in SECRET_SUFFIX):
                skipped+=1;continue
            if not path.is_file():raise ValueError('only regular source files supported')
            stat=path.stat()
            if stat.st_size>MAX_FILE_BYTES:raise ValueError('oversized source file in snapshot')
            files+=1;size+=stat.st_size
            if files>MAX_FILES or size>MAX_TOTAL_BYTES:raise ValueError('snapshot file/byte limit exceeded')
            rel=path.relative_to(project)
            target=destination/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
            target.chmod(0o644)
    for base,dirs,_ in os.walk(destination):
        Path(base).chmod(0o755)
    return {'files':files,'bytes':size,'skipped_files':skipped}


def docker_command(check:dict,project:Path,snap:Path,image:str)->list[str]:
    args,_=validate_check(check,project)
    check_image(image)
    cwd=(project/check.get('cwd','.')).resolve().relative_to(project.resolve())
    entry='python' if args[0] in ('python','python3') else 'node'
    # Re-check selected files/directories are actually included in the snapshot.
    validate_check(check,snap)
    workdir='/workspace'+(('/'+cwd.as_posix()) if cwd.parts else '')
    return ['docker','run','--rm','--network','none','--read-only',
       '--cap-drop','ALL','--security-opt','no-new-privileges','--pull','never',
       '--pids-limit','64','--memory','256m','--cpus','1',
       '--user','65534:65534','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
       '--mount',f'type=bind,src={snap},dst=/workspace,readonly',
       '--workdir',workdir,'--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1',
       '--entrypoint',entry,image,*args[1:]]


def run(project:Path, image:str, *, execute:bool=False, name:str|None=None)->dict:
    project=project.resolve(strict=True)
    check_image(image)
    config=project/'.ai/checks.json'
    if config.is_symlink():raise ValueError('checks config symlink not permitted')
    checks=json.loads(config.read_text('utf-8'))['checks']
    if not isinstance(checks,list):raise ValueError('checks must be a list')
    selected=[c for c in checks if name is None or c.get('name')==name]
    if name and not selected:raise ValueError('unknown check name')
    reports=[]
    with tempfile.TemporaryDirectory(prefix='ai-check-snapshot-') as work:
        snap=Path(work)/'source';snap.mkdir()
        stats=snapshot(project,snap)
        for c in selected:
            args,timeout=validate_check(c,project)
            command=docker_command(c,project,snap,image)
            entry={'name':c.get('name','unnamed'),'status':'planned_only','runner':'docker',
                   'command':command[:command.index('--entrypoint')]+['--entrypoint',command[command.index('--entrypoint')+1],'<pinned-image>',*args[1:]]}
            # Reports expose only image placeholder; image digest recorded separately.
            if not c.get('enabled',False):entry['status']='disabled'
            elif execute:
                if shutil.which('docker') is None:raise ValueError('Docker CLI not installed; no test was executed')
                clean={k:v for k,v in os.environ.items() if k in ('PATH','SYSTEMROOT','WINDIR','LANG','LC_ALL')}
                clean['DOCKER_CONFIG']=str(Path(work)/'no-docker-auth')
                try:
                    r=subprocess.run(command,timeout=min(timeout+12,132),capture_output=True,
                                     text=True,errors='replace',check=False,env=clean)
                    entry.update(status='passed' if r.returncode==0 else 'failed',exit_code=r.returncode,
                                 stdout_tail=r.stdout[-2000:],stderr_tail=r.stderr[-2000:])
                except subprocess.TimeoutExpired:entry['status']='timeout'
            reports.append(entry)
    return {'schema_version':1,'runner':'docker','image':image,'actually_executed':execute,
            'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),'snapshot':stats,'checks':reports,
            'summary':{k:sum(c['status']==k for c in reports) for k in ('passed','failed','timeout','disabled','planned_only')},
            'security_note':'No host test execution. Docker isolation is not a guarantee; trust your daemon and image. No network, caps or host write mount.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Opt-in Docker snapshot test runner')
    p.add_argument('--project',required=True)
    p.add_argument('--image',required=True,help='trusted image reference pinned by sha256 digest')
    p.add_argument('--name')
    p.add_argument('--run',action='store_true',help='explicitly permit Docker test execution')
    a=p.parse_args(argv)
    try:print(json.dumps(run(Path(a.project),a.image,execute=a.run,name=a.name),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
