"""Mobile Patient API Controller - Xử lý toàn bộ yêu cầu từ ứng dụng di động bệnh nhân kết nối CSDL SQL Server."""
from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from core.database import get_db
from core.mobile_auth import contract, bearer, verify, fail, public_user
from models.appointment_model import AppointmentModel
from models.patient_model import PatientModel
from models.clinic_model import ClinicModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.user_model import UserModel

mobile_patient_bp = Blueprint('mobile_patient', __name__, url_prefix='/api/v1/mobile/patient')


def get_current_mobile_patient():
    """Xác thực token Bearer của bệnh nhân và lấy thông tin bệnh nhân tương ứng."""
    token = bearer()
    conn = get_db()
    cursor = conn.cursor()
    try:
        user, claims, _ = verify(cursor, token)
        patient_id = user.get('patient_id') or claims.get('pid')
        if not patient_id:
            fail('PATIENT_NOT_FOUND', 'Không tìm thấy hồ sơ bệnh nhân tương ứng.', 404)
        return user, patient_id
    finally:
        conn.close()


@mobile_patient_bp.get('/dashboard')
@contract
def mobile_dashboard():
    """Lấy dữ liệu tổng quan trang chủ của bệnh nhân trên mobile."""
    user, patient_id = get_current_mobile_patient()
    patient = PatientModel.get_by_id(patient_id)
    if not patient:
        fail('PATIENT_NOT_FOUND', 'Hồ sơ bệnh nhân không tồn tại.', 404)

    # Lấy lịch khám sắp tới
    all_appts = AppointmentModel.get_by_patient(patient_id)
    upcoming = [a for a in all_appts if a.get('trang_thai') not in ['Đã khám', 'Đã hủy', 'Hoàn thành']]
    upcoming_appt = upcoming[0] if upcoming else None

    # Lấy thông báo chưa đọc
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM thong_bao WHERE tai_khoan_id = ? AND (da_doc = 0 OR da_doc IS NULL)", (user['id'],))
        row = cursor.fetchone()
        unread_count = row[0] if row else 0
    except Exception:
        unread_count = 0
    finally:
        conn.close()

    vitals = patient.get('vitals') or {}
    vitals_exist = any(vitals.get(k) for k in ['mach', 'nhiet_do', 'huyet_ap', 'spo2', 'can_nang', 'chieu_cao'])

    return jsonify({
        'success': True,
        'patient': {
            'id': patient.get('id'),
            'ma_bn': patient.get('ma_benh_nhan'),
            'ho_ten': patient.get('ho_ten'),
            'sdt': patient.get('sdt'),
            'email': patient.get('email') or '',
            'ngay_sinh': str(patient.get('ngay_sinh') or '')[:10],
            'gioi_tinh': patient.get('gioi_tinh') or 'Nam',
            'so_the_bhyt': patient.get('so_the_bhyt') or '',
            'bhyt': patient.get('so_the_bhyt') or '',
            'nhom_mau': patient.get('nhom_mau') or 'Chưa xác định',
            'dia_chi': patient.get('dia_chi') or '',
            'di_ung': patient.get('di_ung') or '',
            'benh_nen': patient.get('tien_su_benh') or '',
            'lien_he_khan_cap': patient.get('nguoi_than_sdt') or ''
        },
        'upcoming_appointment': upcoming_appt,
        'latest_vitals': vitals if vitals_exist else None,
        'unread_notifications': unread_count
    })


