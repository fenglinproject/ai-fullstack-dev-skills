#!/usr/bin/env python3
"""Three actual local Git commits with gated tests, only in a TEMPORARY fixture.

No network access, remote Git operations, model calls or production deployment.
--execute-tests is required before any project Python test code is executed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from dashboard.snapshot import snapshot
from orchestrator.cli import init
from orchestrator.workflow import apply,preview,verify
from orchestrator.git_collab import branch,commit,draft_pr
from tools.repo_health_v43 import audit


def _git(root:Path,*args:str)->str:
    p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=10,check=False)
    if p.returncode:raise RuntimeError('local Git operation failed: '+p.stderr[:150])
    return p.stdout.strip()


def exercise(*,execute_tests:bool=False,rounds:int=3)->dict:
    if not isinstance(rounds,int) or not 1<=rounds<=5:raise ValueError('rounds must be 1..5')
    with tempfile.TemporaryDirectory(prefix='v43-independent-repo-') as work:
        project=Path(work)/'repo'
        shutil.copytree(ROOT/'examples/workflow-demo',project,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc','.ai'))
        (project/'.gitignore').write_text('.ai/\n__pycache__/\n*.pyc\n','utf-8')
        _git(project,'init','-b','main')
        _git(project,'config','user.name','Fixture Operator')
        _git(project,'config','user.email','fixture@invalid.example')
        _git(project,'add','.')
        _git(project,'commit','-m','Baseline demo fixture')
        baseline=_git(project,'rev-parse','HEAD')
        if not execute_tests:
            # No source edits or tests, even in the disposable fixture.
            return {'mode':'preview-only','rounds_planned':rounds,
                    'git_baseline_pinned':bool(baseline), 'executed_tests':0,
                    'remote_operations':0,'temporary_repo_removed_on_exit':True}
        init(project)
        cfg=project/'.ai/checks.json'
        checks=json.loads(cfg.read_text('utf-8'))
        checks['checks'][0]['enabled']=True
        cfg.write_text(json.dumps(checks),encoding='utf-8')
        branch(project,'ai/v43-reliability',approved=True)
        commits=[]; reports=[]
        source=project/'src/formatter.py'
        for i in range(rounds):
            old=source.read_text('utf-8')
            if i==0:
                needle='return f"Hello {name}"'
                replacement='return f"Hello {name}!"'
            else:
                needle='return f"Hello {name}!"'+('  # verified iteration '+str(i) if i>1 else '')
                replacement='return f"Hello {name}!"  # verified iteration '+str(i+1)
            assert old.count(needle)==1
            change={'schema_version':3,'task_id':f'V43-{i+1}',
                    'summary':f'Improve verified fixture greeting iteration {i+1}',
                    'changes':[{'action':'replace','path':'src/formatter.py',
                                'expected_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                                'old_text':needle,'new_text':replacement}]}
            planned=preview(project,change)
            assert planned['approved'] is False and planned['files'][0]['diff']
            applied=apply(project,change,approved=True)
            validated=verify(project,applied['change_id'],execute=True,close_task=True)
            if not validated['all_passed']:raise RuntimeError('fixture tests unexpectedly failed')
            committed=commit(project,applied['change_id'],f'Fix fixture iteration {i+1}',approved=True)
            commits.append(committed['commit'])
            reports.append(validated['report'])
        change_id=applied['change_id']
        draft=draft_pr(project,change_id,'Fixture reliability review')
        view=snapshot(project)
        health=audit(project,require_clean=True)
        if not health['healthy'] or view['stats']['by_status']['done']!=rounds:
            raise RuntimeError('repository or dashboard verification failed')
        return {'mode':'trusted-tests-executed-in-temporary-repository','rounds':rounds,
                'git_branch':health['git']['branch'],'commits_created':len(commits),
                'unique_commits':len(set(commits)), 'passed_test_reports':len(reports),
                'verified_completed_tasks':view['stats']['by_status']['done'],
                'audit_healthy':health['healthy'],'worktree_clean':health['git']['dirty_entries']==0,
                'offline_pr_draft_created':bool(draft['draft']),
                'remote_operations':0,'temporary_repo_removed_on_exit':True,
                'limitations':'Bundled trusted fixture only; does not prove performance on public or unknown repositories.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Trusted local Git review and verification exercise')
    p.add_argument('--execute-tests',action='store_true',help='explicitly run project Python unit tests')
    p.add_argument('--rounds',type=int,default=3,help='1..5 actual verified local commits')
    a=p.parse_args(argv)
    print(json.dumps(exercise(execute_tests=a.execute_tests,rounds=a.rounds),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
