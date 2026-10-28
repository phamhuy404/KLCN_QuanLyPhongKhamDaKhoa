"""Explicit encounter identity. No patient-only or historical matching."""
import base64
from contextvars import ContextVar
from datetime import date
from functools import wraps
from uuid import UUID

from core.scheduling import CalendarError, integer


OPEN_RECORDS = ('Đang khám', 'Đang kê đơn', 'Chờ kết quả CLS', 'Chờ kết luận')
OPEN_APPOINTMENTS = ('Đã tiếp nhận', 'Đang khám', 'Chờ kết quả CLS', 'Chờ kết luận', 'Đang kê đơn')
_new_images = ContextVar('emr_new_images', default=None)


def track_new_image(path):
    images = _new_images.get()
    if images is not None:
        images.append(path)


def atomic_emr_request(function):
    """Commit after building the response; clean only files created by this request."""
    @wraps(function)
    def run(*args, **kwargs):
        from flask import current_app, jsonify, make_response
        from werkzeug.exceptions import HTTPException
        from core.scheduling import serialized
        created = []
        token = _new_images.set(created)
        @serialized
        def operation():
            try:
                from flask import request
                if request.is_json:
                    data = request.get_json() or {}
                    for aliases in (('appointment_id', 'lich_hen_id'), ('patient_id', 'benh_nhan_id'),
                                    ('doctor_id', 'bac_si_id'), ('room_id', 'phong_kham_id')):
                        values = [str(data[key]) for key in aliases if data.get(key) is not None]
                        if len(set(values)) > 1:
                            raise CalendarError('Các định danh trong yêu cầu không khớp nhau.')
                    for key in ('medicines', 'don_thuoc', 'lab_services', 'dich_vu_chi_dinh', 'images'):
                        if data.get(key) is not None and not isinstance(data[key], list):
                            raise CalendarError('Thuốc, dịch vụ và ảnh phải là danh sách hợp lệ.')
                response = make_response(function(*args, **kwargs))
            except HTTPException as exc:
                response = exc.get_response()
            return response.status_code < 400, response
        try:
            ok, response = operation()
            if not ok:
                for path in created:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        current_app.logger.exception('Unable to clean new EMR image after rollback')
            if hasattr(response, 'status_code'):
                return response
            return jsonify(success=False, message=response), 400
        finally:
            _new_images.reset(token)
    return run


