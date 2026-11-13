"""V3 integration/attack tests: preview, approval, rollback, drift, verify, handoff."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from orchestrator.cli import init, status
from orchestrator.workflow import (preflight, preview, apply, review, restore, verify,
                                   handoff, safe_relative, load_proposal)

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'project';self.root.mkdir()
        self.front=self.root/'frontend';self.front.mkdir()
        self.file=self.front/'index.js';self.file.write_text('const label = "red";\n',encoding='utf-8')
        init(self.root)
        self.plan={'schema_version':3,'task_id':'T-001',
            'summary':'Change button style from red to blue',
            'changes':[{'path':'frontend/index.js','action':'replace',
                'expected_sha256':hashlib.sha256(self.file.read_bytes()).hexdigest(),
                'old_text':'"red"','new_text':'"blue"'}]}
    def tearDown(self):self.temp.cleanup()

    def test_preview_has_diff_without_write(self):
        r=preview(self.root,self.plan)
        self.assertIn('"blue"',r['files'][0]['diff'])
        self.assertFalse(r['approved'])
        self.assertIn('"red"',self.file.read_text())
    def test_reject_apply_without_approval(self):
        with self.assertRaisesRegex(ValueError,'approve'):apply(self.root,self.plan)
        self.assertIn('"red"',self.file.read_text())
    def test_apply_review_restore_roundtrip(self):
        result=apply(self.root,self.plan,approved=True)
        self.assertIn('"blue"',self.file.read_text())
        self.assertTrue(review(self.root,result['change_id'])['all_files_match'])
        reverted=restore(self.root,result['change_id'],approved=True)
        self.assertEqual(reverted['status'],'restored')
        self.assertIn('"red"',self.file.read_text())
        with self.assertRaisesRegex(ValueError,'only applied'):restore(self.root,result['change_id'],approved=True)
    def test_create_and_restore(self):
        self.plan['changes'].append({'path':'frontend/generated.js','action':'create',
            'content':'export const READY = true;\n'})
        r=apply(self.root,self.plan,approved=True)
        self.assertTrue((self.front/'generated.js').is_file())
        restore(self.root,r['change_id'],approved=True)
        self.assertFalse((self.front/'generated.js').exists())
    def test_preflight_is_all_or_nothing(self):
        self.plan['changes'].append({'path':'frontend/missing.js','action':'replace',
            'expected_sha256':'0'*64,'old_text':'x','new_text':'y'})
        with self.assertRaises(ValueError):apply(self.root,self.plan,approved=True)
        self.assertIn('"red"',self.file.read_text())
    def test_stale_hash_prevents_overwrite(self):
        self.file.write_text('const label="green";\n')
        with self.assertRaisesRegex(ValueError,'stale'):apply(self.root,self.plan,approved=True)
    def test_restore_refuses_newer_user_edits(self):
        r=apply(self.root,self.plan,approved=True)
        self.file.write_text('const label="purple";\n')
        self.assertFalse(review(self.root,r['change_id'])['all_files_match'])
        with self.assertRaisesRegex(ValueError,'refusing'):restore(self.root,r['change_id'],approved=True)
        self.assertIn('"purple"',self.file.read_text())
    def test_restore_requires_explicit_approval(self):
        r=apply(self.root,self.plan,approved=True)
        with self.assertRaisesRegex(ValueError,'approve'):restore(self.root,r['change_id'])
    def test_reject_traversal(self):
        for path in ['../outside.js','frontend/../../out.js','/tmp/foo.js','frontend\\file.js',
                     '.ai/task_state.json','.git/config','.env','frontend/.env.test',
                     'skills/00_core/myfile.md','frontend/private.pem','frontend/x.sqlite']:
            with self.subTest(path=path),self.assertRaises(ValueError):
                safe_relative(self.root,path,allow_missing=True)
    def test_symlink_protection(self):
        target=Path(self.temp.name)/'outside';target.mkdir()
        try:(self.root/'escape').symlink_to(target,target_is_directory=True)
        except (NotImplementedError,OSError):self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError,'symlink'):safe_relative(self.root,'escape/w.txt',allow_missing=True)
    def test_ambiguous_old_text(self):
        self.file.write_text('"red"\n"red"\n')
        self.plan['changes'][0]['expected_sha256']=hashlib.sha256(self.file.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'exactly once'):preflight(self.root,self.plan)
    def test_binary_rejected(self):
        self.file.write_bytes(b'\x00binary')
        self.plan['changes'][0]['expected_sha256']=hashlib.sha256(self.file.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'binary'):preflight(self.root,self.plan)
    def test_max_changes(self):
        self.plan['changes']=[{'action':'create','path':f'frontend/{i}.js','content':'x'} for i in range(21)]
        with self.assertRaises(ValueError):preflight(self.root,self.plan)
    def test_dry_verify_no_pass_or_task_close(self):
        r=apply(self.root,self.plan,approved=True)
        with self.assertRaises(ValueError):verify(self.root,r['change_id'],close_task=True)
        self.assertFalse(verify(self.root,r['change_id'])['all_passed'])
    def test_verify_executes_and_closes_task(self):
        (self.root/'tests').mkdir()
        (self.root/'tests/test_ok.py').write_text('import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        (self.root/'.ai/checks.json').write_text(json.dumps({'checks':[{'name':'u','cwd':'.',
            'args':['python','-m','unittest','discover','-s','tests'],
            'timeout_seconds':20,'enabled':True}]}))
        r=apply(self.root,self.plan,approved=True)
        verified=verify(self.root,r['change_id'],execute=True,close_task=True)
        self.assertTrue(verified['all_passed'])
        self.assertEqual(status(self.root)['tasks'][0]['status'],'done')
        restored=restore(self.root,r['change_id'],approved=True)
        self.assertEqual(restored['status'],'restored')
        self.assertEqual(status(self.root)['tasks'][0]['status'],'blocked')
    def test_failure_wont_close_task(self):
        (self.root/'tests').mkdir()
        (self.root/'tests/test_fail.py').write_text('import unittest\nclass Test(unittest.TestCase):\n def test_fail(self): self.fail()\n')
        (self.root/'.ai/checks.json').write_text(json.dumps({'checks':[{'name':'u','cwd':'.',
            'args':['python','-m','unittest','discover','-s','tests'],'enabled':True}]}))
        r=apply(self.root,self.plan,approved=True)
        with self.assertRaisesRegex(ValueError,'did not all pass'):verify(self.root,r['change_id'],execute=True,close_task=True)
        self.assertFalse(status(self.root)['tasks'])
    def test_handoff_does_not_invoke_agent(self):
        h=handoff(self.root,'修改按钮颜色')
        self.assertEqual(h['schema_version'],3)
        self.assertTrue(h['selected_skills'])
        self.assertIn('Return a JSON proposal',h['agent_instructions'][1])
    def test_load_proposal_fails_schema(self):
        path=self.root/'proposal.json';path.write_text(json.dumps({'schema_version':2,'changes':[]}))
        with self.assertRaisesRegex(ValueError,'schema'):load_proposal(path)
    def test_proposal_duplicate_paths(self):
        p=self.root/'proposal.json';self.plan['changes']*=2
        p.write_text(json.dumps(self.plan))
        with self.assertRaisesRegex(ValueError,'duplicate'):load_proposal(p)

if __name__=='__main__':unittest.main()

class HighRiskGateTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.project=Path(self.t.name);(self.project/'backend').mkdir();init(self.project)
        self.target=self.project/'backend/auth.py';self.target.write_text('def check():\n return True\n')
        self.plan={'schema_version':3,'task_id':'SEC-1','summary':'Update user authentication logic',
                   'changes':[{'path':'backend/auth.py','action':'replace',
                               'expected_sha256':hashlib.sha256(self.target.read_bytes()).hexdigest(),
                               'old_text':'return True','new_text':'return False'}]}
    def tearDown(self):self.t.cleanup()
    def test_path_risk_detected_even_if_summary_is_style(self):
        self.plan['summary']='Change button style color only'
        p=preview(self.project,self.plan)
        self.assertEqual(p['risk_review']['execution_mode'],'strict')
        with self.assertRaisesRegex(ValueError,'high-risk-reviewed'):
            apply(self.project,self.plan,approved=True)
    def test_high_risk_needs_two_signals(self):
        with self.assertRaisesRegex(ValueError,'approve'):
            apply(self.project,self.plan,high_risk_reviewed=True)
        with self.assertRaisesRegex(ValueError,'high-risk-reviewed'):
            apply(self.project,self.plan,approved=True)
        result=apply(self.project,self.plan,approved=True,high_risk_reviewed=True)
        self.assertEqual(result['status'],'applied')
        self.assertEqual(self.target.read_text().splitlines()[-1],' return False')
