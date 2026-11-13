"""V4.1 dashboard boundary, privacy, HTTP, live project snapshot tests."""
from __future__ import annotations

import hashlib
import http.client
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from dashboard.server import create_server
from dashboard.snapshot import snapshot
from orchestrator.cli import init, add_task, set_task
from tools.run_checks import save_report

ROOT = Path(__file__).resolve().parents[1]


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)

    def test_empty_project_read_only(self):
        data = snapshot(self.project)
        self.assertEqual(data['stats']['tasks'], 0)
        self.assertFalse((self.project / '.ai').exists())
        self.assertEqual(data['mode'], 'read-only')
        self.assertTrue(data['warnings'])

    def test_existing_task_and_report_fingerprint(self):
        init(self.project)
        add_task(self.project, 'TASK1', 'Implement safe feature')
        report = {'schema_version': 2, 'project': str(self.project.resolve()),
                  'actually_executed': True, 'timestamp': '2026-11-08T10:00:00+00:00',
                  'checks': [{'name': 'python-unittest', 'status': 'passed', 'stdout_tail': 'SECRET-DO-NOT-DISPLAY'}]}
        file = Path(save_report(self.project, report))
        set_task(self.project, 'TASK1', 'done', report=file.name)
        data = snapshot(self.project)
        self.assertEqual(data['stats']['tasks'], 1)
        self.assertEqual(data['stats']['successful_reports'], 1)
        self.assertEqual(data['tasks'][0]['evidence_integrity'], 'verified')
        self.assertNotIn('SECRET-DO-NOT-DISPLAY', json.dumps(data))
        file.write_text(file.read_text() + ' ', encoding='utf-8')
        data = snapshot(self.project)
        self.assertEqual(data['stats']['evidence_alerts'], 1)
        self.assertEqual(data['tasks'][0]['evidence_integrity'], 'warning')

    def test_change_and_repair_private_fields_not_exposed(self):
        init(self.project)
        changes = self.project / '.ai' / 'changes' / 'change-1'
        changes.mkdir(parents=True)
        (changes / 'manifest.json').write_text(json.dumps({
            'schema_version': 3, 'change_id': 'change-1', 'task_id': 'TASK1',
            'status': 'applied', 'files': [{'path': 'src/private.py', 'diff': 'SECRET-CHANGE-RAW',
            'backup_base64': 'PRIVATE-BACKUP'}], 'summary': 'PRIVATE-SUMMARY'}), encoding='utf-8')
        loop = self.project / '.ai' / 'loops' / 'loop-example'
        loop.mkdir(parents=True)
        (loop / 'state.json').write_text(json.dumps({
            'schema_version': 1, 'run_id': 'loop-example', 'stage': 'completed',
            'created_at': '2026-11-08T09:00:00+00:00', 'updated_at': '2026-11-08T09:03:00+00:00',
            'task': 'PRIVATE-PROMPT', 'attempts': [{'status': 'failed'}, {'status': 'passed'}]}), encoding='utf-8')
        data = snapshot(self.project)
        self.assertEqual(data['stats']['changes'], 1)
        self.assertEqual(data['loops']['runs'], 1)
        self.assertEqual(data['loops']['completed'], 1)
        self.assertEqual(data['loops']['total_attempts'], 2)
        serialized = json.dumps(data)
        for secret in ('PRIVATE-SUMMARY', 'PRIVATE-PROMPT', 'SECRET-CHANGE-RAW', 'PRIVATE-BACKUP'):
            self.assertNotIn(secret, serialized)

    def test_symlink_project_ai_rejected(self):
        elsewhere = self.project / 'elsewhere'
        elsewhere.mkdir()
        (self.project / '.ai').symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            snapshot(self.project)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            create_server(self.project)

    def test_task_and_report_symlinks_not_followed(self):
        init(self.project)
        secret = self.project / 'secret.json'
        secret.write_text('{"title":"NEVER-EXPOSED-SECRET"}')
        (self.project / '.ai' / 'task_state.json').unlink()
        (self.project / '.ai' / 'task_state.json').symlink_to(secret)
        reports = self.project / '.ai' / 'reports'
        reports.mkdir()
        (reports / 'stolen.json').symlink_to(secret)
        data = snapshot(self.project)
        self.assertEqual(data['tasks'], [])
        self.assertEqual(data['reports'], [])
        self.assertNotIn('NEVER-EXPOSED-SECRET', json.dumps(data))

    def test_git_read_only(self):
        def git(*args):
            return subprocess.run(['git','-C',str(self.project),*args],check=True,capture_output=True,text=True)
        git('init','-q')
        git('config','user.email','unit@example.test')
        git('config','user.name','Unit Test')
        (self.project/'main.py').write_text('print(123)\n')
        git('add','main.py')
        git('-c','core.hooksPath=/dev/null','commit','-qm','init')
        (self.project/'main.py').write_text('print(456)\n')
        before=git('status','--porcelain').stdout
        d=snapshot(self.project)
        after=git('status','--porcelain').stdout
        self.assertEqual(before,after)
        self.assertTrue(d['git']['available'])
        self.assertTrue(d['git']['dirty'])
        self.assertIn('main.py',[r['path'] for r in d['git']['files']])


class DashboardHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.server = create_server(self.project, port=0, token='test-token-fixed')
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self._stop_server)
        self.port = self.server.server_port
        self.assertEqual(self.server.server_address[0], '127.0.0.1')

    def _stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=3)

    def request(self, method, url, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=4)
        conn.request(method,url,headers=headers or {})
        response = conn.getresponse()
        status,headers,body=response.status,dict(response.getheaders()),response.read()
        conn.close()
        return status,headers,body

    def test_auth_and_browser_assets(self):
        self.assertEqual(self.request('GET','/api/snapshot')[0],403)
        self.assertEqual(self.request('GET','/?token=wrong')[0],403)
        code,headers,_ = self.request('GET','/?token=test-token-fixed')
        self.assertEqual(code,303)
        self.assertEqual(headers['Location'],'/')
        self.assertIn('HttpOnly',headers['Set-Cookie'])
        self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        cookie=headers['Set-Cookie'].split(';',1)[0]
        for url in ('/','/static/app.js','/static/style.css','/api/snapshot'):
            code,h,body = self.request('GET',url,{'Cookie':cookie})
            self.assertEqual(code,200,url)
            self.assertGreater(len(body),100,url)
            self.assertEqual(h['Cache-Control'],'no-store, private')
            self.assertEqual(h['X-Frame-Options'],'DENY')
            if url == '/api/snapshot':
                self.assertEqual(json.loads(body)['mode'],'read-only')
        self.assertEqual(self.request('GET','/',{'Cookie':cookie})[0],200)

    def test_denied_write_and_host_header(self):
        cookie = {'Cookie':'fsdash_token=test-token-fixed'}
        self.assertEqual(self.request('POST','/api/snapshot',cookie)[0],405)
        self.assertEqual(self.request('PUT','/api/snapshot',cookie)[0],405)
        self.assertEqual(self.request('DELETE','/api/snapshot',cookie)[0],405)
        self.assertEqual(self.request('GET','/api/../../secret',cookie)[0],404)
        self.assertEqual(self.request('GET','/api/snapshot',{'Cookie':cookie['Cookie'],'Host':'malicious.example'})[0],403)
        self.assertFalse((self.project/'.ai').exists())

    def test_fullstack_cli_starts_real_loopback_server(self):
        proc = subprocess.Popen([sys.executable, str(ROOT / 'fullstack.py'), 'dashboard',
                                 '--project', str(self.project), '--port', '0'],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        try:
            self.assertRegex(proc.stdout.readline(), r'V4\.[12]')
            self.assertIn('链接', proc.stdout.readline())
            link = proc.stdout.readline().strip()
            parsed = urlsplit(link)
            self.assertEqual(parsed.hostname, '127.0.0.1')
            self.assertTrue(parsed.query.startswith('token='))
            c = http.client.HTTPConnection('127.0.0.1', parsed.port, timeout=5)
            c.request('GET', parsed.path + '?' + parsed.query)
            res = c.getresponse()
            self.assertEqual(res.status, 303)
            self.assertIn('HttpOnly', res.getheader('Set-Cookie'))
            res.read()
            c.close()
            self.assertFalse((self.project / '.ai').exists())
        finally:
            proc.terminate()
            proc.wait(timeout=5)
            proc.stdout.close()
            proc.stderr.close()

    def test_no_unsafe_dynamic_html_sink(self):
        static=(ROOT/'dashboard'/'static'/'app.js').read_text(encoding='utf-8')
        for bad in ('innerHTML','outerHTML','eval(', 'document.write(', 'fetch("https://'):
            self.assertNotIn(bad,static)
        page=(ROOT/'dashboard'/'static'/'index.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>',page)
        self.assertIn('charset="utf-8"',page)


if __name__ == '__main__':
    unittest.main()
