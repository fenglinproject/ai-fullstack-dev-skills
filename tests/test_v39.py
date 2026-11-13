import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import lsp_client, project_config, external_repo_benchmark
from tools.incremental_index import build
from tools.test_selection import select
from tools.incremental_graph import snapshot, compare

MOCK=Path(__file__).with_name('mock_lsp_server.py').resolve()


class LSPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'src').mkdir()
        (self.root/'src/widget.py').write_text('def unused():\n    pass\ndef Widget():\n    pass\n')

    def test_full_protocol_symbol_query(self):
        with lsp_client.LSPClient(self.root,[sys.executable,str(MOCK)]) as client:
            result=client.workspace_symbols('Widget')
        self.assertEqual(result['matches'][0]['path'],'src/widget.py')
        self.assertEqual(result['matches'][0]['line'],3)
        self.assertEqual(result['rejected'],1)

    def test_definition(self):
        with lsp_client.LSPClient(self.root,[sys.executable,str(MOCK)]) as client:
            result=client.definition('src/widget.py',0,0)
        self.assertEqual(len(result['matches']),1)

    def test_start_requires_absolute_binary(self):
        with self.assertRaises(ValueError):
            lsp_client.LSPClient(self.root,['python','file.py'])

    def test_invalid_definition_and_limit(self):
        with lsp_client.LSPClient(self.root,[sys.executable,str(MOCK)]) as client:
            with self.assertRaises(ValueError):client.definition('../etc/passwd',0,0)
            with self.assertRaises(ValueError):client.workspace_symbols('x',limit=101)

    def test_server_timeout_and_kill(self):
        with self.assertRaises(TimeoutError):
            with lsp_client.LSPClient(self.root,[sys.executable,str(MOCK),'hang'],timeout=.2) as client:
                client.workspace_symbols('Widget')

    def test_malformed_framing_rejected(self):
        with self.assertRaises(RuntimeError):
            with lsp_client.LSPClient(self.root,[sys.executable,str(MOCK),'malformed']) as client:
                client.workspace_symbols('Widget')

    def test_symlink_source_not_allowed(self):
        (self.root/'src/secret.py').symlink_to(self.root/'src/widget.py')
        with lsp_client.LSPClient(self.root,[sys.executable,str(MOCK)]) as client:
            self.assertNotIn('src/secret.py',client.allowed)


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'package.json').write_text(json.dumps({'workspaces':['packages/*']}))
        (self.root/'packages/web/src').mkdir(parents=True)
        (self.root/'packages/lib/src').mkdir(parents=True)
        (self.root/'packages/lib/package.json').write_text(json.dumps({'name':'@demo/lib','exports':{'.':{'import':'./src/index.ts'},'./util':'./src/util.ts'}}))
        (self.root/'packages/web/package.json').write_text(json.dumps({'name':'@demo/web'}))
        (self.root/'tsconfig.base.json').write_text('{ "compilerOptions": { "baseUrl": "." } }')
        (self.root/'packages/web/tsconfig.json').write_text('''{ // comment
          "extends":"../../tsconfig.base.json",
          "compilerOptions":{"baseUrl":".","paths":{"@ui/*":["src/*",],}},
          "references":[{"path":"../lib"}],
        }''')
        (self.root/'packages/lib/tsconfig.json').write_text('{}')
        (self.root/'packages/web/src/main.ts').write_text("import {helper} from '@ui/helper';\nimport {util} from '@demo/lib/util';\nexport const value=util()+helper();\n")
        (self.root/'packages/web/src/helper.ts').write_text('export const helper = () => 1;\n')
        (self.root/'packages/lib/src/util.ts').write_text('export const util = () => 2;\n')
        (self.root/'packages/lib/src/index.ts').write_text('export const unused=1;\n')
        (self.root/'packages/web/src/main.test.ts').write_text("import {value} from './main';\nexport const test=value;\n")

    def test_jsonc_quoted_comments(self):
        data=project_config._jsonc('{"url":"https://test.example/a/*b*/",/* block */"x":1,}')
        self.assertEqual(data['url'],'https://test.example/a/*b*/')
        self.assertEqual(project_config._jsonc('{"s":"literal,}",}')["s"], 'literal,}')

    def test_paths_references_and_exports(self):
        result=project_config.inspect(self.root)
        cfg=result['configs']['packages/web/tsconfig.json']
        self.assertEqual(cfg['aliases']['@ui/*'],['packages/web/src/*'])
        self.assertEqual(cfg['references'],['packages/lib/tsconfig.json'])
        self.assertEqual(result['package_exports']['@demo/lib']['./util'],['packages/lib/src/util.ts'])

    def test_index_resolves_alias_and_subpath(self):
        index=build(self.root,use_cache=False)
        row=index['files']['packages/web/src/main.ts']
        self.assertIn('packages/web/src/helper.ts',row['dependencies'])
        self.assertIn('packages/lib/src/util.ts',row['dependencies'])
        result=select(index,['packages/lib/src/util.ts'])
        self.assertIn('packages/web/src/main.test.ts',[t['path'] for t in result['tests']])

    def test_invalid_outside_config_warning(self):
        (self.root/'packages/web/tsconfig.json').write_text('{"extends":"../../../../outside.json"}')
        result=project_config.inspect(self.root)
        self.assertTrue(any('unresolved-extends' in w for w in result['warnings']))

    def test_cycle_warning(self):
        (self.root/'tsconfig.base.json').write_text('{"extends":"./packages/web/tsconfig.json"}')
        result=project_config.inspect(self.root)
        self.assertTrue(any('invalid-config' in w for w in result['warnings']))

    def test_nested_config_references_and_unresolved_alias(self):
        (self.root/'packages/web/tsconfig.json').write_text('{"compilerOptions":{"paths":{"@ui/*":["src/*"]}}}')
        result=project_config.inspect(self.root)
        self.assertEqual(result['configs']['packages/web/tsconfig.json']['aliases']['@ui/*'],['packages/web/src/*'])

    def test_incomplete_config_triggers_full_suite_warning(self):
        (self.root/'packages/web/tsconfig.json').write_text('{"extends":"missing-tsconfig.json"}')
        index=build(self.root,use_cache=False)
        self.assertIn('incomplete-project-configuration',select(index,['packages/web/src/main.ts'])['caution_flags'])
        self.assertIn('incomplete-project-configuration',compare(None,snapshot(index))['caution_flags'])

    def test_symlink_config_rejected(self):
        target=self.root/'packages/web/tsconfig.json'
        target.unlink()
        target.symlink_to(self.root/'packages/lib/tsconfig.json')
        result=project_config.inspect(self.root)
        self.assertTrue(any('invalid-config' in w for w in result['warnings']))


class IndependentRepoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name)/'independent-git-repo';self.repo.mkdir()
        (self.repo/'src').mkdir();(self.repo/'tests').mkdir()
        (self.repo/'src/math.py').write_text('def add_one(x):\n    return x + 1\n')
        (self.repo/'tests/test_math.py').write_text('from src.math import add_one\n\ndef test_math():\n    assert add_one(1) == 2\n')
        def git(*args):
            return subprocess.check_output(['git','-C',str(self.repo),*args],text=True).strip()
        git('init','-q');git('add','.');
        subprocess.run(['git','-C',str(self.repo),'-c','user.name=Bench','-c','user.email=bench@example.com','commit','-qm','fixture'],check=True)
        self.commit=git('rev-parse','HEAD')
        self.manifest=Path(self.tmp.name)/'cases.json'
        self.manifest.write_text(json.dumps({'schema_version':1,'commit_sha':self.commit,
               'symbol_cases':[{'id':'symbol1','query':'add_one','expected_path':'src/math.py','expected_symbol':'add_one'}],
               'test_cases':[{'id':'test1','changed':['src/math.py'],'expected_test':'tests/test_math.py'}]}))

    def test_pinned_clean_repo_metrics(self):
        result=external_repo_benchmark.evaluate(self.repo,self.manifest,repeats=2)
        self.assertEqual(result['commit_sha'],self.commit)
        self.assertEqual(result['symbol_results']['hits'],1)
        self.assertEqual(result['test_results']['hits'],1)
        self.assertEqual(len(result['duration_ms']['runs']),2)

    def test_dirty_repo_rejected(self):
        (self.repo/'src/math.py').write_text('edited')
        with self.assertRaisesRegex(ValueError,'clean'):
            external_repo_benchmark.evaluate(self.repo,self.manifest)

    def test_unpinned_commit_rejected(self):
        m=json.loads(self.manifest.read_text());m['commit_sha']='0'*40
        self.manifest.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'pin'):
            external_repo_benchmark.evaluate(self.repo,self.manifest)

    def test_manifest_expected_must_be_tracked(self):
        m=json.loads(self.manifest.read_text());m['symbol_cases'][0]['expected_path']='src/missing.py'
        self.manifest.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'tracked'):
            external_repo_benchmark.evaluate(self.repo,self.manifest)


if __name__=='__main__':unittest.main()
