#!/usr/bin/env python3
"""Auditable, opt-in dependency graph snapshots/deltas built from V3.7 AST index.

No source execution/network. Snapshots are *untrusted local metadata*; only local
module resolution, never proof of a complete runtime dependency graph.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
from collections import deque
from pathlib import Path
try:
    from tools.incremental_index import build
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import build

CACHE = 'dependency_graph_v38.json'
MAX_SNAPSHOT = 8*1024*1024


def _cache_path(root:Path)->Path:
    path = root/'.ai'/'cache'/CACHE
    for item in (root/'.ai',root/'.ai'/'cache',path):
        if item.is_symlink():
            raise ValueError('unsafe symlink graph cache')
    return path


def snapshot(index:dict)->dict:
    files=index['files']
    return {'schema_version':1,'root':index['root'],
            'edges':{p:sorted(set(r['dependencies'])) for p,r in sorted(files.items())},
            'sha256':{p:r['sha256'] for p,r in sorted(files.items())},
            'configuration_warnings':list(index.get('project_config_warnings',[])),
            'uncertain_files':sorted(p for p,r in files.items()
                if r.get('parse_errors') or r.get('dynamic_imports') or r.get('unresolved_local_imports'))}


def _load(root:Path)->dict|None:
    p = _cache_path(root)
    if not p.exists():return None
    if not p.is_file() or p.stat().st_size > MAX_SNAPSHOT:
        raise ValueError('invalid graph cache')
    try:
        result=json.loads(p.read_text('utf-8'))
    except (UnicodeError,json.JSONDecodeError):
        return None
    if (not isinstance(result,dict) or result.get('schema_version') != 1
            or result.get('root') != str(root)):
        return None
    edges=result.get('edges'); hashes=result.get('sha256')
    if not isinstance(edges,dict) or not isinstance(hashes,dict):return None
    # Cache data must not influence filesystem access; validate all paths and neighbors.
    def valid(p):
        return isinstance(p,str) and p and not p.startswith('/') and '\\' not in p and '..' not in p.split('/')
    if any(not valid(k) or not isinstance(v,list) or len(v)>2000 or any(not valid(d) for d in v)
           for k,v in edges.items()):return None
    if any(not valid(k) or not isinstance(v,str) or len(v)!=64 for k,v in hashes.items()):return None
    return result


def _write(root:Path,data:dict)->None:
    dest=_cache_path(root)
    dest.parent.mkdir(parents=True,exist_ok=True)
    _cache_path(root)
    fd,tmp=tempfile.mkstemp(prefix='.graph-',dir=dest.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            os.fchmod(f.fileno(),0o600)
            json.dump(data,f,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            f.flush();os.fsync(f.fileno())
        if os.stat(tmp).st_size > MAX_SNAPSHOT:
            raise ValueError('graph cache exceeds max size')
        _cache_path(root)
        os.replace(tmp,dest)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def compare(previous:dict|None,current:dict, *, changed:list[str]|None=None,max_depth:int=30)->dict:
    if not 1<=max_depth<=30:raise ValueError('depth 1..30')
    old_edges=(previous or {}).get('edges',{})
    old_hashes=(previous or {}).get('sha256',{})
    new_edges=current['edges'];new_hashes=current['sha256']
    changed_files=sorted(p for p in new_hashes if old_hashes.get(p)!=new_hashes[p])
    deleted_files=sorted(set(old_hashes)-set(new_hashes))
    changed_files += deleted_files
    seeds=sorted(set(changed if changed is not None else changed_files))
    if (len(seeds)>1000 or any(not isinstance(s,str) or s.startswith('/') or '..' in s.split('/') or '\\' in s for s in seeds)):
        raise ValueError('invalid changed file paths')
    edges_added=[];edges_removed=[]
    for path in sorted(set(old_edges)|set(new_edges)):
        before=set(old_edges.get(path,[]));after=set(new_edges.get(path,[]))
        edges_added.extend([path,d] for d in sorted(after-before))
        edges_removed.extend([path,d] for d in sorted(before-after))
    reverse={}
    for edges in (old_edges,new_edges):
        for src,deps in edges.items():
            for dep in deps:reverse.setdefault(dep,set()).add(src)
    queue=deque((s,0) for s in seeds)
    seen=set(seeds); affected=[]; truncated=False
    while queue:
        node,depth=queue.popleft()
        parents=sorted(reverse.get(node,()))
        if depth>=max_depth:
            if any(parent not in seen for parent in parents):truncated=True
            continue
        for parent in parents:
            if parent not in seen:
                seen.add(parent);affected.append({'path':parent,'depth':depth+1,'via':node})
                queue.append((parent,depth+1))
    unknown=[p for p in seeds if p not in old_hashes and p not in new_hashes]
    warnings=[]
    if previous is None:warnings.append('no-previous-graph-snapshot')
    if unknown:warnings.append('unknown-changed-files')
    if truncated:warnings.append('dependency-depth-limit')
    if current.get('uncertain_files'):warnings.append('unresolved-or-dynamic-imports')
    if current.get('configuration_warnings'):warnings.append('incomplete-project-configuration')
    return {'schema_version':1,'indexed_files':len(new_hashes),
            'changed_or_deleted_files':sorted(set(changed_files)),
            'files_added':sorted(set(new_hashes)-set(old_hashes)),
            'files_deleted':deleted_files,'edges_added':edges_added,'edges_removed':edges_removed,
            'affected_dependents':affected,'caution_flags':warnings,'full_suite_required':bool(warnings),
            'note':'Only static candidate impacts. Previous snapshot is untrusted metadata, not a release gate; full tests required.'}


def analyze(project:Path, *,save:bool=False,changed:list[str]|None=None)->dict:
    root=project.resolve(strict=True)
    old=_load(root)
    index=build(root,use_cache=True,save_cache=save)
    now=snapshot(index)
    result=compare(old,now,changed=changed)
    result['index_stats']=index['stats']
    result['workspaces']=[x['name'] for x in index['workspace']['packages']]
    if save:_write(root,now)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description='Offline AST dependency graph deltas; no project code executed')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--save',action='store_true',help='opt-in local graph/index snapshot writes')
    p.add_argument('--changed',nargs='*')
    a=p.parse_args(argv)
    try:print(json.dumps(analyze(a.project,save=a.save,changed=a.changed),ensure_ascii=False,indent=2))
    except (ValueError,OSError,RuntimeError) as e:p.exit(2,'error: '+str(e)+'\n')
if __name__=='__main__':main()
