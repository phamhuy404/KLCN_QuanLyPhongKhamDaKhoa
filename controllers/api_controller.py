from datetime import datetime, date
from flask import Blueprint, request, jsonify, session
from core.security import login_required, roles_required
from models.user_model import UserModel
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/appointment/book', methods=['POST'])
@login_required
def book_appointment():
    """API đặt lịch hẹn khám bệnh có kiểm soát xác thực và phân quyền danh tính."""
    data = request.get_json() or {}
    user = session.get('user') or {}
    user_role = user.get('vai_tro')

    if user_role == 'BENHNHAN':
        # Bệnh nhân tự đặt lịch: Không tin tưởng patient_id client gửi lên, lấy từ tài khoản đã xác thực
        patient_id = user.get('patient_id')
        if not patient_id:
            patient_rec = PatientModel.get_by_account_id(user.get('id'))
            if patient_rec:
                patient_id = patient_rec['id']
                user['patient_id'] = patient_id
                session.modified = True
            else:
                return jsonify({
                    'success': False,
                    'message': 'Tài khoản của bạn chưa được liên kết với hồ sơ bệnh nhân nào!'
                }), 400
    elif user_role in ['ADMIN', 'LETAN', 'BACSI']:
        # Nhân viên/bác sĩ đặt lịch hẹn thay cho bệnh nhân
        patient_id = data.get('patient_id')
        if not patient_id:
            return jsonify({
                'success': False,
                'message': 'Vui lòng cung cấp mã ID của bệnh nhân cần đặt lịch!'
            }), 400
        patient_rec = PatientModel.get_by_id(patient_id)
        if not patient_rec:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy thông tin bệnh nhân trong hệ thống!'
            }), 404
    else:
        return jsonify({
            'success': False,
            'message': 'Tài khoản không có quyền đặt lịch khám bệnh!'
        }), 403

    chuyen_khoa_id = data.get('chuyen_khoa_id', 1)
    bac_si_id = data.get('bac_si_id')
    ngay_hen = data.get('ngay_hen')
    gio_hen = data.get('gio_hen')
    ly_do = data.get('ly_do', 'Khám theo yêu cầu')

    if not ngay_hen or not gio_hen:
        return jsonify({'success': False, 'message': 'Vui lòng chọn ngày và giờ khám!'}), 400

    success, result = AppointmentModel.create(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do, audit_user=user)
    if success:
        return jsonify({'success': True, 'ma_lich_hen': result, 'message': 'Đặt lịch thành công!'})
    return jsonify({'success': False, 'message': result}), 400

@api_bp.route('/appointment/assign-doctor', methods=['POST'])
@roles_required('ADMIN', 'BACSI')
def assign_doctor():
    """API phân công bác sĩ phụ trách lịch hẹn hoặc bác sĩ tự nhận ca khám."""
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    user = session.get('user', {})
    user_role = user.get('vai_tro')

    if user_role == 'BACSI':
        doctor_id = user.get('bac_si_id')
    else:
        doctor_id = data.get('bac_si_id')

    if not appointment_id or not doctor_id:
        return jsonify({'success': False, 'message': 'Thiếu ID lịch hẹn hoặc ID bác sĩ!'}), 400

    success, msg = AppointmentModel.assign_doctor(appointment_id, int(doctor_id), user_info=user)
    if success:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/doctors/schedule-availability', methods=['GET'])
@roles_required('ADMIN', 'BACSI', 'LETAN')
def doctor_schedule_availability():
    """API tra cứu bác sĩ theo chuyên khoa kèm lịch trực và số lượt còn trống trong ngày."""
    dept_id = request.args.get('department_id', type=int)
    if not dept_id:
        return jsonify({'success': False, 'message': 'Thiếu mã chuyên khoa!'}), 400

    raw_date = request.args.get('date')
    if raw_date:
        raw_date = raw_date.strip()
        try:
            valid_dt = datetime.strptime(raw_date, '%Y-%m-%d')
            date_str = valid_dt.strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Tham số ngày không đúng định dạng YYYY-MM-DD!'
            }), 400
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    docs = AppointmentModel.get_doctors_with_availability(dept_id, date_str)
    return jsonify({'success': True, 'doctors': docs})

