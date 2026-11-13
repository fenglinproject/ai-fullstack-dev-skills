"""V3.5 local retrieval, failure advice, benchmark and opt-in agent integration."""
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator import agent, loop
from orchestrator.cli import init
from tools import context_retrieval as cr
from tools.failure_triage import classify, summarize, repair_strategy
from tools.benchmark_v35 import ROOT, FIXTURES, evaluate, compare


class ContextRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/'src').mkdir()
        (self.root/'tests').mkdir()
        (self.root/'src/greeting.py').write_text('def greet(name):\n    return "hello " + name\n',encoding='utf-8')
        (self.root/'tests/test_greeting.py').write_text('from src.greeting import greet\n\ndef test_greet():\n    assert greet("x") == "hello x"\n',encoding='utf-8')
    def tearDown(self):self.temp.cleanup()
    def test_project_source_results(self):
        out=cr.retrieve(self.root,'greet function')
        self.assertEqual(out['results'][0]['path'],'src/greeting.py')
        self.assertEqual(out['results'][0]['line_start'],1)
        self.assertIn('def greet',out['results'][0]['snippet'])
        self.assertEqual(out['results'][0]['sha256'],hashlib.sha256((self.root/'src/greeting.py').read_bytes()).hexdigest())
    def test_example_proposal_not_treated_as_source(self):
        (self.root/'proposal.json').write_text('{"instructions":"greet function"}')
        self.assertNotIn('proposal.json',[x['path'] for x in cr.retrieve(self.root,'greet function')['results']])
    def test_ignored_private_files(self):
        (self.root/'.ai').mkdir();(self.root/'.ai/private.py').write_text('def private_password():pass')
        (self.root/'.env').write_text('SECRET_API_KEY=123')
        self.assertFalse(cr.retrieve(self.root,'private password')['results'])
        self.assertFalse(cr.retrieve(self.root,'SECRET_API_KEY')['results'])
    def test_no_symlink_followed(self):
        outside=self.root.parent/'v35_sensitive_outside.py'
        outside.write_text('def secretfunc():pass')
        (self.root/'src/link.py').symlink_to(outside)
        try:self.assertEqual(cr.retrieve(self.root,'secretfunc')['results'],[])
        finally:outside.unlink(missing_ok=True)
    def test_skip_sensitive_content(self):
        (self.root/'src/key.py').write_text('def auth_token():\n    api_key="TOP_SECRET_VALUE_123456789"\n')
        r=cr.retrieve(self.root,'auth_token')
        self.assertNotIn('src/key.py',[v['path'] for v in r['results']])
        self.assertGreaterEqual(r['skipped_sensitive_files'],1)
    def test_no_network_and_no_modification(self):
        before=(self.root/'src/greeting.py').read_bytes()
        with patch('urllib.request.urlopen',side_effect=AssertionError('network must not be used')):
            cr.retrieve(self.root,'greet')
        self.assertEqual(before,(self.root/'src/greeting.py').read_bytes())
    def test_query_limits(self):
        for query in ('','a', 'x'*1001, 'sk-123456789abcdefghi'):
            with self.subTest(query=query),self.assertRaises(ValueError):cr.retrieve(self.root,query)
        for limit in (0,13,True):
            with self.subTest(limit=limit),self.assertRaises(ValueError):cr.retrieve(self.root,'greet',limit)
    def test_file_cap_rejected(self):
        with patch.object(cr,'MAX_FILES',1):
            with self.assertRaisesRegex(ValueError,'limits exceeded'):cr.retrieve(self.root,'greet')
    def test_case_stable(self):
        a=cr.retrieve(self.root,'GREET function',include_snippets=False)
        b=cr.retrieve(self.root,'GREET function',include_snippets=False)
        self.assertEqual(a,b)
    def test_result_snippet_opt_out(self):
        self.assertNotIn('snippet',cr.retrieve(self.root,'greet',include_snippets=False)['results'][0])


class FailureTriageTests(unittest.TestCase):
    def test_categories(self):
        examples={'ModuleNotFoundError: No module named app':'dependency_missing',
            'SyntaxError: invalid syntax':'syntax_error',
            'AssertionError: mismatch':'assertion_failure',
            'TypeError: missing argument':'type_error',
            'ConnectionRefusedError':'connection_failure',
            'PermissionError: denied':'permission_failure',
            'TimeoutError':'timeout', 'random failure':'unknown'}
        for message,expected in examples.items():
            with self.subTest(message=message):self.assertEqual(classify(message)['category'],expected)
    def test_status_fallback(self):
        self.assertEqual(classify('',status='timeout')['category'],'timeout')
    def test_advisory_no_commands(self):
        report={'checks':[{'name':'api','status':'failed','stderr_tail':'AssertionError: wrong result'},
                          {'name':'okay','status':'passed'}]}
        got=summarize(report)
        self.assertEqual(got['total_failed'],1)
        self.assertEqual(got['checks'][0]['category'],'assertion_failure')
        self.assertNotIn('stderr_tail',got['checks'][0])
    def test_nontest_exception(self):
        with self.assertRaises(ValueError):classify(None)
    def test_repeated_category_escalation(self):
        advice=repair_strategy(['assertion_failure'],['assertion_failure','syntax_error'])
        self.assertTrue(advice['escalate_review'])
        self.assertEqual(advice['repeated_categories'],['assertion_failure'])
        self.assertFalse(repair_strategy(['syntax_error'],['assertion_failure'])['escalate_review'])
    def test_invalid_categories_refused(self):
        with self.assertRaises(ValueError):repair_strategy(['malicious_shell_action'])


