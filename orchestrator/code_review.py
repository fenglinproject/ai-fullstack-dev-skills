#!/usr/bin/env python3
"""Read-only heuristics for V3 changes. No 'approved' security verdict is made."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
try:
    from orchestrator.workflow import _load_change,_drift
    from tools.dependency_graph import graph
except ModuleNotFoundError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from orchestrator.workflow import _load_change,_drift
    from tools.dependency_graph import graph

PATTERNS=[
 ('embedded_credentials','high',re.compile(r'(?:api[_-]?key|password|secret|private[_-]?key|token)\s*[:=]\s*["\'][^"\']{8,}',re.I)),
 ('private_key','high',re.compile(r'-----BEGIN [\w ]*PRIVATE KEY-----')),
 ('dynamic_execution','medium',re.compile(r'\b(?:eval|exec)\s*\(|\bsubprocess\.(?:Popen|run)\s*\(')),
 ('unsafe_shell','medium',re.compile(r'\bshell\s*=\s*True\b|\bos\.system\s*\(')),
 ('unfinished_code','low',re.compile(r'\b(?:FIXME|TODO|XXX)\b')),
 ('debug_print','low',re.compile(r'\bconsole\.log\s*\(|\bdebugger\s*;')),
]


def review(project:Path,change_id:str)->dict:
    project=project.resolve(strict=True)
    _,record=_load_change(project,change_id)
    drift=_drift(project,record)
    findings=[]
    for item in record['files']:
        rel=item['path']
        for n,line in enumerate(item['diff'].splitlines(),1):
            if not line.startswith('+') or line.startswith('+++'):continue
            added=line[1:]
            for rule,severity,rx in PATTERNS:
                if rx.search(added):findings.append({'path':rel,'diff_line':n,'rule':rule,'severity':severity})
            if added.rstrip()!=added:
                findings.append({'path':rel,'diff_line':n,'rule':'trailing_whitespace','severity':'low'})
    selected=[x['path'] for x in record['files'] if (project/x['path']).is_file()]
    source=[p for p in selected if Path(p).suffix.lower() in {'.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue'}]
    impact=None
    if source:
        try:impact=graph(project,source)
        except ValueError as e:impact={'error':str(e)}
    return {'change_id':change_id,'status':record['status'],'all_files_match':all(x['unchanged_since_apply'] for x in drift),
            'findings':findings,'counts':{x:sum(f['severity']==x for f in findings) for x in ('high','medium','low')},
            'import_impact':impact,
            'note':'Heuristic findings only; absence of findings is NOT proof of security, correctness, or approval.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Review proposed/applied code change heuristically')
    p.add_argument('--project',required=True);p.add_argument('--change-id',required=True)
    a=p.parse_args(argv)
    try:print(json.dumps(review(Path(a.project),a.change_id),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as e:p.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
