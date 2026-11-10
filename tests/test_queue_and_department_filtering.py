import unittest
from datetime import datetime
from models.appointment_model import AppointmentModel

class TestQueueAndDepartmentFiltering(unittest.TestCase):
    def test_appointment_unavailable_detection(self):
        """Kiểm tra lịch hẹn quá hạn được đánh dấu Không khả dụng chuẩn xác."""
        appts = AppointmentModel.get_all(limit=50)
        today_str = datetime.now().strftime('%Y-%m-%d')
        for a in appts:
            raw_tt = a.get('trang_thai_raw') or ''
            app_date = str(a.get('ngay_hen'))[:10]
            is_finished = raw_tt in ['Đã khám', 'Hoàn thành', 'completed', 'Đã hủy', 'cancelled']
            if not is_finished and app_date < today_str:
                self.assertTrue(a.get('is_unavailable'), f"Appt {a.get('id')} date {app_date} must be unavailable")
                self.assertEqual(a.get('trang_thai_hien_thi'), 'Không khả dụng')

    def test_call_appointment_early_validation(self):
        """Kiểm tra chỉ cho phép gọi các ca khám trong ngày hôm nay."""
        all_appts = AppointmentModel.get_all()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        other_day_appt = next((a for a in all_appts if str(a.get('ngay_hen'))[:10] != today_str), None)
        if other_day_appt:
            ok, msg = AppointmentModel.call_appointment_early(other_day_appt['id'])
            self.assertFalse(ok)
            self.assertIn("Chỉ được phép gọi các ca khám trong ngày hôm nay", msg)

    def test_trigger_auto_call_queue_safety(self):
        """Kiểm tra hàm quét gọi số tự động chạy an toàn không phát sinh ngoại lệ."""
        called = AppointmentModel.trigger_auto_call_queue()
        self.assertIsInstance(called, int)

if __name__ == '__main__':
    unittest.main()
