#!/usr/bin/env python3
"""V3.2 bounded, human-gated AI development/repair sessions.

Each round has three independently authorized steps: propose, approve, test.
There is NO unattended code writing or test execution. Model calls are opt-in.
Test execution is trusted-local-code ONLY, NOT a security sandbox.
Journal state survives process restarts; applying operations have recovery IDs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

try:
    from orchestrator import agent, workflow
    from orchestrator.cli import ai_folder, add_task, set_task, status
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from orchestrator import agent, workflow
    from orchestrator.cli import ai_folder, add_task, set_task, status

ID_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')
STAGES = {'awaiting_approval','applying','awaiting_test','testing','awaiting_repair',
          'completed','exhausted','unverified','aborted','rollback_blocked','recovery_needed'}
MAX_ROUNDS = 5


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _root(project:Path)->Path:
    project=project.resolve(strict=True)
    ai=ai_folder(project)
    if ai.is_symlink() or not ai.is_dir() or ai.resolve()!=project/'.ai':
        raise ValueError('initialize project using orchestrator/cli.py init')
    folder=ai/'loops'
    if folder.is_symlink():raise ValueError('symlink loop directory forbidden')
    folder.mkdir(mode=0o700,exist_ok=True)
    return folder


def _run_dir(project:Path,run_id:str)->Path:
    if not isinstance(run_id,str) or not ID_RE.fullmatch(run_id):
        raise ValueError('invalid loop run_id')
    directory=_root(project)/run_id
    if directory.is_symlink() or not directory.is_dir():raise ValueError('unknown or unsafe loop run')
    return directory


def _load(project:Path,run_id:str)->dict:
    f=_run_dir(project,run_id)/'state.json'
    if f.is_symlink() or not f.is_file():raise ValueError('loop state missing or unsafe')
    state=json.loads(f.read_text('utf-8'))
    if state.get('schema_version')!=1 or state.get('run_id')!=run_id or state.get('stage') not in STAGES:
        raise ValueError('invalid loop state')
    return state


def _write(project:Path,state:dict)->None:
    target=_run_dir(project,state['run_id'])/'state.json'
    state['updated_at']=utc()
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,prefix='.loop-',delete=False) as fp:
        temp=Path(fp.name)
        os.chmod(temp,0o600)
        json.dump(state,fp,ensure_ascii=False,indent=2)
        fp.write('\n');fp.flush();os.fsync(fp.fileno())
    try:temp.replace(target)
    finally:temp.unlink(missing_ok=True)


@contextmanager
def _lock(project:Path,run_id:str):
    directory=_run_dir(project,run_id)
    path=directory/'lock'
    if path.is_symlink():raise ValueError('symlink loop lock forbidden')
    with path.open('a+b') as handle:
        if os.name=='nt':
            import msvcrt
            handle.seek(0);handle.write(b'0');handle.flush();handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX)
        try:yield
        finally:
            if os.name=='nt':
                handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(handle,fcntl.LOCK_UN)


def _proposal_file(project:Path,state:dict)->Path:
    rel=state['attempts'][-1]['proposal_path']
    path=project/rel
    expected_dir=ai_folder(project)/'proposals'
    if path.is_symlink() or path.parent.resolve()!=expected_dir.resolve() or not path.is_file():
        raise ValueError('unsafe or missing proposal path')
    if digest(path)!=state['attempts'][-1]['proposal_sha256']:
        raise ValueError('proposal changed since review; refuse to apply')
    return path


def _provider_args(*,response_file=None,endpoint=None,model=None,api_key_env='AI_CODING_API_KEY',
                   send_to_model=False,allow_local_http=False):
    return dict(response_file=Path(response_file) if response_file else None,
        endpoint=endpoint,model=model,api_key_env=api_key_env,
        send_to_model=send_to_model,allow_local_http=allow_local_http)


def _append_proposal(project:Path,state:dict,*,report_name:str|None=None,**provider)->dict:
    result=agent.prepare(project,state['task'],state['task_id'],state['include'],
                         create_prefixes=state['allow_create_prefixes'],report_name=report_name,**provider)
    proposal_path=project/result['proposal_path']
    state['attempts'].append({'round':len(state['attempts'])+1,
                             'proposal_path':result['proposal_path'],
                             'proposal_sha256':digest(proposal_path),
                             'created_at':utc(),'status':'awaiting_approval'})
    state['stage']='awaiting_approval'
    output={'proposal_path':result['proposal_path'],'provider':result['provider']}
    if 'repair_strategy' in result:output['repair_strategy']=result['repair_strategy']
    return output


def start(project:Path,task:str,task_id:str,include:list[str],*,max_rounds:int=3,
          allow_create_prefixes:list[str]|None=None,auto_context:bool=False,auto_limit:int=6,**provider)->dict:
    project=project.resolve(strict=True)
    if isinstance(max_rounds,bool) or not isinstance(max_rounds,int) or not 1<=max_rounds<=MAX_ROUNDS:
        raise ValueError('max_rounds must be 1..5')
    _root(project)
    run_id='loop-'+uuid.uuid4().hex
    state={'schema_version':1,'run_id':run_id,'task':task,'task_id':task_id,'include':include,
           'allow_create_prefixes':allow_create_prefixes or [],'max_rounds':max_rounds,
           'attempts':[],'stage':'awaiting_approval','created_at':utc(),'updated_at':utc()}
    # A model failure does not create an incomplete session. No API keys persisted.
    if auto_context:
        if provider.get('send_to_model'):
            raise ValueError('preview and explicitly approve --include paths before sending local code to a live model')
        from tools.context_retrieval import retrieve
        candidates=retrieve(project,task,auto_limit,include_snippets=False)
        state['include']=list(dict.fromkeys([*include,*(c['path'] for c in candidates['results'])]))
        if len(state['include'])>agent.MAX_SOURCE_FILES:
            raise ValueError('selected context exceeds 12 files')
    info=_append_proposal(project,state,**provider)
    folder=_root(project)/run_id
    folder.mkdir(mode=0o700)
    _write(project,state)
    return {'run_id':run_id,'stage':state['stage'],'round':1,'max_rounds':max_rounds,**info,
            'next':'Inspect proposal and run approve with explicit --approve; no source modified.'}


def _reconcile(project:Path,state:dict)->dict:
    if state['stage']!='applying':return state
    attempt=state['attempts'][-1]
    operation_id=attempt.get('operation_id')
    if not operation_id:state['stage']='recovery_needed';_write(project,state);return state
    matches=[]
    for manifest in (ai_folder(project)/'changes').glob('*/manifest.json'):
        if manifest.is_symlink() or not manifest.is_file():continue
        data=json.loads(manifest.read_text('utf-8'))
        if data.get('operation_id')==operation_id:
            matches.append(data)
    if len(matches)==1 and matches[0].get('status')=='applied':
        attempt['change_id']=matches[0]['change_id']
        attempt['status']='applied'
        state['stage']='awaiting_test'
    elif not matches:
        state['stage']='awaiting_approval'
        attempt['status']='awaiting_approval'
        attempt.pop('operation_id',None)
    else:
        state['stage']='recovery_needed'
    _write(project,state)
    return state


def inspect(project:Path,run_id:str)->dict:
    project=project.resolve(strict=True)
    with _lock(project,run_id):
        state=_reconcile(project,_load(project,run_id))
        next_steps={'awaiting_approval':'review pending proposal, then approve --approve',
                    'awaiting_test':'test --trust-project-code (runs trusted local tests)',
                    'testing':'tests may have executed before interruption; inspect reports, then explicitly re-run test if needed',
                    'awaiting_repair':'repair with explicit offline response or --send-to-model',
                    'unverified':'No passing or failing executed checks; configure valid enabled tests, then explicitly re-test',
                    'rollback_blocked':'review drift, then abort --restore --approve again',
                    'recovery_needed':'manual recovery required; inspect .ai/changes before proceeding'}
        return {'run_id':run_id,'stage':state['stage'],'round':len(state['attempts']),
                'max_rounds':state['max_rounds'],'attempts':state['attempts'],
                'next':next_steps.get(state['stage'],'No automatic action; inspect recorded results.')}


def approve(project:Path,run_id:str,*,approved:bool=False,high_risk_reviewed:bool=False)->dict:
    if not approved:raise ValueError('explicit --approve required to apply source changes')
    project=project.resolve(strict=True)
    with _lock(project,run_id):
        state=_reconcile(project,_load(project,run_id))
        if state['stage']!='awaiting_approval':raise ValueError('current stage is not awaiting approval')
        path=_proposal_file(project,state)
        proposal=workflow.load_proposal(path)
        attempt=state['attempts'][-1]
        attempt['operation_id']='op-'+uuid.uuid4().hex
        state['stage']='applying';_write(project,state)
        try:
            result=workflow.apply(project,proposal,approved=True,
                high_risk_reviewed=high_risk_reviewed,operation_id=attempt['operation_id'])
        except Exception:
            # If a manifest was partially written or a process was interrupted, require reconciliation.
            _reconcile(project,state)
            raise
        attempt['change_id']=result['change_id'];attempt['status']='applied'
        state['stage']='awaiting_test';_write(project,state)
        return {'run_id':run_id,'round':attempt['round'],'change_id':result['change_id'],
                'stage':'awaiting_test','next':'Run test --trust-project-code only in an environment you trust.'}


def test(project:Path,run_id:str,*,trust_project_code:bool=False,isolated_image:str|None=None)->dict:
    if trust_project_code and isolated_image:raise ValueError('choose trusted host checks OR isolated Docker checks, not both')
    if not trust_project_code and not isolated_image:
        raise ValueError('running tests requires --trust-project-code or --isolated-image')
    if isolated_image:
        from tools.isolated_checks import check_image
        import shutil
        check_image(isolated_image)
        if shutil.which('docker') is None:
            raise ValueError('Docker CLI unavailable; test stage not changed')
    project=project.resolve(strict=True)
    with _lock(project,run_id):
        state=_load(project,run_id)
        if state['stage'] not in ('awaiting_test','testing','unverified'):
            raise ValueError('no applied change is awaiting tests')
        attempt=state['attempts'][-1]
        state['stage']='testing';_write(project,state)
        try:
            result=workflow.verify(project,attempt['change_id'],execute=True,close_task=False,isolated_image=isolated_image)
        except Exception:
            # An interrupted test might have run already; only explicit re-test is permitted.
            state['stage']='testing';_write(project,state)
            raise
        report=project/result['report']
        attempt['report_path']=result['report']
        attempt['report_sha256']=digest(report)
        attempt['all_passed']=result['all_passed']
        report_data=json.loads(report.read_text('utf-8'))
        from tools.failure_triage import summarize
        attempt['failure_categories']=[x['category'] for x in summarize(report_data)['checks']]
        has_failures=any(c.get('status') in ('failed','error','timeout') for c in report_data.get('checks',[]))
        attempt['status']='passed' if result['all_passed'] else ('failed' if has_failures else 'unverified')
        if result['all_passed']:
            known={t['id'] for t in status(project)['tasks']}
            if state['task_id'] not in known:add_task(project,state['task_id'],state['task'])
            set_task(project,state['task_id'],'done',report=report.name)
            state['stage']='completed'
        elif has_failures:
            state['stage']='exhausted' if len(state['attempts'])>=state['max_rounds'] else 'awaiting_repair'
        else:
            state['stage']='unverified'
        _write(project,state)
        return {'run_id':run_id,'round':attempt['round'],'stage':state['stage'],
                'all_passed':result['all_passed'],'report':result['report'],
                'remaining_rounds':state['max_rounds']-len(state['attempts'])}


def repair(project:Path,run_id:str,**provider)->dict:
    project=project.resolve(strict=True)
    with _lock(project,run_id):
        state=_load(project,run_id)
        if state['stage']!='awaiting_repair':raise ValueError('repair requires failing executed test and a remaining round')
        attempt=state['attempts'][-1]
        report_path=project/attempt['report_path']
        if (report_path.is_symlink() or not report_path.is_file() or
                digest(report_path)!=attempt['report_sha256']):
            raise ValueError('failed test evidence changed or missing; cannot request repair')
        evidence=json.loads(report_path.read_text('utf-8'))
        if evidence.get('workflow_change_id')!=attempt['change_id']:
            raise ValueError('failed report is not associated with this change')
        # The repair must be based on exactly the previous change that failed.
        checked=workflow.review(project,attempt['change_id'])
        if checked['status']!='applied' or not checked['all_files_match']:
            raise ValueError('source drift since failed test; cannot continue loop')
        # Only failed categories from earlier rounds inform repeated-failure strategy.
        previous=[category for old in state['attempts'][:-1] if old.get('status')=='failed'
                  for category in old.get('failure_categories',[])]
        # Local preview incorporates prior failed rounds without transmitting new files.
        from tools.repair_context import rank as rank_repair_context
        reports=[]
        for old in state['attempts'][:-1]:
            if old.get('status')!='failed':continue
            path=project/old['report_path']
            if path.is_symlink() or digest(path)!=old['report_sha256']:
                raise ValueError('previous failure evidence changed')
            content=json.loads(path.read_text('utf-8'))
            for check in content.get('checks',[]):
                if isinstance(check,dict) and check.get('status') in ('failed','error','timeout'):
                    reports.append('\n'.join(str(check.get(f,'')) for f in ('stderr_tail','stdout_tail','error'))[-2600:])
        historical_hints=rank_repair_context(project,state['task'],reports[-12:])
        info=_append_proposal(project,state,report_name=report_path.name,
                              prior_failure_categories=previous,**provider)
        info['repair_context_hints']=historical_hints
        _write(project,state)
        return {'run_id':run_id,'round':len(state['attempts']),'stage':state['stage'],**info,
                'next':'Review the repair proposal before separately approving it.'}


def abort(project:Path,run_id:str,*,restore:bool=False,approved:bool=False)->dict:
    project=project.resolve(strict=True)
    with _lock(project,run_id):
        state=_load(project,run_id)
        if state['stage'] in ('applying','testing','recovery_needed'):
            raise ValueError('in-flight operation needs explicit recovery or review before abort')
        if restore and not approved:raise ValueError('--restore requires explicit --approve')
        restored=[]
        if restore:
            # Roll back in reverse order; workflow.restore refuses to overwrite drift.
            for attempt in reversed(state['attempts']):
                change_id=attempt.get('change_id')
                if not change_id:continue
                manifest=workflow.review(project,change_id)
                if manifest['status']=='restored':continue
                try:workflow.restore(project,change_id,approved=True)
                except Exception:
                    state['stage']='rollback_blocked';_write(project,state)
                    raise
                restored.append(change_id)
        state['stage']='aborted';_write(project,state)
        return {'run_id':run_id,'stage':'aborted','restored_changes':restored,
                'note':'No Git checkout, reset, commit, push or deployment performed.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='V3.2: capped, human-gated coding/repair sessions')
    sub=p.add_subparsers(dest='action',required=True)
    for action in ('start','status','resume','approve','test','repair','abort'):
        s=sub.add_parser(action);s.add_argument('--project',required=True)
        if action=='start':
            s.add_argument('--task',required=True);s.add_argument('--task-id',required=True)
            s.add_argument('--include',action='append',default=[])
            s.add_argument('--allow-create-prefix',action='append',default=[])
            s.add_argument('--max-rounds',type=int,default=3)
            s.add_argument('--auto-context',action='store_true',help='local-only source selection; not for live model calls')
            s.add_argument('--auto-limit',type=int,default=6)
        else:s.add_argument('--run-id',required=True)
        if action in ('start','repair'):
            s.add_argument('--response-file',type=Path)
            s.add_argument('--endpoint');s.add_argument('--model')
            s.add_argument('--api-key-env',default='AI_CODING_API_KEY')
            s.add_argument('--send-to-model',action='store_true')
            s.add_argument('--allow-local-http',action='store_true')
        if action in ('approve','abort'):s.add_argument('--approve',action='store_true')
        if action=='approve':s.add_argument('--high-risk-reviewed',action='store_true')
        if action=='test':
            s.add_argument('--trust-project-code',action='store_true')
            s.add_argument('--isolated-image',help='Docker snapshot runner, pinned image digest required')
        if action=='abort':s.add_argument('--restore',action='store_true')
    args=p.parse_args(argv)
    try:
        project=Path(args.project).resolve(strict=True)
        if args.action=='start':
            result=start(project,args.task,args.task_id,args.include,max_rounds=args.max_rounds,
                         allow_create_prefixes=args.allow_create_prefix,
                         auto_context=args.auto_context,auto_limit=args.auto_limit,**_provider_args(
                         response_file=args.response_file,endpoint=args.endpoint,model=args.model,
                         api_key_env=args.api_key_env,send_to_model=args.send_to_model,
                         allow_local_http=args.allow_local_http))
        elif args.action in ('status','resume'):result=inspect(project,args.run_id)
        elif args.action=='approve':result=approve(project,args.run_id,approved=args.approve,
                high_risk_reviewed=args.high_risk_reviewed)
        elif args.action=='test':result=test(project,args.run_id,trust_project_code=args.trust_project_code,isolated_image=args.isolated_image)
        elif args.action=='repair':result=repair(project,args.run_id,**_provider_args(
            response_file=args.response_file,endpoint=args.endpoint,model=args.model,
            api_key_env=args.api_key_env,send_to_model=args.send_to_model,
            allow_local_http=args.allow_local_http))
        else:result=abort(project,args.run_id,restore=args.restore,approved=args.approve)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        p.exit(2,f'error: {e}\n')


if __name__=='__main__':main()
