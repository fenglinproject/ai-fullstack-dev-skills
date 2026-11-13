"""V4.9 supply chain tests: metadata checks are not online CI or key ownership proof."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import supply_chain_v49 as sc
from tools import package_release_v49 as pkg

ROOT=Path(__file__).resolve().parents[1]

class SupplyChainPolicies(unittest.TestCase):
    def test_audit_action_sha_and_lock(self):
        r=sc.audit()
        self.assertTrue(r['passed'])
        self.assertEqual(r['action_references'],18)
        self.assertEqual(len(r['pinned_action_types']),5)
    def _root(self,folder):
        root=Path(folder)
        (root/'ci').mkdir();(root/'.github/workflows').mkdir(parents=True)
        for rel in ('ci/actions_pins.json','ci/toolchain.json','package.json','package-lock.json','.github/workflows/test.yml'):
            p=root/rel;p.write_bytes((ROOT/rel).read_bytes())
        return root
    def test_mutable_action_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=self._root(d);p=r/'.github/workflows/test.yml'
            p.write_text(p.read_text().replace('actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8','actions/checkout@v5'))
            with self.assertRaisesRegex(ValueError,'mutable'):sc.audit(root=r)
    def test_unapproved_action_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=self._root(d);p=r/'.github/workflows/test.yml'
            p.write_text(p.read_text()+'\n      - uses: evil/action@'+'a'*40+'\n')
            with self.assertRaisesRegex(ValueError,'unapproved'):sc.audit(root=r)
    def test_lock_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=self._root(d);p=r/'package-lock.json';v=json.loads(p.read_text())
            v['packages']['node_modules/typescript']['integrity']='sha512-evil';p.write_text(json.dumps(v))
            with self.assertRaisesRegex(ValueError,'unlocked'):sc.audit(root=r)
    def test_dependency_script_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=self._root(d);p=r/'package.json';v=json.loads(p.read_text());v['scripts']={'preinstall':'node bad.js'};p.write_text(json.dumps(v))
            with self.assertRaisesRegex(ValueError,'package lock'):sc.audit(root=r)
    def test_no_global_npm_install(self):
        with tempfile.TemporaryDirectory() as d:
            r=self._root(d);p=r/'.github/workflows/test.yml'
            p.write_text(p.read_text()+'\n      - run: npm install -g something\n')
            with self.assertRaisesRegex(ValueError,'locked npm'):sc.audit(root=r)

class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.tmp.name)
        cls.archive=cls.root/pkg.ZIP_NAME
        cls.pkg=pkg.make_package(cls.archive)
        cls.statement=cls.root/'provenance.json'
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_archive_format(self):
        self.assertEqual(self.pkg['toolkit_version'],'4.9')
        self.assertTrue(pkg.verify_package(self.archive)['verified_integrity'])
    def test_file_manifest_integrity(self):
        with zipfile.ZipFile(self.archive) as z:
            data=json.loads(z.read(pkg.NAME+'/'+pkg.MANIFEST))
        self.assertEqual(data['toolkit_version'],'4.9')
        self.assertFalse(data['signed'])
    def test_packager_refuses_private_key_files(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d);(fake/'private.pem').write_text('this would be secret')
            with patch.object(pkg,'ROOT',fake):
                with self.assertRaisesRegex(ValueError,'potential secret'):pkg.files_to_release()
    def test_tampered_archive_rejected(self):
        damaged=self.root/'damaged.zip'
        buf=bytearray(self.archive.read_bytes());buf[120]^=1;damaged.write_bytes(buf)
        with self.assertRaises((ValueError,zipfile.BadZipFile,KeyError)):pkg.verify_package(damaged)
    def test_unsigned_provenance_roundtrip(self):
        self.statement.unlink(missing_ok=True)
        sc.create_provenance(self.archive,self.statement,commit='f'*40,run_id='1234')
        result=sc.verify_provenance(self.archive,self.statement)
        self.assertTrue(result['digest_matches'])
        self.assertFalse(result['source_authenticated'])
    def test_provenance_tampering(self):
        self.statement.unlink(missing_ok=True)
        sc.create_provenance(self.archive,self.statement)
        doc=json.loads(self.statement.read_text());doc['subject'][0]['digest']['sha256']='0'*64
        self.statement.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,'digest'):sc.verify_provenance(self.archive,self.statement)
    def test_provenance_rejects_invalid_sha(self):
        with self.assertRaisesRegex(ValueError,'source commit'):
            sc.create_provenance(self.archive,self.root/'invalid.json',commit='wrong',run_id='1234')
    def test_output_not_overwritten(self):
        path=self.root/'exists.json';path.write_text('existing')
        with self.assertRaisesRegex(ValueError,'new file'):sc.create_sbom(path)
    def test_sbom(self):
        out=self.root/'sbom.json';out.unlink(missing_ok=True)
        sc.create_sbom(out)
        v=json.loads(out.read_text())
        self.assertEqual(v['components'][0]['version'],'5.9.3')
        self.assertEqual(v['bomFormat'],'CycloneDX')
    def test_sign_requires_approval(self):
        with self.assertRaisesRegex(ValueError,'approve'):sc.sign(self.archive,self.root/'missing.pem',self.root/'not.sig')
    @unittest.skipUnless(shutil.which('openssl'),'OpenSSL required')
    def test_cryptographic_sign_and_reject_tampered(self):
        key=self.root/'test-private.pem';pub=self.root/'test-public.pem';sig=self.root/'sig.bin'
        subprocess.run(['openssl','ecparam','-name','prime256v1','-genkey','-noout','-out',str(key)],check=True,capture_output=True)
        subprocess.run(['openssl','pkey','-in',str(key),'-pubout','-out',str(pub)],check=True,capture_output=True)
        sig.unlink(missing_ok=True)
        sc.sign(self.archive,key,sig,approve=True)
        self.assertTrue(sc.verify_signature(self.archive,pub,sig)['signature_verified'])
        with tempfile.TemporaryDirectory() as d:
            copied=Path(d)/'tampered.zip'
            copied.write_bytes(self.archive.read_bytes()+b'evil')
            with self.assertRaisesRegex(ValueError,'verification failed'):
                sc.verify_signature(copied,pub,sig)
        with zipfile.ZipFile(self.archive) as z:
            names=z.namelist()
        self.assertFalse(any(n.endswith('test-private.pem') for n in names))
    def test_cli_audit(self):
        proc=subprocess.run([sys.executable,'fullstack.py','supply-chain','audit'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertTrue(json.loads(proc.stdout)['passed'])

if __name__=='__main__':unittest.main()
