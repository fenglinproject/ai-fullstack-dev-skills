"""V5.0 release lifecycle tests: local, read-only before approval, no publisher impersonation."""
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import lifecycle_v50 as lc
from tools import package_release_v50 as pkg

ROOT=Path(__file__).resolve().parents[1]


def small_archive(directory:Path,version:str='4.9',files=None) -> Path:
    if files is None:files={'fullstack.py':f'print("test-{version}")\n'.encode(),'README.md':b'fixture, not a real distribution\n'}
    archive=directory/f'fixture-{version}.zip'
    manifest={'schema_version':1,'toolkit_version':version,'digest_algorithm':'sha256',
              'signed':False,'files':[{'path':k,'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
                                       for k,v in sorted(files.items())],
              'note':'This is a local fixture, not a trusted distribution.'}
    with zipfile.ZipFile(archive,'w') as z:
        for name,blob in files.items():
            info=zipfile.ZipInfo(f'ai-fullstack-dev-skills-v{version}/'+name)
            info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
            z.writestr(info,blob)
        name=f'ai-fullstack-dev-skills-v{version}/RELEASE_MANIFEST_V{version}.json'
        info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
        z.writestr(info,json.dumps(manifest))
    return archive

class Lifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle_dir=tempfile.TemporaryDirectory()
        cls.bundle=Path(cls.bundle_dir.name)
        cls.v49=small_archive(cls.bundle,'4.9')
        cls.v50=cls.bundle/pkg.ZIP_NAME
        pkg.make_package(cls.v50)
        cls.d49=lc._hash_file(cls.v49)
        cls.d50=lc._hash_file(cls.v50)

    @classmethod
    def tearDownClass(cls):cls.bundle_dir.cleanup()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.home=self.base/'managed'

    def tearDown(self):self.tmp.cleanup()

    def _install(self):return lc.apply(self.home,self.v49,self.d49,approve=True)
    def _upgrade(self):return lc.apply(self.home,self.v50,self.d50,approve=True)

    def test_v50_release_manifest(self):
        r=pkg.verify_package(self.v50)
        self.assertEqual(r['toolkit_version'],'5.0')
        self.assertGreaterEqual(r['files_verified'],480)

    def test_plan_creates_nothing(self):
        result=lc.plan(self.home,self.v49,self.d49)
        self.assertEqual(result['action'],'install')
        self.assertFalse(self.home.exists())
        self.assertFalse(result['signed_with_supplied_key'])

    def test_plan_wrong_sha_fails(self):
        with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
            lc.plan(self.home,self.v49,'f'*64)
        self.assertFalse(self.home.exists())

    def test_digest_requires_hex(self):
        with self.assertRaisesRegex(ValueError,'lower-case hex'):
            lc.plan(self.home,self.v49,'ABC')

    def test_signature_pair_required(self):
        with self.assertRaisesRegex(ValueError,'together'):
            lc.plan(self.home,self.v49,self.d49,public_key=self.base/'missing.pem')

    def test_install_upgrade_and_rollback_preserve_workspace(self):
        r=self._install();self.assertEqual(r['action'],'install')
        self.assertEqual(lc.status(self.home,integrity=True)['version'],'4.9')
        (self.home/'workspace'/'personal.txt').write_text('keep forever')
        r=self._upgrade()
        self.assertEqual(r['action'],'upgrade')
        self.assertEqual(lc.status(self.home,integrity=True)['version'],'5.0')
        self.assertEqual((self.home/'workspace'/'personal.txt').read_text(),'keep forever')
        launcher=subprocess.run([sys.executable,str(self.home/'launch.py'),'--version'],capture_output=True,text=True)
        self.assertEqual(launcher.returncode,0,launcher.stderr)
        self.assertIn('5.0',launcher.stdout)
        preview=lc.rollback(self.home)
        self.assertTrue(preview['planned'])
        self.assertEqual(lc.status(self.home)['version'],'5.0')
        lc.rollback(self.home,approve=True)
        self.assertEqual(lc.status(self.home,integrity=True)['version'],'4.9')
        self.assertEqual((self.home/'workspace'/'personal.txt').read_text(),'keep forever')
        self.assertTrue((self.home/'releases'/r['active']).exists())

    def test_upgrade_no_approval_no_change(self):
        self._install()
        before=lc.status(self.home)['active']
        r=lc.apply(self.home,self.v50,self.d50,approve=False)
        self.assertTrue(r['planned'])
        self.assertEqual(lc.status(self.home)['active'],before)

    def test_can_rollback_multiple_times(self):
        self._install();self._upgrade()
        lc.rollback(self.home,approve=True)
        lc.rollback(self.home,approve=True)
        self.assertEqual(lc.status(self.home)['version'],'5.0')

    def test_cannot_rollback_without_history(self):
        self._install()
        with self.assertRaisesRegex(ValueError,'no previous'):
            lc.rollback(self.home,approve=True)

    def test_import_private_workspace(self):
        self._install()
        source=self.base/'oldproject';(source/'src').mkdir(parents=True)
        (source/'src'/'app.py').write_text('print(1)')
        (source/'.secrets').write_text('do-not-log')
        plan=lc.import_workspace(self.home,source,'my-project')
        self.assertEqual(plan['files'],2)
        self.assertFalse((self.home/'workspace'/'my-project').exists())
        lc.import_workspace(self.home,source,'my-project',approve=True)
        self.assertEqual((self.home/'workspace'/'my-project'/'src'/'app.py').read_text(),'print(1)')
        self.assertEqual((source/'.secrets').read_text(),'do-not-log')
        self._upgrade()
        self.assertTrue((self.home/'workspace'/'my-project'/'src'/'app.py').is_file())

    @unittest.skipIf(os.name == "nt", "Windows may restrict symlink creation")
    def test_import_refuses_symlink(self):
        self._install()
        source=self.base/'old';source.mkdir()
        (source/'link').symlink_to(self.base/'missing')
        with self.assertRaisesRegex(ValueError,'symlink'):
            lc.import_workspace(self.home,source,'safe',approve=True)

    def test_import_refuses_existing_destination(self):
        self._install()
        source=self.base/'old';source.mkdir();(source/'a').write_text('x')
        lc.import_workspace(self.home,source,'one',approve=True)
        with self.assertRaisesRegex(ValueError,'already exists'):
            lc.import_workspace(self.home,source,'one',approve=True)

    def test_modified_installed_release_detected(self):
        r=self._install()
        (self.home/'releases'/r['active']/'fullstack.py').write_text('tampered')
        self.assertFalse(lc.status(self.home,integrity=True)['active_integrity_ok'])
        self._upgrade()
        with self.assertRaisesRegex(ValueError,'integrity failed'):
            lc.rollback(self.home,approve=True)

    def test_operation_lock_blocks_upgrade(self):
        self._install()
        (self.home/'.release-manager'/'operation.lock').write_text('lock')
        with self.assertRaisesRegex(ValueError,'in progress'):
            self._upgrade()
        self.assertEqual(lc.status(self.home)['version'],'4.9')

    @unittest.skipIf(os.name == "nt", "Windows may restrict symlink creation")
    def test_symlink_home_rejected(self):
        actual=self.base/'actual';actual.mkdir()
        self.home.symlink_to(actual,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):
            lc.plan(self.home,self.v49,self.d49)

    @unittest.skipIf(os.name == "nt", "Windows may restrict symlink creation")
    def test_symlink_release_dir_rejected(self):
        self._install()
        releases=self.home/'releases';renamed=self.home/'releases_old'
        releases.rename(renamed);releases.symlink_to(renamed,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'installation folder'):
            self._upgrade()

    def test_unsafe_zip_member_rejected(self):
        for rel in ('../escape.py','src/../escape.py','CON.txt','foo\\evil.py','src/../../escape.py'):
            with self.subTest(rel=rel):
                archive=small_archive(self.base,'4.9',{'fullstack.py':b'x','README.md':b'y',rel:b'z'})
                with self.assertRaisesRegex(ValueError,'unsafe archive'):
                    lc.plan(self.home,archive,lc._hash_file(archive))

    def test_casefold_collision_rejected(self):
        archive=small_archive(self.base,'4.9',{'Readme.md':b'a','README.md':b'b','fullstack.py':b'x'})
        with self.assertRaisesRegex(ValueError,'case-colliding'):
            lc.plan(self.home,archive,lc._hash_file(archive))

    def test_symlink_zip_rejected(self):
        archive=self.base/'symlink.zip'
        manifest={'schema_version':1,'toolkit_version':'4.9','digest_algorithm':'sha256', 'signed':False,'files':[]}
        with zipfile.ZipFile(archive,'w') as z:
            i=zipfile.ZipInfo('ai-fullstack-dev-skills-v4.9/escape')
            i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16
            z.writestr(i,'/etc/passwd')
            z.writestr('ai-fullstack-dev-skills-v4.9/RELEASE_MANIFEST_V4.9.json',json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'unsafe archive'):
            lc.plan(self.home,archive,lc._hash_file(archive))

    def test_invalid_manifest_detected(self):
        archive=small_archive(self.base,'4.9',{'fullstack.py':b'x'})
        # Modify content after manifest generation without altering manifest entry.
        damaged=self.base/'bad.zip'
        with zipfile.ZipFile(archive) as src, zipfile.ZipFile(damaged,'w') as dst:
            for i in src.infolist():
                b=src.read(i)
                if i.filename.endswith('fullstack.py'):b=b'bad'
                dst.writestr(i,b)
        with self.assertRaisesRegex(ValueError,'manifest'):
            lc.plan(self.home,damaged,lc._hash_file(damaged))

    def test_modified_zip_after_plan_rejected(self):
        self._install()
        original_plan=lc.plan(self.home,self.v50,self.d50)
        with patch.object(lc,'inspect_archive',side_effect=[original_plan,ValueError('archive changed after planning')]):
            with self.assertRaisesRegex(ValueError,'archive changed'):
                lc.apply(self.home,self.v50,self.d50,approve=True)
        self.assertEqual(lc.status(self.home)['version'],'4.9')

    def test_cli_install_upgrade_rollback(self):
        base=[sys.executable,str(ROOT/'fullstack.py'),'lifecycle']
        run=lambda *args:subprocess.run([*base,*args],cwd=ROOT,capture_output=True,text=True)
        p=run('install','--home',str(self.home),'--archive',str(self.v49),'--expected-sha256',self.d49)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(self.home.exists())
        p=run('install','--home',str(self.home),'--archive',str(self.v49),'--expected-sha256',self.d49,'--approve')
        self.assertEqual(p.returncode,0,p.stderr)
        p=run('upgrade','--home',str(self.home),'--archive',str(self.v50),'--expected-sha256',self.d50,'--approve')
        self.assertEqual(p.returncode,0,p.stderr)
        p=run('rollback','--home',str(self.home),'--approve')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(lc.status(self.home)['version'],'4.9')

    def test_launcher_refuses_tampered_install(self):
        installed=self._install()
        target=self.home/'releases'/installed['active']/'README.md'
        target.write_text('unauthorized change')
        p=subprocess.run([sys.executable,str(self.home/'launch.py'),'--version'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('integrity mismatch',p.stderr)

    def test_manifest_tampering_rejected(self):
        installed=self._install()
        manifest=self.home/'releases'/installed['active']/'RELEASE_MANIFEST_V4.9.json'
        manifest.write_text(manifest.read_text()+'\n')
        self.assertFalse(lc.status(self.home,integrity=True)['active_integrity_ok'])
        p=subprocess.run([sys.executable,str(self.home/'launch.py'),'--version'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('manifest integrity mismatch',p.stderr)

    def test_v50_supply_chain_and_provenance(self):
        from tools import supply_chain_v50 as sc
        self.assertTrue(sc.audit()['passed'])
        statement=self.base/'provenance.json'
        sc.create_provenance(self.v50,statement)
        v=sc.verify_provenance(self.v50,statement)
        self.assertTrue(v['digest_matches'])
        self.assertFalse(v['source_authenticated'])
        sbom=self.base/'sbom.json'
        sc.create_sbom(sbom)
        self.assertEqual(json.loads(sbom.read_text())['metadata']['component']['version'],'5.0')

    def test_unmanaged_nonempty_home_rejected(self):
        self.home.mkdir();(self.home/'personal').write_text('donotchange')
        with self.assertRaisesRegex(ValueError,'empty'):
            lc.plan(self.home,self.v49,self.d49)
        self.assertEqual((self.home/'personal').read_text(),'donotchange')

if __name__=='__main__':unittest.main()
