#!/usr/bin/env python3
"""Review-first development workflow (stdlib only).

Agent-generated proposals are untrusted data. This module never invokes an LLM,
executes arbitrary shell snippets, stages/commits files, or deploys. Only explicit
human --approve may apply/restore a validated, hash-pinned text change set.
Tests are opt-in and MUST be run only against trusted source in a separate
trusted development environment; the check runner is not a sandbox.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

from orchestrator.write_guard_v46 import serialized

try:
    from orchestrator.cli import _task_lock, add_task, ai_folder, route, set_task, status
    from tools.run_checks import run as run_checks, save_report
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from orchestrator.cli import _task_lock, add_task, ai_folder, route, set_task, status
    from tools.run_checks import run as run_checks, save_report

MAX_CHANGES=20
MAX_BYTES=256 * 1024
MAX_TOTAL=1024 * 1024
BANNED_SEGMENTS={'.git','.ai','node_modules','.venv','venv','__pycache__','.next','dist','build','.github','skills','policies'}
HIGH_RISK_PATH_TERMS={'auth','authentication','authorization','permission','payment','refund','billing','migration','migrations','secrets','credentials','token','schema'}
BANNED_NAMES={'id_rsa','id_ed25519','credentials.json','secrets.json','authorized_keys'}
IGNORED_SUFFIXES={'.pem','.key','.p12','.pfx','.sqlite','.sqlite3','.db','.zip','.tar','.exe','.dll','.so','.png','.jpg','.pdf','.pyc'}
ID_PATTERN=re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z')


def _hash(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _utc()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_relative(root:Path, value:str, *, allow_missing:bool=False)->Path:
    if not isinstance(value,str) or not value or '\\' in value or '\x00' in value or ':' in value or len(value)>240:
        raise ValueError('invalid project relative file path')
    rel=Path(value)
    parts=rel.parts
    if rel.is_absolute() or not parts or any(x in {'.','..'} for x in parts):
        raise ValueError('absolute or parent traversal path forbidden')
    if any(x in BANNED_SEGMENTS or x.startswith('.env') or x.startswith('.git') for x in parts):
        raise ValueError('protected directory or secret path forbidden')
    if any(p.startswith('.') for p in parts):
        raise ValueError('hidden file paths require separate project-specific review')
    if rel.name.lower() in BANNED_NAMES or rel.suffix.lower() in IGNORED_SUFFIXES:
        raise ValueError('binary, database, or secret file path forbidden')
    base=root.resolve(strict=True)
    candidate=base
    for part in parts:
        candidate=candidate/part
        if candidate.is_symlink():raise ValueError('symlink path forbidden')
    if base not in candidate.resolve(strict=False).parents:
        raise ValueError('path escapes project')
    if not allow_missing and not candidate.is_file():
        raise ValueError('target file does not exist')
    if candidate.exists() and not candidate.is_file():raise ValueError('target is not a regular file')
    return candidate


def _text_bytes(text:str)->bytes:
    if not isinstance(text,str):raise ValueError('change content must be text')
    raw=text.encode('utf-8')
    if len(raw)>MAX_BYTES or '\x00' in text:raise ValueError('text exceeds size limit or contains NUL')
    return raw


def read_existing(path:Path)->tuple[str,bytes]:
    data=path.read_bytes()
    if len(data)>MAX_BYTES or b'\x00' in data:raise ValueError('binary or oversized input')
    try:content=data.decode('utf-8')
    except UnicodeDecodeError as e:raise ValueError('only UTF-8 text modifications are supported') from e
    return content,data


def load_proposal(path:Path)->dict:
    if path.stat().st_size>MAX_TOTAL+120_000:raise ValueError('proposal too large')
    p=json.loads(path.read_text('utf-8'))
    if not isinstance(p,dict) or p.get('schema_version')!=3:
        raise ValueError('proposal schema_version must be 3')
    if not ID_PATTERN.fullmatch(str(p.get('task_id',''))):raise ValueError('invalid task_id')
    if not isinstance(p.get('summary'),str) or not 5<=len(p['summary'])<=500:
        raise ValueError('summary must contain 5..500 characters')
    changes=p.get('changes')
    if not isinstance(changes,list) or not 1<=len(changes)<=MAX_CHANGES:
        raise ValueError('changes list must contain 1..20 entries')
    if len({c.get('path') for c in changes if isinstance(c,dict)})!=len(changes):
        raise ValueError('duplicate target file')
    return p


def preflight(project:Path,proposal:dict)->list[dict]:
    """Resolve *all* operations against pinned source hashes before any write."""
    root=project.resolve(strict=True)
    if not root.is_dir():raise ValueError('project must be an existing directory')
    if not 1 <= len(proposal.get('changes',[])) <= MAX_CHANGES:
        raise ValueError('changes list must contain 1..20 entries')
    total=0;prepared=[];seen=set()
    for op in proposal['changes']:
        if not isinstance(op,dict) or op.get('action') not in {'create','replace'}:
            raise ValueError('only create and replace actions are supported')
        path=safe_relative(root,op.get('path'),allow_missing=True)
        rel=path.relative_to(root).as_posix()
        if rel in seen:raise ValueError('duplicate target file')
        seen.add(rel)
        if op['action']=='create':
            if path.exists():raise ValueError(f'create target exists: {rel}')
            content=_text_bytes(op.get('content'))
            before=None; after=content
        else:
            if not path.is_file():raise ValueError(f'replace target missing: {rel}')
            old,raw=read_existing(path)
            expected=op.get('expected_sha256')
            if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):
                raise ValueError(f'expected_sha256 is required for replace: {rel}')
            if _hash(raw)!=expected:raise ValueError(f'stale original hash: {rel}')
            needle=op.get('old_text');repl=op.get('new_text')
            if not isinstance(needle,str) or not needle or not isinstance(repl,str):
                raise ValueError('replace requires nonempty old_text and string new_text')
            if old.count(needle)!=1:raise ValueError(f'replacement must match exactly once: {rel}')
            after=_text_bytes(old.replace(needle,repl,1))
            if after==raw:raise ValueError(f'no-op replacement: {rel}')
            before=raw
        total+=len(after)+(len(before) if before is not None else 0)
        if total>MAX_TOTAL:raise ValueError('total changed data exceeds 1 MiB')
        before_text='' if before is None else before.decode('utf-8')
        diff=''.join(difflib.unified_diff(before_text.splitlines(keepends=True),
             after.decode('utf-8').splitlines(keepends=True),
             fromfile=('a/'+rel if before is not None else '/dev/null'),
             tofile='b/'+rel))
        prepared.append({'path':path,'relative':rel,'before':before,'after':after,
                         'before_sha256':_hash(before) if before is not None else None,
                         'after_sha256':_hash(after),'diff':diff,'action':op['action']})
    return prepared


def proposal_risk(proposal:dict,edits:list[dict])->dict:
    routed=route(proposal['summary'],limit=2)
    sensitive_paths=[e['relative'] for e in edits
        if any(re.search(r'(?<![a-z])'+re.escape(t)+r'(?![a-z])',e['relative'].casefold()) for t in HIGH_RISK_PATH_TERMS)]
    return {'execution_mode':'strict' if sensitive_paths or routed['execution_mode']=='strict' else routed['execution_mode'],
            'sensitive_paths':sensitive_paths,'routing':routed}

def preview(project:Path, proposal:dict)->dict:
    edits=preflight(project,proposal)
    risk=proposal_risk(proposal,edits)
    return {'task_id':proposal['task_id'],'summary':proposal['summary'],
            'route':risk['routing'],'risk_review':risk, 
            'approved':False,'files':[{'path':e['relative'],'action':e['action'],
            'before_sha256':e['before_sha256'],'after_sha256':e['after_sha256'],
            'diff':e['diff']} for e in edits],
            'warning':'Untrusted proposals require human review; preview runs no code and writes no project source.'}


def _atomic_bytes(path:Path,data:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.ai-edit-',delete=False) as f:
        tmp=Path(f.name)
        try:
            f.write(data);f.flush();os.fsync(f.fileno())
            os.chmod(tmp, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    try:tmp.replace(path)
    finally:tmp.unlink(missing_ok=True)


def _change_root(project:Path)->Path:
    ai=ai_folder(project)
    if not ai.exists() or ai.is_symlink() or ai.resolve()!=project.resolve()/'.ai':
        raise ValueError('initialize project first; .ai must not be symlink')
    dest=ai/'changes'
    if dest.is_symlink():raise ValueError('symlink changes directory forbidden')
    dest.mkdir(parents=True,exist_ok=True)
    return dest


def _git_info(project:Path)->dict:
    """Read-only Git metadata; never stage, commit, checkout or reset."""
    try:
        r=subprocess.run(['git','-C',str(project),'rev-parse','--show-toplevel'],
            capture_output=True,text=True,timeout=3,check=False)
        if r.returncode!=0 or Path(r.stdout.strip()).resolve()!=project.resolve():
            return {'available':False,'note':'Project is not its own Git repository root'}
        h=subprocess.run(['git','-C',str(project),'rev-parse','HEAD'],
            capture_output=True,text=True,timeout=3,check=False)
        s=subprocess.run(['git','-C',str(project),'status','--porcelain','--untracked-files=normal'],
            capture_output=True,text=True,timeout=3,check=False)
        return {'available':True,'head':h.stdout.strip() if h.returncode==0 else None,
                'status_before':s.stdout.splitlines()[:100] if s.returncode==0 else []}
    except (OSError,subprocess.TimeoutExpired):return {'available':False}


def _json_write(path:Path,record:dict)->None:
    _atomic_bytes(path,(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))


@serialized
def apply(project:Path,proposal:dict,*,approved:bool=False,high_risk_reviewed:bool=False,operation_id:str|None=None)->dict:
    if not approved:raise ValueError('explicit --approve required to modify project source')
    if operation_id is not None and not ID_PATTERN.fullmatch(operation_id):
        raise ValueError('invalid workflow operation_id')
    project=project.resolve(strict=True)
    with _task_lock(project):
        edits=preflight(project,proposal)
        risk=proposal_risk(proposal,edits)
        if risk['execution_mode']=='strict' and not high_risk_reviewed:
            raise ValueError('strict-risk change requires --high-risk-reviewed in addition to --approve')
        container=_change_root(project)
        change_id=uuid.uuid4().hex
        directory=container/change_id
        directory.mkdir(mode=0o700)
        manifest={'schema_version':3,'change_id':change_id,'task_id':proposal['task_id'],
                  'summary':proposal['summary'],'operation_id':operation_id,'created_at':_utc(),'status':'prepared',
                  'git':_git_info(project),'risk_review':{'execution_mode':risk['execution_mode'],
                  'sensitive_paths':risk['sensitive_paths'],'high_risk_reviewed':bool(high_risk_reviewed)},'files':[]}
        for e in edits:
            manifest['files'].append({'path':e['relative'],'action':e['action'],
                'before_sha256':e['before_sha256'],'after_sha256':e['after_sha256'],
                'backup_base64':base64.b64encode(e['before']).decode('ascii') if e['before'] is not None else None,
                'diff':e['diff']})
        record=directory/'manifest.json'
        _json_write(record,manifest)  # persist backups before first source write
        written=[]
        try:
            for e in edits:
                # Revalidate after staging; guard against unrelated concurrent edits.
                path=safe_relative(project,e['relative'],allow_missing=True)
                if e['action']=='replace':
                    if not path.is_file() or _hash(path.read_bytes())!=e['before_sha256']:
                        raise ValueError(f'target changed while applying: {e["relative"]}')
                elif path.exists():raise ValueError(f'create target appeared: {e["relative"]}')
                _atomic_bytes(path,e['after']);written.append(e)
        except BaseException:
            for e in reversed(written):
                if e['action']=='create':e['path'].unlink(missing_ok=True)
                else:_atomic_bytes(e['path'],e['before'])
            manifest['status']='aborted'
            _json_write(record,manifest)
            raise
        manifest['status']='applied';manifest['applied_at']=_utc()
        _json_write(record,manifest)
        return {'change_id':change_id,'task_id':proposal['task_id'],'status':'applied',
                'manifest':str(record.relative_to(project)),'files':[e['relative'] for e in edits],
                'git':manifest['git'],'note':'Applied locally; NOT committed, deployed or tested.'}


def _load_change(project:Path,change_id:str)->tuple[Path,dict]:
    if not ID_PATTERN.fullmatch(change_id):raise ValueError('invalid change identifier')
    path=_change_root(project)/change_id/'manifest.json'
    if path.is_symlink() or not path.is_file():raise ValueError('unknown or unsafe change id')
    record=json.loads(path.read_text('utf-8'))
    if record.get('schema_version')!=3 or record.get('change_id')!=change_id:
        raise ValueError('invalid manifest')
    return path,record


def _drift(project:Path,manifest:dict)->list[dict]:
    files=[]
    for e in manifest['files']:
        path=safe_relative(project,e['path'],allow_missing=True)
        current=_hash(path.read_bytes()) if path.exists() else None
        files.append({'path':e['path'],'expected_sha256':e['after_sha256'],
                      'actual_sha256':current,'unchanged_since_apply':current==e['after_sha256']})
    return files


def review(project:Path,change_id:str)->dict:
    path,manifest=_load_change(project.resolve(strict=True),change_id)
    drift=_drift(project,manifest)
    return {'change_id':change_id,'task_id':manifest['task_id'],'status':manifest['status'],
            'files':drift,'all_files_match':all(x['unchanged_since_apply'] for x in drift),
            'diffs':{e['path']:e['diff'] for e in manifest['files']},
            'git':_git_info(project.resolve(strict=True)),
            'note':'Git data are read-only. Review the diff; no staging or commit was performed.'}


@serialized
def restore(project:Path,change_id:str,*,approved:bool=False)->dict:
    if not approved:raise ValueError('explicit --approve required for restore')
    project=project.resolve(strict=True)
    with _task_lock(project):
        path,manifest=_load_change(project,change_id)
        if manifest['status']!='applied':raise ValueError('only applied changes can be restored')
        drift=_drift(project,manifest)
        if not all(x['unchanged_since_apply'] for x in drift):
            raise ValueError('source changed since apply; refusing to overwrite newer edits')
        backups={}
        for op in manifest['files']:
            if op['action']=='replace':
                try:original=base64.b64decode(op['backup_base64'],validate=True)
                except (ValueError,TypeError) as exc:raise ValueError('invalid saved backup') from exc
                if _hash(original)!=op['before_sha256']:raise ValueError('backup hash mismatch')
                backups[op['path']]=original
        for op in reversed(manifest['files']):
            file=safe_relative(project,op['path'],allow_missing=True)
            if op['action']=='create':file.unlink()
            else:_atomic_bytes(file,backups[op['path']])
        manifest['status']='restored';manifest['restored_at']=_utc()
        _json_write(path,manifest)
        # A formerly verified change should no longer be advertised as completed.
        state=ai_folder(project)/'task_state.json'
        if state.is_file():
            data=json.loads(state.read_text('utf-8'))
            for task in data.get('tasks',[]):
                if task.get('id')==manifest['task_id'] and task.get('status')=='done':
                    task['status']='blocked';task['updated_at']=_utc()
            _json_write(state,data)
        return {'change_id':change_id,'status':'restored','files':[x['path'] for x in drift],
                'note':'Restored the recorded text files; unrelated working-tree changes were untouched.'}


@serialized
def verify(project:Path,change_id:str,*,execute:bool=False,close_task:bool=False,isolated_image:str|None=None)->dict:
    project=project.resolve(strict=True)
    if close_task and not execute:raise ValueError('--close-task requires --run')
    path,manifest=_load_change(project,change_id)
    if manifest['status']!='applied' or not all(x['unchanged_since_apply'] for x in _drift(project,manifest)):
        raise ValueError('change no longer matches applied source; review or restore first')
    before=_drift(project,manifest)
    verification_head=_git_info(project).get("head")
    if isolated_image:
        try:
            from tools.isolated_checks import run as run_isolated
        except ModuleNotFoundError:
            from tools.isolated_checks import run as run_isolated
        checks=run_isolated(project,isolated_image,execute=execute)
    else:
        checks=run_checks(project,execute=execute)
    after=_drift(project,manifest)
    if _git_info(project).get("head") != verification_head:
        raise ValueError("Git HEAD changed during verification; tests must be rerun")
    if before!=after or not all(x['unchanged_since_apply'] for x in after):
        raise ValueError('source changed during tests; verification rejected')
    checks['workflow_change_id']=change_id
    report=save_report(project,checks)
    all_passed=(execute and bool(checks.get('checks')) and
                all(x.get('status')=='passed' for x in checks['checks']))
    # A last-execution pointer (including failures) makes stale success evidence
    # ineligible for a later Git commit. It is not a cryptographic signature:
    # a user with write access to .ai can change the local records.
    with _task_lock(project):
        path,latest=_load_change(project,change_id)
        if latest['status']!='applied' or not all(x['unchanged_since_apply'] for x in _drift(project,latest)):
            raise ValueError('change was restored or modified while running checks')
        report_path=Path(report)
        if report_path.is_symlink():raise ValueError('test report became unsafe')
        latest['last_verification']={
            'report':report_path.name,
            'sha256':_hash(report_path.read_bytes()),
            'executed':bool(execute), 'passed':bool(all_passed),
            'source_hashes':{e['path']:e['after_sha256'] for e in latest['files']},
            'git_head':_git_info(project).get('head'),
            'verified_at':_utc(),
        }
        _json_write(path,latest)
    result={'change_id':change_id,'report':str(Path(report).relative_to(project)),
            'all_passed':all_passed,'summary':checks['summary'],'executed':execute}
    if close_task:
        if not all_passed:raise ValueError(f'checks did not all pass; saved report at {report}')
        task_id=latest['task_id']
        known={t['id'] for t in status(project)['tasks']}
        if task_id not in known:add_task(project,task_id,latest['summary'])
        result['task']=set_task(project,task_id,'done',report=Path(report).name)
    return result



def handoff(project:Path,task:str)->dict:
    """Portable contract for an external coding agent, not an agent invocation."""
    project=project.resolve(strict=True)
    result=route(task)
    return {'schema_version':3,'task':task,'project':str(project),
            'selected_skills':[{'id':s['id'],'relative_path':s['path']} for s in result['selected']],
            'required_policies':result['rules'],
            'agent_instructions':['Inspect source and user requirements before editing.',
                'Return a JSON proposal following docs/agent_proposal.schema.json.',
                'Use SHA-256 of the current UTF-8 file as expected_sha256.',
                'Use unique old_text fragments for replacements; no code execution in proposals.',
                'Do not stage, commit, deploy, or run tests without separate user authorization.'],
            'execution_mode':result['execution_mode'],
            'note':'An external coding agent must generate the proposal; this command does not invoke AI.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='V3 human-approved code change workflow; local text files only')
    sub=parser.add_subparsers(dest='action',required=True)
    for cmd in ('preview','apply','review','restore','verify','handoff'):
        p=sub.add_parser(cmd);p.add_argument('--project',required=True)
        if cmd in ('preview','apply'):p.add_argument('--proposal',required=True)
        if cmd in ('review','restore','verify'):p.add_argument('--change-id',required=True)
        if cmd in ('apply','restore'):p.add_argument('--approve',action='store_true')
        if cmd=='apply':p.add_argument('--high-risk-reviewed',action='store_true',help='extra attestation for authentication, payments, schemas, deployments or sensitive paths')
        if cmd=='verify':
            p.add_argument('--run',action='store_true',help='execute trusted tests (NOT sandboxed)')
            p.add_argument('--close-task',action='store_true',help='close task only after passed executed tests')
            p.add_argument('--isolated-image',help='use Docker snapshot runner with pinned image digest (explicit --run still required)')
        if cmd in ('apply','restore','verify'):p.add_argument('--worktree-token',help='required if human worktree reservation exists')
        if cmd=='handoff':p.add_argument('--task',required=True)
    args=parser.parse_args(argv)
    try:
        project=Path(args.project).resolve(strict=True)
        if args.action in ('preview','apply'):
            proposal=load_proposal(Path(args.proposal))
            result=preview(project,proposal) if args.action=='preview' else apply(project,proposal,approved=args.approve,high_risk_reviewed=args.high_risk_reviewed,worktree_token=args.worktree_token)
        elif args.action=='review':result=review(project,args.change_id)
        elif args.action=='restore':result=restore(project,args.change_id,approved=args.approve,worktree_token=args.worktree_token)
        elif args.action=='verify':result=verify(project,args.change_id,execute=args.run,close_task=args.close_task,isolated_image=args.isolated_image,worktree_token=args.worktree_token)
        else:result=handoff(project,args.task)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,UnicodeDecodeError,json.JSONDecodeError) as e:
        parser.exit(2,f'error: {e}\n')

if __name__=='__main__':main()
