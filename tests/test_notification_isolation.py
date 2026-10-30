import unittest
from datetime import datetime, date, timedelta
from core.database import get_db
from models.notification_model import NotificationModel
from models.appointment_model import AppointmentModel
from models.schedule_model import ScheduleModel
from models.medical_record_model import MedicalRecordModel

class NotificationIsolationTestCase(unittest.TestCase):
    """Kiểm thử tính cô lập và phân loại thông báo theo từng tài khoản / vai trò."""

    def test_01_create_targeted_notifications(self):
        """Kiểm tra tạo thông báo đúng đích danh cho từng vai trò."""
        # Bệnh nhân (tai_khoan_id = 37: 0901234561)
        ok, msg = NotificationModel.create(
            tai_khoan_id=37,
            tieu_de="Test thông báo bệnh nhân",
            noi_dung="Nội dung bệnh nhân",
            loai_thong_bao="Đặt lịch hẹn",
            lien_ket="/patient/appointments"
        )
        self.assertTrue(ok)

        # Lấy thông báo của bệnh nhân
        notifs = NotificationModel.get_user_notifications(37, limit=5)
        self.assertTrue(any(n['tieu_de'] == "Test thông báo bệnh nhân" for n in notifs))

        # Kiểm tra tài khoản khác (ví dụ admin tai_khoan_id = 1) KHÔNG thấy thông báo của bệnh nhân
        admin_notifs = NotificationModel.get_user_notifications(1, limit=50)
        self.assertFalse(any(n['tieu_de'] == "Test thông báo bệnh nhân" for n in admin_notifs))

    def test_02_notification_filtering_by_category(self):
        """Kiểm tra bộ lọc tab thông báo theo danh mục."""
        # Tạo các loại thông báo khác nhau cho admin (id = 1)
        NotificationModel.create(1, "Lịch hẹn mới", "Chi tiết hẹn", loai_thong_bao="Lịch hẹn")
        NotificationModel.create(1, "Đăng ký ca làm", "Chi tiết ca", loai_thong_bao="Lịch trực")
        NotificationModel.create(1, "Kết quả xét nghiệm", "Chi tiết CLS", loai_thong_bao="Cận lâm sàng")
        NotificationModel.create(1, "Hóa đơn viện phí", "Chi tiết viện phí", loai_thong_bao="Thanh toán")

        # Lọc tab appointment
        appt_list = NotificationModel.get_user_notifications(1, limit=50, loai='appointment')
        self.assertTrue(all('lịch' in n['loai_thong_bao'].lower() or 'hẹn' in n['loai_thong_bao'].lower() for n in appt_list))

        # Lọc tab shift
        shift_list = NotificationModel.get_user_notifications(1, limit=50, loai='shift')
        self.assertTrue(all('trực' in n['loai_thong_bao'].lower() or 'ca làm' in n['loai_thong_bao'].lower() for n in shift_list))

        # Lọc tab exam
        exam_list = NotificationModel.get_user_notifications(1, limit=50, loai='exam')
        self.assertTrue(all('khám' in n['loai_thong_bao'].lower() or 'lâm sàng' in n['loai_thong_bao'].lower() or 'xét nghiệm' in n['loai_thong_bao'].lower() for n in exam_list))

    def test_03_polling_initial_load_anti_spam(self):
        """Kiểm tra polling khi khởi tạo lần đầu (init=1 hoặc last_id=0) không bắn new_notifications."""
        data_init = NotificationModel.get_poll_updates(tai_khoan_id=1, last_id=0, is_init=True)
        self.assertEqual(data_init['new_notifications'], [])
        self.assertGreater(data_init['latest_id'], 0)
        self.assertIsInstance(data_init['recent_list'], list)

        # Polling với last_id nhỏ hơn latest_id (mô phỏng có thông báo mới sau đó)
        data_new = NotificationModel.get_poll_updates(tai_khoan_id=1, last_id=data_init['latest_id'] - 1, is_init=False)
        self.assertGreater(len(data_new['new_notifications']), 0)
        self.assertTrue(all(n['id'] > data_init['latest_id'] - 1 for n in data_new['new_notifications']))

    def test_04_mark_read_and_unread_count(self):
        """Kiểm tra đánh dấu đã đọc một và tất cả thông báo."""
        # Tạo thông báo mới chưa đọc cho id = 1
        NotificationModel.create(1, "Thông báo kiểm thử đọc", "Nội dung", loai_thong_bao="Hệ thống")
        notifs = NotificationModel.get_user_notifications(1, limit=1)
        self.assertTrue(len(notifs) > 0)
        nid = notifs[0]['id']

        # Đánh dấu đọc đơn lẻ
        ok, msg = NotificationModel.mark_as_read(nid, tai_khoan_id=1)
        self.assertTrue(ok)

        # Đánh dấu đọc tất cả
        ok_all, msg_all = NotificationModel.mark_all_as_read(tai_khoan_id=1)
        self.assertTrue(ok_all)
        unread = NotificationModel.get_unread_count(tai_khoan_id=1)
        self.assertEqual(unread, 0)

    def test_05_notify_role_ktv_and_pharmacist(self):
        """Kiểm tra gửi thông báo tới nhóm vai trò KTV và DUOCSI."""
        ok_ktv = NotificationModel.notify_role('KTV', "Yêu cầu X-quang mới", "BN kiểm tra X-quang", "Cận lâm sàng")
        self.assertTrue(ok_ktv)

        ok_ph = NotificationModel.notify_role('DUOCSI', "Đơn thuốc mới", "Chuẩn bị thuốc", "Cấp phát thuốc")
        self.assertTrue(ok_ph)

    def test_06_dropdown_vs_page_history_limit(self):
        """Kiểm tra dropdown chuông chỉ lấy 10 thông báo gần nhất còn trang lịch sử lấy toàn bộ."""
        # Tài khoản test id = 1
        for i in range(15):
            NotificationModel.create(1, f"Thông báo lịch sử test #{i+1}", f"Nội dung #{i+1}", loai_thong_bao="Hệ thống")

        # 1. Dropdown qua poll updates chỉ trả về tối đa 10 thông báo gần nhất
        poll_data = NotificationModel.get_poll_updates(1, last_id=0, is_init=True)
        self.assertLessEqual(len(poll_data['recent_list']), 10)

        # 2. Trang lịch sử đầy đủ khi limit=None trả về toàn bộ (> 10)
        full_history = NotificationModel.get_user_notifications(1, limit=None)
        self.assertGreaterEqual(len(full_history), 15)

        # 3. Khi limit=10 thì đúng 10
        top_10 = NotificationModel.get_user_notifications(1, limit=10)
        self.assertEqual(len(top_10), 10)

        # Dọn dẹp dữ liệu test
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM thong_bao WHERE tieu_de LIKE 'Thông báo lịch sử test #%'")
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
