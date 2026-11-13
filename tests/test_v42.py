"""V4.2 large-state coverage, concurrent reads, and real bundled Todo lifecycle."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from dashboard.snapshot import _mtime, snapshot
from tools.stability_v42 import create_fixture, concurrent_probe, evaluate
import importlib.util
ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'examples' / 'v42-reliability-demo' / 'run_demo.py'
spec = importlib.util.spec_from_file_location('v42_real_demo', DEMO)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class DashboardLongTermTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='v42-tests-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_total_tasks_not_limited_to_300(self):
        create_fixture(self.root, tasks=900, reports=0, loops=0)
        view = snapshot(self.root)
        self.assertEqual(view['stats']['tasks'], 900)
        self.assertEqual(view['coverage']['tasks_displayed'], 300)
        self.assertEqual(view['stats']['by_status'], {'todo':225,'in_progress':225,'blocked':225,'done':225})
        self.assertEqual(len(view['tasks']), 300)
        self.assertTrue(any('仅展示' in w for w in view['warnings']))
        self.assertEqual(view['coverage']['evidence_checked_tasks'], 300)

    def test_most_recent_tasks_selected_not_first_tasks(self):
        create_fixture(self.root, tasks=305, reports=0, loops=0)
        file = self.root / '.ai' / 'task_state.json'
        data = json.loads(file.read_text())
        data['tasks'][0]['id'] = 'LATEST-FIRST'
        data['tasks'][0]['updated_at'] = '2099-01-01T00:00:00+00:00'
        data['tasks'][1]['id'] = 'OLDEST-SECOND'
        data['tasks'][1]['updated_at'] = '1900-01-01T00:00:00+00:00'
        file.write_text(json.dumps(data))
        view = snapshot(self.root)
        self.assertEqual(view['tasks'][0]['id'], 'LATEST-FIRST')
        self.assertNotIn('OLDEST-SECOND', [row['id'] for row in view['tasks']])

    def test_recent_report_selection_not_early_500(self):
        create_fixture(self.root, tasks=0, reports=555, loops=0)
        folder = self.root / '.ai' / 'reports'
        for i, f in enumerate(sorted(folder.glob('*.json'))):
            os.utime(f, (10_000 + i, 10_000 + i))
        view = snapshot(self.root)
        self.assertEqual(len(view['reports']), 60)
        self.assertEqual(view['reports'][0]['name'], 'checks-bench-00554.json')
        self.assertTrue(any('仅显示最近' in w for w in view['warnings']))
        self.assertEqual(view['coverage']['report_display_limit'], 60)

    def test_deleted_entry_mtime_safe(self):
        self.assertEqual(_mtime(self.root / 'deleted-file.json'), -1)

    def test_corrupt_task_state_returns_warning(self):
        create_fixture(self.root, tasks=5, reports=0, loops=0)
        (self.root / '.ai' / 'task_state.json').write_text('{broken!')
        view = snapshot(self.root)
        self.assertEqual(view['stats']['tasks'], 0)
        self.assertTrue(any('任务状态文件' in warning for warning in view['warnings']))

    def test_symlink_report_not_followed(self):
        create_fixture(self.root, tasks=0, reports=0, loops=0)
        outside = self.root / 'private.json'
        outside.write_text(json.dumps({'schema_version':2,'secret':'DO-NOT-LEAK'}))
        (self.root / '.ai' / 'reports' / 'probe.json').symlink_to(outside)
        view = snapshot(self.root)
        self.assertNotIn('DO-NOT-LEAK', json.dumps(view))
        self.assertFalse(view['reports'])

    def test_bounded_fixture_generator(self):
        with self.assertRaises(ValueError): create_fixture(self.root, tasks=10_001)
        with self.assertRaises(ValueError): create_fixture(self.root, reports=3_001)
        with self.assertRaises(ValueError): create_fixture(self.root, loops=401)

    def test_read_benchmark_does_not_modify_project(self):
        create_fixture(self.root, tasks=480, reports=55, loops=15)
        file = self.root / '.ai' / 'task_state.json'
        original = file.read_bytes()
        result = evaluate(self.root, reads=3)
        self.assertTrue(result['consistent_counts'])
        self.assertEqual(result['last_sample']['tasks_total'],480)
        self.assertEqual(result['last_sample']['tasks_displayed'],300)
        self.assertEqual(file.read_bytes(),original)

    def test_concurrent_atomic_writes_keep_task_state_readable(self):
        create_fixture(self.root, tasks=450, reports=15, loops=10)
        result = concurrent_probe(self.root, rounds=12)
        self.assertEqual(result['errors'], [])
        self.assertTrue(result['writer_finished'])
        self.assertTrue(result['all_counts_correct'])

    def test_excessive_repair_runs_mark_metrics_unavailable_not_zero(self):
        create_fixture(self.root, tasks=1, reports=0, loops=400)
        extra = self.root / '.ai' / 'loops' / 'loop-extra'
        extra.mkdir()
        view = snapshot(self.root)
        self.assertFalse(view['loops']['available'])
        self.assertTrue(any('修复循环记录不可用' in w for w in view['warnings']))

    def test_no_project_code_executed_for_stability_fixture(self):
        create_fixture(self.root, tasks=12, reports=5, loops=2)
        view = snapshot(self.root)
        self.assertEqual(view['mode'],'read-only')
        self.assertEqual(view['stats']['tasks'],12)
        self.assertEqual(view['loops']['runs'],2)


class TodoProjectIntegrationTests(unittest.TestCase):
    def test_bundled_real_todo_preview_only(self):
        result = demo.exercise(execute_tests=False)
        self.assertEqual(result['executed_checks'],0)
        self.assertEqual(result['verified_completed'],0)
        self.assertTrue(result['dashboard_read_only'])

    def test_bundled_real_todo_test_and_evidence(self):
        result = demo.exercise(execute_tests=True)
        self.assertEqual(result['executed_checks'],1)
        self.assertEqual(result['verified_completed'],1)
        self.assertTrue(result['temporary_project_deleted_on_exit'])


if __name__ == '__main__':
    unittest.main()
