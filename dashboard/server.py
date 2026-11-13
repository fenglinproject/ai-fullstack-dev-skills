"""Token-gated loopback HTTP viewer; no write endpoints or project code execution."""
from __future__ import annotations

import hmac
import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from dashboard.snapshot import snapshot

STATIC = Path(__file__).resolve().parent / 'static'
RESOURCES = {'/': ('index.html', 'text/html; charset=utf-8'),
             '/static/app.js': ('app.js', 'text/javascript; charset=utf-8'),
             '/static/style.css': ('style.css', 'text/css; charset=utf-8')}
SECURITY_HEADERS = {
    'Cache-Control': 'no-store, private',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Cross-Origin-Resource-Policy': 'same-origin',
    'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
}


def create_server(project: Path, port: int = 0, token: str | None = None) -> ThreadingHTTPServer:
    """Construct an HTTP server without starting its serving loop; useful for tests."""
    root = project.resolve(strict=True)
    if not root.is_dir() or root == Path(root.anchor) or (root / '.ai').is_symlink():
        raise ValueError('invalid project directory or symlinked .ai')
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError('port must be 0..65535')
    secret = token if token is not None else secrets.token_urlsafe(32)
    if not isinstance(secret, str) or not secret or len(secret) > 256:
        raise ValueError('invalid access token')

    class DashboardHandler(BaseHTTPRequestHandler):
        server_version = 'LocalDashboard/4.2'
        sys_version = ''

        def log_message(self, format, *args):
            # No request URLs/tokens in terminal or persisted logs.
            return

        def _respond(self, status, body: bytes, content_type='text/plain; charset=utf-8', headers=None):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            for key, value in SECURITY_HEADERS.items():
                self.send_header(key, value)
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def _host_ok(self):
            expected = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            return self.headers.get('Host', '') in expected

        def _authorized(self):
            cookies = self.headers.get('Cookie', '')
            for part in cookies.split(';'):
                name, sep, value = part.strip().partition('=')
                if sep and name == 'fsdash_token' and hmac.compare_digest(value, secret):
                    return True
            return False

        def do_GET(self):
            if not self._host_ok():
                self._respond(403, b'Invalid Host header')
                return
            parsed = urlsplit(self.path)
            if parsed.path == '/' and 'token' in parse_qs(parsed.query):
                supplied = parse_qs(parsed.query).get('token', [''])[0]
                if not hmac.compare_digest(supplied, secret):
                    self._respond(403, b'Invalid access token')
                    return
                self._respond(303, b'', headers={
                    'Location': '/', 'Set-Cookie': f'fsdash_token={secret}; HttpOnly; SameSite=Strict; Path=/'})
                return
            if not self._authorized():
                self._respond(403, b'Access token required. Open the URL shown in your terminal.')
                return
            if parsed.query:
                self._respond(404, b'Not found')
                return
            if parsed.path == '/api/snapshot':
                try:
                    body = json.dumps(snapshot(root), ensure_ascii=False).encode('utf-8')
                except (ValueError, OSError) as error:
                    self._respond(503, json.dumps({'error': 'Project state unavailable', 'reason': type(error).__name__}).encode('utf-8'),
                                  'application/json; charset=utf-8')
                    return
                self._respond(200, body, 'application/json; charset=utf-8')
            elif parsed.path in RESOURCES:
                filename, mime = RESOURCES[parsed.path]
                self._respond(200, (STATIC / filename).read_bytes(), mime)
            else:
                self._respond(404, b'Not found')

        def do_POST(self):
            self._respond(405, b'Read-only dashboard. Use CLI for approved changes.', headers={'Allow': 'GET'})

        def do_PUT(self):
            self.do_POST()

        def do_DELETE(self):
            self.do_POST()

    server = ThreadingHTTPServer(('127.0.0.1', port), DashboardHandler)
    server.daemon_threads = True
    return server


def serve(project: Path, port: int = 8765, open_browser: bool = False) -> None:
    secret = secrets.token_urlsafe(32)
    with create_server(project, port, token=secret) as server:
        link = f'http://127.0.0.1:{server.server_port}/?token={secret}'
        print('AI Fullstack V4.2 本地只读控制台', flush=True)
        print('请勿把下面的本地访问链接分享给他人：', flush=True)
        print(link, flush=True)
        print('按 Ctrl+C 停止。网页不会执行测试、修改源代码或连接外部服务。', flush=True)
        if open_browser:
            webbrowser.open(link)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            print('\n控制台已停止。', flush=True)
        finally:
            server.shutdown()