def resolve(cursor, patient_id, doctor_id=None, room_id=None, appointment_id=None,
            record_id=None, walk_in=False, encounter_key=None, audit_user=None):
    patient_id = integer(patient_id)
    if appointment_id and walk_in:
        raise CalendarError('Không được đồng thời chọn lịch hẹn và khám trực tiếp mới.')
    for value in (doctor_id, room_id, appointment_id):
        if value is not None and integer(value) <= 0:
            raise CalendarError('Định danh bác sĩ, phòng hoặc lịch hẹn không hợp lệ.')
    cursor.execute('SELECT id FROM benh_nhan WHERE id = ?', (patient_id,))
    if not cursor.fetchone():
        raise CalendarError('Không có hồ sơ bệnh nhân.')
    record = None
    if record_id:
        cursor.execute('SELECT * FROM phieu_kham WHERE id = ? OR ma_phieu = ?',
                       (int(str(record_id)) if str(record_id).isdigit() else -1, str(record_id)))
        record = cursor.fetchone()
        if not record or record['benh_nhan_id'] != patient_id:
            raise CalendarError('Phiếu khám không thuộc bệnh nhân.')
        if appointment_id and str(record.get('lich_hen_id')) != str(appointment_id):
            raise CalendarError('Không được ghép hoặc đổi liên kết lịch hẹn của phiếu khám.')
        appointment_id = record.get('lich_hen_id')
        if doctor_id and str(doctor_id) != str(record['bac_si_id']):
            raise CalendarError('Không được đổi bác sĩ của phiếu khám.')
        if room_id and str(room_id) != str(record['phong_kham_id']):
            raise CalendarError('Không được đổi phòng của phiếu khám.')
        doctor_id, room_id = record['bac_si_id'], record['phong_kham_id']
    appointment = None
    if appointment_id:
        cursor.execute('SELECT * FROM lich_hen WHERE id = ?', (integer(appointment_id),))
        appointment = cursor.fetchone()
        if not appointment or appointment['benh_nhan_id'] != patient_id:
            raise CalendarError('Lịch hẹn không thuộc bệnh nhân.')
        if appointment['trang_thai'] not in OPEN_APPOINTMENTS:
            raise CalendarError('Lịch hẹn chưa tiếp nhận hoặc đã kết thúc/hủy.')
        if str(appointment['ngay_hen'])[:10] > date.today().isoformat():
            raise CalendarError('Chưa đến ngày khám của lịch hẹn.')
        if doctor_id and str(doctor_id) != str(appointment['bac_si_id']):
            raise CalendarError('Bác sĩ không khớp lịch hẹn.')
        if room_id and str(room_id) != str(appointment['phong_kham_id']):
            raise CalendarError('Phòng khám không khớp lịch hẹn.')
        doctor_id, room_id = appointment['bac_si_id'], appointment['phong_kham_id']
        cursor.execute('SELECT * FROM phieu_kham WHERE lich_hen_id = ?', (appointment['id'],))
        linked = cursor.fetchall()
        if len(linked) > 1 or (record and linked and record['id'] != linked[0]['id']):
            raise CalendarError('Liên kết lịch hẹn không duy nhất; cần kiểm tra dữ liệu.')
        if not record and linked:
            record = linked[0]
    code = None
    if not appointment and not record:
        if walk_in is not True:
            raise CalendarError('Phải chọn lịch hẹn hoặc xác nhận khám trực tiếp.')
        try:
            token = UUID(str(encounter_key))
        except (ValueError, TypeError, AttributeError):
            raise CalendarError('Khám trực tiếp cần encounter_key UUID riêng cho lần khám.')
        code = 'PKW' + base64.urlsafe_b64encode(token.bytes).decode('ascii').rstrip('=')
        cursor.execute('SELECT * FROM phieu_kham WHERE ma_phieu = ?', (code,))
        record = cursor.fetchone()
        if record and (record['benh_nhan_id'] != patient_id or str(record['bac_si_id']) != str(doctor_id)
                       or str(record['phong_kham_id']) != str(room_id) or record.get('lich_hen_id') is not None):
            raise CalendarError('Định danh lần khám đã thuộc hồ sơ khác.')
    if record:
        if record['trang_thai'] not in OPEN_RECORDS:
            raise CalendarError('Phiếu khám đã kết thúc; không được lưu/hoàn tất lại.')
        if record['benh_nhan_id'] != patient_id or str(record['bac_si_id']) != str(doctor_id):
            raise CalendarError('Bác sĩ hoặc bệnh nhân không khớp phiếu khám.')
    if not audit_user or not audit_user.get('id'):
        raise CalendarError('Thiếu tài khoản thực hiện khám.')
    cursor.execute('''SELECT tk.id, v.ma_vai_tro FROM tai_khoan tk
                      JOIN vai_tro v ON v.id = tk.vai_tro_id WHERE tk.id = ? AND tk.trang_thai = 1''', (audit_user['id'],))
    actor = cursor.fetchone()
    if not actor or actor['ma_vai_tro'] not in ('ADMIN', 'BACSI'):
        raise CalendarError('Tài khoản không có quyền khám bệnh.')
    cursor.execute('''SELECT bs.*, nv.tai_khoan_id, nv.trang_thai AS staff_active, tk.trang_thai AS account_active
                      FROM bac_si bs JOIN nhan_vien nv ON nv.id = bs.nhan_vien_id
                      JOIN tai_khoan tk ON tk.id = nv.tai_khoan_id WHERE bs.id = ?''', (doctor_id,))
    doctor = cursor.fetchone()
    if not doctor or doctor['staff_active'] != 1 or doctor['account_active'] != 1 or doctor['trang_thai_lam_viec'] != 'Đang làm việc':
        raise CalendarError('Bác sĩ không tồn tại hoặc không hoạt động.')
    if actor['ma_vai_tro'] == 'BACSI' and doctor['tai_khoan_id'] != actor['id']:
        raise CalendarError('Bác sĩ chỉ được ghi phiếu khám do mình phụ trách.')
    cursor.execute('SELECT trang_thai FROM chuyen_khoa WHERE id=?', (doctor['chuyen_khoa_id'],))
    department = cursor.fetchone()
    if not department or department['trang_thai'] != 1:
        raise CalendarError('Chuyên khoa không hoạt động.')
    cursor.execute('SELECT chuyen_khoa_id, trang_thai FROM phong_kham WHERE id = ?', (room_id,))
    room = cursor.fetchone()
    if not room or room['trang_thai'] != 1 or room['chuyen_khoa_id'] != doctor['chuyen_khoa_id']:
        raise CalendarError('Phòng không hoạt động hoặc không thuộc chuyên khoa bác sĩ.')
    if appointment and appointment['chuyen_khoa_id'] != doctor['chuyen_khoa_id']:
        raise CalendarError('Chuyên khoa lịch hẹn không khớp bác sĩ.')
    return record, appointment, patient_id, doctor['id'], integer(room_id), code


def ensure_results_ready(cursor, record_id):
    cursor.execute('''SELECT ct.trang_thai, ct.ket_qua, ct.file_ket_qua FROM chi_tiet_chi_dinh ct
                      JOIN phieu_chi_dinh cd ON cd.id = ct.phieu_chi_dinh_id WHERE cd.phieu_kham_id = ?''', (record_id,))
    for result in cursor.fetchall():
        if result['trang_thai'] != 'Đã duyệt' or not (str(result.get('ket_qua') or '').strip() or str(result.get('file_ket_qua') or '').strip()):
            raise CalendarError('Còn kết quả CLS chưa có dữ liệu hoặc chưa được duyệt.')


def validated_medicines(cursor, medicines):
    if not isinstance(medicines, list):
        raise CalendarError('Danh sách thuốc không hợp lệ.')
    checked, seen = [], set()
    for medicine in medicines:
        drug, quantity = integer(medicine.get('thuoc_id')), integer(medicine.get('so_luong'))
        if quantity <= 0 or drug in seen:
            raise CalendarError('Thuốc trùng hoặc số lượng không hợp lệ.')
        seen.add(drug)
        cursor.execute('SELECT id,ten_thuoc,so_luong_ton,don_vi_tinh,don_gia FROM thuoc WHERE id = ?', (drug,))
        row = cursor.fetchone()
        if not row or quantity > (row['so_luong_ton'] or 0):
            raise CalendarError('Thuốc không tồn tại hoặc không đủ tồn kho.')
        checked.append(dict(medicine,thuoc_id=drug,so_luong=quantity,ten_thuoc=row['ten_thuoc'],
                            don_gia=row['don_gia'],don_vi_tinh=row['don_vi_tinh'],
                            lieu_dung=medicine.get('lieu_dung') or '',cach_dung=medicine.get('cach_dung') or ''))
    return checked
