import unittest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from core.database import get_db
from core.security import hash_password, verify_password
from models.user_model import UserModel
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.clinic_model import ClinicModel

class ComprehensiveScenariosTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        self.db = get_db()
        self.cursor = self.db.cursor()

    def tearDown(self):
        try:
            if hasattr(self, 'db') and self.db:
                self.db.commit()
                self.db.close()
        except Exception:
            pass

    def test_scenario_01_doctor_onboarding_and_profile_completion(self):
        """Kịch bản 1: Admin tạo Bác sĩ mới bằng SĐT -> Bác sĩ đăng nhập 123 -> Đổi MK & Hoàn tất hồ sơ"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        doctor_phone = f"091{ts}"
        doctor_cccd = f"079085{ts[-6:]}"
        
        # 1. Admin đăng nhập
        self.client.get('/logout')
        admin_login = self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        self.assertEqual(admin_login.status_code, 200)

        # 2. Admin tạo Bác sĩ mới chỉ bằng SĐT
        create_res = self.client.post('/admin/doctors/create', data={
            'sdt': doctor_phone,
            'chuyen_khoa_id': '1'
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 200)

        # Kiểm tra tài khoản trong DB: username = phone, mật khẩu = 123, da_hoan_thien_ho_so = 0
        self.db.commit()
        self.cursor.execute("SELECT * FROM tai_khoan WHERE sdt = ?", (doctor_phone,))
        doc_acc = self.cursor.fetchone()
        self.assertIsNotNone(doc_acc)
        self.assertEqual(doc_acc['da_hoan_thien_ho_so'], 0)
        self.assertTrue(verify_password(doc_acc['password'], '123'))

        # 3. Đăng xuất Admin, Bác sĩ mới đăng nhập bằng SĐT + 123
        self.client.get('/logout')
        doc_login = self.client.post('/login', data={'username': doctor_phone, 'password': '123'})
        self.assertEqual(doc_login.status_code, 302)
        self.assertIn('/admin/doctor/complete-profile', doc_login.headers.get('Location', ''))

        # 4. Khi chưa hoàn thiện hồ sơ, cố vào trang dashboard sẽ bị chặn và redirect về complete-profile
        dashboard_attempt = self.client.get('/admin/dashboard')
        self.assertEqual(dashboard_attempt.status_code, 302)
        self.assertIn('/admin/doctor/complete-profile', dashboard_attempt.headers.get('Location', ''))

        # 5. Bác sĩ hoàn thiện hồ sơ
        new_pass = "DoctorPass@2026"
        complete_res = self.client.post('/admin/doctor/complete-profile', data={
            'ho_ten': "BS. Nguyễn Văn Khảo Sát",
            'chuyen_khoa_id': '1',
            'phong_kham_id': '1',
            'hoc_vi': 'Thạc sĩ, Bác sĩ',
            'so_nam_kinh_nghiem': '8',
            'gia_kham': '250000',
            'cccd': doctor_cccd,
            'ngay_sinh': '1985-05-15',
            'gioi_tinh': '1',
            'gioi_thieu': 'Bác sĩ chuyên khoa tiêu hóa với 8 năm kinh nghiệm',
            'new_password': new_pass,
            'confirm_password': new_pass
        }, follow_redirects=True)
        self.assertEqual(complete_res.status_code, 200)

        # 6. Kiểm tra sau khi hoàn tất, da_hoan_thien_ho_so = 1 và đăng nhập được bằng mật khẩu mới
        self.db.commit()
        self.cursor.execute("SELECT * FROM tai_khoan WHERE sdt = ?", (doctor_phone,))
        updated_acc = self.cursor.fetchone()
        self.assertEqual(updated_acc['da_hoan_thien_ho_so'], 1)
        self.assertTrue(verify_password(updated_acc['password'], new_pass))

        # Kiểm tra bảng bac_si qua nhan_vien có thông tin
        self.cursor.execute("""
            SELECT b.*, nv.ho_ten 
            FROM bac_si b 
            JOIN nhan_vien nv ON b.nhan_vien_id = nv.id 
            WHERE nv.tai_khoan_id = ?
        """, (updated_acc['id'],))
        doc_info = self.cursor.fetchone()
        self.assertIsNotNone(doc_info)
        self.assertEqual(doc_info['ho_ten'], "BS. Nguyễn Văn Khảo Sát")
        self.assertEqual(doc_info['trang_thai_lam_viec'], 'Đang làm việc')

    def test_scenario_02_patient_profile_catalogs_and_medical_records(self):
        """Kịch bản 2: Bệnh nhân đăng ký nhanh -> Đăng nhập chuyển hướng hoàn thiện -> Cập nhật Nhóm máu, Dị ứng, Bệnh nền, BHYT"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        patient_phone = f"092{ts}"
        patient_cccd = f"079192{ts[-6:]}"
        
        # 1. Đăng ký bệnh nhân nhanh (chưa có CCCD/Ngày sinh -> da_hoan_thien_ho_so = 0)
        ok, msg = UserModel.register_patient(
            ho_ten="Nguyễn Thị Mai Anh",
            sdt=patient_phone,
            password="PatientPass@123"
        )
        self.assertTrue(ok, f"Đăng ký bệnh nhân thất bại: {msg}")

        # 2. Đăng nhập bệnh nhân bằng SĐT -> Tự động chuyển hướng vào complete-profile
        self.client.get('/logout')
        login_res = self.client.post('/login', data={'username': patient_phone, 'password': 'PatientPass@123'})
        self.assertEqual(login_res.status_code, 302)
        self.assertIn('/patient/complete-profile', login_res.headers.get('Location', ''))

        # 3. Bệnh nhân hoàn tất hồ sơ lần đầu tại /patient/complete-profile
        comp_res = self.client.post('/patient/complete-profile', data={
            'ho_ten': 'Nguyễn Thị Mai Anh',
            'ngay_sinh': '1992-08-20',
            'gioi_tinh': 'Nữ',
            'dia_chi': '123 Đường Test, Quận 1, TP.HCM',
            'cccd': patient_cccd,
            'nhom_mau': 'A+',
            'nhom_mau_bien_the': 'Rh-',
            'di_ung': 'Penicillin, Aspirin, Tôm cua',
            'benh_ly_nen': 'Tăng huyết áp, Đái tháo đường type 2'
        }, follow_redirects=True)
        self.assertEqual(comp_res.status_code, 200)

        # 4. Bệnh nhân cập nhật thêm thông tin BHYT tại /api/patient/update-profile
        update_res = self.client.post('/api/patient/update-profile', json={
            'ho_ten': 'Nguyễn Thị Mai Anh',
            'ngay_sinh': '1992-08-20',
            'gioi_tinh': 'Nữ',
            'dia_chi': '123 Đường Test, Quận 1, TP.HCM',
            'bhyt': '0791950003',
            'nhom_mau': 'A+',
            'ghi_chu_nhom_mau': 'Rh-',
            'di_ung': 'Penicillin, Aspirin, Tôm cua',
            'tien_su_benh': 'Tăng huyết áp, Đái tháo đường type 2'
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertTrue(update_res.get_json().get('success'))

        # 5. Kiểm tra trong DB
        self.db.commit()
        self.cursor.execute("""
            SELECT bn.* FROM benh_nhan bn
            JOIN tai_khoan tk ON bn.tai_khoan_id = tk.id
            WHERE tk.sdt = ?
        """, (patient_phone,))
        bn = self.cursor.fetchone()
        self.assertIsNotNone(bn)
        self.assertEqual(bn['nhom_mau'], 'A+')
        self.assertIn('Rh-', bn.get('ghi_chu_nhom_mau', ''))
        self.assertIn('Penicillin', bn.get('di_ung', ''))
        self.assertIn('Tăng huyết áp', bn.get('tien_su_benh', ''))
        self.assertEqual(bn['bhyt'], '0791950003')

        # 6. Truy cập trang /patient/records để kiểm tra xem hồ sơ bệnh án có hiển thị mượt mà không
        rec_res = self.client.get('/patient/records')
        self.assertEqual(rec_res.status_code, 200)

    def test_scenario_03_online_booking_and_reception_flow(self):
        """Kịch bản 3: Bệnh nhân đặt lịch khám online -> Tiếp tân duyệt tiếp nhận & Hủy lịch hẹn"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        patient_phone = f"093{ts}"
        patient_cccd = f"079190{ts[-6:]}"
        
        # 1. Đăng ký & Kích hoạt bệnh nhân
        UserModel.register_patient(
            ho_ten="Trần Tuấn Khang",
            sdt=patient_phone,
            password="BookingPass@123",
            ngay_sinh="1990-01-01",
            gioi_tinh="Nam",
            cccd=patient_cccd
        )
        self.cursor.execute("UPDATE tai_khoan SET da_hoan_thien_ho_so = 1 WHERE sdt = ?", (patient_phone,))
        self.db.commit()

        self.client.get('/logout')
        self.client.post('/login', data={'username': patient_phone, 'password': 'BookingPass@123'}, follow_redirects=True)

        # Lấy ID bệnh nhân
        self.cursor.execute("SELECT bn.id FROM benh_nhan bn JOIN tai_khoan tk ON bn.tai_khoan_id = tk.id WHERE tk.sdt = ?", (patient_phone,))
        bn_id = self.cursor.fetchone()['id']

        # 2. Đặt lịch khám trực tuyến qua API /api/appointment/book
        book_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        self.cursor.execute("DELETE FROM lich_hen WHERE bac_si_id = 1 AND ngay_hen = ? AND gio_hen = '09:00'", (book_date,))
        self.db.commit()
        book_res = self.client.post('/api/appointment/book', json={
            'chuyen_khoa_id': 1,
            'bac_si_id': 1,
            'ngay_hen': book_date,
            'gio_hen': '09:00',
            'ly_do': 'Đau đầu, chóng mặt kéo dài'
        })
        self.assertEqual(book_res.status_code, 200)
        book_data = book_res.get_json()
        self.assertTrue(book_data.get('success'))

        # 3. Tiếp tân đăng nhập kiểm tra danh sách lịch hẹn
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        app_page = self.client.get('/admin/appointments')
        self.assertEqual(app_page.status_code, 200)

        # 4. Tiếp nhận bệnh nhân: cập nhật trạng thái confirmed
        self.db.commit()
        self.cursor.execute("SELECT TOP 1 id FROM lich_hen WHERE benh_nhan_id = ? ORDER BY id DESC", (bn_id,))
        created_app_id = self.cursor.fetchone()['id']
        status_res = self.client.post('/api/appointment/update-status', json={
            'appointment_id': created_app_id,
            'status': 'confirmed'
        })
        self.assertEqual(status_res.status_code, 200)

        # 5. Thử kịch bản Hủy lịch hẹn qua API /api/appointment/cancel
        ok_create, res_create = AppointmentModel.create(
            benh_nhan_id=bn_id,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=book_date,
            gio_hen='14:00',
            ly_do_kham='Thử hủy lịch'
        )
        self.assertTrue(ok_create)
        self.db.commit()
        self.cursor.execute("SELECT TOP 1 id FROM lich_hen WHERE benh_nhan_id = ? ORDER BY id DESC", (bn_id,))
        app_id_cancel = self.cursor.fetchone()['id']

        cancel_res = self.client.post('/api/appointment/cancel', json={
            'id': app_id_cancel,
            'ly_do': 'Bệnh nhân bận việc đột xuất'
        })
        self.assertEqual(cancel_res.status_code, 200)
        cancel_data = cancel_res.get_json()
        self.assertTrue(cancel_data.get('success'))

        # Kiểm tra trạng thái trong DB đã chuyển thành cancelled
        self.db.commit()
        self.cursor.execute("SELECT trang_thai FROM lich_hen WHERE id = ?", (app_id_cancel,))
        app_row = self.cursor.fetchone()
        self.assertIn(app_row['trang_thai'], ['cancelled', 'Da_huy', 'Đã hủy'])

    def test_scenario_04_doctor_examination_lab_prescription_and_pharmacy(self):
        """Kịch bản 4: Bác sĩ khám bệnh -> Kê đơn thuốc & Chỉ định xét nghiệm -> KTV nhập kết quả & Duyệt -> Bệnh nhân chọn mua viện -> Tiếp tân duyệt -> Thu ngân thu tiền -> Dược sĩ cấp phát"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        patient_phone = f"094{ts}"
        patient_cccd = f"079188{ts[-6:]}"
        
        # 1. Chuẩn bị bệnh nhân
        UserModel.register_patient(
            ho_ten="Lê Quốc Bảo",
            sdt=patient_phone,
            password="EmrPass@123",
            ngay_sinh="1988-12-12",
            gioi_tinh="Nam",
            cccd=patient_cccd
        )
        self.cursor.execute("UPDATE tai_khoan SET da_hoan_thien_ho_so = 1 WHERE sdt = ?", (patient_phone,))
        self.db.commit()

        self.cursor.execute("SELECT bn.id FROM benh_nhan bn JOIN tai_khoan tk ON bn.tai_khoan_id = tk.id WHERE tk.sdt = ?", (patient_phone,))
        bn_id = self.cursor.fetchone()['id']

        # 2. Đăng nhập Bác sĩ bs_noi_1
        self.client.get('/logout')
        bs_login = self.client.post('/login', data={'username': 'bs_noi_1', 'password': 'Password@123'}, follow_redirects=True)
        self.assertEqual(bs_login.status_code, 200)

        # 3. Lấy thông tin thuốc và dịch vụ xét nghiệm có sẵn trong DB
        self.cursor.execute("SELECT TOP 1 id, ten_thuoc, so_luong_ton FROM thuoc WHERE so_luong_ton > 10")
        med = self.cursor.fetchone()
        med_id = med['id']
        initial_stock = med['so_luong_ton']

        self.cursor.execute("SELECT TOP 1 id, ten_dich_vu FROM dich_vu WHERE loai_dich_vu LIKE N'%xét nghiệm%' OR loai_dich_vu LIKE N'%cls%' OR 1=1")
        serv = self.cursor.fetchone()
        service_id = serv['id']

        # 4. Bác sĩ lưu phiếu khám bệnh EMR
        emr_payload = {
            'patient_id': bn_id,
            'doctor_id': 1,
            'room_id': 1,
            'reason': 'Ho, sốt nhẹ, tức ngực',
            'symptoms': 'Ho có đờm 3 ngày',
            'diagnosis': 'J20 - Viêm phế quan cap',
            'icd': 'J20',
            'treatment': 'Theo dõi và điều trị nội khoa',
            'advice': 'Uống nhiều nước ấm, nghỉ ngơi hợp lý',
            'reexam_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'lab_services': [service_id],
            'medicines': [
                {
                    'thuoc_id': med_id,
                    'so_luong': 10,
                    'cach_dung': 'Uống sau ăn',
                    'sang': '1', 'trua': '0', 'chieu': '1', 'toi': '0'
                }
            ]
        }

        save_res = self.client.post('/api/emr/save', json=emr_payload)
        self.assertEqual(save_res.status_code, 200)
        emr_res_data = save_res.get_json()
        self.assertTrue(emr_res_data.get('success'))

        # Lấy phiếu khám mới nhất của bệnh nhân
        self.db.commit()
        self.cursor.execute("SELECT TOP 1 id FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY id DESC", (bn_id,))
        phieu_kham_row = self.cursor.fetchone()
        self.assertIsNotNone(phieu_kham_row)
        phieu_kham_id = phieu_kham_row['id']

        # Kiểm tra phiếu chỉ định và chi tiết chỉ định được tạo
        self.cursor.execute("SELECT TOP 1 id FROM phieu_chi_dinh WHERE phieu_kham_id = ?", (phieu_kham_id,))
        pcd = self.cursor.fetchone()
        self.assertIsNotNone(pcd)
        self.cursor.execute("SELECT TOP 1 id, trang_thai FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id = ?", (pcd['id'],))
        ctcd = self.cursor.fetchone()
        self.assertIsNotNone(ctcd)
        ctcd_id = ctcd['id']

        # 5. Kỹ thuật viên xét nghiệm đăng nhập (ktv_1)
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'ktv_1', 'password': 'Password@123'}, follow_redirects=True)

        lab_page = self.client.get('/admin/lab')
        self.assertEqual(lab_page.status_code, 200)

        # KTV lưu kết quả xét nghiệm
        save_lab_res = self.client.post('/api/lab/result/save', json={
            'chi_tiet_id': ctcd_id,
            'ket_qua': 'Bạch cầu trong giới hạn bình thường (6.5 x 10^9/L)',
            'ket_luan': 'Chưa phát hiện dấu hiệu nhiễm trùng nặng',
            'file_dinh_kem': ''
        })
        self.assertEqual(save_lab_res.status_code, 200)
        self.assertTrue(save_lab_res.get_json().get('success'))

        # KTV duyệt kết quả xét nghiệm
        approve_lab_res = self.client.post('/api/lab/result/approve', json={'chi_tiet_id': ctcd_id})
        self.assertEqual(approve_lab_res.status_code, 200)

        # Lấy ID đơn thuốc vừa tạo
        self.db.commit()
        self.cursor.execute("SELECT TOP 1 id, trang_thai FROM don_thuoc WHERE phieu_kham_id = ?", (phieu_kham_id,))
        dt = self.cursor.fetchone()
        self.assertIsNotNone(dt)
        dt_id = dt['id']

        # 6. Bệnh nhân chọn mua thuốc tại bệnh viện
        self.client.get('/logout')
        self.client.post('/login', data={'username': patient_phone, 'password': 'EmrPass@123'}, follow_redirects=True)
        opt_res = self.client.post('/api/prescription/choose-buying-option', json={
            'prescription_id': dt_id,
            'option': 'Mua tại bệnh viện'
        })
        self.assertEqual(opt_res.status_code, 200)

        # 7. Tiếp tân / Admin duyệt đơn thuốc mua tại bệnh viện
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        approve_dt_res = self.client.post('/api/prescription/approve', json={'prescription_id': dt_id})
        self.assertEqual(approve_dt_res.status_code, 200)

        # 8. Thu ngân xác nhận thanh toán hóa đơn tiền thuốc
        self.db.commit()
        self.cursor.execute("UPDATE hoa_don SET trang_thai = N'Đã thanh toán' WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%'", (phieu_kham_id,))
        self.db.commit()

        # 9. Dược sĩ đăng nhập (duocsi_1) để cấp phát thuốc và trừ kho
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'duocsi_1', 'password': 'Password@123'}, follow_redirects=True)

        pharm_page = self.client.get('/admin/pharmacy')
        self.assertEqual(pharm_page.status_code, 200)

        dispense_res = self.client.post('/api/pharmacy/dispense', json={'prescription_id': dt_id})
        self.assertEqual(dispense_res.status_code, 200)
        self.assertTrue(dispense_res.get_json().get('success'))

        # Kiểm tra tồn kho thuốc bị trừ đúng 10 viên
        self.db.commit()
        self.cursor.execute("SELECT so_luong_ton FROM thuoc WHERE id = ?", (med_id,))
        new_stock = self.cursor.fetchone()['so_luong_ton']
        self.assertEqual(new_stock, initial_stock - 10)

        # Thử nghiệm chống cấp phát lặp lại (idempotency): cấp phát lần 2 phải bị từ chối
        dispense_again = self.client.post('/api/pharmacy/dispense', json={'prescription_id': dt_id})
        self.assertEqual(dispense_again.status_code, 400)

    def test_scenario_05_patient_feedback_and_home_display(self):
        """Kịch bản 5: Bệnh nhân gửi góp ý/đánh giá -> Admin xem danh sách -> Hiển thị ngẫu nhiên trên trang Home"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        patient_phone = f"095{ts}"
        patient_cccd = f"079194{ts[-6:]}"
        
        # 1. Đăng ký & Đăng nhập bệnh nhân
        UserModel.register_patient(
            ho_ten="Võ Hoàng Yến",
            sdt=patient_phone,
            password="FeedbackPass@123",
            ngay_sinh="1994-04-04",
            gioi_tinh="Nữ",
            cccd=patient_cccd
        )
        self.cursor.execute("UPDATE tai_khoan SET da_hoan_thien_ho_so = 1 WHERE sdt = ?", (patient_phone,))
        self.db.commit()

        self.client.get('/logout')
        self.client.post('/login', data={'username': patient_phone, 'password': 'FeedbackPass@123'}, follow_redirects=True)

        # 2. Gửi góp ý phản hồi
        fb_content = f"Dịch vụ phòng khám rất tận tâm và chu đáo {ts}!"
        fb_res = self.client.post('/patient/feedbacks', data={
            'chu_de': 'Dịch vụ khám bệnh',
            'noi_dung': fb_content,
            'diem_danh_gia': '5'
        }, follow_redirects=True)
        self.assertEqual(fb_res.status_code, 200)

        # Kiểm tra lưu vào CSDL bảng phan_hoi
        self.db.commit()
        self.cursor.execute("SELECT TOP 1 * FROM phan_hoi WHERE noi_dung = ?", (fb_content,))
        saved_fb = self.cursor.fetchone()
        self.assertIsNotNone(saved_fb)

        # 3. Admin kiểm tra trang danh sách phản hồi
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        admin_fb_page = self.client.get('/admin/feedbacks')
        self.assertEqual(admin_fb_page.status_code, 200)

        # 4. Kiểm tra trang Home tải phản hồi mượt mà không bị crash
        home_res = self.client.get('/home')
        self.assertEqual(home_res.status_code, 200)

    def test_scenario_06_account_username_edit_and_login_by_phone_or_username(self):
        """Kịch bản 6: Ràng buộc đổi username, không chứa khoảng cách, đăng nhập được bằng cả SĐT lẫn username"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        test_phone = f"096{ts}"
        patient_cccd = f"079193{ts[-6:]}"
        new_username = f"user_{ts}"
        bad_username = f"bad user {ts}"
        
        # 1. Tạo tài khoản
        ok, msg = UserModel.register_patient(
            ho_ten="Phạm Gia Hưng",
            sdt=test_phone,
            password="SecurePass@123",
            ngay_sinh="1993-03-03",
            gioi_tinh="Nam",
            cccd=patient_cccd
        )
        self.assertTrue(ok)
        
        self.db.commit()
        self.cursor.execute("SELECT id FROM tai_khoan WHERE sdt = ?", (test_phone,))
        acc_id = self.cursor.fetchone()['id']

        # 2. Thử cập nhật username có khoảng trắng -> Bị từ chối
        ok_bad, msg_bad = UserModel.update_username(acc_id, bad_username)
        self.assertFalse(ok_bad)
        self.assertIn("khoảng cách", msg_bad.lower())

        # 3. Cập nhật username hợp lệ
        ok_good, msg_good = UserModel.update_username(acc_id, new_username)
        self.assertTrue(ok_good)

        # 4. Đăng nhập bằng username mới
        self.client.get('/logout')
        login_u = self.client.post('/login', data={'username': new_username, 'password': 'SecurePass@123'})
        self.assertEqual(login_u.status_code, 302)

        # 5. Đăng xuất và đăng nhập lại bằng SĐT
        self.client.get('/logout')
        login_p = self.client.post('/login', data={'username': test_phone, 'password': 'SecurePass@123'})
        self.assertEqual(login_p.status_code, 302)

    def test_scenario_07_all_admin_navigation_routes_render_ok(self):
        """Kịch bản 7: Kiểm tra tất cả các route chính của Quản trị viên render 200 OK (không crash do template/database)"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        routes_to_test = [
            '/admin/dashboard',
            '/admin/doctors',
            '/admin/patients',
            '/admin/appointments',
            '/admin/emr',
            '/admin/lab',
            '/admin/pharmacy',
            '/admin/billing',
            '/admin/staff',
            '/admin/catalogs',
            '/admin/feedbacks',
            '/admin/articles',
            '/admin/banners',
            '/admin/backups',
            '/admin/reports',
            '/admin/profile'
        ]

        for route in routes_to_test:
            with self.subTest(route=route):
                res = self.client.get(route)
                self.assertEqual(res.status_code, 200, f"Route {route} trả về status {res.status_code}")

    def test_scenario_08_staff_schedule_management_and_shift_capacity(self):
        """Kịch bản 8: Đăng ký lịch trực, kiểm tra hạn mức ca trực và tra cứu bác sĩ trực khả dụng"""
        from models.schedule_model import ScheduleModel
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'bs_noi_1', 'password': 'Password@123'}, follow_redirects=True)

        bounds = ScheduleModel.get_week_bounds()
        target_date = bounds['next_week_2'][0].strftime('%Y-%m-%d')

        # Thử đăng ký ca trực tối
        reg_res = self.client.post('/api/schedule/register', json={
            'ngay_lam_viec': target_date,
            'ca_lam_viec': 3,
            'phong_kham_id': 1,
            'ghi_chu': 'Trực ca tối phòng 101'
        })
        self.assertIn(reg_res.status_code, [200, 400])
        if reg_res.status_code == 400:
            msg = reg_res.get_json().get('message', '')
            self.assertTrue(any(w in msg for w in ['đã đủ', 'tối đa', 'đã đăng ký', 'Xung đột']))

        # Tra cứu bác sĩ trực khả dụng
        avail_res = self.client.get(f'/api/schedule/available-doctors?chuyen_khoa_id=1&ngay_hen={target_date}')
        self.assertEqual(avail_res.status_code, 200)

        # Admin kiểm tra trang quản lý nhân sự
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        staff_res = self.client.get('/admin/staff')
        self.assertEqual(staff_res.status_code, 200)

    def test_scenario_09_medical_catalogs_update_and_toggle(self):
        """Kịch bản 9: Cập nhật thông tin danh mục phòng khám và bật/tắt kích hoạt trạng thái"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        cat_res = self.client.get('/admin/catalogs')
        self.assertEqual(cat_res.status_code, 200)

        # Cập nhật thông tin phòng khám 1
        update_res = self.client.post('/api/catalog/room/update', json={
            'id': 1,
            'ten_phong': 'Phòng Khám Nội 101 (Test)',
            'chuyen_khoa_id': 1
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertTrue(update_res.get_json().get('success'))

        # Toggle tắt và bật lại
        tog1 = self.client.post('/api/catalog/room/toggle', json={'id': 1})
        self.assertEqual(tog1.status_code, 200)
        tog2 = self.client.post('/api/catalog/room/toggle', json={'id': 1})
        self.assertEqual(tog2.status_code, 200)
        self.assertEqual(tog2.get_json().get('new_status'), 1)

    def test_scenario_10_cms_article_creation_and_banner_publishing(self):
        """Kịch bản 10: Quản trị viên đăng bài viết y khoa, banner và hiển thị trang tin tức công khai"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        ts = datetime.now().strftime('%H%M%S')
        art_res = self.client.post('/admin/articles/create', data={
            'tieu_de': f'Chăm sóc sức khỏe mùa lạnh {ts}',
            'danh_muc': 'Cam nang suc khoe',
            'tom_tat': 'Bảo vệ đường hô hấp trong mùa đông.',
            'noi_dung': '<p>Nội dung chi tiết bài viết cẩm nang y tế sức khỏe...</p>',
            'trang_thai': '1'
        }, follow_redirects=True)
        self.assertEqual(art_res.status_code, 200)

        banner_res = self.client.post('/admin/banners/create', data={
            'tieu_de': f'Banner Khám Tổng Quát {ts}',
            'loai_banner': 'popup',
            'trang_thai': '1'
        }, follow_redirects=True)
        self.assertEqual(banner_res.status_code, 200)

        # Trang tin tức công khai
        pub_res = self.client.get('/articles')
        self.assertEqual(pub_res.status_code, 200)

    def test_scenario_11_system_database_backup(self):
        """Kịch bản 11: Tạo bản sao lưu cơ sở dữ liệu hệ thống từ giao diện quản trị"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        bk_page = self.client.get('/admin/backups')
        self.assertEqual(bk_page.status_code, 200)

        bk_res = self.client.post('/api/backup/create', json={'type': 'database'})
        self.assertEqual(bk_res.status_code, 200)
        data = bk_res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('.bak', data.get('message', ''))

    def test_scenario_12_multi_entity_csv_export_and_sample_templates(self):
        """Kịch bản 12: Xuất dữ liệu CSV và tải mẫu CSV cho tất cả các phân hệ quản lý"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        modules = ['patients', 'doctors', 'medicines', 'appointments', 'services', 'articles']
        for mod in modules:
            with self.subTest(module=mod):
                exp = self.client.get(f'/admin/export-csv/{mod}')
                self.assertEqual(exp.status_code, 200, f"Export CSV {mod} failed")
                self.assertIn('text/csv', exp.content_type)

                sample = self.client.get(f'/admin/download-sample-csv/{mod}')
                self.assertEqual(sample.status_code, 200, f"Sample CSV {mod} failed")

    def test_scenario_13_reports_financial_and_clinic_analytics(self):
        """Kịch bản 13: Báo cáo thống kê tài chính, lượt khám và biểu đồ phân tích"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        rep_all = self.client.get('/admin/reports')
        self.assertEqual(rep_all.status_code, 200)

        rep_filter = self.client.get('/admin/reports?from_date=2026-01-01&to_date=2026-12-31')
        self.assertEqual(rep_filter.status_code, 200)

    def test_scenario_14_emr_save_normal_and_history_retrieval(self):
        """Kịch bản 14: Bác sĩ hoàn thành khám sức khỏe nhanh (save-normal) và tra cứu hồ sơ bệnh án"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'bs_noi_1', 'password': 'Password@123'}, follow_redirects=True)

        save_res = self.client.post('/api/emr/save-normal', json={
            'patient_id': 1,
            'room_id': 1
        })
        self.assertEqual(save_res.status_code, 200)
        data = save_res.get_json()
        self.assertTrue(data.get('success'))
        ma_phieu = data.get('ma_phieu')
        self.assertTrue(ma_phieu)

        # Chi tiết phiếu khám
        detail_res = self.client.get(f'/api/emr/detail?ma_phieu={ma_phieu}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertTrue(detail_res.get_json().get('success'))

        # Lịch sử bệnh án bệnh nhân
        history_res = self.client.get('/api/emr/history?patient_id=1')
        self.assertEqual(history_res.status_code, 200)
        self.assertTrue(history_res.get_json().get('success'))

    def test_scenario_15_in_app_notifications_and_automated_reminders(self):
        """Kịch bản 15: Kiểm tra hệ thống quét nhắc lịch tự động và polling thông báo in-app"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        rem_res = self.client.post('/api/notifications/run-reminders')
        self.assertEqual(rem_res.status_code, 200)
        self.assertTrue(rem_res.get_json().get('success'))

        poll_res = self.client.get('/api/notifications/poll')
        self.assertEqual(poll_res.status_code, 200)
        self.assertTrue(poll_res.get_json().get('success'))

    def test_scenario_16_doctor_work_status_toggle(self):
        """Kịch bản 16: Bật/tắt trạng thái làm việc (Đang làm việc <-> Ngoài giờ làm việc) của bác sĩ"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        tog1 = self.client.post('/api/doctor/toggle-work-status', json={'doctor_id': 1})
        self.assertEqual(tog1.status_code, 200)
        status1 = tog1.get_json().get('new_status')
        self.assertIn(status1, ['Đang làm việc', 'Ngoài giờ làm việc'])

        tog2 = self.client.post('/api/doctor/toggle-work-status', json={'doctor_id': 1})
        self.assertEqual(tog2.status_code, 200)
        status2 = tog2.get_json().get('new_status')
        self.assertIn(status2, ['Đang làm việc', 'Ngoài giờ làm việc'])
        self.assertNotEqual(status1, status2)

    def test_scenario_17_patient_portal_views_and_feedback_submission(self):
        """Kịch bản 17: Toàn bộ cổng thông tin bệnh nhân (Patient Portal) và gửi đánh giá phản hồi"""
        ts = datetime.now().strftime('%M%S%f')[-6:]
        p_phone = f"097{ts}"
        p_cccd = f"079198{ts}"
        p_pass = "PatientPortal@123"

        ok, msg = UserModel.register_patient(
            ho_ten=f"Bệnh Nhân Portal {ts}",
            sdt=p_phone,
            password=p_pass,
            ngay_sinh="1996-06-20",
            gioi_tinh="Nữ",
            cccd=p_cccd
        )
        self.assertTrue(ok)

        self.client.get('/logout')
        login_res = self.client.post('/login', data={'username': p_phone, 'password': p_pass}, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        routes = [
            '/patient/dashboard',
            '/patient/records',
            '/patient/billing',
            '/patient/lab-results',
            '/patient/notifications',
            '/patient/profile',
            '/patient/feedbacks'
        ]
        for r in routes:
            with self.subTest(route=r):
                res = self.client.get(r)
                self.assertEqual(res.status_code, 200)

        # Gửi đánh giá phản hồi
        fb_res = self.client.post('/patient/feedbacks', data={
            'bac_si_id': '1',
            'so_sao': '5',
            'noi_dung': 'Dịch vụ khám bệnh chuyên nghiệp, bác sĩ rất tận tình!',
            'dich_vu_id': ''
        }, follow_redirects=True)
        self.assertEqual(fb_res.status_code, 200)

        # Admin xem danh sách đánh giá
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        admin_fb = self.client.get('/admin/feedbacks')
        self.assertEqual(admin_fb.status_code, 200)

    def test_scenario_18_account_management_role_toggle_and_reset(self):
        """Kịch bản 18: Quản trị tài khoản, gán phân quyền vai trò, bật/tắt kích hoạt và cấp lại mật khẩu"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        ts = datetime.now().strftime('%M%S%f')[-6:]
        staff_phone = f"092{ts}"
        staff_res = self.client.post('/admin/accounts/create-staff', data={
            'ho_ten': f'Nhân viên {ts}',
            'sdt': staff_phone,
            'vai_tro_id': '4',
            'email': f'staff_{ts}@h2tcare.vn'
        }, follow_redirects=True)
        self.assertEqual(staff_res.status_code, 200)

        self.db.commit()
        self.cursor.execute("SELECT id FROM tai_khoan WHERE sdt = ?", (staff_phone,))
        acc_row = self.cursor.fetchone()
        self.assertIsNotNone(acc_row)
        acc_id = acc_row['id']

        # Lấy thông tin tài khoản
        acc_detail = self.client.get(f'/api/admin/account/{acc_id}')
        self.assertEqual(acc_detail.status_code, 200)
        self.assertTrue(acc_detail.get_json().get('success'))

        # Đổi vai trò tài khoản sang Lễ tân (vai_tro_id = 2)
        role_res = self.client.post('/api/admin/account/set-role', json={
            'account_id': acc_id,
            'vai_tro_id': 2
        })
        self.assertEqual(role_res.status_code, 200)
        self.assertTrue(role_res.get_json().get('success'))

        # Bật/tắt trạng thái tài khoản
        tog_res = self.client.post('/api/admin/account/toggle', json={'account_id': acc_id})
        self.assertEqual(tog_res.status_code, 200)
        self.assertTrue(tog_res.get_json().get('success'))

        # Cấp lại mật khẩu mặc định (123)
        reset_res = self.client.post('/api/admin/account/reset-password', json={'account_id': acc_id})
        self.assertEqual(reset_res.status_code, 200)
        self.assertTrue(reset_res.get_json().get('success'))

    def test_scenario_19_appointment_reschedule_and_cancellation(self):
        """Kịch bản 19: Bệnh nhân đổi lịch hẹn và hủy lịch hẹn trước giờ khám"""
        ts = datetime.now().strftime('%M%S%f')[-6:]
        p_phone = f"095{ts}"
        p_cccd = f"079199{ts}"
        p_pass = "ApptFlow@123"

        ok, msg = UserModel.register_patient(
            ho_ten=f"Bệnh Nhân Hẹn {ts}",
            sdt=p_phone,
            password=p_pass,
            ngay_sinh="1994-04-14",
            gioi_tinh="Nam",
            cccd=p_cccd
        )
        self.assertTrue(ok)

        self.client.get('/logout')
        self.client.post('/login', data={'username': p_phone, 'password': p_pass}, follow_redirects=True)

        target_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        book_res = self.client.post('/api/appointment/book', json={
            'ngay_hen': target_date,
            'gio_hen': '08:30',
            'chuyen_khoa_id': 1,
            'bac_si_id': 1,
            'ly_do': 'Khám tai mũi họng theo hẹn'
        })
        self.assertEqual(book_res.status_code, 200)
        book_data = book_res.get_json()
        self.assertTrue(book_data.get('success'))
        appt_ref = book_data.get('ma_lich_hen') or book_data.get('appointment_id')

        # Đổi lịch hẹn sang ngày tiếp theo
        resched_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        resched_res = self.client.post('/api/appointment/reschedule', json={
            'appointment_id': appt_ref,
            'ngay_hen_moi': resched_date,
            'gio_hen_moi': '09:30'
        })
        self.assertEqual(resched_res.status_code, 200)
        self.assertTrue(resched_res.get_json().get('success'))

        # Hủy lịch hẹn
        cancel_res = self.client.post('/api/appointment/cancel', json={
            'appointment_id': appt_ref,
            'ly_do_huy': 'Đổi kế hoạch cá nhân'
        })
        self.assertEqual(cancel_res.status_code, 200)
        self.assertTrue(cancel_res.get_json().get('success'))

    def test_scenario_20_staff_shift_cancellation_flow(self):
        """Kịch bản 20: Bác sĩ gửi đơn xin hủy ca trực và Quản trị viên xét duyệt đơn"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'bs_noi_1', 'password': 'Password@123'}, follow_redirects=True)

        self.db.commit()
        self.cursor.execute("""
            SELECT TOP 1 llv.id 
            FROM lich_lam_viec llv
            JOIN bac_si bs ON llv.bac_si_id = bs.id
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            WHERE t.username = 'bs_noi_1' AND (llv.trang_thai_duyet = 'DA_DUYET' OR llv.trang_thai_duyet IS NULL)
        """)
        shift_row = self.cursor.fetchone()
        if shift_row:
            s_id = shift_row['id']
            req_cancel = self.client.post('/api/schedule/cancel-request', json={
                'schedule_id': s_id,
                'ly_do': 'Lý do sức khỏe đột xuất'
            })
            self.assertEqual(req_cancel.status_code, 200)
            self.assertTrue(req_cancel.get_json().get('success'))

            # Admin duyệt đơn xin hủy
            self.client.get('/logout')
            self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
            approve_res = self.client.post('/api/schedule/approve-cancellation', json={
                'schedule_id': s_id,
                'approved': True
            })
            self.assertEqual(approve_res.status_code, 200)
            self.assertTrue(approve_res.get_json().get('success'))

    def test_scenario_21_csv_data_import(self):
        """Kịch bản 21: Nhập dữ liệu phân hệ Thuốc bằng tệp CSV chuẩn UTF-8-SIG"""
        import io
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        ts = datetime.now().strftime('%H%M%S')
        csv_content = f"ten_thuoc,don_vi_tinh,gia_ban,so_luong_ton,cong_dung,huong_dan_su_dung\nThuốc Bổ Phế H2T {ts},Lọ,65000,120,Bổ phế giảm ho,Ngày uống 2 lần\n"
        data = {
            'file': (io.BytesIO(csv_content.encode('utf-8-sig')), f'test_meds_{ts}.csv')
        }
        import_res = self.client.post('/admin/import-csv/medicines', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(import_res.status_code, 200)

    def test_scenario_22_connection_resilience_and_double_close_safety(self):
        """Kịch bản 22: Cơ chế chịu lỗi kết nối CSDL, gọi đóng và rollback lặp lại an toàn không crash"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1 AS alive")
        row = cur.fetchone()
        self.assertEqual(row['alive'], 1)
        
        # Đóng kết nối
        conn.close()
        # Gọi tiếp các thao tác dọn dẹp sau khi đã đóng xem có tự động xử lý an toàn không
        conn.close()
        conn.rollback()
        conn.commit()

    def test_scenario_23_appointment_datetime_multi_format_and_shift_normalization(self):
        """Kịch bản 23: Chuẩn hóa ngày giờ đa định dạng và phân bổ ca trực chuẩn xác (12h/24h, DD/MM/YYYY)"""
        from models.appointment_model import AppointmentModel
        from datetime import date, timedelta

        today = date.today()
        # 1. Chuẩn hóa ngày
        self.assertEqual(AppointmentModel.normalize_date('2026-11-20'), '2026-11-20')
        self.assertEqual(AppointmentModel.normalize_date('20/11/2026'), '2026-11-20')
        self.assertEqual(AppointmentModel.normalize_date('20-11-2026'), '2026-11-20')

        # 2. Chuẩn hóa giờ và ca làm việc
        self.assertEqual(AppointmentModel.normalize_time('8:30'), '08:30')
        self.assertEqual(AppointmentModel.get_shift_from_time('8:30'), 1)

        self.assertEqual(AppointmentModel.normalize_time('09:15 AM'), '09:15')
        self.assertEqual(AppointmentModel.get_shift_from_time('09:15 AM'), 1)

        self.assertEqual(AppointmentModel.normalize_time('2:30 PM'), '14:30')
        self.assertEqual(AppointmentModel.get_shift_from_time('2:30 PM'), 2)

        self.assertEqual(AppointmentModel.normalize_time('07:30 PM'), '19:30')
        self.assertEqual(AppointmentModel.get_shift_from_time('07:30 PM'), 3)

        # 3. Đặt lịch khám bằng ngày DD/MM/YYYY và giờ 12h PM
        ts = datetime.now().strftime('%M%S%f')[-6:]
        p_phone = f"091{ts}"
        UserModel.register_patient(
            ho_ten=f"Bệnh Nhân Hẹn Đa Định Dạng {ts}",
            sdt=p_phone,
            password="Password@123",
            ngay_sinh="1995-05-15",
            gioi_tinh="Nam",
            cccd=f"079198{ts}"
        )

        self.client.get('/logout')
        self.client.post('/login', data={'username': p_phone, 'password': 'Password@123'}, follow_redirects=True)

        future_str = (today + timedelta(days=6)).strftime('%d/%m/%Y')
        work_d = (today + timedelta(days=6)).strftime('%Y-%m-%d')
        self.cursor.execute("DELETE FROM lich_hen WHERE bac_si_id = 1 AND ngay_hen = ? AND (gio_hen = '14:30:00' OR gio_hen = '14:30')", (work_d,))
        self.db.commit()
        book_res = self.client.post('/api/appointment/book', json={
            'ngay_hen': future_str,
            'gio_hen': '2:30 PM',
            'chuyen_khoa_id': 1,
            'bac_si_id': 1,
            'ly_do': 'Khám chuyên khoa nội'
        })
        self.assertEqual(book_res.status_code, 200)
        self.assertTrue(book_res.get_json().get('success'))

        # 4. Thử đặt lịch ngày quá khứ -> Bị từ chối
        past_str = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        past_res = self.client.post('/api/appointment/book', json={
            'ngay_hen': past_str,
            'gio_hen': '09:00',
            'chuyen_khoa_id': 1,
            'bac_si_id': 1,
            'ly_do': 'Cố tình đặt lịch quá khứ'
        })
        self.assertEqual(past_res.status_code, 400)
        self.assertIn("quá khứ", past_res.get_json().get('message', ''))

    def test_scenario_24_patient_age_calculation_multi_format_and_accuracy(self):
        """Kịch bản 24: Tính tuổi bệnh nhân chính xác từ đa định dạng ngày sinh (YYYY-MM-DD, DD/MM/YYYY)"""
        from models.patient_model import calculate_patient_age
        from datetime import date
        today = date.today()
        birth_year = today.year - 25

        # Đa dạng các cách nhập ngày sinh
        self.assertEqual(calculate_patient_age(f"{birth_year}-01-01"), 25)
        self.assertEqual(calculate_patient_age(f"01/01/{birth_year}"), 25)
        self.assertEqual(calculate_patient_age(f"01-01-{birth_year}"), 25)
        self.assertEqual(calculate_patient_age(str(birth_year)), 25)

    def test_scenario_25_reexamination_date_dynamic_delta_and_sanitization(self):
        """Kịch bản 25: Tính toán khoảng cách ngày tái khám chính xác (Sau N ngày) và chuẩn hóa ngày tái khám"""
        from models.medical_record_model import normalize_reexam_date
        from models.patient_model import PatientModel
        from datetime import date, timedelta

        # 1. Chuẩn hóa ngày tái khám
        self.assertIsNone(normalize_reexam_date(None))
        self.assertIsNone(normalize_reexam_date(''))
        self.assertEqual(normalize_reexam_date('15/12/2026'), '2026-12-15')
        self.assertEqual(normalize_reexam_date('2026-12-15'), '2026-12-15')

        # 2. Khám bệnh và hẹn tái khám sau 10 ngày
        today = date.today()
        reexam_d = (today + timedelta(days=10)).strftime('%d/%m/%Y')
        ts = datetime.now().strftime('%M%S%f')[-6:]
        p_phone = f"093{ts}"
        UserModel.register_patient(
            ho_ten=f"Bệnh Nhân Tái Khám {ts}",
            sdt=p_phone,
            password="Password@123",
            ngay_sinh="1990-10-10",
            gioi_tinh="Nữ",
            cccd=f"079199{ts}"
        )

        self.db.commit()
        self.cursor.execute("SELECT id FROM benh_nhan WHERE sdt = ?", (p_phone,))
        p_id = self.cursor.fetchone()['id']

        self.client.get('/logout')
        self.client.post('/login', data={'username': 'bs_noi_1', 'password': 'Password@123'}, follow_redirects=True)

        save_res = self.client.post('/api/emr/save', json={
            'patient_id': p_id,
            'doctor_id': 1,
            'room_id': 1,
            'reason': 'Kiểm tra sức khỏe định kỳ',
            'symptoms': 'Không có triệu chứng',
            'diagnosis': 'Z00.0 - Khám sức khỏe tổng quát',
            'icd': 'Z00.0',
            'treatment': 'Tư vấn chế độ ăn uống',
            'advice': 'Tái khám sau 10 ngày',
            'reexam_date': reexam_d,
            'medicines': [
                {'thuoc_id': 6, 'so_luong': 5, 'lieu_dung': '1 viên/ngày', 'cach_dung': 'Sau ăn'}
            ],
            'lab_services': []
        })
        self.assertEqual(save_res.status_code, 200)

        # Kiểm tra sổ y bạ hiển thị đúng khoảng cách 10 ngày thay vì số ngày cố định
        p_history = PatientModel.get_patient_history(p_id)
        self.assertTrue(len(p_history) > 0)
        self.assertIn("Sau 10 ngày", p_history[0].get('lich_tai_kham', ''))

    def test_scenario_26_invoice_payment_by_code_and_id_resilience(self):
        """Kịch bản 26: Xác nhận thanh toán viện phí linh hoạt bằng cả mã chuỗi (HD...) lẫn ID nguyên bản"""
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # Lấy một hóa đơn chưa thanh toán hoặc vừa sinh
        self.db.commit()
        self.cursor.execute("SELECT TOP 1 id, ma_hoa_don FROM hoa_don ORDER BY id DESC")
        hd_row = self.cursor.fetchone()
        if hd_row:
            pay_code_res = self.client.post('/api/billing/pay', json={
                'invoice_id': hd_row['ma_hoa_don'],
                'payment_method': 'Tiền mặt'
            })
            self.assertEqual(pay_code_res.status_code, 200)
            self.assertTrue(pay_code_res.get_json().get('success'))

    def test_scenario_27_single_patient_per_doctor_slot_enforcement(self):
        """Kịch bản 27: Chỉ nhận 1 bệnh nhân cho mỗi lịch hẹn 30 phút trong ca của bác sĩ (chặn trùng lịch)"""
        from datetime import date, timedelta
        target_date = (date.today() + timedelta(days=9)).strftime('%Y-%m-%d')
        slot_time = '10:00'

        # Dọn sạch các lịch hẹn thử nghiệm trùng ngày giờ
        self.cursor.execute("DELETE FROM lich_hen WHERE bac_si_id = 1 AND ngay_hen = ? AND gio_hen = ?", (target_date, slot_time))
        self.db.commit()

        # Bệnh nhân 1 đặt lịch thành công
        ok1, res1 = AppointmentModel.create(
            benh_nhan_id=1,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=target_date,
            gio_hen=slot_time,
            ly_do_kham="Bệnh nhân 1 khám tổng quát"
        )
        self.assertTrue(ok1, f"Bệnh nhân 1 đặt lịch thất bại: {res1}")

        # Bệnh nhân 2 cùng đặt bác sĩ 1 vào cùng khung giờ 30 phút -> Bị từ chối
        ok2, res2 = AppointmentModel.create(
            benh_nhan_id=2,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=target_date,
            gio_hen=slot_time,
            ly_do_kham="Bệnh nhân 2 đặt trùng giờ bác sĩ"
        )
        self.assertFalse(ok2)
        self.assertIn("Mỗi khung giờ 30 phút bác sĩ chỉ nhận 1 bệnh nhân", res2)

    def test_scenario_28_time_slots_status_colors_and_restrictions(self):
        """Kịch bản 28: Kiểm tra trạng thái khung giờ khám (vàng: đã có người hẹn, đỏ: ngoài giờ, xanh: còn trống)"""
        from datetime import date, timedelta
        target_date = (date.today() + timedelta(days=9)).strftime('%Y-%m-%d')
        slot_time = '10:00'

        res = self.client.get(f'/api/appointment/time-slots?date={target_date}&department_id=1&doctor_id=1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

        morning_shift = next((s for s in data['shifts'] if s['shift'] == 1), None)
        self.assertIsNotNone(morning_shift)

        # Khung giờ 10:00 đã có bệnh nhân 1 đặt -> Phải có màu vàng và không thể chọn
        booked_slot = next((s for s in morning_shift['slots'] if s['time'] == slot_time), None)
        self.assertIsNotNone(booked_slot)
        self.assertEqual(booked_slot['status'], 'booked')
        self.assertEqual(booked_slot['color'], 'yellow')
        self.assertFalse(booked_slot['selectable'])

        # Kiểm tra khung giờ quá khứ trên ngày hiện tại -> Phải có màu đỏ (ngoài giờ) và không thể chọn
        today_str = date.today().strftime('%Y-%m-%d')
        today_res = self.client.get(f'/api/appointment/time-slots?date={today_str}&department_id=1')
        self.assertEqual(today_res.status_code, 200)
        today_data = today_res.get_json()
        early_slot = today_data['shifts'][0]['slots'][0]
        self.assertEqual(early_slot['status'], 'off_duty')
        self.assertEqual(early_slot['color'], 'red')
        self.assertFalse(early_slot['selectable'])

    def test_scenario_29_reschedule_conflict_prevention_on_slot(self):
        """Kịch bản 29: Dời lịch hẹn sang khung giờ bác sĩ đã có bệnh nhân khác -> Bị từ chối"""
        from datetime import date, timedelta
        date_a = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        date_b = (date.today() + timedelta(days=11)).strftime('%Y-%m-%d')

        self.cursor.execute("DELETE FROM lich_hen WHERE bac_si_id = 1 AND ngay_hen IN (?, ?)", (date_a, date_b))
        self.db.commit()

        # Tạo lịch 1 tại date_a 08:30
        ok1, code1 = AppointmentModel.create(1, 1, 1, date_a, '08:30', 'Lịch A')
        self.assertTrue(ok1)
        # Tạo lịch 2 tại date_b 08:30
        ok2, code2 = AppointmentModel.create(2, 1, 1, date_b, '08:30', 'Lịch B')
        self.assertTrue(ok2)

        self.cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = ?", (code2,))
        appt2_id = self.cursor.fetchone()['id']

        # Dời lịch 2 sang date_a lúc 08:30 (trùng với lịch 1 của bác sĩ 1) -> Phải thất bại
        ok_resched, msg_resched = AppointmentModel.reschedule(
            appt2_id,
            new_date=date_a,
            new_time='08:30',
            user_info={'vai_tro': 'ADMIN', 'id': 1, 'ho_ten': 'Admin'}
        )
        self.assertFalse(ok_resched)
        self.assertIn("Mỗi khung giờ 30 phút bác sĩ chỉ nhận 1 bệnh nhân", msg_resched)

    def test_scenario_30_assign_doctor_conflict_prevention_on_slot(self):
        """Kịch bản 30: Phân công bác sĩ vào lịch hẹn khi bác sĩ đã có bệnh nhân trong khung giờ 30 phút -> Bị từ chối"""
        from datetime import date, timedelta
        target_date = (date.today() + timedelta(days=12)).strftime('%Y-%m-%d')

        self.cursor.execute("DELETE FROM lich_hen WHERE ngay_hen = ?", (target_date,))
        self.db.commit()

        # Lịch 1: Bác sĩ 1 phụ trách lúc 09:30
        ok1, code1 = AppointmentModel.create(1, 1, 1, target_date, '09:30', 'Lịch đã có bác sĩ')
        self.assertTrue(ok1)

        # Lịch 2: Chưa có bác sĩ phụ trách lúc 09:30
        ok2, code2 = AppointmentModel.create(2, 1, None, target_date, '09:30', 'Lịch chờ phân công')
        self.assertTrue(ok2)

        self.cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = ?", (code2,))
        appt2_id = self.cursor.fetchone()['id']

        # Thử phân công Bác sĩ 1 vào Lịch 2 -> Phải bị từ chối vì Bác sĩ 1 đã kín lịch lúc 09:30
        ok_assign, msg_assign = AppointmentModel.assign_doctor(
            appointment_id=appt2_id,
            doctor_id=1,
            user_info={'vai_tro': 'LETAN', 'id': 2, 'ho_ten': 'Tiếp tân'}
        )
        self.assertFalse(ok_assign)
        self.assertIn("Mỗi khung giờ 30 phút bác sĩ chỉ nhận 1 bệnh nhân", msg_assign)

    def test_scenario_31_doctor_creation_without_ho_ten_and_no_space_username(self):
        """Kịch bản 31: Tạo tài khoản bác sĩ không cần nhập họ tên, kiểm tra ràng buộc username không có khoảng trắng"""
        ts = datetime.now().strftime('%M%S%f')[-7:]
        test_phone = f"098{ts}"

        # Thử username có khoảng trắng -> Bị từ chối
        ok_space, msg_space = UserModel.create_doctor_account(
            sdt=test_phone,
            username='bs test_space',
            chuyen_khoa_id=1
        )
        self.assertFalse(ok_space)
        self.assertIn("không được chứa khoảng cách", msg_space)

        # Tạo không cần nhập họ tên -> Thành công, tự động gán tên mặc định
        valid_user = f"bs_{ts}"
        ok_create, msg_create = UserModel.create_doctor_account(
            ho_ten=None,
            sdt=test_phone,
            username=valid_user,
            chuyen_khoa_id=1
        )
        self.assertTrue(ok_create)

        # Kiểm tra hồ sơ bác sĩ vừa tạo
        self.cursor.execute("SELECT t.da_hoan_thien_ho_so, nv.ho_ten FROM tai_khoan t JOIN nhan_vien nv ON t.id = nv.tai_khoan_id WHERE t.username = ?", (valid_user,))
        acc = self.cursor.fetchone()
        self.db.commit()
        self.assertEqual(acc['da_hoan_thien_ho_so'], 0)
        self.assertIn(test_phone, acc['ho_ten'])

    def test_scenario_32_patient_and_doctor_schema_fallback_compatibility(self):
        """Kịch bản 32: Đảm bảo get_patient_history, get_doctor_by_id và get_staff_profile chạy an toàn kể cả khi thiếu cột"""
        history = PatientModel.get_patient_history(1)
        self.assertIsInstance(history, list)

        doctor = UserModel.get_doctor_by_id(1)
        self.assertIsNotNone(doctor)
        self.assertIn('ho_ten', doctor)
        self.assertIn('trang_thai_lam_viec', doctor)

        staff = UserModel.get_staff_profile(1)
        self.assertIsNotNone(staff)
        self.assertIn('username', staff)

    def test_scenario_33_cancel_appointment_endpoint_and_state(self):
        """Kịch bản 33: Hủy lịch hẹn khám qua API /api/appointment/cancel và cập nhật trạng thái an toàn"""
        from datetime import date, timedelta
        target_date = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
        ok, code = AppointmentModel.create(1, 1, 1, target_date, '14:00', 'Khám kiểm tra hủy hẹn')
        self.assertTrue(ok)

        appt = AppointmentModel.get_by_id(code)
        self.assertIsNotNone(appt)

        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN', 'ho_ten': 'Admin'}

        res = self.client.post('/api/appointment/cancel', json={
            'id': appt['id'],
            'ly_do': 'Bệnh nhân bận việc đột xuất'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        # Xác minh trong CSDL
        fresh_appt = AppointmentModel.get_by_id(appt['id'])
        self.assertEqual(fresh_appt['trang_thai'], 'Đã hủy')

    def test_scenario_34_dashboard_queue_and_room_filtering_data(self):
        """Kịch bản 34: Trang Dashboard trả về danh sách phòng khám và hàng đợi bệnh nhân có thuộc tính phòng khám"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN', 'ho_ten': 'Admin'}

        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('dashboard-room-filter', html)
        self.assertIn('filterDashboardQueue', html)
        self.assertIn('data-room-id', html)

if __name__ == '__main__':
    unittest.main()
