"""V3.7 new capability and security tests; no real external APIs."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import incremental_index as idx, test_selection
from tools.benchmark_v37 import evaluate, ROOT
from orchestrator import agent
from orchestrator.cli import init


class IncrementalIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'src').mkdir();(self.root/'tests').mkdir()
        (self.root/'src/math.py').write_text('def add(a, b):\n    return a + b\n')
        (self.root/'tests/test_math.py').write_text('from src.math import add\nassert add(1, 2) == 3\n')
    def tearDown(self):self.temp.cleanup()
    def test_read_only_without_save_cache(self):
        x=idx.build(self.root)
        self.assertEqual(x['stats'],{'files':2,'parsed':2,'reused':0,'removed':0})
        self.assertFalse((self.root/'.ai').exists())
    def test_cache_save_and_no_reparse(self):
        first=idx.build(self.root,save_cache=True);second=idx.build(self.root)
        self.assertEqual(first['stats']['parsed'],2)
        self.assertEqual(second['stats']['parsed'],0)
        self.assertEqual(second['stats']['reused'],2)
        self.assertEqual(first['files'],second['files'])
    def test_same_mtime_changed_hash(self):
        f=self.root/'src/math.py';idx.build(self.root,save_cache=True)
        old=f.stat()
        f.write_text('def sub(a, b):\n    return a - b\n')
        os.utime(f,ns=(old.st_atime_ns,old.st_mtime_ns))
        x=idx.build(self.root)
        self.assertEqual(x['stats']['parsed'],1)
        self.assertEqual(x['stats']['reused'],1)
        self.assertEqual(idx.search(x,'sub')['matches'][0]['name'],'sub')
        self.assertFalse(idx.search(x,'add')['matches'])
    def test_deletion_is_detected(self):
        idx.build(self.root,save_cache=True)
        (self.root/'src/math.py').unlink()
        x=idx.build(self.root)
        self.assertEqual(x['stats']['removed'],1)
        self.assertNotIn('src/math.py',x['files'])
    def test_safety_secret_and_symlink(self):
        outside=self.root.parent/'outside_v37.py';outside.write_text('def bad():pass')
        (self.root/'src/link.py').symlink_to(outside)
        (self.root/'src/key.py').write_text('api_key="SUPER_SECRET_VALID_TOKEN_123456"')
        try:
            x=idx.build(self.root)
            self.assertNotIn('src/link.py',x['files']);self.assertNotIn('src/key.py',x['files'])
        finally:outside.unlink(missing_ok=True)
    def test_cache_symlink_rejected(self):
        idx.build(self.root,save_cache=True)
        (self.root/'.ai/cache/code_index_v37.json').unlink()
        outside=self.root.parent/'outside_index_v37.json';outside.write_text('{}')
        (self.root/'.ai/cache/code_index_v37.json').symlink_to(outside)
        try:
            with self.assertRaisesRegex(ValueError,'symlinks'):idx.build(self.root,save_cache=True)
            self.assertEqual(outside.read_text(),'{}')
        finally:outside.unlink(missing_ok=True)
    def test_python_import_dependency(self):
        x=idx.build(self.root)
        self.assertEqual(x['files']['tests/test_math.py']['dependencies'],['src/math.py'])
    def test_failed_parse_reported(self):
        (self.root/'src/broken.py').write_text('def broken(:\n')
        x=idx.build(self.root)
        self.assertTrue(x['files']['src/broken.py']['parse_errors'])
        self.assertTrue(test_selection.select(x,['src/math.py'])['full_suite_required'])
    def test_dynamic_python_marks_uncertainty(self):
        (self.root/'src/dynamic.py').write_text("def load():\n    return __import__('src.math')\n")
        x=idx.build(self.root)
        self.assertTrue(test_selection.select(x,['src/math.py'])['full_suite_required'])
    def test_bound_and_query_validation(self):
        x=idx.build(self.root)
        for q in ('','sk-1234567890abcdefghi'):
            with self.assertRaises(ValueError):idx.search(x,q)
        for limit in (0,21,True):
            with self.assertRaises(ValueError):idx.search(x,'add',limit)
        with patch.object(idx,'MAX_FILES',1):
            with self.assertRaisesRegex(ValueError,'resource cap'):idx.build(self.root)
    def test_js_typescript_parsing(self):
        (self.root/'src/compute.ts').write_text('export class Engine { run() { return 5; } }\n')
        (self.root/'src/task.js').write_text("import {Engine} from './compute';\nfunction execute() {return new Engine().run();}\n")
        x=idx.build(self.root)
        self.assertEqual(idx.search(x,'Engine')['matches'][0]['path'],'src/compute.ts')
        self.assertIn('src/compute.ts',x['files']['src/task.js']['dependencies'])
        self.assertEqual(idx.search(x,'run')['matches'][0]['qualified_name'],'Engine.run')
    def test_dynamic_js_marks_full_suite(self):
        (self.root/'src/script.js').write_text('const m = import(variableName);')
        x=idx.build(self.root)
        self.assertTrue(test_selection.select(x,['src/math.py'])['full_suite_required'])
    def test_missing_node_is_clear_error(self):
        (self.root/'src/new.ts').write_text('export const foo = 4;')
        with patch.object(idx.shutil,'which',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'Node.js required'):idx.build(self.root)


class SelectionTests(unittest.TestCase):
    def test_four_project_dependency_selection(self):
        for project,change,wanted in (
          ('inventory-service','src/pricing.py','tests/test_orders.py'),
          ('notes-workspace','core/search.py','tests/test_notes.py'),
          ('ts-workspace','src/price.ts','tests/invoice.test.ts'),
          ('js-dashboard','src/metrics.js','tests/report.test.js')):
            with self.subTest(project=project):
                root=ROOT/'benchmarks/projects'/project
                found=test_selection.select(idx.build(root),[change])
                self.assertIn(wanted,[t['path'] for t in found['tests']])
                self.assertFalse(found['full_suite_required'])
    def test_unknown_file_conservative(self):
        x=idx.build(ROOT/'benchmarks/projects/js-dashboard')
        res=test_selection.select(x,['unknown.py'])
        self.assertTrue(res['full_suite_required'])
        self.assertIn('unknown-or-unindexed-changed-file',res['caution_flags'])
    def test_invalid_changed_files(self):
        x=idx.build(ROOT/'benchmarks/projects/js-dashboard')
        for changed in (["../key.py"],["/key.py"],[],['bad\\name'],['']):
            with self.subTest(changed=changed),self.assertRaises(ValueError):test_selection.select(x,changed)
    def test_unresolved_import(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'source.ts').write_text("import {x} from './missing'; export const y=x;")
            (root/'source.test.ts').write_text("import {y} from './source'; if(y){}")
            res=test_selection.select(idx.build(root),['source.ts'])
            self.assertTrue(res['full_suite_required'])
            self.assertIn('unresolved-local-imports',res['caution_flags'])
    def test_no_test_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a.py').write_text('x=1')
            res=test_selection.select(idx.build(root),['a.py'])
            self.assertTrue(res['full_suite_required'])
            self.assertIn('no-statically-related-tests',res['caution_flags'])


class V37IntegrationTests(unittest.TestCase):
    def test_multilang_preview_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'src').mkdir();(root/'src/price.ts').write_text('export function finalPrice(a: number){ return a; }')
            init(root)
            context=agent.prepare(root,'Adjust finalPrice implementation','TASK37',['src/price.ts'],context_only=True,multilang_hints=True)
            self.assertEqual([x['path'] for x in context['included_files']],['src/price.ts'])
            self.assertEqual(context['multilang_hints']['search']['matches'][0]['name'],'finalPrice')
            self.assertFalse((root/'.ai/proposals').exists())
    def test_benchmark(self):
        a=evaluate();b=evaluate()
        self.assertEqual(a,b)
        self.assertEqual(a['symbols']['hit'],6)
        self.assertEqual(a['test_selection']['hit'],5)
        self.assertEqual(len(a['projects']),4)
    def test_benchmark_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'cases.json';f.write_text(json.dumps({'schema_version':1,'symbol_cases':[{'project':'../secrets'}],'test_cases':[]}))
            with self.assertRaises(ValueError):evaluate(f)

if __name__=='__main__':unittest.main()
