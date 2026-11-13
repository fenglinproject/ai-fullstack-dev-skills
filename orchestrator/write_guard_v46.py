#!/usr/bin/env python3
"""Cooperative, OS-backed serialization for Git worktree writers.

This protects ONLY this toolkit's participating entrypoints. It cannot lock out
an editor, bare `git`, or another application. Repositories must be trusted.
No automatic recovery or lock stealing; OS lock is released on process exit.
"""
from __future__ import annotations

import contextlib
import hmac
import json
import os
import stat
import re
import subprocess
import time
from pathlib import Path

GATE_NAME = 'ai-fullstack-v46-operation.flock'
RESERVATION_NAME = 'ai-fullstack-v45-write.lock'
TOKEN_RE = re.compile(r'[a-f0-9]{64}\Z')


def _run_git(project: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(['git', '-C', str(project), *args],
                                capture_output=True, timeout=4, check=False)
        if not isinstance(result.returncode, int):
            # Some test harnesses patch subprocess; never treat mock output as a repository.
            return None
        if result.returncode != 0:
            stderr = result.stderr
            reason = stderr.decode('utf-8','replace') if isinstance(stderr, bytes) else str(stderr)
            if 'not a git repository' in reason.lower() and args == ('rev-parse', '--show-toplevel'):
                return None
            raise ValueError('cannot verify Git worktree; refusing unguarded write')
        raw = result.stdout
        if not isinstance(raw, (bytes, str)):
            return None
        return raw.decode('utf-8', 'replace').strip() if isinstance(raw, bytes) else raw.strip()
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Git worktree detection timed out; refusing unguarded write') from exc
    except (OSError, TypeError, AttributeError) as exc:
        raise ValueError('Git worktree detection unavailable; refusing unguarded write') from exc


def git_common_dir(project: Path) -> Path | None:
    """Return common Git directory or None for a non-Git project.

    A path inside an existing Git tree but not at its top-level is rejected,
    rather than silently forgoing cross-worktree protection.
    """
    root = project.resolve(strict=True)
    dotgit=root/'.git'
    # A worktree root always has a .git directory or gitdir pointer file.
    # Checking it first avoids mistaking unrelated (e.g. Docker-mocked)
    # subprocess responses for a Git root, and rejects nested subprojects.
    if dotgit.is_symlink():
        raise ValueError('symlinked Git metadata is not supported')
    if not dotgit.exists():
        if any((parent/'.git').exists() or (parent/'.git').is_symlink() for parent in root.parents):
            raise ValueError('Git-managed project must be its worktree root')
        return None
    top = _run_git(root, 'rev-parse', '--show-toplevel')
    if top is None:
        return None
    if Path(top).resolve() != root:
        raise ValueError('Git-managed project must be its worktree root')
    common = _run_git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if common is None:
        raise ValueError('cannot resolve shared Git directory')
    location = Path(common)
    if location.is_symlink() or not location.is_dir():
        raise ValueError('invalid shared Git directory')
    return location.resolve(strict=True)


def _lock(fd: int, timeout: float) -> None:
    if not 0 <= timeout <= 30:
        raise ValueError('lock timeout must be within 0..30 seconds')
    limit = time.monotonic() + timeout
    while True:
        try:
            if os.name == 'nt':
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except (OSError, BlockingIOError) as exc:
            if time.monotonic() >= limit:
                raise ValueError('another worktree operation holds the write gate') from exc
            time.sleep(0.05)


def _unlock(fd: int) -> None:
    if os.name == 'nt':
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


def _reservation_check(common: Path, token: str | None) -> None:
    path = common / RESERVATION_NAME
    if not path.exists() and not path.is_symlink():
        if token is not None:
            raise ValueError('reservation token supplied but no reservation exists')
        return
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4096:
        raise ValueError('unsafe worktree reservation; manual review required')
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('invalid worktree reservation; manual review required') from exc
    recorded = data.get('token') if isinstance(data, dict) else None
    if (not isinstance(data, dict) or data.get('schema_version') != 1 or
            not isinstance(recorded, str) or TOKEN_RE.fullmatch(recorded) is None):
        raise ValueError('invalid worktree reservation; manual review required')
    if not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None or not hmac.compare_digest(recorded, token):
        raise ValueError('worktree write reservation requires its matching token')


@contextlib.contextmanager
def write_guard(project: Path, *, token: str | None = None,
                timeout: float = 5.0, reservation_admin: bool = False):
    """Exclusive Git common-dir gate + optional human reservation check.

    Non-Git projects still use their existing local `_task_lock`. Git projects
    cannot bypass the manual reservation simply by calling workflow.apply.
    """
    common = git_common_dir(Path(project))
    if common is None:
        if token:
            raise ValueError('worktree tokens require a Git repository')
        yield
        return
    gate = common / GATE_NAME
    if gate.is_symlink() or (gate.exists() and not gate.is_file()):
        raise ValueError('unsafe write gate path')
    fd = os.open(gate, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    locked = False
    try:
        stat_info = os.fstat(fd)
        if not stat.S_ISREG(stat_info.st_mode) or stat_info.st_nlink != 1:
            raise ValueError('unsafe write gate file')
        if stat_info.st_size == 0:
            os.write(fd, b'\0')
        _lock(fd, timeout)
        locked = True
        if not reservation_admin:
            _reservation_check(common, token)
        yield
    finally:
        if locked:
            _unlock(fd)
        os.close(fd)


def serialized(function):
    """Opt-in decorator for tool entrypoints; `worktree_token` never forwarded."""
    import functools
    @functools.wraps(function)
    def wrapper(project, *args, worktree_token: str | None = None, **kwargs):
        with write_guard(Path(project), token=worktree_token):
            return function(project, *args, **kwargs)
    return wrapper
