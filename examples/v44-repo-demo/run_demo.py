#!/usr/bin/env python3
"""V4.4 independent trusted fixture: real local Git, offline CI, no remote actions.

Default is preview-only. --execute-tests explicitly runs the existing trusted
V4.3 local fixture test/commit process, never user project code.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from orchestrator.cli import init
from tools.repo_readiness_v44 import inspect,readiness
from tools.repo_trial_v44 import sample


def _git(root:Path,*args):
    p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=8)
    if p.returncode:raise RuntimeError('trusted local Git fixture failed')
    return p.stdout.strip()


def exercise(*,execute_tests:bool=False)->dict:
    with tempfile.TemporaryDirectory(prefix='v44-local-repository-') as td:
        root=Path(td)/'source-repo'
        root.mkdir()
        (root/'service.py').write_text('def greeting():\n    return "hello"\n','utf-8')
        (root/'pyproject.toml').write_text('[project]\nname="fixture-service"\nversion="0.1"\n','utf-8')
        (root/'.gitignore').write_text('.ai/\n','utf-8')
        _git(root,'init','-b','main')
        _git(root,'config','user.name','V44 Fixture')
        _git(root,'config','user.email','fixture@invalid.example')
        _git(root,'add','.')
        _git(root,'commit','-m','Pinned trusted fixture baseline')
        head=_git(root,'rev-parse','HEAD')
        # The source repository is not modified by intake/readiness/CI review.
        before=inspect(root,expected_head=head)
        init(root)  # explicit fixture setup only
        receipt=Path(td)/'local-ci.json'
        receipt.write_text(json.dumps({'schema_version':1,'provider':'local-ci','run_id':'trusted_fixture',
            'commit':head,'checks':[{'name':'fixture-lint','status':'completed','conclusion':'success'}]}),'utf-8')
        snapshot=readiness(root,expected_head=head,require_clean=True,require_ci=True,
                           ci_receipt=receipt,required_checks=['fixture-lint'])
        trial=sample(root,repeats=3,expected_head=head,require_clean=True,
                     require_ci=True,ci_receipt=receipt,required_checks=['fixture-lint'])
        if snapshot['status']!='reviewable' or not trial['all_reviewable']:
            raise RuntimeError('fixture intake was unexpectedly blocked')
        result={'mode':'local-read-only-trial','git_head_pinned':before['git']['head_matches_pin'],
                'ci_signal':'unsigned-offline-json','reliability_samples':trial['samples'],
                'readiness':snapshot['status'],'source_executed':False,'remote_operations':0}
        if execute_tests:
            from importlib.util import spec_from_file_location,module_from_spec
            spec=spec_from_file_location('v43_tested_demo',ROOT/'examples/v43-repo-demo/run_demo.py')
            mod=module_from_spec(spec);spec.loader.exec_module(mod)
            live=mod.exercise(execute_tests=True,rounds=2)
            result.update({'mode':'trusted-fixture-tests-authorized','source_executed':True,
                           'local_commits':live['commits_created'],'tested_pass':live['audit_healthy']})
        return result


def main(argv=None):
    p=argparse.ArgumentParser(description='V4.4 independent local Git and CI-readiness demo')
    p.add_argument('--execute-tests',action='store_true',help='explicitly execute bundled TRUSTED fixture tests')
    args=p.parse_args(argv)
    print(json.dumps(exercise(execute_tests=args.execute_tests),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
