"""Bearer-only patient API, reusing the same models and policy as the web portal."""
from datetime import date, datetime, time
from decimal import Decimal
from flask import Blueprint, request, jsonify, g
from core.database import get_db
from core.mobile_auth import contract, bearer, verify, fail, public_user, MobileAuthError
from core.validators import validate_patient_profile
from core.security import positive_id
from core.catalog import get_all_catalogs
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.clinic_model import ClinicModel
from models.user_model import UserModel
from models.billing_model import BillingModel
from models.pharmacy_model import PharmacyModel
from models.feedback_model import FeedbackModel
from models.notification_model import NotificationModel

mobile_patient_bp = Blueprint('mobile_patient', __name__, url_prefix='/api/v1/mobile/patient')
PROFILE_FIELDS = ('username', 'ho_ten', 'sdt', 'ngay_sinh', 'gioi_tinh', 'cccd', 'bhyt',
    'email', 'dia_chi', 'nhom_mau', 'ghi_chu_nhom_mau', 'di_ung', 'tien_su_benh',
    'tien_su_gia_dinh', 'nguoi_than_ho_ten', 'nguoi_than_sdt', 'nguoi_than_quan_he')


def json_value(value):
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, (date, datetime, time)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def respond(**values):
    return jsonify(json_value(dict(success=True, **values)))


@mobile_patient_bp.before_request
def authenticate():
    try:
        return authenticate_request()
    except MobileAuthError as error:
        return jsonify(success=False, error_code=error.code, message=error.message), error.status
    except Exception:
        return jsonify(success=False, error_code='SERVICE_UNAVAILABLE', message='Không thể xác thực lúc này. Vui lòng thử lại.'), 503


def authenticate_request():
    token = bearer()
    connection = get_db()
    try:
        user, _, _ = verify(connection.cursor(), token)
    finally:
        connection.close()
    # Request-local only: do not create or authenticate a Flask cookie session.
    g.authenticated_user = user
    g.mobile_patient = user
    if not user.get('da_hoan_thien_ho_so') and request.endpoint not in {
            'mobile_patient.profile', 'mobile_patient.complete_profile'}:
        fail('PROFILE_REQUIRED', 'Vui lòng hoàn thiện thông tin cá nhân trước.', 409)
    return None


@mobile_patient_bp.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


def patient_id():
    return g.mobile_patient['patient_id']


def body():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        fail('VALIDATION_ERROR', 'Cần JSON object hợp lệ.', 400)
    return value


def identifier(value, optional=False):
    if optional and value in (None, ''):
        return None
    result = positive_id(value)
    if result is None:
        fail('VALIDATION_ERROR', 'Mã dữ liệu không hợp lệ.', 400)
    return result


def own_appointment(appt_id):
    appointment = AppointmentModel.get_by_id(appt_id)
    if not appointment or appointment.get('benh_nhan_id') != patient_id():
        fail('NOT_FOUND', 'Không tìm thấy lịch hẹn của bạn.', 404)
    return appointment


def result_or_fail(result, code='UPDATE_FAILED', status=409):
    ok, message = result
    if not ok:
        # Legacy models may include SQL exception text; never return that text.
        if any(word in str(message).lower() for word in ('sql', 'odbc', 'traceback', 'driver')):
            fail('SERVICE_UNAVAILABLE', 'Không thể hoàn tất thao tác. Vui lòng thử lại.', 503)
        fail(code, str(message), status)
    return message


def profile_data():
    raw = PatientModel.get_by_id(patient_id())
    if not raw:
        fail('PATIENT_NOT_FOUND', 'Không tìm thấy hồ sơ bệnh nhân.', 404)
    data = {key: raw.get(key) for key in PROFILE_FIELDS}
    data.update(id=raw['id'], ma_bn=raw.get('ma_benh_nhan'),
        so_cccd=raw.get('cccd'), so_the_bhyt=raw.get('bhyt'), avatar=raw.get('avatar'),
        vitals=raw.get('vitals'), profile_complete=bool(g.mobile_patient.get('da_hoan_thien_ho_so')),
        qr_payload=raw.get('ma_benh_nhan'))
    return data


@mobile_patient_bp.get('/profile')
@contract
def profile():
    return respond(patient=profile_data(), catalogs=get_all_catalogs())


