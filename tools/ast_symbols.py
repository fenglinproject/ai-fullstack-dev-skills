#!/usr/bin/env python3
"""Bounded, read-only Python AST symbol and reference discovery.

AST is authoritative for Python syntax *locations*, not runtime binding. Other
languages are not parsed here. Never executes source or follows symlinks.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from tools.context_retrieval import _source_files, SENSITIVE_TEXT, tokens
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.context_retrieval import _source_files, SENSITIVE_TEXT, tokens

MAX_SYMBOLS = 12000
MAX_REFERENCES = 24000
IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')


def _parts(value: str) -> set[str]:
    """Split camelCase, dotted names and snake_case for conservative ranking."""
    words = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', value)
    return set(re.findall(r'[a-z][a-z0-9]*', words.casefold()))


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str):
        self.rel = rel
        self.scopes: list[str] = []
        self.symbols: list[dict] = []
        self.references: list[dict] = []
        self.import_aliases: dict[str, str] = {}

    def _definition(self, node: ast.AST, name: str, kind: str):
        qualified = '.'.join([*self.scopes, name])
        self.symbols.append({'path': self.rel, 'name': name, 'qualified_name': qualified,
                             'kind': kind, 'line': node.lineno,
                             'end_line': getattr(node, 'end_lineno', node.lineno)})
        self.scopes.append(name)
        for child in node.body:
            self.visit(child)
        self.scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._definition(node, node.name, 'method' if self.scopes else 'function')

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._definition(node, node.name, 'async_method' if self.scopes else 'async_function')

    def visit_ClassDef(self, node: ast.ClassDef):
        self._definition(node, node.name, 'class')

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.level == 0:
            for item in node.names:
                if item.name != '*':
                    self.import_aliases[item.asname or item.name] = f'{node.module or ""}.{item.name}'.strip('.')
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for item in node.names:
            self.import_aliases[item.asname or item.name.split('.')[0]] = item.name
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        called = node.func
        if isinstance(called, ast.Name):
            name = called.id
            target = self.import_aliases.get(name)
        elif isinstance(called, ast.Attribute):
            name = called.attr
            target = (self.import_aliases.get(called.value.id, '') + '.' + name).lstrip('.') if isinstance(called.value, ast.Name) else None
        else:
            name = None
            target = None
        if name:
            self.references.append({'path': self.rel, 'name': name, 'line': node.lineno,
                                    'scope': '.'.join(self.scopes), 'import_target_hint': target})
        self.generic_visit(node)


def index(project: Path) -> dict:
    root = project.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    symbols: list[dict] = []
    references: list[dict] = []
    parse_errors: list[str] = []
    scanned = 0
    for path, _ in _source_files(root):
        if path.suffix.lower() != '.py':
            continue
        raw = path.read_bytes()
        try:
            source = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if SENSITIVE_TEXT.search(source) or '\0' in source:
            continue
        rel = path.relative_to(root).as_posix()
        scanned += 1
        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError:
            parse_errors.append(rel)
            continue
        visitor = _Visitor(rel)
        visitor.visit(tree)
        symbols.extend(visitor.symbols)
        references.extend(visitor.references)
        if len(symbols) > MAX_SYMBOLS or len(references) > MAX_REFERENCES:
            raise ValueError('AST index symbol or reference cap exceeded; narrow the project')
    return {'schema_version': 1, 'files_scanned': scanned,
            'symbols': sorted(symbols, key=lambda x: (x['path'], x['line'], x['qualified_name'])),
            'references': sorted(references, key=lambda x: (x['path'], x['line'], x['name'])),
            'parse_errors': sorted(parse_errors),
            'note': 'Read-only Python AST locations. References are name-based hints, not resolved call graphs.'}


def search(project: Path, query: str, limit: int = 8, *, include_references: bool = True) -> dict:
    if not isinstance(query, str) or not query.strip() or len(query) > 1000 or SENSITIVE_TEXT.search(query):
        raise ValueError('query must be nonempty, <=1000 characters, and contain no detected secrets')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 12:
        raise ValueError('limit must be 1..12')
    idx = index(project)
    query_parts = _parts(query)
    query_fold = query.casefold().strip()
    candidates = []
    for item in idx['symbols']:
        target = item['qualified_name'].casefold()
        name = item['name'].casefold()
        parts = _parts(item['qualified_name'])
        exact = any(w.casefold() == name or w.casefold() == target for w in IDENTIFIER.findall(query))
        score = (90 if exact else 0) + (35 if name in query_fold else 0)
        score += 8 * len(query_parts & parts)
        score += 2 * len(_parts(item['path']) & query_parts)
        if score <= 0:
            continue
        candidates.append({**item, 'score': score})
    candidates.sort(key=lambda x: (-x['score'], x['path'], x['line'], x['qualified_name']))
    selected = candidates[:limit]
    # Deliberately keep reference output bounded. A same-named call is a candidate,
    # and may not actually refer to the selected symbol.
    if include_references:
        for item in selected:
            matches = [r for r in idx['references'] if r['name'] == item['name']]
            item['candidate_call_sites'] = matches[:20]
            item['call_sites_truncated'] = len(matches) > 20
    return {'schema_version': 1, 'query': query, 'matches': selected,
            'files_scanned': idx['files_scanned'], 'parse_errors': idx['parse_errors'],
            'method': 'python-ast', 'note': idx['note']}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline Python AST symbol lookup (no source execution)')
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--query', required=True)
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--no-references', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = search(args.project, args.query, args.limit, include_references=not args.no_references)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(2, f'error: {exc}\n')


if __name__ == '__main__':
    main()
