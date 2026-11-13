#!/usr/bin/env python3
"""Read-only, bounded static npm/pnpm/yarn workspace discovery.

Parses package.json and a conservative static subset of pnpm-workspace.yaml.
Never executes package scripts, package managers, plugins, or arbitrary YAML tags.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path

MAX_MANIFEST = 128 * 1024
MAX_WORKSPACES = 200
MAX_DEPTH = 8
SAFE_PATTERN = re.compile(r'^[a-zA-Z0-9_./*@{}?\[\]!+-]+$')


def _read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_MANIFEST:
        raise ValueError('unsafe or oversized manifest')
    try:
        data = json.loads(path.read_text('utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('invalid JSON workspace manifest') from exc
    if not isinstance(data, dict):
        raise ValueError('package.json must be an object')
    return data


def _patterns(root: Path, package: dict) -> tuple[list[str], list[str]]:
    workspaces = package.get('workspaces', [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get('packages', [])
    if not isinstance(workspaces, list):
        raise ValueError('workspaces must be an array')
    if (root/'pnpm-workspace.yaml').exists():
        file = root/'pnpm-workspace.yaml'
        if file.is_symlink() or not file.is_file() or file.stat().st_size > MAX_MANIFEST:
            raise ValueError('unsafe pnpm workspace manifest')
        text = file.read_text('utf-8')
        active = False
        for line in text.splitlines():
            # Support only the static YAML list; reject unexpected lines inside section.
            if line.strip() == 'packages:':
                active = True
                continue
            if active and line and not line[0].isspace() and not line.startswith('#'):
                active = False
            if active:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if not stripped.startswith('- '):
                    raise ValueError('pnpm workspace requires static package globs')
                value = stripped[2:].strip().strip('"\'')
                workspaces.append(value)
    if len(workspaces) > MAX_WORKSPACES:
        raise ValueError('too many workspace patterns')
    positive, negative = [], []
    for item in workspaces:
        if not isinstance(item, str):
            raise ValueError('invalid workspace pattern')
        negative_flag = item.startswith('!')
        pattern = item[1:] if negative_flag else item
        if (not pattern or len(pattern) > 128 or not SAFE_PATTERN.fullmatch(pattern)
                or pattern.startswith('/') or any(part == '..' for part in pattern.split('/'))
                or '**' in pattern or len(pattern.split('/')) > MAX_DEPTH):
            raise ValueError('unsafe workspace pattern')
        (negative if negative_flag else positive).append(pattern.rstrip('/'))
    return positive, negative


def _safe_package(root: Path, folder: Path) -> bool:
    if folder.is_symlink() or not folder.is_dir():
        return False
    try:
        rel = folder.relative_to(root)
    except ValueError:
        return False
    if len(rel.parts) > MAX_DEPTH:
        return False
    current = root
    for segment in rel.parts:
        current = current / segment
        if current.is_symlink() or segment in ('node_modules', '.git', '.ai') or segment.startswith('.'):
            return False
    return True


def discover(project: Path) -> dict:
    root = project.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    manifest = root/'package.json'
    if not manifest.exists():
        return {'schema_version': 1, 'packages': [], 'aliases': {}, 'warnings': ['root-package-json-missing']}
    package = _read_json(manifest)
    patterns, excluded = _patterns(root, package)
    folders: dict[str,Path] = {}
    for pat in patterns:
        for folder in root.glob(pat):
            if _safe_package(root, folder) and (folder/'package.json').is_file() and not (folder/'package.json').is_symlink():
                folders[folder.relative_to(root).as_posix()] = folder
                if len(folders) > MAX_WORKSPACES:
                    raise ValueError('workspace package cap exceeded')
    for pat in excluded:
        for folder in root.glob(pat):
            if folder.is_relative_to(root):
                folders.pop(folder.relative_to(root).as_posix(), None)
    packages = []
    aliases = {}
    warnings = []
    for rel, folder in sorted(folders.items()):
        item = _read_json(folder/'package.json')
        name = item.get('name')
        if not isinstance(name,str) or not re.fullmatch(r'(?:@[\w.-]+/)?[\w.-]{1,100}', name):
            warnings.append('invalid-package-name:' + rel)
            continue
        if name in aliases:
            raise ValueError('duplicate workspace package name: '+name)
        # Entry point only; no exports condition evaluation or tsconfig plugin loading.
        entries = []
        for key in ('source','module','main','types','typings'):
            value = item.get(key)
            if isinstance(value,str) and value.startswith('./'):
                entries.append(value[2:])
        entries += ['src/index.ts','src/index.tsx','src/index.js','src/index.jsx',
                    'index.ts','index.tsx','index.js','index.jsx']
        packages.append({'name':name,'path':rel,'candidate_entries':list(dict.fromkeys(entries))})
        aliases[name] = rel
    return {'schema_version':1,'packages':packages,'aliases':aliases,'warnings':warnings,
            'note':'Static local workspace discovery only; not a package-manager or tsconfig resolver.'}


def main(argv=None):
    p = argparse.ArgumentParser(description='Inspect local npm/yarn/pnpm workspaces without executing manifests')
    p.add_argument('--project',type=Path,required=True)
    args = p.parse_args(argv)
    try:
        print(json.dumps(discover(args.project),ensure_ascii=False,indent=2))
    except (OSError,ValueError) as exc:
        p.exit(2,'error: '+str(exc)+'\n')

if __name__ == '__main__':
    main()
