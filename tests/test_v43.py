"""V4.3 independent local Git, evidence integrity, audit and safety tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from orchestrator.cli import init, add_task
from orchestrator.workflow import apply, verify
from orchestrator.git_collab import branch, commit
from tools.repo_health_v43 import audit

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v43_demo',ROOT/'examples/v43-repo-demo/run_demo.py')
demo=importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class LiveGitAuditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='v43-audit-')
        self.addCleanup(tmp.cleanup)
        self.p=Path(tmp.name)/'repo'
        shutil.copytree(ROOT/'examples/workflow-demo',self.p,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc','.ai'))
        (self.p/'.gitignore').write_text('.ai/\n','utf-8')
        self.git('init','-b','main')
        self.git('config','user.name','Local Fixture')
        self.git('config','user.email','local@invalid.example')
        self.git('add','.')
        self.git('commit','-m','Fixture baseline')
        init(self.p)
        data=json.loads((self.p/'.ai/checks.json').read_text('utf-8'))
        data['checks'][0]['enabled']=True
        (self.p/'.ai/checks.json').write_text(json.dumps(data),'utf-8')

    def git(self,*args):
        return subprocess.run(['git','-C',str(self.p),*args],check=True,capture_output=True,text=True).stdout.strip()

    def change(self,old='return f"Hello {name}"',new='return f"Hello {name}!"',task='V43-1'):
        src=self.p/'src/formatter.py'
        proposal={'schema_version':3,'task_id':task,'summary':'Fix local fixture greeting behavior',
                  'changes':[{'action':'replace','path':'src/formatter.py',
                             'expected_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                             'old_text':old,'new_text':new}]}
        return apply(self.p,proposal,approved=True)['change_id']

    def _pass(self):
        branch(self.p,'ai/v43',approved=True)
        cid=self.change()
        result=verify(self.p,cid,execute=True,close_task=True)
        self.assertTrue(result['all_passed'])
        return cid,result

    def test_audit_clean_repository_and_head(self):
        sha=self.git('rev-parse','HEAD')
        result=audit(self.p,expected_head=sha,require_clean=True)
        self.assertTrue(result['healthy']);self.assertEqual(result['counts']['tasks'],0)

    def test_dirty_repository_fail_closed_when_requested(self):
        (self.p/'src/formatter.py').write_text('changed outside workflow','utf-8')
        result=audit(self.p,require_clean=True)
        self.assertFalse(result['healthy']);self.assertIn('working tree not clean',result['errors'])

    def test_pinned_git_head_rejects_mismatch(self):
        self.assertFalse(audit(self.p,expected_head='0'*40)['healthy'])
        with self.assertRaises(ValueError):audit(self.p,expected_head='not-a-sha')

    def test_applied_source_drift_detected(self):
        cid=self.change()
        (self.p/'src/formatter.py').write_text('drifted','utf-8')
        result=audit(self.p)
        self.assertFalse(result['healthy'])
        self.assertTrue(any('applied source' in m for m in result['errors']))

    def test_prepared_change_warns_after_interruption(self):
        cid=self.change()
        path=self.p/'.ai/changes'/cid/'manifest.json'
        info=json.loads(path.read_text('utf-8'));info['status']='prepared'
        path.write_text(json.dumps(info),'utf-8')
        result=audit(self.p)
        self.assertEqual(result['counts']['prepared'],1)
        self.assertTrue(any('interrupted' in m for m in result['warnings']))

    def test_completed_task_with_no_evidence_rejected(self):
        add_task(self.p,'broken','Broken completion')
        path=self.p/'.ai/task_state.json'
        info=json.loads(path.read_text('utf-8'))
        info['tasks'][0]['status']='done'
        path.write_text(json.dumps(info),'utf-8')
        self.assertFalse(audit(self.p)['healthy'])

    def test_approved_commit_requires_intact_report(self):
        cid,result=self._pass()
        report=self.p/result['report']
        report.write_bytes(report.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'integrity mismatch'):
            commit(self.p,cid,'Fix trusted demo issue',approved=True)
        self.assertFalse(audit(self.p)['healthy'])

    def test_failing_recheck_invalidates_prior_pass(self):
        cid,_=self._pass()
        path=self.p/'.ai/checks.json'
        data=json.loads(path.read_text('utf-8'))
        data['checks'][0]['args']=['python','-c','print(1)']
        path.write_text(json.dumps(data),'utf-8')
        self.assertFalse(verify(self.p,cid,execute=True)['all_passed'])
        with self.assertRaisesRegex(ValueError,'no executed passing test'):
            commit(self.p,cid,'Fix trusted demo issue',approved=True)

    def test_git_head_changes_after_checks_rejected(self):
        cid,_=self._pass()
        self.git('commit','--allow-empty','-m','Another local commit')
        with self.assertRaisesRegex(ValueError,'HEAD changed since verification'):
            commit(self.p,cid,'Fix trusted demo issue',approved=True)

    def test_commit_marks_record_historical(self):
        cid,_=self._pass()
        committed=commit(self.p,cid,'Fix trusted demo issue',approved=True)
        rec=json.loads((self.p/'.ai/changes'/cid/'manifest.json').read_text('utf-8'))
        self.assertEqual(rec['status'],'committed')
        self.assertEqual(rec['git_commit'],committed['commit'])
        self.assertEqual(audit(self.p,require_clean=True)['counts']['committed'],1)
        # Subsequent source edits are valid: the original Git object is immutable.
        self.change('return f"Hello {name}!"','return f"Hello {name}!"  # follow-up','V43-2')
        self.assertTrue(audit(self.p)['healthy'])

    def test_committed_snapshot_checksum_detects_record_corruption(self):
        cid,_=self._pass()
        commit(self.p,cid,'Fix trusted demo issue',approved=True)
        path=self.p/'.ai/changes'/cid/'manifest.json'
        data=json.loads(path.read_text('utf-8'))
        data['files'][0]['after_sha256']='0'*64
        path.write_text(json.dumps(data),'utf-8')
        self.assertFalse(audit(self.p)['healthy'])

    def test_symlinked_state_rejected(self):
        target=self.p/'.ai'
        target.rename(self.p/'moved-state')
        try:target.symlink_to(self.p/'moved-state',target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError,'symlinked'):
            audit(self.p)

    def test_audit_does_not_output_source_or_test_logs(self):
        source=self.p/'src/formatter.py'
        source.write_text('PRIVATE_SOURCE_DO_NOT_PRINT\n','utf-8')
        result=audit(self.p)
        self.assertNotIn('PRIVATE_SOURCE_DO_NOT_PRINT',json.dumps(result))

    def test_cli_exposes_read_only_audit(self):
        ok=subprocess.run([sys.executable,str(ROOT/'fullstack.py'),'audit-repo','--project',str(self.p),'--require-clean'],
                          cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertTrue(json.loads(ok.stdout)['healthy'])
        (self.p/'newfile.txt').write_text('uncommitted','utf-8')
        bad=subprocess.run([sys.executable,str(ROOT/'fullstack.py'),'audit-repo','--project',str(self.p),'--require-clean'],
                           cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(bad.returncode,1)

    def test_read_only_audit_does_not_modify_files(self):
        state=self.p/'.ai/task_state.json';before=state.read_bytes()
        audit(self.p)
        self.assertEqual(before,state.read_bytes())


class MultiCommitIntegrationTests(unittest.TestCase):
    def test_preview_mode_never_executes_fixture_tests(self):
        result=demo.exercise()
        self.assertEqual(result['executed_tests'],0)
        self.assertEqual(result['remote_operations'],0)

    def test_three_real_local_commits_and_evidence(self):
        result=demo.exercise(execute_tests=True,rounds=3)
        self.assertEqual(result['commits_created'],3)
        self.assertEqual(result['unique_commits'],3)
        self.assertTrue(result['worktree_clean'])
        self.assertEqual(result['verified_completed_tasks'],3)
        self.assertTrue(result['audit_healthy'])

    def test_invalid_round_limit_fails(self):
        with self.assertRaises(ValueError):demo.exercise(rounds=6)


if __name__=='__main__':unittest.main()
