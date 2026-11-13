#!/usr/bin/env python3
"""V4.0 read-only local environment diagnostics: never installs or executes project code."""
from __future__ import annotations
import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _version(binary: str, args: tuple[str, ...]) -> str | None:
    path = shutil.which(binary)
    if not path:
        return None
    try:
        result = subprocess.run([path, *args], capture_output=True, text=True,
                                timeout=3, check=False)
        return (result.stdout or result.stderr).strip().splitlines()[0][:120] if result.returncode == 0 else 'present (version unavailable)'
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return 'present (version unavailable)'


def diagnose(project: Path | None = None) -> dict:
    checks = [
        {'name': 'python', 'status': 'ready' if sys.version_info >= (3, 10) else 'unsupported',
         'detail': platform.python_version(), 'required': True},
        {'name': 'git', 'status': 'ready' if shutil.which('git') else 'missing',
         'detail': _version('git', ('--version',)), 'required': False},
        {'name': 'node', 'status': 'ready' if shutil.which('node') else 'missing',
         'detail': _version('node', ('--version',)), 'required': False},
        {'name': 'typescript', 'status': 'ready' if shutil.which('tsc') else 'missing',
         'detail': _version('tsc', ('--version',)), 'required': False},
        {'name': 'clangd', 'status': 'ready' if shutil.which('clangd') else 'missing',
         'detail': _version('clangd', ('--version',)), 'required': False},
        {'name': 'docker', 'status': 'available-cli' if shutil.which('docker') else 'missing',
         'detail': 'CLI detection only; daemon and sandbox properties are NOT verified', 'required': False},
    ]
    warnings = []
    if project is not None:
        root = project.resolve(strict=True)
        if not root.is_dir() or root == Path('/'):
            raise ValueError('project must be an existing non-root directory')
        checks.append({'name': 'project-path', 'status': 'ready', 'detail': str(root), 'required': True})
        if (root/'.ai').is_symlink():
            checks.append({'name': 'project-state', 'status': 'unsafe', 'detail': 'symlink .ai directory', 'required': True})
        else:
            checks.append({'name': 'project-state',
                           'status': 'ready' if (root/'.ai/task_state.json').is_file() else 'not-initialized',
                           'detail': 'state file exists' if (root/'.ai/task_state.json').is_file() else 'initialize with project init',
                           'required': False})
    if not shutil.which('node') or not shutil.which('tsc'):
        warnings.append('JS/TS AST features need Node.js and a TypeScript compiler.')
    if not shutil.which('clangd'):
        warnings.append('Live C/C++ LSP demonstration needs separately installed trusted clangd.')
    return {'schema_version': 1, 'toolkit_version': '4.0', 'checks': checks, 'warnings': warnings,
            'overall': 'ready' if all(c['status'] == 'ready' for c in checks if c['required']) else 'needs-attention',
            'note': 'Diagnostic only; no package install, network access, model API call or project code execution.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only V4.0 environment diagnostic')
    parser.add_argument('--project',type=Path)
    opts=parser.parse_args(argv)
    try:
        print(json.dumps(diagnose(opts.project),ensure_ascii=False,indent=2))
    except (OSError,ValueError) as exc:
        parser.exit(2,'error: '+str(exc)+'\n')

if __name__=='__main__':main()
