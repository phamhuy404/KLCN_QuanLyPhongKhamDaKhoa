# -*- coding: utf-8 -*-
import unittest
from app import create_app
from core.database import get_db
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel

class TestArchitecturalUpgrades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = cls.app.test_client()

    def login_as(self, role='ADMIN', doctor_id=1):
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {
                'id': 1,
                'username': 'admin_test',
                'vai_tro': role,
                'ho_ten': 'Quản Trị Viên',
                'bac_si_id': doctor_id
            }

    def test_01_numeric_vitals_and_history(self):
        """Kiểm tra các trường sinh hiệu số nguyên/số thực và truy vấn SQL ngưỡng sinh hiệu."""
        vitals = PatientModel.find_patients_by_vitals(min_systolic=120)
        self.assertIsInstance(vitals, list)

        history = PatientModel.get_vitals_history(1)
        self.assertIsInstance(history, list)
        if history:
            first = history[0]
            self.assertIn('huyet_ap_tam_thu', first)
            self.assertIn('mach_num', first)
            self.assertIn('nhiet_do_num', first)

    def test_02_patient_normalized_allergies_and_medical_history(self):
        """Kiểm tra nạp danh mục và quan hệ dị ứng/tiền sử chuẩn hóa trong get_by_id."""
        p = PatientModel.get_by_id(1)
        self.assertIsNotNone(p)
        self.assertIn('danh_sach_di_ung', p)
        self.assertIn('danh_sach_tien_su', p)
        self.assertIn('vitals', p)
        self.assertIn('mach_num', p['vitals'])
        self.assertIn('nhiet_do_num', p['vitals'])

    def test_03_kiosk_live_queue_api(self):
        """Kiểm tra API hàng đợi Kiosk TV trực tiếp."""
        res = self.client.get('/api/kiosk/live-queue')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)

    def test_04_kiosk_page_render(self):
        """Kiểm tra trang giao diện màn hình sảnh Kiosk TV."""
        self.login_as('ADMIN')
        res = self.client.get('/admin/kiosk')
        self.assertEqual(res.status_code, 200)
        self.assertIn('KIOSK TV LIVE', res.get_data(as_text=True))
        self.assertIn('kiosk-grid', res.get_data(as_text=True))

    def test_05_reception_kiosk_button(self):
        """Kiểm tra nút chuyển sang Kiosk trên trang lễ tân."""
        self.login_as('LETAN')
        res = self.client.get('/admin/reception')
        self.assertEqual(res.status_code, 200)
        self.assertIn('/admin/kiosk', res.get_data(as_text=True))

    def test_06_emr_split_view_and_allergy_modal(self):
        """Kiểm tra cấu trúc Split View và Modal cảnh báo sốc phản vệ trên trang EMR."""
        self.login_as('BACSI', doctor_id=1)
        res = self.client.get('/admin/emr')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        # Kiểm tra các khối Split View cố định bên trái
        self.assertIn('id="allergy-warning-box"', html)
        self.assertIn('id="current-patient-allergy"', html)
        self.assertIn('id="current-patient-history"', html)
        self.assertIn('id="emr-ha"', html)
        self.assertIn('id="emr-mach"', html)
        self.assertIn('id="emr-t"', html)
        self.assertIn('id="emr-spo2"', html)
        # Kiểm tra 4 phần cuộn liên tục bên phải
        self.assertIn('id="tab-kham"', html)
        self.assertIn('id="tab-cls"', html)
        self.assertIn('id="tab-thuoc"', html)
        self.assertIn('id="tab-ket-luan"', html)
        # Kiểm tra Modal Popup cảnh báo sốc phản vệ
        self.assertIn('id="modal-anaphylaxis-alert"', html)
        self.assertIn('NGUY CƠ SỐC PHẢN VỆ', html)

if __name__ == '__main__':
    unittest.main()
