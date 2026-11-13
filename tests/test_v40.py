"""V4.0 integrated console / real LSP / safety / release evidence tests."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from orchestrator.console import dispatch, parser_factory, main
from tools.doctor import diagnose
from tools.release_gate import verify
from tools.lsp_client import LSPClient

ROOT=Path(__file__).resolve().parents[1]
MOCK=ROOT/'tests/mock_lsp_server.py'


def cli(*args):
    return subprocess.run([sys.executable,str(ROOT/'fullstack.py'),*map(str,args)],
                          cwd=ROOT,capture_output=True,text=True,timeout=30,check=False)


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p=Path(self.temp.name)

    def test_console_help_and_version(self):
        self.assertEqual(cli('--help').returncode,0)
        self.assertRegex(cli('--version').stdout,r'AI Fullstack Dev Skills [45]\.[0-9]+')

    def test_doctor_read_only_and_missing_optional(self):
        a=diagnose(self.p)
        self.assertIn(a['overall'],('ready','needs-attention'))
        self.assertFalse((self.p/'.ai').exists())
        self.assertTrue(any(c['name']=='python' for c in a['checks']))
        self.assertEqual(cli('doctor','--project',self.p).returncode,0)

    def test_route_and_index_read_only(self):
        (self.p/'main.py').write_text('def cloud_filter(item):\n    return bool(item)\n')
        routed=cli('route','--task','Modify a CSS button')
        self.assertEqual(routed.returncode,0)
        self.assertIn('selected',json.loads(routed.stdout))
        got=cli('index','--project',self.p,'--query','cloud_filter')
        self.assertEqual(got.returncode,0,got.stderr)
        self.assertTrue(json.loads(got.stdout)['search']['matches'])
        self.assertFalse((self.p/'.ai').exists())

    def test_test_selection_conservative(self):
        (self.p/'core.py').write_text('def calculate(x):\n    return x + 1\n')
        (self.p/'test_core.py').write_text('from core import calculate\n')
        got=cli('select-tests','--project',self.p,'--changed','core.py')
        self.assertEqual(got.returncode,0,got.stderr)
        self.assertIn('test_core.py',[t['path'] for t in json.loads(got.stdout)['tests']])

    def test_lsp_requires_explicit_authorization(self):
        (self.p/'main.py').write_text('def Widget(): pass\n')
        r=cli('lsp','--project',self.p,'--server',sys.executable,'--server-arg',str(MOCK),'--query','Widget')
        self.assertEqual(r.returncode,2)
        self.assertIn('requires --allow-start',r.stderr)

    def test_opt_in_mock_lsp(self):
        (self.p/'src').mkdir()
        (self.p/'src/widget.py').write_text('def unused():\n    pass\ndef Widget():\n    pass\n')
        r=cli('lsp','--project',self.p,'--server',sys.executable,'--server-arg',str(MOCK),
              '--query','Widget','--allow-start')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['matches'][0]['path'],'src/widget.py')

    def test_bundled_gate_requires_execute(self):
        report_dir=ROOT/'benchmarks/reports'
        existed=report_dir.exists()
        original=set(report_dir.iterdir()) if existed else set()
        planned=verify(profile='smoke',execute=False)
        self.assertFalse(planned['actually_executed'])
        self.assertGreaterEqual(planned['summary']['planned'],4)
        self.assertEqual(planned['summary']['passed'],0)
        self.assertEqual(report_dir.exists(),existed)
        if existed:
            self.assertEqual(set(report_dir.iterdir()),original)

    def test_gate_output_path_must_be_reports(self):
        with self.assertRaisesRegex(ValueError,'report output'):
            verify(profile='smoke',execute=True,output=self.p/'arbitrary.json')

    def test_unsafe_symlink_lsp_cpp_rejected(self):
        (self.p/'secret.cpp').write_text('int hidden() { return 1; }\n')
        (self.p/'alias.cpp').symlink_to(self.p/'secret.cpp')
        with LSPClient(self.p,[sys.executable,str(MOCK)]) as client:
            self.assertNotIn('alias.cpp',client.allowed)

    def test_c_family_file_allowed_for_local_lsp(self):
        (self.p/'math.cpp').write_text('int add(int x, int y) { return x + y; }\n')
        with LSPClient(self.p,[sys.executable,str(MOCK)]) as client:
            self.assertIn('math.cpp',client.allowed)

    def test_project_complete_check_evidence(self):
        (self.p/'tests').mkdir()
        (self.p/'tests/test_ok.py').write_text('import unittest\nclass Check(unittest.TestCase):\n def test_ok(self): self.assertEqual(1+1,2)\n')
        self.assertEqual(cli('project','init','--project',self.p).returncode,0)
        self.assertEqual(cli('project','add-task','--project',self.p,'--id','DEV1','--title','Verify fixture').returncode,0)
        cfg=self.p/'.ai/checks.json'
        data=json.loads(cfg.read_text())
        data['checks'][0]['enabled']=True
        cfg.write_text(json.dumps(data))
        preview=cli('check','--project',self.p)
        self.assertEqual(preview.returncode,0)
        self.assertEqual(json.loads(preview.stdout)['summary']['planned_only'],1)
        self.assertFalse((self.p/'.ai/reports').exists())
        checked=cli('check','--project',self.p,'--execute','--save-report')
        self.assertEqual(checked.returncode,0,checked.stderr)
        record=json.loads(checked.stdout)
        self.assertEqual(record['summary']['passed'],1)
        report_name=Path(record['saved_report']).name
        done=cli('project','set-task','--project',self.p,'--id','DEV1','--status','done','--report',report_name)
        self.assertEqual(done.returncode,0,done.stderr)
        status=json.loads(cli('project','status','--project',self.p).stdout)
        self.assertEqual(status['tasks'][0]['status'],'done')
        self.assertEqual(status['tasks'][0]['evidence'][0]['integrity'],'valid')

    def test_cannot_mark_done_unverified(self):
        cli('project','init','--project',self.p)
        cli('project','add-task','--project',self.p,'--id','T','--title','Work')
        result=cli('project','set-task','--project',self.p,'--id','T','--status','done')
        self.assertEqual(result.returncode,2)


@unittest.skipUnless(shutil.which('clangd'),'requires an installed trusted clangd')
class LiveClangdTests(unittest.TestCase):
    def test_real_language_server_definition(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/'main.cpp').write_text('int add(int x,int y){return x+y;}\nint main(){return add(2,3);}\n')
            with LSPClient(p,[shutil.which('clangd'),'--background-index=false'],timeout=15) as client:
                got=client.definition('main.cpp',1,19)
            self.assertEqual(got['matches'][0]['path'],'main.cpp')
            self.assertEqual(got['matches'][0]['line'],1)


if __name__=='__main__':unittest.main()
