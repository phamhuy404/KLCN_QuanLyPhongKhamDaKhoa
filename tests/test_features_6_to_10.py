"""
Bộ kiểm thử tự động toàn diện cho các chức năng 6 - 10:
6. Quản lý tài khoản và phân quyền
7. Quản lý lịch hẹn, đổi và hủy lịch
8. Quản lý phiếu chỉ định và kết quả xét nghiệm/cận lâm sàng
9. Chỉnh sửa và quản lý bệnh án điện tử (EMR)
10. Quản lý đơn thuốc, chống trừ kho lặp lại và ngăn sửa đơn đã cấp phát
"""

import unittest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from core.database import get_db
from core.audit import AuditLogger
from core.security import hash_password, verify_password
from models.user_model import UserModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel


class Features6To10TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    # =========================================================================
    # 6. QUẢN LÝ TÀI KHOẢN VÀ PHÂN QUYỀN
    # =========================================================================
    def test_01_account_management_crud_toggle_and_disabled_login(self):
        """Kiểm tra quản lý tài khoản, vô hiệu hóa và chặn đăng nhập tài khoản bị khóa"""
        ts = datetime.now().strftime('%H%M%S%f')[-6:]
        username = f"test_user_{ts}"
        sdt = f"099{ts}"
        password = "UserPass@123"

        # 1. Đăng ký tài khoản bệnh nhân mới
        ok_reg, msg_reg = UserModel.register_patient(
            ho_ten=f"Bệnh Nhân Test {ts}",
            sdt=sdt,
            ngay_sinh="1995-05-15",
            gioi_tinh="Nam",
            cccd=f"001{ts}999",
            email=f"bn_{ts}@test.local",
            bhyt=f"DN479{ts}",
            password=password
        )
        self.assertTrue(ok_reg, f"Đăng ký thất bại: {msg_reg}")

        # 2. Xác thực đăng nhập ban đầu thành công
        auth_user = UserModel.authenticate(username=sdt, password=password)
        self.assertIsNotNone(auth_user, "Tài khoản mới tạo phải đăng nhập được")
        user_id = auth_user['id']

        # 3. Lấy chi tiết tài khoản
        acc_detail = UserModel.get_account_detail(user_id)
        self.assertIsNotNone(acc_detail)
        self.assertEqual(acc_detail['username'], sdt)
        self.assertEqual(acc_detail['trang_thai'], 1)

        # 4. Quản trị viên vô hiệu hóa tài khoản
        ok_tog, new_st = UserModel.toggle_account_status(user_id, audit_user={'id': 1, 'ho_ten': 'Admin'})
        self.assertTrue(ok_tog)
        self.assertEqual(new_st, 0, "Trạng thái sau toggle phải là 0 (vô hiệu hóa)")

        # 5. Đảm bảo tài khoản bị vô hiệu hóa KHÔNG THỂ đăng nhập
        auth_disabled = UserModel.authenticate(username=sdt, password=password)
        self.assertIsNone(auth_disabled, "Tài khoản bị vô hiệu hóa không được phép đăng nhập!")

        # 6. Đặt lại mật khẩu mới
        new_pwd = "NewPassword@456"
        ok_reset, msg_reset = UserModel.reset_account_password(user_id, new_pwd, audit_user={'id': 1, 'ho_ten': 'Admin'})
        self.assertTrue(ok_reset)

        # Bật lại tài khoản và kiểm tra đăng nhập bằng mật khẩu mới
        UserModel.toggle_account_status(user_id)
        auth_new = UserModel.authenticate(username=sdt, password=new_pwd)
        self.assertIsNotNone(auth_new, "Sau khi đổi mật khẩu và kích hoạt lại, phải đăng nhập được bằng mật khẩu mới")

        # 7. Quản trị viên gán vai trò hợp lệ từ CSDL
        ok_role, msg_role = UserModel.set_account_role(user_id, role_id=2, audit_user={'id': 1, 'ho_ten': 'Admin'}) # LETAN
        self.assertTrue(ok_role)
        acc_updated = UserModel.get_account_detail(user_id)
        self.assertEqual(acc_updated['vai_tro_id'], 2)

    def test_02_account_rbac_protection(self):
        """Bảo vệ quyền truy cập: Bệnh nhân không được gọi API quản lý tài khoản"""
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 9999, 'patient_id': 9999, 'vai_tro': 'BENHNHAN', 'ho_ten': 'Bệnh nhân'}

        resp = self.client.get('/api/admin/accounts/list')
        self.assertIn(resp.status_code, [401, 403], "Bệnh nhân không được phép xem danh sách tài khoản quản trị")

        resp2 = self.client.post('/api/admin/account/toggle', json={'account_id': 1})
        self.assertEqual(resp2.status_code, 403, "Bệnh nhân không được phép toggle tài khoản")

    # =========================================================================
    # 7. QUẢN LÝ LỊCH HẸN, ĐỔI VÀ HỦY LỊCH
    # =========================================================================
    def test_03_appointment_booking_and_past_validation(self):
        """Kiểm tra đặt lịch hẹn: chặn đặt lịch quá khứ, kiểm tra lượt ca trực"""
        future_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        past_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

        # 1. Thử đặt lịch trong quá khứ -> Phải thất bại
        ok_past, msg_past = AppointmentModel.create(
            benh_nhan_id=1,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=past_date,
            gio_hen="08:30",
            ly_do_kham="Khám bệnh"
        )
        self.assertFalse(ok_past, "Không được phép đặt lịch hẹn trong quá khứ")

        # 2. Đặt lịch tương lai hợp lệ -> Thành công
        ok_fut, code_or_err = AppointmentModel.create(
            benh_nhan_id=1,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=future_date,
            gio_hen="08:30",
            ly_do_kham="Khám tổng quát"
        )
        self.assertTrue(ok_fut, f"Đặt lịch tương lai thất bại: {code_or_err}")

    def test_04_appointment_reschedule_and_cancel_ownership(self):
        """Kiểm tra đổi và hủy lịch: Bệnh nhân chỉ thao tác trên lịch của mình và trước giờ khám"""
        future_date1 = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
        future_date2 = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

        # Tạo lịch cho Bệnh nhân 1
        ok, appt_code = AppointmentModel.create(
            benh_nhan_id=1,
            chuyen_khoa_id=1,
            bac_si_id=1,
            ngay_hen=future_date1,
            gio_hen="09:00",
            ly_do_kham="Khám tim mạch"
        )
        self.assertTrue(ok)
        all_appts = AppointmentModel.get_all()
        created_appt = next(a for a in all_appts if a['ma_lich_hen'] == appt_code)
        appt_id = created_appt['id']

        # 1. Bệnh nhân 2 cố ý đổi lịch của Bệnh nhân 1 -> Bị từ chối
        user_bn2 = {'id': 202, 'patient_id': 2, 'vai_tro': 'BENHNHAN', 'ho_ten': 'Bệnh nhân 2'}
        ok_hack, msg_hack = AppointmentModel.reschedule(
            appointment_id=appt_id,
            new_date=future_date2,
            new_time="10:00",
            user_info=user_bn2
        )
        self.assertFalse(ok_hack, "Bệnh nhân không được sửa lịch của người khác")

        # 2. Bệnh nhân 1 tự đổi lịch trước giờ khám -> Thành công
        user_bn1 = {'id': 101, 'patient_id': 1, 'vai_tro': 'BENHNHAN', 'ho_ten': 'Bệnh nhân 1'}
        ok_resched, msg_resched = AppointmentModel.reschedule(
            appointment_id=appt_id,
            new_date=future_date2,
            new_time="10:00",
            ly_do="Đổi lịch do bận công tác",
            user_info=user_bn1
        )
        self.assertTrue(ok_resched, f"Bệnh nhân 1 đổi lịch thất bại: {msg_resched}")
        updated_appt = AppointmentModel.get_by_id(appt_id)
        self.assertEqual(str(updated_appt['ngay_hen'])[:10], future_date2)

        # 3. Hủy lịch hẹn: Cập nhật trạng thái 'Đã hủy', không xóa cứng
        ok_cancel, msg_cancel = AppointmentModel.cancel(
            appointment_id=appt_id,
            reason="Bệnh nhân báo hủy",
            user_info=user_bn1
        )
        self.assertTrue(ok_cancel, f"Hủy lịch thất bại: {msg_cancel}")
        cancelled_appt = AppointmentModel.get_by_id(appt_id)
        self.assertIsNotNone(cancelled_appt, "Hủy lịch không được xóa cứng bản ghi khỏi CSDL")
        self.assertEqual(cancelled_appt['trang_thai'], 'Đã hủy')

        # 4. Thử hủy lại lịch đã hủy -> Bị chặn
        ok_cancel_again, msg_cancel_again = AppointmentModel.cancel(appointment_id=appt_id, user_info=user_bn1)
        self.assertFalse(ok_cancel_again, "Không được phép hủy lại lịch đã hủy")

    # =========================================================================
    # 8. PHIẾU CHỈ ĐỊNH VÀ KẾT QUẢ XÉT NGHIỆM / CẬN LÂM SÀNG
    # =========================================================================
    def test_05_lab_order_workflow_ktv_and_doctor_approval(self):
        """Kiểm tra luồng xét nghiệm: KTV nhập kết quả, bác sĩ duyệt, chặn sửa khi đã duyệt"""
        # 1. Bác sĩ tạo phiên khám EMR có chỉ định CLS (Dịch vụ 1)
        ok_emr, pk_code = MedicalRecordModel.save_examination(
            patient_id=1,
            doctor_id=1,
            room_id=1,
            reason="Khám kiểm tra xét nghiệm",
            symptoms="Mệt mỏi kéo dài",
            diagnosis="Theo dõi thiếu máu",
            icd="D64 - Thiếu máu khác",
            treatment="Xét nghiệm huyết học",
            advice="Nghỉ ngơi",
            lab_service_ids=[1],
            medicines=[]
        )
        self.assertTrue(ok_emr, f"Tạo phiên khám EMR thất bại: {pk_code}")

        # Lấy phiếu chỉ định vừa tạo
        lab_orders = MedicalRecordModel.get_all_lab_orders()
        latest_order = lab_orders[0]
        chi_tiet_id = latest_order['chi_tiet_id']
        self.assertEqual(latest_order['trang_thai'], 'Chờ thực hiện')

        # 2. KTV cập nhật kết quả -> Chuyển trạng thái 'Chờ duyệt'
        ktv_user = {'id': 50, 'ho_ten': 'KTV Nguyễn Văn K', 'vai_tro': 'KTV'}
        ok_res, msg_res = MedicalRecordModel.update_lab_result(
            chi_tiet_id=chi_tiet_id,
            ket_qua="Chỉ số RBC: 4.5 T/L, HGB: 135 g/L (Trong giới hạn bình thường)",
            ktv_name=ktv_user['ho_ten'],
            audit_user=ktv_user
        )
        self.assertTrue(ok_res, f"KTV nhập kết quả thất bại: {msg_res}")
        item_after_ktv = MedicalRecordModel.get_lab_item_by_id(chi_tiet_id)
        self.assertEqual(item_after_ktv['trang_thai'], 'Chờ duyệt')

        # 3. Bác sĩ duyệt kết quả -> Chuyển trạng thái 'Đã duyệt'
        doc_user = {'id': 10, 'ho_ten': 'BS CK1 Trần Bác Sĩ', 'vai_tro': 'BACSI'}
        ok_appr, msg_appr = MedicalRecordModel.approve_lab_result(
            chi_tiet_id=chi_tiet_id,
            doctor_name=doc_user['ho_ten'],
            approval_note="Kết quả xét nghiệm bình thường, đủ điều kiện kết luận.",
            audit_user=doc_user
        )
        self.assertTrue(ok_appr, f"Bác sĩ duyệt thất bại: {msg_appr}")
        item_approved = MedicalRecordModel.get_lab_item_by_id(chi_tiet_id)
        self.assertEqual(item_approved['trang_thai'], 'Đã duyệt')
        self.assertEqual(item_approved['bac_si_duyet'], doc_user['ho_ten'])

        # 4. Kiểm tra chặn sửa kết quả đã duyệt
        ok_edit_again, msg_edit_again = MedicalRecordModel.update_lab_result(
            chi_tiet_id=chi_tiet_id,
            ket_qua="Cố ý sửa kết quả đã duyệt",
            audit_user=ktv_user
        )
        self.assertFalse(ok_edit_again, "Không được phép sửa kết quả xét nghiệm đã được duyệt!")

        # 5. Bệnh nhân chỉ xem được kết quả đã duyệt
        bn_results = MedicalRecordModel.get_lab_orders_by_patient(patient_id=1, approved_only=True)
        for r in bn_results:
            self.assertEqual(r['trang_thai'], 'Đã duyệt')

    # =========================================================================
    # 9. CHỈNH SỬA VÀ QUẢN LÝ BỆNH ÁN ĐIỆN TỬ
    # =========================================================================
    def test_06_emr_update_and_audit_history(self):
        """Bác sĩ cập nhật bệnh án EMR, lưu vết trước/sau trong audit_log"""
        # Tạo bệnh án EMR
        ok_emr, pk_code = MedicalRecordModel.save_examination(
            patient_id=1,
            doctor_id=1,
            room_id=1,
            reason="Đau bụng âm ỉ",
            symptoms="Đau vùng thượng vị",
            diagnosis="Viêm dạ dày cấp",
            icd="K29.0 - Viêm dạ dày cấp",
            treatment="Điều trị nội khoa",
            advice="Ăn đồ mềm"
        )
        self.assertTrue(ok_emr)

        # Tìm ID phiếu khám
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id FROM phieu_kham WHERE ma_phieu = ?', (pk_code,))
        pk_id = cur.fetchone()['id']
        conn.close()

        # Bác sĩ cập nhật chẩn đoán và hướng điều trị
        doc_user = {'id': 10, 'ho_ten': 'BS CK1 Trần Bác Sĩ', 'vai_tro': 'BACSI'}
        new_diag = "Viêm loét dạ dày tá tràng có vi khuẩn HP"
        new_icd = "K25 - Loét dạ dày"
        new_treat = "Phác đồ 4 thuốc có Bismuth trong 14 ngày"

        ok_upd, msg_upd = MedicalRecordModel.update_examination(
            record_id=pk_id,
            doctor_id=1,
            diagnosis=new_diag,
            icd=new_icd,
            treatment=new_treat,
            advice="Tuyệt đối kiêng bia rượu, tái khám sau 14 ngày",
            reexam_date=(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
            reason="Bổ sung kết quả nội soi dạ dày có HP (+)",
            audit_user=doc_user
        )
        self.assertTrue(ok_upd, f"Cập nhật EMR thất bại: {msg_upd}")

        # Xác minh dữ liệu đã cập nhật trong CSDL
        rec_updated = MedicalRecordModel.get_examination_by_id(pk_id)
        self.assertEqual(rec_updated['chan_doan_so_bo'], new_diag)
        self.assertEqual(rec_updated['chan_doan_icd'], new_icd)

        # Xác minh audit log được lưu đầy đủ trước và sau
        logs = AuditLogger.get_logs(table_name='phieu_kham', row_id=pk_id)
        self.assertGreater(len(logs), 0, "Phải có bản ghi audit log khi sửa bệnh án EMR")
        latest_log = logs[0]
        self.assertEqual(latest_log['action'], 'UPDATE_EMR')
        self.assertIn("Viêm dạ dày cấp", latest_log['before_json'])
        self.assertIn(new_diag, latest_log['after_json'])

    # =========================================================================
    # 10. QUẢN LÝ ĐƠN THUỐC, CHỐNG TRỪ KHO LẶP LẠI & CHẶN SỬA ĐƠN ĐÃ CẤP
    # =========================================================================
    def test_07_prescription_safe_dispense_and_prevent_double_dispense(self):
        """Cấp phát thuốc an toàn, trừ kho chính xác, chống cấp phát lặp lại (double-dispense)"""
        # Tạo đơn thuốc mới qua EMR với Thuốc 1 (Paracetamol, tồn kho ban đầu)
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, ten_thuoc, so_luong_ton FROM thuoc WHERE id = 1')
        t1 = cur.fetchone()
        t1_id = t1['id']
        t1_ton_ban_dau = t1['so_luong_ton']
        conn.close()

        # Tạo phiếu khám với đơn thuốc 5 viên
        qty_order = 5
        ok_emr, pk_code = MedicalRecordModel.save_examination(
            patient_id=1,
            doctor_id=1,
            room_id=1,
            reason="Sốt siêu vi",
            symptoms="Sốt 38.5 độ",
            diagnosis="Sốt do virus",
            icd="B34.9",
            treatment="Hạ sốt",
            advice="Uống nhiều nước",
            medicines=[{'thuoc_id': t1_id, 'so_luong': qty_order, 'lieu_dung': '1 viên/lần', 'cach_dung': 'Uống khi sốt'}]
        )
        self.assertTrue(ok_emr)

        # Lấy mã đơn thuốc vừa tạo
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT dt.id, dt.ma_don_thuoc, dt.trang_thai FROM don_thuoc dt JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id WHERE pk.ma_phieu = ?', (pk_code,))
        dt_row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(dt_row)
        dt_id = dt_row['id']
        dt_code = dt_row['ma_don_thuoc']

        # 1. Bác sĩ cập nhật đơn thuốc khi CHƯA cấp phát -> Thành công
        doc_user = {'id': 10, 'ho_ten': 'Bác sĩ kê đơn', 'vai_tro': 'BACSI'}
        ok_upd_dt, msg_upd_dt = PharmacyModel.update_prescription(
            prescription_id=dt_id,
            medicines=[{'thuoc_id': t1_id, 'so_luong': 10, 'lieu_dung': '1 viên/lần', 'cach_dung': 'Uống khi sốt > 38.5'}],
            advice="Nghỉ ngơi và chườm ấm",
            reason="Tăng số lượng thuốc hạ sốt dự phòng",
            audit_user=doc_user
        )
        self.assertTrue(ok_upd_dt, f"Cập nhật đơn thuốc chưa cấp thất bại: {msg_upd_dt}")

        # 2. Dược sĩ xuất thuốc lần 1 -> Thành công, trừ 10 viên trong kho
        duocsi_user = {'id': 30, 'ho_ten': 'Dược sĩ Lê Văn D', 'vai_tro': 'DUOCSI'}
        ok_disp, msg_disp = PharmacyModel.dispense_prescription(dt_id, audit_user=duocsi_user)
        self.assertTrue(ok_disp, f"Xuất thuốc lần 1 thất bại: {msg_disp}")

        # Kiểm tra tồn kho sau lần 1
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT so_luong_ton FROM thuoc WHERE id = ?', (t1_id,))
        t1_ton_sau_lan_1 = cur.fetchone()['so_luong_ton']
        self.assertEqual(t1_ton_sau_lan_1, t1_ton_ban_dau - 10, "Tồn kho phải giảm chính xác 10 viên")

        # 3. CHỐNG DOUBLE-DISPENSE: Dược sĩ xuất thuốc lần 2 trên cùng đơn -> BỊ TỪ CHỐI
        ok_disp2, msg_disp2 = PharmacyModel.dispense_prescription(dt_id, audit_user=duocsi_user)
        self.assertFalse(ok_disp2, "Không được phép cấp phát lần 2 trên đơn đã xuất thuốc!")
        self.assertIn("đã được cấp phát trước đó", msg_disp2)

        # Xác minh tồn kho KHÔNG bị trừ thêm lần nữa
        cur.execute('SELECT so_luong_ton FROM thuoc WHERE id = ?', (t1_id,))
        t1_ton_sau_lan_2 = cur.fetchone()['so_luong_ton']
        self.assertEqual(t1_ton_sau_lan_2, t1_ton_sau_lan_1, "Tồn kho không được phép bị trừ thêm khi thao tác gửi lại")

        # 4. NGĂN CHỈNH SỬA ĐƠN ĐÃ CẤP PHÁT: Bác sĩ thử sửa đơn đã cấp thuốc -> BỊ TỪ CHỐI
        ok_edit_dispensed, msg_edit_dispensed = PharmacyModel.update_prescription(
            prescription_id=dt_id,
            medicines=[{'thuoc_id': t1_id, 'so_luong': 20}],
            audit_user=doc_user
        )
        self.assertFalse(ok_edit_dispensed, "Đơn thuốc đã cấp phát không được phép chỉnh sửa trực tiếp!")
        self.assertIn("không thể chỉnh sửa trực tiếp", msg_edit_dispensed)

        # 5. HỦY / ĐIỀU CHỈNH ĐƠN CÓ LƯU VẾT VÀ HOÀN KHO AN TOÀN
        ok_cancel_dt, msg_cancel_dt = PharmacyModel.cancel_or_adjust_prescription(
            prescription_id=dt_id,
            reason="Bệnh nhân dị ứng với thành phần thuốc, bác sĩ thu hồi đơn",
            restore_stock=True,
            audit_user=doc_user
        )
        self.assertTrue(ok_cancel_dt, f"Hủy đơn có hoàn kho thất bại: {msg_cancel_dt}")

        # Kiểm tra tồn kho đã được hoàn lại 10 viên
        cur.execute('SELECT so_luong_ton FROM thuoc WHERE id = ?', (t1_id,))
        t1_ton_sau_hoan = cur.fetchone()['so_luong_ton']
        self.assertEqual(t1_ton_sau_hoan, t1_ton_ban_dau, "Sau khi hủy đơn có hoàn kho, số lượng tồn phải trở về ban đầu")
        conn.close()

    def test_08_banner_and_doctor_profile_privacy(self):
        """Kiểm tra quản lý banner trang chủ và phân quyền riêng tư hồ sơ bác sĩ."""
        from models.banner_model import BannerModel

        # 1. Kiểm tra CRUD banner
        ok_create, msg_create = BannerModel.create({
            'tieu_de': 'Khám sức khỏe công nghệ cao 2026',
            'phu_de': 'Ưu đãi đặc biệt',
            'mo_ta': 'Gói khám tầm soát sức khỏe toàn diện cho gia đình',
            'hinh_anh': 'https://images.unsplash.com/photo-test',
            'link_lien_ket': '/booking',
            'text_nut': 'Đăng ký ngay',
            'thu_tu': 99,
            'trang_thai': 1
        })
        self.assertTrue(ok_create, f"Tạo banner thất bại: {msg_create}")

        banners = BannerModel.get_all()
        created_banner = next((b for b in banners if b['tieu_de'] == 'Khám sức khỏe công nghệ cao 2026'), None)
        self.assertIsNotNone(created_banner, "Banner vừa tạo phải xuất hiện trong danh sách")

        # 2. Toggle trạng thái banner
        ok_toggle, new_status = BannerModel.toggle_status(created_banner['id'])
        self.assertTrue(ok_toggle)
        self.assertEqual(new_status, 0)

        # 3. Xóa banner dọn dẹp
        ok_del, _ = BannerModel.delete(created_banner['id'])
        self.assertTrue(ok_del)

        # 4. Kiểm tra phân quyền bác sĩ: Bác sĩ chỉ xem được hồ sơ của chính mình
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 2, 'username': 'bs_quan', 'vai_tro': 'BACSI', 'bac_si_id': 1}

        res_own = self.client.get('/admin/doctors/1')
        self.assertEqual(res_own.status_code, 200, "Bác sĩ phải xem được hồ sơ của chính mình")

        res_other = self.client.get('/admin/doctors/2')
        self.assertEqual(res_other.status_code, 302, "Bác sĩ xem hồ sơ bác sĩ khác phải bị điều hướng về hồ sơ của mình")
        self.assertEqual(res_other.headers.get('Location'), '/admin/doctors/1')

    def test_09_multi_format_and_url_image_recognition(self):
        """Kiểm tra nhận diện đa định dạng ảnh (PNG, GIF, BMP, TIFF, SVG), Base64, URL và avatar bệnh nhân."""
        import base64
        import io
        from PIL import Image
        from core.image_service import process_image_input, save_and_compress_image, delete_uploaded_image

        # 1. Kiểm tra nén các định dạng ảnh khác nhau sang WebP
        for fmt in ['PNG', 'BMP', 'GIF', 'TIFF']:
            im = Image.new('RGB', (100, 100), color='blue')
            buf = io.BytesIO()
            im.save(buf, format=fmt)
            raw_bytes = buf.getvalue()

            web_path, err = process_image_input(raw_bytes, category='benh_nhan', quality=80)
            self.assertIsNone(err, f"Xử lý định dạng {fmt} không được có lỗi: {err}")
            self.assertTrue(web_path.endswith('.webp'), f"Định dạng {fmt} phải được nén thành file .webp")
            delete_uploaded_image(web_path)

        # 2. Kiểm tra định dạng SVG vector
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="green" /></svg>'
        web_svg, err_svg = process_image_input(svg_content, category='bai_viet')
        self.assertIsNone(err_svg)
        self.assertTrue(web_svg.endswith('.svg'), "Định dạng SVG phải được lưu dạng .svg an toàn")
        delete_uploaded_image(web_svg)

        # 3. Kiểm tra Base64 Data URI
        im = Image.new('RGB', (80, 80), color='purple')
        buf = io.BytesIO()
        im.save(buf, format='PNG')
        data_uri = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

        web_b64, err_b64 = process_image_input(data_uri, category='bac_si', quality=85)
        self.assertIsNone(err_b64)
        self.assertTrue(web_b64.endswith('.webp'), "Chuỗi Base64 Data URI phải được giải mã và nén thành .webp")
        delete_uploaded_image(web_b64)

        # 4. Kiểm tra URL ảnh ngoại tuyến / trực tuyến (fallback an toàn)
        url_input = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200"
        web_url, err_url = process_image_input(url_input, category='banners', quality=82)
        self.assertIsNone(err_url)
        self.assertTrue(web_url.startswith('/static/uploads/') or web_url.startswith('http'), "URL phải được tải nén hoặc fallback an toàn")
        if web_url.startswith('/static/uploads/'):
            delete_uploaded_image(web_url)

        # 5. Kiểm tra cập nhật avatar bệnh nhân qua endpoint /patient/profile/avatar
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = {'id': 5, 'username': '0901234567', 'vai_tro': 'BENHNHAN', 'benh_nhan_id': 1}

        res_post = self.client.post('/patient/profile/avatar', data={
            'avatar_url': 'https://images.unsplash.com/photo-sample'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn('Cập nhật ảnh đại diện thành công', res_post.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()

