#!/usr/bin/env python3
"""Bounded, deterministic, read-only source-context suggestions (no embeddings/network).

Results are candidates, not permission to transmit files to a model. Source text
is untrusted and may contain prompt-injection attempts. Symlinks, credential
files and private work artifacts are skipped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css', '.scss',
              '.json', '.yaml', '.yml', '.sql', '.go', '.java', '.rs', '.md'}
SKIP_DIRS = {'.git', '.ai', 'node_modules', '.venv', 'venv', '__pycache__',
             '.next', '.nuxt', '.pytest_cache', 'dist', 'build', 'coverage',
             '.tox', '.idea', '.vscode', 'vendor'}
SENSITIVE_NAMES = re.compile(r'(^\.env(?:\..*)?$|\.pem$|\.key$|^id_rsa|^id_ed25519|credential|secret|^\.npmrc$|^\.pypirc$)', re.I)
SENSITIVE_TEXT = re.compile(r'-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----|\b(?:sk-[a-zA-Z0-9_-]{12,}|gh[pousr]_[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16})\b|\b(?:api[_-]?key|password|access[_-]?token|client[_-]?secret)\s*[:=]\s*[\"\'][^\s\"\']{8,}[\"\']', re.I)
TOKEN = re.compile(r'[A-Za-z_][A-Za-z_0-9]*|[\u3400-\u9fff]+')
STOP = {'the','a','an','of','in','on','and','to','for','is','are','with','this','that','please','fix','change','modify','update','make','some','file','files','代码','修改','实现','请','这个','一下','添加','功能','新增'}
MAX_FILES = 3500
MAX_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024
MAX_RESULTS = 12


def tokens(text: str) -> list[str]:
    out=[]
    for part in TOKEN.findall(text.casefold()):
        if part in STOP: continue
        if re.fullmatch(r'[\u3400-\u9fff]+',part):
            if len(part)<2: continue
            out.extend(part[i:i+2] for i in range(len(part)-1))
        else:
            out.append(part)
            if '_' in part:out.extend(x for x in part.split('_') if len(x)>2)
    return list(dict.fromkeys(x for x in out if len(x)>1))[:32]


def _source_files(root: Path):
    count=0; total=0
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(parent)/d).is_symlink())
        for name in sorted(names):
            path=Path(parent)/name
            if (path.is_symlink() or path.suffix.lower() not in EXTENSIONS
                    or SENSITIVE_NAMES.search(name) or name.lower()=='proposal.json'):continue
            if not path.is_file(): continue
            size=path.stat().st_size
            if size>MAX_FILE_BYTES or size==0:continue
            count+=1;total+=size
            if count>MAX_FILES or total>MAX_BYTES:
                raise ValueError('source index limits exceeded; narrow the project or exclude generated files')
            yield path, size


def _score(source: str, rel: str, query_terms: list[str]) -> tuple[float, int]:
    lines=source.splitlines()
    path=rel.casefold()
    path_terms=set(tokens(path))
    path_score=sum(15 for term in query_terms if term in path_terms) + sum(5 for term in query_terms if term in path)
    best_score=0.0; best_line=0
    # Specific symbols and definition sites outrank incidental comments.
    for no,line in enumerate(lines,1):
        low=line.casefold()
        hits=sum(1 for term in query_terms if term in low)
        if not hits:continue
        score=hits*5 + (5 if re.match(r'^\s*(async\s+)?(def|class|function|export|const|interface|type)\s',line) else 0)
        if hits>=2:score+=hits*2
        if score>best_score:best_score=score;best_line=no
    if not best_score and not path_score:return 0.0,0
    if not best_line:best_line=1
    # Prefer application source over test-only mentions when evidence is otherwise tied.
    parts=rel.split('/')
    if any(p in parts for p in ('tests','test','__tests__')) and not any(x in query_terms for x in ('test','tests','testing','测试')):
        path_score-=12
    if rel.lower().endswith('.md') and not any(x in query_terms for x in ('readme','docs','document','documentation','文档')):
        path_score-=14
    if not rel.lower().endswith('.md') and not any(p in parts for p in ('tests','test','__tests__')):
        path_score+=8
    return float(best_score+path_score),best_line


def retrieve(project: Path, query: str, limit: int=6, *, include_snippets: bool=True) -> dict:
    root=project.resolve(strict=True)
    if not root.is_dir() or not isinstance(query,str) or len(query)>1000 or not query.strip():
        raise ValueError('expected a project directory and nonempty query under 1000 characters')
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=MAX_RESULTS:
        raise ValueError('limit must be 1..12')
    if SENSITIVE_TEXT.search(query): raise ValueError('query appears to contain a secret')
    terms=tokens(query)
    if not terms: raise ValueError('query has no useful searchable terms')
    results=[]; scanned=0; skipped_sensitive=0
    for file,size in _source_files(root):
        scanned+=1
        try:
            raw=file.read_bytes()
            if b'\x00' in raw:continue
            contents=raw.decode('utf-8')
        except (OSError,UnicodeDecodeError):continue
        if SENSITIVE_TEXT.search(contents):
            skipped_sensitive+=1;continue
        relative=file.relative_to(root).as_posix()
        score,line=_score(contents,relative,terms)
        if score<=0:continue
        lines=contents.splitlines()
        start=max(1,line-2);end=min(len(lines),line+2)
        entry={'path':relative,'sha256':hashlib.sha256(raw).hexdigest(),
               'bytes':size,'score':score,'line_start':start,'line_end':end}
        if include_snippets: entry['snippet']='\n'.join(lines[start-1:end])[:1200]
        results.append(entry)
    results.sort(key=lambda e:(-e['score'],e['path']))
    return {'schema_version':1,'query':query,'query_terms':terms,'results':results[:limit],
            'scanned_files':scanned,'skipped_sensitive_files':skipped_sensitive,
            'note':'Read-only, lexical candidates; not semantic proof. No files transmitted or edited. Explicit approval is still needed before external model sharing.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Search local project source (no embeddings, network, or writes)')
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--query',required=True)
    parser.add_argument('--limit',type=int,default=6)
    parser.add_argument('--no-snippets',action='store_true')
    args=parser.parse_args(argv)
    try: print(json.dumps(retrieve(args.project,args.query,args.limit,include_snippets=not args.no_snippets),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as e: parser.exit(2,f'error: {e}\n')


if __name__=='__main__':main()
