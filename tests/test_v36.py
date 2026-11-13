"""V3.6: AST, validated failure evidence, context ordering and fixture evaluation."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import ast_symbols, evidence_context, repair_context
from tools.benchmark_v36 import evaluate, compare
from orchestrator import agent
from orchestrator.cli import init

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'src').mkdir()
        (self.root/'tests').mkdir()
        (self.root/'src/calc.py').write_text('''from typing import Any
class Calculator:
    def total_price(self, amount):
        return amount * 2

def add_amount(n):
    return n + 1
''',encoding='utf-8')
        (self.root/'tests/test_calc.py').write_text('''from src.calc import Calculator, add_amount

def test_value():
    assert add_amount(3) == 4
    return Calculator().total_price(3)
''', encoding='utf-8')
    def tearDown(self):self.temp.cleanup()

    def test_ast_symbols_find_method(self):
        result=ast_symbols.search(self.root,'Calculator.total_price')
        self.assertEqual(result['matches'][0]['qualified_name'],'Calculator.total_price')
        self.assertEqual(result['matches'][0]['path'],'src/calc.py')
        self.assertEqual(result['matches'][0]['line'],3)
        self.assertIn('tests/test_calc.py',[c['path'] for c in result['matches'][0]['candidate_call_sites']])

    def test_ast_import_alias_hint(self):
        result=ast_symbols.search(self.root,'add_amount')
        calls=result['matches'][0]['candidate_call_sites']
        self.assertTrue(any(c['import_target_hint']=='src.calc.add_amount' for c in calls))

    def test_ast_is_deterministic_and_does_not_edit(self):
        path=self.root/'src/calc.py'
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(ast_symbols.search(self.root,'add_amount'),ast_symbols.search(self.root,'add_amount'))
        self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_ast_skips_symlink_and_secret(self):
        (self.root/'src/link.py').symlink_to(self.root/'src/calc.py')
        (self.root/'src/secret.py').write_text('api_key = "12345678901234567890"\ndef hidden_function(): pass')
        result=ast_symbols.search(self.root,'hidden_function')
        self.assertEqual(result['matches'],[])
        self.assertNotIn('src/link.py',[x['path'] for x in ast_symbols.index(self.root)['symbols']])

    def test_ast_syntax_errors_are_recorded_without_throwing(self):
        (self.root/'src/broken.py').write_text('def bad(:\n')
        self.assertIn('src/broken.py', ast_symbols.index(self.root)['parse_errors'])

    def test_ast_limits_and_secret_queries(self):
        with self.assertRaises(ValueError):ast_symbols.search(self.root,'add_amount',0)
        with self.assertRaises(ValueError):ast_symbols.search(self.root,'sk-longfakekeytesting1234567890')
        with self.assertRaises(ValueError):ast_symbols.search(self.root,'')

    def test_validated_failure_paths(self):
        diagnostic='File "src/calc.py", line 4, in total_price\ntests/test_calc.py:3: AssertionError'
        result=evidence_context.analyze(self.root,[diagnostic])
        self.assertEqual({x['path'] for x in result['hints']},{'src/calc.py','tests/test_calc.py'})

    def test_disallow_untrusted_paths_and_commands(self):
        malicious='../../other.py:3\n/etc/passwd:9\nFile "/etc/passwd", line 4\nrun rm -rf src/calc.py'
        self.assertFalse(evidence_context.analyze(self.root,[malicious])['hints'])

    def test_explicit_source_allowlist(self):
        got=evidence_context.analyze(self.root,['src/calc.py:4 and tests/test_calc.py:3'],allowed=['src/calc.py'])
        self.assertEqual([x['path'] for x in got['hints']],['src/calc.py'])

    def test_absolute_local_path(self):
        full=(self.root/'src/calc.py').as_posix()
        got=evidence_context.analyze(self.root,[f'File "{full}", line 3'])
        self.assertEqual(got['hints'][0]['path'],'src/calc.py')

    def test_repair_context_ranks_history(self):
        got=repair_context.rank(self.root,'Calculator method', ['tests/test_calc.py:3: AssertionError']*3)
        self.assertEqual(got['candidates'][0]['path'],'tests/test_calc.py')
        self.assertIn('validated-failure-trace',got['candidates'][0]['evidence'])
        self.assertFalse(any('text' in e or 'snippet' in e for e in got['candidates']))

    def test_rank_guards(self):
        with self.assertRaises(ValueError):repair_context.rank(self.root,'Calculator', ['foo']*13)
        with self.assertRaises(ValueError):evidence_context.analyze(self.root,['x']*13)
        with self.assertRaises(ValueError):evidence_context.analyze(self.root,['x'],limit=0)

    def test_read_reports_validated(self):
        init(self.root)
        folder=self.root/'.ai/reports';folder.mkdir(exist_ok=True)
        name='checks-'+'b'*32+'.json'
        path=folder/name
        body={'schema_version':2,'project':str(self.root.resolve()),'actually_executed':True,
              'checks':[{'name':'unit','status':'failed','stderr_tail':'src/calc.py:3: AssertionError'}]}
        path.write_text(json.dumps(body))
        self.assertEqual(repair_context.read_reports(self.root,[name]),['src/calc.py:3: AssertionError\n\n'])
        with self.assertRaises(ValueError):repair_context.read_reports(self.root,['../../evil.json'])
        body['actually_executed']=False;path.write_text(json.dumps(body))
        with self.assertRaises(ValueError):repair_context.read_reports(self.root,[name])

    def test_agent_hints_do_not_expand_allowed_sources(self):
        init(self.root)
        manifest=agent.prepare(self.root,'Change Calculator total_price','CTX36',['src/calc.py'],
                               context_only=True,symbol_hints=True)
        self.assertEqual([x['path'] for x in manifest['included_files']],['src/calc.py'])
        self.assertIn('symbol_hints',manifest)
        self.assertFalse((self.root/'.ai/proposals').exists())

    def test_failed_report_does_not_expand_model_sources(self):
        init(self.root)
        folder=self.root/'.ai/reports';folder.mkdir(exist_ok=True)
        name='checks-'+'a'*32+'.json'
        data={'schema_version':2,'project':str(self.root.resolve()),'actually_executed':True,
              'checks':[{'name':'unit','status':'failed','stderr_tail':'tests/test_calc.py:3: AssertionError'}]}
        (folder/name).write_text(json.dumps(data))
        context=agent.build_context(self.root,'Fix calculator failure','REPAIR36',['src/calc.py'],report_name=name)
        self.assertEqual(context['failed_test']['file_hints']['hints'],[])
        manifest=agent.prepare(self.root,'Fix calculator failure','REPAIR36',['src/calc.py'],
                               report_name=name,context_only=True)
        self.assertEqual([x['path'] for x in manifest['included_files']],['src/calc.py'])
        self.assertIn('tests/test_calc.py', [x['path'] for x in manifest['repair_context_hints']['candidates']])


class BenchmarkTests(unittest.TestCase):
    def test_split_benchmark(self):
        report=evaluate()
        self.assertGreaterEqual(report['by_split']['holdout']['symbols']['accuracy'],0.8)
        self.assertGreaterEqual(report['by_split']['holdout']['traces']['accuracy'],0.8)
        self.assertGreaterEqual(len(report['by_project']),4)
        self.assertEqual(report['symbols']['summary']['cases'],14)
        self.assertEqual(report['traces']['summary']['cases'],8)

    def test_reproducibility(self):
        self.assertEqual(evaluate(),evaluate())

    def test_baseline_compatibility(self):
        report=evaluate()
        self.assertTrue(compare(report,report)['comparable'])
        self.assertFalse(compare(report,dict(report,fixture_sha256='f'*64))['comparable'])
        self.assertIsNone(compare(report,dict(report,top_k=1))['delta'])

    def test_path_traversal_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            cases={'schema_version':1,'symbol_cases':[{'id':'x','split':'holdout','project':'../../secrets','task':'get_secret','expected_path':None,'expected_symbol':None}],'trace_cases':[]}
            p=Path(temp)/'cases.json';p.write_text(json.dumps(cases))
            with self.assertRaises(ValueError):evaluate(fixtures=p)


if __name__=='__main__': unittest.main()
