"""V3.2 cap, approval boundaries, recovery and executed repair evidence."""
from tests.fixture_optin import enable_test_checks
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from orchestrator.cli import init, status
from orchestrator import loop

ROOT=Path(__file__).resolve().parents[1]

class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'demo'
        shutil.copytree(ROOT/'examples/workflow-demo',self.root,
                        ignore=shutil.ignore_patterns('__pycache__'))
        init(self.root)
        enable_test_checks(self.root)
        self.source=self.root/'src/formatter.py'
        self.task='Fix greeting punctuation in the example module'
        self.task_id='LOOP-1'
    def tearDown(self):self.tmp.cleanup()

    def response(self,old='return f"Hello {name}"',new='return f"Hello {name}!"'):
        p={'schema_version':3,'task_id':self.task_id,'summary':self.task,'changes':[
           {'action':'replace','path':'src/formatter.py',
             'expected_sha256':hashlib.sha256(self.source.read_bytes()).hexdigest(),
             'old_text':old,'new_text':new}]}
        file=Path(self.tmp.name)/'response.json'
        file.write_text(json.dumps(p),encoding='utf-8')
        return file

    def start(self,max_rounds=3,new='return f"Hello {name}!"'):
        out=loop.start(self.root,self.task,self.task_id,['src/formatter.py'],
             max_rounds=max_rounds,response_file=self.response(new=new))
        return out['run_id']

    def test_start_is_review_only_and_persistent(self):
        original=self.source.read_bytes();rid=self.start()
        self.assertEqual(self.source.read_bytes(),original)
        saved=loop.inspect(self.root,rid)
        self.assertEqual(saved['stage'],'awaiting_approval')
        self.assertEqual(saved['attempts'][0]['round'],1)
        self.assertTrue((self.root/saved['attempts'][0]['proposal_path']).exists())
        self.assertFalse((self.root/'.ai/loops'/rid/'state.json').read_text().find('sk-')>=0)

    def test_requires_approval_and_trusted_code_flag(self):
        rid=self.start()
        with self.assertRaisesRegex(ValueError,'approve'):loop.approve(self.root,rid)
        result=loop.approve(self.root,rid,approved=True)
        self.assertEqual(result['stage'],'awaiting_test')
        with self.assertRaisesRegex(ValueError,'trust-project-code'):loop.test(self.root,rid)
        self.assertEqual(loop.inspect(self.root,rid)['stage'],'awaiting_test')

    def test_one_round_success_tracks_real_evidence(self):
        rid=self.start(max_rounds=1)
        loop.approve(self.root,rid,approved=True)
        result=loop.test(self.root,rid,trust_project_code=True)
        self.assertTrue(result['all_passed'])
        self.assertEqual(result['stage'],'completed')
        report=json.loads((self.root/result['report']).read_text())
        self.assertTrue(report['actually_executed'])
        self.assertEqual(status(self.root)['tasks'][0]['status'],'done')
        with self.assertRaisesRegex(ValueError,'repair requires'):
            loop.repair(self.root,rid,response_file=self.response())

    def test_two_round_repair_and_reverse_rollback(self):
        rid=self.start(max_rounds=2,new='return f"Hello {name}?"')
        loop.approve(self.root,rid,approved=True)
        first=loop.test(self.root,rid,trust_project_code=True)
        self.assertFalse(first['all_passed'])
        self.assertEqual(first['stage'],'awaiting_repair')
        path=self.response(old='return f"Hello {name}?"',new='return f"Hello {name}!"')
        nxt=loop.repair(self.root,rid,response_file=path)
        self.assertEqual(nxt['round'],2)
        loop.approve(self.root,rid,approved=True)
        second=loop.test(self.root,rid,trust_project_code=True)
        self.assertEqual(second['stage'],'completed')
        self.assertEqual(len(loop.inspect(self.root,rid)['attempts']),2)
        restored=loop.abort(self.root,rid,restore=True,approved=True)
        self.assertEqual(len(restored['restored_changes']),2)
        self.assertEqual(self.source.read_text().splitlines()[-1], '    return f"Hello {name}"')
        self.assertEqual(status(self.root)['tasks'][0]['status'],'blocked')

    def test_max_rounds_stop(self):
        rid=self.start(max_rounds=1,new='return f"Hello {name}?"')
        loop.approve(self.root,rid,approved=True)
        result=loop.test(self.root,rid,trust_project_code=True)
        self.assertEqual(result['stage'],'exhausted')
        with self.assertRaisesRegex(ValueError,'repair requires'):
            loop.repair(self.root,rid,response_file=self.response())

    def test_repair_report_tampering_rejected(self):
        rid=self.start(new='return f"Hello {name}?"')
        loop.approve(self.root,rid,approved=True)
        result=loop.test(self.root,rid,trust_project_code=True)
        (self.root/result['report']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'evidence changed'):
            loop.repair(self.root,rid,response_file=self.response())

    def test_repair_source_drift_rejected(self):
        rid=self.start(new='return f"Hello {name}?"')
        loop.approve(self.root,rid,approved=True)
        loop.test(self.root,rid,trust_project_code=True)
        self.source.write_text(self.source.read_text()+'\n# changed after failing test\n')
        with self.assertRaisesRegex(ValueError,'source drift'):
            loop.repair(self.root,rid,response_file=self.response())

    def test_proposal_tampering_rejected(self):
        rid=self.start()
        proposal=self.root/loop.inspect(self.root,rid)['attempts'][0]['proposal_path']
        proposal.write_text(proposal.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'proposal changed'):
            loop.approve(self.root,rid,approved=True)
        self.assertIn('return f"Hello {name}"',self.source.read_text())

    def test_abort_requires_approval_to_restore(self):
        rid=self.start()
        loop.approve(self.root,rid,approved=True)
        with self.assertRaisesRegex(ValueError,'--approve'):
            loop.abort(self.root,rid,restore=True)
        self.assertIn('return f"Hello {name}!"',self.source.read_text())
        out=loop.abort(self.root,rid,restore=True,approved=True)
        self.assertEqual(out['stage'],'aborted')
        self.assertIn('return f"Hello {name}"',self.source.read_text())

    def test_abort_refuses_newer_edits(self):
        rid=self.start()
        loop.approve(self.root,rid,approved=True)
        self.source.write_text(self.source.read_text()+'\n# personal edit\n')
        with self.assertRaisesRegex(ValueError,'refusing to overwrite'):
            loop.abort(self.root,rid,restore=True,approved=True)
        self.assertEqual(loop.inspect(self.root,rid)['stage'],'rollback_blocked')

    def test_reconcile_after_crash_between_apply_and_state_write(self):
        rid=self.start()
        state=loop._load(self.root,rid)
        attempt=state['attempts'][-1]
        attempt['operation_id']='op-test-crash-recovery'
        state['stage']='applying';loop._write(self.root,state)
        from orchestrator.workflow import apply,load_proposal
        prop=load_proposal(self.root/attempt['proposal_path'])
        changed=apply(self.root,prop,approved=True,operation_id=attempt['operation_id'])
        inspected=loop.inspect(self.root,rid)
        self.assertEqual(inspected['stage'],'awaiting_test')
        self.assertEqual(inspected['attempts'][-1]['change_id'],changed['change_id'])

    def test_reconcile_no_manifest_returns_to_approval(self):
        rid=self.start()
        state=loop._load(self.root,rid)
        state['stage']='applying'
        state['attempts'][-1]['operation_id']='op-lost'
        loop._write(self.root,state)
        self.assertEqual(loop.inspect(self.root,rid)['stage'],'awaiting_approval')

    def test_model_failure_does_not_leave_started_run(self):
        before=set((self.root/'.ai/loops').iterdir()) if (self.root/'.ai/loops').exists() else set()
        with self.assertRaisesRegex(ValueError,'network model invocation'):
            loop.start(self.root,self.task,self.task_id,['src/formatter.py'])
        self.assertEqual(set((self.root/'.ai/loops').iterdir()),before)

    def test_round_boundaries(self):
        with self.assertRaisesRegex(ValueError,'max_rounds'):
            self.start(max_rounds=0)
        with self.assertRaisesRegex(ValueError,'max_rounds'):
            self.start(max_rounds=6)

    def test_disabled_checks_not_called_repair_failure(self):
        rid=self.start()
        loop.approve(self.root,rid,approved=True)
        config=self.root/'.ai/checks.json'
        data=json.loads(config.read_text())
        data['checks'][0]['enabled']=False
        config.write_text(json.dumps(data))
        result=loop.test(self.root,rid,trust_project_code=True)
        self.assertEqual(result['stage'],'unverified')
        with self.assertRaisesRegex(ValueError,'repair requires'):
            loop.repair(self.root,rid,response_file=self.response())

if __name__=='__main__':unittest.main()