def validated_profile(onboarding=False):
    raw = body()
    # Reject nested/overlong fields before invoking the shared web validators.
    data = {key: raw[key] for key in PROFILE_FIELDS if key in raw}
    if any(not isinstance(v, str) or len(v) > 4000 for v in data.values()):
        fail('VALIDATION_ERROR', 'Trường thông tin không hợp lệ hoặc quá dài.', 400)
    current = profile_data()
    merged = {key: str(current.get(key) or '') for key in PROFILE_FIELDS}
    merged.update(data)
    if onboarding:
        # The web keeps the registered phone read-only during onboarding.
        merged['sdt'] = g.mobile_patient.get('sdt') or current.get('sdt') or ''
    valid, errors = validate_patient_profile(merged, onboarding=onboarding)
    if not valid:
        fail('VALIDATION_ERROR', '\n'.join(errors.values()), 400)
    if merged.get('nhom_mau') and merged['nhom_mau'] not in get_all_catalogs()['nhom_mau']:
        fail('VALIDATION_ERROR', 'Nhóm máu không thuộc danh mục.', 400)
    return merged


@mobile_patient_bp.post('/complete-profile')
@contract
def complete_profile():
    data = validated_profile(onboarding=True)
    result_or_fail(UserModel.complete_patient_profile(g.mobile_patient['id'], data))
    user = UserModel.get_session_user(g.mobile_patient['id'])
    return respond(message='Đã hoàn thiện hồ sơ.', user=public_user(user))


@mobile_patient_bp.put('/profile')
@contract
def update_profile():
    if not g.mobile_patient.get('da_hoan_thien_ho_so'):
        fail('PROFILE_REQUIRED', 'Vui lòng hoàn thiện thông tin cá nhân trước.', 409)
    data = validated_profile()
    result_or_fail(PatientModel.update_profile(patient_id(), data), status=400)
    user = UserModel.get_session_user(g.mobile_patient['id'])
    return respond(message='Đã lưu thông tin cá nhân.', user=public_user(user))


@mobile_patient_bp.post('/profile/avatar')
@contract
def avatar():
    from core.image_service import process_image_input, MAX_IMAGE_BYTES
    if request.content_length and request.content_length > MAX_IMAGE_BYTES + 256 * 1024:
        fail('IMAGE_TOO_LARGE', 'Ảnh vượt quá 8 MiB.', 413)
    source = request.files.get('avatar_file')
    if source is None:
        source = (request.form.get('avatar_url') or '').strip()
    if not source:
        fail('VALIDATION_ERROR', 'Chọn ảnh hoặc nhập URL HTTPS được phép.', 400)
    path, error = process_image_input(source, category='benh_nhan', quality=85)
    if error or not path:
        fail('INVALID_IMAGE', error or 'Ảnh không hợp lệ.', 400)
    result_or_fail(PatientModel.update_patient_avatar(patient_id(), path))
    return respond(message='Đã cập nhật ảnh đại diện.', avatar=path)


@mobile_patient_bp.get('/dashboard')
@contract
def dashboard():
    patient = profile_data()
    appointments = AppointmentModel.get_by_patient(patient_id())
    upcoming = [a for a in appointments if a.get('status_code') in ('waiting', 'confirmed')]
    upcoming.sort(key=lambda a: (str(a.get('ngay_hen') or ''), str(a.get('gio_hen') or '')))
    return respond(patient=patient, upcoming_appointment=upcoming[0] if upcoming else None,
        latest_vitals=patient.get('vitals'), unread_notifications=NotificationModel.get_unread_count(g.mobile_patient['id']))


@mobile_patient_bp.get('/booking-meta')
@contract
def booking_meta():
    departments = ClinicModel.get_all_departments(active_only=True)
    department = request.args.get('chuyen_khoa_id', type=int)
    department = department or (departments[0]['id'] if departments else None)
    if department is None:
        return respond(departments=[], specialties=[], doctors=[], slots=[], booked_slots=[], exam_services=[])
    if not any(d['id'] == department for d in departments):
        fail('VALIDATION_ERROR', 'Chuyên khoa không hoạt động.', 400)
    day = request.args.get('date') or date.today().isoformat()
    try:
        date.fromisoformat(day)
    except ValueError:
        fail('VALIDATION_ERROR', 'Ngày hẹn không hợp lệ.', 400)
    matrix = AppointmentModel.get_booking_matrix(day, department)
    if not matrix.get('success'):
        fail('BOOKING_UNAVAILABLE', 'Không thể tải lịch khám.', 503)
    doctor = request.args.get('bac_si_id', type=int)
    available = matrix.get('doctor_slots', {}).get(doctor, []) if doctor else matrix.get('all_available_slots', [])
    services = [s for s in ClinicModel.get_exam_services(active_only=True)
        if s.get('chuyen_khoa_id') in (None, department)]
    now = datetime.now()
    available = [slot for slot in available if datetime.fromisoformat(day + 'T' + slot) > now]
    return respond(departments=departments, specialties=departments,
        doctors=matrix.get('doctors', []), slots=available, booked_slots=[],
        exam_services=services, matrix=matrix, department_id=department)