@mobile_patient_bp.get('/booking-meta')
@contract
def mobile_booking_meta():
    """Lấy danh mục chuyên khoa, bác sĩ và khung giờ đã đặt để hỗ trợ đặt lịch."""
    dept_id = request.args.get('chuyen_khoa_id', type=int)
    doctor_id = request.args.get('bac_si_id', type=int)
    date_str = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')

    departments = ClinicModel.get_all_departments(active_only=True)
    all_doctors = UserModel.get_all_doctors()

    if dept_id:
        doctors = [d for d in all_doctors if d.get('chuyen_khoa_id') == dept_id]
    else:
        doctors = all_doctors

    # Khung giờ đã được đặt trước
    conn = get_db()
    cursor = conn.cursor()
    booked_slots = []
    try:
        query = "SELECT gio_hen FROM lich_hen WHERE CAST(ngay_hen AS DATE) = ? AND trang_thai NOT IN (N'Đã hủy')"
        params = [date_str]
        if doctor_id:
            query += " AND bac_si_id = ?"
            params.append(doctor_id)
        elif dept_id:
            query += " AND chuyen_khoa_id = ?"
            params.append(dept_id)
        cursor.execute(query, tuple(params))
        for r in cursor.fetchall():
            if r['gio_hen']:
                booked_slots.append(str(r['gio_hen'])[:5])
    except Exception:
        pass
    finally:
        conn.close()

    specialties_fmt = [{
        'id': d['id'],
        'ten_chuyen_khoa': d.get('ten_khoa'),
        'mo_ta': d.get('mo_ta') or ''
    } for d in departments]

    doctors_fmt = [{
        'id': doc['id'],
        'ho_ten': doc.get('ten_bac_si') or doc.get('ho_ten'),
        'hoc_vi': doc.get('chuc_danh') or 'Bác sĩ',
        'chuyen_khoa_id': doc.get('chuyen_khoa_id'),
        'ten_chuyen_khoa': doc.get('ten_khoa'),
        'gia_kham': float(doc.get('gia_kham') or 150000),
        'phong_kham': doc.get('ten_phong') or 'Quầy tiếp đón phân bổ'
    } for doc in doctors]

    return jsonify({
        'success': True,
        'specialties': specialties_fmt,
        'doctors': doctors_fmt,
        'booked_slots': booked_slots
    })


@mobile_patient_bp.get('/appointments')
@contract
def mobile_get_appointments():
    """Lấy danh sách lịch hẹn của bệnh nhân từ CSDL SQL Server."""
    _, patient_id = get_current_mobile_patient()
    appointments = AppointmentModel.get_by_patient(patient_id)
    return jsonify({
        'success': True,
        'appointments': appointments
    })


@mobile_patient_bp.post('/appointments')
@contract
def mobile_create_appointment():
    """Tạo mới lịch hẹn từ App Mobile và lưu trực tiếp vào bảng lich_hen của SQL Server."""
    user, patient_id = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}

    chuyen_khoa_id = data.get('chuyen_khoa_id') or 1
    bac_si_id = data.get('bac_si_id')
    ngay_hen = data.get('ngay_hen') or data.get('date')
    gio_hen = data.get('gio_hen') or data.get('time')
    ly_do = data.get('ly_do') or 'Khám theo yêu cầu từ App Mobile'

    if not ngay_hen or not gio_hen:
        fail('VALIDATION_ERROR', 'Vui lòng chọn ngày và giờ khám bệnh!', 400)

    try:
        chuyen_khoa_id = int(chuyen_khoa_id)
    except (ValueError, TypeError):
        chuyen_khoa_id = 1

    if bac_si_id:
        try:
            bac_si_id = int(bac_si_id)
        except (ValueError, TypeError):
            bac_si_id = None

    success, result = AppointmentModel.create(
        benh_nhan_id=patient_id,
        chuyen_khoa_id=chuyen_khoa_id,
        bac_si_id=bac_si_id,
        ngay_hen=ngay_hen,
        gio_hen=gio_hen,
        ly_do_kham=ly_do,
        audit_user=user,
        return_details=True
    )

    if not success:
        fail('BOOKING_FAILED', str(result), 400)

    # Lấy lại chi tiết lịch hẹn vừa tạo để trả về đầy đủ cho App
    ma_lh = result.get('ma_lich_hen') if isinstance(result, dict) else result
    appts = AppointmentModel.get_by_patient(patient_id)
    created_item = next((a for a in appts if a.get('ma_lich_hen') == ma_lh), None)

    return jsonify({
        'success': True,
        'message': 'Đặt lịch khám thành công! Bộ phận tiếp đón sẽ duyệt và xác nhận lịch hẹn của bạn.',
        'appointment': created_item or {'ma_lich_hen': ma_lh, 'ngay_hen': ngay_hen, 'gio_hen': gio_hen}
    }), 201


