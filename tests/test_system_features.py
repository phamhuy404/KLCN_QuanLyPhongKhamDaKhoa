"""
Kiểm thử tự động toàn diện các tính năng mới:
1. Sao lưu và phục hồi dữ liệu (RBAC, path traversal, backup audit log)
2. Tiếp nhận và quản lý phản hồi bệnh nhân (Patient isolation, reply, in-app noti)
3. Thông báo nhắc lịch và tái khám (In-app, SMTP env fallback, chống gửi trùng)
4. Quản lý danh mục chuyên khoa, phòng khám, dịch vụ (CRUD, validation, bảo toàn tham chiếu)
5. Quản lý nhân sự và phân ca trực (Kiểm tra xung đột trùng lịch, ca trực, RBAC)
"""

import unittest
import os
import sys
from datetime import datetime, timedelta

# Đảm bảo import được module từ thư mục gốc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from core.database import get_db
from models.backup_model import BackupModel
from models.feedback_model import FeedbackModel
from models.notification_model import NotificationModel
from core.notification_service import NotificationService
from models.clinic_model import ClinicModel
from models.user_model import UserModel
from models.schedule_model import ScheduleModel


class SystemFeaturesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    # =========================================================================
    # 1. KIỂM THỬ SAO LƯU và PHỤC HỒI DỮ LIỆU
    # =========================================================================
    def test_01_backup_path_traversal_protection(self):
        """Kiểm tra ngăn chặn path traversal khi tải hoặc phục hồi file backup"""
        ok_res, msg_res = BackupModel.restore_backup("..\\windows\\system32\\cmd.exe", confirm=True)
        self.assertFalse(ok_res, "Không được phép phục hồi file có dấu hiệu path traversal hoặc sai định dạng")

        ok_res2, msg_res2 = BackupModel.restore_backup("../../../etc/passwd", confirm=True)
        self.assertFalse(ok_res2, "Không được phép path traversal unix style")

    def test_02_backup_creation_and_audit(self):
        """Kiểm tra tạo bản sao lưu trên DB hiện tại và ghi audit log"""
        ok, msg = BackupModel.create_backup(user_name="unit_test_admin")
        self.assertTrue(ok, f"Tạo backup thất bại: {msg}")

        # Kiểm tra danh sách bản sao lưu và thư mục
        backup_data = BackupModel.list_backups()
        self.assertIsInstance(backup_data, dict)
        self.assertIn('files', backup_data)
        self.assertIn('history', backup_data)
        self.assertGreater(len(backup_data['files']), 0, "Phải có ít nhất 1 file backup")

        # Kiểm tra file mới nhất
        latest_file = backup_data['files'][0]
        backup_dir = BackupModel.get_backup_dir()
        full_path = os.path.join(backup_dir, latest_file['ten_tap_tin'])
        self.assertTrue(os.path.exists(full_path), "File backup phải tồn tại trên ổ đĩa")
        self.assertGreater(latest_file['dung_luong'], 0, "Dung lượng file backup phải lớn hơn 0")

    def test_03_backup_rbac_protection(self):
        """Bảo vệ quyền truy cập: Người dùng chưa đăng nhập hoặc vai trò bệnh nhân không được phép gọi API backup"""
        # 1. Chưa đăng nhập -> 401
        resp = self.client.post('/api/backup/create')
        self.assertIn(resp.status_code, [401, 403], "Chưa đăng nhập không được phép gọi API backup")

        # 2. Đăng nhập vai trò Bệnh nhân -> 403 Forbidden
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 9999, 'patient_id': 9999, 'vai_tro': 'BENHNHAN', 'ho_ten': 'BN test'}
        resp = self.client.post('/api/backup/create')
        self.assertEqual(resp.status_code, 403, "Bệnh nhân không được phép tạo backup")

    # =========================================================================
    # 2. KIỂM THỬ PHẢN HỒI BỆNH NHÂN và BẢO VỆ DỮ LIỆU RIÊNG TƯ
    # =========================================================================
    def test_04_feedback_patient_isolation(self):
        """Bệnh nhân chỉ được xem phản hồi của chính mình; CSKH/Admin xem và trả lời được"""
        # Tạo phản hồi cho Bệnh nhân 1
        ok, msg = FeedbackModel.create(
            benh_nhan_id=1,
            phieu_kham_id=None,
            chu_de="Dịch vụ khám bệnh",
            diem_danh_gia=5,
            noi_dung="Bác sĩ khám rất tận tâm và chu đáo."
        )
        self.assertTrue(ok, f"Gửi phản hồi thất bại: {msg}")

        # Lấy danh sách phản hồi của Bệnh nhân 1
        list_bn1 = FeedbackModel.get_by_patient(benh_nhan_id=1)
        self.assertGreater(len(list_bn1), 0, "Bệnh nhân 1 phải có danh sách phản hồi")
        latest_fb_id = list_bn1[0]['id']

        # Bệnh nhân 2 không nhìn thấy phản hồi của Bệnh nhân 1
        list_bn2 = FeedbackModel.get_by_patient(benh_nhan_id=2)
        bn2_ids = [item['id'] for item in list_bn2]
        self.assertNotIn(latest_fb_id, bn2_ids, "Bệnh nhân 2 không được thấy phản hồi của Bệnh nhân 1")

        # Admin/CSKH trả lời phản hồi
        reply_ok, reply_msg = FeedbackModel.reply(
            feedback_id=latest_fb_id,
            tra_loi="Cảm ơn quý khách đã gửi ý kiến đóng góp cho phòng khám!",
            trang_thai="Đã giải quyết",
            nguoi_tra_loi="Bộ phận CSKH"
        )
        self.assertTrue(reply_ok, f"Trả lời phản hồi thất bại: {reply_msg}")

        # Xác minh phản hồi đã được cập nhật
        fb_updated = FeedbackModel.get_by_id(latest_fb_id)
        self.assertEqual(fb_updated['trang_thai'], "Đã giải quyết")
        self.assertEqual(fb_updated['tra_loi'], "Cảm ơn quý khách đã gửi ý kiến đóng góp cho phòng khám!")

    # =========================================================================
    # 3. KIỂM THỬ THÔNG BÁO và NHẮC LỊCH KHÔNG GỬI TRÙNG
    # =========================================================================
    def test_05_inapp_notifications(self):
        """Tạo thông báo in-app, lấy danh sách và đánh dấu đã đọc"""
        ok, noti_id = NotificationModel.create(
            tai_khoan_id=1,
            tieu_de="Nhắc lịch khám thử nghiệm",
            noi_dung="Quý khách có lịch khám vào ngày mai.",
            loai_thong_bao="NhacLichKham",
            lien_ket="/patient/appointments"
        )
        self.assertTrue(ok, "Tạo thông báo in-app thất bại")

        # Đếm số lượng chưa đọc
        unread = NotificationModel.get_unread_count(tai_khoan_id=1)
        self.assertGreaterEqual(unread, 1)

        # Lấy danh sách thông báo
        notifs = NotificationModel.get_user_notifications(tai_khoan_id=1, limit=5)
        self.assertGreater(len(notifs), 0)

        # Đánh dấu đã đọc tất cả
        mark_ok, _ = NotificationModel.mark_all_as_read(tai_khoan_id=1)
        self.assertTrue(mark_ok)
        unread_after = NotificationModel.get_unread_count(tai_khoan_id=1)
        self.assertEqual(unread_after, 0, "Sau khi mark_all_as_read thì số chưa đọc phải bằng 0")

    def test_06_reminder_deduplication(self):
        """Kiểm tra cơ chế chống gửi trùng nhắc lịch khám/tái khám"""
        import time
        # Dùng ID ngẫu nhiên duy nhất cho mỗi lần chạy test để tránh trùng với lịch sử chạy trước
        dummy_ref_id = int(time.time() * 1000) % 10000000
        loai = 'TAI_KHAM'

        # Lần 1: Chưa gửi -> phải trả về False
        has_sent = NotificationService.check_reminder_sent(loai_nhac=loai, phieu_kham_id=dummy_ref_id)
        self.assertFalse(has_sent, "Ban đầu nhắc nhở chưa được ghi nhận gửi")

        # Ghi nhận log đã gửi (TAI_KHAM dùng phieu_kham_id, không có FK constraint trực tiếp)
        NotificationService._log_reminder(
            benh_nhan_id=None,
            loai_nhac=loai,
            phieu_kham_id=dummy_ref_id,
            kenh_gui='IN_APP',
            trang_thai='THANH_CONG'
        )

        # Lần 2: Đã gửi -> phải trả về True để chặn gửi lại
        has_sent_after = NotificationService.check_reminder_sent(loai_nhac=loai, phieu_kham_id=dummy_ref_id)
        self.assertTrue(has_sent_after, "Nhắc nhở đã được ghi nhận và không được gửi trùng lần 2")

    def test_07_smtp_status_and_inapp_fallback(self):
        """Nếu chưa cấu hình SMTP, hệ thống báo rõ trạng thái và chạy quét an toàn"""
        smtp_cfg = NotificationService.get_smtp_status()
        self.assertIn('configured', smtp_cfg)
        self.assertIn('server', smtp_cfg)

        # Chạy quét nhắc nhở định kỳ (không ném Exception dù thiếu SMTP)
        stats = NotificationService.run_all_reminders()
        self.assertIn('appointments_scanned', stats)
        self.assertIn('reexams_scanned', stats)

    # =========================================================================
    # 4. KIỂM THỬ QUẢN LÝ CHUYÊN KHOA, PHÒNG KHÁM, DỊCH VỤ
    # =========================================================================
    def test_08_department_crud_and_safety(self):
        """CRUD Chuyên khoa, đổi trạng thái và không xóa cứng khi có bác sĩ tham chiếu"""
        test_code = f"CK_UT_{datetime.now().strftime('%M%S')}"
        ok, res_id = ClinicModel.create_department(
            ma_khoa=test_code,
            ten_khoa=f"Khoa Test {test_code}",
            mo_ta="Khoa thử nghiệm",
            gia_kham=200000.0
        )
        self.assertTrue(ok, f"Tạo chuyên khoa thất bại: {res_id}")
        dep_id = res_id

        # Cập nhật thông tin
        up_ok, up_msg = ClinicModel.update_department(
            dep_id=dep_id,
            ma_khoa=test_code,
            ten_khoa=f"Khoa Test {test_code} Đã sửa",
            mo_ta="Đã cập nhật mô tả",
            gia_kham=250000.0
        )
        self.assertTrue(up_ok, f"Cập nhật thất bại: {up_msg}")

        # Bật/Tắt trạng thái hoạt động
        tog_ok, new_st = ClinicModel.toggle_department_status(dep_id=dep_id)
        self.assertTrue(tog_ok)
        self.assertEqual(new_st, 0, "Sau toggle từ active 1 phải chuyển sang 0")

        # Xóa (khoa mới tạo chưa có bác sĩ liên kết -> xóa được)
        del_ok, del_msg = ClinicModel.delete_department(dep_id=dep_id)
        self.assertTrue(del_ok, f"Xóa khoa test thất bại: {del_msg}")

    def test_09_prevent_hard_delete_referenced_catalog(self):
        """Chặn xóa cứng chuyên khoa đã có dữ liệu tham chiếu (ví dụ Khoa đang có Bác sĩ)"""
        departments = ClinicModel.get_all_departments(active_only=False)
        referenced_dep_id = None
        for dep in departments:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM bac_si WHERE chuyen_khoa_id = ?", (dep['id'],))
            chk = cur.fetchone()
            conn.close()
            if chk and chk['cnt'] > 0:
                referenced_dep_id = dep['id']
                break

        if referenced_dep_id:
            del_ok, del_msg = ClinicModel.delete_department(referenced_dep_id)
            self.assertFalse(del_ok, "Không được phép xóa cứng chuyên khoa đang có bác sĩ hoạt động")
            self.assertIn("vô hiệu hóa", del_msg.lower())

    # =========================================================================
    # 5. KIỂM THỬ QUẢN LÝ NHÂN SỰ và PHÂN CA TRỰC XUNG ĐỘT
    # =========================================================================
    def test_10_staff_crud_and_status(self):
        """Thêm nhân viên y tế, đổi trạng thái làm việc"""
        ts = datetime.now().strftime('%H%M%S%f')[-8:]   # 8 chữ số duy nhất
        staff_data = {
            'ho_ten': f"Bác sĩ Test {ts}",
            'sdt': f"09{ts[:9]}",           # SĐT 11 ký tự duy nhất
            'chuc_vu': "Bác sĩ Chuyên Khoa I",
            'vai_tro_id': 3,                # BACSI
            'chuyen_khoa_id': 1,
            'email': f"bs{ts}@clinic.local",
            'username': f"bs_test_{ts}",
            'password': "Password@123",
            'cccd': f"0{ts[:11]}"          # CCCD 12 chữ số duy nhất
        }
        ok, res = UserModel.create_staff(staff_data)
        self.assertTrue(ok, f"Tạo nhân viên thất bại: {res}")
        staff_id = res

        # Bật/Tắt trạng thái làm việc
        tog_ok, new_st = UserModel.toggle_staff_status(staff_id)
        self.assertTrue(tog_ok, f"Toggle trạng thái thất bại: {new_st}")
        self.assertEqual(new_st, 0, "Sau toggle từ active 1 phải chuyển sang 0")

        # Lấy thông tin nhân viên và xác nhận trạng thái
        staff_info = UserModel.get_staff_by_id(staff_id)
        self.assertIsNotNone(staff_info)
        self.assertEqual(staff_info['trang_thai'], 0)

    def test_11_schedule_conflict_detection(self):
        """Kiểm tra chống trùng lịch làm việc: cùng bác sĩ hoặc cùng phòng trong 1 ca trực, và chặn ngày quá khứ"""
        future_date = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
        ca_lam = 1
        room_id = 1
        doctor_id = 1

        # Tạo ca trực đầu tiên
        ok1, res1 = ScheduleModel.create_schedule(
            bac_si_id=doctor_id,
            phong_kham_id=room_id,
            ngay_lam=future_date,
            ca_lam=ca_lam,
            so_luong_kham_toi_da=15
        )
        self.assertTrue(ok1, f"Tạo ca trực ban đầu thất bại: {res1}")
        created_id = res1

        try:
            # 1. Thử tạo ca trực trùng Bác sĩ cùng ngày cùng ca (khác phòng) -> Phải bị chặn
            conflict_doc, msg_doc = ScheduleModel.create_schedule(
                bac_si_id=doctor_id,
                phong_kham_id=2,
                ngay_lam=future_date,
                ca_lam=ca_lam
            )
            self.assertFalse(conflict_doc, "Phải chặn xung đột khi cùng bác sĩ đã có lịch trực")
            self.assertIn("xung đột", msg_doc.lower())

            # 2. Thử tạo ca trực trùng Phòng cùng ngày cùng ca (khác bác sĩ) -> Phải bị chặn
            conflict_room, msg_room = ScheduleModel.create_schedule(
                bac_si_id=2,
                phong_kham_id=room_id,
                ngay_lam=future_date,
                ca_lam=ca_lam
            )
            self.assertFalse(conflict_room, "Phải chặn xung đột khi phòng khám đã có bác sĩ khác trực")
            self.assertIn("xung đột", msg_room.lower())

            # 3. Thử xếp lịch trong ngày quá khứ -> Phải bị chặn
            past_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            past_ok, past_msg = ScheduleModel.create_schedule(
                bac_si_id=doctor_id,
                phong_kham_id=room_id,
                ngay_lam=past_date,
                ca_lam=ca_lam
            )
            self.assertFalse(past_ok, "Không được phép tạo ca trực trong quá khứ")
            self.assertIn("quá khứ", past_msg.lower())

        finally:
            # Dọn dẹp ca trực test
            ScheduleModel.delete_schedule(created_id)


if __name__ == '__main__':
    unittest.main()
