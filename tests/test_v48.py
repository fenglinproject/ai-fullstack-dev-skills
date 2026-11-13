"""V4.8 offline contract and package tests; simulated CI fixtures are NOT CI runs."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import ci_release_v48 as ci
from tools import package_release_v48 as pkg
from tools import toolchain_v48 as tc
from tools.release_matrix_v47 import SHARDS
from tools.release_gate import _matrix


class EvidenceContract(unittest.TestCase):
    SHA='a'*40
    RUN='237971'
    ATTEMPT='1'

    @classmethod
    def fake_record(cls, suite, system):
        # Synthetic record for schema tests; never used as real CI verification.
        if suite in SHARDS:
            raw={'shard':suite,'actually_executed':True,
                 'modules':[{'module':n,'status':'passed','tests_reported':1,
                             'source_sha256':hashlib.sha256((ci.ROOT/'tests'/(n+'.py')).read_bytes()).hexdigest()}
                            for n in SHARDS[suite]]}
            count=len(raw['modules'])
        elif suite=='smoke':
            raw={'actually_executed':True, 'steps':[{'name':s[0],'status':'passed'} for s in _matrix('smoke')]}
            count=len(raw['steps'])
        else:
            raw={'executed':True, 'steps':[{'name':s,'status':'passed','exit_code':0}
                                             for s in ('unittest','fault-injection')]}
            count=2
        return {'schema_version':1,'toolkit_version':'4.8', 'suite':suite,
                'platform':system, 'executed':True, 'status':'passed',
                'timestamp':'2026-11-12T00:00:00+00:00','origin':'github-actions',
                'commit_sha':cls.SHA,'run_id':cls.RUN,'attempt':cls.ATTEMPT,
                'checks_count':count,'elapsed_seconds':1.0,'details':raw,
                'details_sha256':hashlib.sha256(ci.canonical(raw)).hexdigest()}

    def fixture_directory(self, path):
        for suite, system in ci.REQUIRED:
            p=path/f'ci_v48_{system}_{suite}.json'
            p.write_text(json.dumps(self.fake_record(suite,system)),encoding='utf-8')

    def aggregate(self, folder):
        return ci.aggregate(folder,sha=self.SHA,run_id=self.RUN,attempt=self.ATTEMPT)

    def test_exact_eight_required(self):
        self.assertEqual(len(ci.REQUIRED),8)
        self.assertEqual(len([x for x in ci.REQUIRED if x[1]=='linux']),6)

    def test_plan_does_not_execute(self):
        v=ci.run_suite('smoke',execute=False,context={'origin':'local','commit_sha':'u','run_id':'u','attempt':'u'})
        self.assertEqual(v['status'],'planned')
        self.assertFalse(v['executed'])

    def test_context_missing_github_details_rejected(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true','GITHUB_SHA':'fake','GITHUB_RUN_ID':'1','GITHUB_RUN_ATTEMPT':'1'}):
            with self.assertRaises(ValueError):ci.context_from_environment()

    def test_context_runner_mismatch_rejected(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true','GITHUB_SHA':self.SHA,'GITHUB_RUN_ID':'1',
                                     'GITHUB_RUN_ATTEMPT':'1','RUNNER_OS':'DefinitelyFake'}):
            with self.assertRaises(ValueError):ci.context_from_environment()

    def test_complete_synthetic_matrix_only_contract(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            self.fixture_directory(folder)
            v=self.aggregate(folder)
            self.assertTrue(v['verified_consistency'])
            self.assertFalse(v['externally_signed'])
            self.assertEqual(len(v['suites']),8)

    def test_missing_os_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            (folder/'ci_v48_macos_locks.json').unlink()
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_unexpected_extra_report_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            (folder/'unrecognized.json').write_text('{}')
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_wrong_run_context_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            record=self.fake_record('locks','windows');record['run_id']='9'
            (folder/'ci_v48_windows_locks.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_failed_suite_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            record=self.fake_record('locks','macos');record['status']='failed'
            (folder/'ci_v48_macos_locks.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_fake_report_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            record=self.fake_record('smoke','linux');record['details']['steps'][0]['status']='failed'
            (folder/'ci_v48_linux_smoke.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_source_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            record=self.fake_record('core','linux')
            record['details']['modules'][0]['source_sha256']='0'*64
            record['details_sha256']=hashlib.sha256(ci.canonical(record['details'])).hexdigest()
            (folder/'ci_v48_linux_core.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_locally_labeled_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            record=self.fake_record('locks','linux');record['origin']='local'
            (folder/'ci_v48_linux_locks.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_symlink_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.fixture_directory(folder)
            p=folder/'ci_v48_linux_locks.json';target=folder/'reference'
            target.write_bytes(p.read_bytes());p.unlink()
            try:p.symlink_to(target)
            except (OSError,NotImplementedError):self.skipTest('symlink unsupported')
            with self.assertRaises(ValueError):self.aggregate(folder)

    def test_output_overwrite_prohibited(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ci_v48_test.json';path.write_text('existing')
            with patch.object(ci,'ROOT',Path(d)):
                # outside allowed root even before overwrite check
                with self.assertRaises(ValueError):ci._validate_destination(path)


class ReleasePackage(unittest.TestCase):
    def test_no_secret_or_runtime_paths_are_included(self):
        names=[p.relative_to(pkg.ROOT).as_posix() for p in pkg.files_to_release()]
        self.assertGreater(len(names),400)
        self.assertFalse(any(x.startswith(('benchmarks/reports/','.git/','.ai/')) for x in names))
        self.assertNotIn(pkg.MANIFEST,names)

    def test_deterministic_zip_and_inner_manifest_verification(self):
        with tempfile.TemporaryDirectory() as d:
            first=Path(d)/'first';second=Path(d)/'second'
            first.mkdir();second.mkdir()
            a=first/pkg.ZIP_NAME;b=second/pkg.ZIP_NAME
            r1=pkg.make_package(a);r2=pkg.make_package(b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertTrue(r1['verified_integrity'])
            self.assertEqual(r1['files_verified'],r2['files_verified'])
            self.assertEqual(len(a.with_suffix('.zip.sha256').read_text().split()[0]),64)

    def test_archive_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/pkg.ZIP_NAME
            with zipfile.ZipFile(p,'w') as z:
                z.writestr(pkg.NAME+'/../bad.txt','not safe')
            with self.assertRaises(ValueError):pkg.verify_package(p)

    def test_archive_rejects_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/pkg.ZIP_NAME
            with zipfile.ZipFile(p,'w') as z:
                with __import__('warnings').catch_warnings():
                    __import__('warnings').simplefilter('ignore')
                    z.writestr(pkg.NAME+'/duplicate.txt','a')
                    z.writestr(pkg.NAME+'/duplicate.txt','b')
            with self.assertRaises(ValueError):pkg.verify_package(p)

    def test_archive_rejects_symlink_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/pkg.ZIP_NAME
            with zipfile.ZipFile(p,'w') as z:
                inf=zipfile.ZipInfo(pkg.NAME+'/link.txt')
                inf.create_system=3
                inf.external_attr=(0o120777)<<16
                z.writestr(inf,'target')
            with self.assertRaises(ValueError):pkg.verify_package(p)

    def test_output_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/pkg.ZIP_NAME;p.write_text('existing')
            with self.assertRaises(ValueError):pkg.make_package(p)


class Toolchain(unittest.TestCase):
    def test_python_runtime_check_is_non_mutating(self):
        result=tc.version_check('python')
        self.assertEqual(result['component'],'python')
        self.assertIsInstance(result['passed'],bool)

    def test_unknown_component_rejected(self):
        with self.assertRaises(ValueError):tc.version_check('mystery')

    def test_node_version_parsing(self):
        class R:
            returncode=0
            stdout='v22.5.0\n'
        with patch('tools.toolchain_v48.shutil.which',return_value='node'):
            result=tc.version_check('node',runner=lambda *a,**kw:R())
        self.assertTrue(result['passed'])

    def test_typescript_version_mismatch(self):
        class R:
            returncode=0
            stdout='Version 5.8.3\n'
        with patch('tools.toolchain_v48.shutil.which',return_value='tsc'):
            result=tc.version_check('typescript',runner=lambda *a,**kw:R())
        self.assertFalse(result['passed'])


if __name__=='__main__':unittest.main()
