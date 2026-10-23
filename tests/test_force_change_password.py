import unittest
from app import create_app
from models.user_model import UserModel
from core.database import get_db

class ForceChangePasswordTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_force_change_password_flow(self):
        # 1. Reset password for account 2 (or a test account) to '123'
        ok, msg = UserModel.reset_account_password(2, '123', audit_user={'id': 1, 'ho_ten': 'Admin', 'vai_tro': 'ADMIN'})
        self.assertTrue(ok)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, yeu_cau_doi_mat_khau FROM tai_khoan WHERE id = 2")
        acc = cursor.fetchone()
        conn.close()
        self.assertEqual(acc['yeu_cau_doi_mat_khau'], 1)

        # 2. Login with password '123'
        resp_login = self.client.post('/login', data={
            'username': acc['username'],
            'password': '123'
        }, follow_redirects=False)
        self.assertEqual(resp_login.status_code, 302)
        self.assertIn('/force-change-password', resp_login.headers.get('Location', ''))

        # 3. Follow redirect to force-change-password
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('force_change_password'))

        # Try to access admin dashboard -> must be redirected to /force-change-password
        resp_blocked = self.client.get('/admin/', follow_redirects=False)
        self.assertEqual(resp_blocked.status_code, 302)
        self.assertIn('/force-change-password', resp_blocked.headers.get('Location', ''))

        # 4. Attempt to set invalid password (e.g. too short or still 123)
        resp_invalid = self.client.post('/force-change-password', data={
            'new_password': '123',
            'confirm_password': '123'
        })
        self.assertEqual(resp_invalid.status_code, 200)

        # 5. Successfully update new password
        resp_success = self.client.post('/force-change-password', data={
            'new_password': 'NewPassword@2026',
            'confirm_password': 'NewPassword@2026'
        }, follow_redirects=False)
        self.assertEqual(resp_success.status_code, 302)

        # 6. Verify flag in DB cleared
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT yeu_cau_doi_mat_khau FROM tai_khoan WHERE id = 2")
        acc_updated = cursor.fetchone()
        conn.close()
        self.assertEqual(acc_updated['yeu_cau_doi_mat_khau'], 0)

if __name__ == '__main__':
    unittest.main()