@mobile_patient_bp.post('/appointments/<int:appointment_id>/reschedule')
@contract
def mobile_reschedule_appointment(appointment_id):
    """Đổi ngày/giờ lịch hẹn trên App."""
    user, patient_id = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}
    ngay_hen = data.get('ngay_hen')
    gio_hen = data.get('gio_hen')
    ly_do = data.get('ly_do')

    if not ngay_hen or not gio_hen:
        fail('VALIDATION_ERROR', 'Vui lòng cung cấp ngày và giờ mới!', 400)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, benh_nhan_id, trang_thai FROM lich_hen WHERE id = ?", (appointment_id,))
        row = cursor.fetchone()
        if not row or row['benh_nhan_id'] != patient_id:
            fail('FORBIDDEN', 'Bạn không có quyền chỉnh sửa lịch hẹn này!', 403)
        if row['trang_thai'] in ['Đã tiếp nhận', 'Đã xác nhận', 'Đã duyệt', 'Đang chờ khám']:
            fail('LOCKED_STATE', 'Lịch khám đã được phê duyệt xác nhận nên không thể thay đổi thông tin hay dời lịch!', 400)
        if row['trang_thai'] in ['Đã khám', 'Hoàn thành']:
            fail('INVALID_STATE', 'Lịch hẹn đã hoàn thành khám bệnh không thể đổi giờ.', 400)
        if row['trang_thai'] == 'Đã hủy':
            fail('INVALID_STATE', 'Lịch hẹn đã bị hủy không thể đổi giờ.', 400)

        cursor.execute("""
            UPDATE lich_hen
            SET ngay_hen = ?, gio_hen = ?, ly_do_kham = COALESCE(?, ly_do_kham), trang_thai = N'Chờ tiếp nhận'
            WHERE id = ?
        """, (ngay_hen, gio_hen, ly_do, appointment_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Đổi lịch khám thành công!'})


@mobile_patient_bp.post('/appointments/<int:appointment_id>/cancel')
@contract
def mobile_cancel_appointment(appointment_id):
    """Hủy lịch hẹn từ App Mobile."""
    user, patient_id = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}
    reason = data.get('reason') or 'Bệnh nhân tự hủy trên App Mobile'

    success, msg = AppointmentModel.update_status(appointment_id, 'Đã hủy', user_info=user)
    if not success:
        fail('CANCEL_FAILED', msg, 400)

    return jsonify({'success': True, 'message': 'Đã hủy lịch hẹn thành công!'})


@mobile_patient_bp.get('/records')
@contract
def mobile_medical_records():
    """Lấy danh sách hồ sơ bệnh án EMR, kết quả xét nghiệm và đơn thuốc của bệnh nhân."""
    _, patient_id = get_current_mobile_patient()
    records = PatientModel.get_patient_history(patient_id)
    patient = PatientModel.get_by_id(patient_id)
    vitals = patient.get('vitals') if patient else None

    has_real_vitals = False
    if vitals and isinstance(vitals, dict):
        has_real_vitals = any(v is not None and str(v).strip() != '' for v in vitals.values())

    effective_vitals = vitals if has_real_vitals else None

    return jsonify({
        'success': True,
        'records': records,
        'vitals': effective_vitals,
        'latest_vitals': effective_vitals
    })


@mobile_patient_bp.post('/prescriptions/<int:prescription_id>/purchase-option')
@contract
def mobile_prescription_purchase_option(prescription_id):
    """Cập nhật lựa chọn nhận thuốc: Mua tại bệnh viện hoặc Tự mua ngoài."""
    user, patient_id = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}
    option = data.get('option') or 'Mua tại bệnh viện'

    prescription = PharmacyModel.get_prescription_detail(prescription_id)
    if not prescription or prescription.get('benh_nhan_id') != patient_id:
        fail('FORBIDDEN', 'Không tìm thấy đơn thuốc hoặc bạn không có quyền!', 403)

    success, msg = PharmacyModel.choose_medicine_purchase_option(prescription_id, option, audit_user=user)
    if not success:
        fail('UPDATE_FAILED', msg, 400)

    return jsonify({'success': True, 'message': msg})


