"""V3.4 regression: symbol impact, offline metrics, opt-in GitHub boundary."""
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
from orchestrator.git_collab import branch, commit, draft_pr
from orchestrator.workflow import apply, load_proposal, verify
from orchestrator.github_ci import _repo_from_origin, checks, publish
from tools.semantic_impact import analyze
from tools.loop_metrics import summarize

ROOT=Path(__file__).resolve().parents[1]


class SemanticImpactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.p=Path(self.tmp.name)
        (self.p/'src').mkdir();(self.p/'tests').mkdir()
        (self.p/'src/util.py').write_text('def greet(name: str) -> str:\n    return name\n')
        (self.p/'src/app.py').write_text('from src.util import greet\nprint(greet("hi"))\n')
        (self.p/'tests/test_app.py').write_text('from src.app import foo\n')
        self.git('init','-b','main')
        self.git('config','user.email','test@invalid.example')
        self.git('config','user.name','Test')
        self.git('add','.')
        self.git('commit','-m','baseline')
    def git(self,*args):
        return subprocess.run(['git',*args],cwd=self.p,check=True,capture_output=True,text=True).stdout
    def tearDown(self):self.tmp.cleanup()
    def test_changed_signature_and_importer(self):
        (self.p/'src/util.py').write_text('def greet(name: str, suffix: str="!") -> str:\n    return name + suffix\n')
        report=analyze(self.p,['src/util.py'])
        self.assertIn({'name':'greet','kind':'signature_changed'},report['changed'][0]['symbol_changes'])
        self.assertEqual(report['changed'][0]['candidate_importers'][0]['path'],'src/app.py')
        self.assertIn('tests/test_app.py',[x['path'] for x in report['dependency_impact']['affected_dependents']])
    def test_added_removed_symbols(self):
        (self.p/'src/util.py').write_text('def renamed(name):\n    return name\n')
        changes=analyze(self.p,['src/util.py'])['changed'][0]['symbol_changes']
        self.assertEqual({(x['name'],x['kind']) for x in changes},{('renamed','added'),('greet','removed')})
    def test_syntax_error_indicated_not_executed(self):
        (self.p/'src/util.py').write_text('def invalid(:\n')
        self.assertTrue(analyze(self.p,['src/util.py'])['changed'][0]['parse_error'])
    def test_no_baseline(self):
        (self.p/'src/new.py').write_text('VALUE=1')
        self.assertFalse(analyze(self.p,['src/new.py'])['changed'][0]['baseline_available'])
    def test_reject_unsafe_paths(self):
        with self.assertRaises(ValueError):analyze(self.p,['../../passwd'])


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def record(self,run_id,status,attempts):
        folder=self.p/'.ai/loops'/run_id
        folder.mkdir(parents=True)
        s={'schema_version':1,'run_id':run_id,'stage':status,
           'created_at':'2026-11-06T01:00:00+00:00','updated_at':'2026-11-06T01:02:00+00:00',
           'task':'Never leak my private task details','attempts':[{'status':a} for a in attempts]}
        (folder/'state.json').write_text(json.dumps(s))
    def test_empty(self):
        self.assertEqual(summarize(self.p)['runs'],0)
        self.assertIsNone(summarize(self.p)['completion_rate'])
    def test_aggregates_without_task_text(self):
        self.record('loop-aaaa','completed',['failed','passed'])
        self.record('loop-bbbb','exhausted',['failed'])
        s=summarize(self.p)
        self.assertEqual((s['runs'],s['completed'],s['failed_attempts'],s['passed_attempts']),(2,1,2,1))
        self.assertEqual(s['completion_rate'],0.5)
        self.assertEqual(s['repaired_success_runs'],1)
        self.assertEqual(s['first_pass_success_runs'],0)
        self.assertEqual(s['p95_elapsed_seconds'],120)
        self.assertEqual(s['attempt_distribution']['2'],1)
        self.assertEqual(s['mean_elapsed_seconds'],120)
        self.assertNotIn('Never leak',json.dumps(s))
    def test_bad_state_skipped(self):
        self.record('loop-aaaa','completed',['passed'])
        self.record('loop-bbbb','completed',['invalid'])
        r=summarize(self.p)
        self.assertEqual(r['runs'],1);self.assertTrue(r['warnings'])
    def test_symlink_rejected(self):
        outside=self.p/'outside';outside.mkdir()
        (self.p/'.ai').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'unsafe'):summarize(self.p)
    def test_single_round_first_pass(self):
        self.record('loop-aaaa','completed',['passed'])
        r=summarize(self.p)
        self.assertEqual(r['first_pass_success_rate'],1)
        self.assertEqual(r['attempt_distribution']['1'],1)
    def test_max_runs_enforced(self):
        self.record('loop-aaaa','completed',['passed'])
        self.record('loop-bbbb','completed',['passed'])
        with self.assertRaises(ValueError):summarize(self.p,max_runs=1)


class GithubTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'p'
        shutil.copytree(ROOT/'examples/workflow-demo',self.p,ignore=shutil.ignore_patterns('__pycache__'))
        init(self.p)
        enable_test_checks(self.p)
        (self.p/'.gitignore').write_text('.ai/\n')
        self.git('init','-b','main')
        self.git('config','user.name','Test User')
        self.git('config','user.email','test@invalid.example')
        self.git('remote','add','origin','https://github.com/example/repository.git')
        self.git('add','.')
        self.git('commit','-m','baseline')
    def tearDown(self):self.tmp.cleanup()
    def git(self,*a):
        return subprocess.run(['git',*a],cwd=self.p,check=True,capture_output=True,text=True).stdout
    def test_origin_repo(self):
        self.assertEqual(_repo_from_origin(self.p),'example/repository')
    def test_bad_origin(self):
        self.git('remote','set-url','origin','https://github.evil.com/example/repository')
        with self.assertRaisesRegex(ValueError,'github.com'):checks(self.p,1)
    def test_checks_no_network_preview(self):
        with patch('orchestrator.github_ci._call_gh',side_effect=AssertionError('network was used')):
            report=checks(self.p,123)
        self.assertFalse(report['network_access'])
        self.assertIn('--json',report['command'])
    def test_checks_empty_not_passed(self):
        with patch('orchestrator.github_ci._call_gh',return_value={'number':123,'url':'x','state':'OPEN','statusCheckRollup':[]}):
            report=checks(self.p,123,execute=True)
        self.assertFalse(report['all_checks_successful'])
    def test_checks_mixed_status(self):
        r={'number':123,'url':'x','state':'OPEN','statusCheckRollup':[{'name':'lint','conclusion':'SUCCESS'},{'name':'tests','status':'IN_PROGRESS'}]}
        with patch('orchestrator.github_ci._call_gh',return_value=r):
            self.assertFalse(checks(self.p,123,execute=True)['all_checks_successful'])
    def _prepare(self):
        branch(self.p,'ai/feature',approved=True)
        ch=apply(self.p,load_proposal(self.p/'proposal.json'),approved=True)
        cid=ch['change_id']
        verify(self.p,cid,execute=True)
        commit(self.p,cid,'Fix greeting punctuation',approved=True)
        draft_pr(self.p,cid,'Fix greeting punctuation')
        return cid
    def test_publish_requires_local_commit_and_draft(self):
        cid=self._prepare()
        with patch('orchestrator.github_ci._create_remote_draft',side_effect=AssertionError('network was used')):
            preview=publish(self.p,cid,title='Fix greeting punctuation')
        self.assertFalse(preview['published'])
        self.assertFalse(preview['network_access'])
        with self.assertRaisesRegex(ValueError,'approve'):
            publish(self.p,cid,title='Fix greeting punctuation',execute=True)
    def test_publish_approved_mocked_gh(self):
        cid=self._prepare()
        class Response:
            returncode=0
            stdout=b'https://github.com/example/repository/pull/17\n'
            stderr=b''
        with patch('orchestrator.github_ci._create_remote_draft',return_value='https://github.com/example/repository/pull/17') as mock:
            out=publish(self.p,cid,title='Fix greeting punctuation',execute=True,approved=True)
        self.assertTrue(out['published']);self.assertIn('--draft',mock.call_args.args[0])
    def test_publish_refuses_mismatched_commit(self):
        cid=self._prepare()
        (self.p/'bad.py').write_text('print(1)')
        with self.assertRaisesRegex(ValueError,'clean'):
            publish(self.p,cid,title='Fix greeting punctuation')
    def test_publish_cli_error_hides_secrets(self):
        cid=self._prepare()
        class Response:
            returncode=1
            stdout=b''
            stderr=b'gh secret private token=DO_NOT_ECHO'
        with patch('orchestrator.github_ci.shutil.which',return_value='/usr/bin/gh'),patch('orchestrator.github_ci.subprocess.run',return_value=Response()):
            with self.assertRaises(ValueError) as e:
                from orchestrator.github_ci import _create_remote_draft
                _create_remote_draft(['pr','create'],'example/repository')
        self.assertNotIn('DO_NOT_ECHO',str(e.exception))


if __name__ == '__main__':unittest.main()
