"""V4.6 cooperative worktree gating and interrupted transaction recovery."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.cli import init
from orchestrator.git_collab import branch,commit
from orchestrator.workflow import apply,verify,_load_change,_json_write,_hash
from orchestrator.recovery_v46 import recover_prepared,recover_commit
from orchestrator.write_guard_v46 import write_guard,git_common_dir
from tools.worktree_lock_v45 import acquire,release

ROOT=Path(__file__).resolve().parents[1]

class V46Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='v46-')
        self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name)/'repo';self.project.mkdir()
        self.git('init','-b','main')
        self.git('config','user.name','Fixture')
        self.git('config','user.email','fixture@invalid.example')
        (self.project/'src').mkdir()
        self.file=self.project/'src/hello.py'
        self.file.write_text('def greet():\n    return "red"\n','utf-8')
        self.git('add','src/hello.py');self.git('commit','-m','initial')
        init(self.project)
        (self.project/'tests').mkdir()
        (self.project/'tests/test_ok.py').write_text('import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n','utf-8')
        (self.project/'.ai/checks.json').write_text(json.dumps({'checks':[
            {'name':'unit','cwd':'.','args':['python','-m','unittest','discover','-s','tests'],
             'enabled':True,'timeout_seconds':15}]}),'utf-8')
        self.git('add','tests/test_ok.py');self.git('commit','-m','add trusted tests')
    def git(self,*args):
        return subprocess.run(['git','-C',str(self.project),*args],capture_output=True,text=True,check=True,timeout=10).stdout.strip()
    def proposal(self):
        return {'schema_version':3,'task_id':'V46-A','summary':'Change button color label',
                'changes':[{'path':'src/hello.py','action':'replace',
                  'expected_sha256':_hash(self.file.read_bytes()),
                  'old_text':'"red"','new_text':'"blue"'}]}
    def applied(self):
        return apply(self.project,self.proposal(),approved=True)['change_id']
    def prepared(self):
        cid=self.applied()
        manifest,record=_load_change(self.project,cid)
        record['status']='prepared'
        _json_write(manifest,record)
        return cid

    def test_shared_common_dir_and_reservation_refuses_unauthorized_write(self):
        linked=Path(self.temp.name)/'linked'
        self.git('worktree','add','-b','linked',str(linked))
        self.assertEqual(git_common_dir(self.project),git_common_dir(linked))
        lease=acquire(self.project,approved=True)
        try:
            with self.assertRaisesRegex(ValueError,'matching token'):
                apply(self.project,self.proposal(),approved=True)
            cid=apply(self.project,self.proposal(),approved=True,
                      worktree_token=lease['release_token'])['change_id']
            self.assertIsInstance(cid,str)
        finally:
            release(linked,lease['release_token'])

    def test_prepared_preview_and_explicit_rollback(self):
        cid=self.prepared()
        report=recover_prepared(self.project,cid)
        self.assertTrue(report['safe_to_restore'])
        self.assertEqual(report['files'][0]['state'],'after')
        self.assertIn('blue',self.file.read_text('utf-8'))
        result=recover_prepared(self.project,cid,approved=True)
        self.assertEqual(result['status'],'aborted')
        self.assertIn('red',self.file.read_text('utf-8'))

    def test_prepared_incomplete_create_is_idempotent(self):
        p=self.proposal()
        p['changes'].append({'path':'src/new.py','action':'create','content':'print(2)\n'})
        cid=apply(self.project,p,approved=True)['change_id']
        (self.project/'src/new.py').unlink()
        path,record=_load_change(self.project,cid)
        record['status']='prepared';_json_write(path,record)
        result=recover_prepared(self.project,cid,approved=True)
        self.assertTrue(result['source_rollback'])
        self.assertIn('red',self.file.read_text('utf-8'))
        self.assertFalse((self.project/'src/new.py').exists())

    def test_prepared_modified_source_rejected_without_overwrite(self):
        cid=self.prepared()
        self.file.write_text('user later edits\n','utf-8')
        self.assertFalse(recover_prepared(self.project,cid)['safe_to_restore'])
        with self.assertRaisesRegex(ValueError,'refuse'):
            recover_prepared(self.project,cid,approved=True)
        self.assertEqual(self.file.read_text('utf-8'),'user later edits\n')

    def test_prepared_corrupt_backup_refused(self):
        cid=self.prepared()
        path,record=_load_change(self.project,cid)
        record['files'][0]['backup_base64']='bad!!!'
        _json_write(path,record)
        with self.assertRaisesRegex(ValueError,'backup'):
            recover_prepared(self.project,cid,approved=True)

    def test_interrupted_commit_after_git_commit_can_be_reconciled(self):
        branch(self.project,'ai/recover',approved=True)
        cid=self.applied()
        self.assertTrue(verify(self.project,cid,execute=True)['all_passed'])
        from orchestrator import git_collab
        write_original=git_collab._json_write
        calls=[]
        def fail_after_git(path,doc):
            calls.append(1)
            if len(calls)==2:
                raise OSError('simulated process death after Git commit')
            return write_original(path,doc)
        with patch('orchestrator.git_collab._json_write',side_effect=fail_after_git):
            with self.assertRaisesRegex(OSError,'simulated process death'):
                commit(self.project,cid,'Fix blue label',approved=True)
        head=self.git('rev-parse','HEAD')
        self.assertEqual(_load_change(self.project,cid)[1]['status'],'applied')
        pending=recover_commit(self.project,cid)
        self.assertEqual(pending['state'],'committed_unrecorded')
        self.assertEqual(pending['commit'],head)
        res=recover_commit(self.project,cid,approved=True)
        self.assertEqual(res['status'],'committed')
        self.assertEqual(res['git_commit'],head)
        self.assertEqual(head,self.git('rev-parse','HEAD'))

    def test_uncommitted_transaction_only_clears_intent(self):
        branch(self.project,'ai/no-commit',approved=True)
        cid=self.applied()
        report=verify(self.project,cid,execute=True)['report']
        path,record=_load_change(self.project,cid)
        from orchestrator.git_collab import _git
        head=_git(self.project,'rev-parse','HEAD')
        name=Path(report).name
        record['commit_transaction']={'schema_version':1,'state':'prepared','base_head':head,
           'branch':'ai/no-commit','message':'Fix blue label','paths':['src/hello.py'],
           'verified_report':name,
           'verified_report_sha256':_hash((self.project/'.ai/reports'/name).read_bytes()),
           'source_hashes':{'src/hello.py':record['files'][0]['after_sha256']}}
        _json_write(path,record)
        self.assertEqual(recover_commit(self.project,cid)['state'],'not_committed')
        self.assertEqual(recover_commit(self.project,cid,approved=True)['status'],'applied')

    def test_staged_changes_block_commit_recovery(self):
        branch(self.project,'ai/staged',approved=True)
        cid=self.applied();verify(self.project,cid,execute=True)
        path,record=_load_change(self.project,cid)
        report=record['last_verification']['report']
        record['commit_transaction']={'schema_version':1,'state':'prepared',
            'base_head':self.git('rev-parse','HEAD'),'branch':'ai/staged',
            'message':'Fix blue label','paths':['src/hello.py'],
            'verified_report':report,'verified_report_sha256':record['last_verification']['sha256'],
            'source_hashes':{'src/hello.py':record['files'][0]['after_sha256']}}
        _json_write(path,record)
        self.git('add','src/hello.py')
        with self.assertRaisesRegex(ValueError,'index has staged'):
            recover_commit(self.project,cid,approved=True)

    def test_cli_prepared_preview_is_read_only(self):
        cid=self.prepared()
        r=subprocess.run([sys.executable,str(ROOT/'fullstack.py'),'recover','prepared',
            '--project',str(self.project),'--change-id',cid],capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue(json.loads(r.stdout)['safe_to_restore'])
        self.assertIn('blue',self.file.read_text('utf-8'))

    def test_guard_fails_on_unsafe_reservation(self):
        lock=self.project/'.git/ai-fullstack-v45-write.lock'
        lock.write_text('broken','utf-8')
        with self.assertRaisesRegex(ValueError,'reservation'):
            apply(self.project,self.proposal(),approved=True)

    def test_bad_gate_symlink_refuses_write(self):
        gate=self.project/'.git/ai-fullstack-v46-operation.flock'
        gate.symlink_to(self.file)
        with self.assertRaisesRegex(ValueError,'unsafe write gate'):
            apply(self.project,self.proposal(),approved=True)
        self.assertIn('red',self.file.read_text('utf-8'))

    def test_recovery_requires_token_during_reservation(self):
        cid=self.prepared()
        lease=acquire(self.project,approved=True)
        try:
            with self.assertRaisesRegex(ValueError,'matching token'):
                recover_prepared(self.project,cid,approved=True)
            recovered=recover_prepared(self.project,cid,approved=True,
                                       worktree_token=lease['release_token'])
            self.assertEqual(recovered['status'],'aborted')
        finally:
            release(self.project,lease['release_token'])

    def test_prepared_create_with_user_content_never_removed(self):
        p=self.proposal()
        p['changes'].append({'path':'src/new.py','action':'create','content':'print(2)\n'})
        cid=apply(self.project,p,approved=True)['change_id']
        path,record=_load_change(self.project,cid)
        record['status']='prepared';_json_write(path,record)
        (self.project/'src/new.py').write_text('user edited this\n','utf-8')
        with self.assertRaisesRegex(ValueError,'refuse'):
            recover_prepared(self.project,cid,approved=True)
        self.assertEqual((self.project/'src/new.py').read_text('utf-8'),'user edited this\n')

    def test_pending_commit_corrupt_report_rejected(self):
        branch(self.project,'ai/report-hash',approved=True)
        cid=self.applied();verify(self.project,cid,execute=True)
        path,record=_load_change(self.project,cid)
        verified=record['last_verification']
        record['commit_transaction']={'schema_version':1,'state':'prepared',
          'base_head':self.git('rev-parse','HEAD'),'branch':'ai/report-hash',
          'message':'Fix blue label','paths':['src/hello.py'],
          'verified_report':verified['report'],'verified_report_sha256':verified['sha256'],
          'source_hashes':{'src/hello.py':record['files'][0]['after_sha256']}}
        _json_write(path,record)
        r=self.project/'.ai/reports'/verified['report']
        r.write_bytes(r.read_bytes()+b'altered')
        with self.assertRaisesRegex(ValueError,'evidence changed'):
            recover_commit(self.project,cid,approved=True)

    def test_gate_serializes_across_worktree_processes(self):
        linked=Path(self.temp.name)/'secondary'
        self.git('worktree','add','-b','secondary',str(linked))
        code='from orchestrator.write_guard_v46 import write_guard; from pathlib import Path; import time; import sys; '\
             'p=Path(sys.argv[1]); g=write_guard(p,timeout=3); g.__enter__(); print("LOCKED",flush=True); time.sleep(1); g.__exit__(None,None,None)'
        process=subprocess.Popen([sys.executable,'-c',code,str(self.project)],cwd=ROOT,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(),'LOCKED')
            with self.assertRaisesRegex(ValueError,'write gate'):
                with write_guard(linked,timeout=0):pass
        finally:
            process.communicate(timeout=10)
            self.assertEqual(process.returncode,0)

if __name__=='__main__':unittest.main()
