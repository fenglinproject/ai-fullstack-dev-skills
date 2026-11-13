#!/usr/bin/env python3
"""V3.7 content-hash incremental Python and TypeScript/JavaScript AST index.

Indexes *locations and import hints*, not source content. Reads project code
only, does not execute it, and never sends files to a model or network.
Cache writes are opt-in and limited to .ai/cache; symlinks are rejected.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from tools.context_retrieval import SKIP_DIRS, SENSITIVE_NAMES, SENSITIVE_TEXT
    from tools.ast_symbols import _Visitor
    from tools.monorepo_workspace import discover
    from tools.project_config import inspect as inspect_project_config
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.context_retrieval import SKIP_DIRS, SENSITIVE_NAMES, SENSITIVE_TEXT
    from tools.ast_symbols import _Visitor
    from tools.monorepo_workspace import discover
    from tools.project_config import inspect as inspect_project_config

SUFFIXES={'.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.mts','.cts'}
MAX_FILES=5000
MAX_BYTES=48*1024*1024
MAX_FILE_BYTES=256*1024
MAX_RECORDS=130000
CACHE_NAME='code_index_v37.json'
SCHEMA=1


def _cache_path(root:Path)->Path:
    ai=root/'.ai';folder=ai/'cache';target=folder/CACHE_NAME
    for p in (ai,folder,target):
        if p.is_symlink():raise ValueError('cache path cannot contain symlinks')
    return target


def _candidates(root:Path):
    count=0;total=0
    for parent, dirs, names in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.') and not (Path(parent)/d).is_symlink())
        for name in sorted(names):
            path=Path(parent)/name
            if path.suffix.lower() not in SUFFIXES or path.is_symlink() or SENSITIVE_NAMES.search(name):continue
            if not path.is_file():continue
            size=path.stat().st_size
            if not 0<size<=MAX_FILE_BYTES:continue
            count+=1;total+=size
            if count>MAX_FILES or total>MAX_BYTES:raise ValueError('index resource cap exceeded; narrow the project')
            try:
                raw=path.read_bytes()
                if b'\0' in raw:continue
                source=raw.decode('utf-8')
            except (OSError,UnicodeDecodeError):continue
            if SENSITIVE_TEXT.search(source):continue
            yield path.relative_to(root).as_posix(),hashlib.sha256(raw).hexdigest(),source


def _python(rel:str,source:str)->dict:
    try:tree=ast.parse(source,filename=rel)
    except SyntaxError as e:
        return {'symbols':[],'references':[],'imports':[],'dynamic_imports':False,'parse_errors':[{'line':e.lineno or 0,'code':'SyntaxError'}]}
    v=_Visitor(rel);v.visit(tree)
    imports=[];dynamic=False
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports.extend({'module':x.name,'level':0,'names':[]} for x in node.names)
        elif isinstance(node,ast.ImportFrom):
            imports.append({'module':node.module or '', 'level':node.level,'names':[x.name for x in node.names if x.name!='*']})
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('__import__','eval','exec'):
            dynamic=True
    return {'symbols':v.symbols,'references':v.references,'imports':imports,'dynamic_imports':dynamic,'parse_errors':[]}


def _typescript(batch:list[tuple[str,str]])->dict[str,dict]:
    node=shutil.which('node')
    if not node:raise RuntimeError('Node.js required for JS/TS AST; install Node 20+ and TypeScript 5.9.3')
    result={}
    for start in range(0,len(batch),24):
        items=[{'path':path,'source':source} for path,source in batch[start:start+24]]
        proc=subprocess.run([node,str(Path(__file__).with_name('ts_ast_bridge.cjs'))],
                            input=json.dumps({'items':items}),text=True,capture_output=True,timeout=25,check=False)
        if proc.returncode:
            raise RuntimeError('JS/TS AST unavailable: '+proc.stderr.strip()[:300])
        response=json.loads(proc.stdout)
        for item in response['files']:
            path=item.pop('path')
            result[path]=item
    return result


def _resolve_imports(records:dict, workspace:dict|None=None, config:dict|None=None):
    paths=set(records)
    def resolve(p, prefer_js=False):
        base=posixpath.normpath(p)
        if base.startswith('../') or base=='..' or base.startswith('/'):return None
        extensions=('.ts','.tsx','.js','.jsx','.mjs','.cjs','.mts','.cts','.py') if prefer_js else ('.py','.ts','.tsx','.js','.jsx','.mjs','.cjs','.mts','.cts')
        candidates=[base]+[base+ext for ext in extensions]
        candidates += [base+'/index'+ext for ext in ('.ts','.tsx','.js','.jsx')]
        candidates += [base+'/__init__.py']
        return next((candidate for candidate in candidates if candidate in paths),None)
    package_map = {p['name']: p for p in (workspace or {}).get('packages', [])}
    config = config or {}
    config_files = config.get('configs', {})
    static_exports = config.get('package_exports', {})
    def resolve_alias(spec, rel):
        # Only the nearest tsconfig/jsconfig applies; never infer root-wide aliases
        # when code belongs to another nested project.
        parent=posixpath.dirname(rel)
        candidates=[(posixpath.dirname(c), c, opt) for c,opt in config_files.items()
                    if parent == posixpath.dirname(c) or parent.startswith(posixpath.dirname(c).rstrip('/')+'/')]
        for _folder,_name,opts in sorted(candidates,key=lambda t:len(t[0]),reverse=True)[:1]:
            for pattern,targets in opts.get('aliases', {}).items():
                if '*' in pattern:
                    left,right=pattern.split('*',1)
                    if not(spec.startswith(left) and spec.endswith(right)):continue
                    piece=spec[len(left):len(spec)-len(right) if right else None]
                elif pattern == spec:piece=''
                else:continue
                for target in targets:
                    found=resolve(target.replace('*',piece),prefer_js=True)
                    if found:return found,True
                return None,True
        return None,False
    package_names = sorted(package_map, key=len, reverse=True)
    local_scopes = {name.split('/')[0]+'/' for name in package_map if name.startswith('@')}
    def resolve_workspace(spec:str):
        name = next((n for n in package_names if spec == n or spec.startswith(n+'/')), None)
        if name is None:
            return None, False
        info = package_map[name]
        remainder = spec[len(name):].lstrip('/')
        root = info['path']
        export_key='./'+remainder if remainder else '.'
        exported=static_exports.get(name,{}).get(export_key,[])
        if name in static_exports:
            # Declared exports restrict subpaths; do not invent hidden paths.
            candidates = exported
        else:
            candidates = ([posixpath.join(root,remainder)] if remainder else
                          [posixpath.join(root,e) for e in info['candidate_entries']])
        found = next((target for base in candidates if (target := resolve(base,prefer_js=True))),None)
        return found, True
    for rel,item in records.items():
        deps=set();unresolved=[]
        for imported in item['imports']:
            if rel.endswith('.py'):
                name=imported['module'].replace('.','/')
                level=imported['level']; parent=posixpath.dirname(rel)
                if level:
                    base=parent
                    for _ in range(level-1):base=posixpath.dirname(base)
                    target=posixpath.join(base,name)
                else:target=name
                options=[target]+[posixpath.join(target,n) for n in imported['names']]
                found=[p for x in options if (p:=resolve(x))]
                deps.update(found)
                if level and not found:unresolved.append('.'*level+name)
            elif isinstance(imported,str):
                if imported.startswith('.'):
                    target=posixpath.join(posixpath.dirname(rel),imported)
                    found=resolve(target,prefer_js=True)
                    if found:deps.add(found)
                    else:unresolved.append(imported)
                else:
                    resolved,local = resolve_workspace(imported)
                    if not resolved:
                        aliased,had_alias=resolve_alias(imported,rel)
                        if aliased:resolved=aliased
                        local=local or had_alias
                    if resolved:deps.add(resolved)
                    elif local or any(imported.startswith(scope) for scope in local_scopes) or imported.startswith(('@/','~/','@app/','@src/','src/','app/')):
                        unresolved.append(imported)
        item['dependencies']=sorted(deps)
        item['unresolved_local_imports']=sorted(set(unresolved))[:50]
    return records


def _read_cache(root:Path)->dict:
    p=_cache_path(root)
    if not p.exists():return {}
    if not p.is_file() or p.stat().st_size>16*1024*1024:raise ValueError('invalid or oversized index cache')
    try:data=json.loads(p.read_text('utf-8'))
    except (json.JSONDecodeError,UnicodeDecodeError):return {}
    if not isinstance(data,dict) or data.get('schema_version')!=SCHEMA or data.get('root')!=str(root):return {}
    value=data.get('files')
    return value if isinstance(value,dict) else {}


def _write_cache(root:Path,records:dict):
    p=_cache_path(root)
    p.parent.mkdir(parents=True,exist_ok=True)
    _cache_path(root)  # re-check after mkdir
    payload={'schema_version':SCHEMA,'root':str(root),'files':records}
    descriptor,tmp=tempfile.mkstemp(prefix='.index-',dir=p.parent)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as f:
            os.fchmod(f.fileno(),0o600)
            json.dump(payload,f,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            f.flush();os.fsync(f.fileno())
        _cache_path(root)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def build(project:Path, *, save_cache:bool=False, use_cache:bool=True)->dict:
    root=project.resolve(strict=True)
    if not root.is_dir():raise ValueError('project must be a directory')
    cached=_read_cache(root) if use_cache else {}
    current={}; js=[]; parsed=0;reused=0
    for rel,sha,source in _candidates(root):
        old=cached.get(rel)
        if isinstance(old,dict) and old.get('sha256')==sha and isinstance(old.get('symbols'),list):
            current[rel]=dict(old);reused+=1
            continue
        if rel.endswith('.py'):
            record=_python(rel,source)
            current[rel]={'sha256':sha,**record};parsed+=1
        else:js.append((rel,sha,source))
    if js:
        processed=_typescript([(p,text) for p,sha,text in js])
        for rel,sha,_ in js:
            current[rel]={'sha256':sha,**processed[rel]};parsed+=1
    removed=len(set(cached)-set(current))
    if sum(len(v['symbols'])+len(v['references']) for v in current.values())>MAX_RECORDS:
        raise ValueError('index record cap exceeded')
    workspace=discover(root)
    project_config=inspect_project_config(root)
    _resolve_imports(current,workspace,project_config)
    if save_cache:_write_cache(root,current)
    return {'schema_version':SCHEMA,'root':str(root),'files':dict(sorted(current.items())),
            'stats':{'files':len(current),'parsed':parsed,'reused':reused,'removed':removed},
            'workspace':workspace, 'project_config_warnings':project_config['warnings'],
            'note':'Local hash-based AST cache with static workspace aliases; not full module/LSP resolution. Never executes or uploads source.'}


def search(index:dict, query:str,limit:int=10)->dict:
    if not isinstance(query,str) or not query.strip() or len(query)>1000 or SENSITIVE_TEXT.search(query):raise ValueError('unsafe query')
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=20:raise ValueError('limit 1..20')
    q=query.casefold();terms={x for x in __import__('re').findall(r'[a-z_][a-z_0-9]*',q) if len(x)>1}
    result=[]
    for path,record in index['files'].items():
        for item in record['symbols']:
            name=item['name'].casefold();full=item['qualified_name'].casefold()
            score=(100 if full==q else 0)+(70 if name==q else 0)+(35 if name in q else 0)+8*len(terms & set(__import__('re').findall(r'[a-z_][a-z_0-9]*',full)))
            if score:result.append({**item,'score':score})
    result.sort(key=lambda x:(-x['score'],x['path'],x['line']))
    return {'query':query,'matches':result[:limit],'note':'Candidate symbols only; runtime bindings not established.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Read-only by default, content-hash incremental Python/JS/TS AST index')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--query')
    p.add_argument('--limit',type=int,default=10)
    p.add_argument('--save-cache',action='store_true',help='opt-in write under project/.ai/cache')
    p.add_argument('--no-cache',action='store_true')
    p.add_argument('--summary',action='store_true',help='hide index records, show counts')
    a=p.parse_args(argv)
    try:
        res=build(a.project,save_cache=a.save_cache,use_cache=not a.no_cache)
        result={'schema_version':SCHEMA,'stats':res['stats'],'parse_errors':{k:r['parse_errors'] for k,r in res['files'].items() if r['parse_errors']}}
        if a.query:result['search']=search(res,a.query,a.limit)
        if not a.summary and not a.query:result['files']={p:{'symbols':r['symbols'],'dependencies':r['dependencies'],'unresolved_local_imports':r['unresolved_local_imports']} for p,r in res['files'].items()}
        print(json.dumps(result,indent=2,ensure_ascii=False))
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
