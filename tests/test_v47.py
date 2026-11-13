"""V4.7 release shard, timeout, report safety and process-death tests."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import release_matrix_v47 as matrix
from tools import fault_injection_v47 as faults


class ReleaseMatrixTests(unittest.TestCase):
    def test_shards_enumerate_every_test_once(self):
        matrix.validate_matrix()
        all_modules = matrix.listed_modules('all')
        self.assertEqual(len(all_modules), len(set(all_modules)))
        self.assertIn('test_v47', all_modules)

    def test_preview_does_not_execute(self):
        with patch.object(matrix, '_execute', side_effect=AssertionError('should never execute')):
            result = matrix.run_matrix('platform')
        self.assertFalse(result['actually_executed'])
        self.assertEqual(result['summary']['planned'], len(matrix.SHARDS['platform']))
        self.assertEqual(result['summary']['passed'], 0)

    def test_shard_is_strictly_approved(self):
        with self.assertRaises(ValueError):
            matrix.listed_modules('custom; python evil.py')
        with self.assertRaises(ValueError):
            matrix.run_matrix('all', max_total_seconds=3601)
        with self.assertRaises(ValueError):
            matrix.run_matrix('core', module_timeout_seconds=0)

    def test_failures_timeouts_never_count_as_passed(self):
        with patch.object(matrix, '_execute', side_effect=[
            {'status': 'passed', 'tests_reported': 3},
            {'status': 'timeout', 'tests_reported': None},
            *[{'status': 'failed', 'tests_reported': None}] * (len(matrix.SHARDS['platform']) - 2)
        ]):
            result = matrix.run_matrix('platform', execute=True)
        self.assertEqual(result['summary']['passed'], 1)
        self.assertEqual(result['summary']['timeout'], 1)
        self.assertEqual(result['tests_reported'], 3)

    def test_budget_exhausted_marks_not_run(self):
        with patch.object(matrix, '_execute', side_effect=lambda name, timeout:
                          {'status': 'passed', 'elapsed_seconds': 0}):
            with patch.object(matrix.time, 'monotonic', side_effect=[0, 2, 2, 2, 2, 2]):
                result = matrix.run_matrix('platform', execute=True, max_total_seconds=1)
        self.assertTrue(all(row['status'] == 'not_run' for row in result['modules']))

    def test_report_destination_restriction(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'report must'):
                matrix.save({'x': 1}, Path(td) / 'a.json')
            with self.assertRaisesRegex(ValueError, 'report must'):
                matrix.save({'x': 1}, matrix.ROOT / 'benchmarks/reports/../../escape.json')

    def test_actual_single_module_separate_process(self):
        # Uses an inexpensive historical module as a real subprocess; not a mock.
        result = matrix._execute('test_v21', timeout=30)
        self.assertEqual(result['status'], 'passed', result.get('diagnostic_tail'))
        self.assertGreater(result['tests_reported'] or 0, 0)
        self.assertEqual(len(result['source_sha256']), 64)

    def test_expired_module_times_out(self):
        # Exercise the process-group termination branch against a local child.
        with patch.object(matrix, 'ROOT', Path(__file__).resolve().parents[1]):
            with patch.object(matrix.subprocess, 'Popen') as mock:
                class Fake:
                    pid = 99999999
                    returncode = None
                    def __init__(self): self.calls = 0
                    def communicate(self, timeout=None):
                        if self.calls == 0:
                            self.calls += 1
                            raise matrix.subprocess.TimeoutExpired(['python'], timeout)
                        return '', 'Ran 0 tests\n'
                    def poll(self): return 0
                mock.return_value = Fake()
                with patch.object(matrix, '_terminate_tree') as terminate:
                    result = matrix._execute('test_v21', 1)
        self.assertEqual(result['status'], 'timeout')
        terminate.assert_called_once()


class FaultInjectionTests(unittest.TestCase):
    @unittest.skipUnless(__import__('shutil').which('git'), 'Git required for fault test')
    def test_real_process_death_releases_gate(self):
        result = faults.run_faults()
        self.assertTrue(result['passed'])
        self.assertIn('concurrent_write_rejected', result['events'])
        self.assertIn('lock_recovered_after_process_death', result['events'])


if __name__ == '__main__':
    unittest.main()
