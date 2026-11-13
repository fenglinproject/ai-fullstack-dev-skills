"""V4.5 CI observation, shared worktree advisory lock and cross-repo sampling."""
import subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from tools.remote_ci_v45 import verify
from tools.worktree_lock_v45 import status, acquire, release
from tools.repo_comparison_v45 import compare

class V45Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='v45-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.repo=self.root/'repo';self.repo.mkdir()
        def git(*args):
            return subprocess.run(['git','-C',str(self.repo),*args],check=True,capture_output=True,text=True,timeout=8).stdout.strip()
        self.git=git
        git('init','-b','main');git('config','user.name','Fixture');git('config','user.email','fixture@invalid.example')
        (self.repo/'sample.py').write_text('print(1)\n','utf-8')
        git('add','.');git('commit','-m','initial')
        self.head=git('rev-parse','HEAD')
        git('remote','add','origin','https://github.com/example/project.git')

    def test_remote_preview_makes_no_network_call(self):
        with patch('tools.remote_ci_v45._call_gh',side_effect=AssertionError('network forbidden')):
            r=verify(self.repo,expected_head=self.head,required_checks=['unit'],execute=False)
        self.assertFalse(r['verified']);self.assertFalse(r['network_access'])

    def test_remote_check_success_with_authenticated_cli_response_mock(self):
        result={'total_count':1,'check_runs':[{'name':'unit','status':'completed','conclusion':'success','head_sha':self.head}]}
        with patch('tools.remote_ci_v45._call_gh',return_value=result) as c:
            r=verify(self.repo,expected_head=self.head,required_checks=['unit'],execute=True)
        self.assertTrue(r['verified']);self.assertEqual(c.call_count,1)

    def test_remote_absent_duplicate_failed_or_pending_fail_closed(self):
        base={'name':'unit','status':'completed','conclusion':'success','head_sha':self.head}
        for runs in ([],[base,base],[{**base,'conclusion':'failure'}],[{**base,'status':'in_progress'}]):
            with self.subTest(runs=runs):
                with patch('tools.remote_ci_v45._call_gh',return_value={'total_count':len(runs),'check_runs':runs}):
                    self.assertFalse(verify(self.repo,expected_head=self.head,required_checks=['unit'],execute=True)['verified'])

    def test_remote_incomplete_page_or_wrong_sha_rejected(self):
        base={'name':'unit','status':'completed','conclusion':'success','head_sha':self.head}
        with patch('tools.remote_ci_v45._call_gh',return_value={'total_count':101,'check_runs':[base]}):
            with self.assertRaisesRegex(ValueError,'incomplete'):verify(self.repo,expected_head=self.head,required_checks=['unit'],execute=True)
        with patch('tools.remote_ci_v45._call_gh',return_value={'total_count':1,'check_runs':[{**base,'head_sha':'0'*40}]}):
            with self.assertRaisesRegex(ValueError,'mismatch'):verify(self.repo,expected_head=self.head,required_checks=['unit'],execute=True)

    def test_remote_requires_current_exact_commit_and_valid_checks(self):
        with self.assertRaises(ValueError):verify(self.repo,expected_head='0'*40,required_checks=['unit'])
        with self.assertRaises(ValueError):verify(self.repo,expected_head=self.head,required_checks=[])
        with self.assertRaises(ValueError):verify(self.repo,expected_head=self.head,required_checks=['unit','unit'])

    def test_worktree_lock_requires_consent_and_token(self):
        with self.assertRaisesRegex(ValueError,'approve'):acquire(self.repo)
        info=acquire(self.repo,approved=True)
        self.assertTrue(status(self.repo)['locked'])
        self.assertNotIn('token',status(self.repo))
        with self.assertRaises(ValueError):acquire(self.repo,approved=True)
        with self.assertRaises(ValueError):release(self.repo,'0'*64)
        self.assertTrue(release(self.repo,info['release_token'])['released'])
        self.assertFalse(status(self.repo)['locked'])

    def test_linked_worktree_sees_same_reservation(self):
        linked=self.root/'linked'
        self.git('worktree','add','-b','another',str(linked))
        info=acquire(self.repo,approved=True)
        try:
            self.assertTrue(status(linked)['locked'])
            with self.assertRaises(ValueError):acquire(linked,approved=True)
            self.assertTrue(release(linked,info['release_token'])['released'])
        finally:
            if status(self.repo)['locked']:release(self.repo,info['release_token'])
        self.assertFalse(status(self.repo)['locked'])

    def test_corrupt_lock_must_not_be_stolen(self):
        loc=self.repo/'.git'/'ai-fullstack-v45-write.lock'
        loc.write_text('broken','utf-8')
        with self.assertRaises(ValueError):status(self.repo)
        with self.assertRaises(ValueError):acquire(self.repo,approved=True)

    def test_compare_two_real_local_repos(self):
        other=self.root/'other';other.mkdir()
        subprocess.run(['git','-C',str(other),'init','-b','main'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(other),'config','user.name','Fixture'],check=True)
        subprocess.run(['git','-C',str(other),'config','user.email','fixture@invalid.example'],check=True)
        (other/'hello.txt').write_text('hello','utf-8')
        subprocess.run(['git','-C',str(other),'add','.'],check=True)
        subprocess.run(['git','-C',str(other),'commit','-m','initial'],check=True,capture_output=True)
        result=compare([self.repo,other],samples=2)
        self.assertEqual(len(result['results']),2)
        self.assertTrue(all(x['stable_head'] for x in result['results']))
        with self.assertRaises(ValueError):compare([self.repo,self.repo])
        with self.assertRaises(ValueError):compare([self.repo],samples=21)

if __name__=='__main__':unittest.main()
