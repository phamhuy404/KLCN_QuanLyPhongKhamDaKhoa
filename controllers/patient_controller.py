from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from core.security import login_required
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.billing_model import BillingModel
from models.clinic_model import ClinicModel
from models.user_model import UserModel

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def _get_current_patient_id():
    """Lấy ID bệnh nhân từ phiên đăng nhập hiện tại."""
    user = session.get('user')
    if not user:
        return None
    if user.get('patient_id'):
        return user['patient_id']
    # Nếu là bác sĩ/admin đang xem thử giao diện bệnh nhân
    return 1

@patient_bp.route('/')
@patient_bp.route('/dashboard')
@login_required
def dashboard():
    """Bảng điều khiển tổng quan cổng bệnh nhân."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    appointments = AppointmentModel.get_by_patient(patient_id)
    return render_template('patient/dashboard.html', active_page='dashboard', patient=patient, appointments=appointments)

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

        success, _ = AppointmentModel.create(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do)
        return redirect(url_for('patient.dashboard'))

    patient = PatientModel.get_by_id(patient_id)
    departments = ClinicModel.get_all_departments(active_only=True)
    doctors = UserModel.get_all_doctors()
    return render_template('patient/booking.html', active_page='booking', patient=patient, departments=departments, doctors=doctors)

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
    return render_template('patient/lab_results.html', active_page='lab_results', patient=patient)

@patient_bp.route('/billing')
@login_required
def billing():
    """Tra cứu hóa đơn viện phí và chi trả BHYT."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    invoices = BillingModel.get_by_patient(patient_id)
    
    # --- THÊM ĐOẠN NÀY ĐỂ FIX LỖI THIẾU KEY ---
    if invoices:
        for inv in invoices:
            if 'tien_bhyt_chi_tra' not in inv or inv['tien_bhyt_chi_tra'] is None:
                inv['tien_bhyt_chi_tra'] = 0
    # ------------------------------------------

    return render_template('patient/billing.html', active_page='billing', patient=patient, invoices=invoices)

@patient_bp.route('/profile')
@login_required
def profile():
    """Thông tin cá nhân, BHYT và số liên hệ khẩn cấp."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    return render_template('patient/profile.html', active_page='profile', patient=patient)

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
        chu_de = request.form.get('chu_de', 'Dịch vụ khám bệnh')
        diem_danh_gia = request.form.get('diem_danh_gia', 5, type=int)
        noi_dung = request.form.get('noi_dung', '')
        phieu_kham_id = request.form.get('phieu_kham_id', type=int)
        FeedbackModel.create(patient_id, phieu_kham_id, chu_de, diem_danh_gia, noi_dung)
        return redirect(url_for('patient.feedbacks'))

    my_feedbacks = FeedbackModel.get_by_patient(patient_id)
    return render_template('patient/feedbacks.html', active_page='feedbacks', patient=patient, feedbacks=my_feedbacks)

@patient_bp.route('/notifications')
@login_required
def notifications():
    """Xem danh sách toàn bộ thông báo in-app của tài khoản."""
    from models.notification_model import NotificationModel
    user = session.get('user', {})
    tai_khoan_id = user.get('id')
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    notifs = NotificationModel.get_user_notifications(tai_khoan_id, limit=50)
    unread_cnt = NotificationModel.get_unread_count(tai_khoan_id)
    return render_template('patient/notifications.html', active_page='notifications', patient=patient, notifications=notifs, unread_count=unread_cnt)

