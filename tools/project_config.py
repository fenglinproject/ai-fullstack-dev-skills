#!/usr/bin/env python3
"""V3.9 bounded, read-only tsconfig/JSConfig JSONC and package exports inspection.

No npm/Yarn/pnpm execution; does not evaluate Javascript config or plugins.
Supports relative `extends`, `references`, static `compilerOptions.paths`, and
static conditional `package.json` exports. Unresolved features cause warnings.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from tools.monorepo_workspace import discover, _read_json
    from tools.context_retrieval import SKIP_DIRS
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.monorepo_workspace import discover, _read_json
    from tools.context_retrieval import SKIP_DIRS

MAX_CONFIGS = 250
MAX_BYTES = 128 * 1024
MAX_DEPTH = 12
MAX_ALIASES = 150
MAX_TARGETS = 300


def _jsonc(text: str) -> dict:
    """Remove JS comments/trailing commas without modifying quoted strings."""
    out = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if text.startswith('//', i):
            i = text.find('\n', i)
            if i < 0:
                break
            out.append('\n')
            i += 1
            continue
        if text.startswith('/*', i):
            end = text.find('*/', i + 2)
            if end < 0:
                raise ValueError('unterminated JSONC block comment')
            out.append(' ')
            i = end + 2
            continue
        out.append(ch)
        i += 1
    # Strip trailing commas only outside JSON strings.
    stripped=''.join(out)
    clean=[]; inside=False; escaped=False
    for idx,ch in enumerate(stripped):
        if inside:
            clean.append(ch)
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':inside=False
            continue
        if ch=='"':inside=True;clean.append(ch);continue
        if ch==',':
            j=idx+1
            while j<len(stripped) and stripped[j].isspace():j+=1
            if j<len(stripped) and stripped[j] in '}]':continue
        clean.append(ch)
    return json.loads(''.join(clean))


def _inside(root: Path, file: Path) -> bool:
    if not file.is_relative_to(root) or file.is_symlink():
        return False
    current = root
    for part in file.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            return False
    return True


def _read(root: Path, file: Path) -> dict:
    if not _inside(root, file) or not file.is_file() or file.stat().st_size > MAX_BYTES:
        raise ValueError('unsafe or oversized configuration file')
    data = _jsonc(file.read_text('utf-8'))
    if not isinstance(data, dict):
        raise ValueError('configuration root must be an object')
    return data


def _local(root: Path, parent: Path, raw: str, *, config: bool = False) -> Path | None:
    if (not isinstance(raw, str) or not raw or len(raw) > 255 or '\\' in raw
            or raw.startswith('/') or raw.startswith('~') or '\0' in raw
            ):
        return None
    # Do not resolve symlinks even if target ends up inside root.
    target = Path(os.path.normpath(str(parent / raw)))
    if not _inside(root, target):
        return None
    if config and target.suffix not in {'.json', '.jsonc'}:
        target = target.with_suffix('.json')
    return target if _inside(root, target) else None


def inspect(project: Path) -> dict:
    root = project.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be directory')
    files: list[Path] = []
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.') and not (Path(folder)/d).is_symlink())
        for name in ('tsconfig.json', 'jsconfig.json'):
            if name in names:
                files.append(Path(folder)/name)
                if len(files) > MAX_CONFIGS:
                    raise ValueError('config count limit exceeded')
    warnings: list[str] = []
    result: dict[str,dict] = {}
    cache: dict[Path,dict] = {}

    def parse(file: Path, stack: set[Path]) -> dict:
        if file in cache:
            return cache[file]
        if file in stack or len(stack) >= MAX_DEPTH:
            raise ValueError('tsconfig extends cycle or depth limit')
        data = _read(root, file)
        opts = data.get('compilerOptions', {})
        if not isinstance(opts, dict):
            raise ValueError('invalid compilerOptions')
        parent_config = data.get('extends')
        inherited = {}
        if parent_config is not None:
            if not isinstance(parent_config, str) or not parent_config.startswith('.'):
                warnings.append('unsupported-package-extends:' + file.relative_to(root).as_posix())
            else:
                parent = _local(root, file.parent, parent_config, config=True)
                if parent is None or not parent.is_file():
                    warnings.append('unresolved-extends:' + file.relative_to(root).as_posix())
                else:
                    inherited = dict(parse(parent, stack | {file}))
        # baseUrl and paths are paired with declaring configuration folder.
        effective = dict(inherited)
        base = opts.get('baseUrl')
        if isinstance(base, str):
            found = _local(root, file.parent, base or '.')
            if found is None:
                warnings.append('invalid-base-url:' + file.relative_to(root).as_posix())
            else:
                effective['base'] = found.relative_to(root).as_posix()
        paths = opts.get('paths')
        if paths is not None:
            if not isinstance(paths, dict) or len(paths) > MAX_ALIASES:
                raise ValueError('invalid or oversized paths mapping')
            aliases = {}
            alias_base = root / effective.get('base', file.parent.relative_to(root).as_posix())
            for pattern, targets in paths.items():
                if (not isinstance(pattern,str) or len(pattern)>120 or pattern.count('*')>1
                        or not isinstance(targets,list) or not 1<=len(targets)<=12):
                    warnings.append('unsupported-paths-entry:' + file.relative_to(root).as_posix())
                    continue
                valid_targets=[]
                for target in targets:
                    if not isinstance(target,str) or target.count('*')>1:
                        continue
                    prefix = target.replace('*','')
                    test = _local(root, alias_base, prefix or '.')
                    if test is None:
                        continue
                    # Store root-relative templates; wildcard is inserted by resolver.
                    rel = test.relative_to(root).as_posix().rstrip('/')
                    if '*' in target:
                        rel = rel + ('/' if prefix.endswith('/') and rel != '.' else '') + '*'
                    valid_targets.append(rel)
                if valid_targets:
                    aliases[pattern]=valid_targets
                else:
                    warnings.append('unresolved-paths-entry:' + file.relative_to(root).as_posix())
            effective['aliases']=aliases
        references = data.get('references', [])
        if not isinstance(references, list) or len(references) > 100:
            raise ValueError('invalid project references')
        ref_paths=[]
        for entry in references:
            if not isinstance(entry, dict):
                continue
            target = _local(root, file.parent, entry.get('path'))
            if target is None:
                warnings.append('invalid-reference:' + file.relative_to(root).as_posix())
                continue
            if target.is_dir():
                target /= 'tsconfig.json'
            elif target.suffix != '.json':
                target = target / 'tsconfig.json'
            if not _inside(root, target) or not target.is_file():
                warnings.append('unresolved-reference:' + file.relative_to(root).as_posix())
                continue
            ref_paths.append(target.relative_to(root).as_posix())
        effective['references']=sorted(set(ref_paths))
        cache[file] = effective
        return effective

    for file in sorted(files):
        rel=file.relative_to(root).as_posix()
        try:
            result[rel] = parse(file, set())
        except (ValueError, UnicodeError, OSError, json.JSONDecodeError) as exc:
            warnings.append('invalid-config:' + rel + ':' + str(exc)[:60])

    workspace = discover(root)
    exports={}
    for pkg in workspace['packages']:
        manifest=root/pkg['path']/'package.json'
        try:
            raw=_read_json(manifest).get('exports')
        except ValueError:
            warnings.append('invalid-package-json:'+pkg['path'])
            continue
        if raw is None:
            continue
        mapping={}
        def record(key, value, depth=0):
            if depth > 6 or len(mapping) > MAX_TARGETS:
                return
            if isinstance(value, str):
                if not value.startswith('./'):
                    return
                dest=_local(root, root/pkg['path'], value)
                if dest is not None and '*' not in value:
                    mapping.setdefault(key, []).append(dest.relative_to(root).as_posix())
            elif isinstance(value, dict):
                for cond, target in value.items():
                    if cond in {'default','import','require','types','node','browser'}:
                        record(key,target,depth+1)
            elif isinstance(value, list):
                for target in value[:8]:
                    record(key,target,depth+1)
        if isinstance(raw, str) or isinstance(raw, list):
            record('.',raw)
        elif isinstance(raw, dict):
            if all(not k.startswith('.') for k in raw):
                record('.',raw)
            else:
                for key,val in raw.items():
                    if isinstance(key,str) and (key=='.' or (key.startswith('./') and '*' not in key)):
                        record(key,val)
        if mapping:
            exports[pkg['name']]=mapping
        else:
            warnings.append('unsupported-exports:'+pkg['name'])
    return {'schema_version':1,'configs':result,'package_exports':exports,
            'warnings':sorted(set(warnings)),
            'note':'Static JSONC/tsconfig and package exports hints; unsupported aliases/conditions require full suite.'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Static TS project references, path aliases and package exports (no scripts)')
    p.add_argument('--project',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        print(json.dumps(inspect(a.project),ensure_ascii=False,indent=2))
    except (OSError, ValueError) as e:
        p.exit(2,'error: '+str(e)+'\n')


if __name__=='__main__':
    main()
