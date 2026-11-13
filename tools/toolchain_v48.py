#!/usr/bin/env python3
"""Check pinned CI toolchain against the running machine, without installing anything."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'ci' / 'toolchain.json'


def version_check(component: str, *, runner=None) -> dict:
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    if component=='python':
        actual=f'{sys.version_info.major}.{sys.version_info.minor}'
        required=config['python_ci_minor']
    elif component in ('node','typescript'):
        command=['node','--version'] if component=='node' else ['tsc','--version']
        executable=shutil.which(command[0])
        if executable is None:
            return {'component':component,'passed':False,'reason':'command unavailable'}
        cp=(runner or subprocess.run)(command, capture_output=True,text=True,timeout=12,check=False)
        if cp.returncode!=0:
            return {'component':component,'passed':False,'reason':'version command failed'}
        actual=(cp.stdout or '').strip()
        required=config['node_ci_major'] if component=='node' else config['typescript_ci_exact']
        if component=='node':
            match=re.fullmatch(r'v(\d+)\.\d+\.\d+',actual)
            actual=match.group(1) if match else 'invalid-version'
        else:
            match=re.fullmatch(r'Version (\d+\.\d+\.\d+)',actual)
            actual=match.group(1) if match else 'invalid-version'
    else:
        raise ValueError('unknown toolchain component')
    return {'component':component,'required':str(required),'actual':actual,
            'passed':actual==str(required), 'note':'CI version policy only; not an install or integrity audit'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--component',choices=('python','node','typescript'),action='append',required=True)
    args=p.parse_args()
    rows=[version_check(c) for c in args.component]
    print(json.dumps({'schema_version':1,'checks':rows},indent=2))
    return 0 if all(r['passed'] for r in rows) else 1


if __name__=='__main__':raise SystemExit(main())
