"""Subprocess CLI contract for V3.2 state transitions and approvals."""
from tests.fixture_optin import enable_test_checks
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'orchestrator/loop.py'

class LoopCLITests(unittest.TestCase):
    def test_two_round_cli_offline(self):
        from orchestrator.cli import init
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'project'
            shutil.copytree(ROOT/'examples/workflow-demo',root,
                            ignore=shutil.ignore_patterns('__pycache__'))
            init(root)
            enable_test_checks(root)
            original=(root/'src/formatter.py').read_bytes()
            def invoke(*argv,success=True):
                r=subprocess.run([sys.executable,str(CLI),*argv,'--project',str(root)],
                                 capture_output=True,text=True,cwd=ROOT,timeout=25)
                if success:
                    self.assertEqual(r.returncode,0,r.stderr)
                    return json.loads(r.stdout)
                self.assertNotEqual(r.returncode,0)
                return r.stderr
            def response(old,new,file):
                path=Path(tmp)/file
                doc={'schema_version':3,'task_id':'E2E-1','summary':'Fix greeting punctuation in the example module',
                     'changes':[{'action':'replace','path':'src/formatter.py',
                        'expected_sha256':hashlib.sha256((root/'src/formatter.py').read_bytes()).hexdigest(),
                        'old_text':old,'new_text':new}]}
                path.write_text(json.dumps(doc))
                return path
            p1=response('return f"Hello {name}"','return f"Hello {name}?"','first.json')
            session=invoke('start','--task','Fix greeting punctuation in the example module',
                '--task-id','E2E-1','--include','src/formatter.py','--max-rounds','2','--response-file',str(p1))
            rid=session['run_id']
            self.assertEqual((root/'src/formatter.py').read_bytes(),original)
            self.assertIn('approve',invoke('approve','--run-id',rid,success=False))
            invoke('approve','--run-id',rid,'--approve')
            self.assertIn('trust-project-code',invoke('test','--run-id',rid,success=False))
            first=invoke('test','--run-id',rid,'--trust-project-code')
            self.assertEqual(first['stage'],'awaiting_repair')
            p2=response('return f"Hello {name}?"','return f"Hello {name}!"','second.json')
            invoke('repair','--run-id',rid,'--response-file',str(p2))
            self.assertEqual(invoke('resume','--run-id',rid)['stage'],'awaiting_approval')
            invoke('approve','--run-id',rid,'--approve')
            end=invoke('test','--run-id',rid,'--trust-project-code')
            self.assertEqual(end['stage'],'completed')
            final=invoke('abort','--run-id',rid,'--restore','--approve')
            self.assertEqual(len(final['restored_changes']),2)
            self.assertEqual((root/'src/formatter.py').read_bytes(),original)

if __name__=='__main__':unittest.main()
