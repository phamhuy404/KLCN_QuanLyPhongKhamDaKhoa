from functools import wraps
from flask import session, redirect, url_for, request, abort, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Mã hóa mật khẩu bằng thuật toán scrypt an toàn."""
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    """Kiểm tra mật khẩu nhập vào so với mật khẩu lưu trong CSDL."""
    try:
        return check_password_hash(stored_hash, password)
    except Exception:
        return stored_hash == password


STAFF_ROLES = frozenset({'ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV'})


def positive_id(value):
    if isinstance(value, bool):
        return None
    try:
        parsed = int(str(value))
        return parsed if parsed > 0 else None
    except (ValueError, TypeError):
        return None


def deny(status=403, message='Bạn không có quyền truy cập hồ sơ này!'):
    if request.path.startswith('/api/'):
        response = jsonify(success=False, message=message)
        response.status_code = status
        abort(response)
    abort(status)


def refresh_session_user():
    """Read current database identity once per request."""
    if hasattr(g, 'authenticated_user'):
        return g.authenticated_user
    user = session.get('user')
    account_id = positive_id(user.get('id')) if isinstance(user, dict) else None
    identity = None
    if session.get('logged_in') and account_id:
        from models.user_model import UserModel
        identity = UserModel.get_session_user(account_id)
    g.authenticated_user = identity
    if identity is None:
        session.clear()
    else:
        session['user'] = identity
        session['force_change_password'] = bool(identity.get('yeu_cau_doi_mat_khau'))
    return identity


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if refresh_session_user() is None:
            if request.path.startswith('/api/'):
                deny(401, 'Tài khoản không tồn tại, bị khóa hoặc thiếu hồ sơ phù hợp!')
            return redirect(url_for('auth.login', next=request.path))
        if session.get('force_change_password') and request.endpoint not in (
                'auth.force_change_password', 'auth.logout'):
            if request.path.startswith('/api/'):
                deny(403, 'Bắt buộc đổi mật khẩu mới!')
            return redirect(url_for('auth.force_change_password'))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session['user']['vai_tro'] not in allowed_roles:
                deny()
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def current_patient_id():
    user = refresh_session_user()
    if not user or user.get('vai_tro') != 'BENHNHAN':
        deny()
    patient_id = positive_id(user.get('patient_id'))
    if patient_id is None:
        deny()
    return patient_id


def require_own_patient(target=None):
    patient_id = current_patient_id()
    if target is not None and positive_id(target) != patient_id:
        deny()
    return patient_id


def patient_scope_ids():
    """Shared list/detail policy; doctors follow the existing department list scope."""
    user = refresh_session_user()
    if not user:
        deny(401)
    if user['vai_tro'] == 'BENHNHAN':
        return {current_patient_id()}
    if user['vai_tro'] not in STAFF_ROLES:
        deny()
    if user['vai_tro'] != 'BACSI':
        # Preserve existing staff read scope pending business clarification.
        return None
    if not hasattr(g, 'patient_scope_ids'):
        from models.patient_model import PatientModel
        department_id = positive_id(user.get('chuyen_khoa_id'))
        rows = PatientModel.get_by_department(department_id) if department_id else []
        g.patient_scope_ids = {positive_id(row.get('id')) for row in rows}
    return g.patient_scope_ids


def require_patient_access(target):
    patient_id = positive_id(target)
    if patient_id is None:
        deny(400, 'Mã bệnh nhân không hợp lệ!')
    scope = patient_scope_ids()
    if scope is not None and patient_id not in scope:
        deny()
    from core.database import get_db
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM benh_nhan WHERE id = ?', (patient_id,))
        if not cursor.fetchone():
            deny(404, 'Không tìm thấy hồ sơ bệnh nhân!')
    finally:
        conn.close()
    return patient_id


def filter_patient_records(rows, key='benh_nhan_id'):
    scope = patient_scope_ids()
    return rows if scope is None else [r for r in rows if positive_id(r.get(key)) in scope]


def visible_patients(include_history=False):
    from models.patient_model import PatientModel
    user = refresh_session_user()
    if not user:
        deny(401)
    scope = patient_scope_ids()
    if user['vai_tro'] == 'BACSI':
        department_id = positive_id(user.get('chuyen_khoa_id'))
        return PatientModel.get_by_department(department_id, include_history=include_history) if department_id else []
    if scope is None:
        return PatientModel.get_all(include_history=include_history)
    patient = PatientModel.get_by_id(current_patient_id())
    return [patient] if patient else []


def safe_next_url(value):
    """Accept only local absolute paths, including after percent decoding."""
    from urllib.parse import urlsplit, unquote
    if not isinstance(value, str) or not value:
        return None
    decoded = value
    for _ in range(10):
        if any(ord(c) < 32 or ord(c) == 127 for c in decoded) or chr(92) in decoded:
            return None
        try:
            parts = urlsplit(decoded)
        except ValueError:
            return None
        if parts.scheme or parts.netloc or not decoded.startswith('/') or decoded.startswith('//'):
            return None
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            return value
        decoded = next_decoded
    return None
