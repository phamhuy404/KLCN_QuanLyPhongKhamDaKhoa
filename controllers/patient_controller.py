from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from core.security import login_required, roles_required, current_patient_id
from core.validators import validate_patient_profile
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.billing_model import BillingModel
from models.clinic_model import ClinicModel
from models.user_model import UserModel

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.before_request
@roles_required('BENHNHAN')
def check_patient_profile_completion():
    """Kiểm tra bệnh nhân đã hoàn thiện thông tin cá nhân chưa trước khi truy cập các tính năng."""
    user = session.get('user')
    if user and user.get('vai_tro') == 'BENHNHAN':
        # Nếu chưa hoàn thiện hồ sơ và không ở trang complete-profile
        if not user.get('da_hoan_thien_ho_so'):
            if request.endpoint and request.endpoint != 'patient.complete_profile' and request.endpoint != 'auth.logout':
                return redirect(url_for('patient.complete_profile'))

def _get_current_patient_id():
    """Lấy ID bệnh nhân từ phiên đăng nhập hiện tại theo tai_khoan_id."""
    return current_patient_id()

@patient_bp.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    """Trang điền thông tin cá nhân khi đăng ký mới và đăng nhập lần đầu."""
    user = session.get('user')
    if not user or user.get('vai_tro') != 'BENHNHAN':
        return redirect(url_for('admin.dashboard'))

    # Nếu đã hoàn thiện rồi thì không cần điền lại, về dashboard
    if user.get('da_hoan_thien_ho_so'):
        return redirect(url_for('patient.dashboard'))

    patient_id = _get_current_patient_id()
    from core.catalog import get_all_catalogs
    catalogs = get_all_catalogs()
    patient = PatientModel.get_by_id(patient_id) if patient_id else None
    cur_nhom_mau = (patient.get('nhom_mau') if patient else None) or 'Chưa rõ'

    if request.method == 'POST':
        cur_nhom_mau = request.form.get('nhom_mau', cur_nhom_mau)
        is_valid, errors = validate_patient_profile(request.form)
        if not is_valid:
            return render_template('patient/complete_profile.html', errors=errors, form=request.form, patient=patient, cur_nhom_mau=cur_nhom_mau, catalogs=catalogs)

        # Lưu thông tin hồ sơ vào SQL Server
        success, msg = UserModel.complete_patient_profile(user['id'], request.form)
        if not success:
            return render_template('patient/complete_profile.html', errors={'db': msg}, form=request.form, patient=patient, cur_nhom_mau=cur_nhom_mau, catalogs=catalogs)

        # Cập nhật lại session
        user['da_hoan_thien_ho_so'] = 1
        user['ho_ten'] = request.form.get('ho_ten', '').strip()
        session['user'] = user

        flash('Hồ sơ bệnh nhân của bạn đã được kích hoạt thành công!', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template('patient/complete_profile.html', patient=patient, cur_nhom_mau=cur_nhom_mau, catalogs=catalogs)

@patient_bp.route('/')
@patient_bp.route('/dashboard')
@login_required
def dashboard():
    """Bảng điều khiển tổng quan cổng bệnh nhân kèm quét nhắc lịch khám tự động."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    appointments = AppointmentModel.get_by_patient(patient_id)

    # Tự động quét và nhắc nhở lịch khám trong 24h - 48h tới
    try:
        from core.notification_service import NotificationService
        NotificationService.run_all_reminders()
    except Exception as e:
        pass

    user = session.get('user', {})
    tai_khoan_id = user.get('id')
    recent_notifs = []
    if tai_khoan_id:
        try:
            from models.notification_model import NotificationModel
            recent_notifs = NotificationModel.get_user_notifications(tai_khoan_id, limit=5)
        except Exception:
            pass

    upcoming_appointment = appointments[0] if appointments else None

    return render_template('patient/dashboard.html', active_page='dashboard', patient=patient, appointments=appointments, upcoming_appointment=upcoming_appointment, recent_notifications=recent_notifs)

@patient_bp.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    """Đặt lịch khám bệnh trực tuyến (Chỉ hiển thị chuyên khoa và bác sĩ đang hoạt động)."""
    patient_id = _get_current_patient_id()

    if request.method == 'POST':
        chuyen_khoa_id = request.form.get('chuyen_khoa_id', 1, type=int)
        bac_si_id = request.form.get('bac_si_id', type=int)
        ngay_hen = request.form.get('ngay_hen')
        gio_hen = request.form.get('gio_hen')
        ly_do = request.form.get('ly_do', '')

        success, res = AppointmentModel.create(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do)
        if success:
            flash('Đặt lịch khám thành công! Hệ thống đang chờ Lễ tân tiếp nhận.', 'success')
            return redirect(url_for('patient.dashboard'))
        else:
            flash(f'Đặt lịch khám thất bại: {res}', 'error')

    patient = PatientModel.get_by_id(patient_id)
    departments = ClinicModel.get_all_departments(active_only=True)
    doctors = UserModel.get_all_doctors()
    return render_template('patient/booking.html', active_page='booking', patient=patient, departments=departments, doctors=doctors)

@patient_bp.route('/appointments')
@login_required
def appointments():
    """Xem và quản lý toàn bộ danh sách lịch hẹn khám của bệnh nhân."""
    patient_id = _get_current_patient_id()
    patient = None
    if patient_id:
        patient = PatientModel.get_by_id(patient_id)

    appts = AppointmentModel.get_by_patient(patient_id) if patient_id else []
    return render_template('patient/appointments.html', active_page='appointments', patient=patient, appointments=appts)

@patient_bp.route('/records')
@login_required
def records():
    """Hồ sơ bệnh án điện tử cá nhân của bệnh nhân."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    return render_template('patient/records.html', active_page='records', patient=patient)

@patient_bp.route('/lab-results')
@login_required
def lab_results():
    """Tra cứu kết quả xét nghiệm và chẩn đoán hình ảnh."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    all_cls, cls_stats = PatientModel.get_all_lab_results(patient_id)
    return render_template('patient/lab_results.html', active_page='lab_results', patient=patient, all_cls=all_cls, cls_stats=cls_stats)

@patient_bp.route('/billing')
@login_required
def billing():
    """Tra cứu hóa đơn viện phí và chi trả BHYT."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    invoices = BillingModel.get_by_patient(patient_id)
    
    # Toàn bộ tính toán tổng hợp, bóc tách và phân loại thực hiện ở BackEnd
    tong_tien = sum(float(inv.get('tong_tien') or 0) for inv in invoices)
    tien_bhyt = sum(float(inv.get('tien_bhyt_chi_tra') or inv.get('tien_bhyt') or 0) for inv in invoices)
    da_thanh_toan = sum(float(inv.get('thanh_tien') or 0) for inv in invoices if inv.get('trang_thai') == 'Đã thanh toán')
    chua_thanh_toan = sum(float(inv.get('thanh_tien') or 0) for inv in invoices if inv.get('trang_thai') == 'Chưa thanh toán')
    unpaid_list = [inv for inv in invoices if inv.get('trang_thai') == 'Chưa thanh toán']
    first_unpaid = unpaid_list[0] if unpaid_list else None

    billing_stats = {
        'tong_tien': tong_tien,
        'tien_bhyt': tien_bhyt,
        'da_thanh_toan': da_thanh_toan,
        'chua_thanh_toan': chua_thanh_toan,
        'so_hoa_don_cho': len(unpaid_list),
        'tong_so_hoa_don': len(invoices)
    }

    return render_template('patient/billing.html', active_page='billing', patient=patient, invoices=invoices, billing_stats=billing_stats, unpaid=first_unpaid)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Thông tin cá nhân, BHYT và số liên hệ khẩn cấp kèm danh mục y tế chuẩn."""
    from core.catalog import get_all_catalogs
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    catalogs = get_all_catalogs()

    if request.method == 'POST':
        data = request.form.to_dict()
        success, msg = PatientModel.update_profile(patient_id, data)
        if success:
            if 'user' in session:
                session['user']['ho_ten'] = data.get('ho_ten', session['user'].get('ho_ten'))
                session['user']['sdt'] = data.get('sdt', session['user'].get('sdt'))
                session['user']['email'] = data.get('email', session['user'].get('email'))
                session.modified = True
            flash('Lưu và đồng bộ hồ sơ y tế thành công!', 'success')
            return redirect(url_for('patient.profile'))
        else:
            flash(f'Lỗi cập nhật hồ sơ: {msg}', 'error')

    return render_template('patient/profile.html', active_page='profile', patient=patient, catalogs=catalogs)

@patient_bp.route('/profile/avatar', methods=['POST'])
@login_required
def profile_avatar():
    """Cập nhật ảnh đại diện bệnh nhân hỗ trợ tải tệp đa định dạng hoặc dán link URL."""
    from core.image_service import process_image_input
    patient_id = _get_current_patient_id()
    if not patient_id:
        flash('Không tìm thấy thông tin bệnh nhân.', 'error')
        return redirect(url_for('patient.profile'))

    image_file = request.files.get('avatar_file')
    avatar_url = (request.form.get('avatar_url') or '').strip()

    source = image_file if (image_file and getattr(image_file, 'filename', None)) else avatar_url
    if not source:
        flash('Vui lòng chọn tệp ảnh hoặc nhập đường dẫn ảnh hợp lệ.', 'warning')
        return redirect(url_for('patient.profile'))

    final_path, err = process_image_input(source, category='benh_nhan', quality=85)
    if err:
        flash(err, 'error')
        return redirect(url_for('patient.profile'))

    if final_path:
        PatientModel.update_patient_avatar(patient_id, final_path)
        flash('Cập nhật ảnh đại diện thành công!', 'success')
    else:
        flash('Không thể xử lý hình ảnh đã cung cấp.', 'error')

    return redirect(url_for('patient.profile'))

@patient_bp.route('/feedbacks', methods=['GET', 'POST'])
@login_required
def feedbacks():
    """Cổng gửi và tra cứu tiến độ xử lý phản hồi, đóng góp ý kiến của bệnh nhân."""
    from models.feedback_model import FeedbackModel
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)

    if request.method == 'POST':
        chu_de = request.form.get('chu_de') or request.form.get('tieu_de') or 'Dịch vụ khám bệnh'
        raw_diem = request.form.get('diem_danh_gia') or request.form.get('danh_gia') or 5
        try:
            diem_danh_gia = int(raw_diem)
        except (ValueError, TypeError):
            diem_danh_gia = 5
        noi_dung = request.form.get('noi_dung', '')
        phieu_kham_id = request.form.get('phieu_kham_id', type=int)
        FeedbackModel.create(patient_id, phieu_kham_id, chu_de, diem_danh_gia, noi_dung)
        return redirect(url_for('patient.feedbacks'))

    my_feedbacks = FeedbackModel.get_by_patient(patient_id)
    return render_template('patient/feedbacks.html', active_page='feedbacks', patient=patient, feedbacks=my_feedbacks)

@patient_bp.route('/notifications')
@login_required
def notifications():
    """Xem danh sách toàn bộ thông báo in-app của tài khoản bệnh nhân."""
    from models.notification_model import NotificationModel
    user = session.get('user', {})
    tai_khoan_id = user.get('id')
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    loai = request.args.get('tab', 'all')
    unread_only = request.args.get('unread', '0') == '1'
    notifs = NotificationModel.get_user_notifications(tai_khoan_id, limit=None, loai=loai, unread_only=unread_only)
    unread_cnt = NotificationModel.get_unread_count(tai_khoan_id)
    return render_template('patient/notifications.html',
                           active_page='notifications',
                           patient=patient,
                           notifications=notifs,
                           unread_count=unread_cnt,
                           active_tab=loai,
                           unread_only=unread_only)
