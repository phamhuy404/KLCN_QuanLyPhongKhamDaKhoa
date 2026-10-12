from functools import wraps
from flask import session, redirect, url_for, request, abort, jsonify
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

def login_required(f):
    """Decorator kiểm tra người dùng đã đăng nhập chưa."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('user'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập để tiếp tục!'}), 401
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    """Decorator kiểm tra vai trò người dùng (RBAC)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in') or not session.get('user'):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Yêu cầu đăng nhập!'}), 401
                return redirect(url_for('auth.login', next=request.path))
            
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
