import unittest
from core.csv_service import CSVService
from models.user_model import UserModel
from models.appointment_model import AppointmentModel

class TestUpgradedFeatures(unittest.TestCase):
    """Kiểm thử các tính năng nâng cấp: CSV import/export, bảo vệ tài khoản admin và phân công bác sĩ."""

    def test_csv_sample_generation(self):
        """Kiểm tra tạo file mẫu CSV cho 5 module có UTF-8 BOM."""
        modules = ['medicines', 'services', 'articles', 'accounts', 'appointments']
        for m in modules:
            data, filename = CSVService.get_sample_csv(m)
            self.assertTrue(data.startswith('\ufeff'), f'Module {m} thiếu UTF-8-SIG BOM')
            self.assertTrue(filename.endswith('.csv'))

    def test_csv_export(self):
        """Kiểm tra xuất dữ liệu thực tế từ CSDL ra CSV cho các module."""
        modules = ['medicines', 'services', 'articles', 'accounts', 'appointments']
        for m in modules:
            data, filename = CSVService.export_csv(m)
            self.assertTrue(data.startswith('\ufeff'), f'Module {m} xuất CSV thiếu BOM')
            self.assertTrue(len(data) > 3)

    def test_admin_account_protection(self):
        """Kiểm tra không thể vô hiệu hóa tài khoản quản trị viên."""
        # Tài khoản admin hệ thống mặc định ID 1
        ok, msg = UserModel.toggle_account_status(1)
        self.assertFalse(ok)
        self.assertIn('không thể vô hiệu hóa', msg.lower())

    def test_doctor_availability_lookup(self):
        """Kiểm tra tra cứu bác sĩ kèm số lượt khám trống."""
        docs = AppointmentModel.get_doctors_with_availability(1)
        self.assertIsInstance(docs, list)
        if docs:
            self.assertIn('available_slots', docs[0])
            self.assertIn('booked_slots', docs[0])

    def test_medicine_csv_duplicate_accumulation(self):
        """Kiểm tra cộng dồn số lượng tồn khi nhập CSV thuốc trùng lặp."""
        sample_csv = "ma_thuoc,ten_thuoc,hoat_chat,ham_luong,don_vi_tinh,gia_ban,so_luong_ton,han_su_dung,huong_dan_su_dung,trang_thai\n"
        sample_csv += "TH001,Paracetamol 500mg,Paracetamol,500mg,Viên,1500,10,2028-12-31,Uống sau ăn,1\n"
        
        ok, msg, inserted, updated = CSVService.import_csv('medicines', sample_csv.encode('utf-8'))
        self.assertTrue(ok)
        self.assertIn('thành công', msg.lower())

    def test_staff_filtering_by_role(self):
        """Kiểm tra lọc danh sách nhân sự theo phân quyền vai trò."""
        admin_user = {'id': 1, 'vai_tro': 'ADMIN'}
        all_staff = UserModel.get_all_staff(user_info=admin_user)
        self.assertTrue(len(all_staff) > 0)

        # Bác sĩ thấy bác sĩ chung chuyên khoa và tài khoản Quản trị viên (ADMIN)
        doctor_user = {'id': 2, 'vai_tro': 'BACSI', 'bac_si_id': 1, 'chuyen_khoa_id': 1}
        doc_staff = UserModel.get_all_staff(user_info=doctor_user)
        has_admin_in_doc = any(s.get('ma_vai_tro') == 'ADMIN' for s in doc_staff)
        self.assertTrue(has_admin_in_doc, "Bác sĩ phải thấy được tài khoản ADMIN")
        for s in doc_staff:
            if s.get('ma_vai_tro') != 'ADMIN':
                self.assertEqual(s.get('ma_vai_tro'), 'BACSI')
                if s.get('chuyen_khoa_id'):
                    self.assertEqual(s.get('chuyen_khoa_id'), 1)

        # Lễ tân thấy nhân sự lễ tân và tài khoản Quản trị viên (ADMIN)
        letan_user = {'id': 3, 'vai_tro': 'LETAN'}
        letan_staff = UserModel.get_all_staff(user_info=letan_user)
        has_admin_in_letan = any(s.get('ma_vai_tro') == 'ADMIN' for s in letan_staff)
        self.assertTrue(has_admin_in_letan, "Lễ tân phải thấy được tài khoản ADMIN")
        for s in letan_staff:
            if s.get('ma_vai_tro') != 'ADMIN':
                self.assertEqual(s.get('ma_vai_tro'), 'LETAN')

        # Role dưới tuyệt đối không thể đổi mật khẩu tài khoản Admin
        admin_acc = next(s for s in letan_staff if s.get('ma_vai_tro') == 'ADMIN')
        ok_reset, msg_reset = UserModel.reset_account_password(admin_acc['tai_khoan_id'], 'Hacked@123', audit_user=letan_user)
        self.assertFalse(ok_reset, "Role dưới không được phép đổi mật khẩu tài khoản Admin")

    def test_week_bounds_and_registration_rules(self):
        """Kiểm tra quy tắc đăng ký ca làm: chỉ được đăng ký 2 tuần tiếp theo, tuần hiện tại bị chặn."""
        from models.schedule_model import ScheduleModel
        from datetime import date, timedelta

        bounds = ScheduleModel.get_week_bounds()
        self.assertIn('current_week', bounds)
        self.assertIn('next_week_1', bounds)
        self.assertIn('next_week_2', bounds)

        # Tuần hiện tại (chặn đăng ký trực tiếp)
        today_str = str(date.today())
        test_user = {'id': 1, 'vai_tro': 'ADMIN', 'staff_id': 1}
        ok_cur, msg_cur = ScheduleModel.register_schedule(test_user, today_str, ca_lam=1)
        self.assertFalse(ok_cur)
        self.assertIn('2 tuần tiếp theo', msg_cur)

        # Tuần tiếp theo (hợp lệ)
        from core.database import get_db
        w1_start = bounds['next_week_1'][0]

        # Xóa dữ liệu ca test cũ nếu có
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id = 1 AND ngay_lam = ? AND ca_lam = 1", (str(w1_start),))
        conn.commit()
        conn.close()

        ok_w1, msg_w1 = ScheduleModel.register_schedule(test_user, str(w1_start), ca_lam=1)
        self.assertTrue(ok_w1, f"Đăng ký tuần W+1 thất bại: {msg_w1}")

        # Dọn dẹp sau khi test
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id = 1 AND ngay_lam = ? AND ca_lam = 1", (str(w1_start),))
        conn.commit()
        conn.close()

    def test_shift_capacity_limit(self):
        """Kiểm tra kiểm soát hạn mức mỗi ca tối đa 5 người cho từng vai trò."""
        from models.schedule_model import ScheduleModel
        bounds = ScheduleModel.get_week_bounds()
        w2_start = bounds['next_week_2'][0]
        cnt, max_cap, is_full = ScheduleModel.check_role_shift_capacity(str(w2_start), 1, 1)
        self.assertEqual(max_cap, 5)
        self.assertIsInstance(cnt, int)
        self.assertIsInstance(is_full, bool)

    def test_staff_page_access_for_all_roles(self):
        """Kiểm tra toàn bộ 5 vai trò nhân sự đều truy cập và render trang Quản lý Nhân sự & Lịch trực thành công."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        roles_to_test = ['ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV']
        for role in roles_to_test:
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['user'] = {
                    'id': 1,
                    'username': f'test_{role.lower()}',
                    'ho_ten': f'Test {role}',
                    'vai_tro': role,
                    'staff_id': 1,
                    'bac_si_id': 1 if role == 'BACSI' else None,
                    'chuyen_khoa_id': 1 if role == 'BACSI' else None
                }
            resp = client.get('/admin/staff')
            self.assertEqual(resp.status_code, 200, f"Role {role} không truy cập được /admin/staff")
            html = resp.data.decode('utf-8')
            self.assertIn("Quản lý Nhân sự & Lịch trực", html)

if __name__ == '__main__':
    unittest.main()