@mobile_patient_bp.get('/billing')
@contract
def mobile_billing():
    """Lấy danh sách hóa đơn viện phí và thông tin quyền lợi BHYT của bệnh nhân."""
    _, patient_id = get_current_mobile_patient()
    invoices = BillingModel.get_by_patient(patient_id)
    patient = PatientModel.get_by_id(patient_id)
    so_bhyt = patient.get('so_the_bhyt') or ''
    has_bhyt = bool(so_bhyt.strip())

    total_tien = sum(float(i.get('tong_tien') or 0) for i in invoices)
    total_bhyt = sum(float(i.get('tien_bhyt') or i.get('tien_bhyt_chi_tra') or 0) for i in invoices)
    da_thanh_toan = sum(float(i.get('thanh_tien') or i.get('thuc_thu') or 0) for i in invoices if i.get('trang_thai') == 'Đã thanh toán')
    chua_thanh_toan = sum(float(i.get('thanh_tien') or i.get('thuc_thu') or 0) for i in invoices if i.get('trang_thai') != 'Đã thanh toán')
    cho_count = len([i for i in invoices if i.get('trang_thai') != 'Đã thanh toán'])

    return jsonify({
        'success': True,
        'has_bhyt': has_bhyt,
        'so_the_bhyt': so_bhyt,
        'stats': {
            'has_bhyt': has_bhyt,
            'so_the_bhyt': so_bhyt,
            'tong_tien': total_tien,
            'tien_bhyt': total_bhyt,
            'da_thanh_toan': da_thanh_toan,
            'chua_thanh_toan': chua_thanh_toan,
            'so_hoa_don_cho': cho_count,
            'tong_so_hoa_don': len(invoices)
        },
        'invoices': invoices
    })


@mobile_patient_bp.get('/lab-results')
@contract
def mobile_lab_results():
    """Lấy danh sách phiếu cận lâm sàng & xét nghiệm của bệnh nhân."""
    _, patient_id = get_current_mobile_patient()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                ct.id,
                pcd.ma_chi_dinh AS ma_phieu,
                dv.ten_dich_vu,
                dv.loai_dich_vu,
                pcd.thoi_gian_chi_dinh AS ngay_chi_dinh,
                ct.thoi_gian_thuc_hien AS ngay_tra_ket_qua,
                ct.ktv_thuc_hien,
                ct.ket_qua,
                ct.ghi_chu_duyet AS ket_luan,
                ct.trang_thai,
                ct.file_dinh_kem AS file_ket_qua
            FROM chi_tiet_chi_dinh ct
            JOIN phieu_chi_dinh pcd ON ct.phieu_chi_dinh_id = pcd.id
            JOIN phieu_kham pk ON pcd.phieu_kham_id = pk.id
            JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            WHERE pk.benh_nhan_id = ?
            ORDER BY ct.id DESC
        """, (patient_id,))
        results = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    return jsonify({'success': True, 'results': results})


@mobile_patient_bp.get('/notifications')
@contract
def mobile_notifications():
    """Lấy danh sách thông báo của tài khoản bệnh nhân."""
    user, _ = get_current_mobile_patient()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, tieu_de, noi_dung, loai_thong_bao AS loai, da_doc,
                   CASE WHEN da_doc = 1 THEN 1 ELSE 0 END AS da_xem,
                   CONVERT(VARCHAR(19), thoi_gian_tao, 120) AS thoi_gian,
                   CONVERT(VARCHAR(19), thoi_gian_tao, 120) AS thoi_gian_tao,
                   lien_ket
            FROM thong_bao
            WHERE tai_khoan_id = ?
            ORDER BY id DESC
        """, (user['id'],))
        notifs = []
        for r in cursor.fetchall():
            d = dict(r)
            d['da_xem'] = bool(d.get('da_doc') == 1 or d.get('da_doc') is True)
            notifs.append(d)
    finally:
        conn.close()

    return jsonify({'success': True, 'notifications': notifs})


