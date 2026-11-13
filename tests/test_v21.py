import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from orchestrator.cli import route,init,add_task,set_task,status
from tools.audit_catalog import audit
from tools.run_checks import run,validate_check,save_report
from tools.impact_scan import scan

ROOT=Path(__file__).resolve().parents[1]

class IntentRoutingTests(unittest.TestCase):
    def test_login_page_blue_button(self):
        r=route('把登录页按钮改成蓝色，不改认证逻辑')
        self.assertEqual((r['selected'][0]['id'],r['execution_mode']),('frontend.static_page_build','light'))
    def test_payment_checkout_css(self):
        r=route('在支付结算页面调整 CSS 间距')
        self.assertEqual((r['selected'][0]['id'],r['execution_mode']),('frontend.static_page_build','light'))
    def test_negation(self):
        r=route('不要修改数据库，只调整页面样式')
        self.assertEqual(r['execution_mode'],'light')
    def test_create_nextjs(self):
        self.assertEqual(route('创建可运行的 Next.js 应用')['selected'][0]['id'],'frontend.frontend_project_init')
    def test_wechat_miniprogram(self):
        self.assertEqual(route('开发微信小程序预约日历')['selected'][0]['id'],'frontend.miniprogram_config_generator')
    def test_k8s_health(self):
        self.assertEqual(route('添加 Kubernetes 健康检查')['selected'][0]['id'],'architecture.logging_monitoring_plan')
    def test_database_production_schema_high(self):
        self.assertEqual(route('修改生产数据库表结构')['execution_mode'],'strict')
    def test_real_auth_logic_high(self):
        self.assertEqual(route('修改用户认证逻辑')['execution_mode'],'strict')
    def test_real_payment_high(self):
        self.assertEqual(route('实现支付退款接口')['execution_mode'],'strict')
    def test_description_of_payments_low(self):
        self.assertEqual(route('解释支付系统是什么')['execution_mode'],'light')

class ExecutorGuardTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
        (self.root/'.ai').mkdir();(self.root/'tests').mkdir()
    def tearDown(self):self.t.cleanup()
    def deny(self,args):
        with self.assertRaises(ValueError):validate_check({'args':args},self.root)
    def test_deny_arbitrary_npm(self):self.deny(['npm','run','erase-all-data'])
    def test_deny_arbitrary_python_module(self):self.deny(['python','-m','my_custom_module'])
    def test_deny_node_eval(self):self.deny(['node','-e','require("fs").rmSync("data")'])
    def test_deny_shell(self):self.deny(['bash','-c','echo hi'])
    def test_deny_python_inline(self):self.deny(['python','-c','print(1)'])
    def test_deny_weird_unittest_options(self):self.deny(['python','-m','unittest','discover','-s','tests','--locals'])
    def test_deny_cwd_escape(self):
        with self.assertRaises(ValueError):validate_check({'args':['python','-m','unittest','discover','-s','tests'],'cwd':'../'},self.root)
    def test_allow_explicit_discovery(self):
        cmd,_=validate_check({'args':['python','-m','unittest','discover','-s','tests','-p','test*.py']},self.root)
        self.assertEqual(cmd[0],'python')
    def test_dry_run_not_accepted_as_evidence(self):
        init(self.root);add_task(self.root,'T-2','run tests')
        (self.root/'.ai/checks.json').write_text(json.dumps({'checks':[{'name':'t','cwd':'.',
            'args':['python','-m','unittest','discover','-s','tests'],'enabled':True}]}))
        report=run(self.root,False);filename=Path(save_report(self.root,report)).name
        with self.assertRaises(ValueError):set_task(self.root,'T-2','done',report=filename)
    def test_passed_report_closes_task(self):
        (self.root/'tests/test_dummy.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_true(self): self.assertTrue(True)\n')
        init(self.root);add_task(self.root,'T-2','run tests')
        (self.root/'.ai/checks.json').write_text(json.dumps({'checks':[{'name':'t','cwd':'.',
            'args':['python','-m','unittest','discover','-s','tests'],'enabled':True}]}))
        report=run(self.root,True)
        self.assertEqual(report['summary']['passed'],1)
        filename=Path(save_report(self.root,report)).name
        state=set_task(self.root,'T-2','done',report=filename)
        self.assertEqual(state['evidence'][0]['verification'],'check_runner')
        self.assertEqual(len(state['evidence'][0]['sha256']),64)
    def test_concurrent_task_additions_are_serialized(self):
        init(self.root)
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(lambda n:add_task(self.root,f'T-{n}','parallel addition'),range(15)))
        self.assertEqual(len(status(self.root)['tasks']),15)
    def test_evidence_tamper_is_visible(self):
        (self.root/'tests/test_dummy.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_true(self): self.assertTrue(True)\n')
        init(self.root);add_task(self.root,'T-2','verified code')
        (self.root/'.ai/checks.json').write_text(json.dumps({'checks':[{'name':'t','cwd':'.',
            'args':['python','-m','unittest','discover','-s','tests'],'enabled':True}]}))
        filename=Path(save_report(self.root,run(self.root,True))).name
        set_task(self.root,'T-2','done',report=filename)
        self.assertEqual(status(self.root)['tasks'][0]['evidence'][0]['integrity'],'valid')
        (self.root/'.ai/reports'/filename).write_text('{}')
        self.assertEqual(status(self.root)['tasks'][0]['evidence'][0]['integrity'],'modified')
    def test_failure_cannot_close(self):
        init(self.root);add_task(self.root,'T-2','run tests')
        fake={'schema_version':2,'project':str(self.root.resolve()),'actually_executed':True,
              'checks':[{'name':'x','status':'failed'}]}
        fn=Path(save_report(self.root,fake)).name
        with self.assertRaises(ValueError):set_task(self.root,'T-2','done',report=fn)
    def test_manual_attestation_needs_reason(self):
        init(self.root);add_task(self.root,'T-2','review requirements')
        with self.assertRaises(ValueError):set_task(self.root,'T-2','done',manual_reason='ok')
        state=set_task(self.root,'T-2','done',manual_reason='Reviewed all PRD acceptance criteria')
        self.assertEqual(state['evidence'][0]['verification'],'manual_attestation')

class CatalogAndImpactTests(unittest.TestCase):
    def test_catalog_mirror(self):self.assertTrue(audit()['passed'],audit()['issues'])
    def test_no_legacy_dangling_refs(self):
        index=json.loads((ROOT/'skills_index.json').read_text())
        self.assertEqual(len(index['skills']),144)
        self.assertFalse(any('testing.integration_test' in str(s) for s in index['skills']))
    def test_impact_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'frontend').mkdir();(root/'backend').mkdir()
            (root/'frontend/a.ts').write_text('const order_status = true;\n')
            (root/'backend/a.py').write_text('order_status = 3\n')
            r=scan(root,'order_status')
            self.assertEqual(r['candidate_files'],2)
            self.assertEqual({v['category'] for v in r['matches']},{'frontend','backend'})
    def test_impact_scan_is_only_textual(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn('Text match only',scan(Path(tmp),'symbol')['limitation'])

if __name__=='__main__':unittest.main()
