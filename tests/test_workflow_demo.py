"""End-to-end test of shipped proposal, real unittest, evidence and restoration."""
from tests.fixture_optin import enable_test_checks
import shutil
import tempfile
import unittest
from pathlib import Path

from orchestrator.cli import init, status
from orchestrator.workflow import load_proposal, preview, apply, verify, restore

ROOT=Path(__file__).resolve().parents[1]

class ShippedDemoTests(unittest.TestCase):
    def test_full_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'demo'
            shutil.copytree(ROOT/'examples'/'workflow-demo',dest,
                            ignore=shutil.ignore_patterns('__pycache__'))
            init(dest)
            enable_test_checks(dest)
            proposal=load_proposal(dest/'proposal.json')
            self.assertTrue(preview(dest,proposal)['files'][0]['diff'])
            changed=apply(dest,proposal,approved=True)
            report=verify(dest,changed['change_id'],execute=True,close_task=True)
            self.assertTrue(report['all_passed'])
            self.assertEqual(status(dest)['tasks'][0]['status'],'done')
            restore(dest,changed['change_id'],approved=True)
            self.assertEqual(status(dest)['tasks'][0]['status'],'blocked')
            self.assertIn('return f"Hello {name}"',(dest/'src/formatter.py').read_text())

if __name__=='__main__':unittest.main()
