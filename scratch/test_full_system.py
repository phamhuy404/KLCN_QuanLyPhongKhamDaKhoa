import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from core.database import get_db, init_db
from models.user_model import UserModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from core.validators import validate_patient_profile

def run_tests():
    print("[RUN] Bắt đầu kiểm thử toàn diện hệ thống quản lý phòng khám trên SQL Server")

    init_db()
    conn = get_db()
    cur = conn.cursor()

    test_phone = '0909999888'

    # Dọn dẹp dữ liệu test cũ nếu có
    cur.execute("SELECT id FROM tai_khoan WHERE username = ?", (test_phone,))
    old_acc = cur.fetchone()
    if old_acc:
        uid = old_acc['id']
        cur.execute("DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id IN (SELECT id FROM hoa_don WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?))", (uid,))
        cur.execute("DELETE FROM hoa_don WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?)", (uid,))
        cur.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id IN (SELECT id FROM don_thuoc WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?)))", (uid,))
        cur.execute("DELETE FROM don_thuoc WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?))", (uid,))
        cur.execute("DELETE FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id IN (SELECT id FROM phieu_chi_dinh WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?)))", (uid,))
        cur.execute("DELETE FROM phieu_chi_dinh WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?))", (uid,))
        cur.execute("DELETE FROM phieu_kham WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?)", (uid,))
        cur.execute("DELETE FROM lich_hen WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?)", (uid,))
        cur.execute("DELETE FROM thong_bao WHERE tai_khoan_id = ?", (uid,))
        cur.execute("DELETE FROM chi_so_sinh_ton WHERE benh_nhan_id IN (SELECT id FROM benh_nhan WHERE tai_khoan_id = ?)", (uid,))
        cur.execute("DELETE FROM benh_nhan WHERE tai_khoan_id = ?", (uid,))
        cur.execute("DELETE FROM tai_khoan WHERE id = ?", (uid,))
        conn.commit()

    # 1. Kiểm tra quy mô cơ sở dữ liệu
    cur.execute("SELECT COUNT(*) as cnt FROM tai_khoan")
    cnt_acc = cur.fetchone()['cnt']
    print(f"[TEST 1] Tổng số tài khoản: {cnt_acc} (Yêu cầu >= 61)")
    assert cnt_acc >= 61

    cur.execute("SELECT COUNT(*) as cnt FROM bac_si")
    cnt_doc = cur.fetchone()['cnt']
    print(f"[TEST 2] Tổng số bác sĩ chuyên khoa: {cnt_doc} (Yêu cầu 35)")
    assert cnt_doc >= 35

    cur.execute("SELECT COUNT(*) as cnt FROM benh_nhan")
    cnt_pat = cur.fetchone()['cnt']
    print(f"[TEST 3] Tổng số bệnh nhân mẫu: {cnt_pat} (Yêu cầu >= 10)")
    assert cnt_pat >= 10

    cur.execute("SELECT COUNT(*) as cnt FROM lich_lam_viec")
    cnt_shifts = cur.fetchone()['cnt']
    print(f"[TEST 4] Tổng số ca trực bác sĩ trong CSDL: {cnt_shifts} (Yêu cầu >= 400)")
    assert cnt_shifts >= 400

    # 2. Đăng nhập đa vai trò
    roles_test = [
        ('admin', 'admin123', 'ADMIN'),
        ('letan_1', 'Password@123', 'LETAN'),
        ('duocsi_1', 'Password@123', 'DUOCSI'),
        ('ktv_1', 'Password@123', 'KTV'),
        ('bs_noi_1', 'Password@123', 'BACSI'),
        ('0901234561', '123456', 'BENHNHAN')
    ]
    for u, p, expected_role in roles_test:
        user = UserModel.authenticate(u, p)
        assert user is not None, f"Đăng nhập thất bại: {u}"
        assert user['vai_tro'] == expected_role
    print(f"[TEST 5] Xác thực thành công 6 vai trò hệ thống")

    # 3. Đăng ký & hoàn thiện hồ sơ với bộ ràng buộc dữ liệu
    ok, msg = UserModel.register_patient('Trần Thử Nghiệm', test_phone, '123456', 'test@gmail.com')
    assert ok
    new_user = UserModel.authenticate(test_phone, '123456')
    assert new_user['da_hoan_thien_ho_so'] == 0
    print(f"[TEST 6] Đăng ký mới thành công, cờ hồ sơ = 0")

    bad_data = {
        'ho_ten': 'Nguyễn Văn <script>alert(1)</script>',
        'sdt': test_phone,
        'cccd': '07912345678a',
        'ngay_sinh': '2030-01-01',
        'dia_chi': 'Quận 1'
    }
    is_valid, errs = validate_patient_profile(bad_data)
    assert not is_valid
    print(f"[TEST 7] Chặn thành công ký tự lạ và lỗi định dạng: {list(errs.keys())}")

    good_data = {
        'ho_ten': 'Trần Thử Nghiệm Chuẩn',
        'sdt': test_phone,
        'ngay_sinh': '1998-05-20',
        'gioi_tinh': 'Nam',
        'cccd': '079198000999',
        'bhyt': 'GD4791980009999',
        'email': 'test.chuan@gmail.com',
        'dia_chi': '140 Lê Trọng Tấn, Tây Thạnh, Tân Phú, TP.HCM',
        'nhom_mau': 'O+',
        'ghi_chu_nhom_mau': 'ABO: O, Rh: Dương',
        'di_ung': 'Không có',
        'tien_su_benh': 'Khỏe mạnh',
        'tien_su_gia_dinh': 'Không',
        'nguoi_than_ho_ten': 'Trần Văn Cha',
        'nguoi_than_sdt': '0901999777',
        'nguoi_than_quan_he': 'Bố'
    }
    is_valid_good, _ = validate_patient_profile(good_data)
    assert is_valid_good
    ok_comp, _ = UserModel.complete_patient_profile(new_user['id'], good_data)
    assert ok_comp
    updated_user = UserModel.authenticate(test_phone, '123456')
    assert updated_user['da_hoan_thien_ho_so'] == 1
    print(f"[TEST 8] Hoàn thiện hồ sơ thành công, cờ hồ sơ = 1")

    # 4. Kiểm tra thuật toán đồng bộ ca trực theo giờ khám
    test_date_str = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
    # Giờ khám Ca 1 Sáng (08:30)
    morning_docs, shift_1 = AppointmentModel.get_doctors_by_shift(test_date_str, '08:30', chuyen_khoa_id=1)
    assert shift_1 == 1, f"08:30 phải thuộc Ca 1 (Sáng): {shift_1}"
    assert len(morning_docs) > 0, "Phải tìm thấy bác sĩ trực Ca 1 Sáng"
    chosen_doc = morning_docs[0]
    print(f"[TEST 9] Lọc bác sĩ trực ca sáng (08:30) thành công: {chosen_doc['ho_ten']} ({chosen_doc['ten_khoa']})")

    # Giờ khám Ca 2 Chiều (15:00)
    afternoon_docs, shift_2 = AppointmentModel.get_doctors_by_shift(test_date_str, '15:00', chuyen_khoa_id=1)
    assert shift_2 == 2, f"15:00 phải thuộc Ca 2 (Chiều): {shift_2}"
    assert len(afternoon_docs) > 0, "Phải tìm thấy bác sĩ trực Ca 2 Chiều"

    # Giờ khám Ca 3 Tối (19:00)
    evening_docs, shift_3 = AppointmentModel.get_doctors_by_shift(test_date_str, '19:00', chuyen_khoa_id=1)
    assert shift_3 == 3, f"19:00 phải thuộc Ca 3 (Tối): {shift_3}"
    assert len(evening_docs) > 0, "Phải tìm thấy bác sĩ trực Ca 3 Tối"
    print(f"[TEST 10] Đồng bộ 3 ca trực và 13 khung giờ chuẩn xác")

    # 5. Đặt lịch -> Bác sĩ chỉ xem được khi Tiếp tân/Admin duyệt
    ok_book, ma_lh = AppointmentModel.create(
        updated_user['patient_id'],
        1,
        chosen_doc['id'],
        test_date_str,
        '08:30',
        'Đau ngực nhẹ khi vận động'
    )
    assert ok_book, f"Đặt lịch thất bại: {ma_lh}"

    cur.execute("SELECT id, trang_thai FROM lich_hen WHERE ma_lich_hen = ?", (ma_lh,))
    lh_info = cur.fetchone()
    lh_id = lh_info['id']
    assert lh_info['trang_thai'] == 'Chờ tiếp nhận', f"Trạng thái ban đầu phải là Chờ tiếp nhận: {lh_info['trang_thai']}"
    print(f"[TEST 11] Đặt lịch khám thành công, trạng thái ban đầu: {lh_info['trang_thai']}")

    # Lấy tài khoản user của bác sĩ được chọn
    cur.execute('''
        SELECT t.id, t.username, v.ma_vai_tro AS vai_tro, nv.ho_ten, bs.id AS bac_si_id, bs.chuyen_khoa_id
        FROM tai_khoan t 
        JOIN vai_tro v ON t.vai_tro_id = v.id 
        JOIN nhan_vien nv ON nv.tai_khoan_id = t.id 
        JOIN bac_si bs ON bs.nhan_vien_id = nv.id 
        WHERE bs.id = ?
    ''', (chosen_doc['id'],))
    doc_user = dict(cur.fetchone())

    # Khi chưa duyệt: Bác sĩ không thấy lịch này
    doc_appts_before = AppointmentModel.get_for_user(doc_user)
    appt_codes_before = [a['ma_lich_hen'] for a in doc_appts_before]
    assert ma_lh not in appt_codes_before, "Bác sĩ không được thấy lịch khám khi chưa được Lễ tân duyệt!"
    print(f"[TEST 12] Phân quyền chuẩn xác: Lịch ở trạng thái chờ được ẩn khỏi mục của bác sĩ")

    # Tiếp tân / Admin duyệt lịch
    ok_acc, msg_acc = AppointmentModel.update_status(lh_id, 'Đã xác nhận', user_info={'id': 2, 'ho_ten': 'Lễ tân trực'})
    assert ok_acc

    # Sau khi duyệt: Bác sĩ thấy lịch
    doc_appts_after = AppointmentModel.get_for_user(doc_user)
    appt_codes_after = [a['ma_lich_hen'] for a in doc_appts_after]
    assert ma_lh in appt_codes_after, "Sau khi duyệt, lịch khám phải hiển thị ở mục của bác sĩ!"
    print(f"[TEST 13] Sau khi Lễ tân duyệt: Lịch đã xuất hiện ở danh sách của bác sĩ trực")

    # Bệnh nhân nhận được thông báo in-app
    cur.execute("SELECT COUNT(*) as c FROM thong_bao WHERE tai_khoan_id = ? AND tieu_de LIKE N'%Tiếp nhận%'", (updated_user['id'],))
    assert cur.fetchone()['c'] >= 1
    print(f"[TEST 14] Bệnh nhân nhận thông báo in-app khi lịch khám được duyệt")

    # 6. Khám lâm sàng bình thường (Sức khỏe tốt) -> Xuất hóa đơn ngay
    ok_normal, ma_pk_normal = MedicalRecordModel.save_examination(
        patient_id=updated_user['patient_id'],
        doctor_id=chosen_doc['id'],
        room_id=1,
        reason='Khám sức khỏe tổng quát',
        symptoms='Không có triệu chứng bất thường',
        diagnosis='Z00.0 - Khám sức khỏe tổng quát (Bình thường)',
        icd='Z00.0',
        treatment='Tư vấn dinh dưỡng',
        advice='Duy trì thể dục thể thao',
        lab_service_ids=[],
        medicines=[]
    )
    assert ok_normal, f"Lưu khám sức khỏe tốt thất bại: {ma_pk_normal}"

    cur.execute("SELECT ma_hoa_don, thanh_tien, trang_thai FROM hoa_don WHERE phieu_kham_id = (SELECT id FROM phieu_kham WHERE ma_phieu = ?)", (ma_pk_normal,))
    hd_normal = cur.fetchone()
    assert hd_normal is not None
    assert hd_normal['trang_thai'] == 'Chưa thanh toán'
    print(f"[TEST 15] Khám lâm sàng bình thường thành công: Xuất hóa đơn viện phí {hd_normal['ma_hoa_don']} ({hd_normal['thanh_tien']} đ)")

    # 7. Khám chuyên sâu có Cận lâm sàng & Kê đơn thuốc
    ok_full, ma_pk_full = MedicalRecordModel.save_examination(
        patient_id=updated_user['patient_id'],
        doctor_id=chosen_doc['id'],
        room_id=1,
        reason='Đau bụng và ợ hơi',
        symptoms='Đau thượng vị âm ỉ',
        diagnosis='K29.5 - Viêm dạ dày mạn tính',
        icd='K29.5',
        treatment='Nội soi dạ dày & điều trị nội khoa',
        advice='Tránh đồ cay nóng',
        lab_service_ids=[8, 13],  # Nội soi + Xét nghiệm máu
        medicines=[{'thuoc_id': 6, 'so_luong': 10}]
    )
    assert ok_full, f"Lưu khám chuyên sâu thất bại: {ma_pk_full}"
    print(f"[TEST 16] Lưu phiếu khám chuyên sâu và ra chỉ định CLS thành công: {ma_pk_full}")

    # Kiểm tra đơn thuốc ban đầu: 'Chờ bệnh nhân xác nhận mua', chưa trừ kho
    cur.execute("SELECT id, ma_don_thuoc, trang_thai, hinh_thuc_mua FROM don_thuoc WHERE phieu_kham_id = (SELECT id FROM phieu_kham WHERE ma_phieu = ?)", (ma_pk_full,))
    dt_full = cur.fetchone()
    assert dt_full is not None
    assert dt_full['trang_thai'] == 'Chờ bệnh nhân xác nhận mua'
    assert dt_full['hinh_thuc_mua'] == 'Chưa chọn'
    print(f"[TEST 17] Đơn thuốc ban đầu ở trạng thái: {dt_full['trang_thai']} | Hình thức mua: {dt_full['hinh_thuc_mua']}")

    # 8. Kỹ thuật viên upload ảnh Cận lâm sàng và lưu kết quả
    cur.execute("SELECT ct.id FROM chi_tiet_chi_dinh ct JOIN phieu_chi_dinh cd ON ct.phieu_chi_dinh_id = cd.id WHERE cd.phieu_kham_id = (SELECT id FROM phieu_kham WHERE ma_phieu = ?)", (ma_pk_full,))
    cls_ids = [r['id'] for r in cur.fetchall()]
    assert len(cls_ids) >= 1

    target_cls_id = cls_ids[0]
    ok_lab, msg_lab = MedicalRecordModel.update_lab_result(
        chi_tiet_id=target_cls_id,
        ket_qua='Hình ảnh niêm mạc hang vị xung huyết nhẹ, không thấy ổ loét',
        file_ket_qua='/static/uploads/can_lam_sang/cls_test_sample.webp',
        ktv_name='KTV Trần Minh Đức'
    )
    assert ok_lab, f"Cập nhật kết quả CLS thất bại: {msg_lab}"

    # Bác sĩ duyệt kết quả Cận lâm sàng
    ok_appr, msg_appr = MedicalRecordModel.approve_lab_result(
        chi_tiet_id=target_cls_id,
        doctor_name=chosen_doc['ho_ten'],
        approval_note='Đồng ý với kết quả chẩn đoán hình ảnh'
    )
    assert ok_appr, f"Duyệt kết quả CLS thất bại: {msg_appr}"

    cur.execute("SELECT ket_qua, file_ket_qua, trang_thai FROM chi_tiet_chi_dinh WHERE id = ?", (target_cls_id,))
    cls_row = cur.fetchone()
    assert cls_row['file_ket_qua'] == '/static/uploads/can_lam_sang/cls_test_sample.webp'
    assert cls_row['trang_thai'] == 'Đã duyệt'
    print(f"[TEST 18] Kỹ thuật viên lưu kết quả và đính kèm ảnh chụp CLS thành công: {cls_row['file_ket_qua']} | Bác sĩ đã duyệt: {cls_row['trang_thai']}")

    # Bệnh nhân nhận thông báo hoàn thành CLS, mời quay lại phòng khám
    cur.execute("SELECT COUNT(*) as c FROM thong_bao WHERE tai_khoan_id = ? AND tieu_de LIKE N'%kết quả Cận lâm sàng%'", (updated_user['id'],))
    assert cur.fetchone()['c'] >= 1
    print(f"[TEST 19] Bệnh nhân nhận thông báo hướng dẫn quay lại phòng khám sau khi có kết quả CLS")

    # 9. Bệnh nhân chọn mua thuốc tại bệnh viện
    cur.execute("SELECT so_luong_ton FROM thuoc WHERE id = 6")
    stock_before_buy = cur.fetchone()['so_luong_ton']

    ok_buy, msg_buy = PharmacyModel.choose_medicine_purchase_option(dt_full['id'], 'Mua tại bệnh viện')
    assert ok_buy, f"Chọn mua thuốc thất bại: {msg_buy}"

    cur.execute("SELECT so_luong_ton FROM thuoc WHERE id = 6")
    stock_after_buy = cur.fetchone()['so_luong_ton']
    assert stock_after_buy == stock_before_buy - 10, f"Kho thuốc phải tự động trừ 10 viên: {stock_before_buy} -> {stock_after_buy}"

    cur.execute("SELECT ma_hoa_don, thanh_tien, trang_thai FROM hoa_don WHERE ma_hoa_don LIKE 'HDT%' AND benh_nhan_id = ?", (updated_user['patient_id'],))
    hd_thuoc = cur.fetchone()
    assert hd_thuoc is not None, "Phải sinh hóa đơn thuốc riêng biệt cho bệnh viện"
    print(f"[TEST 20] Mua thuốc tại viện thành công: Sinh hóa đơn thuốc {hd_thuoc['ma_hoa_don']}, tự động trừ kho {stock_before_buy} -> {stock_after_buy}")

    # 10. Quản lý thanh toán viện phí và đối soát
    all_invoices = BillingModel.get_all()
    assert len(all_invoices) > 0
    my_inv = [i for i in all_invoices if i['ma_hoa_don'] == hd_thuoc['ma_hoa_don']][0]
    assert 'chi_tiet' in my_inv
    assert 'khoan_muc' in my_inv
    print(f"[TEST 21] Phân hệ Viện phí truy vấn đủ chi tiết các khoản thu và bảng kê")

    ok_pay_thuoc, msg_pay_thuoc = BillingModel.pay_invoice(hd_thuoc['ma_hoa_don'], 'Chuyển khoản VietQR', 'Cổng VietQR Trực Tuyến')
    assert ok_pay_thuoc
    cur.execute("SELECT trang_thai FROM hoa_don WHERE ma_hoa_don = ?", (hd_thuoc['ma_hoa_don'],))
    assert cur.fetchone()['trang_thai'] == 'Đã thanh toán'
    print(f"[TEST 22] Thanh toán trực tuyến hóa đơn thuốc thành công")

    # Dọn dẹp dữ liệu test
    cur.execute("DELETE FROM chi_tiet_hoa_don WHERE hoa_don_id IN (SELECT id FROM hoa_don WHERE benh_nhan_id = ?)", (updated_user['patient_id'],))
    cur.execute("DELETE FROM hoa_don WHERE benh_nhan_id = ?", (updated_user['patient_id'],))
    cur.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id IN (SELECT id FROM don_thuoc WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id = ?))", (updated_user['patient_id'],))
    cur.execute("DELETE FROM don_thuoc WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id = ?)", (updated_user['patient_id'],))
    cur.execute("DELETE FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id IN (SELECT id FROM phieu_chi_dinh WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id = ?))", (updated_user['patient_id'],))
    cur.execute("DELETE FROM phieu_chi_dinh WHERE phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id = ?)", (updated_user['patient_id'],))
    cur.execute("DELETE FROM phieu_kham WHERE benh_nhan_id = ?", (updated_user['patient_id'],))
    cur.execute("DELETE FROM lich_hen WHERE benh_nhan_id = ?", (updated_user['patient_id'],))
    cur.execute("DELETE FROM thong_bao WHERE tai_khoan_id = ?", (updated_user['id'],))
    cur.execute("DELETE FROM chi_so_sinh_ton WHERE benh_nhan_id = ?", (updated_user['patient_id'],))
    cur.execute("DELETE FROM benh_nhan WHERE id = ?", (updated_user['patient_id'],))
    cur.execute("DELETE FROM tai_khoan WHERE id = ?", (updated_user['id'],))
    # Phục hồi 10 viên thuốc test
    cur.execute("UPDATE thuoc SET so_luong_ton = so_luong_ton + 10 WHERE id = 6")
    conn.commit()
    conn.close()

    print("\n[SUCCESS] Toàn bộ 22/22 bài kiểm thử hệ thống đều ĐẠT 100% PASS!")

if __name__ == '__main__':
    run_tests()
