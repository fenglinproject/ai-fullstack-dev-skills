#!/usr/bin/env python3
"""V5.0 side-by-side release installation, upgrade and rollback.

All operations are local. SHA-256 establishes byte integrity, *not* publisher identity.
The operator must independently trust the expected digest or signing public key.
No project code is executed during installation. User data belongs in <home>/workspace.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

MAX_ARCHIVE = 100_000_000
MAX_TOTAL = 200_000_000
MAX_FILE = 50_000_000
MAX_FILES = 5000
NAME = re.compile(r'^ai-fullstack-dev-skills-v(\d+\.\d+)$')
HEX = re.compile(r'^[a-f0-9]{64}$')
RELEASE_ID = re.compile(r'^v\d+\.\d+-[a-f0-9]{16}$')
ILLEGAL_WIN = re.compile(r'[<>:"\\|?*\x00-\x1f]')
RESERVED_WIN = re.compile(r'(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$')


def _hash_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _path_ok(path: str) -> bool:
    if not path or path.startswith('/') or '\\' in path:
        return False
    p=PurePosixPath(path)
    return all(s not in ('', '.', '..') and s == s.rstrip(' .') and not ILLEGAL_WIN.search(s)
               and not RESERVED_WIN.match(s) for s in path.split('/')) and str(p)==path


def _no_symlink_chain(path: Path) -> None:
    """Refuse existing symlinked home/archive path components."""
    for p in (path, *path.parents):
        if p.is_symlink():
            raise ValueError('symlink path component forbidden')


def _ensure_safe_home(home: Path) -> Path:
    home=home.expanduser().absolute()
    _no_symlink_chain(home)
    if home == Path(home.anchor) or len(home.parts) < 3:
        raise ValueError('home must be an explicit non-root path')
    return home


def inspect_archive(archive: Path, expected_sha256: str, *, public_key: Path | None=None,
                    signature: Path | None=None) -> dict:
    if not HEX.fullmatch(expected_sha256):
        raise ValueError('expected-sha256 must be 64 lower-case hex characters')
    _no_symlink_chain(archive.absolute())
    if not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError('archive missing or over size limit')
    digest=_hash_file(archive)
    if digest != expected_sha256:
        raise ValueError('archive SHA-256 mismatch')
    if (public_key is None) != (signature is None):
        raise ValueError('public-key and signature must be supplied together')
    sig_ok=False
    if public_key is not None:
        from tools.supply_chain_v49 import verify_signature
        verify_signature(archive, public_key, signature)
        sig_ok=True
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist()
        if not entries or len(entries) > MAX_FILES+1:
            raise ValueError('invalid member count')
        roots={n.filename.partition('/')[0] for n in entries}
        if len(roots)!=1 or not NAME.fullmatch(next(iter(roots))):
            raise ValueError('unexpected archive root')
        root=roots.pop()
        version=NAME.fullmatch(root).group(1)
        names=[]; total=0
        for e in entries:
            rel=e.filename[len(root)+1:] if e.filename.startswith(root+'/') else ''
            mode=(e.external_attr>>16) & 0o170000
            if (e.is_dir() or not _path_ok(rel) or mode not in (0, stat.S_IFREG)
                    or e.file_size>MAX_FILE):
                raise ValueError('unsafe archive member')
            total+=e.file_size
            if total>MAX_TOTAL:raise ValueError('archive exceeds uncompressed size limit')
            names.append(rel)
        if len({x.casefold() for x in names})!=len(names):
            raise ValueError('duplicate or case-colliding archive paths')
        manifest_name=f'RELEASE_MANIFEST_V{version}.json'
        if manifest_name not in names:raise ValueError('missing versioned release manifest')
        if z.getinfo(root+'/'+manifest_name).file_size>3_000_000:
            raise ValueError('manifest oversized')
        manifest=json.loads(z.read(root+'/'+manifest_name))
        if (not isinstance(manifest,dict) or manifest.get('toolkit_version')!=version
                or manifest.get('schema_version')!=1 or manifest.get('digest_algorithm')!='sha256'
                or not isinstance(manifest.get('files'),list)):
            raise ValueError('invalid release manifest')
        rows=manifest['files']
        if [r.get('path') for r in rows] != sorted(x for x in names if x!=manifest_name):
            raise ValueError('manifest inventory differs from archive')
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'path','bytes','sha256'} or not isinstance(row['bytes'],int) or not HEX.fullmatch(str(row['sha256'])):
                raise ValueError('invalid manifest entry')
            item=z.getinfo(root+'/'+row['path'])
            if item.file_size!=row['bytes']:
                raise ValueError('manifest size mismatch')
            h=hashlib.sha256()
            with z.open(item) as stream:
                for block in iter(lambda:stream.read(65536), b''):h.update(block)
            if h.hexdigest()!=row['sha256']:
                raise ValueError('archive member hash mismatch')
        return {'schema_version':1,'version':version,'release_id':f'v{version}-{digest[:16]}',
                'archive_sha256':digest,'files_verified':len(rows),'signed_with_supplied_key':sig_ok,
                'authenticated_publisher':False,
                'note':'SHA-256 checks bytes, not release identity. A verified signature is trusted only if its public key has been authenticated independently.'}


def _load(home: Path) -> dict | None:
    state_path=home/'.release-manager'/'state.json'
    if not state_path.exists():return None
    _no_symlink_chain(state_path)
    if state_path.stat().st_size>100000:
        raise ValueError('state file oversized')
    data=json.loads(state_path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema_version')!=1 or not isinstance(data.get('releases'),dict) or not isinstance(data.get('history'),list):
        raise ValueError('invalid lifecycle state')
    if not RELEASE_ID.fullmatch(data.get('active','')):
        raise ValueError('invalid active release id')
    if data['active'] not in data['releases']:
        raise ValueError('active release missing from registry')
    if any(not RELEASE_ID.fullmatch(k) or not isinstance(v,dict) or v.get('release_id')!=k or not HEX.fullmatch(v.get('sha256',''))
           for k,v in data['releases'].items()):
        raise ValueError('invalid release registry')
    if any(not RELEASE_ID.fullmatch(x) or x not in data['releases'] for x in data['history']):
        raise ValueError('invalid release history')
    return data


def _atomic_state(home:Path, data:dict) -> None:
    manager=home/'.release-manager'
    name=manager/('state.'+uuid.uuid4().hex+'.tmp')
    try:
        with name.open('x',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2)
            f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,manager/'state.json')
        if os.name=='posix':
            fd=os.open(manager,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
    finally:
        name.unlink(missing_ok=True)


@contextmanager
def _lock(home:Path):
    path=home/'.release-manager'/'operation.lock'
    _no_symlink_chain(path.parent)
    flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0)
    try:fd=os.open(path,flags,0o600)
    except FileExistsError as ex:raise ValueError('lifecycle operation already in progress or interrupted; inspect operation.lock') from ex
    try:
        with os.fdopen(fd,'w') as f:
            f.write(json.dumps({'pid':os.getpid(),'note':'manual investigation required if interrupted'})+'\n')
            f.flush();os.fsync(f.fileno())
        yield
    finally:
        path.unlink(missing_ok=True)


def _launcher_contents() -> str:
    return '''#!/usr/bin/env python3
"""Launch the active installed release only after local integrity checks."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
home=Path(__file__).resolve().parent
record=json.loads((home/'.release-manager'/'state.json').read_text(encoding='utf-8'))
release=record['active']
if not re.fullmatch(r'v\\d+\\.\\d+-[a-f0-9]{16}', release):
    raise SystemExit('invalid active release record')
