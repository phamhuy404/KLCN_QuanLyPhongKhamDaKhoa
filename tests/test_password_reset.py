"""Isolated recovery checks; SMTP and production SQL are never contacted."""
import os
import re
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from flask import Flask
from core import password_reset as reset
from core.security import verify_password, hash_password
from app import create_app


class MockCursor:
    def __init__(self, db):
        self.db = db
        self._last_row = None
        self._rows = []

    def execute(self, sql, params=()):
        sql_clean = re.sub(r'\s+', ' ', sql).strip()
        params = list(params)

        if "SELECT DISTINCT t.id FROM tai_khoan t" in sql_clean:
            email = params[0] if params else None
            matching = [t for t in self.db['tai_khoan'] if t['email'].lower() == (email or '').lower() and t.get('trang_thai') == 1]
            self._rows = [{'id': m['id']} for m in matching]
            self._last_row = self._rows[0] if self._rows else None

        elif "SELECT otp_hash, expires_at, sent_at, attempts, verified FROM password_reset_otp" in sql_clean:
            acc_id = params[0] if params else None
            matching = [o for o in self.db['password_reset_otp'] if o['account_id'] == acc_id]
            self._rows = matching
            self._last_row = matching[0] if matching else None

        elif "DELETE FROM password_reset_otp" in sql_clean:
            acc_id = params[0] if params else None
            self.db['password_reset_otp'] = [o for o in self.db['password_reset_otp'] if o['account_id'] != acc_id]
            self._rows = []
            self._last_row = None

        elif "INSERT INTO password_reset_otp" in sql_clean:
            # (account_id, otp_hash, expires_at, sent_at, attempts, verified)
            acc_id, otp_h, exp_at, sent_at = params[0], params[1], params[2], params[3]
            self.db['password_reset_otp'].append({
                'account_id': acc_id,
                'otp_hash': otp_h,
                'expires_at': exp_at,
                'sent_at': sent_at,
                'attempts': 0,
                'verified': 0
            })
            self._rows = []
            self._last_row = None

        elif "UPDATE password_reset_otp SET attempts=attempts+1" in sql_clean:
            acc_id = params[0] if params else None
            for o in self.db['password_reset_otp']:
                if o['account_id'] == acc_id:
                    o['attempts'] += 1
            self._rows = []
            self._last_row = None

        elif "UPDATE password_reset_otp SET verified=1" in sql_clean:
            acc_id = params[0] if params else None
            for o in self.db['password_reset_otp']:
                if o['account_id'] == acc_id:
                    o['verified'] = 1
            self._rows = []
            self._last_row = None

        elif "UPDATE tai_khoan SET password=" in sql_clean:
            pwd, acc_id = params[0], params[1]
            for t in self.db['tai_khoan']:
                if t['id'] == acc_id:
                    t['password'] = pwd
                    t['yeu_cau_doi_mat_khau'] = 0
            self._rows = []
            self._last_row = None

        elif "UPDATE password_reset_otp SET expires_at=" in sql_clean:
            exp_at = params[0]
            for o in self.db['password_reset_otp']:
                o['expires_at'] = exp_at

        elif "SELECT otp_hash FROM password_reset_otp" in sql_clean:
            self._rows = self.db['password_reset_otp']
            self._last_row = self._rows[0] if self._rows else None

        elif "SELECT attempts FROM password_reset_otp" in sql_clean:
            self._rows = self.db['password_reset_otp']
            self._last_row = self._rows[0] if self._rows else None

        elif "SELECT password FROM tai_khoan" in sql_clean:
            self._rows = self.db['tai_khoan']
            self._last_row = self._rows[0] if self._rows else None

        elif "SELECT COUNT(*) FROM password_reset_otp" in sql_clean:
            cnt = len(self.db['password_reset_otp'])
            self._rows = [{0: cnt, 'cnt': cnt}]
            self._last_row = self._rows[0]

        return self

    def fetchone(self):
        return self._last_row

    def fetchall(self):
        return self._rows


