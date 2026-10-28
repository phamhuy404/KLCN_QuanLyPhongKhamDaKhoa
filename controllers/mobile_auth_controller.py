"""Patient-only mobile contract; independent of Flask web cookie sessions."""
import json
from datetime import date
from flask import Blueprint, request, jsonify
from core.database import get_db
from core.security import verify_password
from core.validators import validate_name, VN_PHONE_PATTERN, EMAIL_PATTERN
from core.mobile_auth import contract, mutation, fail, issue, verify, bearer, public_user
from models.user_model import UserModel

mobile_auth_bp = Blueprint('mobile_auth', __name__, url_prefix='/api/v1/mobile/auth')


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        fail('VALIDATION_ERROR', 'Cần JSON object hợp lệ.', 400)
    return data


def text(data, key, maximum, required=True, trim=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        fail('VALIDATION_ERROR', 'Trường '+key+' không hợp lệ.', 400)
    return value.strip() if trim else value


@mobile_auth_bp.post('/login')
@contract
def login():
    data = body()
    identifier, password = text(data, 'identifier', 254), text(data, 'password', 128, trim=False)
    def operation():
        cursor = get_db().cursor()
        cursor.execute('''SELECT DISTINCT t.id, t.password FROM tai_khoan t
            LEFT JOIN benh_nhan bn ON bn.tai_khoan_id=t.id
            LEFT JOIN nhan_vien nv ON nv.tai_khoan_id=t.id
            WHERE t.username=? OR t.sdt=? OR t.email=? OR bn.sdt=? OR bn.email=? OR nv.sdt=? OR nv.email=?''', (identifier,)*7)
        accounts = cursor.fetchall()
        if len(accounts) != 1 or not verify_password(accounts[0]['password'], password):
            fail('INVALID_CREDENTIALS', 'Thông tin đăng nhập không chính xác.')
        return issue(cursor, accounts[0]['id'])
    return jsonify(mutation(operation))


@mobile_auth_bp.post('/register')
@contract
def register():
    data = body()
    name, phone = text(data, 'ho_ten', 100), text(data, 'sdt', 10)
    email, password = text(data, 'email', 254, required=False).lower(), text(data, 'password', 128, trim=False)
    birth, gender = text(data, 'ngay_sinh', 10), text(data, 'gioi_tinh', 10)
    valid, normalized = validate_name(name)
    if not valid or not VN_PHONE_PATTERN.fullmatch(phone) or (email and not EMAIL_PATTERN.fullmatch(email)):
        fail('VALIDATION_ERROR', 'Họ tên, số điện thoại hoặc email không hợp lệ.', 400)
    if len(password) < 6 or password != password.strip() or gender not in {'Nam','Nữ','Khác'}:
        fail('VALIDATION_ERROR', 'Mật khẩu tối thiểu 6 ký tự, không có khoảng trắng đầu/cuối; giới tính không hợp lệ.', 400)
    try:
        birthday = date.fromisoformat(birth)
        if birthday.isoformat() != birth or birthday > date.today() or birthday.year < 1900:
            raise ValueError()
    except ValueError:
        fail('VALIDATION_ERROR', 'Ngày sinh phải là YYYY-MM-DD hợp lệ, không ở tương lai.', 400)
    def operation():
        cursor = get_db().cursor()
        cursor.execute('''SELECT id FROM tai_khoan WHERE username=? OR sdt=? OR (? != '' AND LOWER(email)=?)
            UNION ALL SELECT id FROM benh_nhan WHERE sdt=? OR (? != '' AND LOWER(email)=?)''',
            (phone,phone,email,email,phone,email,email))
        if cursor.fetchone():
            fail('ACCOUNT_EXISTS', 'Số điện thoại hoặc email đã tồn tại. Vui lòng đăng nhập hoặc liên hệ phòng khám.', 409)
        success, _ = UserModel.register_patient(normalized, phone, password, email or None,
                                              ngay_sinh=birth, gioi_tinh=gender)
        if not success:
            fail('REGISTRATION_FAILED', 'Không thể tạo tài khoản/hồ sơ bệnh nhân.', 503)
        cursor.execute('SELECT id FROM tai_khoan WHERE username=?', (phone,))
        accounts = cursor.fetchall()
        if len(accounts) != 1:
            fail('REGISTRATION_FAILED', 'Không xác định được tài khoản vừa tạo.', 503)
        return issue(cursor, accounts[0]['id'])
    return jsonify(mutation(operation)), 201


@mobile_auth_bp.get('/me')
@contract
def me():
    token = bearer()
    conn = get_db()
    try:
        user, claims, _ = verify(conn.cursor(), token)
        return jsonify(success=True, user=public_user(user), token_type='Bearer', expires_at=claims['exp'])
    finally:
        conn.close()


@mobile_auth_bp.post('/logout')
@contract
def logout():
    token = bearer()
    def operation():
        cursor = get_db().cursor()
        user, claims, revoked = verify(cursor, token, for_logout=True)
        if not revoked:
            cursor.execute('''INSERT INTO audit_log
                (table_name,row_id,action,performed_by,performed_by_name,performed_at,reason,before_json,after_json)
                VALUES (?,?,?,?,?,GETDATE(),?,NULL,?)''',
                ('tai_khoan',user['id'],'MOBILE_LOGOUT',None,None,
                 'Mobile logout',json.dumps({'jti':claims['jti'],'expires_at':claims['exp']})))
        return dict(success=True, message='Đã vô hiệu hóa phiên Mobile.')
    return jsonify(mutation(operation))
