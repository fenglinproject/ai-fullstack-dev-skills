#!/usr/bin/env python3
"""Narrow opt-in test runner. NOT a sandbox for untrusted repository code.

Only supports Python's unittest discovery and JavaScript syntax checks. A test
module can execute arbitrary Python; users must review/trust the repository.
Arbitrary npm scripts, Python -c/-m <module>, npx and shell commands are rejected.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

SCHEMA_VERSION=2


def within(root:Path, relative:str, directory:bool|None=None)->Path:
    if not isinstance(relative,str) or not relative or '\x00' in relative:
        raise ValueError('path is invalid')
    source=Path(relative)
    if source.is_absolute():raise ValueError('absolute paths are not allowed')
    base=root.resolve();p=(base/source).resolve()
    if p!=base and base not in p.parents:raise ValueError('path escapes project')
    if directory is True and not p.is_dir():raise ValueError(f'directory not found: {relative}')
    if directory is False and not p.is_file():raise ValueError(f'file not found: {relative}')
    return p


def verify_project_path(project,cwd):return within(project,cwd,directory=True)


def _parse_unittest(args,project,cwd):
    # Restrict to unittest discovery, not arbitrary importable Python modules.
    if args[:4] not in (["python","-m","unittest","discover"],["python3","-m","unittest","discover"]):
        raise ValueError('only python -m unittest discover is allowed')
    tail=args[4:]; found=set();i=0
    while i<len(tail):
        tok=tail[i]
        if tok in {'-v','-q'}:
            if tok in found:raise ValueError('duplicate unittest flag')
            found.add(tok);i+=1;continue
        if tok not in {'-s','-p','-t'} or tok in found or i+1>=len(tail):
            raise ValueError('unsupported unittest discover option')
        value=tail[i+1]
        if tok=='-p':
            if len(value)>80 or not re.fullmatch(r'[a-zA-Z0-9_*?.-]+\.py',value):
                raise ValueError('invalid unittest filename pattern')
        else: within(cwd,value,directory=True)
        found.add(tok);i+=2
    # Never implicitly run all project modules. Prefer explicit tests directory.
    if '-s' not in found:raise ValueError('test start directory must be explicit (-s)')


def validate_check(check,project):
    if not isinstance(check,dict):raise ValueError('check must be an object')
    args=check.get('args')
    if not isinstance(args,list) or not args or not all(isinstance(a,str) and a for a in args):
        raise ValueError('args must be nonempty string array')
    if any(any(x in a for x in ('\n','\r','\x00')) for a in args):
        raise ValueError('newline or NUL in arguments')
    cwd=verify_project_path(project,check.get('cwd','.'))
    exe=args[0]
    if exe in ('python','python3'):
        _parse_unittest(args,project,cwd)
    elif exe=='node':
        if len(args)!=3 or args[1]!='--check':raise ValueError('only node --check FILE is allowed')
        target=within(cwd,args[2],directory=False)
        if target.suffix.lower() not in {'.js','.mjs','.cjs'}:
            raise ValueError('node syntax check requires .js/.mjs/.cjs file')
    else:
        raise ValueError('executable not allowlisted for read-only checks')
    timeout=check.get('timeout_seconds',30)
    if isinstance(timeout,bool) or not isinstance(timeout,int) or not 1<=timeout<=120:
        raise ValueError('timeout_seconds must be 1..120')
    return args,timeout


def run(project:Path,execute:bool=False,name:str|None=None)->dict:
    project=project.resolve()
    path=project/'.ai'/'checks.json'
    if path.is_symlink():raise ValueError('symlink checks.json is not supported')
    within(project,'.ai',directory=True)
    config=json.loads(path.read_text('utf-8'))
    if not isinstance(config.get('checks'),list):raise ValueError('checks must be a list')
    reports=[]
    selected=[c for c in config['checks'] if name is None or c.get('name')==name]
    if name is not None and not selected:raise ValueError(f'unknown check name: {name}')
    for c in selected:
        item={'name':c.get('name','unnamed'),'args':c.get('args',[]),'status':'not_run'}
        try:
            cmd,timeout=validate_check(c,project)
            if not c.get('enabled',False):item['status']='disabled'
            elif execute:
                # Clean exported environment: testing *may still execute arbitrary repository code*.
                env={k:v for k,v in os.environ.items() if k in ('PATH','SYSTEMROOT','WINDIR','LANG','LC_ALL')}
                env.update({'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','NO_COLOR':'1'})
                result=subprocess.run(cmd,cwd=verify_project_path(project,c.get('cwd','.')),
                                      timeout=timeout,capture_output=True,text=True,check=False,
                                      env=env,errors='replace')
                item.update({'status':'passed' if result.returncode==0 else 'failed',
                 'exit_code':result.returncode,'stdout_tail':result.stdout[-2000:], 'stderr_tail':result.stderr[-2000:]})
            else:item['status']='planned_only'
        except subprocess.TimeoutExpired:item['status']='timeout'
        except (ValueError,OSError,FileNotFoundError) as e:
            item.update({'status':'error','error':str(e)})
        reports.append(item)
    return {'schema_version':SCHEMA_VERSION,'project':str(project),
            'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),
            'actually_executed':execute,'checks':reports,
            'summary':{k:sum(x['status']==k for x in reports) for k in
                       ['passed','failed','error','timeout','disabled','planned_only','not_run']},
            'security_note':'Trusted repository only: tests can execute arbitrary project code; this runner is not a sandbox.'}


def save_report(project:Path,report:dict)->str:
    project=project.resolve()
    within(project,'.ai',directory=True)
    folder=project/'.ai'/'reports';folder.mkdir(parents=True,exist_ok=True)
    if folder.is_symlink():raise ValueError('reports directory cannot be a symlink')
    # O_EXCL to avoid overwriting old evidence.
    filename='checks-'+uuid.uuid4().hex+'.json'
    p=folder/filename
    with p.open('x',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    return str(p)


def main(argv=None):
    p=argparse.ArgumentParser(description='Preview or run reviewed tests (trusted local projects only)')
    p.add_argument('--project',default=str(Path(__file__).resolve().parents[1]/'project'))
    p.add_argument('--run',action='store_true',help='opt in to execute *trusted* test code')
    p.add_argument('--name',help='select one named check')
    p.add_argument('--save-report',action='store_true',help='save immutable-name evidence in .ai/reports')
    a=p.parse_args(argv)
    project=Path(a.project).resolve()
    if not project.is_dir():p.error('project does not exist')
    try:
        report=run(project,a.run,a.name)
        if a.save_report:report['report_path']=save_report(project,report)
    except (FileNotFoundError,ValueError,OSError,json.JSONDecodeError) as e:p.error(str(e))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if any(x['status'] in ('failed','timeout','error') for x in report['checks']):sys.exit(1)
if __name__=='__main__':main()