class MockConnection:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return MockCursor(self.db)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    def execute(self, sql, params=()):
        c = self.cursor()
        return c.execute(sql, params)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.mock_db = {
            'tai_khoan': [{'id': 1, 'email': 'patient@example.com', 'password': 'old-hash', 'trang_thai': 1, 'yeu_cau_doi_mat_khau': 0}],
            'benh_nhan': [{'tai_khoan_id': 1, 'email': 'patient@example.com'}],
            'nhan_vien': [],
            'password_reset_otp': []
        }
        self.app = Flask(__name__)
        self.app.secret_key = 'isolated-password-reset-secret-32bytes'
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)

        self.db_patch = patch.object(reset, 'get_db', side_effect=self.connection)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.sent_codes = []

        def send_mail(address, subject, html):
            self.assertEqual(address, 'patient@example.com')
            self.sent_codes.append(re.search(r'>([0-9]{6})</div>', html).group(1))
            return True, 'ok'

        self.mail_patch = patch.object(reset.NotificationService, 'send_email', side_effect=send_mail)
        self.mail_patch.start()
        self.addCleanup(self.mail_patch.stop)

    def connection(self):
        return MockConnection(self.mock_db)

    def test_send_verify_reset_consumes_code_and_hashes_password(self):
        result = reset.send_otp('Patient@Example.com')
        self.assertEqual(result['expires_in'], 300)
        code = self.sent_codes[-1]
        with self.connection() as conn:
            row = conn.execute('SELECT otp_hash FROM password_reset_otp').fetchone()
            self.assertNotEqual(row['otp_hash'], code)
        with self.assertRaises(reset.ResetError) as wrong:
            reset.verify_otp('patient@example.com', '999999' if code != '999999' else '888888')
        self.assertEqual(wrong.exception.code, 'INVALID_OTP')
        with self.connection() as conn:
            self.assertEqual(conn.execute('SELECT attempts FROM password_reset_otp').fetchone()['attempts'], 1)
        with self.assertRaises(reset.ResetError) as unverified:
            reset.reset_password('patient@example.com', code, 'new-password', 'new-password')
        self.assertEqual(unverified.exception.code, 'OTP_NOT_VERIFIED')
        reset.verify_otp('patient@example.com', code)
        reset.reset_password('patient@example.com', code, 'new-password', 'new-password')
        with self.connection() as conn:
            password = conn.execute('SELECT password FROM tai_khoan').fetchone()['password']
            self.assertTrue(verify_password(password, 'new-password'))
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM password_reset_otp').fetchone()[0], 0)

    def test_unknown_email_cooldown_and_expiry(self):
        with self.assertRaises(reset.ResetError) as missing:
            reset.send_otp('missing@example.com')
        self.assertEqual(missing.exception.code, 'EMAIL_NOT_FOUND')
        reset.send_otp('patient@example.com')
        with self.assertRaises(reset.ResetError) as cooldown:
            reset.send_otp('patient@example.com')
        self.assertEqual(cooldown.exception.code, 'RESEND_COOLDOWN')
        with self.connection() as conn:
            conn.execute('UPDATE password_reset_otp SET expires_at=?',
                         ((reset._utc_now() - timedelta(seconds=1)).isoformat(),))
        with self.assertRaises(reset.ResetError) as expired:
            reset.verify_otp('patient@example.com', self.sent_codes[-1])
        self.assertEqual(expired.exception.code, 'OTP_EXPIRED')

    def test_web_and_mobile_routes_share_recovery_flow(self):
        app = create_app({'TESTING': True, 'SECRET_KEY': self.app.secret_key,
                          'DATABASE_CONNECTION_FACTORY': self.connection})
        client = app.test_client()
        page = client.get('/forgot-password')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Quên mật khẩu'.encode(), page.data)
        with client.session_transaction() as session:
            csrf = session['password_reset_csrf']
        page = client.post('/forgot-password', data={
            'csrf_token': csrf, 'action': 'send', 'email': 'patient@example.com'})
        self.assertEqual(page.status_code, 200)
        self.assertIn('Xác thực mã OTP'.encode(), page.data)
        code = self.sent_codes[-1]
        response = client.post('/api/v1/mobile/auth/forgot-password/verify-otp',
                               json={'email': 'patient@example.com', 'otp_code': code})
        self.assertEqual(response.status_code, 200)
        response = client.post('/api/v1/mobile/auth/forgot-password/reset',
                               json={'email': 'patient@example.com', 'otp_code': code,
                                     'new_password': 'new-password', 'confirm_password': 'new-password'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])


if __name__ == '__main__':
    unittest.main()
