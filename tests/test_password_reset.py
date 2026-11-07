"""Isolated recovery checks; SMTP and production SQL are never contacted."""
import os
import re
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import patch

from flask import Flask
from core import password_reset as reset
from core.security import verify_password
from app import create_app


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, 'reset.sqlite')
        self.app = Flask(__name__)
        self.app.secret_key = 'isolated-password-reset-secret-32bytes'
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        with self.connection() as conn:
            conn.executescript('''CREATE TABLE tai_khoan (id INTEGER PRIMARY KEY, email TEXT, password TEXT, trang_thai INTEGER, yeu_cau_doi_mat_khau INTEGER);
                CREATE TABLE benh_nhan (tai_khoan_id INTEGER, email TEXT);
                CREATE TABLE nhan_vien (tai_khoan_id INTEGER, email TEXT);
                CREATE TABLE password_reset_otp (account_id INTEGER PRIMARY KEY, otp_hash TEXT, expires_at TEXT, sent_at TEXT, attempts INTEGER, verified INTEGER);
                INSERT INTO tai_khoan VALUES (1, 'patient@example.com', 'old-hash', 1, 0);''')
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
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        self.addCleanup(conn.close)
        return conn

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
