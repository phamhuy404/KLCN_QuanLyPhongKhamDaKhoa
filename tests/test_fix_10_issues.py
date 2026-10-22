import unittest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from core.database import get_db
from core.security import is_safe_redirect_url, generate_csrf_token, validate_csrf_token
from models.user_model import UserModel
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.notification_model import NotificationModel
import config

class TestFix10Issues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    # =========================================================================
    # LỖI 1: API đặt lịch khám yêu cầu đăng nhập và danh tính xác thực
    # =========================================================================
    def test_01_booking_without_login_rejected(self):
        """API đặt lịch khám không đăng nhập phải bị từ chối 401"""
        res = self.client.post('/api/appointment/book', json={
            'chuyen_khoa_id': 1,
            'ngay_hen': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'gio_hen': '10:00'
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data['success'])

    def test_02_booking_patient_spoofing_prevented(self):
        """Bệnh nhân tự đặt lịch: patient_id từ client bị bỏ qua, hệ thống dùng patient_id từ session"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 100,
                'username': 'benhnhan_test',
                'vai_tro': 'BENHNHAN',
                'patient_id': 2
            }

        tomorrow = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        # Client cố tình gửi patient_id = 999 để giả mạo bệnh nhân khác
        res = self.client.post('/api/appointment/book', json={
            'patient_id': 999,
            'chuyen_khoa_id': 1,
            'ngay_hen': tomorrow,
            'gio_hen': '10:00:00',
            'ly_do': 'Khám định kỳ bảo mật'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        # Xác minh trong DB lịch hẹn được tạo cho patient_id = 2 chứ KHÔNG PHẢI 999
        ma_lh = data.get('ma_lich_hen')
        appt = AppointmentModel.get_by_code(ma_lh)
        self.assertIsNotNone(appt)
        self.assertEqual(appt['benh_nhan_id'], 2)

    def test_03_booking_no_patient_profile_rejected(self):
        """Tài khoản BENHNHAN không liên kết hồ sơ bệnh nhân nào phải bị từ chối 400"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 999999,
                'username': 'unlinked_user',
                'vai_tro': 'BENHNHAN',
                'patient_id': None
            }

        res = self.client.post('/api/appointment/book', json={
            'chuyen_khoa_id': 1,
            'ngay_hen': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'gio_hen': '10:00:00'
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('chưa được liên kết', data['message'])

    def test_04_booking_unauthorized_role_rejected(self):
        """Tài khoản vai trò không được phép đặt lịch (DUOCSI) phải bị từ chối 403"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 101,
                'username': 'duocsi_test',
                'vai_tro': 'DUOCSI'
            }

        res = self.client.post('/api/appointment/book', json={
            'patient_id': 1,
            'chuyen_khoa_id': 1,
            'ngay_hen': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'gio_hen': '10:00:00'
        })
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # LỖI 2: Portal bệnh nhân không dùng ID mặc định và kiểm soát truy cập
    # =========================================================================
    def test_05_patient_portal_staff_redirected(self):
        """Nhân viên (ADMIN, LETAN, BACSI) vào portal bệnh nhân phải bị chuyển hướng về admin dashboard"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'vai_tro': 'ADMIN'
            }

        res = self.client.get('/patient/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin', res.headers.get('Location', ''))

    def test_06_patient_update_profile_non_patient_rejected(self):
        """API update profile từ chối nếu không phải vai trò BENHNHAN"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 2,
                'username': 'bs_nam',
                'vai_tro': 'BACSI',
                'bac_si_id': 1
            }

        res = self.client.post('/api/patient/update-profile', json={'ho_ten': 'Hacker'})
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # LỖI 3: API đổi lịch và hủy lịch kiểm soát quyền theo vai trò
    # =========================================================================
    def test_07_reschedule_other_patient_rejected(self):
        """Bệnh nhân cố đổi lịch hẹn của bệnh nhân khác bị từ chối"""
        # Tạo lịch hẹn cho patient_id = 1
        future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        ok, appt_code = AppointmentModel.create(
            patient_id=1, chuyen_khoa_id=1, bac_si_id=1,
            ngay_hen=future_date, gio_hen='09:00:00', ly_do='Khám tim mạch'
        )
        self.assertTrue(ok)
        appt = AppointmentModel.get_by_code(appt_code)
        appt_id = appt['id']

        # Đăng nhập với tư cách Bệnh nhân khác (patient_id = 2)
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 50,
                'username': 'patient_attacker',
                'vai_tro': 'BENHNHAN',
                'patient_id': 2
            }

        new_date = (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d')
        res = self.client.post('/api/appointment/reschedule', json={
            'appointment_id': appt_id,
            'ngay_hen': new_date,
            'gio_hen': '14:00:00'
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('chính mình', data['message'])

    def test_08_cancel_unauthorized_role_rejected(self):
        """Vai trò không được phép hủy lịch (DUOCSI) bị từ chối 403"""
        future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        ok, appt_code = AppointmentModel.create(
            patient_id=1, chuyen_khoa_id=1, bac_si_id=1,
            ngay_hen=future_date, gio_hen='10:30:00', ly_do='Khám tổng quát'
        )
        self.assertTrue(ok)
        appt = AppointmentModel.get_by_code(appt_code)
        appt_id = appt['id']

        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 60,
                'username': 'duocsi_user',
                'vai_tro': 'DUOCSI'
            }

        res = self.client.post('/api/appointment/cancel', json={
            'appointment_id': appt_id,
            'reason': 'Hủy trái phép'
        })
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # LỖI 4: API tra cứu lịch bác sĩ import datetime và validate ngày
    # =========================================================================
    def test_09_doctor_schedule_availability_dates(self):
        """Tra cứu lịch bác sĩ hoạt động tốt khi có và không có tham số date, bắt lỗi khi sai định dạng"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'vai_tro': 'ADMIN'
            }

        # 1. Không truyền date -> tự động lấy ngày hiện tại mà không bị NameError datetime
        res = self.client.get('/api/doctors/schedule-availability?department_id=1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('doctors', data)

        # 2. Truyền date hợp lệ
        res2 = self.client.get('/api/doctors/schedule-availability?department_id=1&date=2026-10-30')
        self.assertEqual(res2.status_code, 200)

        # 3. Truyền date sai định dạng -> trả về lỗi 400
        res3 = self.client.get('/api/doctors/schedule-availability?department_id=1&date=invalid-date')
        self.assertEqual(res3.status_code, 400)
        data3 = res3.get_json()
        self.assertFalse(data3['success'])
        self.assertIn('định dạng', data3['message'])

    # =========================================================================
    # LỖI 6: Tìm kiếm bệnh nhân theo tham số search và an toàn SQL
    # =========================================================================
    def test_10_patient_search_functionality(self):
        """Chức năng tìm kiếm bệnh nhân theo từ khóa họ tên, SĐT, CCCD an toàn qua parameterized SQL"""
        # 1. Tìm theo tên
        results = PatientModel.search('Nam')
        self.assertIsInstance(results, list)

        # 2. Tìm từ khóa không tồn tại
        empty_res = PatientModel.search('XYZ_NON_EXISTENT_PATIENT_99999')
        self.assertEqual(len(empty_res), 0)

        # 3. Route /admin/patients nhận và xử lý tham số search
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN'}

        res = self.client.get('/admin/patients?search=Nam')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Nam', res.data)

    # =========================================================================
    # LỖI 7: API và Model thông báo hoạt động chính xác
    # =========================================================================
    def test_11_notification_api_and_model(self):
        """API /api/notifications trả về dữ liệu thật và số lượng chưa đọc"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN'}

        res = self.client.get('/api/notifications')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('notifications', data)
        self.assertIn('unread_count', data)
        self.assertIsInstance(data['unread_count'], int)

    # =========================================================================
    # LỖI 8: CSRF protection và logout sử dụng POST
    # =========================================================================
    def test_12_logout_method_post_and_get_rejected(self):
        """Logout qua GET bị từ chối 405 Method Not Allowed; logout qua POST thành công xóa session"""
        # GET request bị từ chối
        res_get = self.client.get('/logout')
        self.assertEqual(res_get.status_code, 405)

        # POST request với session đăng nhập
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN'}

        res_post = self.client.post('/logout')
        self.assertEqual(res_post.status_code, 302)

        # Xác minh session đã bị xóa hoàn toàn
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('logged_in'))
            self.assertIsNone(sess.get('user'))

    def test_13_csrf_validation_logic(self):
        """Kiểm tra logic tạo và xác thực token CSRF"""
        with app.test_request_context():
            token = generate_csrf_token()
            self.assertTrue(len(token) >= 32)
            self.assertTrue(validate_csrf_token(token))
            self.assertFalse(validate_csrf_token('invalid_token_123456'))
            self.assertFalse(validate_csrf_token(''))

    # =========================================================================
    # LỖI 9: Cấu hình SECRET_KEY và DEBUG Mode
    # =========================================================================
    def test_14_config_security_rules(self):
        """Kiểm tra SECRET_KEY không rỗng và DEBUG tuân thủ cấu hình"""
        self.assertIsNotNone(config.SECRET_KEY)
        self.assertTrue(len(config.SECRET_KEY) > 10)
        self.assertIsInstance(config.DEBUG, bool)

    # =========================================================================
    # LỖI 10: Chống tấn công Open Redirect
    # =========================================================================
    def test_15_open_redirect_validation(self):
        """Kiểm tra hàm is_safe_redirect_url phát hiện chính xác URL độc hại và nội bộ"""
        with app.test_request_context(base_url='http://localhost:5000/'):
            # URL nội bộ an toàn -> Hợp lệ
            self.assertTrue(is_safe_redirect_url('/admin/dashboard'))
            self.assertTrue(is_safe_redirect_url('/patient/booking'))
            self.assertTrue(is_safe_redirect_url('/patient/records?tab=history'))

            # URL bên ngoài hoặc độc hại -> Bị chặn
            self.assertFalse(is_safe_redirect_url('http://evil.com'))
            self.assertFalse(is_safe_redirect_url('https://attacker.site/steal'))
            self.assertFalse(is_safe_redirect_url('//evil.com/fake'))
            self.assertFalse(is_safe_redirect_url('\\\\evil.com\\fake'))
            self.assertFalse(is_safe_redirect_url('javascript:alert(1)'))
            self.assertFalse(is_safe_redirect_url(None))
            self.assertFalse(is_safe_redirect_url(''))

    def test_16_login_redirect_behavior(self):
        """Kiểm tra luồng đăng nhập điều hướng an toàn và từ chối next độc hại"""
        # Đăng nhập với next = 'http://attacker.com'
        res = self.client.post('/login?next=http://attacker.com', data={
            'username': 'admin',
            'password': 'Password@123' # Thử tài khoản
        })
        # Nếu đăng nhập thành công, redirect KHÔNG ĐƯỢC là http://attacker.com
        if res.status_code == 302:
            location = res.headers.get('Location', '')
            self.assertNotIn('attacker.com', location)
            self.assertTrue(location.startswith('/') or 'localhost' in location or '127.0.0.1' in location)

if __name__ == '__main__':
    unittest.main()
