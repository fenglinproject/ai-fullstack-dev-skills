import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
from orchestrator.cli import load,route,init,add_task,set_task,score
from tools.audit_catalog import audit
from tools.run_checks import validate_check,run

class CatalogTests(unittest.TestCase):
    def test_all_original_skills_present(self):self.assertEqual(len(load()),144)
    def test_no_broken_dependencies(self):self.assertTrue(audit()['passed'],audit()['issues'])
    def test_no_unconditional_mysql_for_every_skill(self):
        self.assertFalse(any('mysql <' in ' '.join(e['verification_commands']) for e in load().values()))
    def test_primary_skills_exist(self):
        primary=json.loads((ROOT/'orchestrator/primary_skills.json').read_text())
        self.assertTrue(set(primary['primary']).issubset(set(load())))

class RouterTests(unittest.TestCase):
    def test_small_css_change_is_light(self):
        r=route('修改按钮颜色')
        self.assertEqual(r['execution_mode'],'light')
        self.assertEqual(r['selected'][0]['id'],'frontend.static_page_build')
    def test_payment_implementation_strict(self):
        r=route('实现支付退款接口')
        self.assertEqual(r['execution_mode'],'strict')
        self.assertIn('policies/HIGH_RISK.md',r['rules'])
    def test_auth_implementation_strict(self):
        self.assertEqual(route('新增注册登录模块')['execution_mode'],'strict')
    def test_production_database_change_strict(self):
        self.assertEqual(route('生产库数据库迁移')['execution_mode'],'strict')
    def test_planning_does_not_trigger_strict(self):
        self.assertIn(route('帮我做MVP需求范围定义')['execution_mode'],('light','standard'))
    def test_analysis_only_can_be_light(self):
        self.assertEqual(route('解释支付系统是什么')['execution_mode'],'light')
    def test_explicit_skill_id_selection(self):
        r=route('请运行 requirements.prd_generator')
        self.assertEqual(r['selected'][0]['id'],'requirements.prd_generator')
    def test_unknown_task_has_safe_fallback(self):
        self.assertEqual(route('xyz_unknown_domain_string')['selected'][0]['id'],'core.project_context_collector')
    def test_request_strict_can_escalate(self):
        self.assertEqual(route('修改按钮颜色',mode='strict')['execution_mode'],'strict')
    def test_light_cannot_downgrade_payment(self):
        self.assertEqual(route('实现支付系统',mode='light')['execution_mode'],'strict')

class StateTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.path=Path(self.directory.name)
    def tearDown(self):self.directory.cleanup()
    def test_init_writes_expected_files(self):
        result=init(self.path);self.assertEqual(len(result['created']),7)
        self.assertIn('proposals/', (self.path/'.ai/.gitignore').read_text('utf-8'))
    def test_non_destructive_init(self):
        init(self.path);p=self.path/'.ai/decisions.md';p.write_text('user decisions','utf-8')
        init(self.path);self.assertEqual(p.read_text('utf-8'),'user decisions')
    def test_tasks_persist_and_verify_close(self):
        init(self.path);task=add_task(self.path,'T-1','review docs','documentation.docs_orchestrator')
        self.assertEqual(task['status'],'todo')
        self.assertEqual(set_task(self.path,'T-1','in_progress')['status'],'in_progress')
        with self.assertRaises(ValueError):set_task(self.path,'T-1','done')
        self.assertRaises(ValueError,set_task,self.path,'T-1','done',checked=True)
        self.assertEqual(set_task(self.path,'T-1','done',manual_reason='Documentation manually reviewed and accepted')['status'],'done')
        self.assertEqual(json.loads((self.path/'.ai/task_state.json').read_text())['tasks'][0]['status'],'done')
    def test_duplicate_task_rejected(self):
        init(self.path);add_task(self.path,'T-1','abc')
        with self.assertRaises(ValueError):add_task(self.path,'T-1','abc')

class CheckRunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.path=Path(self.directory.name)
        (self.path/'.ai').mkdir()
    def tearDown(self):self.directory.cleanup()
    def test_cwd_escape_denied(self):
        with self.assertRaises(ValueError):validate_check({'args':['python','-m','unittest'],'cwd':'../'},self.path)
    def test_shell_payload_denied(self):
        with self.assertRaises(ValueError):validate_check({'args':['python','-c','print(1)']},self.path)
    def test_shell_command_denied(self):
        with self.assertRaises(ValueError):validate_check({'args':['bash','-c','echo yes']},self.path)
    def test_timeout_bound(self):
        with self.assertRaises(ValueError):validate_check({'args':['python','-m','unittest'],'timeout_seconds':1000},self.path)
    def test_dry_run_does_not_claim_execution(self):
        (self.path/'tests').mkdir()
        cfg={'checks':[{'name':'sample','enabled':True,'args':['python','-m','unittest','discover','-s','tests'],'timeout_seconds':15}]}
        (self.path/'.ai/checks.json').write_text(json.dumps(cfg))
        result=run(self.path,False)
        self.assertFalse(result['actually_executed'])
        self.assertEqual(result['checks'][0]['status'],'planned_only')

if __name__=='__main__':unittest.main()