root=home/'releases'/release
info=record['releases'][release]
manifest=root/('RELEASE_MANIFEST_V'+info['version']+'.json')
if manifest.is_symlink() or not manifest.is_file():
    raise SystemExit('missing or unsafe release manifest')
manifest_bytes=manifest.read_bytes()
if hashlib.sha256(manifest_bytes).hexdigest()!=info['manifest_sha256']:
    raise SystemExit('release manifest integrity mismatch; refusing to execute')
doc=json.loads(manifest_bytes)
if doc.get('toolkit_version')!=info['version']:
    raise SystemExit('release version mismatch')
for row in doc['files']:
    rel=row['path']
    if (not isinstance(rel,str) or rel.startswith('/') or '..' in rel.split('/')
            or '\\\\' in rel):
        raise SystemExit('invalid installed release path')
    file=root/rel
    if (file.is_symlink() or not file.is_file() or file.stat().st_size!=row['bytes']
            or hashlib.sha256(file.read_bytes()).hexdigest()!=row['sha256']):
        raise SystemExit('installed release integrity mismatch; refusing to execute')
app=root/'fullstack.py'
if not app.is_file():raise SystemExit('missing installed application')
raise SystemExit(subprocess.call([sys.executable,str(app),*sys.argv[1:]],cwd=app.parent))
'''


def _installed_integrity(home:Path, release_id:str) -> bool:
    root=home/'releases'/release_id
    _no_symlink_chain(root)
    match=RELEASE_ID.fullmatch(release_id)
    if not match or not root.is_dir():return False
    version=release_id[1:].split('-')[0]
    mf=root/f'RELEASE_MANIFEST_V{version}.json'
    if mf.is_symlink() or not mf.is_file():return False
    try:
        state_path=home/'.release-manager'/'state.json'
        if state_path.is_file():
            active_state=_load(home)
            registry=active_state['releases'].get(release_id,{})
            pinned=registry.get('manifest_sha256')
            if pinned is not None and _hash_file(mf)!=pinned:
                return False
        doc=json.loads(mf.read_text(encoding='utf-8'))
        if doc['toolkit_version']!=version or not isinstance(doc['files'],list):return False
        for row in doc['files']:
            if not _path_ok(row['path']):return False
            p=root/row['path']
            if p.is_symlink() or not p.is_file() or p.stat().st_size!=row['bytes'] or _hash_file(p)!=row['sha256']:
                return False
        return True
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
        return False


def status(home:Path, *, integrity:bool=False) -> dict:
    home=_ensure_safe_home(home)
    state=_load(home) if home.exists() else None
    if state is None:
        return {'installed':False,'home':str(home),'workspace':None}
    active=state['active']
    return {'installed':True,'home':str(home),'active':active,
            'version':state['releases'][active]['version'],
            'release_count':len(state['releases']), 'history':state['history'],
            'workspace':str(home/'workspace'),
            'operation_locked':(home/'.release-manager'/'operation.lock').exists(),
            'active_integrity_ok':_installed_integrity(home,active) if integrity else None,
            'notes':'The external workspace is preserved across upgrades and rollbacks.'}


def plan(home:Path,archive:Path,expected_sha256:str,*,public_key:Path|None=None,signature:Path|None=None) -> dict:
    home=_ensure_safe_home(home)
    data=inspect_archive(archive,expected_sha256,public_key=public_key,signature=signature)
    state=_load(home) if home.exists() else None
    action='install' if state is None else 'upgrade'
    if home.exists() and state is None and list(home.iterdir()):
        raise ValueError('install home must be empty or managed by this tool')
    if state is not None and state['active']==data['release_id']:
        raise ValueError('target release already active')
    return {**data,'planned':True,'action':action,'home':str(home),
            'from_release':state['active'] if state else None,
            'preserves': 'All existing releases and <home>/workspace, without deleting or executing project files'}


def _extract(archive:Path, destination:Path, version:str) -> None:
    root=f'ai-fullstack-dev-skills-v{version}/'
    with zipfile.ZipFile(archive) as z:
        for m in z.infolist():
            rel=m.filename[len(root):]
            target=destination/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(m) as inp, target.open('xb') as out:
                shutil.copyfileobj(inp,out,65536)


def apply(home:Path, archive:Path,expected_sha256:str,*,approve:bool=False,
          public_key:Path|None=None,signature:Path|None=None) -> dict:
    result=plan(home,archive,expected_sha256,public_key=public_key,signature=signature)
    if not approve:return result
    home=_ensure_safe_home(home)
    if not home.exists():home.mkdir(parents=True)
    if not (home/'.release-manager').exists():
        (home/'.release-manager').mkdir()
    (home/'releases').mkdir(exist_ok=True)
    (home/'workspace').mkdir(exist_ok=True)
    for folder in (home/'.release-manager',home/'releases',home/'workspace'):
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError('installation folder must be a real directory')
    with _lock(home):
        snapshot=home/'.release-manager'/('.archive-'+uuid.uuid4().hex+'.zip')
        try:
            with archive.open('rb') as incoming, snapshot.open('xb') as copied:
                shutil.copyfileobj(incoming,copied,1024*1024)
                copied.flush();os.fsync(copied.fileno())
            verified_again=inspect_archive(snapshot,expected_sha256,public_key=public_key,signature=signature)
            if verified_again['release_id'] != result['release_id']:
                raise ValueError('archive changed after planning')
            return _apply_verified_snapshot(home, snapshot, result)
        finally:
            snapshot.unlink(missing_ok=True)

def _apply_verified_snapshot(home:Path, snapshot:Path,result:dict) -> dict:
    state=_load(home)
    if result['action'] != ('install' if state is None else 'upgrade'):
        raise ValueError('lifecycle state changed since plan')
    if state and state['active']!=result['from_release']:
        raise ValueError('active release changed since plan')
    rid=result['release_id']
    dest=home/'releases'/rid
    if dest.exists():
        if not _installed_integrity(home,rid):
            raise ValueError('existing release directory cannot be safely reused')
    else:
        staging=home/'releases'/('.staging-'+uuid.uuid4().hex)
        staging.mkdir()
        try:
            _extract(snapshot,staging,result['version'])
            # Re-hash extracted bytes independently of the validated ZIP.
            manifest=json.loads((staging/f'RELEASE_MANIFEST_V{result["version"]}.json').read_text(encoding='utf-8'))
            for row in manifest['files']:
                file=staging/row['path']
                if file.is_symlink() or not file.is_file() or _hash_file(file)!=row['sha256']:
                    raise ValueError('extracted member integrity check failed')
            os.replace(staging,dest)
        finally:
            if staging.exists():shutil.rmtree(staging)
    if not _installed_integrity(home,rid):
        raise ValueError('installed release integrity check failed')
    if state is None:
        # Generated launcher is deliberately outside the versioned release.
        launcher=home/'launch.py'
        if launcher.exists() or launcher.is_symlink():
            raise ValueError('launcher path exists; refuse to overwrite')
        launcher.write_text(_launcher_contents(),encoding='utf-8')
        state={'schema_version':1,'active':rid,'releases':{},'history':[]}
    manifest_file=dest/f'RELEASE_MANIFEST_V{result["version"]}.json'
    state['releases'][rid]={'release_id':rid,'version':result['version'],
                            'sha256':result['archive_sha256'],
                            'manifest_sha256':_hash_file(manifest_file)}
    state['active']=rid
    state['history'].append(rid)
    _atomic_state(home,state)
    return {'installed':True,'action':result['action'],'active':rid,
        'previous':result['from_release'],'launcher':str(home/'launch.py'),
        'workspace':str(home/'workspace'),
        'source_authenticated':False,'signature_verified_with_supplied_key':result['signed_with_supplied_key']}

def rollback(home:Path,*,approve:bool=False) -> dict:
    home=_ensure_safe_home(home)
    state=_load(home)
    if not state:raise ValueError('no managed installation found')
    previous=next((x for x in reversed(state['history'][:-1]) if x!=state['active']),None)
    if previous is None:raise ValueError('no previous release to roll back to')
    if not _installed_integrity(home,previous):raise ValueError('previous release integrity failed')
    if not approve:return {'planned':True,'action':'rollback','from_release':state['active'],'to_release':previous}
    with _lock(home):
        current=_load(home)
        if current!=state:raise ValueError('installation changed since rollback plan')
        if not _installed_integrity(home,previous):raise ValueError('previous release integrity failed under lock')
        current['active']=previous
        current['history'].append(previous)
        _atomic_state(home,current)
    return {'rolled_back':True,'active':previous,'preserved_workspace':str(home/'workspace')}


def _source_files(source:Path) -> list[Path]:
    if not source.is_dir():raise ValueError('workspace source must be an existing directory')
    files=[];total=0
    for parent,dirs,names in os.walk(source,followlinks=False):
        for d in dirs:
            if (Path(parent)/d).is_symlink():raise ValueError('workspace contains symlink')
        for n in names:
            file=Path(parent)/n
            if file.is_symlink():raise ValueError('workspace contains symlink')
            if not file.is_file():raise ValueError('workspace contains unsafe file')
            total+=file.stat().st_size
            if total>MAX_TOTAL:raise ValueError('workspace exceeds import size cap')
            files.append(file)
            if len(files)>MAX_FILES:raise ValueError('workspace contains too many files')
    return files


def import_workspace(home:Path,source:Path,name:str,*,approve:bool=False) -> dict:
    home=_ensure_safe_home(home)
    source=source.expanduser().absolute()
    _no_symlink_chain(source)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',name):
        raise ValueError('workspace name is invalid')
    if not _load(home):raise ValueError('install a managed release first')
    dest=home/'workspace'/name
    if dest.exists() or dest.is_symlink():raise ValueError('workspace destination already exists')
    if source==home or source in home.parents or home in source.parents:
        raise ValueError('workspace source must be outside the installation home')
    _no_symlink_chain(home/'workspace')
    files=_source_files(source)
    if not approve:
        return {'planned':True,'action':'import-workspace','source':str(source),
                'destination':str(dest),'files':len(files),'does_not_modify_source':True}
    with _lock(home):
        if dest.exists():raise ValueError('workspace destination already exists')
        staging=home/'workspace'/('.staging-'+uuid.uuid4().hex)
        staging.mkdir()
        try:
            for file in files:
                rel=file.relative_to(source)
                target=staging/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                # Source files may contain secrets: preserve privately, do not inspect contents.
                fd=os.open(file,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
                try:
                    metadata=os.fstat(fd)
                    if not stat.S_ISREG(metadata.st_mode):raise ValueError('workspace source changed type')
                    with os.fdopen(fd,'rb',closefd=False) as inp, target.open('xb') as out:
                        shutil.copyfileobj(inp,out,65536)
                finally:
                    os.close(fd)
            os.replace(staging,dest)
        finally:
            if staging.exists():shutil.rmtree(staging)
    return {'imported':True,'destination':str(dest),'files':len(files),'source_preserved':True}
