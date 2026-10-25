from functools import wraps
from flask import session, redirect, url_for, request, abort, jsonify
import secrets
import hmac
from urllib.parse import urlparse, urljoin
<<<<<<< Updated upstream
from werkzeug.security import generate_password_hash, check_password_hash

def generate_csrf_token():
    """Tạo hoặc lấy CSRF token an toàn ngẫu nhiên được lưu trữ trong session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf_token(token):
    """Xác thực CSRF token gửi lên bằng thuật toán so sánh chuỗi hmac chống tấn công timing."""
    session_token = session.get('_csrf_token')
    if not session_token or not token:
        return False
    return hmac.compare_digest(str(session_token), str(token))

def is_safe_redirect_url(target):
    """Kiểm tra URL chuyển hướng có phải là đường dẫn nội bộ an toàn (chống Open Redirect)."""
    if not target or not isinstance(target, str):
        return False
    target = target.strip()
    # Ngăn chặn schema-relative (//attacker.com) hoặc backslash (\attacker.com)
    if target.startswith('//') or '\\' in target:
        return False
    # Phải bắt đầu bằng dấu gạch chéo nội bộ
    if not target.startswith('/'):
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
=======
from flask import current_app, g, session, redirect, url_for, request, abort, jsonify
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

MOBILE_ACCESS_TOKEN_MAX_AGE = 3600
MOBILE_ACCESS_TOKEN_SALT = 'h2t-mobile-access-token-v1'
>>>>>>> Stashed changes

def hash_password(password):
    """Mã hóa mật khẩu bằng thuật toán scrypt an toàn."""
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    """Kiểm tra mật khẩu nhập vào so với mật khẩu lưu trong CSDL."""
    try:
        return check_password_hash(stored_hash, password)
    except Exception:
        return stored_hash == password

<<<<<<< Updated upstream
=======
def generate_csrf_token():
    """Sinh hoặc lấy CSRF token lưu trong session hiện tại."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf_token(token):
    """Xác thực CSRF token gửi lên với token trong session."""
    session_token = session.get('_csrf_token')
    if not token or not session_token:
        return False
    return hmac.compare_digest(str(session_token), str(token))


def generate_mobile_access_token(account_id):
    serializer = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt=MOBILE_ACCESS_TOKEN_SALT
    )
    return serializer.dumps({'sub': str(account_id)})


def mobile_patient_required(f):
    """Authenticate Mobile bearer tokens and require an active patient account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization = request.headers.get('Authorization', '')
        scheme, separator, token = authorization.partition(' ')
        if not separator or scheme.lower() != 'bearer' or not token.strip():
            return jsonify({'success': False, 'message': 'Yêu cầu token xác thực!'}), 401

        serializer = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt=MOBILE_ACCESS_TOKEN_SALT
        )
        try:
            payload = serializer.loads(
                token.strip(),
                max_age=MOBILE_ACCESS_TOKEN_MAX_AGE
            )
        except (BadSignature, SignatureExpired):
            return jsonify({'success': False, 'message': 'Token không hợp lệ hoặc đã hết hạn!'}), 401

        account_id = payload.get('sub') if isinstance(payload, dict) else None
        if not account_id or not str(account_id).isdigit():
            return jsonify({'success': False, 'message': 'Token không hợp lệ!'}), 401

        from models.user_model import UserModel
        identity = UserModel.get_mobile_identity(int(account_id))
        if not identity:
            return jsonify({'success': False, 'message': 'Tài khoản không hoạt động hoặc không tồn tại!'}), 401
        if identity.get('vai_tro') != 'BENHNHAN' or not identity.get('patient_id'):
            return jsonify({'success': False, 'message': 'Chỉ tài khoản bệnh nhân được sử dụng Mobile App!'}), 403

        g.mobile_user = identity
        return f(*args, **kwargs)
    return decorated_function

def is_safe_redirect_url(target):
    """Kiểm tra URL chuyển hướng có an toàn (nội bộ hệ thống) hay không."""
    if not target or not isinstance(target, str):
        return False
    target = target.strip()
    if not target:
        return False
    # Chặn URL bắt đầu bằng giao thức nguy hiểm
    if target.startswith(('javascript:', 'data:', 'vbscript:')):
        return False
    # Chặn URL scheme-relative // hoặc bypass bằng dấu gạch chéo ngược \
    if target.startswith('//') or target.startswith(r'\/') or target.startswith('\\'):
        return False

    try:
        host = request.host_url if request else 'http://localhost/'
        ref_url = urlparse(host)
        test_url = urlparse(urljoin(host, target))
        if test_url.scheme not in ('http', 'https'):
            return False
        if ref_url and test_url.netloc != ref_url.netloc:
            return False
    except Exception:
        return False

    return target.startswith('/')

>>>>>>> Stashed changes
def login_required(f):
    """Decorator kiểm tra người dùng đã đăng nhập chưa và tài khoản có đang hoạt động hay không."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('user'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập để tiếp tục!'}), 401
            return redirect(url_for('auth.login', next=request.path))
        
        user_id = session.get('user', {}).get('id')
        if user_id:
            from models.user_model import UserModel
            if not UserModel.check_account_active(user_id):
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Tài khoản của bạn đã bị vô hiệu hóa!'}), 401
                return redirect(url_for('auth.login', error='Tài khoản của bạn đã bị vô hiệu hóa!'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    """Decorator kiểm tra vai trò người dùng (RBAC) và trạng thái tài khoản hoạt động."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in') or not session.get('user'):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Yêu cầu đăng nhập!'}), 401
                return redirect(url_for('auth.login', next=request.path))

            user_id = session.get('user', {}).get('id')
            if user_id:
                from models.user_model import UserModel
                if not UserModel.check_account_active(user_id):
                    session.clear()
                    if request.path.startswith('/api/'):
                        return jsonify({'success': False, 'message': 'Tài khoản của bạn đã bị vô hiệu hóa!'}), 401
                    return redirect(url_for('auth.login', error='Tài khoản của bạn đã bị vô hiệu hóa!'))
            
            user_role = session.get('user', {}).get('vai_tro')
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này!'}), 403
                # Nếu là bệnh nhân cố vào trang quản trị, đưa về dashboard bệnh nhân
                if user_role == 'BENHNHAN':
                    return redirect(url_for('patient.dashboard'))
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

