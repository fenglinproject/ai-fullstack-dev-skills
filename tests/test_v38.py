"""V3.8 monorepo/graph/LSP boundary checks and independent disposable fixture."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import incremental_index as idx
from tools import incremental_graph as graph
from tools import monorepo_workspace as ws
from tools import lsp_import
from tools.benchmark_v38 import evaluate,paired_comparison,fixture
from tools.test_selection import select


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        fixture(self.root,4)
    def tearDown(self):self.temp.cleanup()
    def test_discover_and_names(self):
        found=ws.discover(self.root)
        self.assertEqual(len(found['packages']),4)
        self.assertEqual(found['aliases']['@fixture/pkg001'],'packages/pkg001')
    def test_workspace_edges(self):
        ix=idx.build(self.root)
        self.assertEqual(ix['files']['packages/pkg001/src/index.ts']['dependencies'],['packages/pkg000/src/index.ts'])
        result=select(ix,['packages/pkg000/src/index.ts'])
        self.assertIn('packages/pkg003/tests/index.test.ts',[x['path'] for x in result['tests']])
        self.assertFalse(result['full_suite_required'])
    def test_exclusions(self):
        (self.root/'pnpm-workspace.yaml').write_text("packages:\n  - 'packages/*'\n  - '!packages/pkg002'\n")
        names=[x['name'] for x in ws.discover(self.root)['packages']]
        self.assertNotIn('@fixture/pkg002',names)
    def test_reject_unsafe_glob(self):
        (self.root/'package.json').write_text(json.dumps({'workspaces':['../**/*']}))
        with self.assertRaisesRegex(ValueError,'unsafe workspace'):ws.discover(self.root)
    def test_reject_recursive_workspace_glob(self):
        (self.root/'package.json').write_text(json.dumps({'workspaces':['packages/**']}))
        with self.assertRaisesRegex(ValueError,'unsafe workspace'):ws.discover(self.root)
    def test_reject_duplicate_packages(self):
        p=self.root/'packages/pkg003/package.json'
        p.write_text(json.dumps({'name':'@fixture/pkg000'}))
        with self.assertRaisesRegex(ValueError,'duplicate workspace'):ws.discover(self.root)
    def test_symlink_folder_ignored(self):
        (self.root/'packages/link').symlink_to(self.root/'packages/pkg000',target_is_directory=True)
        self.assertEqual(len(ws.discover(self.root)['packages']),4)
    def test_does_not_execute_package_scripts(self):
        marker=self.root/'executed'
        content=json.loads((self.root/'package.json').read_text())
        content['scripts']={'postinstall':f'touch {marker}'}
        (self.root/'package.json').write_text(json.dumps(content))
        ws.discover(self.root)
        self.assertFalse(marker.exists())
    def test_manifest_change_relinks_existing_cache(self):
        first=idx.build(self.root,save_cache=True)
        manifest=self.root/'packages/pkg001/package.json'
        manifest.write_text(json.dumps({'name':'@fixture/renamed','source':'./src/index.ts'}))
        second=idx.build(self.root)
        self.assertEqual(second['stats']['parsed'],0)
        self.assertNotEqual(first['files']['packages/pkg002/src/index.ts']['dependencies'],
                            second['files']['packages/pkg002/src/index.ts']['dependencies'])
        self.assertIn('@fixture/pkg001',second['files']['packages/pkg002/src/index.ts']['unresolved_local_imports'])
        self.assertTrue(select(second,['packages/pkg001/src/index.ts'])['full_suite_required'])
    def test_pnpm_unsafe_nonstatic(self):
        (self.root/'pnpm-workspace.yaml').write_text('packages:\n  - \n    custom: code\n')
        with self.assertRaisesRegex(ValueError,'static'):ws.discover(self.root)


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);fixture(self.root,4)
    def tearDown(self):self.temp.cleanup()
    def test_writes_only_when_opted_in_and_detects_change(self):
        first=graph.analyze(self.root)
        self.assertIn('no-previous-graph-snapshot',first['caution_flags'])
        self.assertFalse((self.root/'.ai').exists())
        graph.analyze(self.root,save=True)
        self.assertTrue((self.root/'.ai/cache/dependency_graph_v38.json').exists())
        target=self.root/'packages/pkg000/src/index.ts'
        target.write_text('export function value(): number { return 99; }')
        diff=graph.analyze(self.root)
        self.assertIn('packages/pkg000/src/index.ts',diff['changed_or_deleted_files'])
        self.assertIn('packages/pkg001/src/index.ts',[x['path'] for x in diff['affected_dependents']])
    def test_remove_file_detected(self):
        graph.analyze(self.root,save=True)
        (self.root/'packages/pkg001/src/index.ts').unlink()
        diff=graph.analyze(self.root)
        self.assertIn('packages/pkg001/src/index.ts',diff['files_deleted'])
    def test_edge_delta(self):
        graph.analyze(self.root,save=True)
        (self.root/'packages/pkg001/src/index.ts').write_text('export function value(){ return 42; }')
        diff=graph.analyze(self.root)
        self.assertIn(['packages/pkg001/src/index.ts','packages/pkg000/src/index.ts'],diff['edges_removed'])
    def test_symlink_cache_rejected(self):
        external=self.root/'safe'
        external.write_text('{}')
        (self.root/'.ai').symlink_to(self.root/'packages')
        with self.assertRaisesRegex(ValueError,'symlink'):graph.analyze(self.root,save=True)
    def test_cache_corrupted_read_not_crash(self):
        graph.analyze(self.root,save=True)
        (self.root/'.ai/cache/dependency_graph_v38.json').write_text('{bad')
        diff=graph.analyze(self.root)
        self.assertIn('no-previous-graph-snapshot',diff['caution_flags'])
    def test_unknown_changed_full_suite(self):
        graph.analyze(self.root,save=True)
        diff=graph.analyze(self.root,changed=['missing.py'])
        self.assertTrue(diff['full_suite_required'])
    def test_max_depth_warn(self):
        graph.analyze(self.root,save=True)
        diff=graph.analyze(self.root,changed=['packages/pkg000/src/index.ts'])
        self.assertIn('packages/pkg003/src/index.ts',[x['path'] for x in diff['affected_dependents']])
        restricted=graph.compare(graph.snapshot(idx.build(self.root)),graph.snapshot(idx.build(self.root)),
                                 changed=['packages/pkg000/src/index.ts'],max_depth=1)
        self.assertIn('dependency-depth-limit',restricted['caution_flags'])


class LSPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'src').mkdir()
        self.code=self.root/'src/demo.py';self.code.write_text('def greet():\n    return 1\n')
        self.export=self.root/'lsp.json'
    def tearDown(self):self.temp.cleanup()
    def test_valid_lsp_record(self):
        self.export.write_text(json.dumps({'symbols':[{'name':'greet','location':{'uri':self.code.as_uri(),
                        'range':{'start':{'line':0,'character':0}}}}]}))
        result=lsp_import.interpret(self.root,self.export,'greet')
        self.assertEqual(result['matches'][0]['line'],1)
        self.assertEqual(result['matches'][0]['path'],'src/demo.py')
    def test_outside_and_network_uri_rejected(self):
        self.export.write_text(json.dumps({'symbols':[{'name':'bad','location':{'uri':'https://example.com','range':{'start':{'line':0}}}},
            {'name':'bad','location':{'uri':'file:///etc/passwd','range':{'start':{'line':0}}}}]}))
        result=lsp_import.interpret(self.root,self.export)
        self.assertEqual(result['matches'],[])
        self.assertEqual(result['rejected_records'],2)
    def test_reject_symlink_file(self):
        (self.root/'src/linked.py').symlink_to(self.code)
        self.export.write_text(json.dumps([{'name':'secret','location':{'uri':(self.root/'src/linked.py').as_uri(),
                  'range':{'start':{'line':0}}}}]))
        self.assertEqual(lsp_import.interpret(self.root,self.export)['matches'],[])
    def test_reject_symlink_export(self):
        target=self.root/'real.json';target.write_text('[]')
        self.export.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'invalid'):lsp_import.interpret(self.root,self.export)


class BenchmarkTests(unittest.TestCase):
    def test_generated_fixture_checks(self):
        result=evaluate(4)
        self.assertEqual(result['warm_parse_count'],0)
        self.assertEqual(result['single_edit_parse_count'],1)
        self.assertTrue(result['test_candidate_found'])
        self.assertEqual(result['model_calls'],0)
    def test_paired_outcome_math(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'outcome.json'
            f.write_text(json.dumps({'schema_version':1,'cases':[
                {'id':'a','before_pass':False,'after_pass':True},
                {'id':'b','before_pass':True,'after_pass':False},
                {'id':'c','before_pass':False,'after_pass':True}]}))
            result=paired_comparison(f)
            self.assertEqual(result['improved_cases'],2)
            self.assertEqual(result['regressed_cases'],1)
            self.assertAlmostEqual(result['absolute_delta'],1/3,places=4)
    def test_duplicate_outcomes_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'outcome.json'
            f.write_text(json.dumps({'schema_version':1,'cases':[{'id':'a','before_pass':True,'after_pass':True}]*2}))
            with self.assertRaises(ValueError):paired_comparison(f)

if __name__=='__main__':unittest.main()
