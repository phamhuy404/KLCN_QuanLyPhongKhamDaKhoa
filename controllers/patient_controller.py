from flask import Blueprint, render_template, request, redirect, url_for, session
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
    """Đặt lịch khám bệnh trực tuyến."""
    patient_id = _get_current_patient_id()

    if request.method == 'POST':
        chuyen_khoa_id = request.form.get('chuyen_khoa_id', 1, type=int)
        bac_si_id = request.form.get('bac_si_id', type=int)
        ngay_hen = request.form.get('ngay_hen')
        gio_hen = request.form.get('gio_hen')
        ly_do = request.form.get('ly_do', '')

        success, _ = AppointmentModel.create(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do)
        return redirect(url_for('patient.dashboard'))

    departments = ClinicModel.get_all_departments()
    doctors = UserModel.get_all_doctors()
    return render_template('patient/booking.html', active_page='booking', departments=departments, doctors=doctors)

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
    return render_template('patient/billing.html', active_page='billing', patient=patient, invoices=invoices)

@patient_bp.route('/profile')
@login_required
def profile():
    """Thông tin cá nhân, BHYT và số liên hệ khẩn cấp."""
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    return render_template('patient/profile.html', active_page='profile', patient=patient)
