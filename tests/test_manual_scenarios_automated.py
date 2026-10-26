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

if __name__ == '__main__':
    unittest.main()
