#!/usr/bin/env python3
"""Optional offline LSP WorkspaceSymbol/Location JSON import.

Does NOT launch language servers, run project configuration or contact networks.
Accepts previously exported LSP metadata only, validates every file URI against
indexed source files, and returns candidate locations without sharing source.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
try:
    from tools.incremental_index import build
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import build

MAX_BYTES=1024*1024
MAX_SYMBOLS=1000


def _relative(root:Path,uri:str)->str|None:
    if not isinstance(uri,str) or len(uri)>4000:return None
    try:
        parts=urlparse(uri)
        if parts.scheme!='file' or parts.netloc not in ('','localhost') or parts.params or parts.query or parts.fragment:
            return None
        # Prevent encoded separators and ambiguous path encodings.
        if re.search(r'%2f|%5c|%00',parts.path,re.I):return None
        raw=unquote(parts.path)
        path=Path(raw)
        if not path.is_absolute() or any(x=='..' for x in path.parts):return None
        rel=path.relative_to(root).as_posix()
        return rel if rel and not rel.startswith('../') else None
    except (ValueError,OSError):return None


def interpret(project:Path,export:Path,query:str|None=None, *,limit:int=20)->dict:
    root=project.resolve(strict=True)
    if not 1<=limit<=100:raise ValueError('limit 1..100')
    if query is not None and (not isinstance(query,str) or len(query)>200):raise ValueError('invalid query')
    if export.is_symlink() or not export.is_file() or export.stat().st_size>MAX_BYTES:
        raise ValueError('invalid or oversized LSP export')
    try:payload=json.loads(export.read_text('utf-8'))
    except (UnicodeError,json.JSONDecodeError) as e:raise ValueError('malformed LSP JSON export') from e
    if isinstance(payload,dict): payload=payload.get('symbols')
    if not isinstance(payload,list) or len(payload)>MAX_SYMBOLS:raise ValueError('expected bounded symbol list')
    allowed=set(build(root)['files'])
    matches=[]; rejected=0
    for item in payload:
        if not isinstance(item,dict):rejected+=1;continue
        name=item.get('name','')
        loc=item.get('location',item)
        if not isinstance(name,str) or not 1<=len(name)<=200 or not isinstance(loc,dict):rejected+=1;continue
        rel=_relative(root,loc.get('uri',''))
        position=loc.get('range',{}).get('start',{}) if isinstance(loc.get('range',{}),dict) else {}
        line=position.get('line') if isinstance(position,dict) else None
        if rel not in allowed or not isinstance(line,int) or isinstance(line,bool) or not 0<=line<=10000000:
            rejected+=1;continue
        if query and query.casefold() not in name.casefold():continue
        matches.append({'name':name,'path':rel,'line':line+1,'source':'lsp-export-candidate'})
    matches.sort(key=lambda x:(x['path'],x['line'],x['name']))
    return {'schema_version':1,'matches':matches[:limit],'total_matched':len(matches),
            'rejected_records':rejected,
            'note':'Imported, not verified LSP locations. No server launched; no source transmitted or executed.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Read validated LSP-exported symbol locations without launching servers')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--export',type=Path,required=True)
    p.add_argument('--query')
    p.add_argument('--limit',type=int,default=20)
    a=p.parse_args(argv)
    try:print(json.dumps(interpret(a.project,a.export,a.query,limit=a.limit),ensure_ascii=False,indent=2))
    except (ValueError,OSError,RuntimeError) as e:p.exit(2,'error: '+str(e)+'\n')
if __name__=='__main__':main()
