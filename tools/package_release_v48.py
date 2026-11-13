#!/usr/bin/env python3
"""Deterministic release packager and strict per-file ZIP verifier (unsigned SHA-256)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = 'ai-fullstack-dev-skills-v4.8'
MANIFEST = 'RELEASE_MANIFEST_V4.8.json'
ZIP_NAME = NAME + '.zip'
IGNORE_PARTS = {'.git', '.ai', '__pycache__', 'node_modules', '.venv', 'dist',
                '.pytest_cache', '.mypy_cache', '.next'}
MAX_MEMBERS = 5000
MAX_FILE_BYTES = 50_000_000
MAX_TOTAL_BYTES = 200_000_000


def is_distributable(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if path.is_symlink() or any(p in IGNORE_PARTS for p in parts):
        return False
    if parts[0] == 'benchmarks' and len(parts) > 1 and parts[1] == 'reports':
        return False
    if parts[-1].startswith('.env') and parts[-1] not in ('.env.example',):
        return False
    if parts[-1].endswith(('.pyc','.pyo','.log','.tmp','.sqlite','.sqlite3')):
        return False
    return True


def files_to_release() -> list[Path]:
    out=[]
    for parent, dirs, names in os.walk(ROOT, followlinks=False):
        root=Path(parent)
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_PARTS
                         and not (root == ROOT/'benchmarks' and d == 'reports'))
        for d in dirs:
            if (root / d).is_symlink():
                raise ValueError('source directory contains an unsafe symlink')
        for name in names:
            path=root/name
            if path.is_symlink():
                raise ValueError('source includes symbolic link: '+str(path.relative_to(ROOT)))
            if is_distributable(path) and name != MANIFEST:
                if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
                    raise ValueError('invalid or oversized source file')
                out.append(path)
    return sorted(out, key=lambda x:x.relative_to(ROOT).as_posix())


def manifest_for(paths: list[Path]) -> dict:
    rows=[]
    for path in paths:
        blob=path.read_bytes()
        rows.append({'path':path.relative_to(ROOT).as_posix(),
                     'bytes':len(blob), 'sha256':hashlib.sha256(blob).hexdigest()})
    if len(rows) > MAX_MEMBERS or sum(r['bytes'] for r in rows)>MAX_TOTAL_BYTES:
        raise ValueError('release size budget exceeded')
    return {'schema_version':1, 'toolkit_version':'4.8',
            'digest_algorithm':'sha256', 'signed':False, 'files':rows,
            'note':'Integrity checks detect accidental changes; hashes are not digital signatures.'}


def _info(rel: str) -> zipfile.ZipInfo:
    info=zipfile.ZipInfo(NAME + '/' + rel, date_time=(1980,1,1,0,0,0))
    info.create_system=3
    info.external_attr=(stat.S_IFREG | 0o644)<<16
    info.compress_type=zipfile.ZIP_DEFLATED
    return info


def make_package(output: Path) -> dict:
    if output.name != ZIP_NAME:
        raise ValueError('output name must match release version')
    if output.exists() or output.is_symlink() or output.parent.is_symlink():
        raise ValueError('refusing to replace release output or use symlink directory')
    if not output.parent.is_dir():
        raise ValueError('release output directory must already exist')
    sidecar=output.with_suffix(output.suffix+'.sha256')
    if sidecar.exists() or sidecar.is_symlink():
        raise ValueError('refusing to replace existing checksum file')
    paths=files_to_release()
    manifest=manifest_for(paths)
    manifest_path=ROOT/MANIFEST
    if manifest_path.is_symlink():
        raise ValueError('invalid manifest file')
    manifest_bytes=(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    manifest_path.write_bytes(manifest_bytes)
    flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(os.open(output, flags, 0o600), 'wb') as target:
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in paths:
                z.writestr(_info(path.relative_to(ROOT).as_posix()), path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            z.writestr(_info(MANIFEST), manifest_bytes, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        target.flush()
        os.fsync(target.fileno())
    result=verify_package(output)
    sidecar=output.with_suffix(output.suffix+'.sha256')
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    with os.fdopen(os.open(sidecar, flags, 0o600), 'w') as f:
        f.write(digest+'  '+output.name+'\n')
    return {**result, 'archive_sha256':digest, 'checksum_file':str(sidecar)}


def verify_package(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError('invalid archive file')
    try:
        z=zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ValueError('not a valid zip file') from exc
    with z:
        members=z.infolist()
        if len(members)>MAX_MEMBERS+1 or not members:
            raise ValueError('invalid member count')
        names=[]
        for m in members:
            if m.is_dir() or m.file_size>MAX_FILE_BYTES or (m.external_attr>>16)&0o170000 != stat.S_IFREG:
                raise ValueError('unexpected archive entry')
            if not m.filename.startswith(NAME+'/'):
                raise ValueError('archive root directory mismatch')
            rel=m.filename[len(NAME)+1:]
            if not rel or rel.startswith('/') or '\\' in rel or any(x in ('','..','.') for x in rel.split('/')):
                raise ValueError('unsafe archive entry path')
            names.append(rel)
        if len(names)!=len(set(names)) or MANIFEST not in names:
            raise ValueError('missing manifest or duplicate members')
        info=z.getinfo(NAME+'/'+MANIFEST)
        if info.file_size>MAX_FILE_BYTES:
            raise ValueError('oversized manifest')
        manifest=json.loads(z.read(info))
        if (set(manifest)!={'schema_version','toolkit_version','digest_algorithm','signed','files','note'}
                or manifest['schema_version']!=1 or manifest['toolkit_version']!='4.8'
                or manifest['digest_algorithm']!='sha256' or manifest['signed'] is not False
                or not isinstance(manifest['files'],list)):
            raise ValueError('invalid manifest metadata')
        rows=manifest['files']
        if [r['path'] for r in rows] != sorted(x for x in names if x!=MANIFEST):
            raise ValueError('manifest files do not match archive')
        if sum(m.file_size for m in members)>MAX_TOTAL_BYTES:
            raise ValueError('archive uncompressed size budget exceeded')
        for row in rows:
            if set(row)!={'path','sha256','bytes'}:
                raise ValueError('bad manifest file record')
            member=z.getinfo(NAME+'/'+row['path'])
            if row['bytes']!=member.file_size:
                raise ValueError('archive size mismatch: '+row['path'])
            h=hashlib.sha256()
            with z.open(member) as f:
                while True:
                    chunk=f.read(65536)
                    if not chunk:break
                    h.update(chunk)
            if h.hexdigest()!=row['sha256']:
                raise ValueError('archive digest mismatch: '+row['path'])
        return {'schema_version':1,'toolkit_version':'4.8','archive':path.name,
                'verified_integrity':True,'signed':False,'files_verified':len(rows),
                'archive_bytes':path.stat().st_size}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='cmd', required=True)
    pkg=sub.add_parser('create')
    pkg.add_argument('--output',type=Path,required=True)
    pkg.add_argument('--execute',action='store_true')
    check=sub.add_parser('verify')
    check.add_argument('--archive',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.cmd=='verify':result=verify_package(args.archive)
        elif args.execute:result=make_package(args.output)
        else:result={'planned':True,'output':str(args.output),'files':len(files_to_release())}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile,json.JSONDecodeError) as exc:
        p.error(str(exc))


if __name__=='__main__':raise SystemExit(main())
