#!/usr/bin/env python3
"""V4.0 reproducible, fixed toolkit verification profiles.

No arbitrary command injection. BUNDLED fixture tests can execute Python/JS
code and are NOT sandboxed: execution requires explicit --execute.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _matrix(profile: str):
    if profile not in ('smoke','full'):raise ValueError('unknown verification profile')
    steps=[
        ('catalog', [sys.executable,'tools/audit_catalog.py'], 30, None),
        ('router', [sys.executable,'tools/benchmark_router.py'], 35, None),
        ('v4-unit', [sys.executable,'-m','unittest','tests.test_v40','-q'], 75, None),
        ('todo-api', [sys.executable,'-m','unittest','discover','-s','tests','-q'], 60, 'examples/runnable-todo'),
    ]
    if profile=='full':
        # Run each historical module in an independent process. The legacy
        # monolithic discovery command can hang due to shared module state.
        for f in sorted((ROOT/'tests').glob('test_*.py')):
            if f.name=='test_v40.py':
                continue  # already covered as v4-unit above
            steps.append(('unit-'+f.stem, [sys.executable,'-m','unittest','tests.'+f.stem,'-q'], 65, None))
        steps.extend([
            ('node-fixture', ['node','--test','benchmarks/projects/js-dashboard/tests/report.test.js'], 30, None),
            ('typescript-fixture', ['tsc','--project','benchmarks/projects/ts-workspace/tsconfig.json','--noEmit'], 40, None),
            ('repair-demo', [sys.executable,'examples/loop-demo/run_offline_demo.py'], 45, None),
            ('v35-benchmark', [sys.executable,'tools/benchmark_v35.py','--min-recall','0.8','--min-triage','0.8'], 40, None),
            ('v36-benchmark', [sys.executable,'tools/benchmark_v36.py','--min-holdout','0.75'], 40, None),
            ('v37-benchmark', [sys.executable,'tools/benchmark_v37.py','--min-accuracy','0.8'], 45, None),
            ('v38-benchmark', [sys.executable,'tools/benchmark_v38.py','--modules','12'], 45, None),
        ])
    return steps


def verify(*,profile='smoke',execute=False,output:Path|None=None) -> dict:
    if output is not None and not execute:
        raise ValueError('report output requires explicitly approved --execute')
    if output is not None:
        dest=output.absolute()
        allowed=(ROOT/'benchmarks'/'reports').resolve()
        if (dest.parent!=allowed or not dest.name.endswith('.json') or dest.is_symlink()
                or len(dest.name)>100):
            raise ValueError('report output must be a .json file under benchmarks/reports (no symlinks)')
    rows=[]
    for name,cmd,timeout,cwd in _matrix(profile):
        if execute:
            print(f'[verify] starting {name}', file=sys.stderr, flush=True)
        item={'name':name,'command':cmd,'status':'planned','timeout_seconds':timeout}
        if execute:
            if shutil.which(cmd[0]) is None and not Path(cmd[0]).is_file():
                item['status']='skipped'; item['reason']='optional executable unavailable'
            else:
                start=time.monotonic()
                try:
                    env={k:v for k,v in os.environ.items() if k in ('PATH','SYSTEMROOT','WINDIR','LANG','LC_ALL','HOME','TMP','TEMP','TMPDIR')}
                    env['PYTHONDONTWRITEBYTECODE']='1'
                    completed=subprocess.run(cmd,cwd=ROOT/cwd if cwd else ROOT,env=env,
                                            timeout=timeout,capture_output=True,text=True,check=False,errors='replace')
                    item.update({'status':'passed' if completed.returncode==0 else 'failed',
                                 'exit_code':completed.returncode,'duration_seconds':round(time.monotonic()-start,3)})
                    # Keep log lengths bounded; avoid leaking potentially private project content.
                    if completed.returncode:
                        item['diagnostic_tail']=(completed.stderr or completed.stdout)[-500:]
                except subprocess.TimeoutExpired:
                    item.update({'status':'failed','reason':'timeout','duration_seconds':round(time.monotonic()-start,3)})
                except OSError:
                    item.update({'status':'failed','reason':'process could not start'})
        rows.append(item)
        if execute:
            print(f'[verify] finished {name}: {item["status"]}', file=sys.stderr, flush=True)
    result={'schema_version':1,'toolkit_version':'4.8','profile':profile,
            'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),
            'actually_executed':bool(execute),'steps':rows,
            'summary':{status:sum(x['status']==status for x in rows)
                       for status in ('passed','failed','skipped','planned')},
            'note':'Bundled test commands only. No user project execution, network calls, remote PR, or model invocation; local toolkit fixture tests are NOT sandboxed.'}
    if output:
        dest=output.absolute()
        allowed=(ROOT/'benchmarks'/'reports').resolve()
        allowed.mkdir(exist_ok=True)
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result
