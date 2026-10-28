"""Mock SQL protocol unit/contract tests, NOT MSSQL integration."""
import json
import unittest
from unittest.mock import patch
from app import create_test_app
from core.security import hash_password
from models.user_model import UserModel


class Connection:
    def __init__(self, fixture):
        self.fixture, self.pending, self.rows = fixture, [], []
    def cursor(self):
        return self
    def execute(self, sql, params=()):
        self.fixture['sql'].append(sql)
        if 'calendar_lock_result' in sql:
            self.rows = [{'calendar_lock_result':0}]
        elif 'SELECT DISTINCT t.id, t.password' in sql:
            self.rows = [{'id':11,'password':self.fixture['password']}] if params[0] in ('patient','0912345678','patient@example.test') else []
        elif 'SELECT id FROM benh_nhan WHERE tai_khoan_id' in sql:
            self.rows = [{'id':101}] if self.fixture.get('profile',True) else []
        elif 'SELECT password FROM tai_khoan' in sql:
            self.rows = [{'password':self.fixture['password']}]
        elif "action='MOBILE_LOGOUT'" in sql:
            self.rows = [{'id':1}] if params[1] in self.fixture['revoked'] else []
        elif 'INSERT INTO audit_log' in sql:
            self.pending.append(json.loads(params[-1])['jti'])
            self.rows = []
        elif 'UNION ALL SELECT id FROM benh_nhan' in sql:
            self.rows = [{'id':11}] if self.fixture.get('duplicate') else []
        elif 'SELECT id FROM tai_khoan WHERE username' in sql:
            self.rows = [{'id':11}]
        else:
            raise AssertionError('Unexpected mocked SQL protocol: '+sql)
        return self
    def fetchone(self):
        return self.rows.pop(0) if self.rows else None
    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows
    def commit(self):
        if self.fixture.get('commit_failure'):
            raise RuntimeError('simulated commit failure')
        self.fixture['revoked'].update(self.pending)
        self.pending.clear()
    def rollback(self):
        self.fixture['rollback'] += 1
        self.pending.clear()
    def close(self):
        pass


class MobileAuthContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = hash_password('Secret123!')

    def setUp(self):
        self.fixture = dict(password=self.password,revoked=set(),sql=[],rollback=0)
        self.user = dict(id=11,patient_id=101,vai_tro='BENHNHAN',ho_ten='Test Patient',
                         sdt='0912345678',email='patient@example.test',ma_benh_nhan='BN_TEST')
        self.app = create_test_app({'DATABASE_CONNECTION_FACTORY':lambda:Connection(self.fixture),
                                    'SECRET_KEY':'isolated-mobile-contract-secret-32-characters'})
        self.client = self.app.test_client()
        self.identity = patch.object(UserModel,'get_session_user',side_effect=lambda _:self.user)
        self.identity.start()
        self.addCleanup(self.identity.stop)
        self.forbid = patch('pyodbc.connect',side_effect=AssertionError('Real database forbidden'))
        self.forbid.start()
        self.addCleanup(self.forbid.stop)

    def login(self, **changes):
        return self.client.post('/api/v1/mobile/auth/login',json=dict(identifier='patient',password='Secret123!',**changes))

    def token(self):
        response = self.login()
        self.assertEqual(response.status_code,200,response.get_json())
        return response.get_json()['access_token']

    def headers(self, token):
        return {'Authorization':'Bearer '+token}

    def test_login_me_contract_and_no_web_session(self):
        response = self.login()
        data = response.get_json()
        self.assertEqual(response.status_code,200,data)
        self.assertEqual(data['user']['account_id'],11)
        self.assertEqual(data['user']['patient_id'],101)
        self.assertNotEqual(data['user']['account_id'],data['user']['patient_id'])
        self.assertEqual(data['token_type'],'Bearer')
        self.assertEqual(data['expires_in'],3600)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        result = self.client.get('/api/v1/mobile/auth/me',headers=self.headers(data['access_token']))
        self.assertEqual(result.status_code,200,result.get_json())
        self.assertEqual(result.get_json()['user'],data['user'])
        self.assertNotIn('password',json.dumps(data))
        with self.client.session_transaction() as session:
            self.assertNotIn('logged_in',session)

    def test_wrong_password_unknown_account_role_and_profile(self):
        response = self.client.post('/api/v1/mobile/auth/login',json={'identifier':'patient','password':'wrong'})
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.get_json()['error_code'],'INVALID_CREDENTIALS')
        self.user['vai_tro'] = 'BACSI'
        self.assertEqual(self.login().status_code,403)
        self.user = None
        self.assertEqual(self.login().status_code,401)

    def test_expired_tampered_and_missing_tokens(self):
        with patch('core.mobile_auth.time.time',return_value=1000000):
            token = self.token()
        with patch('core.mobile_auth.time.time',return_value=1003601):
            response = self.client.get('/api/v1/mobile/auth/me',headers=self.headers(token))
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.get_json()['error_code'],'TOKEN_EXPIRED')
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me').status_code,401)
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(token+'tampered')).status_code,401)

    def test_locked_deleted_password_changed_and_missing_profile(self):
        token = self.token()
        self.user = None
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(token)).status_code,401)
        self.user = dict(id=11,patient_id=101,vai_tro='BENHNHAN')
        self.fixture['profile'] = False
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(token)).status_code,401)
        self.fixture['profile'] = True
        self.fixture['password'] = 'changed-password-hash'
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(token)).status_code,401)

    def test_logout_is_persistent_idempotent_and_revokes_only_one_session(self):
        first, second = self.token(), self.token()
        for _ in range(2):
            response = self.client.post('/api/v1/mobile/auth/logout',headers=self.headers(first))
            self.assertEqual(response.status_code,200,response.get_json())
        self.assertEqual(len(self.fixture['revoked']),1)
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(first)).status_code,401)
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(second)).status_code,200)

    def test_logout_commit_failure_does_not_report_revocation(self):
        token = self.token()
        self.fixture['commit_failure'] = True
        response = self.client.post('/api/v1/mobile/auth/logout',headers=self.headers(token))
        self.assertEqual(response.status_code,503)
        self.assertFalse(response.get_json()['success'])
        self.assertEqual(len(self.fixture['revoked']),0)

    def test_locked_account_can_revoke_its_signed_token(self):
        token = self.token()
        user, self.user = self.user, None
        response = self.client.post('/api/v1/mobile/auth/logout',headers=self.headers(token))
        self.assertEqual(response.status_code,200,response.get_json())
        self.user = user
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me',headers=self.headers(token)).status_code,401)

    def test_weak_mobile_secret_and_revocation_storage_failure_issue_no_token(self):
        self.app.config['MOBILE_TOKEN_SECRET'] = 'weak'
        response = self.login()
        self.assertEqual(response.status_code,503)
        self.assertNotIn('access_token',response.get_json())
        self.app.config['MOBILE_TOKEN_SECRET'] = 'isolated-mobile-contract-signing-key-32'
        with patch('core.mobile_auth.revoked',side_effect=RuntimeError('revocation unavailable')):
            response = self.login()
        self.assertEqual(response.status_code,503)
        self.assertNotIn('access_token',response.get_json())

    def test_register_reuses_web_model_and_rolls_back_commit_failure(self):
        payload = dict(ho_ten='Test Patient',sdt='0912345678',ngay_sinh='1990-01-02',gioi_tinh='Nam',password='Secret123!',email='patient@example.test')
        with patch.object(UserModel,'register_patient',return_value=(True,'registered')) as register:
            response = self.client.post('/api/v1/mobile/auth/register',json=payload)
            self.assertEqual(response.status_code,201,response.get_json())
            self.assertEqual(register.call_args.kwargs,dict(ngay_sinh='1990-01-02',gioi_tinh='Nam'))
            self.fixture['commit_failure'] = True
            response = self.client.post('/api/v1/mobile/auth/register',json=payload)
            self.assertEqual(response.status_code,503)
            self.assertNotIn('access_token',response.get_json())

    def test_duplicate_account_and_invalid_registration(self):
        payload = dict(ho_ten='Test Patient',sdt='0912345678',ngay_sinh='1990-01-02',gioi_tinh='Nam',password='Secret123!')
        self.fixture['duplicate'] = True
        response = self.client.post('/api/v1/mobile/auth/register',json=payload)
        self.assertEqual(response.status_code,409,response.get_json())
        self.assertEqual(response.get_json()['error_code'],'ACCOUNT_EXISTS')
        for changes in ({'ngay_sinh':'2099-01-01'},{'ngay_sinh':'02/01/1990'},{'sdt':'invalid'},{'password':'123'},{'ho_ten':'Patient 123'},{'email':'bad'}):
            response = self.client.post('/api/v1/mobile/auth/register',json=dict(payload,**changes))
            self.assertEqual(response.status_code,400,response.get_json())

    def test_malformed_json_and_cookie_cannot_authorize_me(self):
        self.assertEqual(self.client.post('/api/v1/mobile/auth/login',data='{',content_type='application/json').status_code,400)
        with self.client.session_transaction() as session:
            session.update(logged_in=True,user=self.user)
        self.assertEqual(self.client.get('/api/v1/mobile/auth/me').status_code,401)


if __name__ == '__main__':
    unittest.main()
