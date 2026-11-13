#!/usr/bin/env python3
"""An actual test-evidence-dashboard lifecycle using the bundled Todo API.

Runs trusted fixture tests only with --execute-tests. The entire demo lives
under a disposable temporary directory; no production project is altered.
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dashboard.snapshot import snapshot
from orchestrator.cli import init, add_task, set_task
from tools.run_checks import run, save_report


def exercise(execute_tests: bool = False):
    with tempfile.TemporaryDirectory(prefix='v42-real-fixture-') as directory:
        project = Path(directory) / 'todo'
        shutil.copytree(ROOT / 'examples' / 'runnable-todo', project)
        init(project)
        add_task(project, 'V42-INTEGRATION', 'Run bundled Todo API regression tests')
        checks = {'checks': [{'name': 'todo-api', 'cwd': '.',
                              'args': ['python', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                              'timeout_seconds': 60, 'enabled': True}]}
        (project / '.ai' / 'checks.json').write_text(json.dumps(checks), encoding='utf-8')
        report = run(project, execute=execute_tests)
        if execute_tests:
            if [x['status'] for x in report['checks']] != ['passed']:
                raise AssertionError('Todo API tests did not pass')
            filename = Path(save_report(project, report)).name
            set_task(project, 'V42-INTEGRATION', 'done', report=filename)
        state = snapshot(project)
        assert state['stats']['tasks'] == 1
        assert state['stats']['by_status']['done'] == int(execute_tests)
        assert state['stats']['successful_reports'] == int(execute_tests)
        assert state['tasks'][0]['evidence_integrity'] == ('verified' if execute_tests else 'none')
        return {'mode': 'executed-trusted-todo-tests' if execute_tests else 'preview-only',
                'task_count': state['stats']['tasks'],
                'verified_completed': state['stats']['by_status']['done'],
                'executed_checks': report['summary']['passed'],
                'dashboard_read_only': state['mode'] == 'read-only',
                'temporary_project_deleted_on_exit': True}


def main(argv=None):
    p = argparse.ArgumentParser(description='Real Todo fixture -> report -> task evidence -> dashboard')
    p.add_argument('--execute-tests', action='store_true', help='required to execute bundled Python test code')
    a = p.parse_args(argv)
    print(json.dumps(exercise(a.execute_tests), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
