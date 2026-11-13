"""V3.1 agent bridge: bounded data-sharing, untrusted proposal validation, and review-first changes."""
from tests.fixture_optin import enable_test_checks
import hashlib
import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from orchestrator.agent import (AgentError,build_context,call_model,prepare,
    validate_endpoint,validate_proposal)
from orchestrator.cli import init
from orchestrator.git_review import review_git
from orchestrator.workflow import apply,preview,restore,verify
from tools.run_checks import run,save_report

REPO=Path(__file__).resolve().parents[1]


class AgentBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'project'
        shutil.copytree(REPO/'examples/workflow-demo',self.root)
        init(self.root)
        enable_test_checks(self.root)
        self.file=self.root/'src/formatter.py'
        self.task='Fix greeting punctuation in example code'
        self.task_id='AGENT-1'
    def tearDown(self):self.tmp.cleanup()
    def context(self,**kw):
        return build_context(self.root,self.task,self.task_id,['src/formatter.py'],**kw)
    def response(self,path='src/formatter.py',hash_override=None):
        return json.dumps({'schema_version':3,'task_id':self.task_id,'summary':self.task,
          'changes':[{'path':path,'action':'replace',
                      'expected_sha256':hash_override or hashlib.sha256(self.file.read_bytes()).hexdigest(),
                      'old_text':'return f"Hello {name}"','new_text':'return f"Hello {name}!"'}]})
    def test_context_is_explicit_and_is_read_only(self):
        c=self.context()
        self.assertEqual(c['sources'][0]['sha256'],hashlib.sha256(self.file.read_bytes()).hexdigest())
        self.assertEqual(c['sources'][0]['path'],'src/formatter.py')
        self.assertFalse((self.root/'.ai/proposals').exists())
    def test_empty_or_duplicate_source_rejected(self):
        with self.assertRaises(AgentError):build_context(self.root,self.task,self.task_id,[])
        with self.assertRaises(AgentError):build_context(self.root,self.task,self.task_id,['src/formatter.py']*2)
    def test_block_secret_in_source(self):
        self.file.write_text('key = "sk-proj-abc123456789ABCDEFGH"\n')
        with self.assertRaisesRegex(AgentError,'credential'):self.context()
    def test_symlink_cannot_be_sent(self):
        outside=Path(self.tmp.name)/'outside.txt';outside.write_text('not allowed')
        try:(self.root/'src/alias.py').symlink_to(outside)
        except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError,'symlink'):
            build_context(self.root,self.task,self.task_id,['src/alias.py'])
    def test_source_size_limit(self):
        self.file.write_bytes(b'x'*(33*1024))
        with self.assertRaisesRegex(AgentError,'32 KiB'):self.context()
    def test_live_call_must_be_explicitly_authorized(self):
        with self.assertRaisesRegex(AgentError,'send-to-model'):
            prepare(self.root,self.task,self.task_id,['src/formatter.py'],
                    endpoint='https://example.org/v1/chat/completions',model='test')
        self.assertFalse((self.root/'.ai/proposals').exists())
    def test_endpoints_enforce_https(self):
        for url in ('http://example.org/v1/chat/completions','file:///etc/passwd',
                    'https://user:pass@example.org/v1','https://example.org/?token=abc'):
            with self.subTest(url=url),self.assertRaises(AgentError):validate_endpoint(url)
        validate_endpoint('http://127.0.0.1:12345/v1/chat/completions',True)
    def test_model_may_not_modify_unselected_file(self):
        (self.root/'src/other.py').write_bytes(self.file.read_bytes())
        with self.assertRaisesRegex(AgentError,'not explicitly sent'):
            validate_proposal(self.context(),self.response('src/other.py'),self.root)
    def test_model_cannot_forge_source_hash(self):
        with self.assertRaisesRegex(AgentError,'stale or fabricated'):
            validate_proposal(self.context(),self.response(hash_override='0'*64),self.root)
    def test_reject_unknown_proposal_fields(self):
        p=json.loads(self.response());p['run_command']='rm -rf .'
        with self.assertRaisesRegex(AgentError,'fields'):
            validate_proposal(self.context(),json.dumps(p),self.root)
    def test_create_requires_explicit_prefix(self):
        p={'schema_version':3,'task_id':self.task_id,'summary':self.task,
           'changes':[{'action':'create','path':'src/new.py','content':'print("hello")\n'}]}
        with self.assertRaisesRegex(AgentError,'explicitly approved'):
            validate_proposal(self.context(),json.dumps(p),self.root)
        accepted=validate_proposal(self.context(create_prefixes=['src']),json.dumps(p),self.root)
        self.assertEqual(accepted['changes'][0]['path'],'src/new.py')
    def test_offline_full_review_test_restore(self):
        response=Path(self.tmp.name)/'model.txt';response.write_text(self.response())
        info=prepare(self.root,self.task,self.task_id,['src/formatter.py'],response_file=response)
        self.assertEqual(info['provider'],'offline-response-file')
        self.assertEqual(info['files_changed'],1)
        self.assertIn('return f"Hello {name}"',self.file.read_text())
        path=self.root/info['proposal_path']
        proposed=json.loads(path.read_text())
        self.assertFalse(preview(self.root,proposed)['approved'])
        with self.assertRaisesRegex(ValueError,'approve'):apply(self.root,proposed)
        result=apply(self.root,proposed,approved=True)
        verified=verify(self.root,result['change_id'],execute=True,close_task=True)
        self.assertTrue(verified['all_passed'])
        self.assertTrue((self.root/verified['report']).is_file())
        restore(self.root,result['change_id'],approved=True)
        self.assertIn('return f"Hello {name}"',self.file.read_text())
    def test_failed_report_powers_next_repair_context(self):
        report=run(self.root,execute=True)
        self.assertTrue(any(c['status']=='failed' for c in report['checks']))
        report_path=Path(save_report(self.root,report))
        context=self.context(report_name=report_path.name)
        self.assertEqual(context['failed_test']['report_name'],report_path.name)
        self.assertTrue(context['failed_test']['failures'])
        with self.assertRaisesRegex(AgentError,'basename'):
            self.context(report_name='../'+report_path.name)
    def test_refuse_unexecuted_report_as_diagnosis(self):
        report=run(self.root,execute=False)
        path=Path(save_report(self.root,report))
        with self.assertRaisesRegex(AgentError,'actual reports'):
            self.context(report_name=path.name)
    def test_git_review_is_read_only(self):
        try:
            subprocess.run(['git','--version'],check=True,capture_output=True)
        except (OSError,subprocess.CalledProcessError):self.skipTest('git unavailable')
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        result=apply(self.root,json.loads(self.response()),approved=True)
        data=review_git(self.root,result['change_id'])
        self.assertIn('src/formatter.py',data['paths'])
        self.assertEqual(data['change_status'],'applied')
        self.assertIn('No branch, stage, commit',data['note'])