@mobile_patient_bp.get('/appointments')
@contract
def appointments():
    return respond(appointments=AppointmentModel.get_by_patient(patient_id()))


@mobile_patient_bp.get('/appointments/<int:appt_id>')
@contract
def appointment_detail(appt_id):
    return respond(appointment=own_appointment(appt_id))


@mobile_patient_bp.post('/appointments')
@contract
def create_appointment():
    data = body()
    department = identifier(data.get('chuyen_khoa_id'))
    doctor = identifier(data.get('bac_si_id'), optional=True)
    reason = str(data.get('ly_do') or '').strip()
    if len(reason) > 2000:
        fail('VALIDATION_ERROR', 'Lý do khám quá dài.', 400)
    from core.exam_services import appointment_reason
    from core.scheduling import CalendarError
    try:
        reason = appointment_reason(data.get('exam_service_id'), department, reason)
    except CalendarError as exc:
        fail('VALIDATION_ERROR', str(exc), 400)
    result = result_or_fail(AppointmentModel.create(patient_id(), department, doctor,
        data.get('ngay_hen') or data.get('date'), data.get('gio_hen') or data.get('time'), reason,
        audit_user=g.mobile_patient, return_details=True), 'BOOKING_CONFLICT')
    return respond(message='Đã gửi yêu cầu đặt lịch. Vui lòng chờ tiếp đón xác nhận.', appointment=result), 201


@mobile_patient_bp.post('/appointments/<int:appt_id>/reschedule')
@contract
def reschedule(appt_id):
    own_appointment(appt_id)
    data = body()
    message = result_or_fail(AppointmentModel.reschedule(appt_id,
        data.get('ngay_hen'), data.get('gio_hen'), ly_do=data.get('ly_do'),
        new_doctor_id=identifier(data.get('bac_si_id'), optional=True), user_info=g.mobile_patient), 'BOOKING_CONFLICT')
    return respond(message=message)


@mobile_patient_bp.post('/appointments/<int:appt_id>/cancel')
@contract
def cancel(appt_id):
    own_appointment(appt_id)
    data = body()
    message = result_or_fail(AppointmentModel.cancel(appt_id, reason=data.get('reason'), user_info=g.mobile_patient))
    return respond(message=message)


@mobile_patient_bp.get('/records')
@contract
def records():
    history = PatientModel.get_patient_history(patient_id(), approved_only=True)
    vitals = profile_data().get('vitals')
    return respond(records=history, vitals=vitals, latest_vitals=vitals)


@mobile_patient_bp.post('/prescriptions/<int:prescription_id>/purchase-option')
@contract
def purchase_option(prescription_id):
    prescription = PharmacyModel.get_prescription_detail(prescription_id)
    if not prescription or prescription.get('benh_nhan_id') != patient_id():
        fail('NOT_FOUND', 'Không tìm thấy đơn thuốc của bạn.', 404)
    option = body().get('option')
    if option not in ('Mua tại bệnh viện', 'Tự mua ngoài'):
        fail('VALIDATION_ERROR', 'Hình thức nhận thuốc không hợp lệ.', 400)
    return respond(message=result_or_fail(PharmacyModel.choose_medicine_purchase_option(
        prescription_id, option, audit_user=g.mobile_patient)))


def lab_items():
    results, _ = PatientModel.get_all_lab_results(patient_id())
    items = []
    for result in results:
        cls, encounter = result['cls'], result['enc']
        item = dict(result)
        item.update(id=cls['chi_tiet_id'], ten_dich_vu=cls.get('ten'), loai_dich_vu=cls.get('loai'),
            nguoi_thuc_hien=cls.get('bac_si_thuc_hien'), bac_si_chi_dinh=encounter.get('bac_si'),
            chan_doan=encounter.get('chan_doan_icd') or encounter.get('chan_doan_so_bo'),
            file_endpoint=f"/api/v1/mobile/patient/lab-results/{cls['chi_tiet_id']}/image" if cls.get('file_ket_qua') else None)
        items.append(item)
    return items


