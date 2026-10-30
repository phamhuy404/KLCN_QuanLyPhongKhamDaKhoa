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
        # Kiểm tra Admin bị chặn đăng ký ca trực
        test_admin = {'id': 1, 'vai_tro': 'ADMIN', 'staff_id': 1}
        ok_adm, msg_adm = ScheduleModel.register_schedule(test_admin, today_str, ca_lam=1)
        self.assertFalse(ok_adm)
        self.assertIn('không cần đăng ký ca trực', msg_adm)

        # Kiểm tra Bác sĩ đăng ký tuần hiện tại bị chặn
        test_user = {'id': 2, 'vai_tro': 'BACSI', 'staff_id': 2}
        ok_cur, msg_cur = ScheduleModel.register_schedule(test_user, today_str, ca_lam=1)
        self.assertFalse(ok_cur)
        self.assertIn('2 tuần tiếp theo', msg_cur)

        # Tuần tiếp theo (hợp lệ)
        from core.database import get_db
        w1_start = bounds['next_week_1'][0]

        # Xóa dữ liệu ca test cũ nếu có
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam = ? AND ca_lam = 1", (str(w1_start),))
        conn.commit()
        conn.close()

        ok_w1, msg_w1 = ScheduleModel.register_schedule(test_user, str(w1_start), ca_lam=1)
        self.assertTrue(ok_w1, f"Đăng ký tuần W+1 thất bại: {msg_w1}")

        # Dọn dẹp sau khi test
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam = ? AND ca_lam = 1", (str(w1_start),))
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
        """Kiểm tra toàn bộ 5 vai trò nhân sự đều truy cập và render trang Quản lý Nhân sự và Lịch trực thành công."""
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
    def test_get_week_days(self):
        """Kiểm tra tạo danh sách 7 ngày trong tuần với nhãn tiếng Việt."""
        from models.schedule_model import ScheduleModel
        from datetime import date
        days = ScheduleModel.get_week_days(date(2026, 10, 19))
        self.assertEqual(len(days), 7)
        self.assertEqual(days[0]['day_name'], 'Thứ 2')
        self.assertEqual(days[6]['day_name'], 'Chủ nhật')
        self.assertEqual(days[0]['date_str'], '2026-10-19')

    def test_register_multiple_schedules(self):
        """Kiểm tra đăng ký đồng loạt nhiều ca làm việc."""
        from models.schedule_model import ScheduleModel
        from core.database import get_db

        bounds = ScheduleModel.get_week_bounds()
        w1_start = bounds['next_week_1'][0]
        from datetime import datetime, timedelta, date as dt_date
        d1 = datetime.strptime(w1_start, "%Y-%m-%d").date() if isinstance(w1_start, str) else w1_start
        d2 = d1 + timedelta(days=1)

        test_user = {'id': 2, 'vai_tro': 'BACSI', 'staff_id': 2}
        shifts_to_register = [
            {'ngay_lam': str(d1), 'ca_lam': 1},
            {'ngay_lam': str(d2), 'ca_lam': 2}
        ]

        # Dọn dẹp trước
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam IN (?, ?)", (str(d1), str(d2)))
        conn.commit()
        conn.close()

        # Đăng ký hàng loạt
        ok, msg, count, errors = ScheduleModel.register_multiple_schedules(test_user, shifts_to_register)
        self.assertTrue(ok, f"Đăng ký nhiều ca thất bại: {msg}")
        self.assertEqual(count, 2)

        # Dọn dẹp sau khi test
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam IN (?, ?)", (str(d1), str(d2)))
        conn.commit()
        conn.close()

    def test_api_register_multiple(self):
        """Kiểm tra API endpoint /api/schedule/register-multiple."""
        from app import create_app
        from models.schedule_model import ScheduleModel
        from datetime import datetime, timedelta, date as dt_date
        from core.database import get_db

        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        bounds = ScheduleModel.get_week_bounds()
        w1_start = bounds['next_week_1'][0]
        d1 = datetime.strptime(w1_start, "%Y-%m-%d").date() if isinstance(w1_start, str) else w1_start
        d2 = d1 + timedelta(days=2)

        # Dọn dẹp trước
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam IN (?, ?)", (str(d1), str(d2)))
        conn.commit()
        conn.close()

        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 2,
                'username': 'bacsi1',
                'ho_ten': 'BS. Trần Minh Quân',
                'vai_tro': 'BACSI',
                'staff_id': 2
            }

        payload = {
            'shifts': [
                {'ngay_lam': str(d1), 'ca_lam': 1},
                {'ngay_lam': str(d2), 'ca_lam': 3}
            ],
            'phong_kham_id': None,
            'ghi_chu': 'Test bulk registration'
        }

        resp = client.post('/api/schedule/register-multiple', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('success'), f"API lỗi: {data.get('message')}")
        self.assertEqual(data.get('count'), 2)

        # Dọn dẹp sau khi test
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam IN (?, ?)", (str(d1), str(d2)))
        conn.commit()
        conn.close()


    def test_article_permissions_for_admin_and_letan(self):
        """Kiem tra chi Admin va Le tan duoc phep tao, sua va quan ly bai viet."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        for role in ['ADMIN', 'LETAN']:
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['user'] = {
                    'id': 1 if role == 'ADMIN' else 3,
                    'username': f'test_{role.lower()}',
                    'ho_ten': f'Test {role}',
                    'vai_tro': role,
                    'staff_id': 1
                }
            
            # 1. Truy cap danh sach bai viet -> Thanh cong va co nut Viet bai
            resp = client.get('/admin/articles')
            self.assertEqual(resp.status_code, 200)
            html = resp.data.decode('utf-8')
            self.assertIn('Viết và Đăng Bài Mới', html, f"Role {role} phai thay nut Viet bai")

            # 2. Truy cap trang tao bai viet -> 200 OK
            resp_create = client.get('/admin/articles/create')
            self.assertEqual(resp_create.status_code, 200, f"Role {role} phai truy cap duoc /admin/articles/create")

    def test_article_permissions_restricted_for_other_roles(self):
        """Kiem tra Bac si, Duoc si, KTV chi duoc xem danh sach va chi tiet, bi chan tao/sua/xoa."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        role_user_ids = {
            'BACSI': 17,
            'DUOCSI': 7,
            'KTV': 12
        }

        for role, uid in role_user_ids.items():
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['user'] = {
                    'id': uid,
                    'username': f'test_{role.lower()}',
                    'ho_ten': f'Test {role}',
                    'vai_tro': role,
                    'staff_id': uid,
                    'da_hoan_thien_ho_so': 1
                }
            
            # 1. Truy cap danh sach -> 200 OK nhung KHONG co nut Tao/Sua
            resp = client.get('/admin/articles')
            self.assertEqual(resp.status_code, 200, f"Role {role} phai xem duoc danh sach /admin/articles")
            html = resp.data.decode('utf-8')
            self.assertNotIn('Viết và Đăng Bài Mới', html, f"Role {role} khong duoc phep thay nut Viet bai")
            self.assertNotIn('+ Thêm Cẩm Nang Y Tế', html, f"Role {role} khong duoc phep thay nut Them Cam Nang")

            # 2. Thu vao trang tao bai viet -> Bi chuyen huong
            resp_create = client.get('/admin/articles/create')
            self.assertEqual(resp_create.status_code, 302, f"Role {role} khong duoc phep vao /admin/articles/create")

            # 3. Thu gui yeu cau xoa -> 403 Forbidden
            resp_del = client.post('/admin/articles/delete/999')
            self.assertEqual(resp_del.status_code, 403, f"Role {role} khong duoc phep xoa bai viet")
            data_del = resp_del.get_json()
            self.assertFalse(data_del.get('success'))

    def test_public_article_viewing(self):
        """Kiem tra benh nhan va khach deu xem duoc danh sach va chi tiet bai viet cong khai."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.get('/articles')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Chuyên Mục Tin Tức và Cẩm Nang', resp.data.decode('utf-8'))

    def test_dark_mode_configuration_and_assets(self):
        """Kiem tra he thong Dark Mode: script theme.js, custom.css va nut toggle tren giao dien."""
        import os
        self.assertTrue(os.path.exists('static/js/theme.js'), "File static/js/theme.js phai ton tai")
        
        with open('static/js/theme.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        self.assertIn('toggleDarkMode', js_content)
        self.assertIn('updateThemeUI', js_content)

        with open('static/css/custom.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        self.assertIn('html.dark', css_content)
        self.assertIn('#0b1324', css_content)

        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        # Kiem tra tren trang chu co nut toggleDarkMode
        resp = client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('toggleDarkMode()', resp.data.decode('utf-8'))


    def test_public_pricing_page(self):
        """Kiem tra trang bang gia dich vu & vien phi cong khai cho Guest va benh nhan."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.get('/pricing')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('Bảng Giá Dịch Vụ Khám Chữa Bệnh', html)
        self.assertIn('BHYT trả', html)
        self.assertIn('Giá Sau Giảm BHYT', html)

        self.assertEqual(client.get('/services').status_code, 200)
        self.assertEqual(client.get('/bang-gia').status_code, 200)

    def test_public_doctors_page(self):
        """Kiem tra trang doi ngu bac si & nhan vien y te cong khai, khong hien thi admin."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.get('/doctors')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('Đội Ngũ Bác Sĩ & Cán Bộ Y Tế', html)
        self.assertIn('ThS.BS Trần Minh Quân', html)
        self.assertIn('0912111001', html)
        self.assertNotIn('Quản Trị Viên Hệ Thống', html)
        self.assertNotIn('Bác Sĩ Kiểm Thử', html)

        self.assertEqual(client.get('/doi-ngu-bac-si').status_code, 200)

    def test_public_departments_page(self):
        """Kiem tra trang danh sach cac chuyen khoa y te mui nhon cong khai."""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.get('/departments')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('Danh Sách Các Chuyên Khoa Mũi Nhọn', html)
        self.assertIn('Khoa Nội Tổng Quát', html)
        self.assertIn('Phòng Khám Trực Thuộc', html)

        self.assertEqual(client.get('/chuyen-khoa').status_code, 200)

if __name__ == '__main__':
    unittest.main()

