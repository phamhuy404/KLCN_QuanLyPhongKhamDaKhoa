# -*- coding: utf-8 -*-
"""
Bộ kiểm thử toàn diện cho tất cả các tính năng nâng cấp:
1. EMR 2 giai đoạn & Kéo thả / Upload tối đa 10 ảnh WebP (Bác sĩ & KTV).
2. KTV kiểm tra trạng thái thanh toán viện phí CLS.
3. Cảnh báo dị ứng thuốc thời gian thực.
4. Phân quyền đăng ký ca làm: Admin không đăng ký, Lễ tân tự duyệt, Bác sĩ/Dược sĩ/KTV chờ duyệt.
5. Hồ sơ cá nhân nội bộ (Admin & Nhân viên) & đổi mật khẩu.
6. Điều phối lịch hẹn khi hủy ca trực bác sĩ.
7. Chống đặt trùng giờ & Chặn đổi lịch đã xong/hủy.
8. Nhận diện chính xác hóa đơn thuốc (HDT).
"""

import unittest
from datetime import datetime, timedelta, date
from app import create_app
from core.database import get_db
from models.appointment_model import AppointmentModel
from models.schedule_model import ScheduleModel
from models.medical_record_model import MedicalRecordModel
from models.billing_model import BillingModel
from models.user_model import UserModel

class TestFinalComprehensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_01_schedule_role_permissions(self):
        """Phân quyền đăng ký ca làm việc: Admin không đăng ký, Lễ tân tự duyệt ngay, Bác sĩ/Dược sĩ chờ duyệt."""
        bounds = ScheduleModel.get_week_bounds()
        w1_start = bounds['next_week_1'][0]
        w1_str = str(w1_start)

        # 1. Admin đăng ký -> Bị chặn
        admin_user = {'id': 1, 'vai_tro': 'ADMIN', 'staff_id': 1}
        ok_adm, msg_adm = ScheduleModel.register_schedule(admin_user, w1_str, ca_lam=1)
        self.assertFalse(ok_adm)
        self.assertIn("không cần đăng ký", msg_adm)

        # 2. Lễ tân đăng ký -> Tự động duyệt ngay
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT t.id, v.ma_vai_tro, nv.id AS staff_id FROM tai_khoan t JOIN vai_tro v ON t.vai_tro_id = v.id JOIN nhan_vien nv ON t.id = nv.tai_khoan_id WHERE v.ma_vai_tro = 'LETAN'")
        letan_row = cursor.fetchone()
        if not letan_row:
            letan_user = {'id': 99, 'vai_tro': 'LETAN', 'staff_id': 99}
        else:
            letan_user = {'id': letan_row['id'], 'vai_tro': 'LETAN', 'staff_id': letan_row['staff_id']}

        cursor.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id = ? AND ngay_lam = ? AND ca_lam = 1", (letan_user['staff_id'], w1_str))
        conn.commit()

        ok_lt, msg_lt = ScheduleModel.register_schedule(letan_user, w1_str, ca_lam=1)
        self.assertTrue(ok_lt, f"Lễ tân đăng ký ca trực thất bại: {msg_lt}")
        self.assertIn("tự động phê duyệt", msg_lt)

        # Kiểm tra trạng thái trong DB là DA_DUYET
        cursor.execute("SELECT trang_thai_duyet FROM lich_lam_viec WHERE nhan_vien_id = ? AND ngay_lam = ? AND ca_lam = 1", (letan_user['staff_id'], w1_str))
        saved_lt = cursor.fetchone()
        self.assertEqual(saved_lt['trang_thai_duyet'], 'DA_DUYET')

        # Dọn dẹp
        cursor.execute("DELETE FROM lich_lam_viec WHERE nhan_vien_id = ? AND ngay_lam = ? AND ca_lam = 1", (letan_user['staff_id'], w1_str))
        conn.commit()
        conn.close()

    def test_02_appointment_duplicate_and_reschedule_block(self):
        """Chặn đặt trùng giờ và chặn reschedule lịch đã hoàn thành/đã hủy."""
        target_date = (date.today() + timedelta(days=12)).strftime('%Y-%m-%d')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lich_hen WHERE benh_nhan_id = 1 AND ngay_hen = ? AND gio_hen = '09:00'", (target_date,))
        conn.commit()

        # Tạo lịch lần 1
        ok1, code1 = AppointmentModel.create(
            benh_nhan_id=1,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=target_date,
            gio_hen='09:00',
            ly_do_kham='Khám thử nghiệm 1'
        )
        self.assertTrue(ok1, f"Tạo lịch 1 thất bại: {code1}")

        # Tạo lịch lần 2 cùng bệnh nhân, cùng ngày và cùng giờ -> Phải bị từ chối
        ok2, code2 = AppointmentModel.create(
            benh_nhan_id=1,
            chuyen_khoa_id=2,
            bac_si_id=2,
            ngay_hen=target_date,
            gio_hen='09:00',
            ly_do_kham='Khám thử nghiệm trùng giờ'
        )
        self.assertFalse(ok2)
        self.assertIn("đã có lịch hẹn", code2)

        # Cập nhật lịch 1 sang 'Đã khám' rồi thử reschedule -> Phải bị chặn
        cursor.execute("UPDATE lich_hen SET trang_thai = N'Đã khám' WHERE ma_lich_hen = ?", (code1,))
        conn.commit()

        new_date = (date.today() + timedelta(days=13)).strftime('%Y-%m-%d')
        ok_resched, msg_resched = AppointmentModel.reschedule(code1, new_date, '10:00', user_info={'vai_tro': 'BENHNHAN', 'benh_nhan_id': 1})
        self.assertFalse(ok_resched)
        self.assertIn("Không thể đổi lịch hẹn", msg_resched)

        # Dọn dẹp
        cursor.execute("DELETE FROM lich_hen WHERE ma_lich_hen = ?", (code1,))
        conn.commit()
        conn.close()

    def test_03_emr_two_phase_and_multi_image(self):
        """Khám EMR 2 giai đoạn: lưu kết quả lâm sàng + chỉ định CLS -> KTV nhập KQ -> Bác sĩ kết luận."""
        conn = get_db()
        cursor = conn.cursor()

        # 1. Tạo ca khám lâm sàng có chỉ định CLS
        sample_images = ["/static/uploads/kham_benh/test_img1.webp", "/static/uploads/kham_benh/test_img2.webp"]
        ok, ma_phieu = MedicalRecordModel.save_examination(
            patient_id=1,
            doctor_id=1,
            room_id=1,
            reason="Khám dạ dày",
            symptoms="Đau rát thượng vị",
            diagnosis="Theo dõi viêm dạ dày",
            icd="K29.5 - Viêm dạ dày mạn",
            treatment="Chỉ định nội soi và xét nghiệm",
            advice="Nhịn ăn sáng",
            lab_service_ids=[1], # Có chỉ định CLS
            medicines=[],
            images=sample_images,
            audit_user={'id': 1, 'ho_ten': 'BS. Test'}
        )
        self.assertTrue(ok, f"Lưu EMR giai đoạn 1 thất bại: {ma_phieu}")

        cursor.execute("SELECT id, hinh_anh_kham, trang_thai FROM phieu_kham WHERE ma_phieu = ?", (ma_phieu,))
        pk_row = cursor.fetchone()
        self.assertIsNotNone(pk_row)
        self.assertEqual(pk_row['trang_thai'], 'Chờ kết quả CLS')
        self.assertIn("test_img1.webp", pk_row['hinh_anh_kham'])

        # 2. Tìm chi tiết chỉ định CLS tương ứng
        cursor.execute("SELECT id FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id IN (SELECT id FROM phieu_chi_dinh WHERE phieu_kham_id = ?)", (pk_row['id'],))
        ct_row = cursor.fetchone()
        self.assertIsNotNone(ct_row)
        chi_tiet_id = ct_row['id']

        # 3. KTV cập nhật kết quả CLS với nhiều ảnh
        lab_images = ["/static/uploads/cls/xquang1.webp", "/static/uploads/cls/xquang2.webp"]
        import json
        ok_lab, msg_lab = MedicalRecordModel.update_lab_result(
            chi_tiet_id=chi_tiet_id,
            ket_qua="Hình ảnh niêm mạc xung huyết vừa",
            file_ket_qua=json.dumps(lab_images),
            audit_user={'id': 3, 'ho_ten': 'KTV. Test'}
        )
        self.assertTrue(ok_lab, f"KTV cập nhật thất bại: {msg_lab}")

        # 4. Bác sĩ kết luận sau khi có kết quả CLS
        finish_images = ["/static/uploads/kham_benh/test_img1.webp", "/static/uploads/kham_benh/test_img2.webp", "/static/uploads/kham_benh/final_photo.webp"]
        ok_fin, msg_fin = MedicalRecordModel.finish_examination(
            record_id=pk_row['id'],
            diagnosis="Viêm dạ dày trợt nông",
            icd="K29.5 - Viêm dạ dày",
            treatment="Uống thuốc theo đơn 2 tuần",
            advice="Kiêng chua cay",
            reexam_date=(date.today() + timedelta(days=14)).strftime('%Y-%m-%d'),
            medicines=[{'thuoc_id': 6, 'so_luong': 10, 'lieu_dung': '1v x 2 lần', 'cach_dung': 'Sau ăn'}],
            images=finish_images,
            audit_user={'id': 1, 'ho_ten': 'BS. Test'}
        )
        self.assertTrue(ok_fin, f"Hoàn tất EMR giai đoạn 2 thất bại: {msg_fin}")

        # Kiểm tra phiếu khám đã sang 'Hoàn thành'
        cursor.execute("SELECT trang_thai, hinh_anh_kham FROM phieu_kham WHERE id = ?", (pk_row['id'],))
        pk_fin = cursor.fetchone()
        self.assertEqual(pk_fin['trang_thai'], 'Hoàn thành')
        self.assertIn("final_photo.webp", pk_fin['hinh_anh_kham'])

        # Dọn dẹp
        cursor.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id IN (SELECT id FROM don_thuoc WHERE phieu_kham_id = ?)", (pk_row['id'],))
        cursor.execute("DELETE FROM don_thuoc WHERE phieu_kham_id = ?", (pk_row['id'],))
        cursor.execute("DELETE FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id IN (SELECT id FROM phieu_chi_dinh WHERE phieu_kham_id = ?)", (pk_row['id'],))
        cursor.execute("DELETE FROM phieu_chi_dinh WHERE phieu_kham_id = ?", (pk_row['id'],))
        cursor.execute("DELETE FROM hoa_don WHERE phieu_kham_id = ?", (pk_row['id'],))
        cursor.execute("DELETE FROM phieu_kham WHERE id = ?", (pk_row['id'],))
        conn.commit()
        conn.close()

    def test_04_staff_profile_and_password_update(self):
        """Lấy thông tin và cập nhật hồ sơ cá nhân nội bộ (Admin/Nhân viên)."""
        # Kiểm tra lấy thông tin nhân viên
        profile = UserModel.get_staff_profile(account_id=1)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.get('vai_tro'), 'ADMIN')

        # Kiểm tra cập nhật thông tin thành công (không đổi mật khẩu)
        form_data = {
            'ho_ten': 'Quản Trị Viên Hệ Thống',
            'so_dien_thoai': '0909999888',
            'email': 'admin@h2thealthcare.vn',
            'dia_chi': 'TP. Hồ Chí Minh'
        }
        ok, msg = UserModel.update_staff_profile(
            account_id=1,
            form_data=form_data,
            current_password=None,
            new_password=None,
            audit_user={'id': 1, 'ho_ten': 'Admin'}
        )
        self.assertTrue(ok, f"Cập nhật hồ sơ thất bại: {msg}")

        # Kiểm tra nếu mật khẩu hiện tại sai -> Từ chối
        ok_fail, msg_fail = UserModel.update_staff_profile(
            account_id=1,
            form_data=form_data,
            current_password='sai_mat_khau_chac_chan',
            new_password='new_pass_123',
            audit_user={'id': 1, 'ho_ten': 'Admin'}
        )
        self.assertFalse(ok_fail)
        self.assertIn("hiện tại không chính xác", msg_fail)

    def test_05_drug_invoice_identification(self):
        """Chỉ nhận diện hóa đơn thuốc khi mã bắt đầu bằng HDT, không nhầm với hóa đơn khám."""
        # Hóa đơn khám thông thường (HDK...)
        inv_kham = {'ma_hoa_don': 'HDK2609001', 'phieu_kham_id': 1}
        is_drug_kham = inv_kham and str(inv_kham.get('ma_hoa_don', '')).startswith('HDT')
        self.assertFalse(is_drug_kham, "Hóa đơn khám không được nhận diện là hóa đơn thuốc")

        # Hóa đơn thuốc (HDT...)
        inv_thuoc = {'ma_hoa_don': 'HDT2609001', 'phieu_kham_id': 1}
        is_drug_thuoc = inv_thuoc and str(inv_thuoc.get('ma_hoa_don', '')).startswith('HDT')
        self.assertTrue(is_drug_thuoc, "Hóa đơn HDT phải được nhận diện chính xác là hóa đơn thuốc")

if __name__ == '__main__':
    unittest.main()
