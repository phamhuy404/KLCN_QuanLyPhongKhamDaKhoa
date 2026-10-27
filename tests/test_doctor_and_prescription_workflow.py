import os
import sys
import unittest
import random
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from core.database import get_db
from core.security import verify_password
from models.user_model import UserModel
from models.appointment_model import AppointmentModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.medical_record_model import MedicalRecordModel

class DoctorAndPrescriptionWorkflowTestCase(unittest.TestCase):
    """Kiểm thử quy trình tạo bác sĩ, kích hoạt lần đầu và duyệt đơn thuốc tại bệnh viện."""

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_create_doctor_account_default_password_and_guard(self):
        """Kiểm tra admin tạo bác sĩ với mật khẩu mặc định 123 và cơ chế chặn truy cập khi chưa hoàn thiện hồ sơ."""
        random_suffix = random.randint(1000000, 9999999)
        test_phone = f"098{random_suffix}"
        test_name = "Bác Sĩ Kiểm Thử Quy Trình"
        test_email = f"bstest{random_suffix}@phongkham.vn"

        # 1. Admin tạo tài khoản bác sĩ
        ok, res_id = UserModel.create_doctor_account(
            ho_ten=test_name,
            sdt=test_phone,
            email=test_email,
            chuyen_khoa_id=1,
            audit_user={'id': 1, 'ho_ten': 'Admin Test'}
        )
        self.assertTrue(ok, f"Không tạo được tài khoản bác sĩ: {res_id}")

        # 2. Kiểm tra mật khẩu mặc định 123 trong CSDL
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, da_hoan_thien_ho_so FROM tai_khoan WHERE username = ?", (test_phone,))
        acc = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(acc)
        self.assertTrue(verify_password(acc['password'], '123'), "Mật khẩu mặc định phải là 123")
        self.assertEqual(acc['da_hoan_thien_ho_so'], 0, "Bác sĩ mới phải có cờ da_hoan_thien_ho_so = 0")

        # 3. Đăng nhập lần đầu bằng mật khẩu 123
        login_res = self.client.post('/login', data={
            'username': test_phone,
            'password': '123'
        }, follow_redirects=False)

        self.assertEqual(login_res.status_code, 302)
        self.assertIn('/admin/doctor/complete-profile', login_res.headers.get('Location', ''))

        # 4. Khi chưa hoàn thiện hồ sơ, truy cập trang admin khác phải bị điều hướng về complete-profile
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': acc['id'],
                'username': test_phone,
                'vai_tro': 'BACSI',
                'da_hoan_thien_ho_so': 0
            }

        dash_res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(dash_res.status_code, 302)
        self.assertIn('/admin/doctor/complete-profile', dash_res.headers.get('Location', ''))

        # Dọn dẹp tài khoản test
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM nhan_vien WHERE tai_khoan_id = ?", (acc['id'],))
        nv = cursor.fetchone()
        if nv:
            cursor.execute("DELETE FROM bac_si WHERE nhan_vien_id = ?", (nv['id'],))
            cursor.execute("DELETE FROM nhan_vien WHERE id = ?", (nv['id'],))
        cursor.execute("DELETE FROM tai_khoan WHERE id = ?", (acc['id'],))
        conn.commit()
        conn.close()

    def test_02_complete_doctor_profile_validation_and_unlock(self):
        """Kiểm tra ràng buộc đổi mật khẩu mới (khác 123, >= 6 ký tự) và mở khóa truy cập hệ thống."""
        random_suffix = random.randint(1000000, 9999999)
        test_phone = f"097{random_suffix}"
        test_name = "Bác Sĩ Kiểm Thử Ràng Buộc"

        ok, _ = UserModel.create_doctor_account(
            ho_ten=test_name,
            sdt=test_phone,
            chuyen_khoa_id=1
        )
        self.assertTrue(ok)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tai_khoan WHERE username = ?", (test_phone,))
        acc_id = cursor.fetchone()['id']
        conn.close()

        # Từ chối nếu mật khẩu mới trùng mật khẩu mặc định 123
        ok_fail1, msg1 = UserModel.complete_doctor_profile(acc_id, {
            'ho_ten': test_name,
            'new_password': '123',
            'confirm_password': '123'
        })
        self.assertFalse(ok_fail1)
        self.assertIn('không được trùng với mật khẩu mặc định', msg1.lower())

        # Từ chối nếu mật khẩu mới quá ngắn
        ok_fail2, msg2 = UserModel.complete_doctor_profile(acc_id, {
            'ho_ten': test_name,
            'new_password': '12345',
            'confirm_password': '12345'
        })
        self.assertFalse(ok_fail2)
        self.assertIn('6 ký tự', msg2.lower())

        # Thành công khi nhập mật khẩu mới hợp lệ
        new_valid_pwd = 'DoctorSecure@2026'
        ok_succ, msg_succ = UserModel.complete_doctor_profile(acc_id, {
            'ho_ten': f"{test_name} Upgraded",
            'new_password': new_valid_pwd,
            'confirm_password': new_valid_pwd,
            'chuyen_khoa_id': 2,
            'hoc_vi': 'Thạc sĩ Bác sĩ',
            'kinh_nghiem': '10 năm chuyên khoa'
        })
        self.assertTrue(ok_succ, msg_succ)

        # Kiểm tra cờ da_hoan_thien_ho_so đã cập nhật thành 1 và đăng nhập được bằng mật khẩu mới
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT da_hoan_thien_ho_so FROM tai_khoan WHERE id = ?", (acc_id,))
        self.assertEqual(cursor.fetchone()['da_hoan_thien_ho_so'], 1)
        conn.close()

        user_auth = UserModel.authenticate(test_phone, new_valid_pwd)
        self.assertIsNotNone(user_auth)
        self.assertEqual(user_auth['da_hoan_thien_ho_so'], 1)

        old_auth = UserModel.authenticate(test_phone, '123')
        self.assertIsNone(old_auth, "Mật khẩu cũ 123 không được phép đăng nhập nữa")

        # Dọn dẹp
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM nhan_vien WHERE tai_khoan_id = ?", (acc_id,))
        nv = cursor.fetchone()
        if nv:
            cursor.execute("DELETE FROM bac_si WHERE nhan_vien_id = ?", (nv['id'],))
            cursor.execute("DELETE FROM nhan_vien WHERE id = ?", (nv['id'],))
        cursor.execute("DELETE FROM tai_khoan WHERE id = ?", (acc_id,))
        conn.commit()
        conn.close()

    def test_03_doctor_activity_status_indicators(self):
        """Kiểm tra trường trạng thái hoạt động thực tế (is_active_now, trang_thai_hoat_dong)."""
        doctors = UserModel.get_all_doctors()
        self.assertIsInstance(doctors, list)
        self.assertGreater(len(doctors), 0)

        for doc in doctors:
            self.assertIn('is_active_now', doc)
            self.assertIn('trang_thai_hoat_dong', doc)
            self.assertIn(doc['trang_thai_hoat_dong'], ['Đang làm việc', 'Ngoài giờ làm việc'])
            if doc['is_active_now']:
                self.assertEqual(doc['trang_thai_hoat_dong'], 'Đang làm việc')
            else:
                self.assertEqual(doc['trang_thai_hoat_dong'], 'Ngoài giờ làm việc')

        # Kiểm tra API danh sách bác sĩ theo ca
        today_str = datetime.now().strftime('%Y-%m-%d')
        docs_shift, shift = AppointmentModel.get_doctors_by_shift(today_str, '08:30')
        self.assertIsInstance(docs_shift, list)
        for doc in docs_shift:
            self.assertIn('is_active_now', doc)
            self.assertIn('trang_thai_hoat_dong', doc)

    def test_04_prescription_purchase_options_and_approval_workflow(self):
        """Kiểm tra toàn diện quy trình duyệt đơn thuốc: Tiếp tân duyệt (chưa trừ kho), thanh toán hóa đơn, dược sĩ cấp phát (trừ kho)."""
        conn = get_db()
        cursor = conn.cursor()

        # Tìm bệnh nhân và thuốc có sẵn để tạo đơn thuốc test
        cursor.execute("SELECT TOP 1 id, tai_khoan_id, ho_ten FROM benh_nhan")
        bn = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id, ten_thuoc, so_luong_ton FROM thuoc WHERE so_luong_ton >= 10")
        med = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM phieu_kham")
        pk = cursor.fetchone()

        if not bn or not med or not pk:
            conn.close()
            self.skipTest("Cần ít nhất 1 bệnh nhân, 1 phiếu khám và 1 loại thuốc tồn kho >= 10")

        initial_stock = int(med['so_luong_ton'])
        med_id = med['id']
        pk_id = pk['id']
        bn_id = bn['id']

        # 1. Tạo đơn thuốc test
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc")
        next_dt_id = cursor.fetchone()['next_id']
        ma_don = f"DT_TEST_{next_dt_id}"

        cursor.execute('''
            INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, loi_dan, trang_thai)
            VALUES (?, ?, N'Uống theo hướng dẫn', N'Chờ bệnh nhân xác nhận mua')
        ''', (ma_don, pk_id))
        dt_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, cach_dung)
            VALUES (?, ?, 3, N'Ngày uống 2 lần')
        ''', (dt_id, med_id))
        conn.commit()
        conn.close()

        # 2. Bệnh nhân chọn "Tự mua ngoài"
        ok_outside, msg_outside = PharmacyModel.choose_medicine_purchase_option(dt_id, 'Tự mua ngoài')
        self.assertTrue(ok_outside)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trang_thai, hinh_thuc_mua FROM don_thuoc WHERE id = ?", (dt_id,))
        dt_row = cursor.fetchone()
        self.assertEqual(dt_row['trang_thai'], 'Mua ngoài')
        self.assertEqual(dt_row['hinh_thuc_mua'], 'Tự mua ngoài')

        # Kiểm tra tồn kho thuốc KHÔNG bị trừ khi mua ngoài
        cursor.execute("SELECT so_luong_ton FROM thuoc WHERE id = ?", (med_id,))
        self.assertEqual(int(cursor.fetchone()['so_luong_ton']), initial_stock)
        conn.close()

        # 3. Bệnh nhân chọn "Mua tại bệnh viện" -> Chuyển sang Chờ duyệt, sinh hóa đơn thuốc, CHƯA trừ kho
        ok_hosp, msg_hosp = PharmacyModel.choose_medicine_purchase_option(dt_id, 'Mua tại bệnh viện')
        self.assertTrue(ok_hosp)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trang_thai, hinh_thuc_mua FROM don_thuoc WHERE id = ?", (dt_id,))
        dt_row = cursor.fetchone()
        self.assertEqual(dt_row['trang_thai'], 'Chờ duyệt')
        self.assertEqual(dt_row['hinh_thuc_mua'], 'Mua tại bệnh viện')

        # Kiểm tra hóa đơn thuốc được sinh với trạng thái Chưa thanh toán
        cursor.execute("SELECT TOP 1 id, ma_hoa_don, trang_thai, trang_thai_nhan_thuoc FROM hoa_don WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%' AND trang_thai != N'Đã hủy' ORDER BY id DESC", (pk_id,))
        hd_row = cursor.fetchone()
        self.assertIsNotNone(hd_row)
        self.assertEqual(hd_row['trang_thai'], 'Chưa thanh toán')

        # Xác minh tồn kho vẫn CHƯA bị trừ tại bước này
        cursor.execute("SELECT so_luong_ton FROM thuoc WHERE id = ?", (med_id,))
        self.assertEqual(int(cursor.fetchone()['so_luong_ton']), initial_stock, "Chọn mua tại viện chưa được trừ kho ngay")
        conn.close()

        # 4. Tiếp tân / Admin duyệt đơn thuốc -> Đổi trạng thái 'Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy' (VẪN CHƯA trừ kho)
        reviewer = {'id': 1, 'ho_ten': 'Quản Trị Viên Tiếp Tân'}
        ok_appr, msg_appr = PharmacyModel.approve_prescription(dt_id, reviewer_user=reviewer)
        self.assertTrue(ok_appr, f"Duyệt đơn thuốc thất bại: {msg_appr}")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trang_thai, nguoi_duyet, ngay_duyet FROM don_thuoc WHERE id = ?", (dt_id,))
        dt_approved = cursor.fetchone()
        self.assertIn('Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy', dt_approved['trang_thai'])
        self.assertIsNotNone(dt_approved['nguoi_duyet'])
        self.assertIsNotNone(dt_approved['ngay_duyet'])

        # Xác minh: Tiếp tân và Admin duyệt đơn thì kho VẪN CHƯA bị trừ
        cursor.execute("SELECT so_luong_ton FROM thuoc WHERE id = ?", (med_id,))
        self.assertEqual(int(cursor.fetchone()['so_luong_ton']), initial_stock, "Tiếp tân/Admin duyệt đơn không được trừ kho")
        conn.close()

        # 5. Kiểm tra: Sau khi duyệt thì bệnh nhân KHÔNG được đổi sang mua ngoài nữa
        ok_switch, msg_switch = PharmacyModel.choose_medicine_purchase_option(dt_id, 'Tự mua ngoài')
        self.assertFalse(ok_switch, "Đơn thuốc đã duyệt không được phép đổi sang mua ngoài")

        # 6. Dược sĩ cấp phát khi CHƯA thanh toán -> Bị từ chối
        pharmacist = {'id': 4, 'ho_ten': 'Dược sĩ Kho'}
        ok_disp_fail, msg_disp_fail = PharmacyModel.dispense_prescription(dt_id, audit_user=pharmacist)
        self.assertFalse(ok_disp_fail, "Chưa thanh toán tiền thuốc không được cấp phát")

        # 7. Bệnh nhân / Thu ngân thanh toán hóa đơn tiền thuốc
        ok_pay, msg_pay = BillingModel.pay_invoice(hd_row['ma_hoa_don'], payment_method='Chuyển khoản VietQR', cashier_name='Cổng VietQR Trực Tuyến')
        self.assertTrue(ok_pay)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trang_thai, trang_thai_nhan_thuoc FROM hoa_don WHERE id = ?", (hd_row['id'],))
        hd_paid = cursor.fetchone()
        self.assertEqual(hd_paid['trang_thai'], 'Đã thanh toán')
        self.assertEqual(hd_paid['trang_thai_nhan_thuoc'], 'Chưa nhận thuốc')

        # Đơn thuốc cập nhật sang trạng thái 'Chờ nhận thuốc'
        cursor.execute("SELECT trang_thai FROM don_thuoc WHERE id = ?", (dt_id,))
        self.assertEqual(cursor.fetchone()['trang_thai'], 'Chờ nhận thuốc')
        conn.close()

        # 8. Quản lý kho dược bấm cấp phát thuốc -> Lúc này MỚI trừ số lượng kho và cập nhật Đã nhận thuốc
        ok_disp, msg_disp = PharmacyModel.dispense_prescription(dt_id, audit_user=pharmacist)
        self.assertTrue(ok_disp, f"Cấp phát thuốc thất bại: {msg_disp}")

        conn = get_db()
        cursor = conn.cursor()
        # Xác minh tồn kho ĐÃ bị trừ chính xác 3 viên sau khi dược sĩ phát
        cursor.execute("SELECT so_luong_ton FROM thuoc WHERE id = ?", (med_id,))
        stock_after = int(cursor.fetchone()['so_luong_ton'])
        self.assertEqual(stock_after, initial_stock - 3, "Tồn kho phải được trừ sau khi quản lý kho bấm cấp phát thuốc")

        # Xác minh đơn thuốc cập nhật thành 'Đã nhận thuốc'
        cursor.execute("SELECT trang_thai FROM don_thuoc WHERE id = ?", (dt_id,))
        self.assertEqual(cursor.fetchone()['trang_thai'], 'Đã nhận thuốc')

        # Xác minh trên hóa đơn của bệnh nhân cập nhật 'Đã nhận thuốc'
        cursor.execute("SELECT trang_thai_nhan_thuoc FROM hoa_don WHERE id = ?", (hd_row['id'],))
        self.assertEqual(cursor.fetchone()['trang_thai_nhan_thuoc'], 'Đã nhận thuốc')

        # 9. Dọn dẹp đơn thuốc test và hoàn lại số lượng tồn kho
        cursor.execute("UPDATE thuoc SET so_luong_ton = ? WHERE id = ?", (initial_stock, med_id))
        cursor.execute("DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id IN (SELECT id FROM hoa_don WHERE ma_hoa_don LIKE 'HDT%' AND phieu_kham_id = ?)", (pk_id,))
        cursor.execute("DELETE FROM hoa_don WHERE ma_hoa_don LIKE 'HDT%' AND phieu_kham_id = ?", (pk_id,))
        cursor.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (dt_id,))
        cursor.execute("DELETE FROM don_thuoc WHERE id = ?", (dt_id,))
        conn.commit()
        conn.close()


    def test_05_prescription_reject_workflow(self):
        """Kiểm tra quy trình Tiếp tân/Admin từ chối duyệt đơn thuốc: Hủy hóa đơn tiền thuốc, cập nhật trạng thái đơn."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 id, tai_khoan_id, ho_ten FROM benh_nhan")
        bn = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id, ten_thuoc, so_luong_ton FROM thuoc WHERE so_luong_ton >= 10")
        med = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM phieu_kham")
        pk = cursor.fetchone()

        if not bn or not med or not pk:
            conn.close()
            self.skipTest("Cần bệnh nhân, phiếu khám và thuốc tồn kho")

        initial_stock = int(med['so_luong_ton'])
        med_id = med['id']
        pk_id = pk['id']

        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc")
        next_dt_id = cursor.fetchone()['next_id']
        ma_don = f"DT_REJ_{next_dt_id}"

        cursor.execute('''
            INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, loi_dan, trang_thai)
            VALUES (?, ?, N'Uống theo hướng dẫn', N'Chờ bệnh nhân xác nhận mua')
        ''', (ma_don, pk_id))
        dt_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, cach_dung)
            VALUES (?, ?, 2, N'Ngày uống 1 viên')
        ''', (dt_id, med_id))
        conn.commit()
        conn.close()

        # Bệnh nhân chọn mua tại viện -> sinh hóa đơn HDT
        ok_hosp, _ = PharmacyModel.choose_medicine_purchase_option(dt_id, 'Mua tại bệnh viện')
        self.assertTrue(ok_hosp)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 id, ma_hoa_don, trang_thai FROM hoa_don WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%' AND trang_thai != N'Đã hủy' ORDER BY id DESC", (pk_id,))
        hd_row = cursor.fetchone()
        self.assertIsNotNone(hd_row)
        self.assertEqual(hd_row['trang_thai'], 'Chưa thanh toán')
        hd_id = hd_row['id']
        conn.close()

        # Tiếp tân từ chối duyệt đơn kèm lý do
        receptionist = {'id': 2, 'ho_ten': 'Lễ Tân Tuyết Mai'}
        reason_reject = 'Kho thuốc viện hiện đang hết mặt hàng này, vui lòng mua thuốc ngoài'
        ok_rej, msg_rej = PharmacyModel.reject_prescription(dt_id, reason=reason_reject, reviewer_user=receptionist)
        self.assertTrue(ok_rej, f"Từ chối đơn thất bại: {msg_rej}")

        # Xác minh: Đơn thuốc có trạng thái Bị từ chối duyệt
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trang_thai, ly_do_huy, nguoi_duyet FROM don_thuoc WHERE id = ?", (dt_id,))
        dt_after = cursor.fetchone()
        self.assertIn('Bị từ chối duyệt', dt_after['trang_thai'])
        self.assertEqual(dt_after['ly_do_huy'], reason_reject)
        self.assertEqual(dt_after['nguoi_duyet'], receptionist['ho_ten'])

        # Xác minh: Hóa đơn thuốc HDT tự động chuyển sang Đã hủy
        cursor.execute("SELECT trang_thai FROM hoa_don WHERE id = ?", (hd_id,))
        hd_after = cursor.fetchone()
        self.assertEqual(hd_after['trang_thai'], 'Đã hủy')

        # Xác minh: Tồn kho thuốc không bị ảnh hưởng
        cursor.execute("SELECT so_luong_ton FROM thuoc WHERE id = ?", (med_id,))
        self.assertEqual(int(cursor.fetchone()['so_luong_ton']), initial_stock)

        # Dọn dẹp
        cursor.execute("DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id = ?", (hd_id,))
        cursor.execute("DELETE FROM hoa_don WHERE id = ?", (hd_id,))
        cursor.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (dt_id,))
        cursor.execute("DELETE FROM don_thuoc WHERE id = ?", (dt_id,))
        conn.commit()
        conn.close()

    def test_06_appointment_assign_doctor_quota_and_cancellation_billing(self):
        """Kiểm tra: 1) Tiếp tân gán bác sĩ cập nhật ca trực; 2) Hủy lịch hẹn tự động hủy hóa đơn chưa thanh toán."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 id, tai_khoan_id FROM benh_nhan")
        bn = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM bac_si")
        bs = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM chuyen_khoa")
        ck = cursor.fetchone()

        if not bn or not bs or not ck:
            conn.close()
            self.skipTest("Cần dữ liệu bệnh nhân, bác sĩ và chuyên khoa")

        bn_id = bn['id']
        bs_id = bs['id']
        ck_id = ck['id']

        # Tạo ca trực test trong lich_lam_viec
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("UPDATE phieu_kham SET lich_hen_id = NULL WHERE lich_hen_id IN (SELECT id FROM lich_hen WHERE bac_si_id = ? AND ngay_hen = ? AND gio_hen = '08:30')", (bs_id, today_str))
        cursor.execute("DELETE FROM lich_hen WHERE bac_si_id = ? AND ngay_hen = ? AND gio_hen = '08:30'", (bs_id, today_str))
        cursor.execute('''
            INSERT INTO lich_lam_viec (bac_si_id, ngay_lam, ca_lam, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai, trang_thai_duyet)
            VALUES (?, ?, 1, 20, 2, 1, 'DA_DUYET')
        ''', (bs_id, today_str))
        llv_id = cursor.lastrowid

        # Tạo lịch hẹn test
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM lich_hen")
        lh_id_num = cursor.fetchone()['next_id']
        ma_lh = f"LH_TEST_{lh_id_num}"
        cursor.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, chuyen_khoa_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
            VALUES (?, ?, ?, ?, '08:30', N'Khám định kỳ', N'Chờ xác nhận')
        ''', (ma_lh, bn_id, ck_id, today_str))
        lh_id = cursor.lastrowid

        # Tạo hóa đơn tiền khám chưa thanh toán gắn với lịch hẹn
        ma_hdk = f"HDK_TEST_{lh_id_num}"
        cursor.execute('''
            INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, tong_tien, thanh_tien, trang_thai)
            VALUES (?, ?, 150000, 150000, N'Chưa thanh toán')
        ''', (ma_hdk, bn_id))
        hd_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
            VALUES (?, N'Khám bệnh', N'Tiền khám chuyên khoa', ?, 1, 150000, 150000)
        ''', (hd_id, lh_id))
        conn.commit()
        conn.close()

        # 1. Tiếp tân gán bác sĩ cho lịch hẹn -> tăng quota ca trực
        receptionist = {'id': 2, 'ho_ten': 'Lễ Tân'}
        ok_assign, msg_assign = AppointmentModel.assign_doctor(lh_id, bs_id, user_info=receptionist)
        self.assertTrue(ok_assign, f"Gán bác sĩ thất bại: {msg_assign}")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT bac_si_id FROM lich_hen WHERE id = ?", (lh_id,))
        self.assertEqual(cursor.fetchone()['bac_si_id'], bs_id)

        cursor.execute("SELECT so_luong_da_dang_ky FROM lich_lam_viec WHERE id = ?", (llv_id,))
        self.assertEqual(cursor.fetchone()['so_luong_da_dang_ky'], 3, "Quota ca trực phải tăng từ 2 lên 3 sau khi gán bác sĩ")
        conn.close()

        # 2. Hủy lịch hẹn -> Tự động hủy hóa đơn tiền khám chưa thanh toán
        ok_cancel, msg_cancel = AppointmentModel.cancel(lh_id, reason="Bệnh nhân bận việc", user_info=receptionist)
        self.assertTrue(ok_cancel, f"Hủy lịch hẹn thất bại: {msg_cancel}")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trang_thai FROM lich_hen WHERE id = ?", (lh_id,))
        self.assertEqual(cursor.fetchone()['trang_thai'], 'Đã hủy')

        cursor.execute("SELECT trang_thai FROM hoa_don WHERE id = ?", (hd_id,))
        self.assertEqual(cursor.fetchone()['trang_thai'], 'Đã hủy', "Hóa đơn tiền khám chưa thanh toán phải tự động chuyển Đã hủy khi hủy lịch hẹn")

        # Dọn dẹp
        cursor.execute("DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id = ?", (hd_id,))
        cursor.execute("DELETE FROM hoa_don WHERE id = ?", (hd_id,))
        cursor.execute("DELETE FROM lich_hen WHERE id = ?", (lh_id,))
        cursor.execute("DELETE FROM lich_lam_viec WHERE id = ?", (llv_id,))
        conn.commit()
        conn.close()

    def test_07_two_stage_clinical_examination_workflow(self):
        """Kiểm tra quy trình khám bệnh 2 giai đoạn (Chờ kết quả CLS -> finish_examination)."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 id FROM benh_nhan")
        bn = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM bac_si")
        bs = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM dich_vu WHERE loai_dich_vu LIKE N'%xét nghiệm%' OR loai_dich_vu LIKE N'%chẩn đoán%'")
        dv = cursor.fetchone()
        cursor.execute("SELECT TOP 1 id FROM thuoc WHERE so_luong_ton >= 5")
        th = cursor.fetchone()

        if not bn or not bs or not dv or not th:
            conn.close()
            self.skipTest("Cần bệnh nhân, bác sĩ, dịch vụ CLS và thuốc")

        bn_id = bn['id']
        bs_id = bs['id']
        dv_id = dv['id']
        med_id = th['id']

        # 1. Giai đoạn 1: Bác sĩ khám và chỉ định dịch vụ CLS
        doc_user = {'id': 1, 'ho_ten': 'BS Khám Bệnh', 'vai_tro': 'BACSI'}
        ok_save, pk_code = MedicalRecordModel.save_examination(
            patient_id=bn_id,
            doctor_id=bs_id,
            room_id=1,
            reason="Đau bụng quặn cơn",
            symptoms="Đau hạ sườn phải, sốt nhẹ",
            diagnosis="Nghi sỏi mật",
            icd="K80",
            treatment="Chờ kết quả CLS",
            advice="Nghỉ ngơi, chờ kết quả xét nghiệm",
            lab_service_ids=[dv_id],
            medicines=None,
            audit_user=doc_user
        )
        self.assertTrue(ok_save, f"Tạo phiếu khám CLS thất bại: {pk_code}")

        cursor.execute("SELECT id, trang_thai FROM phieu_kham WHERE ma_phieu = ?", (pk_code,))
        pk_row = cursor.fetchone()
        self.assertIsNotNone(pk_row)
        pk_id = pk_row['id']
        self.assertEqual(pk_row['trang_thai'], 'Chờ kết quả CLS', "Phiếu khám có chỉ định CLS phải ở trạng thái Chờ kết quả CLS")

        # 2. Giai đoạn 2: Bác sĩ nhận kết quả và hoàn tất phiên khám (finish_examination)
        ok_fin, msg_fin = MedicalRecordModel.finish_examination(
            record_id=pk_id,
            diagnosis="Viêm túi mật mạn tính",
            icd="K81.1",
            treatment="Điều trị nội khoa ổn định",
            advice="Hạn chế dầu mỡ, tái khám sau 1 tuần",
            medicines=[{'thuoc_id': med_id, 'so_luong': 2, 'lieu_dung': '1 viên/ngày', 'cach_dung': 'Sau ăn sáng'}],
            audit_user=doc_user
        )
        self.assertTrue(ok_fin, f"Hoàn tất phiên khám thất bại: {msg_fin}")

        # Xác minh phiếu khám cập nhật sang 'Hoàn thành'
        cursor.execute("SELECT trang_thai, chan_doan_so_bo, chan_doan_icd FROM phieu_kham WHERE id = ?", (pk_id,))
        pk_after = cursor.fetchone()
        self.assertEqual(pk_after['trang_thai'], 'Hoàn thành')
        self.assertEqual(pk_after['chan_doan_icd'], 'K81.1')

        # Xác minh đơn thuốc được tạo
        cursor.execute("SELECT id, trang_thai FROM don_thuoc WHERE phieu_kham_id = ?", (pk_id,))
        dt_after = cursor.fetchone()
        self.assertIsNotNone(dt_after)

        # Dọn dẹp
        cursor.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (dt_after['id'],))
        cursor.execute("DELETE FROM don_thuoc WHERE id = ?", (dt_after['id'],))
        cursor.execute("DELETE FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id IN (SELECT id FROM phieu_chi_dinh WHERE phieu_kham_id = ?)", (pk_id,))
        cursor.execute("DELETE FROM phieu_chi_dinh WHERE phieu_kham_id = ?", (pk_id,))
        cursor.execute("DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id IN (SELECT id FROM hoa_don WHERE phieu_kham_id = ?)", (pk_id,))
        cursor.execute("DELETE FROM hoa_don WHERE phieu_kham_id = ?", (pk_id,))
        cursor.execute("DELETE FROM phieu_kham WHERE id = ?", (pk_id,))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
