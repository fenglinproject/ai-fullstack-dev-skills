"""Local HTTP adapter; use behind a hardened proxy and production auth before deployment."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
try:from .app import Store,handle
except ImportError:from app import Store,handle

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'frontend'
class Handler(BaseHTTPRequestHandler):
    store=None
    def response(self,status,body,content_type='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'")
        self.send_header('Cache-Control','no-store')
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path in ('/','/app.js','/style.css'):
            name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[self.path]
            mime='text/html' if name.endswith('.html') else ('application/javascript' if name.endswith('.js') else 'text/css')
            return self.response(200,(WEB/name).read_bytes(),mime+'; charset=utf-8')
        return self.api()
    def do_POST(self):return self.api()
    def do_PATCH(self):return self.api()
    def do_DELETE(self):return self.api()
    def api(self):
        try:
            raw_len=self.headers.get('Content-Length','0')
            length=int(raw_len)
            if not 0<=length<=65536:return self.response(413,b'{"error":"body too large"}')
            raw=self.rfile.read(length)
            data=json.loads(raw) if raw else {}
        except (ValueError,json.JSONDecodeError):return self.response(400,b'{"error":"invalid JSON"}')
        status,output=handle(self.store,self.command,self.path,dict(self.headers),data)
        return self.response(status,json.dumps(output,ensure_ascii=False).encode('utf-8'))

def main():
    db_path=os.getenv('TODO_DB',str(ROOT/'todo.sqlite3'))
    Handler.store=Store(db_path)
    server=ThreadingHTTPServer(('127.0.0.1',8765),Handler)
    print('Local demo at http://127.0.0.1:8765 (CTRL+C to stop)',flush=True)
    server.serve_forever()
if __name__=='__main__':main()
