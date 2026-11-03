import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'app.py')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Thêm alias
alias_target = "'doctor_create': 'admin.create_doctor',"
alias_replacement = """'doctor_create': 'admin.create_doctor',
        'maintenance_patient': 'home.maintenance_patient',
        'maintenance_staff': 'home.maintenance_staff',"""

if alias_target in content:
    content = content.replace(alias_target, alias_replacement)

# 2. Thêm maintenance_guard
guard_target = """    @app.before_request
    def redirect_guest_billing():
        if request.path in ('/billing', '/patient/billing') and not session.get('logged_in'):
            return redirect(flask_url_for('home.pricing'))"""

guard_replacement = """    @app.before_request
    def redirect_guest_billing():
        if request.path in ('/billing', '/patient/billing') and not session.get('logged_in'):
            return redirect(flask_url_for('home.pricing'))

    @app.before_request
    def maintenance_guard():
        # Bỏ qua tài nguyên tĩnh, favicon và các route bảo trì/đăng xuất
        if request.path.startswith('/static') or request.path == '/favicon.ico':
            return None

        # Ngoại lệ bắt buộc để không bị lặp điều hướng
        whitelist_paths = (
            '/maintenance/patient',
            '/maintenance/staff',
            '/auth/logout',
            '/logout',
            '/api/maintenance/status'
        )
        if request.path in whitelist_paths:
            return None

        user = session.get('user') or {}
        role = user.get('vai_tro')

        # Quản trị viên (ADMIN) luôn được phép toàn quyền truy cập để quản trị và nâng cấp
        if role == 'ADMIN':
            return None

        # Cho phép truy cập trang đăng nhập khi chưa đăng nhập (để Admin có thể đăng nhập)
        if request.path in ('/login', '/auth/login') and not session.get('logged_in'):
            return None

        from models.system_setting_model import SystemSettingModel
        settings = SystemSettingModel.get_settings()

        # Kiểm tra chế độ bảo trì Cổng Bệnh nhân
        if settings.get('maintenance_patient'):
            is_patient_area = (
                role == 'BENHNHAN' or
                request.path.startswith('/patient') or
                request.path.startswith('/booking') or
                request.path in ('/register', '/auth/register') or
                request.path.startswith('/api/patient')
            )
            if is_patient_area:
                if request.is_json or request.path.startswith('/api/'):
                    from flask import jsonify
                    return jsonify({
                        'success': False,
                        'maintenance': True,
                        'message': settings.get('maintenance_message_patient', 'Hệ thống Cổng Bệnh nhân đang bảo trì nâng cấp.')
                    }), 503
                return redirect('/maintenance/patient')

        # Kiểm tra chế độ bảo trì Phân hệ Nhân viên y tế
        if settings.get('maintenance_staff'):
            is_staff_area = (
                role in ('BACSI', 'LETAN', 'DUOCSI', 'KTV') or
                request.path.startswith('/admin') or
                request.path.startswith('/api/emr') or
                request.path.startswith('/api/schedule') or
                request.path.startswith('/api/doctor')
            )
            if is_staff_area:
                if request.is_json or request.path.startswith('/api/'):
                    from flask import jsonify
                    return jsonify({
                        'success': False,
                        'maintenance': True,
                        'message': settings.get('maintenance_message_staff', 'Hệ thống Quản lý Y tế Nội bộ đang bảo trì nâng cấp.')
                    }), 503
                return redirect('/maintenance/staff')

        return None"""

if guard_target in content:
    content = content.replace(guard_target, guard_replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched app.py with maintenance_guard and aliases")
else:
    print("Guard target not found in app.py")
