import tempfile
import unittest
from pathlib import Path
from backend.app import Store,handle

class TodoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.tmp.name)/'test.db')
    def tearDown(self):self.tmp.cleanup()
    def register(self,email='a@example.org'):
        status,result=handle(self.store,'POST','/api/register',data={'email':email,'password':'strong-passphrase'})
        self.assertEqual(status,201)
        return {'Authorization':'Bearer '+result['token']}
    def test_register_and_login(self):
        self.register()
        status,data=handle(self.store,'POST','/api/login',data={'email':'a@example.org','password':'strong-passphrase'})
        self.assertEqual(status,200);self.assertIn('token',data)
    def test_weak_password_rejected(self):
        status,_=handle(self.store,'POST','/api/register',data={'email':'a@example.org','password':'123'})
        self.assertEqual(status,400)
    def test_duplicate_email_conflict(self):
        self.register();status,_=handle(self.store,'POST','/api/register',data={'email':'a@example.org','password':'another-passphrase'})
        self.assertEqual(status,409)
    def test_wrong_password_denied(self):
        self.register();status,_=handle(self.store,'POST','/api/login',data={'email':'a@example.org','password':'wrong-password'})
        self.assertEqual(status,401)
    def test_auth_required(self):
        self.assertEqual(handle(self.store,'GET','/api/tasks')[0],401)
    def test_create_and_list(self):
        auth=self.register();status,item=handle(self.store,'POST','/api/tasks',auth,{'title':'Review Skills'})
        self.assertEqual(status,201)
        status,listed=handle(self.store,'GET','/api/tasks',auth)
        self.assertEqual(listed['tasks'][0]['title'],'Review Skills')
    def test_ownership_isolation(self):
        a=self.register();b=self.register('b@example.org')
        _,created=handle(self.store,'POST','/api/tasks',a,{'title':'secret'})
        self.assertEqual(handle(self.store,'GET','/api/tasks',b)[1]['tasks'],[])
        self.assertEqual(handle(self.store,'PATCH','/api/tasks/'+str(created['id']),b,{'done':True})[0],404)
        self.assertEqual(handle(self.store,'DELETE','/api/tasks/'+str(created['id']),b)[0],404)
    def test_done_and_delete(self):
        auth=self.register();_,task=handle(self.store,'POST','/api/tasks',auth,{'title':'do it'})
        path='/api/tasks/'+str(task['id'])
        self.assertEqual(handle(self.store,'PATCH',path,auth,{'done':True})[0],200)
        self.assertTrue(handle(self.store,'GET','/api/tasks',auth)[1]['tasks'][0]['done'])
        self.assertEqual(handle(self.store,'DELETE',path,auth)[0],200)
        self.assertFalse(handle(self.store,'GET','/api/tasks',auth)[1]['tasks'])
    def test_bad_title_rejected(self):
        auth=self.register();self.assertEqual(handle(self.store,'POST','/api/tasks',auth,{'title':' '})[0],400)
    def test_sql_injection_input_is_not_interpreted(self):
        auth=self.register();title="'); DROP TABLE tasks; --"
        self.assertEqual(handle(self.store,'POST','/api/tasks',auth,{'title':title})[0],201)
        self.assertEqual(handle(self.store,'GET','/api/tasks',auth)[1]['tasks'][0]['title'],title)
    def test_invalid_done_type(self):
        auth=self.register();_,task=handle(self.store,'POST','/api/tasks',auth,{'title':'task'})
        self.assertEqual(handle(self.store,'PATCH','/api/tasks/'+str(task['id']),auth,{'done':'yes'})[0],400)

if __name__=='__main__':unittest.main()