class LocalProtocolTests(unittest.TestCase):

    def test_model_redirect_rejected_without_forwarding_source(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(307)
                self.send_header('Location','https://unapproved.example/v1/chat/completions')
                self.end_headers()
            def log_message(self,*a):pass
        try:server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        except OSError:self.skipTest('local HTTP server blocked')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            c={'sources':[],'selected':{},'task':'test','task_id':'T-1'}
            with self.assertRaisesRegex(AgentError,'redirect'):
                call_model(c,endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                    model='stub',key='test-key',allow_local_http=True)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)

    def test_live_openai_compatible_protocol_with_opt_in(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'src').mkdir();(root/'src/app.py').write_text('answer = 1\n')
            init(root)
            response={'schema_version':3,'task_id':'NET-1','summary':'Update the example answer',
                      'changes':[{'path':'src/app.py','action':'replace',
                                  'expected_sha256':hashlib.sha256((root/'src/app.py').read_bytes()).hexdigest(),
                                  'old_text':'answer = 1','new_text':'answer = 2'}]}
            observations=[]
            class Handler(BaseHTTPRequestHandler):
                def do_POST(self):
                    n=int(self.headers['Content-Length'])
                    req=json.loads(self.rfile.read(n))
                    observations.append({'path':self.path,'auth':self.headers.get('Authorization'),
                                         'messages':req['messages']})
                    body=json.dumps({'choices':[{'message':{'content':json.dumps(response)}}]}).encode()
                    self.send_response(200);self.send_header('Content-Type','application/json')
                    self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
                def log_message(self,*a):pass
            try:server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            except OSError:self.skipTest('local HTTP server blocked')
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                import os
                os.environ['BRIDGE_TEST_KEY']='test-key-only'
                info=prepare(root,'Update the example answer','NET-1',['src/app.py'],
                        endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                        model='local-stub',api_key_env='BRIDGE_TEST_KEY',
                        allow_local_http=True,send_to_model=True)
                self.assertEqual(len(observations),1)
                self.assertEqual(observations[0]['auth'],'Bearer test-key-only')
                self.assertTrue(info['proposal_path'].startswith('.ai/proposals/'))
                self.assertEqual((root/'src/app.py').read_text(),'answer = 1\n')
                self.assertNotIn('test-key-only',(root/info['proposal_path']).read_text())
            finally:
                server.shutdown();server.server_close();thread.join(timeout=3)
                os.environ.pop('BRIDGE_TEST_KEY',None)

if __name__=='__main__':unittest.main()
