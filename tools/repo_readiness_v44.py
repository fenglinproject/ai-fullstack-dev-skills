#!/usr/bin/env python3
"""V4.4 read-only intake, concurrent change hazards and CI receipt review.

Designed for EXISTING, trusted local Git repositories, not a network clone.
Never starts project processes, writes source, initializes state or calls APIs.
Local CI JSON is unsigned user-provided data, NOT authenticated CI provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from orchestrator.git_review import git
from tools.repo_health_v43 import audit, _bounded_entries, _json

SHA = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
SAFE_NAME = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9._/-]{0,159}\Z')
MAX_RECEIPT = 128_000
MAX_MANIFESTS = 1000
MAX_PATHS = 4000


def _git_text(root: Path, *args: str, limit: int = 50_000) -> str:
    result = git(root, *args, max_bytes=limit)
    if result.returncode:
        raise ValueError('could not inspect Git repository')
    return result.stdout.decode('utf-8', 'replace').strip()


def repository_root(project: Path) -> Path:
    root = Path(project).resolve(strict=True)
    if not root.is_dir() or root == Path('/'):
        raise ValueError('invalid Git project root')
    raw = _git_text(root, 'rev-parse', '--show-toplevel')
    if Path(raw).resolve() != root:
        raise ValueError('project must be the Git worktree root (no parent repository)')
    return root


def _safe_path(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 240 or '\\' in value or '\x00' in value:
        raise ValueError('invalid candidate path')
    p = PurePosixPath(value)
    if (p.is_absolute() or not p.parts or any(x in ('.', '..', '.git', '.ai') for x in p.parts)
            or ':' in value or any(part.casefold() in ('.git','.ai') for part in p.parts)
            or any(ord(c) < 32 for c in value) or value.startswith('-')):
        raise ValueError('unsafe candidate path')
    return str(p)


def inspect(project: Path, *, expected_head: str | None = None) -> dict:
    root = repository_root(project)
    if expected_head is not None and not SHA.fullmatch(expected_head):
        raise ValueError('expected HEAD must be a full commit hash')
    head = _git_text(root, 'rev-parse', 'HEAD')
    branch = _git_text(root, 'branch', '--show-current')
    status = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal', '--', '.', ':(exclude).ai', max_bytes=180_000)
    if status.returncode:
        raise ValueError('unable to inspect working tree')
    dirty = sum(bool(x) for x in status.stdout.split(b'\0'))
    # Never read executable project scripts or return their contents.
    signals = []
    for filename, label in (
        ('package.json','node'), ('pnpm-workspace.yaml','pnpm-workspace'),
        ('pyproject.toml','python'), ('requirements.txt','python'),
        ('go.mod','go'), ('Cargo.toml','rust'), ('pom.xml','maven'),
        ('build.gradle','gradle'), ('tsconfig.json','typescript'),
        ('Dockerfile','container'), ('.github/workflows','github-actions'),
        ('.gitlab-ci.yml','gitlab-ci'), ('Jenkinsfile','jenkins'),
    ):
        f = root/filename
        if f.exists() and not f.is_symlink():
            signals.append(label)
    ai = root/'.ai'
    if ai.is_symlink():
        raise ValueError('unsafe .ai symlink')
    return {
        'schema_version': 1, 'git': {'head':head, 'branch':branch,
        'dirty_entries':dirty,'head_matches_pin':expected_head is None or head == expected_head},
        'detected_stacks': sorted(set(signals)), 'ai_initialized':ai.is_dir(),
        'note':'Read-only local Git inspection; no source code, secrets or scripts are returned or executed.',
    }


def conflicts(project: Path, *, candidate_paths: list[str] | None = None,
              max_records: int = MAX_MANIFESTS) -> dict:
    root = repository_root(project)
    if not 1 <= max_records <= MAX_MANIFESTS:
        raise ValueError('invalid record limit')
    candidates = []
    for candidate in candidate_paths or []:
        rel = _safe_path(candidate)
        path = root
        for component in PurePosixPath(rel).parts:
            path = path/component
            if path.is_symlink():
                raise ValueError('symlink in candidate path')
        candidates.append(rel)
    ai = root/'.ai'
    if ai.is_symlink():
        raise ValueError('unsafe .ai symlink')
    records = _bounded_entries(ai/'changes',max_records)
    active = []
    blockers = []
    by_path: dict[str,list[dict]] = {}
    seen_files = 0
    for directory in records:
        if directory.is_symlink() or not directory.is_dir():
            blockers.append('unsafe change record');continue
        try:
            data = _json(directory/'manifest.json',1_600_000)
            if data.get('schema_version') != 3 or data.get('change_id') != directory.name:
                raise ValueError('invalid change identity')
            if data.get('status') not in ('applied', 'prepared'):
                continue
            task_id = data.get('task_id')
            if not isinstance(task_id,str) or len(task_id)>160:
                raise ValueError('invalid task id')
            files = data.get('files')
            if not isinstance(files,list) or not 1<=len(files)<=20:
                raise ValueError('invalid manifest files')
            paths = []
            for file in files:
                if not isinstance(file,dict):raise ValueError('bad path record')
                rel = _safe_path(file.get('path'))
                paths.append(rel)
                seen_files += 1
                if seen_files > MAX_PATHS:raise ValueError('path scan limit exceeded')
            item = {'change_id':directory.name,'task_id':task_id,'status':data['status'],'paths':paths}
            active.append(item)
            for path in paths:
                by_path.setdefault(path.casefold(),[]).append(item)
            if data['status']=='prepared':
                blockers.append('interrupted prepared change needs review')
        except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
            blockers.append('invalid or excessive active change records')
    overlaps = []
    for path, group in sorted(by_path.items()):
        if len({x['change_id'] for x in group})>1:
            overlaps.append({'path':path,'change_ids':sorted({x['change_id'] for x in group})})
    candidate_hits = []
    for path in candidates:
        matches=by_path.get(path.casefold(),[])
        if matches:
            candidate_hits.append({'path':path, 'change_ids':sorted({x['change_id'] for x in matches})})
    if overlaps: blockers.append('overlapping active changes')
    if candidate_hits: blockers.append('candidate conflicts with active changes')
    return {'schema_version':1,'active_change_count':len(active),
            'overlaps':overlaps,'candidate_conflicts':candidate_hits,
            'prepared_count':sum(x['status']=='prepared' for x in active),
            'blockers':sorted(set(blockers)),
            'note':'Advisory local snapshot only; not a lock, merge engine or concurrency-safe reservation.'}


def review_ci_receipt(receipt: Path, *, expected_head: str, required_checks: list[str] | None = None) -> dict:
    """Review a normalized offline CI JSON receipt. No claims of authenticity."""
    if not SHA.fullmatch(expected_head):
        raise ValueError('expected_head must be a full Git commit SHA')
    required = required_checks or []
    if len(required)>32 or any(not isinstance(c,str) or not SAFE_NAME.fullmatch(c) for c in required):
        raise ValueError('invalid required CI checks')
    receipt=Path(receipt)
    if receipt.is_symlink() or not receipt.is_file() or not 0<receipt.stat().st_size<=MAX_RECEIPT:
        raise ValueError('unsafe or oversized CI receipt')
    raw=receipt.read_bytes()
    data=json.loads(raw)
    if not isinstance(data,dict) or data.get('schema_version')!=1:
        raise ValueError('unsupported CI receipt schema')
    if data.get('provider') not in ('github-actions','gitlab-ci','local-ci'):
        raise ValueError('unsupported CI provider')
    if not isinstance(data.get('run_id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,96}',data['run_id']):
        raise ValueError('invalid run id')
    sha=data.get('commit')
    if not isinstance(sha,str) or not SHA.fullmatch(sha):
        raise ValueError('invalid CI commit SHA')
    records=data.get('checks')
    if not isinstance(records,list) or not 1<=len(records)<=100:
        raise ValueError('missing or excessive CI checks')
    seen=set(); passed=[]; failed=[]
    for entry in records:
        if not isinstance(entry,dict) or not isinstance(entry.get('name'),str) or not SAFE_NAME.fullmatch(entry['name']):
            raise ValueError('invalid check entry')
        name=entry['name']
        if name in seen:raise ValueError('duplicate CI check names')
        seen.add(name)
        if entry.get('status') not in ('completed','queued','in_progress'):
            raise ValueError('invalid CI status')
        if entry.get('conclusion') not in ('success','failure','cancelled','skipped','timed_out',None):
            raise ValueError('invalid CI conclusion')
        if entry['status']=='completed' and entry['conclusion']=='success':passed.append(name)
        else:failed.append(name)
    missing=sorted(set(required)-set(passed))
    matched=sha==expected_head
    accepted=matched and not failed and not missing
    return {'schema_version':1,'provider':data['provider'],'run_id':data['run_id'],
            'commit_matches_pin':matched,'passed_checks':sorted(passed),
            'nonpassing_checks':sorted(failed),'missing_required_checks':missing,
            'eligible_as_unverified_ci_signal':accepted,
            'receipt_sha256':hashlib.sha256(raw).hexdigest(),
            'source_trust':'unsigned-local-JSON',
            'note':'Untrusted local CI claim only; cannot approve Git commit, deployment or task completion.'}


def readiness(project: Path, *, expected_head: str | None = None,
              require_clean:bool = False, candidate_paths:list[str] | None = None,
              ci_receipt:Path | None = None, require_ci:bool=False,
              required_checks:list[str] | None = None) -> dict:
    if required_checks and ci_receipt is None:
        raise ValueError('required CI checks require --ci-receipt')
    if require_ci and ci_receipt is None:
        # Refuse to signal readiness if configured mandatory CI is absent.
        missing_ci=True
    else:missing_ci=False
    info=inspect(project,expected_head=expected_head)
    hazards=conflicts(project,candidate_paths=candidate_paths)
    failures=list(hazards['blockers'])
    warnings=[]
    if not info['git']['head_matches_pin']:failures.append('repository HEAD differs from pinned baseline')
    if require_clean and info['git']['dirty_entries']:failures.append('working tree is dirty')
    if not info['ai_initialized']:
        warnings.append('project state not initialized; use project init only after review')
        health=None
    else:
        health=audit(Path(project),expected_head=expected_head or info['git']['head'],require_clean=require_clean)
        failures.extend(health['errors'])
        warnings.extend(health['warnings'])
    ci=None
    if missing_ci:failures.append('required offline CI receipt missing')
    elif ci_receipt is not None:
        ci=review_ci_receipt(ci_receipt,expected_head=info['git']['head'],required_checks=required_checks)
        if not ci['eligible_as_unverified_ci_signal']:
            failures.append('CI receipt does not match HEAD or all checks passing')
        warnings.append('CI receipt is unsigned local data; verify provider origin separately')
    if not failures and not info['ai_initialized']:
        status='needs_initialization'
    else:
        status='blocked' if failures else 'reviewable'
    return {'schema_version':1,'status':status,'git':info['git'],
            'detected_stacks':info['detected_stacks'],
            'ai_initialized':info['ai_initialized'],
            'change_conflicts':hazards,'audit_summary':{
                'healthy':health['healthy'],'counts':health['counts']} if health else None,
            'ci':ci,'blockers':sorted(set(failures)),'warnings':sorted(set(warnings)),
            'note':'Read-only preflight, not production safety, remote CI attestation or permission to modify code.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='V4.4 read-only repository onboarding and readiness')
    p.add_argument('action',choices=('inspect','conflicts','ci','readiness'))
    p.add_argument('--project',type=Path)
    p.add_argument('--candidate',action='append',default=[])
    p.add_argument('--expected-head')
    p.add_argument('--require-clean',action='store_true')
    p.add_argument('--ci-receipt',type=Path)
    p.add_argument('--required-check',action='append',default=[])
    p.add_argument('--require-ci',action='store_true')
    a=p.parse_args(argv)
    try:
        if a.action in ('inspect','conflicts','readiness') and a.project is None:
            raise ValueError('--project required')
        if a.action=='inspect':r=inspect(a.project,expected_head=a.expected_head)
        elif a.action=='conflicts':r=conflicts(a.project,candidate_paths=a.candidate)
        elif a.action=='ci':
            if a.ci_receipt is None or a.expected_head is None:raise ValueError('CI requires --ci-receipt and --expected-head')
            r=review_ci_receipt(a.ci_receipt,expected_head=a.expected_head,required_checks=a.required_check)
        else:r=readiness(a.project,expected_head=a.expected_head,require_clean=a.require_clean,
            candidate_paths=a.candidate,ci_receipt=a.ci_receipt,require_ci=a.require_ci,
            required_checks=a.required_check)
        print(json.dumps(r,ensure_ascii=False,indent=2))
        return 1 if a.action=='readiness' and r['status']=='blocked' else 0
    except (OSError,ValueError,subprocess.TimeoutExpired,TypeError,json.JSONDecodeError) as e:
        p.exit(2,'error: '+str(e)+'\n')

if __name__=='__main__':raise SystemExit(main())
