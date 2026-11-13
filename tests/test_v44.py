"""V4.4 independent trusted local Git integration and fail-closed review tests."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from orchestrator.cli import init
from orchestrator.workflow import apply
from tools.repo_readiness_v44 import inspect,conflicts,readiness,review_ci_receipt
from tools.repo_trial_v44 import sample

ROOT=Path(__file__).resolve().parents[1]


class V44ReadinessTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='v44-readiness-')
        self.addCleanup(tmp.cleanup)
        self.p=Path(tmp.name)/'independent-business-repo'
        self.p.mkdir()
        (self.p/'src').mkdir()
        (self.p/'src'/'service.py').write_text('def greeting():\n    return "hello"\n','utf-8')
        (self.p/'pyproject.toml').write_text('[project]\nname="local-business"\nversion="0.1"\n','utf-8')
        (self.p/'.gitignore').write_text('.ai/\n','utf-8')
        self.git('init','-b','main')
        self.git('config','user.name','V44 Fixture')
        self.git('config','user.email','fixture@invalid.example')
        self.git('add','.')
        self.git('commit','-m','Independent project baseline')
        self.head=self.git('rev-parse','HEAD')
    def git(self,*args):
        result=subprocess.run(['git','-C',str(self.p),*args],check=True,
                              capture_output=True,text=True,timeout=8)
        return result.stdout.strip()
    def make_receipt(self, *, sha=None, conclusion='success', status='completed', checks=None):
        p=self.p.parent/'ci-receipt.json'
        doc={'schema_version':1,'provider':'github-actions','run_id':'offline_17',
             'commit':sha or self.head,'checks':checks if checks is not None else [
                {'name':'lint','status':status,'conclusion':conclusion},
                {'name':'tests','status':'completed','conclusion':'success'}]}
        p.write_text(json.dumps(doc),'utf-8');return p
    def applied(self,task_id='BIZ-1',old='hello',new='hello!'):
        src=self.p/'src/service.py'
        proposal={'schema_version':3,'task_id':task_id,'summary':'Update business greeting for review',
                'changes':[{'action':'replace','path':'src/service.py',
                            'expected_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                            'old_text':old,'new_text':new}]}
        return apply(self.p,proposal,approved=True)['change_id']

    def test_real_independent_git_intake_is_read_only(self):
        before=(self.p/'src/service.py').read_bytes()
        data=inspect(self.p,expected_head=self.head)
        self.assertEqual(data['git']['dirty_entries'],0)
        self.assertIn('python',data['detected_stacks'])
        self.assertFalse(data['ai_initialized'])
        self.assertEqual((self.p/'src/service.py').read_bytes(),before)
        self.assertFalse((self.p/'.ai').exists())
        self.assertEqual(readiness(self.p)['status'],'needs_initialization')

    def test_initialized_project_is_reviewable(self):
        init(self.p)
        result=readiness(self.p,expected_head=self.head,require_clean=True)
        self.assertEqual(result['status'],'reviewable')
        self.assertEqual(result['audit_summary']['counts']['changes'],0)

    def test_wrong_pinned_head_is_blocked(self):
        self.assertEqual(readiness(self.p,expected_head='0'*40)['status'],'blocked')
        with self.assertRaises(ValueError):inspect(self.p,expected_head='invalid')

    def test_require_clean_blocks_modified_source(self):
        init(self.p)
        (self.p/'src/service.py').write_text('other source','utf-8')
        self.assertEqual(readiness(self.p,require_clean=True)['status'],'blocked')
        self.assertEqual(readiness(self.p,require_clean=False)['status'],'reviewable')

    def test_active_changes_overlap_and_candidate_conflict(self):
        init(self.p)
        cid1=self.applied()
        cid2=self.applied('BIZ-2','hello!','goodbye')
        info=conflicts(self.p,candidate_paths=['src/service.py'])
        self.assertEqual(info['active_change_count'],2)
        self.assertEqual(len(info['overlaps']),1)
        self.assertEqual(set(info['overlaps'][0]['change_ids']),{cid1,cid2})
        self.assertTrue(info['candidate_conflicts'])
        self.assertEqual(readiness(self.p)['status'],'blocked')

    def test_casefold_path_conflict_detection(self):
        init(self.p);self.applied()
        self.assertTrue(conflicts(self.p,candidate_paths=['SRC/SERVICE.PY'])['candidate_conflicts'])
        self.assertFalse(conflicts(self.p,candidate_paths=['src/unrelated.py'])['candidate_conflicts'])

    def test_prepared_change_requires_review(self):
        init(self.p);cid=self.applied()
        manifest=self.p/'.ai/changes'/cid/'manifest.json'
        obj=json.loads(manifest.read_text('utf-8'))
        obj['status']='prepared';manifest.write_text(json.dumps(obj),'utf-8')
        self.assertEqual(readiness(self.p)['status'],'blocked')

    def test_symlink_change_folder_fails_closed(self):
        init(self.p)
        target=self.p/'.ai/changes';target.mkdir(exist_ok=True)
        symlink=target/'fake'
        try:symlink.symlink_to(self.p, target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('symlinks unsupported')
        self.assertTrue(conflicts(self.p)['blockers'])

    def test_symlink_ci_receipt_refused(self):
        receipt=self.make_receipt()
        link=receipt.parent/'linked.json'
        try:link.symlink_to(receipt)
        except (OSError,NotImplementedError):self.skipTest('symlinks unsupported')
        with self.assertRaises(ValueError):review_ci_receipt(link,expected_head=self.head)

    def test_candidate_symlink_rejected(self):
        link=self.p/'shortcut'
        try:link.symlink_to(self.p/'src',target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('symlinks unsupported')
        with self.assertRaisesRegex(ValueError,'symlink'):
            conflicts(self.p,candidate_paths=['shortcut/service.py'])

    def test_ci_local_claim_matches_pinned_head(self):
        r=review_ci_receipt(self.make_receipt(),expected_head=self.head,required_checks=['lint','tests'])
        self.assertTrue(r['eligible_as_unverified_ci_signal'])
        self.assertEqual(r['source_trust'],'unsigned-local-JSON')
        self.assertNotIn('PRIVATE',json.dumps(r))

    def test_ci_commit_mismatch_blocked(self):
        self.assertFalse(review_ci_receipt(self.make_receipt(sha='0'*40),expected_head=self.head)['eligible_as_unverified_ci_signal'])
        self.assertEqual(readiness(self.p,ci_receipt=self.make_receipt(sha='0'*40))['status'],'blocked')

    def test_ci_missing_required_check_blocked(self):
        r=review_ci_receipt(self.make_receipt(),expected_head=self.head,required_checks=['integration'])
        self.assertEqual(r['missing_required_checks'],['integration'])
        self.assertFalse(r['eligible_as_unverified_ci_signal'])

    def test_ci_incomplete_or_failed_does_not_pass(self):
        for status, conclusion in [('completed','failure'),('in_progress',None)]:
            with self.subTest(status=status):
                r=review_ci_receipt(self.make_receipt(status=status,conclusion=conclusion),expected_head=self.head)
                self.assertFalse(r['eligible_as_unverified_ci_signal'])

    def test_ci_duplicate_names_rejected(self):
        duplicate=[{'name':'tests','status':'completed','conclusion':'success'}]*2
        with self.assertRaisesRegex(ValueError,'duplicate'):
            review_ci_receipt(self.make_receipt(checks=duplicate),expected_head=self.head)

    def test_ci_size_limit_enforced(self):
        receipt=self.make_receipt();receipt.write_bytes(b'a'*128001)
        with self.assertRaisesRegex(ValueError,'oversized'):
            review_ci_receipt(receipt,expected_head=self.head)

    def test_required_checks_without_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError,'require --ci-receipt'):
            readiness(self.p,required_checks=['tests'])

    def test_require_ci_missing_is_blocked(self):
        init(self.p)
        result=readiness(self.p,require_ci=True)
        self.assertEqual(result['status'],'blocked')
        self.assertIn('required offline CI receipt missing',result['blockers'])

    def test_reviewable_with_unsigned_ci_contains_warning(self):
        init(self.p)
        r=readiness(self.p,ci_receipt=self.make_receipt(),require_ci=True,
                    required_checks=['tests'])
        self.assertEqual(r['status'],'reviewable')
        self.assertTrue(any('unsigned' in text for text in r['warnings']))

    def test_cli_exposes_readiness_and_conflicts_and_exits_blocked(self):
        init(self.p)
        cmd=[sys.executable,str(ROOT/'fullstack.py'),'repo-readiness','--project',str(self.p),'--expected-head',self.head]
        ok=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertEqual(json.loads(ok.stdout)['status'],'reviewable')
        bad=subprocess.run(cmd+['--require-ci'],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(bad.returncode,1,bad.stderr)
        self.applied()
        cmd=[sys.executable,str(ROOT/'fullstack.py'),'repo-conflicts','--project',str(self.p),'--candidate','src/service.py']
        bad=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(bad.returncode,1,bad.stderr)

    def test_inspection_does_not_leak_source_text(self):
        (self.p/'src/service.py').write_text('TOP_SECRET_DO_NOT_RETURN','utf-8')
        result=readiness(self.p)
        self.assertNotIn('TOP_SECRET_DO_NOT_RETURN',json.dumps(result))

    def test_candidate_path_traversal_rejected(self):
        with self.assertRaises(ValueError):conflicts(self.p,candidate_paths=['../secret.env'])
        with self.assertRaises(ValueError):conflicts(self.p,candidate_paths=['.git/config'])
        with self.assertRaises(ValueError):conflicts(self.p,candidate_paths=['C:drive-path'])

    def test_reliability_samples_real_git_read_only(self):
        init(self.p)
        result=sample(self.p,repeats=4,expected_head=self.head,require_clean=True)
        self.assertTrue(result['all_reviewable'])
        self.assertTrue(result['stable_head'])
        self.assertEqual(result['samples'],4)
        self.assertEqual(len(result['snapshots']),4)
        self.assertFalse((self.p/'.ai'/'loops').exists())

    def test_reliability_samples_gate_failures(self):
        init(self.p)
        result=sample(self.p,repeats=2,require_ci=True)
        self.assertFalse(result['all_reviewable'])
        with self.assertRaises(ValueError):sample(self.p,repeats=31)

    def test_cli_repo_trial(self):
        init(self.p)
        r=subprocess.run([sys.executable,str(ROOT/'fullstack.py'),'repo-trial',
            '--project',str(self.p),'--samples','2','--require-clean'],
            cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['samples'],2)

    def test_js_business_repo_stack_recognized(self):
        other=self.p.parent/'independent-js-repo'
        other.mkdir()
        (other/'package.json').write_text('{"name":"local-js","scripts":{"test":"no-op"}}','utf-8')
        (other/'tsconfig.json').write_text('{}','utf-8')
        subprocess.run(['git','-C',str(other),'init','-b','main'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(other),'config','user.name','Fixture'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(other),'config','user.email','fixture@invalid.example'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(other),'add','.'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(other),'commit','-m','Initial JS fixture'],check=True,capture_output=True)
        self.assertEqual(inspect(other)['detected_stacks'],['node','typescript'])

    def test_not_git_repo_rejected(self):
        other=self.p.parent/'not-a-repo';other.mkdir()
        with self.assertRaises(ValueError):inspect(other)

if __name__=='__main__':unittest.main()
