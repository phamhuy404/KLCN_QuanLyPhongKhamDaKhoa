from flask import Blueprint, render_template, request, abort
from core.security import roles_required
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.clinic_model import ClinicModel
from models.user_model import UserModel

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def admin_access_guard():
    """Bảo vệ phân hệ quản trị: Chỉ cho phép nhân viên y tế và admin truy cập."""
    pass

@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    """Bảng điều khiển quản trị tổng quan toàn hệ thống."""
    stats = ClinicModel.get_dashboard_stats()
    patients = PatientModel.get_all()
    appointments = AppointmentModel.get_all()
    return render_template('admin/dashboard.html', active_page='admin_dashboard', stats=stats, patients=patients, appointments=appointments)

@admin_bp.route('/patients')
def patients():
    """Quản lý danh sách hồ sơ bệnh nhân."""
    patients_list = PatientModel.get_all()
    return render_template('admin/patients.html', active_page='admin_patients', patients=patients_list)

@admin_bp.route('/patients/<int:patient_id>')
@admin_bp.route('/patient_details/<int:patient_id>')
@admin_bp.route('/patient-details/<int:patient_id>')
@admin_bp.route('/patient_detail/<int:patient_id>')
def patient_detail(patient_id):
    """Xem hồ sơ bệnh án 360 độ của một bệnh nhân."""
    patient = PatientModel.get_by_id(patient_id)
    if not patient:
        abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@admin_bp.route('/patient_details')
@admin_bp.route('/patient-details')
def patient_details_default():
    """Xem hồ sơ bệnh nhân đầu tiên hoặc theo id từ query string."""
    patient_id = request.args.get('id', type=int)
    if patient_id:
        patient = PatientModel.get_by_id(patient_id)
    else:
        patients_list = PatientModel.get_all()
        patient = patients_list[0] if patients_list else None

    if not patient:
        abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@admin_bp.route('/appointments')
def appointments():
    """Quản lý tiếp nhận và phân bổ lịch hẹn khám."""
    appointments_list = AppointmentModel.get_all()
    patients_list = PatientModel.get_all()
    return render_template('admin/appointments.html', active_page='admin_appointments', appointments=appointments_list, patients=patients_list)

@admin_bp.route('/reception')
def reception():
    """Phân hệ tiếp đón lễ tân, check-in và đăng ký người bệnh mới."""
    patients_list = PatientModel.get_all()
    appointments_list = AppointmentModel.get_all()
    departments = ClinicModel.get_all_departments()
    return render_template('admin/reception.html', active_page='admin_reception', patients=patients_list, appointments=appointments_list, departments=departments)

@admin_bp.route('/emr')
def emr():
    """Phân hệ bác sĩ: Bệnh án điện tử EMR, chẩn đoán ICD và ra y lệnh."""
    patients_list = PatientModel.get_all()
    medicines = PharmacyModel.get_all_medicines()
    services = ClinicModel.get_all_services()
    doctors = UserModel.get_all_doctors()
    return render_template('admin/emr.html', active_page='admin_emr', patients=patients_list, medicines=medicines, services=services, doctors=doctors)

@admin_bp.route('/lab')
def lab():
    """Phân hệ kỹ thuật viên: Thực hiện xét nghiệm và chẩn đoán hình ảnh."""
    patients_list = PatientModel.get_all()
    services = ClinicModel.get_all_services()
    lab_orders = MedicalRecordModel.get_all_lab_orders()
    return render_template('admin/lab.html', active_page='admin_lab', patients=patients_list, services=services, lab_orders=lab_orders)

@admin_bp.route('/pharmacy')
def pharmacy():
    """Phân hệ dược sĩ: Quản lý kho dược và xuất cấp thuốc theo đơn."""
    medicines = PharmacyModel.get_all_medicines()
    prescriptions = MedicalRecordModel.get_all_prescriptions()
    return render_template('admin/pharmacy.html', active_page='admin_pharmacy', medicines=medicines, prescriptions=prescriptions)

@admin_bp.route('/billing')
def billing():
    """Phân hệ thu ngân: Viện phí, chi trả BHYT và xuất hóa đơn điện tử."""
    invoices = BillingModel.get_all()
    patients_list = PatientModel.get_all()
    return render_template('admin/billing.html', active_page='admin_billing', invoices=invoices, patients=patients_list)

@admin_bp.route('/reports')
def reports():
    """Báo cáo thống kê doanh thu, lưu lượng bệnh nhân và hiệu suất phòng khám."""
    stats = ClinicModel.get_dashboard_stats()
    invoices = BillingModel.get_all()
    return render_template('admin/reports.html', active_page='admin_reports', stats=stats, invoices=invoices)
