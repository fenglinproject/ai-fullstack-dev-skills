"""V3.3 integration + safety regression tests; do not need Docker daemon."""
from tests.fixture_optin import enable_test_checks
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.cli import init
from orchestrator.workflow import apply,load_proposal,verify
from orchestrator.code_review import review
from orchestrator.git_collab import branch,commit,draft_pr
from tools.dependency_graph import graph
from tools.isolated_checks import check_image,run,snapshot

ROOT=Path(__file__).resolve().parents[1]
IMAGE='python@sha256:'+'a'*64

class IsolatedChecksTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.project=Path(self.tmp.name)/'p';self.project.mkdir()
        (self.project/'tests').mkdir()
        (self.project/'tests/test_a.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        init(self.project)
        cfg=self.project/'.ai/checks.json'
        obj=json.loads(cfg.read_text());obj['checks'][0]['enabled']=True
        cfg.write_text(json.dumps(obj))
    def tearDown(self):self.tmp.cleanup()
    def test_requires_pinned_image(self):
        for bad in ['python:3.11','evil@sha256:'+'z'*64,'','python@sha256:'+'A'*64]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):check_image(bad)
    def test_preview_does_not_start_container(self):
        with patch('tools.isolated_checks.subprocess.run',side_effect=AssertionError('executed!')):
            result=run(self.project,IMAGE)
        self.assertFalse(result['actually_executed']);self.assertEqual(result['checks'][0]['status'],'planned_only')
        cmd=result['checks'][0]['command']
        self.assertIn('--network',cmd);self.assertIn('none',cmd);self.assertIn('--cap-drop',cmd)
        self.assertIn('ALL',cmd);self.assertIn('--read-only',cmd);self.assertIn('--pull',cmd);self.assertIn('never',cmd)
    def test_secrets_not_copied(self):
        (self.project/'.env').write_text('SECRET=abc')
        (self.project/'my.key').write_text('secret')
        with tempfile.TemporaryDirectory() as dst:
            snap=Path(dst);stats=snapshot(self.project,snap)
            self.assertFalse((snap/'.env').exists());self.assertFalse((snap/'my.key').exists())
            self.assertTrue((snap/'tests/test_a.py').is_file());self.assertGreaterEqual(stats['skipped_files'],2)
    def test_symlink_snapshot_blocked(self):
        outside=Path(self.tmp.name)/'secret';outside.write_text('hi')
        try:(self.project/'linked.py').symlink_to(outside)
        except (NotImplementedError,OSError):self.skipTest('symlink unsupported')
        with tempfile.TemporaryDirectory() as dst:
            with self.assertRaisesRegex(ValueError,'symlink'):snapshot(self.project,Path(dst))
    def test_docker_unsupported_fails_closed(self):
        with patch('tools.isolated_checks.shutil.which',return_value=None):
            with self.assertRaisesRegex(ValueError,'not installed'):run(self.project,IMAGE,execute=True)
    def test_mocked_docker_invocation(self):
        class Finished:
            returncode=0;stdout='ok';stderr=''
        with patch('tools.isolated_checks.shutil.which',return_value='/usr/bin/docker'),patch('tools.isolated_checks.subprocess.run',return_value=Finished()) as p:
            res=run(self.project,IMAGE,execute=True)
        self.assertEqual(res['checks'][0]['status'],'passed')
        cmd=p.call_args.args[0]
        self.assertEqual(cmd[0:2],['docker','run']);self.assertIn('--user',cmd)
        self.assertIn('--mount',cmd);self.assertIn('--security-opt',cmd)

class GraphAndReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        (self.p/'src').mkdir();(self.p/'tests').mkdir()
        (self.p/'src/util.py').write_text('VALUE = 1\n')
        (self.p/'src/app.py').write_text('from src import util\n')
        (self.p/'tests/test_app.py').write_text('from src.app import f\n')
        (self.p/'src/helper.ts').write_text('export const foo = 1\n')
        (self.p/'src/view.tsx').write_text('import {foo} from "./helper";\n')
    def tearDown(self):self.tmp.cleanup()
    def test_reverse_python_graph(self):
        r=graph(self.p,['src/util.py'])
        paths=[x['path'] for x in r['affected_dependents']]
        self.assertIn('src/app.py',paths);self.assertIn('tests/test_app.py',paths)
    def test_typescript_graph(self):
        r=graph(self.p,['src/helper.ts'])
        self.assertIn('src/view.tsx',[x['path'] for x in r['affected_dependents']])
    def test_reject_traversal(self):
        with self.assertRaises(ValueError):graph(self.p,['../x.py'])
    def test_static_review_finds_suspicious_additions(self):
        init(self.p)
        raw=(self.p/'src/util.py').read_bytes()
        proposal={'schema_version':3,'task_id':'REV-1','summary':'Inspect suspicious new operation',
                  'changes':[{'action':'replace','path':'src/util.py','expected_sha256':hashlib.sha256(raw).hexdigest(),
                              'old_text':'VALUE = 1','new_text':'VALUE = 1\nresult = eval("3+4")  # TODO'}]}
        changed=apply(self.p,proposal,approved=True)
        out=review(self.p,changed['change_id'])
        self.assertGreaterEqual(out['counts']['medium'],1)
        self.assertGreaterEqual(out['counts']['low'],1)
        self.assertIn('src/app.py',[x['path'] for x in out['import_impact']['affected_dependents']])

class GitCollabTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'p'
        shutil.copytree(ROOT/'examples/workflow-demo',self.p,ignore=shutil.ignore_patterns('__pycache__'))
        init(self.p)
        enable_test_checks(self.p)
        (self.p/'.gitignore').write_text('.ai/\n')
        def cmd(*a):
            return subprocess.run(['git',*a],cwd=self.p,check=True,capture_output=True,text=True).stdout.strip()
        self.cmd=cmd
        cmd('init','-b','main');cmd('config','user.name','Test User');cmd('config','user.email','test@invalid.example')
        cmd('add','.');cmd('commit','-m','initial fixture')
    def tearDown(self):self.tmp.cleanup()
    def test_branch_requires_approval_and_clean_tree(self):
        with self.assertRaisesRegex(ValueError,'approve'):branch(self.p,'ai/test',approved=False)
        (self.p/'unexpected.txt').write_text('extra')
        with self.assertRaisesRegex(ValueError,'clean'):branch(self.p,'ai/test',approved=True)
    def test_branch_commit_and_offline_pr_draft(self):
        out=branch(self.p,'ai/demo',approved=True)
        self.assertEqual(out['branch'],'ai/demo')
        with self.assertRaisesRegex(ValueError,'approve'):commit(self.p,'abc','Good patch',approved=False)
        changed=apply(self.p,load_proposal(self.p/'proposal.json'),approved=True)
        cid=changed['change_id']
        with self.assertRaisesRegex(ValueError,'test report'):commit(self.p,cid,'Fix greeting punctuation',approved=True)
        result=verify(self.p,cid,execute=True)
        self.assertTrue(result['all_passed'])
        # Explicit hook override prevents a malicious local pre-commit hook.
        hook=self.p/'.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\ntouch "'+str(self.p/'HACKED')+'"\n')
        hook.chmod(0o755)
        outcome=commit(self.p,cid,'Fix greeting punctuation',approved=True)
        self.assertEqual(outcome['branch'],'ai/demo')
        self.assertFalse((self.p/'HACKED').exists())
        draft=draft_pr(self.p,cid,'Fix greeting punctuation')
        self.assertFalse(draft['published']);self.assertTrue((self.p/draft['draft']).is_file())
        self.assertEqual(self.cmd('status','--porcelain'),'')
        self.assertEqual(self.cmd('log','-1','--format=%s'),'Fix greeting punctuation')
    def test_commit_refuses_unrelated_files_even_with_valid_evidence(self):
        branch(self.p,'ai/demo',approved=True)
        changed=apply(self.p,load_proposal(self.p/'proposal.json'),approved=True)
        verify(self.p,changed['change_id'],execute=True)
        (self.p/'unrelated.py').write_text('a=1')
        with self.assertRaisesRegex(ValueError,'unrelated'):commit(self.p,changed['change_id'],'Fix greeting punctuation',approved=True)

if __name__=='__main__':unittest.main()

class IsolatedWorkflowWiringTests(unittest.TestCase):
    def test_workflow_verify_with_mocked_docker_evidence(self):
        # Proves V3.3 Docker report can be consumed by V3 workflow, but does
        # not assert a container actually ran.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p'
            shutil.copytree(ROOT/'examples/workflow-demo',p,ignore=shutil.ignore_patterns('__pycache__'))
            init(p)
            cfg=p/'.ai/checks.json'
            settings=json.loads(cfg.read_text())
            for c in settings['checks']:c['enabled']=True
            cfg.write_text(json.dumps(settings))
            cid=apply(p,load_proposal(p/'proposal.json'),approved=True)['change_id']
            class DockerResult:
                returncode=0;stdout='simulated container output';stderr=''
            with patch('tools.isolated_checks.shutil.which',return_value='/usr/bin/docker'),patch('tools.isolated_checks.subprocess.run',return_value=DockerResult()):
                report=verify(p,cid,execute=True,isolated_image=IMAGE)
            self.assertTrue(report['all_passed'])
            evidence=json.loads((p/report['report']).read_text())
            self.assertEqual(evidence['runner'],'docker')
            self.assertTrue(evidence['actually_executed'])

class LoopDockerPreflightTests(unittest.TestCase):
    def test_missing_docker_rejected_before_session_mutation(self):
        from orchestrator.loop import test as loop_test
        with patch('shutil.which',return_value=None):
            with self.assertRaisesRegex(ValueError,'test stage not changed'):
                loop_test(Path('/this-session-does-not-exist'),'irrelevant',isolated_image=IMAGE)
