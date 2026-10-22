from flask import Blueprint, render_template, request, redirect, url_for, session
from models.user_model import UserModel
from core.security import is_safe_redirect_url

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Xử lý đăng nhập tự động nhận diện vai trò người dùng và bảo vệ an toàn chuyển hướng."""
    if session.get('logged_in') and session.get('user'):
        user = session['user']
        if user.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = UserModel.authenticate(username, password)
        if not user:
            return render_template('auth/login.html', error='Tên đăng nhập hoặc mật khẩu không chính xác!')

        session['logged_in'] = True
        session['user'] = user

        # Kiểm tra tham số next: Chỉ cho phép URL nội bộ an toàn (Chống Open Redirect)
        next_url = request.form.get('next') or request.args.get('next')
        if next_url and is_safe_redirect_url(next_url):
            if next_url.startswith('/admin') and user['vai_tro'] == 'BENHNHAN':
                return redirect(url_for('patient.dashboard'))
            return redirect(next_url)

        # Điều hướng mặc định an toàn theo vai trò người dùng
        if user['vai_tro'] in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản bệnh nhân mới trực tuyến."""
    if session.get('logged_in') and session.get('user'):
        user = session['user']
        if user.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))
    if request.method == 'POST':
        ho_ten = request.form.get('ho_ten', '').strip()
        sdt = request.form.get('sdt', '').strip()
        ngay_sinh = request.form.get('ngay_sinh', '').strip()
        gioi_tinh = request.form.get('gioi_tinh', 'Nam').strip()
        cccd = request.form.get('cccd', '').strip()
        email = request.form.get('email', '').strip()
        bhyt = request.form.get('bhyt', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if password != confirm_password:
            return render_template('auth/register.html', error='Mật khẩu xác nhận không khớp, vui lòng nhập lại!')

        success, msg = UserModel.register_patient(ho_ten, sdt, ngay_sinh, gioi_tinh, cccd, email, bhyt, password)
        if not success:
            return render_template('auth/register.html', error=msg)

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Đăng xuất và xóa phiên làm việc an toàn bằng phương thức POST và kiểm tra CSRF."""
    session.clear()
    return redirect(url_for('home.home'))
