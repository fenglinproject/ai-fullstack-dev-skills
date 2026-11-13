#!/usr/bin/env python3
"""Offline heuristic test-failure classification; guidance is advisory only."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

RULES=[
 ('dependency_missing',r'(?:ModuleNotFoundError|ImportError|Cannot find module|No module named|missing dependency|npm ERR! code E404)', 'Check dependency declarations and installation environment; do not blindly install packages.'),
 ('syntax_error',r'(?:SyntaxError|IndentationError|unexpected token|unterminated string|ParseError|TS1\d{3})', 'Inspect changed syntax and parser/compiler location; limit changes to affected files.'),
 ('assertion_failure',r'(?:AssertionError|assertion failed|expect\(.+\)|expected:|FAIL: test_|Assertion failed)', 'Compare the expected behavior with the implementation and failing test.'),
 ('type_error',r'(?:TypeError|mypy: error|TS2\d{3}|Argument of type)', 'Trace type definitions, argument contracts, and affected call sites.'),
 ('connection_failure',r'(?:ConnectionRefusedError|ECONNREFUSED|could not connect|Name or service not known)', 'Check service readiness and environment configuration before changing application logic.'),
 ('permission_failure',r'(?:PermissionError|EACCES|permission denied|Operation not permitted)', 'Inspect permissions and test environment; never use elevated privileges automatically.'),
 ('timeout',r'(?:TimeoutError|timed? out|timeout|deadline exceeded)', 'Inspect blocking dependencies and time budget; avoid automatic timeout increases.'),
]
COMPILED=[(name,re.compile(pattern,re.I),advice) for name,pattern,advice in RULES]


def classify(diagnostic: str, status: str='failed') -> dict:
    if not isinstance(diagnostic,str):raise ValueError('diagnostic must be text')
    if len(diagnostic)>20000:diagnostic=diagnostic[-20000:]
    for name,pattern,advice in COMPILED:
        if pattern.search(diagnostic):return {'category':name,'guidance':advice,'confidence':'heuristic'}
    if status=='timeout':return {'category':'timeout','guidance':RULES[-1][2],'confidence':'heuristic'}
    return {'category':'unknown','guidance':'Inspect the exact failing command and source; do not assume a code defect.','confidence':'unknown'}


def summarize(report: dict) -> dict:
    if not isinstance(report,dict):raise ValueError('report must be an object')
    failed=[]
    for check in report.get('checks',[]):
        if not isinstance(check,dict) or check.get('status') not in ('failed','error','timeout'):continue
        raw='\n'.join(str(check.get(k,'')) for k in ('stderr_tail','stdout_tail','error'))
        result=classify(raw,check['status'])
        failed.append({'name':str(check.get('name',''))[:100],'status':check['status'],**result})
    return {'total_failed':len(failed),'checks':failed,'note':'Heuristics only; not execution, diagnosis proof or authorization to edit.'}



def repair_strategy(current_categories: list[str], previous_categories: list[str] | None=None) -> dict:
    """Stable, low-trust advisory derived from test categories across rounds.

    Does not execute fixes or turn a failure hint into an acceptance criterion.
    """
    known={name:advice for name,_,advice in RULES}
    valid=set(known)|{'unknown'}
    if not isinstance(current_categories,list) or any(c not in valid for c in current_categories):
        raise ValueError('invalid current failure categories')
    if previous_categories is None:previous_categories=[]
    if not isinstance(previous_categories,list) or any(c not in valid for c in previous_categories):
        raise ValueError('invalid history categories')
    focus=list(dict.fromkeys(current_categories))[:6]
    recurring=sorted(set(focus)&set(previous_categories))
    advice=[{'category':name,'guidance':known.get(name,'Inspect failing evidence and source before proposing changes.')}
            for name in focus]
    return {'current_categories':focus,'repeated_categories':recurring,
            'escalate_review':bool(recurring), 'suggestions':advice,
            'next_step':('Repeated failure category: review earlier patches, assumptions and test setup before proposing another edit.'
                         if recurring else 'Inspect failing evidence and narrow the next change to its root cause.'),
            'note':'Advisory only. Repetition is a category match, not proof the root cause is unchanged.'}

def main(argv=None):
    p=argparse.ArgumentParser(description='Offline advice from check-runner report')
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        if a.report.is_symlink() or a.report.stat().st_size>128*1024:raise ValueError('unsafe or oversized report')
        data=json.loads(a.report.read_text('utf-8'))
        print(json.dumps(summarize(data),ensure_ascii=False,indent=2))
    except (OSError,ValueError,TypeError) as e:p.exit(2,f'error: {e}\n')


if __name__=='__main__':main()
