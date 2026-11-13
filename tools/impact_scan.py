#!/usr/bin/env python3
"""Read-only textual cross-file reference scan, not a full dependency graph.

Use it to estimate the change surface before editing an identifier. Results
are candidate references that require developer review, not proven dependencies.
"""
import argparse
import json
import re
from pathlib import Path

SUFFIXES={'.py','.js','.jsx','.ts','.tsx','.vue','.sql','.html','.css','.json','.md'}
IGNORE={'.git','.ai','node_modules','.venv','venv','dist','build','__pycache__','.next','coverage'}
MAX_FILE=512*1024

def category(path:Path)->str:
    p=str(path).lower()
    if any(x in p for x in ('test','spec')):return 'tests'
    if path.suffix=='.sql' or any(x in p for x in ('migrations','schema','models')):return 'database'
    if any(x in p for x in ('frontend','component','pages','src/ui')) or path.suffix in {'.vue','.jsx','.tsx','.css','.html'}:return 'frontend'
    if any(x in p for x in ('backend','server','api','route')):return 'backend'
    return 'other'

def scan(project:Path,symbol:str,max_files:int=8000,max_hits:int=150)->dict:
    project=project.resolve()
    if not project.is_dir() or len(symbol)>120 or not re.fullmatch(r'[\w.\-/]+',symbol,re.UNICODE):
        raise ValueError('valid project directory and identifier/path fragment required')
    pattern=re.compile(re.escape(symbol),re.IGNORECASE)
    matches=[];files_seen=0;limited=False
    for file in sorted(project.rglob('*')):
        if any(part in IGNORE for part in file.relative_to(project).parts):continue
        if not file.is_file() or file.suffix.lower() not in SUFFIXES or file.is_symlink():continue
        if file.stat().st_size>MAX_FILE:continue
        files_seen+=1
        if files_seen>max_files:limited=True;break
        try: lines=file.read_text('utf-8').splitlines()
        except (UnicodeDecodeError,OSError):continue
        hits=[{'line':n,'excerpt':line.strip()[:220]} for n,line in enumerate(lines,1) if pattern.search(line)]
        if hits:
            matches.append({'path':str(file.relative_to(project)),'category':category(file),
                            'count':len(hits),'lines':hits[:8]})
            if len(matches)>=max_hits:limited=True;break
    return {'symbol':symbol,'files_scanned':min(files_seen,max_files),'candidate_files':len(matches),
            'truncated':limited,'matches':matches,
            'limitation':'Text match only. Does not resolve aliases, imports, generated code, or semantic dependencies.'}

def main():
    p=argparse.ArgumentParser(description='Find candidate files affected by renaming a symbol')
    p.add_argument('--project',required=True);p.add_argument('--symbol',required=True)
    p.add_argument('--out',help='optional output JSON path');a=p.parse_args()
    result=scan(Path(a.project),a.symbol)
    if a.out:Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
