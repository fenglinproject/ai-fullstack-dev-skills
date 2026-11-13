"""A minimal child process for framing/timeout tests. NOT a real language server."""
import json
import sys
import time
from pathlib import Path


def read_message():
    size=None
    while True:
        line=sys.stdin.buffer.readline()
        if not line:
            return None
        if line == b'\r\n':
            break
        if line.lower().startswith(b'content-length:'):
            size=int(line.split(b':',1)[1].strip())
    return json.loads(sys.stdin.buffer.read(size))


def write_message(value):
    body=json.dumps(value).encode()
    sys.stdout.buffer.write(b'Content-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body)
    sys.stdout.buffer.flush()


def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'normal'
    while True:
        request=read_message()
        if request is None:
            break
        method=request.get('method')
        if mode == 'hang' and method == 'workspace/symbol':
            time.sleep(10)
            continue
        if mode == 'malformed' and method == 'workspace/symbol':
            sys.stdout.buffer.write(b'Content-Length: 99999999\r\n\r\n')
            sys.stdout.buffer.flush()
            break
        if method == 'initialize':
            write_message({'jsonrpc':'2.0','id':request['id'],'result':{'capabilities':{'workspaceSymbolProvider':True,'definitionProvider':True}}})
        elif method == 'workspace/symbol':
            # Exercise ignored server notification & unauthorized server request.
            write_message({'jsonrpc':'2.0','method':'window/logMessage','params':{'type':3,'message':'hello'}})
            write_message({'jsonrpc':'2.0','id':56789,'method':'workspace/configuration','params':{'items':[]}})
            root=Path.cwd()
            rows=[{'name':'Widget','location':{'uri':(root/'src/widget.py').as_uri(),'range':{'start':{'line':2,'character':0}}}},
                  {'name':'Widget','location':{'uri':Path('/etc/passwd').as_uri(),'range':{'start':{'line':0,'character':0}}}}]
            write_message({'jsonrpc':'2.0','id':request['id'],'result':rows})
        elif method == 'textDocument/definition':
            root=Path.cwd()
            write_message({'jsonrpc':'2.0','id':request['id'],'result':{'uri':(root/'src/widget.py').as_uri(),'range':{'start':{'line':2,'character':0}}}})
        elif method == 'shutdown':
            write_message({'jsonrpc':'2.0','id':request['id'],'result':None})
        elif method == 'exit':
            break
        # A valid response to our arbitrary request requires no reply.


if __name__ == '__main__':
    main()
