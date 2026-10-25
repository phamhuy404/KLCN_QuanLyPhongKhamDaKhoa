import unittest
import random
from app import app
from core.database import get_db
from core.security import hash_password, verify_password
from models.user_model import UserModel
from models.patient_model import PatientModel
from models.medical_record_model import MedicalRecordModel
from models.appointment_model import AppointmentModel

class TestLoginPhoneAndConstraints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_schema_columns_exist(self):
        """Kiểm tra các cột mới tự động cập nhật trong schema và không báo lỗi 42S22."""
        conn = get_db()
        cursor = conn.cursor()
        
        # Test phieu_kham.hinh_anh_kham
        cursor.execute("SELECT TOP 1 hinh_anh_kham FROM phieu_kham")
        self.assertTrue(True)

        # Test bac_si.gioi_thieu
        cursor.execute("SELECT TOP 1 gioi_thieu, gia_kham FROM bac_si")
        self.assertTrue(True)

        # Test tai_khoan.yeu_cau_doi_mat_khau, sdt, email
        cursor.execute("SELECT TOP 1 yeu_cau_doi_mat_khau, sdt, email FROM tai_khoan")
        self.assertTrue(True)
        conn.close()

    def test_02_login_with_phone_number(self):
        """Kiểm tra người dùng có thể đăng nhập bằng Số điện thoại thay vì Username."""
        random_suffix = random.randint(1000000, 9999999)
        test_phone = f"091{random_suffix}"
        test_username = f"user_phone_{random_suffix}"
        test_pwd = "Password@123"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tai_khoan (vai_tro_id, username, password, sdt, trang_thai)
            VALUES (6, ?, ?, ?, 1)
        ''', (test_username, hash_password(test_pwd), test_phone))
        acc_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            # 1. Đăng nhập bằng username
            user_by_name = UserModel.authenticate(test_username, test_pwd)
            self.assertIsNotNone(user_by_name)
            self.assertEqual(user_by_name['id'], acc_id)

            # 2. Đăng nhập bằng số điện thoại
            user_by_phone = UserModel.authenticate(test_phone, test_pwd)
            self.assertIsNotNone(user_by_phone)
            self.assertEqual(user_by_phone['id'], acc_id)
        finally:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tai_khoan WHERE id = ?", (acc_id,))
            conn.commit()
            conn.close()

    def test_03_create_doctor_account_with_sdt_and_username_constraints(self):
        """Kiểm tra tạo bác sĩ với tên có học vị, mật khẩu 123, ràng buộc khoảng cách ở username và chống trùng SĐT."""
        random_suffix = random.randint(1000000, 9999999)
        test_phone = f"092{random_suffix}"
        test_name = "BS. CKII Nguyễn Văn Hùng"

        # 1. Tên đăng nhập chứa khoảng cách phải bị từ chối
        ok_space, msg_space = UserModel.create_doctor_account(
            ho_ten=test_name,
            sdt=test_phone,
            username="bs nguyen hung"
        )
        self.assertFalse(ok_space)
        self.assertIn("khoảng cách", msg_space.lower())

        # 2. Tạo bác sĩ với tên đăng nhập hợp lệ và tên có học hàm/học vị (có dấu chấm)
        valid_username = f"bs_hung_{random_suffix}"
        ok_create, msg_create = UserModel.create_doctor_account(
            ho_ten=test_name,
            sdt=test_phone,
            username=valid_username
        )
        self.assertTrue(ok_create, f"Lỗi tạo bác sĩ: {msg_create}")

        # 3. Kiểm tra thông tin trong CSDL: mật khẩu là 123
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, sdt FROM tai_khoan WHERE username = ?", (valid_username,))
        acc = cursor.fetchone()
        self.assertIsNotNone(acc)
        self.assertTrue(verify_password(acc['password'], '123'))
        self.assertEqual(acc['sdt'], test_phone)

        # 4. Kiểm tra chống trùng số điện thoại
        random_suffix2 = random.randint(1000000, 9999999)
        ok_dup, msg_dup = UserModel.create_doctor_account(
            ho_ten="ThS. Bác sĩ Khác",
            sdt=test_phone,
            username=f"bs_khac_{random_suffix2}"
        )
        self.assertFalse(ok_dup)
        self.assertIn("số điện thoại này đã được đăng ký", msg_dup.lower())

        # Dọn dẹp dữ liệu test
        cursor.execute("SELECT id FROM nhan_vien WHERE tai_khoan_id = ?", (acc['id'],))
        nv = cursor.fetchone()
        if nv:
            cursor.execute("DELETE FROM bac_si WHERE nhan_vien_id = ?", (nv['id'],))
            cursor.execute("DELETE FROM nhan_vien WHERE id = ?", (nv['id'],))
        cursor.execute("DELETE FROM tai_khoan WHERE id = ?", (acc['id'],))
        conn.commit()
        conn.close()

    def test_04_edit_username_constraints(self):
        """Kiểm tra cho phép sửa tên đăng nhập và ràng buộc không được chứa khoảng cách."""
        random_suffix = random.randint(1000000, 9999999)
        test_phone = f"093{random_suffix}"
        orig_username = f"nv_test_{random_suffix}"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tai_khoan (vai_tro_id, username, password, sdt, trang_thai)
            VALUES (2, ?, ?, ?, 1)
        ''', (orig_username, hash_password('123'), test_phone))
        acc_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO nhan_vien (tai_khoan_id, ma_nhan_vien, ho_ten, sdt, chuc_vu, trang_thai)
            VALUES (?, ?, N'Nhân Viên Test', ?, N'Tiếp tân', 1)
        ''', (acc_id, f"NV{random_suffix}", test_phone))
        conn.commit()
        conn.close()

        try:
            # 1. Thử đổi tên đăng nhập có chứa khoảng cách -> phải báo lỗi
            ok_sp, msg_sp = UserModel.update_staff_profile(acc_id, {
                'ho_ten': 'Nhân Viên Test',
                'username': 'nv test space'
            })
            self.assertFalse(ok_sp)
            self.assertIn("khoảng cách", msg_sp.lower())

            # 2. Đổi tên đăng nhập hợp lệ không chứa khoảng cách -> thành công
            new_username = f"nv_new_{random_suffix}"
            ok_valid, msg_valid = UserModel.update_staff_profile(acc_id, {
                'ho_ten': 'Nhân Viên Test',
                'username': new_username
            })
            self.assertTrue(ok_valid, f"Không cập nhật được username: {msg_valid}")

            # Xác minh tên đăng nhập mới trong DB
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM tai_khoan WHERE id = ?", (acc_id,))
            updated_acc = cursor.fetchone()
            conn.close()
            self.assertEqual(updated_acc['username'], new_username)
        finally:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM nhan_vien WHERE tai_khoan_id = ?", (acc_id,))
            cursor.execute("DELETE FROM tai_khoan WHERE id = ?", (acc_id,))
            conn.commit()
            conn.close()

    def test_05_cancel_appointment_with_id_or_appointment_id(self):
        """Kiểm tra API hủy lịch hẹn chấp nhận cả appointment_id hoặc id."""
        # Tạo lịch hẹn test
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 id FROM benh_nhan")
        bn = cursor.fetchone()
        bn_id = bn['id'] if bn else 1

        cursor.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, chuyen_khoa_id, ngay_hen, gio_hen, loai_lich_hen, ly_do_kham, trang_thai)
            VALUES (?, ?, 1, CAST(GETDATE() AS DATE), '09:00', 1, N'Test hủy lịch', N'Chờ khám')
        ''', (f"LH{random.randint(100000, 999999)}", bn_id))
        lh_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Gọi cancel bằng API client với body là { 'id': lh_id }
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 1,
                'ho_ten': 'Admin',
                'vai_tro': 'ADMIN'
            }

        res = self.client.post('/api/appointment/cancel', json={
            'id': lh_id,
            'ly_do': 'Khách hàng bận việc'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

        # Dọn dẹp
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lich_hen WHERE id = ?", (lh_id,))
        conn.commit()
        conn.close()

    def test_06_lab_orders_include_ma_bn(self):
        """Kiểm tra danh sách chỉ định cận lâm sàng có trường ma_bn không bị undefined."""
        orders = MedicalRecordModel.get_all_lab_orders()
        for o in orders[:5]:
            self.assertIn('ma_bn', o)
            self.assertTrue(o['ma_bn'], "ma_bn không được để trống hoặc None")

    def test_07_create_doctor_only_phone_and_complete_profile_later(self):
        """Kiểm tra Admin chỉ cần nhập SĐT tạo tài khoản, Bác sĩ tự điền họ tên khi đăng nhập lần đầu."""
        random_suffix = random.randint(1000000, 9999999)
        test_phone = f"096{random_suffix}"

        # 1. Admin tạo tài khoản chỉ bằng SĐT (không truyền ho_ten)
        ok_create, msg_create = UserModel.create_doctor_account(sdt=test_phone)
        self.assertTrue(ok_create, f"Không tạo được tài khoản bác sĩ bằng SĐT: {msg_create}")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, da_hoan_thien_ho_so FROM tai_khoan WHERE username = ?", (test_phone,))
        acc = cursor.fetchone()
        self.assertIsNotNone(acc)
        self.assertEqual(acc['da_hoan_thien_ho_so'], 0)

        # 2. Đăng xuất phiên admin trước đó nếu có và Bác sĩ đăng nhập lần đầu bằng SĐT và 123
        self.client.get('/logout')
        login_res = self.client.post('/login', data={
            'username': test_phone,
            'password': '123'
        }, follow_redirects=False)
        self.assertEqual(login_res.status_code, 302)
        self.assertIn('/admin/doctor/complete-profile', login_res.headers.get('Location', ''))

        # 3. Bác sĩ tự khai báo họ tên thật và hoàn tất hồ sơ
        actual_name = "BS. CKII Lê Minh Trí"
        complete_ok, complete_msg = UserModel.complete_doctor_profile(acc['id'], {
            'ho_ten': actual_name,
            'new_password': 'SecureDoctorPass@123',
            'confirm_password': 'SecureDoctorPass@123',
            'chuyen_khoa_id': 1,
            'hoc_vi': 'BS. CKII',
            'gioi_tinh': 1,
            'ngay_sinh': '1985-10-10',
            'cccd': '079085000123'
        })
        self.assertTrue(complete_ok, f"Lỗi hoàn thiện hồ sơ bác sĩ: {complete_msg}")

        # 4. Xác nhận họ tên thật đã được cập nhật thành công trong nhan_vien
        cursor.execute("SELECT ho_ten FROM nhan_vien WHERE tai_khoan_id = ?", (acc['id'],))
        nv_updated = cursor.fetchone()
        self.assertEqual(nv_updated['ho_ten'], actual_name)

        # Dọn dẹp
        cursor.execute("SELECT id FROM nhan_vien WHERE tai_khoan_id = ?", (acc['id'],))
        nv = cursor.fetchone()
        if nv:
            cursor.execute("DELETE FROM bac_si WHERE nhan_vien_id = ?", (nv['id'],))
            cursor.execute("DELETE FROM nhan_vien WHERE id = ?", (nv['id'],))
        cursor.execute("DELETE FROM tai_khoan WHERE id = ?", (acc['id'],))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()

