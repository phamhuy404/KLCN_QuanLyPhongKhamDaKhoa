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
def book_appointment():
    """API đặt lịch hẹn khám bệnh."""
    data = request.get_json() or {}
    user = session.get('user')
    patient_id = data.get('patient_id') or (user.get('patient_id') if user else 1)

    chuyen_khoa_id = data.get('chuyen_khoa_id', 1)
    bac_si_id = data.get('bac_si_id')
    ngay_hen = data.get('ngay_hen')
    gio_hen = data.get('gio_hen')
    ly_do = data.get('ly_do', 'Khám theo yêu cầu')

    if not ngay_hen or not gio_hen:
        return jsonify({'success': False, 'message': 'Vui lòng chọn ngày và giờ khám!'}), 400

    success, result = AppointmentModel.create(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do)
    if success:
        return jsonify({'success': True, 'ma_lich_hen': result, 'message': 'Đặt lịch thành công!'})
    return jsonify({'success': False, 'message': result}), 400

@api_bp.route('/appointment/update-status', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN')
def update_appointment_status():
    """API cập nhật trạng thái lịch hẹn khám."""
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    new_status = data.get('status')

    if not appointment_id or not new_status:
        return jsonify({'success': False, 'message': 'Thiếu tham số!'}), 400

    success, msg = AppointmentModel.update_status(appointment_id, new_status)
    return jsonify({'success': success, 'message': msg})

@api_bp.route('/admin/reset-password', methods=['POST'])
@roles_required('ADMIN')
def reset_password():
    """API quản trị viên đặt lại mật khẩu cho bệnh nhân."""
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    new_password = data.get('new_password')

    if not patient_id or not new_password:
        return jsonify({'success': False, 'message': 'Thiếu thông tin yêu cầu!'}), 400

    success, msg = UserModel.reset_patient_password(patient_id, new_password)
    return jsonify({'success': success, 'message': msg})

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
    """API dược sĩ xuất thuốc và trừ số lượng kho."""
    data = request.get_json() or {}
    ma_don = data.get('ma_don') or data.get('prescription_id')
    if not ma_don:
        return jsonify({'success': False, 'message': 'Thiếu mã đơn thuốc!'}), 400

    success, msg = PharmacyModel.dispense_prescription(ma_don)
    return jsonify({'success': success, 'message': msg})

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
