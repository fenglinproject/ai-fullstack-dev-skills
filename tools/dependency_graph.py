#!/usr/bin/env python3
"""Bounded read-only dependency candidates for local Python and JS/TS modules.

Imports are heuristic, not language-server semantic resolution. No source is
executed and no dependencies are installed.
"""
from __future__ import annotations
import argparse
import ast
import json
import re
from collections import deque
from pathlib import Path

SUFFIXES={'.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue'}
SKIP={'.git','.ai','node_modules','.venv','venv','dist','build','coverage','.next','__pycache__'}
IMPORT_JS=re.compile(r'''(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*)["'](\.[^"']+)["']''')
MAX_FILES=6000
MAX_SIZE=512*1024


def source_files(project:Path):
    root=project.resolve(strict=True)
    if not root.is_dir():raise ValueError('project must be a directory')
    paths=[]
    for f in root.rglob('*'):
        if any(x in SKIP for x in f.relative_to(root).parts):continue
        if f.is_symlink() or not f.is_file() or f.suffix.lower() not in SUFFIXES:continue
        if f.stat().st_size>MAX_SIZE:continue
        paths.append(f.relative_to(root).as_posix())
        if len(paths)>MAX_FILES:raise ValueError('dependency scan file cap exceeded')
    return sorted(paths)


def _resolve(names:set[str],base:Path)->str|None:
    bases=[base] if base.suffix else [base.with_suffix(ext) for ext in sorted(SUFFIXES)] + [base/'index.ts',base/'index.tsx',base/'index.js',base/'__init__.py']
    for p in bases:
        key=p.as_posix()
        if key in names:return key
    return None


def _python_imports(text:str,rel:Path,names:set[str])->set[str]:
    try:tree=ast.parse(text)
    except SyntaxError:return set()
    imports=set()
    module_base=rel.parent
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for a in node.names:
                dep=_resolve(names,Path(a.name.replace('.','/')))
                if dep:imports.add(dep)
        elif isinstance(node,ast.ImportFrom):
            # Level 1 means current package; level 2 means its parent.
            base=module_base
            if node.level:
                for _ in range(node.level-1):base=base.parent
            else:base=Path('.')
            target=base/((node.module or '').replace('.','/'))
            dep=_resolve(names,target)
            if dep:imports.add(dep)
            for alias in node.names:
                candidate=_resolve(names,target/alias.name)
                if candidate:imports.add(candidate)
    return imports


def _js_imports(text:str,rel:Path,names:set[str])->set[str]:
    result=set()
    for m in IMPORT_JS.finditer(text):
        raw=m.group(1)
        dest=(rel.parent/raw)
        clean=[]
        for part in dest.parts:
            if part=='..':
                if clean:clean.pop()
                else:break
            elif part!='.':clean.append(part)
        else:
            target=_resolve(names,Path(*clean))
            if target:result.add(target)
    return result


def graph(project:Path,changed:list[str],*,max_depth:int=3)->dict:
    root=project.resolve(strict=True)
    if not isinstance(changed,list) or not changed or len(changed)>50 or not isinstance(max_depth,int) or not 1<=max_depth<=6:
        raise ValueError('provide 1..50 changed files and max depth 1..6')
    names=set(source_files(root))
    for rel in changed:
        p=Path(rel)
        if not isinstance(rel,str) or p.is_absolute() or '..' in p.parts or rel not in names:
            raise ValueError(f'changed source file is unknown or unsafe: {rel}')
    edges={}
    for rel in sorted(names):
        p=Path(rel)
        try:text=(root/p).read_text('utf-8')
        except (OSError,UnicodeDecodeError):continue
        edges[rel]=sorted(_python_imports(text,p,names) if p.suffix=='.py' else _js_imports(text,p,names))
    reverse={f:set() for f in names}
    for f,deps in edges.items():
        for d in deps:reverse[d].add(f)
    queue=deque((rel,0) for rel in changed)
    visited=set(changed);dependents=[]
    while queue:
        f,d=queue.popleft()
        if d>=max_depth:continue
        for item in sorted(reverse.get(f,())):
            if item in visited:continue
            visited.add(item);dependents.append({'path':item,'depth':d+1,'via':f})
            queue.append((item,d+1))
    return {'changed':changed,'files_scanned':len(names),'edges':sum(map(len,edges.values())),
            'direct_dependencies':{f:edges.get(f,[]) for f in changed},
            'affected_dependents':dependents,'max_depth':max_depth,
            'limitations':'Static local imports only; excludes package aliases, dynamic imports, runtime data flows and generated code.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Candidate impacted code paths from local import graph')
    p.add_argument('--project',required=True);p.add_argument('--changed',nargs='+',required=True)
    p.add_argument('--max-depth',type=int,default=3)
    a=p.parse_args(argv)
    try:print(json.dumps(graph(Path(a.project),a.changed,max_depth=a.max_depth),ensure_ascii=False,indent=2))
    except (OSError,ValueError) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