class BenchmarkTests(unittest.TestCase):
    def test_curated_cross_project(self):
        report=evaluate()
        self.assertGreaterEqual(report['retrieval']['recall_at_k'],0.8)
        self.assertGreaterEqual(report['triage']['accuracy'],0.8)
        self.assertEqual(len(report['retrieval']['per_project']),2)
        self.assertIn('fixture_sha256',report)
    def test_deterministic(self):
        self.assertEqual(evaluate(),evaluate())
    def test_detect_different_fixtures(self):
        current=evaluate();baseline=dict(current,fixture_sha256='0'*64)
        self.assertFalse(compare(current,baseline)['comparable_fixtures'])
    def test_limit_and_path_traversal(self):
        with self.assertRaises(ValueError):evaluate(top_k=0)
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'bad.json'
            file.write_text(json.dumps({'schema_version':1,'retrieval_cases':[{'id':'hack',
                'project':'../../outside','task':'x','expected_file':'a'}],'failure_cases':[]}))
            with self.assertRaises(ValueError):evaluate(fixtures=file)


class AgentContextIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        (self.p/'src').mkdir()
        (self.p/'src/greet.py').write_text('def greet(name):\n    return name\n')
        init(self.p)
    def tearDown(self):self.tmp.cleanup()
    def test_context_can_auto_select(self):
        out=agent.prepare(self.p,'Change the greet function','T-1',[],auto_context=True,context_only=True)
        self.assertEqual(out['included_files'][0]['path'],'src/greet.py')
        self.assertFalse((self.p/'.ai/proposals').exists())
        self.assertIn('context_retrieval',out)
    def test_live_auto_selection_always_blocked(self):
        with patch('orchestrator.agent.call_model',side_effect=AssertionError('must not call model')):
            with self.assertRaisesRegex(agent.AgentError,'cannot be sent'):
                agent.prepare(self.p,'Change the greet function','T-2',[],
                              auto_context=True,send_to_model=True,endpoint='https://example.com/v1/chat',model='mock')
    def test_failed_report_triage_available_to_context(self):
        folder=self.p/'.ai/reports';folder.mkdir()
        filename='checks-'+'a'*32+'.json'
        report={'schema_version':2,'project':str(self.p.resolve()),'actually_executed':True,
                'checks':[{'name':'unit','status':'failed','stderr_tail':'AssertionError: mismatch'}]}
        (folder/filename).write_text(json.dumps(report))
        context=agent.build_context(self.p,'Fix failed greet test','T-3',['src/greet.py'],report_name=filename)
        self.assertEqual(context['failed_test']['failures'][0]['triage']['category'],'assertion_failure')
        new_context=agent.build_context(self.p,'Fix failed greet test','T-3',['src/greet.py'],
                                        report_name=filename,prior_failure_categories=['assertion_failure'])
        self.assertTrue(new_context['failed_test']['repair_strategy']['escalate_review'])
    def test_loop_offline_auto_selects_and_stores(self):
        # Prepare a deterministic replay proposal consistent with the local source snapshot.
        raw=(self.p/'src/greet.py').read_bytes()
        response={'schema_version':3,'task_id':'T-LOOP','summary':'Update greeting return expression',
                  'changes':[{'path':'src/greet.py','action':'replace','expected_sha256':hashlib.sha256(raw).hexdigest(),
                              'old_text':'return name','new_text':'return "hello " + name'}]}
        payload=self.p/'reply.json';payload.write_text(json.dumps(response))
        out=loop.start(self.p,'Change greet function to add hello','T-LOOP',[],
                       response_file=payload,auto_context=True,max_rounds=2)
        run_folder=self.p/'.ai/loops'/out['run_id']
        state=json.loads((run_folder/'state.json').read_text())
        self.assertIn('src/greet.py',state['include'])
        self.assertEqual(state['stage'],'awaiting_approval')
        self.assertEqual((self.p/'src/greet.py').read_bytes(),raw)
    def test_loop_auto_live_guard_before_creation(self):
        with patch('orchestrator.agent.call_model',side_effect=AssertionError('must not call model')):
            with self.assertRaisesRegex(ValueError,'preview and explicitly approve'):
                loop.start(self.p,'Change greet function to add hello','T-LIVE',[],
                           auto_context=True,send_to_model=True)
        self.assertEqual(list((self.p/'.ai/loops').glob('*/state.json')),[])


if __name__=='__main__':unittest.main()
