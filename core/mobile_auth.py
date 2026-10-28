"""Expiring, signed mobile sessions; live identity and persistent logout checks."""
import hashlib
import hmac
import time
from uuid import uuid4
from functools import wraps
from flask import current_app, request, jsonify
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from core.database import get_db
from core.scheduling import serialized
from core.security import positive_id
from models.user_model import UserModel


class MobileAuthError(Exception):
    def __init__(self, code, message, status=401):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def fail(code, message, status=401):
    raise MobileAuthError(code, message, status)


def signing_key():
    value = current_app.config.get('MOBILE_TOKEN_SECRET') or current_app.secret_key
    value = value.encode() if isinstance(value, str) else value
    if not isinstance(value, bytes) or len(value) < 32:
        raise RuntimeError('Mobile token secret must contain at least 32 bytes')
    return value


def serializer():
    return URLSafeTimedSerializer(signing_key(), salt='clinic.mobile.auth.v1',
                                  signer_kwargs={'digest_method': hashlib.sha256})


def ttl():
    value = current_app.config.get('MOBILE_TOKEN_TTL_SECONDS', 3600)
    if isinstance(value, bool) or not isinstance(value, int) or not 60 <= value <= 86400:
        raise RuntimeError('Invalid mobile token lifetime')
    return value


def stamp(password):
    return hmac.new(signing_key(), ('mobile-password:'+password).encode(), hashlib.sha256).hexdigest()


def live_identity(cursor, account_id):
    user = UserModel.get_session_user(account_id)
    if not user:
        fail('ACCOUNT_UNAVAILABLE', 'Tài khoản bị khóa, đã xóa hoặc thiếu hồ sơ bệnh nhân.')
    if user['vai_tro'] != 'BENHNHAN':
        fail('ROLE_NOT_ALLOWED', 'Chỉ tài khoản bệnh nhân được sử dụng Mobile.', 403)
    if user.get('yeu_cau_doi_mat_khau'):
        fail('PASSWORD_CHANGE_REQUIRED', 'Vui lòng đổi mật khẩu trên Website trước khi dùng Mobile.', 403)
    cursor.execute('SELECT id FROM benh_nhan WHERE tai_khoan_id=?', (account_id,))
    patients = cursor.fetchall()
    if len(patients) != 1 or patients[0]['id'] != user.get('patient_id'):
        fail('ACCOUNT_UNAVAILABLE', 'Liên kết hồ sơ bệnh nhân không hợp lệ.')
    cursor.execute('SELECT password FROM tai_khoan WHERE id=?', (account_id,))
    row = cursor.fetchone()
    if not row or not isinstance(row.get('password'), str):
        fail('ACCOUNT_UNAVAILABLE', 'Tài khoản không còn hợp lệ.')
    return user, row['password']


def public_user(user):
    return dict(account_id=user['id'], patient_id=user['patient_id'], role='BENHNHAN',
                name=user.get('ho_ten') or '', email=user.get('email') or '',
                phone=user.get('sdt') or '', patient_code=user.get('ma_benh_nhan') or '')


def issue(cursor, account_id):
    user, password = live_identity(cursor, account_id)
    now, duration = int(time.time()), ttl()
    claims = dict(sub=user['id'], pid=user['patient_id'], jti=uuid4().hex,
                  stamp=stamp(password), iat=now, exp=now+duration)
    # Fail before issuing a token if durable revocation storage is unavailable.
    revoked(cursor, user['id'], claims['jti'])
    return dict(success=True, user=public_user(user), access_token=serializer().dumps(claims),
                token_type='Bearer', expires_in=duration, expires_at=claims['exp'])


def bearer():
    parts = request.headers.get('Authorization', '').split()
    if len(parts) != 2 or parts[0].lower() != 'bearer' or len(parts[1]) > 4096:
        fail('TOKEN_REQUIRED', 'Cần Bearer token hợp lệ.')
    return parts[1]


def revoked(cursor, account_id, jti):
    cursor.execute("""SELECT TOP (1) id FROM audit_log
        WHERE table_name='tai_khoan' AND row_id=? AND action='MOBILE_LOGOUT'
        AND JSON_VALUE(after_json,'$.jti')=?""", (account_id, jti))
    return cursor.fetchone() is not None


def verify(cursor, token, for_logout=False):
    try:
        claims = serializer().loads(token, max_age=ttl())
    except SignatureExpired:
        fail('TOKEN_EXPIRED', 'Phiên đăng nhập đã hết hạn.')
    except BadSignature:
        fail('TOKEN_INVALID', 'Token không hợp lệ.')
    if not isinstance(claims, dict) or positive_id(claims.get('sub')) is None or positive_id(claims.get('pid')) is None:
        fail('TOKEN_INVALID', 'Token không hợp lệ.')
    now = int(time.time())
    if not isinstance(claims.get('exp'), int) or not isinstance(claims.get('iat'), int) or claims['iat'] > now:
        fail('TOKEN_INVALID', 'Thời hạn token không hợp lệ.')
    if claims['exp'] <= now:
        fail('TOKEN_EXPIRED', 'Phiên đăng nhập đã hết hạn.')
    if not isinstance(claims.get('jti'), str) or len(claims['jti']) != 32:
        fail('TOKEN_INVALID', 'Token không hợp lệ.')
    if for_logout:
        # A signed session may revoke itself even after account lock/deletion.
        # This branch never authorizes a resource or returns patient information.
        user = {'id': claims['sub']}
    else:
        user, password = live_identity(cursor, claims['sub'])
        if user['patient_id'] != claims['pid'] or not hmac.compare_digest(str(claims.get('stamp')), stamp(password)):
            fail('TOKEN_INVALID', 'Phiên đã bị vô hiệu hóa; vui lòng đăng nhập lại.')
    is_revoked = revoked(cursor, user['id'], claims['jti'])
    if is_revoked and not for_logout:
        fail('TOKEN_REVOKED', 'Phiên đã đăng xuất.')
    return user, claims, is_revoked


def contract(function):
    @wraps(function)
    def run(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
            response = current_app.make_response(result)
        except MobileAuthError as exc:
            response = jsonify(success=False, error_code=exc.code, message=exc.message)
            response.status_code = exc.status
        except Exception:
            # No SQL/credentials/token data in responses or exception logs.
            response = jsonify(success=False, error_code='SERVICE_UNAVAILABLE', message='Không thể xác thực lúc này. Vui lòng thử lại.')
            response.status_code = 503
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response
    return run


def mutation(function):
    @serialized
    def operation():
        try:
            return True, function()
        except MobileAuthError as exc:
            return False, exc
    success, result = operation()
    if not success:
        if isinstance(result, MobileAuthError):
            raise result
        fail('SERVICE_UNAVAILABLE', 'Không thể hoàn tất xác thực. Vui lòng thử lại.', 503)
    return result
