#!/usr/bin/env python3
"""Rank local read-only candidate files from task, Python AST and past failures.

Not an automatic source selector; no data egress or permission to edit. Failure
logs are untrusted and cannot cause reading arbitrary paths or invoking tools.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from tools.context_retrieval import retrieve
    from tools.ast_symbols import search
    from tools.evidence_context import analyze
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.context_retrieval import retrieve
    from tools.ast_symbols import search
    from tools.evidence_context import analyze

REPORT_NAME = re.compile(r'checks-[0-9a-f]{32}\.json\Z')


def rank(project: Path, task: str, failures: list[str] | None = None, limit: int = 6) -> dict:
    root=project.resolve(strict=True)
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=12:
        raise ValueError('limit must be 1..12')
    if failures is None:failures=[]
    if not isinstance(failures,list) or len(failures)>12 or any(not isinstance(s,str) or len(s)>20000 for s in failures):
        raise ValueError('at most 12 bounded failure diagnostic strings')
    lexical=retrieve(root,task,12,include_snippets=False)['results']
    semantic=search(root,task,12,include_references=False)['matches']
    paths=analyze(root, failures,limit=20)['hints'] if failures else []
    scored={}
    def add(path, points, evidence):
        entry=scored.setdefault(path, {'path':path,'score':0,'evidence':[]})
        entry['score']+=points
        if evidence not in entry['evidence']:
            entry['evidence'].append(evidence)
    for n,item in enumerate(lexical):
        add(item['path'], max(1,18-n), 'lexical-task-match')
    for n,item in enumerate(semantic):
        add(item['path'], max(4,30-n*2), 'python-ast-symbol')
    for item in paths:
        add(item['path'], 55 + min(item['occurrences'], 5)*10, 'validated-failure-trace')
    candidates=sorted(scored.values(),key=lambda x:(-x['score'],x['path']))[:limit]
    return {'schema_version':1,'method':'local-lexical-ast-and-failure-history',
            'failure_diagnostics_considered':len(failures),'candidates':candidates,
            'note':'Scores are deterministic heuristics, not fault attribution or a file allowlist. Preview and manually approve all model-bound source paths.'}


def read_reports(project: Path, names: list[str]) -> list[str]:
    root=project.resolve(strict=True)
    if len(names)>5 or any(not isinstance(name,str) or not REPORT_NAME.fullmatch(name) for name in names):
        raise ValueError('use at most five report basenames from the check runner')
    folder=root/'.ai'/'reports'
    if folder.is_symlink() or folder.resolve(strict=False)!=root/'.ai'/'reports':
        raise ValueError('unsafe report location')
    diagnostics=[]
    for name in names:
        path=folder/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>128*1024:
            raise ValueError('unsafe or missing report')
        data=json.loads(path.read_text('utf-8'))
        if (not isinstance(data,dict) or data.get('schema_version')!=2 or
            data.get('project')!=str(root) or data.get('actually_executed') is not True):
            raise ValueError('report must be a local executed check report')
        if not isinstance(data.get('checks'),list):raise ValueError('invalid check entries')
        for check in data['checks']:
            if isinstance(check,dict) and check.get('status') in ('failed','error','timeout'):
                msg='\n'.join(str(check.get(field,'')) for field in ('stderr_tail','stdout_tail','error'))[-2600:]
                diagnostics.append(msg)
                if len(diagnostics)>=12:return diagnostics
    return diagnostics


def main(argv=None):
    parser=argparse.ArgumentParser(description='Preview local repair context from verified check reports')
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--task',required=True)
    parser.add_argument('--report',action='append',default=[],help='repeat report basename, max 5')
    parser.add_argument('--limit',type=int,default=6)
    args=parser.parse_args(argv)
    try:
        result=rank(args.project,args.task,read_reports(args.project,args.report),args.limit)
        print(json.dumps(result,indent=2,ensure_ascii=False))
    except (ValueError,OSError,UnicodeDecodeError,KeyError,TypeError,json.JSONDecodeError) as exc:
        parser.exit(2,f'error: {exc}\n')

if __name__=='__main__':main()
