#!/usr/bin/env python3
"""V4.3 bounded, source-free, read-only health audit of a LOCAL Git project.

No project source is read; JSON manifests and report hashes are checked.
Git commands use fixed read-only arguments. This is not a security attestation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from orchestrator.git_review import git
from orchestrator.workflow import _drift

MAX_RECORDS=1000
MAX_TASK_STATE_BYTES=12_000_000
MAX_MANIFEST_BYTES=1_600_000
MAX_REPORT_BYTES=500_000
HEX=re.compile(r'[a-f0-9]{64}\Z')


def _json(path:Path, max_bytes:int)->dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size>max_bytes:
        raise ValueError('missing, symlinked or oversized JSON')
    doc=json.loads(path.read_text('utf-8'))
    if not isinstance(doc,dict):raise ValueError('JSON object expected')
    return doc


def _bounded_entries(folder:Path, limit:int=MAX_RECORDS)->list[Path]:
    if folder.is_symlink():raise ValueError('symlinked data directory')
    if not folder.exists():return []
    if not folder.is_dir():raise ValueError('data directory is not a directory')
    entries=[]
    for entry in folder.iterdir():
        if len(entries)>=limit:raise ValueError('record count exceeds audit limit')
        entries.append(entry)
    return entries


def _report(root:Path,name:str,expected:str|None=None)->bool:
    if not isinstance(name,str) or not re.fullmatch(r'checks-[0-9a-f]{32}\.json',name):return False
    folder=root/'.ai/reports'
    if folder.is_symlink():return False
    path=folder/name
    try:
        raw=path.read_bytes() if not path.is_symlink() and 0<path.stat().st_size<=MAX_REPORT_BYTES else b''
        if not raw:return False
        if expected and hashlib.sha256(raw).hexdigest()!=expected:return False
        doc=json.loads(raw)
        return isinstance(doc,dict) and doc.get('actually_executed') is True and bool(doc.get('checks')) and all(
            isinstance(c,dict) and c.get('status')=='passed' for c in doc['checks'])
    except (OSError,ValueError,json.JSONDecodeError,TypeError):return False


def audit(project:Path,*,expected_head:str|None=None,require_clean:bool=False,max_records:int=MAX_RECORDS)->dict:
    root=project.resolve(strict=True)
    if not root.is_dir() or root==Path('/') or not 1<=max_records<=MAX_RECORDS:
        raise ValueError('invalid project or record limit')
    if expected_head and not re.fullmatch(r'[a-f0-9]{40,64}',expected_head):
        raise ValueError('expected_head must be a full Git commit SHA')
    errors=[];warnings=[];counts={'tasks':0,'done':0,'reports':0,'changes':0,'prepared':0,
                                   'applied':0,'committed':0,'restored':0,'verified_changes':0}
    r=git(root,'rev-parse','--show-toplevel')
    if r.returncode or Path(os.fsdecode(r.stdout).strip()).resolve()!=root:
        raise ValueError('project must be its own Git repository root')
    h=git(root,'rev-parse','HEAD')
    if h.returncode:raise ValueError('repository must have a HEAD commit')
    head=h.stdout.decode('ascii','replace').strip()
    branch=git(root,'branch','--show-current').stdout.decode('utf-8','replace').strip()
    state=git(root,'status','--porcelain=v1','-z','--untracked-files=all','--','.',':(exclude).ai')
    if state.returncode:raise ValueError('cannot inspect Git status')
    dirty_count=sum(1 for s in state.stdout.split(b'\x00') if s and len(s)>3)
    if expected_head and head!=expected_head:errors.append('HEAD differs from pinned baseline')
    if require_clean and dirty_count:errors.append('working tree not clean')
    ai=root/'.ai'
    if ai.is_symlink():raise ValueError('symlinked .ai directory')
    if not ai.is_dir():warnings.append('project state not initialized')
    else:
        task_path=ai/'task_state.json'
        if task_path.exists():
            try:
                data=_json(task_path,MAX_TASK_STATE_BYTES)
                tasks=data.get('tasks')
                if not isinstance(tasks,list):raise ValueError('invalid tasks')
                counts['tasks']=len(tasks)
                for t in tasks:
                    if not isinstance(t,dict):raise ValueError('invalid task')
                    if t.get('status')=='done':
                        counts['done']+=1
                        evidences=t.get('evidence',[])
                        if not isinstance(evidences,list) or not evidences:
                            errors.append('completed task lacks acceptance evidence');continue
                        for ev in evidences:
                            if not isinstance(ev,dict):errors.append('malformed task evidence');continue
                            if ev.get('verification')!='check_runner':continue
                            raw_path=ev.get('path')
                            name=Path(str(raw_path)).name
                            digest=ev.get('sha256')
                            if raw_path!='.ai/reports/'+name:
                                errors.append('task evidence has unexpected report path');continue
                            if not isinstance(digest,str) or not HEX.fullmatch(digest) or not _report(root,name,digest):
                                errors.append('missing, altered or non-passing task evidence')
            except (OSError,ValueError,json.JSONDecodeError,UnicodeError):errors.append('unreadable task state')
        try:
            entries=_bounded_entries(ai/'reports',max_records)
            counts['reports']=len(entries)
            if any(e.is_symlink() for e in entries):errors.append('symlink in report directory')
        except (OSError,ValueError):errors.append('unsafe or excessive reports')
        try:changes=_bounded_entries(ai/'changes',max_records)
        except (OSError,ValueError):
            errors.append('unsafe or excessive change records');changes=[]
        counts['changes']=len(changes)
        for directory in changes:
            try:
                if directory.is_symlink() or not directory.is_dir():raise ValueError('unsafe change folder')
                record=_json(directory/'manifest.json',MAX_MANIFEST_BYTES)
                if record.get('schema_version')!=3 or record.get('change_id')!=directory.name:
                    raise ValueError('bad manifest identity')
                phase=record.get('status')
                if phase=='prepared':
                    counts['prepared']+=1;warnings.append('interrupted prepared change needs manual review')
                elif phase=='applied':
                    counts['applied']+=1
                    if not all(x['unchanged_since_apply'] for x in _drift(root,record)):
                        errors.append('applied source no longer matches recorded hashes')
                elif phase=='committed':
                    counts['committed']+=1
                    commit_sha=record.get('git_commit')
                    if not isinstance(commit_sha,str) or not re.fullmatch(r'[a-f0-9]{40,64}',commit_sha):
                        errors.append('committed change lacks valid Git commit')
                    else:
                        # Compare content at its historical commit, not live HEAD.
                        for changed in record['files']:
                            rel=changed['path']
                            if not isinstance(rel,str) or ':' in rel or rel.startswith('-') or '..' in Path(rel).parts:
                                errors.append('invalid committed path');continue
                            obj=git(root,'show',f'{commit_sha}:{rel}',max_bytes=280_000)
                            if obj.returncode or hashlib.sha256(obj.stdout).hexdigest()!=changed['after_sha256']:
                                errors.append('Git commit snapshot does not match recorded source')
                elif phase=='restored':counts['restored']+=1
                elif phase=='aborted':pass
                else:errors.append('unexpected change record status')
                tx=record.get('commit_transaction')
                if isinstance(tx,dict) and tx.get('state')=='prepared':
                    warnings.append('pending Git commit transaction requires recovery review')
                v=record.get('last_verification')
                if v is not None:
                    if not isinstance(v,dict):errors.append('invalid verification pointer')
                    elif v.get('passed') is True and v.get('executed') is True:
                        counts['verified_changes']+=1
                        if not _report(root,v.get('report'),v.get('sha256')):
                            errors.append('change verification report altered or missing')
                        if v.get('source_hashes')!={f['path']:f['after_sha256'] for f in record['files']}:
                            errors.append('verified file hashes inconsistent with manifest')
            except (OSError,ValueError,KeyError,TypeError,UnicodeError,json.JSONDecodeError):
                errors.append('malformed or unsafe change record')
    return {'schema_version':1,'project':str(root),'git':{'head':head,'branch':branch,'dirty_entries':dirty_count},
            'counts':counts,'healthy':not errors,'errors':sorted(set(errors)),
            'warnings':sorted(set(warnings)),
            'note':'Read-only LOCAL audit. No source/test logs or proposal bodies returned; Git filters/attributes can still be untrusted.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only Git/project integrity audit; does NOT execute tests')
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--expected-head')
    parser.add_argument('--require-clean',action='store_true')
    parser.add_argument('--max-records',type=int,default=MAX_RECORDS)
    args=parser.parse_args(argv)
    try:
        result=audit(args.project,expected_head=args.expected_head,
                     require_clean=args.require_clean,max_records=args.max_records)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['healthy'] else 1
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        parser.exit(2,'error: '+str(exc)+'\n')

if __name__=='__main__':raise SystemExit(main())