@api_bp.route('/appointment/update-status', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN')
def update_appointment_status():
    """API cập nhật trạng thái lịch hẹn khám."""
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    new_status = data.get('status')
    user = session.get('user')

    if not appointment_id or not new_status:
        return jsonify({'success': False, 'message': 'Thiếu tham số!'}), 400

    success, msg = AppointmentModel.update_status(appointment_id, new_status, user_info=user)
    return jsonify({'success': success, 'message': msg})

@api_bp.route('/appointment/reschedule', methods=['POST'])
@api_bp.route('/appointment/update', methods=['POST'])
@login_required
def reschedule_appointment():
    """API đổi lịch hẹn khám (Kiểm soát chặt chẽ quyền hạn bệnh nhân và nhân viên y tế)."""
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    new_date = data.get('ngay_hen')
    new_time = data.get('gio_hen')
    ly_do = data.get('ly_do')
    new_doc_id = data.get('bac_si_id')
    user = session.get('user') or {}
    user_role = user.get('vai_tro')

    if user_role not in ['ADMIN', 'LETAN', 'BACSI', 'BENHNHAN']:
        return jsonify({'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này!'}), 403

    if not appointment_id or not new_date or not new_time:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID lịch hẹn, ngày hẹn mới và giờ hẹn mới!'}), 400

    ok, msg = AppointmentModel.reschedule(appointment_id, new_date, new_time, ly_do=ly_do, new_doctor_id=new_doc_id, user_info=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/appointment/cancel', methods=['POST'])
@login_required
def cancel_appointment():
    """API hủy lịch hẹn khám (Kiểm soát chặt chẽ quyền hạn bệnh nhân và nhân viên y tế)."""
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    reason = data.get('reason') or data.get('ly_do')
    user = session.get('user') or {}
    user_role = user.get('vai_tro')

    if user_role not in ['ADMIN', 'LETAN', 'BACSI', 'BENHNHAN']:
        return jsonify({'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này!'}), 403

    if not appointment_id:
        return jsonify({'success': False, 'message': 'Thiếu ID lịch hẹn cần hủy!'}), 400

    ok, msg = AppointmentModel.cancel(appointment_id, reason=reason, user_info=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
@login_required
def get_appointment_detail(appointment_id):
    """API xem chi tiết một lịch hẹn khám."""
    user = session.get('user', {})
    appt = AppointmentModel.get_by_id(appointment_id)
    if not appt:
        return jsonify({'success': False, 'message': 'Không tìm thấy lịch hẹn!'}), 404

    # Bệnh nhân chỉ xem được lịch của chính mình
    if user.get('vai_tro') == 'BENHNHAN' and appt['benh_nhan_id'] != user.get('patient_id'):
        return jsonify({'success': False, 'message': 'Bạn không có quyền xem lịch hẹn này!'}), 403

    return jsonify({'success': True, 'appointment': appt})

@api_bp.route('/admin/reset-password', methods=['POST'])
@roles_required('ADMIN')
def reset_password():
    """API quản trị viên đặt lại mật khẩu cho bệnh nhân hoặc tài khoản."""
    data = request.get_json() or {}
    account_id = data.get('account_id')
    patient_id = data.get('patient_id')
    new_password = data.get('new_password')
    user = session.get('user')

    if not new_password:
        return jsonify({'success': False, 'message': 'Vui lòng nhập mật khẩu mới!'}), 400

    if account_id:
        success, msg = UserModel.reset_account_password(account_id, new_password, audit_user=user)
        return jsonify({'success': success, 'message': msg})
    elif patient_id:
        success, msg = UserModel.reset_patient_password(patient_id, new_password, audit_user=user)
        return jsonify({'success': success, 'message': msg})

    return jsonify({'success': False, 'message': 'Thiếu ID tài khoản hoặc ID bệnh nhân!'}), 400


@api_bp.route('/catalogs/<name>', methods=['GET'])
def get_catalog(name):
    """API lấy danh mục chuẩn theo tên (nhom_mau, di_ung, tien_su_benh)."""
    from core.catalog import get_all_catalogs
    all_catalogs = get_all_catalogs()
    items = all_catalogs.get(name, [])
    return jsonify({'success': True, 'catalog': name, 'items': items})

@api_bp.route('/patient/update-profile', methods=['POST'])
@login_required
def update_patient_profile():
    """API bệnh nhân cập nhật thông tin cá nhân và hồ sơ sức khỏe."""
    data = request.get_json() or {}
    user = session.get('user', {})
    if user.get('vai_tro') != 'BENHNHAN':
        return jsonify({'success': False, 'message': 'Chức năng cập nhật hồ sơ cá nhân chỉ dành cho bệnh nhân!'}), 403

    patient_id = user.get('patient_id')
    if not patient_id:
        patient_rec = PatientModel.get_by_account_id(user.get('id'))
        if patient_rec:
            patient_id = patient_rec['id']
            session['user']['patient_id'] = patient_id
            session.modified = True
        else:
            return jsonify({'success': False, 'message': 'Tài khoản chưa được liên kết với hồ sơ bệnh nhân hợp lệ!'}), 400

    success, msg = PatientModel.update_profile(patient_id, data)
    if success:
        if 'user' in session:
            session['user']['ho_ten'] = data.get('ho_ten', session['user'].get('ho_ten'))
            session['user']['sdt'] = data.get('sdt', session['user'].get('sdt'))
            session['user']['email'] = data.get('email', session['user'].get('email'))
            session.modified = True
        return jsonify({'success': True, 'message': 'Cập nhật thông tin thành công!'})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/patient/update', methods=['POST'])
@roles_required('ADMIN', 'LETAN', 'BACSI')
def update_patient_admin():
    """API nhân viên cập nhật thông tin hồ sơ bệnh nhân."""
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    if not patient_id:
        return jsonify({'success': False, 'message': 'Thiếu ID bệnh nhân!'}), 400

    success, msg = PatientModel.update_profile(patient_id, data)
    if success:
        return jsonify({'success': True, 'message': 'Cập nhật thành công!'})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/patient/create', methods=['POST'])
@roles_required('ADMIN', 'LETAN', 'BACSI')
def create_patient():
    """API tiếp nhận và tạo hồ sơ bệnh nhân mới."""
    data = request.get_json() or {}
    if not data.get('ho_ten') or not data.get('sdt'):
        return jsonify({'success': False, 'message': 'Họ tên và số điện thoại là bắt buộc!'}), 400

    success, patient_id, ma_bn = PatientModel.create_patient(data)
    if success:
        return jsonify({'success': True, 'patient_id': patient_id, 'ma_benh_nhan': ma_bn, 'message': 'Tiếp nhận thành công!'})
    return jsonify({'success': False, 'message': ma_bn}), 400

@api_bp.route('/emr/save', methods=['POST'])
@roles_required('ADMIN', 'BACSI')
def save_emr_examination():
    """API bác sĩ lưu hồ sơ khám bệnh, ra chỉ định và kê đơn thuốc vào CSDL."""
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    if not patient_id:
        return jsonify({'success': False, 'message': 'Thiếu ID bệnh nhân!'}), 400

    doctor_id = data.get('doctor_id') or session.get('user', {}).get('bac_si_id') or 1
    room_id = data.get('room_id', 1)
    reason = data.get('reason', 'Khám theo yêu cầu')
    symptoms = data.get('symptoms', 'Triệu chứng bình thường')
    diagnosis = data.get('diagnosis', 'Khám tổng quát')
    icd = data.get('icd', 'Z00.0 - Khám sức khỏe tổng quát')
    treatment = data.get('treatment', 'Theo dõi và điều trị nội khoa')
    advice = data.get('advice', 'Ăn uống nghỉ ngơi điều độ')
    reexam_date = data.get('reexam_date')
    lab_service_ids = data.get('lab_services', [])
    medicines = data.get('medicines', [])

    success, result = MedicalRecordModel.save_examination(
        patient_id=patient_id,
        doctor_id=doctor_id,
        room_id=room_id,
        reason=reason,
        symptoms=symptoms,
        diagnosis=diagnosis,
        icd=icd,
        treatment=treatment,
        advice=advice,
        reexam_date=reexam_date,
        lab_service_ids=lab_service_ids,
        medicines=medicines
    )
    if success:
        return jsonify({'success': True, 'ma_phieu': result, 'message': 'Lưu phiếu khám và chuyển toa thành công!'})
    return jsonify({'success': False, 'message': result}), 400

@api_bp.route('/pharmacy/dispense', methods=['POST'])
@roles_required('ADMIN', 'DUOCSI')
def dispense_prescription():
    """API dược sĩ xuất thuốc và trừ số lượng kho (chống xuất trùng, kiểm tra tồn kho an toàn)."""
    data = request.get_json() or {}
    ma_don = data.get('ma_don') or data.get('prescription_id')
    user = session.get('user')
    if not ma_don:
        return jsonify({'success': False, 'message': 'Thiếu mã đơn thuốc!'}), 400

    success, msg = PharmacyModel.dispense_prescription(ma_don, audit_user=user)
    if success:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/pharmacy/add-medicine', methods=['POST'])
@roles_required('ADMIN', 'DUOCSI')
def add_medicine():
    """API thêm dược phẩm mới vào kho thuốc."""
    data = request.get_json() or {}
    ten = data.get('ten_thuoc')
    hoat_chat = data.get('hoat_chat', '')
    dvt = data.get('don_vi_tinh', 'Viên')
    so_luong = int(data.get('so_luong_ton', 0))
    don_gia = float(data.get('don_gia', 0.0))
    ham_luong = data.get('ham_luong', '')
    hang_sx = data.get('hang_san_xuat', 'Việt Nam')

    if not ten:
        return jsonify({'success': False, 'message': 'Tên thuốc là bắt buộc!'}), 400

    success, result = PharmacyModel.add_medicine(ten, hoat_chat, dvt, so_luong, don_gia, ham_luong, hang_sx)
    if success:
        return jsonify({'success': True, 'ma_thuoc': result, 'message': 'Thêm thuốc thành công!'})
    return jsonify({'success': False, 'message': result}), 400

@api_bp.route('/billing/pay', methods=['POST'])
@roles_required('ADMIN', 'LETAN')
def pay_invoice():
    """API thu ngân xác nhận thanh toán viện phí."""
    data = request.get_json() or {}
    ma_hd = data.get('ma_hd') or data.get('invoice_id')
    pttt = data.get('hinh_thuc_thanh_toan', 'Tiền mặt')
    cashier = session.get('user', {}).get('ho_ten', 'Thu ngân')

    if not ma_hd:
        return jsonify({'success': False, 'message': 'Thiếu mã hóa đơn!'}), 400

    success, msg = BillingModel.pay_invoice(ma_hd, pttt, cashier)
    return jsonify({'success': success, 'message': msg})

# ==========================================
# 1. API SAO LƯU VÀ PHỤC HỒI DỮ LIỆU
# ==========================================
@api_bp.route('/backup/create', methods=['POST'])
@roles_required('ADMIN')
def create_backup():
    """API quản trị viên kích hoạt tạo bản sao lưu dữ liệu."""
    from models.backup_model import BackupModel
    user_name = session.get('user', {}).get('ho_ten', 'admin')
    ok, msg = BackupModel.create_backup(user_name=user_name)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/backup/restore', methods=['POST'])
@roles_required('ADMIN')
def restore_backup():
    """API quản trị viên kích hoạt phục hồi dữ liệu từ bản sao lưu hợp lệ."""
    from models.backup_model import BackupModel
    data = request.get_json() or {}
    filename = data.get('filename')
    confirm = data.get('confirm', False)

    if not filename:
        return jsonify({'success': False, 'message': 'Vui lòng chọn tệp sao lưu cần phục hồi!'}), 400

    if not confirm:
        return jsonify({'success': False, 'message': 'Yêu cầu xác nhận rõ ràng trước khi ghi đè dữ liệu!'}), 400

    user_name = session.get('user', {}).get('ho_ten', 'admin')
    ok, msg = BackupModel.restore_backup(filename, user_name=user_name, confirm=confirm)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/backup/download/<path:filename>', methods=['GET'])
@roles_required('ADMIN')
def download_backup(filename):
    """API tải tệp sao lưu dữ liệu (Ngăn chặn triệt để path traversal)."""
    import os
    from flask import send_from_directory, abort
    from werkzeug.utils import secure_filename
    from models.backup_model import BackupModel

    safe_filename = secure_filename(filename)
    backup_dir = BackupModel.get_backup_dir()
    file_path = os.path.join(backup_dir, safe_filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({'success': False, 'message': 'Tệp sao lưu không tồn tại!'}), 404

    return send_from_directory(backup_dir, safe_filename, as_attachment=True)

# ==========================================
# 2. API TIẾP NHẬN VÀ PHẢN HỒI BỆNH NHÂN
# ==========================================
@api_bp.route('/feedback/submit', methods=['POST'])
@login_required
def submit_feedback():
    """API bệnh nhân gửi phản hồi chất lượng dịch vụ."""
    from models.feedback_model import FeedbackModel
    data = request.get_json() or {}
    user = session.get('user', {})
    patient_id = user.get('patient_id')
    if not patient_id:
        return jsonify({'success': False, 'message': 'Chỉ tài khoản bệnh nhân mới có thể gửi phản hồi dịch vụ!'}), 403

    chu_de = data.get('chu_de', 'Dịch vụ khám bệnh')
    diem = data.get('diem_danh_gia', 5)
    noi_dung = data.get('noi_dung', '')
    phieu_kham_id = data.get('phieu_kham_id')

    ok, msg = FeedbackModel.create(patient_id, phieu_kham_id, chu_de, diem, noi_dung)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/feedback/reply', methods=['POST'])
@roles_required('ADMIN', 'LETAN', 'BACSI')
def reply_feedback():
    """API nhân viên y tế / CSKH trả lời và cập nhật trạng thái phản hồi."""
    from models.feedback_model import FeedbackModel
    data = request.get_json() or {}
    feedback_id = data.get('feedback_id')
    tra_loi = data.get('tra_loi', '')
    trang_thai = data.get('trang_thai', 'Đã giải quyết')
    staff_name = session.get('user', {}).get('ho_ten', 'Bộ phận CSKH')

    if not feedback_id or not tra_loi:
        return jsonify({'success': False, 'message': 'Thiếu ID phản hồi hoặc nội dung trả lời!'}), 400

    ok, msg = FeedbackModel.reply(feedback_id, tra_loi, trang_thai, nguoi_tra_loi=staff_name)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

# ==========================================
# 3. API THÔNG BÁO VÀ NHẮC LỊCH KHÁM
# ==========================================
@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """API lấy danh sách thông báo in-app của tài khoản đang đăng nhập."""
    from models.notification_model import NotificationModel
    user = session.get('user', {})
    tai_khoan_id = user.get('id')
    notifs = NotificationModel.get_user_notifications(tai_khoan_id, limit=20)
    unread_cnt = NotificationModel.get_unread_count(tai_khoan_id)
    return jsonify({'success': True, 'notifications': notifs, 'unread_count': unread_cnt})

@api_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    """API đánh dấu thông báo đã đọc."""
    from models.notification_model import NotificationModel
    data = request.get_json() or {}
    user = session.get('user', {})
    tai_khoan_id = user.get('id')

    if data.get('all'):
        ok, msg = NotificationModel.mark_all_as_read(tai_khoan_id)
        return jsonify({'success': ok, 'message': msg})

    notification_id = data.get('notification_id')
    if not notification_id:
        return jsonify({'success': False, 'message': 'Thiếu ID thông báo!'}), 400

    ok, msg = NotificationModel.mark_as_read(notification_id, tai_khoan_id)
    return jsonify({'success': ok, 'message': msg})

@api_bp.route('/notifications/run-reminders', methods=['POST'])
@roles_required('ADMIN', 'LETAN')
def trigger_reminders():
    """API quản trị viên kích hoạt quét và gửi nhắc lịch hẹn/tái khám."""
    from core.notification_service import NotificationService
    stats = NotificationService.run_all_reminders()
    return jsonify({'success': True, 'stats': stats, 'message': f"Đã quét {stats['appointments_scanned']} lịch hẹn và {stats['reexams_scanned']} lịch tái khám. Đã gửi {stats['appointments_reminded'] + stats['reexams_reminded']} nhắc nhở."})

@api_bp.route('/notifications/smtp-status', methods=['GET'])
@roles_required('ADMIN')
def get_smtp_status():
    """API kiểm tra cấu hình SMTP."""
    from core.notification_service import NotificationService
    return jsonify(NotificationService.get_smtp_status())

# ==========================================
# 4. API QUẢN LÝ DANH MỤC Y TẾ (CHUYÊN KHOA, PHÒNG KHÁM, DỊCH VỤ)
# ==========================================
@api_bp.route('/catalog/department/create', methods=['POST'])
@roles_required('ADMIN')
def create_department():
    """API thêm chuyên khoa mới."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    ma = data.get('ma_khoa')
    ten = data.get('ten_khoa')
    mo_ta = data.get('mo_ta', '')
    icon = data.get('icon', 'fa-stethoscope')
    gia = data.get('gia_kham_mac_dinh', 150000.0)

    ok, res = ClinicModel.create_department(ma, ten, mo_ta, icon, gia)
    if ok:
        return jsonify({'success': True, 'department_id': res, 'message': 'Thêm chuyên khoa thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/catalog/department/update', methods=['POST'])
@roles_required('ADMIN')
def update_department():
    """API sửa thông tin chuyên khoa."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    dep_id = data.get('id')
    ma = data.get('ma_khoa')
    ten = data.get('ten_khoa')
    mo_ta = data.get('mo_ta', '')
    icon = data.get('icon', 'fa-stethoscope')
    gia = data.get('gia_kham_mac_dinh', 150000.0)
    tt = data.get('trang_thai', 1)

    if not dep_id:
        return jsonify({'success': False, 'message': 'Thiếu ID chuyên khoa!'}), 400

    ok, msg = ClinicModel.update_department(dep_id, ma, ten, mo_ta, icon, gia, tt)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/catalog/department/toggle', methods=['POST'])
@roles_required('ADMIN')
def toggle_department():
    """API bật/tắt trạng thái chuyên khoa."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    dep_id = data.get('id')
    if not dep_id:
        return jsonify({'success': False, 'message': 'Thiếu ID chuyên khoa!'}), 400

    ok, res = ClinicModel.toggle_department_status(dep_id)
    if ok:
        return jsonify({'success': True, 'new_status': res, 'message': 'Cập nhật trạng thái thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/catalog/department/delete', methods=['POST'])
@roles_required('ADMIN')
def delete_department():
    """API xóa chuyên khoa (có kiểm tra ràng buộc)."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    dep_id = data.get('id')
    if not dep_id:
        return jsonify({'success': False, 'message': 'Thiếu ID chuyên khoa!'}), 400

    ok, msg = ClinicModel.delete_department(dep_id)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/catalog/room/create', methods=['POST'])
@roles_required('ADMIN')
def create_room():
    """API tạo phòng khám mới."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    ck_id = data.get('chuyen_khoa_id')
    ma = data.get('ma_phong')
    ten = data.get('ten_phong')
    tang = data.get('vi_tri_tang', 'Tầng 1')

    ok, res = ClinicModel.create_room(ck_id, ma, ten, tang)
    if ok:
        return jsonify({'success': True, 'room_id': res, 'message': 'Tạo phòng khám thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/catalog/room/update', methods=['POST'])
@roles_required('ADMIN')
def update_room():
    """API sửa thông tin phòng khám."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    r_id = data.get('id')
    ck_id = data.get('chuyen_khoa_id')
    ma = data.get('ma_phong')
    ten = data.get('ten_phong')
    tang = data.get('vi_tri_tang', 'Tầng 1')
    tt = data.get('trang_thai', 1)

    if not r_id:
        return jsonify({'success': False, 'message': 'Thiếu ID phòng khám!'}), 400

    ok, msg = ClinicModel.update_room(r_id, ck_id, ma, ten, tang, tt)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/catalog/room/toggle', methods=['POST'])
@roles_required('ADMIN')
def toggle_room():
    """API bật/tắt trạng thái phòng khám."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    r_id = data.get('id')
    if not r_id:
        return jsonify({'success': False, 'message': 'Thiếu ID phòng khám!'}), 400

    ok, res = ClinicModel.toggle_room_status(r_id)
    if ok:
        return jsonify({'success': True, 'new_status': res, 'message': 'Cập nhật trạng thái thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/catalog/room/delete', methods=['POST'])
@roles_required('ADMIN')
def delete_room():
    """API xóa phòng khám (có kiểm tra ràng buộc)."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    r_id = data.get('id')
    if not r_id:
        return jsonify({'success': False, 'message': 'Thiếu ID phòng khám!'}), 400

    ok, msg = ClinicModel.delete_room(r_id)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/catalog/service/create', methods=['POST'])
@roles_required('ADMIN')
def create_service():
    """API thêm dịch vụ kỹ thuật y tế."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    ck_id = data.get('chuyen_khoa_id')
    ma = data.get('ma_dich_vu')
    ten = data.get('ten_dich_vu')
    loai = data.get('loai_dich_vu', 'Khám bệnh')
    don_gia = data.get('don_gia', 0.0)
    bhyt = data.get('bhyt_chi_tra_pt', 0)
    mo_ta = data.get('mo_ta', '')

    ok, res = ClinicModel.create_service(ck_id, ma, ten, loai, don_gia, bhyt, mo_ta)
    if ok:
        return jsonify({'success': True, 'service_id': res, 'message': 'Thêm dịch vụ thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/catalog/service/update', methods=['POST'])
@roles_required('ADMIN')
def update_service():
    """API sửa thông tin dịch vụ kỹ thuật."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    srv_id = data.get('id')
    ck_id = data.get('chuyen_khoa_id')
    ma = data.get('ma_dich_vu')
    ten = data.get('ten_dich_vu')
    loai = data.get('loai_dich_vu', 'Khám bệnh')
    don_gia = data.get('don_gia', 0.0)
    bhyt = data.get('bhyt_chi_tra_pt', 0)
    mo_ta = data.get('mo_ta', '')
    tt = data.get('trang_thai', 1)

    if not srv_id:
        return jsonify({'success': False, 'message': 'Thiếu ID dịch vụ!'}), 400

    ok, msg = ClinicModel.update_service(srv_id, ck_id, ma, ten, loai, don_gia, bhyt, mo_ta, tt)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/catalog/service/toggle', methods=['POST'])
@roles_required('ADMIN')
def toggle_service():
    """API bật/tắt trạng thái dịch vụ."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    srv_id = data.get('id')
    if not srv_id:
        return jsonify({'success': False, 'message': 'Thiếu ID dịch vụ!'}), 400

    ok, res = ClinicModel.toggle_service_status(srv_id)
    if ok:
        return jsonify({'success': True, 'new_status': res, 'message': 'Cập nhật trạng thái thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/catalog/service/delete', methods=['POST'])
@roles_required('ADMIN')
def delete_service():
    """API xóa dịch vụ kỹ thuật (có kiểm tra ràng buộc)."""
    from models.clinic_model import ClinicModel
    data = request.get_json() or {}
    srv_id = data.get('id')
    if not srv_id:
        return jsonify({'success': False, 'message': 'Thiếu ID dịch vụ!'}), 400

    ok, msg = ClinicModel.delete_service(srv_id)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

# ==========================================
# 5. API QUẢN LÝ NHÂN SỰ VÀ LỊCH LÀM VIỆC
# ==========================================
@api_bp.route('/staff/create', methods=['POST'])
@roles_required('ADMIN')
def create_staff():
    """API thêm nhân viên y tế mới."""
    data = request.get_json() or {}
    ok, res = UserModel.create_staff(data)
    if ok:
        return jsonify({'success': True, 'staff_id': res, 'message': 'Thêm nhân sự thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/staff/update', methods=['POST'])
@roles_required('ADMIN')
def update_staff():
    """API cập nhật thông tin nhân sự."""
    data = request.get_json() or {}
    staff_id = data.get('id')
    if not staff_id:
        return jsonify({'success': False, 'message': 'Thiếu ID nhân viên!'}), 400

    ok, msg = UserModel.update_staff(staff_id, data)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/staff/toggle', methods=['POST'])
@roles_required('ADMIN')
def toggle_staff():
    """API bật/tắt trạng thái làm việc của nhân sự."""
    data = request.get_json() or {}
    staff_id = data.get('id')
    if not staff_id:
        return jsonify({'success': False, 'message': 'Thiếu ID nhân viên!'}), 400

    ok, res = UserModel.toggle_staff_status(staff_id)
    if ok:
        return jsonify({'success': True, 'new_status': res, 'message': 'Cập nhật trạng thái thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/staff/delete', methods=['POST'])
@roles_required('ADMIN')
def delete_staff():
    """API xóa nhân viên y tế."""
    data = request.get_json() or {}
    staff_id = data.get('id')
    if not staff_id:
        return jsonify({'success': False, 'message': 'Thiếu ID nhân viên!'}), 400

    ok, msg = UserModel.delete_staff(staff_id)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/create', methods=['POST'])
@roles_required('ADMIN')
def create_schedule():
    """API tạo ca trực / lịch làm việc mới (có kiểm tra xung đột)."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    bs_id = data.get('bac_si_id')
    nhan_vien_id = data.get('nhan_vien_id')
    pk_id = data.get('phong_kham_id')
    ngay = data.get('ngay_lam')
    ca = data.get('ca_lam', 1)
    bd = data.get('gio_bat_dau')
    kt = data.get('gio_ket_thuc')
    sl = data.get('so_luong_kham_toi_da', 20)

    ok, res = ScheduleModel.create_schedule(bs_id, pk_id, ngay, ca, bd, kt, sl, nhan_vien_id=nhan_vien_id)
    if ok:
        return jsonify({'success': True, 'schedule_id': res, 'message': 'Thêm lịch làm việc thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/schedule/register', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def register_schedule():
    """API nhân viên tự đăng ký ca làm trong 2 tuần tiếp theo."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    user = session.get('user')
    ngay = data.get('ngay_lam')
    ca = data.get('ca_lam', 1)
    pk_id = data.get('phong_kham_id')
    ghi_chu = data.get('ghi_chu')
    ok, msg = ScheduleModel.register_schedule(user, ngay, ca, pk_id, ghi_chu)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/register-multiple', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def register_multiple_schedules():
    """API nhân viên đăng ký nhiều ca làm việc cùng lúc trong 2 tuần tiếp theo."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    user = session.get('user')
    shifts = data.get('shifts', [])
    pk_id = data.get('phong_kham_id')
    ghi_chu = data.get('ghi_chu')
    ok, msg, success_count, errors = ScheduleModel.register_multiple_schedules(user, shifts, pk_id, ghi_chu)
    if ok:
        return jsonify({'success': True, 'message': msg, 'count': success_count, 'errors': errors})
    return jsonify({'success': False, 'message': msg, 'count': success_count, 'errors': errors}), 400

@api_bp.route('/schedule/cancel-request', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def cancel_request_schedule():
    """API gửi đơn xin hủy ca trực trong tuần hiện tại."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    user = session.get('user')
    sc_id = data.get('id') or data.get('schedule_id')
    reason = data.get('ly_do') or data.get('reason')
    if not sc_id or not reason:
        return jsonify({'success': False, 'message': 'Thiếu ID ca trực hoặc lý do xin hủy!'}), 400
    ok, msg = ScheduleModel.request_cancellation(sc_id, user, reason)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/approve-cancellation', methods=['POST'])
@roles_required('ADMIN', 'LETAN')
def approve_cancellation_schedule():
    """API duyệt hoặc từ chối đơn xin hủy ca trực."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    user = session.get('user')
    sc_id = data.get('id') or data.get('schedule_id')
    approved = bool(data.get('approved', True))
    if not sc_id:
        return jsonify({'success': False, 'message': 'Thiếu ID ca trực!'}), 400
    ok, msg = ScheduleModel.approve_cancellation(sc_id, user, approved)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/approve-registration', methods=['POST'])
@roles_required('ADMIN', 'LETAN')
def approve_registration_schedule():
    """API duyệt hoặc từ chối yêu cầu đăng ký ca làm (tối đa 5 người/ca/role)."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    user = session.get('user')
    sc_id = data.get('id') or data.get('schedule_id')
    approved = bool(data.get('approved', True))
    if not sc_id:
        return jsonify({'success': False, 'message': 'Thiếu ID ca trực!'}), 400
    ok, msg = ScheduleModel.approve_schedule(sc_id, user, approved)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/update', methods=['POST'])
@roles_required('ADMIN')
def update_schedule():
    """API sửa thông tin ca làm việc."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    sc_id = data.get('id')
    bs_id = data.get('bac_si_id')
    pk_id = data.get('phong_kham_id')
    ngay = data.get('ngay_lam')
    ca = data.get('ca_lam', 1)
    bd = data.get('gio_bat_dau')
    kt = data.get('gio_ket_thuc')
    sl = data.get('so_luong_kham_toi_da', 20)
    tt = data.get('trang_thai', 1)

    if not sc_id:
        return jsonify({'success': False, 'message': 'Thiếu ID lịch làm việc!'}), 400

    ok, msg = ScheduleModel.update_schedule(sc_id, bs_id, pk_id, ngay, ca, bd, kt, sl, tt)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/toggle', methods=['POST'])
@roles_required('ADMIN')
def toggle_schedule():
    """API bật/tắt trạng thái ca làm việc."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    sc_id = data.get('id')
    if not sc_id:
        return jsonify({'success': False, 'message': 'Thiếu ID lịch làm việc!'}), 400

    ok, res = ScheduleModel.toggle_status(sc_id)
    if ok:
        return jsonify({'success': True, 'new_status': res, 'message': 'Cập nhật trạng thái thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/schedule/delete', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def delete_schedule():
    """API xóa ca làm việc."""
    from models.schedule_model import ScheduleModel
    data = request.get_json() or {}
    sc_id = data.get('id')
    if not sc_id:
        return jsonify({'success': False, 'message': 'Thiếu ID lịch làm việc!'}), 400

    user = session.get('user')
    ok, msg = ScheduleModel.delete_schedule(sc_id, current_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/schedule/available-doctors', methods=['GET'])
def get_available_doctors():
    """API lấy danh sách bác sĩ có ca trực phù hợp theo chuyên khoa và ngày khám."""
    from models.schedule_model import ScheduleModel
    ck_id = request.args.get('chuyen_khoa_id', type=int)
    ngay = request.args.get('ngay_hen')
    if not ck_id or not ngay:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp chuyên khoa và ngày khám!'}), 400

    docs = ScheduleModel.get_available_doctors(ck_id, ngay)
    return jsonify({'success': True, 'doctors': docs})


# =========================================================================
# 6. QUẢN LÝ TÀI KHOẢN VÀ PHÂN QUYỀN
# =========================================================================

@api_bp.route('/admin/accounts/list', methods=['GET'])
@roles_required('ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV')
def list_accounts():
    """API xem danh sách tài khoản bệnh nhân và nhân viên, tìm kiếm và phân trang."""
    role = request.args.get('role', 'ALL')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    data = UserModel.get_accounts(role=role, search=search, page=page, per_page=per_page)
    return jsonify({'success': True, **data})

@api_bp.route('/admin/account/<int:account_id>', methods=['GET'])
@roles_required('ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV')
def get_account_detail_api(account_id):
    """API xem chi tiết một tài khoản và hồ sơ liên kết."""
    acc = UserModel.get_account_detail(account_id)
    if not acc:
        return jsonify({'success': False, 'message': 'Không tìm thấy tài khoản!'}), 404
    return jsonify({'success': True, 'account': acc})

@api_bp.route('/admin/account/toggle', methods=['POST'])
@roles_required('ADMIN')
def toggle_account():
    """API bật/tắt trạng thái kích hoạt tài khoản."""
    data = request.get_json() or {}
    account_id = data.get('account_id') or data.get('id')
    if not account_id:
        return jsonify({'success': False, 'message': 'Thiếu ID tài khoản!'}), 400

    user = session.get('user')
    ok, res = UserModel.toggle_account_status(account_id, audit_user=user)
    if ok:
        status_text = 'kích hoạt' if res == 1 else 'vô hiệu hóa'
        return jsonify({'success': True, 'new_status': res, 'message': f'Đã {status_text} tài khoản thành công!'})
    return jsonify({'success': False, 'message': res}), 400

@api_bp.route('/admin/account/reset-password', methods=['POST'])
@roles_required('ADMIN')
def reset_account_password_api():
    """API quản trị viên đặt lại mật khẩu cho tài khoản."""
    data = request.get_json() or {}
    account_id = data.get('account_id') or data.get('id')
    new_password = data.get('new_password')
    user = session.get('user')

    if not account_id or not new_password:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID tài khoản và mật khẩu mới!'}), 400

    ok, msg = UserModel.reset_account_password(account_id, new_password, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/admin/account/set-role', methods=['POST'])
@roles_required('ADMIN')
def set_account_role_api():
    """API quản trị viên gán vai trò theo danh sách vai trò hiện có trong CSDL."""
    data = request.get_json() or {}
    account_id = data.get('account_id') or data.get('id')
    role_id = data.get('role_id')
    user = session.get('user')

    if not account_id or not role_id:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID tài khoản và ID vai trò!'}), 400

    ok, msg = UserModel.set_account_role(account_id, role_id, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/admin/roles', methods=['GET'])
@roles_required('ADMIN')
def get_roles_list():
    """API lấy danh sách các vai trò hệ thống hiện có."""
    roles = UserModel.get_all_roles()
    return jsonify({'success': True, 'roles': roles})

@api_bp.route('/admin/audit-logs', methods=['GET'])
@roles_required('ADMIN')
def get_audit_logs():
    """API lấy nhật ký kiểm toán hệ thống."""
    from core.audit import AuditLogger
    table_name = request.args.get('table_name')
    row_id = request.args.get('row_id', type=int)
    limit = request.args.get('limit', 50, type=int)

    logs = AuditLogger.get_logs(table_name=table_name, row_id=row_id, limit=limit)
    return jsonify({'success': True, 'logs': logs})


# =========================================================================
# 8. PHIẾU CHỈ ĐỊNH VÀ KẾT QUẢ XÉT NGHIỆM / CẬN LÂM SÀNG
# =========================================================================

@api_bp.route('/lab/orders', methods=['GET'])
@login_required
def get_lab_orders_api():
    """API lấy danh sách phiếu chỉ định cận lâm sàng (bệnh nhân chỉ xem kết quả đã duyệt)."""
    user = session.get('user', {})
    if user.get('vai_tro') == 'BENHNHAN':
        patient_id = user.get('patient_id')
        if not patient_id:
            return jsonify({'success': True, 'orders': []})
        orders = MedicalRecordModel.get_lab_orders_by_patient(patient_id, approved_only=True)
    else:
        orders = MedicalRecordModel.get_all_lab_orders()
    return jsonify({'success': True, 'orders': orders})

@api_bp.route('/lab/result/save', methods=['POST'])
@roles_required('ADMIN', 'KTV')
def save_lab_result():
    """API kỹ thuật viên nhập/cập nhật kết quả xét nghiệm (Chặn sửa nếu đã duyệt)."""
    data = request.get_json() or {}
    chi_tiet_id = data.get('chi_tiet_id') or data.get('order_id')
    ket_qua = data.get('ket_qua')
    file_ket_qua = data.get('file_ket_qua')
    user = session.get('user')

    if not chi_tiet_id or not ket_qua:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID chỉ định và nội dung kết quả xét nghiệm!'}), 400

    ok, msg = MedicalRecordModel.update_lab_result(chi_tiet_id, ket_qua, file_ket_qua=file_ket_qua, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/lab/result/approve', methods=['POST'])
@roles_required('ADMIN', 'BACSI')
def approve_lab_result_api():
    """API bác sĩ duyệt kết quả cận lâm sàng (xác nhận duyệt nội bộ)."""
    data = request.get_json() or {}
    chi_tiet_id = data.get('chi_tiet_id') or data.get('order_id')
    approval_note = data.get('approval_note') or data.get('ghi_chu')
    user = session.get('user')

    if not chi_tiet_id:
        return jsonify({'success': False, 'message': 'Thiếu ID chỉ định cận lâm sàng cần duyệt!'}), 400

    doc_name = user.get('ho_ten', 'Bác sĩ chuyên khoa')
    ok, msg = MedicalRecordModel.approve_lab_result(chi_tiet_id, doctor_name=doc_name, approval_note=approval_note, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/lab/result/view/<int:chi_tiet_id>', methods=['GET'])
@login_required
def view_lab_result(chi_tiet_id):
    """API xem chi tiết kết quả xét nghiệm (bệnh nhân chỉ xem khi đã duyệt)."""
    user = session.get('user', {})
    item = MedicalRecordModel.get_lab_item_by_id(chi_tiet_id)
    if not item:
        return jsonify({'success': False, 'message': 'Không tìm thấy kết quả xét nghiệm!'}), 404

    # Bệnh nhân chỉ xem được kết quả của mình và đã duyệt
    if user.get('vai_tro') == 'BENHNHAN':
        if item.get('patient_id') != user.get('patient_id'):
            return jsonify({'success': False, 'message': 'Bạn không có quyền xem kết quả này!'}), 403
        if item.get('trang_thai') != 'Đã duyệt':
            return jsonify({'success': False, 'message': 'Kết quả xét nghiệm đang được xử lý và chưa được bác sĩ phê duyệt!'}), 403

    return jsonify({'success': True, 'item': item})


# =========================================================================
# 9. CHỈNH SỬA VÀ QUẢN LÝ BỆNH ÁN ĐIỆN TỬ
# =========================================================================

@api_bp.route('/emr/detail/<int:record_id>', methods=['GET'])
@login_required
def get_emr_detail(record_id):
    """API xem chi tiết một phiếu khám bệnh án EMR."""
    user = session.get('user', {})
    rec = MedicalRecordModel.get_examination_by_id(record_id)
    if not rec:
        return jsonify({'success': False, 'message': 'Không tìm thấy hồ sơ bệnh án!'}), 404

    if user.get('vai_tro') == 'BENHNHAN' and rec['benh_nhan_id'] != user.get('patient_id'):
        return jsonify({'success': False, 'message': 'Bạn không có quyền xem hồ sơ bệnh án này!'}), 403

    return jsonify({'success': True, 'record': rec})

@api_bp.route('/emr/update', methods=['POST'])
@roles_required('BACSI')
def update_emr_record():
    """API bác sĩ chỉnh sửa hồ sơ bệnh án EMR (lưu vết kiểm toán trước/sau và lý do sửa)."""
    data = request.get_json() or {}
    record_id = data.get('record_id')
    diagnosis = data.get('diagnosis') or data.get('chan_doan_so_bo')
    icd = data.get('icd') or data.get('chan_doan_icd')
    treatment = data.get('treatment') or data.get('huong_dieu_tri')
    advice = data.get('advice') or data.get('loi_dan')
    reexam_date = data.get('reexam_date') or data.get('ngay_tai_kham')
    reason = data.get('reason') or data.get('ly_do_sua')

    if not record_id or not diagnosis or not treatment:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID phiếu khám, chẩn đoán và hướng điều trị!'}), 400

    user = session.get('user')
    doctor_id = user.get('bac_si_id')

    ok, msg = MedicalRecordModel.update_examination(
        record_id=record_id,
        doctor_id=doctor_id,
        diagnosis=diagnosis,
        icd=icd,
        treatment=treatment,
        advice=advice,
        reexam_date=reexam_date,
        reason=reason,
        audit_user=user
    )
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/emr/history/<int:record_id>', methods=['GET'])
@roles_required('ADMIN', 'BACSI')
def get_emr_history(record_id):
    """API xem lịch sử chỉnh sửa hồ sơ bệnh án."""
    from core.audit import AuditLogger
    logs = AuditLogger.get_logs(table_name='phieu_kham', row_id=record_id)
    return jsonify({'success': True, 'history': logs})


# =========================================================================
# 10. QUẢN LÝ ĐƠN THUỐC VÀ QUÁ TRÌNH ĐIỀU TRỊ
# =========================================================================

@api_bp.route('/prescription/detail/<int:prescription_id>', methods=['GET'])
@login_required
def get_prescription_detail_api(prescription_id):
    """API xem chi tiết đơn thuốc."""
    user = session.get('user', {})
    dt = PharmacyModel.get_prescription_detail(prescription_id)
    if not dt:
        return jsonify({'success': False, 'message': 'Không tìm thấy đơn thuốc!'}), 404

    if user.get('vai_tro') == 'BENHNHAN' and dt.get('benh_nhan_id') != user.get('patient_id'):
        return jsonify({'success': False, 'message': 'Bạn không có quyền xem đơn thuốc này!'}), 403

    return jsonify({'success': True, 'prescription': dt})

@api_bp.route('/prescription/update', methods=['POST'])
@roles_required('BACSI')
def update_prescription_api():
    """API bác sĩ cập nhật đơn thuốc chưa cấp phát (chặn sửa đơn đã cấp thuốc)."""
    data = request.get_json() or {}
    prescription_id = data.get('prescription_id')
    medicines = data.get('medicines', [])
    advice = data.get('advice') or data.get('loi_dan')
    reason = data.get('reason') or data.get('ly_do_sua')

    if not prescription_id or not medicines:
        return jsonify({'success': False, 'message': 'Thiếu ID đơn thuốc hoặc danh mục thuốc cần kê!'}), 400

    user = session.get('user')
    ok, msg = PharmacyModel.update_prescription(prescription_id, medicines, advice=advice, reason=reason, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/prescription/cancel', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'DUOCSI')
def cancel_prescription_api():
    """API hủy/điều chỉnh đơn thuốc đã lưu (xử lý tồn kho an toàn và lưu vết kiểm toán)."""
    data = request.get_json() or {}
    prescription_id = data.get('prescription_id')
    reason = data.get('reason') or data.get('ly_do')
    restore_stock = data.get('restore_stock', True)

    if not prescription_id or not reason:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID đơn thuốc và lý do hủy/điều chỉnh!'}), 400

    user = session.get('user')
    ok, msg = PharmacyModel.cancel_or_adjust_prescription(prescription_id, reason=reason, restore_stock=restore_stock, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@api_bp.route('/prescription/history/<int:prescription_id>', methods=['GET'])
@roles_required('ADMIN', 'BACSI', 'DUOCSI')
def get_prescription_history(prescription_id):
    """API xem lịch sử chỉnh sửa / xuất dược đơn thuốc."""
    from core.audit import AuditLogger
    logs = AuditLogger.get_logs(table_name='don_thuoc', row_id=prescription_id)
    return jsonify({'success': True, 'history': logs})

@api_bp.route('/patient/prescriptions', methods=['GET'])
@login_required
def get_patient_prescriptions():
    """API bệnh nhân xem các đơn thuốc của chính mình (chỉ xem, không sửa)."""
    user = session.get('user', {})
    patient_id = user.get('patient_id')
    if not patient_id:
        return jsonify({'success': True, 'prescriptions': []})

    prescriptions = PharmacyModel.get_prescriptions_by_patient(patient_id)
    return jsonify({'success': True, 'prescriptions': prescriptions})


# =========================================================================
# ALIAS ROUTES — Frontend convenience paths (map to admin routes)
# =========================================================================

@api_bp.route('/account/toggle', methods=['POST'])
@roles_required('ADMIN')
def account_toggle_alias():
    """Alias: /api/account/toggle → /api/admin/account/toggle."""
    data = request.get_json() or {}
    account_id = data.get('id') or data.get('account_id')
    if not account_id:
        return jsonify({'success': False, 'message': 'Thiếu ID tài khoản!'}), 400
    user = session.get('user')
    ok, res = UserModel.toggle_account_status(account_id, audit_user=user)
    if ok:
        status_text = 'kích hoạt' if res == 1 else 'vô hiệu hóa / khóa'
        return jsonify({'success': True, 'new_status': res, 'message': f'Đã {status_text} tài khoản thành công!'})
    return jsonify({'success': False, 'message': res}), 400


@api_bp.route('/account/reset-password', methods=['POST'])
@roles_required('ADMIN')
def account_reset_password_alias():
    """Alias: /api/account/reset-password → /api/admin/account/reset-password."""
    data = request.get_json() or {}
    account_id = data.get('id') or data.get('account_id')
    new_password = data.get('new_password')
    user = session.get('user')
    if not account_id or not new_password:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID tài khoản và mật khẩu mới!'}), 400
    ok, msg = UserModel.reset_account_password(account_id, new_password, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400


@api_bp.route('/account/change-role', methods=['POST'])
@roles_required('ADMIN')
def account_change_role_alias():
    """Alias: /api/account/change-role → /api/admin/account/set-role."""
    data = request.get_json() or {}
    account_id = data.get('id') or data.get('account_id')
    role_id = data.get('role_id')
    user = session.get('user')
    if not account_id or not role_id:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID tài khoản và ID vai trò!'}), 400
    ok, msg = UserModel.set_account_role(account_id, role_id, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400


@api_bp.route('/appointment/status', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN')
def appointment_status_alias():
    """Alias: /api/appointment/status → cập nhật trạng thái lịch hẹn từ admin UI."""
    data = request.get_json() or {}
    appointment_id = data.get('id') or data.get('appointment_id')
    new_status = data.get('status')
    user = session.get('user')
    if not appointment_id or not new_status:
        return jsonify({'success': False, 'message': 'Thiếu ID lịch hẹn hoặc trạng thái mới!'}), 400
    success, msg = AppointmentModel.update_status(appointment_id, new_status, user_info=user)
    return jsonify({'success': success, 'message': msg})


@api_bp.route('/appointment/create', methods=['POST'])
@roles_required('ADMIN', 'LETAN', 'BACSI')
def appointment_create_alias():
    """API tạo lịch hẹn mới từ giao diện admin."""
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    ngay_kham = data.get('ngay_kham') or data.get('ngay_hen')
    gio_kham = data.get('gio_kham') or data.get('gio_hen')
    ly_do = data.get('ly_do_kham') or data.get('ly_do', 'Khám theo yêu cầu')
    bac_si_id = data.get('doctor_id') or data.get('bac_si_id')
    chuyen_khoa_id = data.get('chuyen_khoa_id', 1)
    user = session.get('user')

    if not patient_id or not ngay_kham or not gio_kham:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp bệnh nhân, ngày và giờ khám!'}), 400

    success, result = AppointmentModel.create(
        patient_id, chuyen_khoa_id, bac_si_id, ngay_kham, gio_kham, ly_do, audit_user=user
    )
    if success:
        return jsonify({'success': True, 'ma_lich_hen': result, 'message': 'Tạo lịch hẹn thành công!'})
    return jsonify({'success': False, 'message': result}), 400


@api_bp.route('/lab/result/save-alias', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'KTV')
def lab_result_save_alias():
    """Alias đơn giản cho lưu kết quả xét nghiệm (dùng bởi lab.html JS)."""
    return save_lab_result()
