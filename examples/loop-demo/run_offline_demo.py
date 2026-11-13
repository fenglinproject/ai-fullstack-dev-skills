#!/usr/bin/env python3
"""Execute a TRUSTED, TEMPORARY two-round code-repair demo without network/API keys.

This script is intentionally opt-in. It approves changes and executes tests only
inside an isolated *directory copy* of the repository's trusted demo. A temporary
directory does NOT sandbox malicious tests; do not substitute arbitrary sources.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from orchestrator.cli import init
from orchestrator.loop import start,approve,test,repair,abort


def response(source:Path,dest:Path,old:str,new:str,task:str,task_id:str)->Path:
    data={'schema_version':3,'task_id':task_id,'summary':task,
          'changes':[{'path':'src/formatter.py','action':'replace',
            'expected_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'old_text':old,'new_text':new}]}
    dest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    return dest


def main():
    with tempfile.TemporaryDirectory(prefix='skills-v32-demo-') as temp:
        folder=Path(temp)
        project=folder/'trusted-demo'
        shutil.copytree(ROOT/'examples/workflow-demo',project,
                        ignore=shutil.ignore_patterns('__pycache__'))
        init(project)
        # Opt in to trusted copied-fixture tests. Never change the project default.
        check_file=project/'.ai/checks.json'
        check_data=json.loads(check_file.read_text())
        check_data['checks'][0]['enabled']=True
        check_file.write_text(json.dumps(check_data))
        original=(project/'src/formatter.py').read_bytes()
        task='Fix greeting punctuation in the example module'
        task_id='DEMO-32'
        src=project/'src/formatter.py'
        first=response(src,folder/'round1.json','return f"Hello {name}"',
                       'return f"Hello {name}?"',task,task_id)
        session=start(project,task,task_id,['src/formatter.py'],max_rounds=2,response_file=first)
        print('Initial proposal saved; source unchanged:',src.read_bytes()==original)
        run_id=session['run_id']
        # Explicit approval in the opt-in local demo (not an autonomous permission).
        approve(project,run_id,approved=True)
        failed=test(project,run_id,trust_project_code=True)
        print('Round 1:',failed['stage'],'passed:',failed['all_passed'])
        if failed['stage']!='awaiting_repair':raise RuntimeError('expected the first test to fail')
        second=response(src,folder/'round2.json','return f"Hello {name}?"',
                        'return f"Hello {name}!"',task,task_id)
        repair(project,run_id,response_file=second)
        approve(project,run_id,approved=True)
        passed=test(project,run_id,trust_project_code=True)
        print('Round 2:',passed['stage'],'passed:',passed['all_passed'])
        if passed['stage']!='completed':raise RuntimeError('repair did not pass')
        rolled_back=abort(project,run_id,restore=True,approved=True)
        print('Rollback:',rolled_back['stage'],'original restored:',src.read_bytes()==original)
        assert src.read_bytes()==original


if __name__=='__main__':main()
