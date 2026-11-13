"""Bounded, read-only projection of V2-V4 project records for a local dashboard.

Private material (source, diffs, test stdout, credentials, proposals, backup bytes,
manual acceptance notes) is intentionally excluded from the projection.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path

from tools.loop_metrics import summarize as summarize_loops

MAX_JSON_BYTES = 512_000
MAX_TASK_STATE_BYTES = 12_000_000
MAX_TASKS = 300
MAX_REPORTS = 60
MAX_CHANGES = 60
MAX_LOOPS = 400
MAX_DISCOVERY = 10_000


def _text(value, limit=150):
    return value[:limit] if isinstance(value, str) else ''


def _entry_list(directory: Path, *, suffix: str | None = None, limit: int = 1000) -> list[Path]:
    if directory.is_symlink() or not directory.is_dir():
        return []
    entries = []
    # Bounded traversal; concurrently deleted records are skipped rather than
    # turning the entire dashboard into HTTP 503.
    try:
        for n, path in enumerate(directory.iterdir()):
            if n >= limit:
                break
            try:
                if path.is_symlink() or (suffix and path.suffix != suffix):
                    continue
                entries.append(path)
            except OSError:
                continue
    except OSError:
        return []
    return entries


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime if not path.is_symlink() and (path.is_file() or path.is_dir()) else -1
    except OSError:
        return -1


def _read_json(path: Path, *, max_bytes: int = MAX_JSON_BYTES) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError('missing, symlinked or oversized JSON')
    data = json.loads(path.read_text('utf-8'))
    if not isinstance(data, dict):
        raise ValueError('expected JSON object')
    return data


def _evidence_integrity(root: Path, evidence: dict, report_dir: Path) -> str:
    if evidence.get('verification') != 'check_runner':
        return 'manual' if evidence.get('verification') == 'manual_attestation' else 'unknown'
    name = evidence.get('path')
    digest = evidence.get('sha256')
    if not isinstance(name, str) or not isinstance(digest, str) or len(digest) != 64:
        return 'missing_or_invalid'
    if report_dir.is_symlink() or report_dir.parent.is_symlink():
        return 'missing_or_invalid'
    candidate = root / name
    if candidate.parent != report_dir or candidate.is_symlink():
        return 'missing_or_invalid'
    try:
        if candidate.stat().st_size > MAX_JSON_BYTES:
            return 'missing_or_invalid'
        current = hashlib.sha256(candidate.read_bytes()).hexdigest()
        return 'valid' if current == digest else 'modified'
    except (OSError, ValueError):
        return 'missing_or_invalid'


def _tasks(root: Path, ai: Path, warnings: list[str]) -> tuple[list[dict], dict]:
    """Count all valid tasks, but project only the latest bounded subset.

    A V4.1 bug used the first 300 tasks as the denominator for all KPIs.
    Evidence hashes remain deliberately limited to visible rows; coverage is
    declared so an unchecked record cannot silently count as verified.
    """
    path = ai / 'task_state.json'
    empty = {'total': 0, 'by_status': {k: 0 for k in ('todo', 'in_progress', 'blocked', 'done')},
             'visible': 0}
    if not path.exists():
        return [], empty
    try:
        data = _read_json(path, max_bytes=MAX_TASK_STATE_BYTES)
        if not isinstance(data.get('tasks'), list):
            raise ValueError('tasks must be a list')
        all_tasks = [t for t in data['tasks'] if isinstance(t, dict)]
        counts = {k: sum(t.get('status') == k for t in all_tasks)
                  for k in ('todo', 'in_progress', 'blocked', 'done')}
        # ISO timestamps have a lexical ordering for the uniform UTC timestamps
        # produced by the CLI; malformed timestamps sort last, not crash sorting.
        newest = sorted(all_tasks, key=lambda t: _text(t.get('updated_at'), 40), reverse=True)
        if len(newest) > MAX_TASKS:
            warnings.append(f'共 {len(newest)} 项任务，仅展示最近更新的 {MAX_TASKS} 项；' 
                            '任务状态总数按全部有效记录统计，证据告警仅覆盖已展示任务')
        result = []
        for task in newest[:MAX_TASKS]:
            evidences = task.get('evidence', [])
            if not isinstance(evidences, list):
                evidences = []
            types = [_evidence_integrity(root, e, ai / 'reports') for e in evidences[:20] if isinstance(e, dict)]
            result.append({
                'id': _text(task.get('id'), 80), 'title': _text(task.get('title'), 200),
                'status': task.get('status') if task.get('status') in ('todo', 'in_progress', 'blocked', 'done') else 'unknown',
                'skill': _text(task.get('skill_id'), 90), 'updated_at': _text(task.get('updated_at'), 40),
                'evidence_count': len(evidences),
                'evidence_integrity': 'warning' if any(x in ('modified', 'missing_or_invalid') for x in types) else
                                       ('verified' if 'valid' in types else 'manual' if 'manual' in types else 'none'),
            })
        return result, {'total': len(all_tasks), 'by_status': counts, 'visible': len(result)}
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError):
        warnings.append('任务状态文件不可读取、过大或结构无效')
        return [], empty


def _reports(ai: Path, warnings: list[str]) -> list[dict]:
    folder = ai / 'reports'
    paths = _entry_list(folder, suffix='.json', limit=MAX_DISCOVERY)
    paths.sort(key=_mtime, reverse=True)
    if len(paths) >= MAX_DISCOVERY:
        warnings.append('测试报告数量达到扫描上限，最近报告可能不是全局最新')
    if len(paths) > MAX_REPORTS:
        warnings.append('测试报告数量超过展示上限，仅显示最近 60 项')
    result = []
    for path in paths[:MAX_REPORTS]:
        try:
            data = _read_json(path)
            if data.get('schema_version') != 2:
                continue
            checks = data.get('checks')
            if not isinstance(checks, list) or len(checks) > 300:
                continue
            totals = {k: sum(isinstance(c, dict) and c.get('status') == k for c in checks)
                      for k in ('passed', 'failed', 'error', 'timeout', 'disabled', 'planned_only', 'not_run')}
            result.append({'name': _text(path.name, 100), 'timestamp': _text(data.get('timestamp'), 40),
                'executed': data.get('actually_executed') is True, 'checks': len(checks),
                'passed': totals['passed'], 'failed': totals['failed'] + totals['error'] + totals['timeout'],
                'skipped': totals['disabled'] + totals['planned_only'] + totals['not_run'],
                'status': 'unverified' if data.get('actually_executed') is not True else
                          'failed' if totals['failed'] + totals['error'] + totals['timeout'] else
                          'passed' if checks and totals['passed'] == len(checks) else 'unverified'})
        except (OSError, ValueError, json.JSONDecodeError, UnicodeError):
            warnings.append('已跳过损坏或不安全的测试报告')
    return result


def _changes(ai: Path, warnings: list[str]) -> list[dict]:
    paths = _entry_list(ai / 'changes', limit=MAX_DISCOVERY)
    paths = [p for p in paths if p.is_dir()]
    paths.sort(key=_mtime, reverse=True)
    if len(paths) >= MAX_DISCOVERY:
        warnings.append('变更记录数量达到扫描上限，最近变更可能不是全局最新')
    if len(paths) > MAX_CHANGES:
        warnings.append('变更记录数量超过展示上限，仅显示最近 60 项')
    output = []
    for directory in paths[:MAX_CHANGES]:
        try:
            data = _read_json(directory / 'manifest.json')
            if data.get('schema_version') != 3 or data.get('change_id') != directory.name:
                continue
            edits = data.get('files')
            if not isinstance(edits, list):
                continue
            output.append({'id': _text(data.get('change_id'), 100),
                'task_id': _text(data.get('task_id'), 80), 'status': _text(data.get('status'), 40),
                'file_count': len(edits), 'timestamp': _text(data.get('applied_at') or data.get('restored_at'), 40)})
        except (OSError, ValueError, json.JSONDecodeError, UnicodeError):
            warnings.append('已跳过损坏或不安全的代码变更记录')
    return output


def _git(root: Path) -> dict:
    """No shell, network operation or Git hooks. Only metadata/status, no diffs."""
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SYSTEMROOT', 'WINDIR', 'LANG', 'LC_ALL')}
    env.update({'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0', 'GIT_PAGER': 'cat',
                'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
    prefix = ['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=' + os.devnull,
              '-C', str(root)]

    def command(*args):
        proc = subprocess.run([*prefix, *args], capture_output=True, env=env, timeout=5, check=False)
        if len(proc.stdout) > 160_000 or len(proc.stderr) > 160_000:
            raise ValueError('oversize Git status')
        return proc

    try:
        repo = command('rev-parse', '--show-toplevel')
        if repo.returncode != 0 or Path(os.fsdecode(repo.stdout).strip()).resolve() != root:
            return {'available': False, 'note': '当前目录不是独立 Git 仓库根目录'}
        branch = command('symbolic-ref', '--quiet', '--short', 'HEAD')
        sha = command('rev-parse', '--short=12', 'HEAD')
        status = command('status', '--porcelain=v1', '-z', '--untracked-files=normal')
        if status.returncode:
            raise ValueError('Git status failed')
        records = status.stdout.decode('utf-8', 'replace').split('\x00')
        # Rename entries include an extra path in -z; count status lines conservatively.
        files = []
        index = 0
        while index < len(records) and len(files) < 200:
            entry = records[index]
            index += 1
            if not entry or len(entry) < 4:
                continue
            code = entry[:2]
            files.append({'code': _text(code, 2), 'path': _text(entry[3:], 170)})
            if 'R' in code or 'C' in code:
                index += 1
        return {'available': True, 'branch': _text(branch.stdout.decode('utf-8', 'replace').strip(), 100)
                   if branch.returncode == 0 else '(detached HEAD)',
                'head': _text(sha.stdout.decode('utf-8', 'replace').strip(), 14) if sha.returncode == 0 else None,
                'dirty': bool(status.stdout), 'files': files, 'truncated': len(files) >= 200}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {'available': False, 'note': 'Git 信息暂不可读取（未执行任何 Git 写操作）'}


def snapshot(project: Path) -> dict:
    root = project.resolve(strict=True)
    if not root.is_dir() or root == Path(root.anchor):
        raise ValueError('project must be a non-root existing directory')
    ai = root / '.ai'
    if ai.is_symlink():
        raise ValueError('symlink .ai directory forbidden')
    warnings = []
    tasks, task_counts = _tasks(root, ai, warnings)
    reports = _reports(ai, warnings)
    changes = _changes(ai, warnings)
    try:
        loop_dir = ai / 'loops'
        if loop_dir.is_dir():
            # Bound the number of run directories before the legacy summarizer sorts them.
            count = 0
            for count, _ in enumerate(loop_dir.iterdir(), 1):
                if count > MAX_LOOPS:
                    raise ValueError('too many loop journals')
        loops = summarize_loops(root, max_runs=MAX_LOOPS)
        loops = {'available': True, 'runs': loops['runs'], 'completed': loops['completed'], 'exhausted': loops['exhausted'],
                 'total_attempts': loops['total_attempts'], 'completion_rate': loops['completion_rate'],
                 'first_pass_success_rate': loops['first_pass_success_rate'],
                 'mean_attempts': loops['mean_attempts'],
                 'items': [{'run_id': _text(x['run_id'], 90), 'stage': _text(x['stage'], 50),
                            'attempts': x['attempts'], 'passed_attempts': x['passed_attempts'],
                            'failed_attempts': x['failed_attempts']} for x in loops['items'][:50]]}
    except (OSError, ValueError, KeyError, TypeError):
        warnings.append('修复循环记录不可用或超过扫描上限')
        loops = {'available': False, 'runs': 0, 'completed': 0, 'exhausted': 0, 'total_attempts': 0,
                 'completion_rate': None, 'first_pass_success_rate': None, 'mean_attempts': None, 'items': []}
    git = _git(root)
    by_status = task_counts['by_status']
    if not (ai / 'task_state.json').exists():
        warnings.append('尚未初始化项目状态，可通过 CLI 的 project init 命令创建')
    return {'schema_version': 1, 'version': '4.2', 'mode': 'read-only',
        'project': {'name': _text(root.name, 100), 'path': str(root)},
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'coverage': {'tasks_total': task_counts['total'], 'tasks_displayed': task_counts['visible'],
                     'reports_displayed': len(reports), 'report_display_limit': MAX_REPORTS,
                     'changes_displayed': len(changes), 'changes_display_limit': MAX_CHANGES,
                     'evidence_checked_tasks': len(tasks),
                     'note': '报告及变更统计仅针对最近展示的记录；证据哈希仅检查展示的任务'},
        'stats': {'tasks': task_counts['total'], 'by_status': by_status,
                  'reports': len(reports), 'successful_reports': sum(r['status'] == 'passed' for r in reports),
                  'failed_reports': sum(r['status'] == 'failed' for r in reports),
                  'evidence_alerts': sum(t['evidence_integrity'] == 'warning' for t in tasks),
                  'changes': len(changes)},
        'tasks': tasks, 'reports': reports, 'changes': changes, 'loops': loops, 'git': git,
        'warnings': list(dict.fromkeys(warnings)),
        'privacy': '本地只读取元数据；任务总数涵盖全部有效任务，报告、变更及证据统计仅限展示样本；不会返回源码、Git diff、备份、模型提示词、测试输出正文或密钥。'}
