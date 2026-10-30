"""Real MSSQL only; no fixtures without separately confirmed disposable DB."""
import unittest
from unittest.mock import patch
from tests import test_scheduling_safety as scheduling


class MobileAuthMssqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scheduling.SchedulingTests.setUpClass.__func__(cls)

    connection = scheduling.SchedulingTests.connection
    tearDown = scheduling.SchedulingTests.tearDown

    def setUp(self):
        scheduling.SchedulingTests.setUp(self)
        self.app.config['MOBILE_TOKEN_SECRET'] = 'isolated-mobile-mssql-test-signing-key-32'
        self.keeper.execute('ALTER TABLE benh_nhan ADD co_tai_khoan INT DEFAULT 1')
        self.keeper.commit()

    def login_mobile(self, identifier='fixture_1', password='IsolatedPassword123!'):
        return self.client.post('/api/v1/mobile/auth/login',json=dict(identifier=identifier,password=password))

    def test_register_mobile_then_login_website_same_account_and_patient(self):
        payload = dict(ho_ten='Mobile Patient',sdt='0912345678',ngay_sinh='1990-01-02',gioi_tinh='Nam',
                       email='mobile@example.test',password='SharedSecret123!')
        response = self.client.post('/api/v1/mobile/auth/register',json=payload)
        self.assertEqual(response.status_code,201,response.get_json())
        identity = response.get_json()['user']
        self.assertNotEqual(identity['account_id'],identity['patient_id'])
        self.assertEqual(self.client.post('/api/v1/mobile/auth/register',json=payload).status_code,409)
        web = self.client.post('/login',data={'username':payload['sdt'],'password':payload['password']})
        self.assertEqual(web.status_code,302)
        with self.client.session_transaction() as session:
            self.assertEqual(session['user']['id'],identity['account_id'])
            self.assertEqual(session['user']['patient_id'],identity['patient_id'])

    def test_login_invalid_role_password_locked_and_missing_profile(self):
        for identifier,password,status in [('fixture_1','wrong',401),('fixture_3','IsolatedPassword123!',403),
                                           ('fixture_8','IsolatedPassword123!',401),('fixture_9','IsolatedPassword123!',401)]:
            result = self.login_mobile(identifier,password)
            self.assertEqual(result.status_code,status,result.get_json())

    def test_token_expired_logout_and_locked_after_issue(self):
        result = self.login_mobile()
        self.assertEqual(result.status_code,200,result.get_json())
        token = result.get_json()['access_token']
        headers = {'Authorization':'Bearer '+token}
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=headers).status_code,200)
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=0 WHERE id=1')
        self.keeper.commit()
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=headers).status_code,401)
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=1 WHERE id=1')
        self.keeper.commit()
        for _ in range(2):
            self.assertEqual(self.client.post('/api/v1/mobile/auth/logout',headers=headers).status_code,200)
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=headers).status_code,401)
        with patch('core.mobile_auth.time.time',return_value=1000000):
            expired = self.login_mobile().get_json()['access_token']
        with patch('core.mobile_auth.time.time',return_value=1003601):
            response = self.client.get('/api/v1/mobile/auth/me',headers={'Authorization':'Bearer '+expired})
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.get_json()['error_code'],'TOKEN_EXPIRED')


if __name__ == '__main__':
    unittest.main()