@mobile_patient_bp.get('/lab-results')
@contract
def labs():
    return respond(results=lab_items())


@mobile_patient_bp.get('/lab-results/<int:result_id>/image')
@contract
def lab_image(result_id):
    item = next((i for i in lab_items() if i['id'] == result_id), None)
    if not item or not item.get('file_ket_qua'):
        fail('NOT_FOUND', 'Không tìm thấy ảnh kết quả đã công bố của bạn.', 404)
    from core.medical_media import media_location, serve_medical_image
    location = media_location(item['file_ket_qua'])
    if not location:
        fail('NOT_FOUND', 'Tài liệu không có nguồn được hỗ trợ.', 404)
    store, relative = location
    return serve_medical_image(relative, legacy=store == 'legacy')


@mobile_patient_bp.get('/billing')
@contract
def billing():
    invoices = BillingModel.get_by_patient(patient_id())
    patient = profile_data()
    return respond(invoices=invoices, has_bhyt=bool(patient.get('bhyt')),
        so_the_bhyt=patient.get('bhyt') or '')


@mobile_patient_bp.post('/billing/<int:invoice_id>/instructions')
@contract
def payment_instructions(invoice_id):
    invoice = BillingModel.get_invoice(invoice_id)
    if not invoice or invoice.get('benh_nhan_id') != patient_id():
        fail('NOT_FOUND', 'Không tìm thấy hóa đơn của bạn.', 404)
    payment = result_or_fail(BillingModel.payment_instructions(invoice_id, patient_id=patient_id()))
    return respond(payment=payment, payment_confirmed=False,
        message='Chưa ghi nhận thanh toán. Vui lòng liên hệ quầy thu ngân; chưa tích hợp cổng thanh toán trực tuyến.')


@mobile_patient_bp.get('/feedbacks')
@contract
def feedbacks():
    # Complete history; client renders lazily without a fixed three-item limit.
    return respond(feedbacks=FeedbackModel.get_by_patient(patient_id()))


@mobile_patient_bp.post('/feedbacks')
@contract
def create_feedback():
    data = body()
    encounter = identifier(data.get('phieu_kham_id'), optional=True)
    if encounter and not any(r['id'] == encounter for r in PatientModel.get_patient_history(patient_id(), approved_only=True)):
        fail('NOT_FOUND', 'Không tìm thấy phiếu khám của bạn.', 404)
    score = data.get('diem_danh_gia', 5)
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
        fail('VALIDATION_ERROR', 'Đánh giá phải từ 1 đến 5 sao.', 400)
    topic, content = data.get('chu_de', ''), data.get('noi_dung', '')
    if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 200 or not isinstance(content, str) or not 5 <= len(content.strip()) <= 4000:
        fail('VALIDATION_ERROR', 'Chủ đề tối đa 200 ký tự; nội dung từ 5 đến 4000 ký tự.', 400)
    return respond(message=result_or_fail(FeedbackModel.create(patient_id(), encounter, topic, score, content), status=400)), 201


@mobile_patient_bp.get('/notifications')
@contract
def notifications():
    items = NotificationModel.get_user_notifications(g.mobile_patient['id'], limit=None,
        loai=request.args.get('tab', 'all'), unread_only=request.args.get('unread') == '1')
    for item in items:
        item.update(loai=item.get('loai_thong_bao'), da_xem=bool(item.get('da_doc')),
            thoi_gian=item.get('thoi_gian_tao'))
    return respond(notifications=items, unread_count=NotificationModel.get_unread_count(g.mobile_patient['id']))


@mobile_patient_bp.post('/notifications/read')
@contract
def read_notifications():
    data = body()
    notification_id = data.get('notification_id', data.get('id'))
    if notification_id is None:
        result = NotificationModel.mark_all_as_read(g.mobile_patient['id'])
    else:
        notification_id = identifier(notification_id)
        # Check before mutation to avoid falsely reporting success for another account's ID.
        if not any(n['id'] == notification_id for n in NotificationModel.get_user_notifications(g.mobile_patient['id'], limit=None)):
            fail('NOT_FOUND', 'Không tìm thấy thông báo của bạn.', 404)
        result = NotificationModel.mark_as_read(notification_id, g.mobile_patient['id'])
    return respond(message=result_or_fail(result))
