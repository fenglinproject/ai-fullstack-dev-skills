#!/usr/bin/env python3
"""V3.9 reproducible read-only evaluation of a USER-PROVIDED Git repository.

No clone, download, install, script execution, model call, or modifications.
Pinned-commit ground truth supplied by the user; cannot attest label quality.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

try:
    from tools.incremental_index import build, search
    from tools.test_selection import select
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.incremental_index import build, search
    from tools.test_selection import select

MAX_CASES = 100
MAX_MANIFEST = 256 * 1024


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-C', str(root), *args],
        capture_output=True, text=True, timeout=10, check=False,
        env={'PATH': __import__('os').environ.get('PATH', '')})
    if completed.returncode:
        raise ValueError('Git metadata unavailable; repository must be initialized')
    return completed.stdout.strip()


def _rel(raw: str) -> str:
    if (not isinstance(raw, str) or not raw or len(raw) > 300 or raw.startswith('/')
            or '\\' in raw or any(part in ('', '..', '.') for part in raw.split('/'))):
        raise ValueError('invalid benchmark relative path')
    return raw


def evaluate(project: Path, manifest: Path, *, repeats: int = 2) -> dict:
    if not isinstance(repeats, int) or isinstance(repeats, bool) or not 1 <= repeats <= 3:
        raise ValueError('repeats must be 1..3')
    root = project.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('repository must be directory')
    if root == Path(__file__).resolve().parents[1]:
        raise ValueError('select independent repository, not this toolkit')
    if _git(root,'rev-parse','--show-toplevel') != str(root):
        raise ValueError('project must be Git repository root')
    commit = _git(root,'rev-parse','HEAD')
    if len(commit) != 40:
        raise ValueError('invalid commit hash')
    if _git(root,'status','--porcelain','--untracked-files=normal'):
        raise ValueError('repository must be clean before evaluation')
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>MAX_MANIFEST:
        raise ValueError('invalid or oversized benchmark manifest')
    raw=manifest.read_bytes()
    try:
        cases=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc:
        raise ValueError('invalid benchmark JSON') from exc
    if not isinstance(cases,dict) or cases.get('schema_version')!=1 or cases.get('commit_sha')!=commit:
        raise ValueError('benchmark must pin exact Git HEAD commit_sha')
    symbol_cases=cases.get('symbol_cases', [])
    test_cases=cases.get('test_cases', [])
    if not isinstance(symbol_cases,list) or not isinstance(test_cases,list) or not 1<=len(symbol_cases)+len(test_cases)<=MAX_CASES:
        raise ValueError('1..100 benchmark cases required')
    ids=set();tracked=set(_git(root,'ls-files','--cached').splitlines())
    for c in symbol_cases + test_cases:
        if not isinstance(c,dict) or not isinstance(c.get('id'),str) or not c['id'] or c['id'] in ids:
            raise ValueError('duplicate or invalid case id')
        ids.add(c['id'])
        if c in symbol_cases:
            if not isinstance(c.get('query'),str) or not 1<=len(c['query'])<=200:
                raise ValueError('invalid symbol query')
            if _rel(c.get('expected_path')) not in tracked:
                raise ValueError('expected symbol path must be tracked')
            if not isinstance(c.get('expected_symbol'),str):
                raise ValueError('expected_symbol missing')
        else:
            changed=c.get('changed')
            if not isinstance(changed,list) or not changed or any(_rel(x) not in tracked for x in changed):
                raise ValueError('changed files must be tracked')
            expected=c.get('expected_test')
            if expected is not None and _rel(expected) not in tracked:
                raise ValueError('expected test must be tracked')
    times=[]
    for _ in range(repeats):
        start=time.perf_counter()
        index=build(root,use_cache=False,save_cache=False)
        times.append(round((time.perf_counter()-start)*1000,2))
    symbols=[]; tests=[]
    for c in symbol_cases:
        results=search(index,c['query'],limit=10).get('matches',[])
        rank=next((i+1 for i,r in enumerate(results)
            if r['path']==c['expected_path'] and r.get('qualified_name')==c['expected_symbol']),None)
        symbols.append({'id':c['id'],'hit':rank is not None,'rank':rank})
    for c in test_cases:
        result=select(index,c['changed'])
        expected=c.get('expected_test')
        hit = (expected in {x['path'] for x in result['tests']}) if expected else not bool(result['tests'])
        tests.append({'id':c['id'],'hit':hit,'full_suite_required':result['full_suite_required']})
    if _git(root,'status','--porcelain','--untracked-files=normal'):
        raise RuntimeError('repository modified during benchmark')
    return {'schema_version':1,'repository':root.name,'commit_sha':commit,
            'manifest_sha256':hashlib.sha256(raw).hexdigest(), 'dirty':False,
            'indexed_files':index['stats']['files'],
            'duration_ms':{'runs':times,'median':round(statistics.median(times),2)},
            'symbol_results':{'hits':sum(x['hit'] for x in symbols),'cases':len(symbols),'details':symbols},
            'test_results':{'hits':sum(x['hit'] for x in tests),'cases':len(tests),'details':tests},
            'warnings':index.get('project_config_warnings',[]),
            'note':'Independent pinned local Git repository; read-only. Human-supplied labels not verified. No tests executed or model called.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Read-only pinned Git repo AST/impact benchmark; no network or project code execution')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=2)
    p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    try:
        result=evaluate(a.project,a.manifest,repeats=a.repeats)
        report=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if a.output:
            dest = a.output.absolute()
            repo = a.project.resolve(strict=True)
            if (a.output.is_symlink() or not a.output.parent.is_dir() or
                    dest == repo or repo in dest.parents):
                raise ValueError('output must be outside read-only repository')
            a.output.write_text(report,'utf-8')
        print(report)
    except (OSError,ValueError,RuntimeError,TimeoutError,KeyError) as e:
        p.exit(2,'error: '+str(e)+'\n')


if __name__=='__main__':main()
