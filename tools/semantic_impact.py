#!/usr/bin/env python3
"""Read-only, bounded Git-baseline symbol and import impact hints.

This is Python AST and local-import analysis, NOT a language server or a
proof of all dynamic call sites. JS/TS imports remain dependency-only hints.
"""
from __future__ import annotations
import argparse
import ast
import json
import subprocess
from pathlib import Path

try:
    from tools.dependency_graph import graph, source_files, MAX_SIZE
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.dependency_graph import graph, source_files, MAX_SIZE


def _definitions(text: str) -> dict[str, str] | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            shape = (ast.dump(node.args, include_attributes=False),
                     ast.dump(node.returns, include_attributes=False) if node.returns else '',
                     tuple(ast.dump(x, include_attributes=False) for x in node.decorator_list),
                     isinstance(node, ast.AsyncFunctionDef))
            result[node.name] = repr(shape)
        elif isinstance(node, ast.ClassDef):
            result[node.name] = 'class:' + repr(([ast.dump(x, include_attributes=False) for x in node.bases],
                 [x.name for x in node.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]))
    return result


def _baseline(root: Path, rel: str) -> str | None:
    try:
        result = subprocess.run(['git', '--no-pager', 'show', 'HEAD:' + rel], cwd=root,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=8)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode or len(result.stdout) > MAX_SIZE:
        return None
    try:
        return result.stdout.decode('utf-8')
    except UnicodeDecodeError:
        return None


def analyze(project: Path, changed: list[str]) -> dict:
    root = project.resolve(strict=True)
    names = set(source_files(root))
    if not changed or len(changed) > 50 or any(not isinstance(p, str) or p not in names for p in changed):
        raise ValueError('changed paths must be 1..50 existing, safe source files')
    impact = graph(root, changed)
    results = []
    for rel in changed:
        path = root / rel
        if path.is_symlink() or path.stat().st_size > MAX_SIZE:
            raise ValueError('unsafe source path')
        baseline = _baseline(root, rel)
        entry = {'path': rel, 'baseline_available': baseline is not None,
                 'symbol_changes': [], 'candidate_importers': []}
        if path.suffix == '.py' and baseline is not None:
            before = _definitions(baseline)
            after = _definitions(path.read_text('utf-8'))
            if before is None or after is None:
                entry['parse_error'] = True
            else:
                old_keys, new_keys = set(before), set(after)
                entry['symbol_changes'] = ([{'name': n, 'kind': 'removed'} for n in sorted(old_keys-new_keys)]
                    + [{'name': n, 'kind': 'added'} for n in sorted(new_keys-old_keys)]
                    + [{'name': n, 'kind': 'signature_changed'} for n in sorted(old_keys & new_keys) if before[n] != after[n]])
        elif path.suffix == '.py':
            entry['note'] = 'No Git HEAD baseline; cannot infer symbol changes.'
        # Imported symbols are candidates, not proof of a runtime dependency.
        changed_names = {s['name'] for s in entry['symbol_changes']}
        module_name = rel[:-3].replace('/', '.') if rel.endswith('.py') else ''
        if changed_names and module_name:
            for importer in sorted(names - set(changed)):
                if not importer.endswith('.py'):
                    continue
                f = root / importer
                try:
                    tree = ast.parse(f.read_text('utf-8'))
                except (OSError, UnicodeError, SyntaxError):
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ImportFrom):
                        continue
                    base = '.'.join(Path(importer).parts[:-1])
                    if node.level:
                        parts = base.split('.') if base else []
                        parts = parts[:max(0, len(parts) - node.level + 1)]
                        target = '.'.join(parts + ([node.module] if node.module else []))
                    else:
                        target = node.module or ''
                    if target != module_name:
                        continue
                    hits = sorted({a.name for a in node.names} & changed_names)
                    if hits:
                        entry['candidate_importers'].append({'path': importer, 'symbols': hits, 'line': node.lineno})
        results.append(entry)
    return {'changed': results, 'dependency_impact': impact,
            'limitations': 'Python top-level function/class signatures plus explicit from-import usage; Git HEAD baseline only. '
            'Does not resolve dynamic reflection, re-exports, aliases, runtime data flow, package-relative edge cases, or JS/TS symbols. '
            'Review findings manually; a missing candidate does not imply no impact.'}


def main(argv=None):
    p = argparse.ArgumentParser(description='Read-only Git-baseline symbol impact hints')
    p.add_argument('--project', required=True)
    p.add_argument('--changed', nargs='+', required=True)
    args = p.parse_args(argv)
    try:
        print(json.dumps(analyze(Path(args.project), args.changed), ensure_ascii=False, indent=2))
    except (ValueError, OSError, UnicodeError) as e:
        p.exit(2, f'error: {e}\n')

if __name__ == '__main__':
    main()
