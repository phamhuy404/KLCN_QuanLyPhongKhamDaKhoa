from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import UserModel
from core.security import login_required, refresh_session_user, safe_next_url
from core.validators import VIETNAMESE_NAME_PATTERN, VN_PHONE_PATTERN, FORBIDDEN_CHARS_PATTERN, sanitize_text

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Xử lý đăng nhập tự động nhận diện vai trò người dùng và trạng thái hồ sơ."""
    if refresh_session_user():
        user = session['user']
        if user.get('vai_tro') == 'BACSI' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('admin.doctor_complete_profile'))
        if user.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        if user.get('vai_tro') == 'BENHNHAN' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('patient.complete_profile'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        username = sanitize_text(request.form.get('username', ''))
        password = request.form.get('password', '').strip()

        user = UserModel.authenticate(username, password)
        if not user:
            return render_template('auth/login.html', error='Tên đăng nhập hoặc mật khẩu không chính xác!')

        session.clear()
        session['logged_in'] = True
        session['user'] = user

        # Nếu tài khoản vừa được cấp lại mật khẩu mặc định 123 thì bắt buộc đổi mật khẩu mới
        if user.get('yeu_cau_doi_mat_khau') in (1, True, '1'):
            session['force_change_password'] = True
            return redirect(url_for('auth.force_change_password'))

        # Nếu là Bác sĩ mới tạo và chưa hoàn thiện hồ sơ lần đầu
        if user['vai_tro'] == 'BACSI' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('admin.doctor_complete_profile'))

        # Nếu là Bệnh nhân và chưa hoàn thiện hồ sơ lần đầu
        if user['vai_tro'] == 'BENHNHAN' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('patient.complete_profile'))

        next_url = safe_next_url(request.args.get('next'))
        if next_url:
            if next_url.startswith('/admin') and user['vai_tro'] == 'BENHNHAN':
                return redirect(url_for('patient.dashboard'))
            return redirect(next_url)

        # Điều hướng theo vai trò người dùng
        if user['vai_tro'] in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản bệnh nhân mới trực tuyến với kiểm tra ràng buộc an toàn."""
    if refresh_session_user():
        user = session['user']
        if user.get('vai_tro') == 'BACSI' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('admin.doctor_complete_profile'))
        if user.get('vai_tro') == 'BENHNHAN' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('patient.complete_profile'))
        if user.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        ho_ten = sanitize_text(request.form.get('ho_ten', ''))
        sdt = sanitize_text(request.form.get('sdt', ''))
        email = sanitize_text(request.form.get('email', ''))
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Kiểm tra ký tự lạ cấm
        if FORBIDDEN_CHARS_PATTERN.search(ho_ten) or FORBIDDEN_CHARS_PATTERN.search(sdt):
            return render_template('auth/register.html', error='Dữ liệu nhập vào chứa ký tự đặc biệt không an toàn!', form=request.form)

        # Ràng buộc họ tên
        if not ho_ten or len(ho_ten) < 2 or len(ho_ten) > 100:
            return render_template('auth/register.html', error='Họ và tên phải có độ dài từ 2 đến 100 ký tự!', form=request.form)
        if not VIETNAMESE_NAME_PATTERN.match(ho_ten):
            return render_template('auth/register.html', error='Họ và tên chỉ được chứa chữ cái tiếng Việt và khoảng trắng, không chứa số hay ký tự lạ!', form=request.form)

        # Ràng buộc số điện thoại
        if not sdt or not VN_PHONE_PATTERN.match(sdt):
            return render_template('auth/register.html', error='Số điện thoại không đúng định dạng (10 số, bắt đầu 03, 05, 07, 08, 09)!', form=request.form)

        # Ràng buộc mật khẩu
        if not password or len(password) < 6:
            return render_template('auth/register.html', error='Mật khẩu phải có độ dài tối thiểu 6 ký tự!', form=request.form)
        if password != confirm_password:
            return render_template('auth/register.html', error='Mật khẩu xác nhận không khớp, vui lòng nhập lại!', form=request.form)

        success, msg = UserModel.register_patient(ho_ten, sdt, password, email if email else None)
        if not success:
            return render_template('auth/register.html', error=msg, form=request.form)

        return render_template('auth/login.html', success='Đăng ký tài khoản thành công! Vui lòng đăng nhập để hoàn thiện hồ sơ y tế cá nhân.')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Đăng xuất và xóa phiên làm việc."""
    session.clear()
    return redirect(url_for('home.home'))


@auth_bp.route('/force-change-password', methods=['GET', 'POST'])
@login_required
def force_change_password():
    """Bắt buộc người dùng nhập và lưu mật khẩu mới sau khi được cấp lại mật khẩu 123."""
    if not session.get('logged_in') or not session.get('user'):
        return redirect(url_for('auth.login'))

    user = session.get('user', {})
    if not user.get('yeu_cau_doi_mat_khau'):
        if user.get('vai_tro') == 'BACSI' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('admin.doctor_complete_profile'))
        if user.get('vai_tro') == 'BENHNHAN' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('patient.complete_profile'))
        if user.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        new_pw = request.form.get('new_password', '').strip()
        confirm_pw = request.form.get('confirm_password', '').strip()

        if not new_pw or len(new_pw) < 6:
            return render_template('auth/force_change_password.html', error='Mật khẩu mới phải có tối thiểu 6 ký tự!', user=user)

        if new_pw == '123':
            return render_template('auth/force_change_password.html', error='Vui lòng đặt mật khẩu mới khác với mật khẩu tạm thời (123) để đảm bảo an toàn!', user=user)

        if new_pw != confirm_pw:
            return render_template('auth/force_change_password.html', error='Mật khẩu xác nhận không trùng khớp!', user=user)

        from core.security import hash_password
        from core.database import get_db
        from core.audit import AuditLogger

        conn = get_db()
        cursor = conn.cursor()
        hashed = hash_password(new_pw)
        cursor.execute('UPDATE tai_khoan SET password = ?, yeu_cau_doi_mat_khau = 0 WHERE id = ?', (hashed, user['id']))
        conn.commit()
        conn.close()

        AuditLogger.log(
            table_name='tai_khoan',
            row_id=user['id'],
            action='FORCE_CHANGE_PASSWORD',
            performed_by=user['id'],
            performed_by_name=user.get('ho_ten') or user.get('username'),
            reason='Người dùng hoàn tất đổi mật khẩu lần đầu sau khi được cấp lại mật khẩu'
        )

        user['yeu_cau_doi_mat_khau'] = 0
        session['user'] = user
        session.pop('force_change_password', None)
        flash('Đổi mật khẩu thành công! Tài khoản của bạn đã được kích hoạt an toàn.', 'success')

        if user.get('vai_tro') == 'BACSI' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('admin.doctor_complete_profile'))
        if user.get('vai_tro') == 'BENHNHAN' and not user.get('da_hoan_thien_ho_so'):
            return redirect(url_for('patient.complete_profile'))
        if user.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/force_change_password.html', user=user)