@mobile_patient_bp.post('/notifications/read')
@contract
def mobile_mark_notification_read():
    """Đánh dấu thông báo đã đọc."""
    user, _ = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}
    notif_id = data.get('notification_id') or data.get('id')

    conn = get_db()
    cursor = conn.cursor()
    try:
        if notif_id:
            cursor.execute("UPDATE thong_bao SET da_doc = 1 WHERE id = ? AND tai_khoan_id = ?", (notif_id, user['id']))
        else:
            cursor.execute("UPDATE thong_bao SET da_doc = 1 WHERE tai_khoan_id = ?", (user['id'],))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Đã cập nhật trạng thái thông báo.'})


@mobile_patient_bp.get('/feedbacks')
@contract
def mobile_get_feedbacks():
    """Lấy lịch sử phản hồi ý kiến của bệnh nhân."""
    _, patient_id = get_current_mobile_patient()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, chu_de, diem_danh_gia, noi_dung, ngay_gui, phan_hoi_admin
            FROM phan_hoi
            WHERE benh_nhan_id = ?
            ORDER BY ngay_gui DESC
        """, (patient_id,))
        feedbacks = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    return jsonify({'success': True, 'feedbacks': feedbacks})


@mobile_patient_bp.post('/feedbacks')
@contract
def mobile_submit_feedback():
    """Gửi góp ý, đánh giá dịch vụ từ App Mobile lên CSDL."""
    user, patient_id = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}
    chu_de = data.get('chu_de') or 'Đánh giá từ App Mobile'
    diem = data.get('diem_danh_gia') or 5
    noi_dung = data.get('noi_dung')

    if not noi_dung:
        fail('VALIDATION_ERROR', 'Vui lòng nhập nội dung đánh giá!', 400)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO phan_hoi (benh_nhan_id, chu_de, diem_danh_gia, noi_dung, ngay_gui)
            VALUES (?, ?, ?, ?, GETDATE())
        """, (patient_id, chu_de, diem, noi_dung))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Cảm ơn quý bệnh nhân đã gửi đánh giá!'})


@mobile_patient_bp.put('/profile')
@contract
def mobile_update_profile():
    """Cập nhật thông tin hồ sơ y tế cá nhân và thẻ BHYT vào CSDL SQL Server."""
    _, patient_id = get_current_mobile_patient()
    data = request.get_json(silent=True) or {}

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE benh_nhan
            SET 
                dia_chi = COALESCE(?, dia_chi),
                so_cccd = COALESCE(?, so_cccd),
                so_the_bhyt = COALESCE(?, so_the_bhyt),
                nhom_mau = COALESCE(?, nhom_mau),
                di_ung = COALESCE(?, di_ung),
                tien_su_benh = COALESCE(?, tien_su_benh),
                nguoi_than_sdt = COALESCE(?, nguoi_than_sdt)
            WHERE id = ?
        """, (
            data.get('dia_chi'),
            data.get('cccd') or data.get('so_cccd'),
            data.get('bhyt') or data.get('so_the_bhyt'),
            data.get('nhom_mau'),
            data.get('di_ung'),
            data.get('tien_su_benh') or data.get('benh_nen'),
            data.get('nguoi_than_sdt') or data.get('lien_he_khan_cap'),
            patient_id
        ))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Cập nhật hồ sơ bệnh nhân thành công!'})
