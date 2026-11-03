from flask import Flask, session, url_for as flask_url_for, redirect, request
import config
import secrets

from controllers.home_controller import home_bp
from controllers.auth_controller import auth_bp
from controllers.patient_controller import patient_bp
from controllers.admin_controller import admin_bp
from controllers.api_controller import api_bp
from controllers.mobile_auth_controller import mobile_auth_bp
from controllers.mobile_patient_controller import mobile_patient_bp

_DEVELOPMENT_SECRET_KEY = secrets.token_hex(32)

def create_app(test_config=None):
    """Khởi tạo ứng dụng Flask theo mô hình kiến trúc MVC."""
    app = Flask(__name__)
    app.config.from_object(config)
    if test_config is not None:
        app.config.update(test_config)
    if not app.config.get('SECRET_KEY'):
        if not app.debug and not app.testing:
            raise RuntimeError('SECRET_KEY is required outside debug/test mode')
        app.config['SECRET_KEY'] = _DEVELOPMENT_SECRET_KEY
    elif app.config['SECRET_KEY'] == 'h2t_healthcare_clinic_secret_key_2026':
        raise RuntimeError('The former public default SECRET_KEY must be replaced')
    if not app.testing and (not isinstance(app.secret_key, (str, bytes)) or len(app.secret_key) < 32):
        raise RuntimeError('SECRET_KEY must contain at least 32 characters')
    # Testing must never fall back to the configured production connection.
    if app.testing:
        app.config['DATABASE_ACCESS_ENABLED'] = False
        app.config['NOTIFICATIONS_ENABLED'] = False
    else:
        app.config.setdefault('DATABASE_ACCESS_ENABLED', True)
        app.config.setdefault('NOTIFICATIONS_ENABLED', True)

    # Mobile uses Bearer tokens, not web cookies. Only explicitly configured web origins.
    import os
    app.config.setdefault('MOBILE_ALLOWED_ORIGINS', tuple(
        value.strip() for value in os.environ.get('MOBILE_ALLOWED_ORIGINS', '').split(',') if value.strip()))

    @app.before_request
    def mobile_preflight():
        if request.path.startswith('/api/v1/mobile/') and request.method == 'OPTIONS':
            if request.headers.get('Origin') not in app.config['MOBILE_ALLOWED_ORIGINS']:
                return '', 403
            return '', 204

    @app.after_request
    def mobile_cors(response):
        if request.path.startswith('/api/v1/mobile/'):
            origin = request.headers.get('Origin')
            if origin and origin in app.config['MOBILE_ALLOWED_ORIGINS']:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
                response.vary.add('Origin')
        return response

    # 2. Đăng ký các Controller (Blueprints)
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(mobile_auth_bp)
    app.register_blueprint(mobile_patient_bp)
    from core.medical_media import register_medical_media
    register_medical_media(app)
    from core.clinical_data import display_clinical
    app.jinja_env.filters['clinical'] = display_clinical
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    if app.config.get('MAX_CONTENT_LENGTH') is None:
        app.config['MAX_CONTENT_LENGTH'] = 96 * 1024 * 1024

    # 3. Bảng ánh xạ tương thích ngược cho url_for trong toàn bộ templates
    alias_map = {
        'home': 'home.home',
        'articles': 'home.articles',
        'article_detail': 'home.article_detail',
        'pricing': 'home.pricing',
        'services': 'home.pricing',
        'doctors': 'home.doctors',
        'departments': 'home.departments',
        'booking': 'patient.booking',
        'login': 'auth.login',
        'register': 'auth.register',
        'logout': 'auth.logout',
        'patient_dashboard': 'patient.dashboard',
        'patient_booking': 'patient.booking',
        'patient_appointments': 'patient.appointments',
        'patient_records': 'patient.records',
        'patient_lab_results': 'patient.lab_results',
        'patient_billing': 'patient.billing',
        'patient_profile': 'patient.profile',
        'patient_feedbacks': 'patient.feedbacks',
        'patient_notifications': 'patient.notifications',
        'admin_dashboard': 'admin.dashboard',
        'admin_patients': 'admin.patients',
        'admin_appointments': 'admin.appointments',
        'admin_reception': 'admin.reception',
        'admin_emr': 'admin.emr',
        'admin_lab': 'admin.lab',
        'admin_pharmacy': 'admin.pharmacy',
        'admin_billing': 'admin.billing',
        'admin_reports': 'admin.reports',
        'admin_catalogs': 'admin.catalogs',
        'admin_staff': 'admin.staff',
        'admin_feedbacks': 'admin.feedbacks',
        'admin_backups': 'admin.backups',
        'admin_doctors': 'admin.doctors',
        'admin_doctor_detail': 'admin.doctor_detail',
        'admin_accounts': 'admin.accounts',
        'admin_articles': 'admin.articles',
        'admin_article_create': 'admin.article_create',
        'admin_article_edit': 'admin.article_edit',
        'admin_article_delete': 'admin.article_delete',
        'admin_profile': 'admin.profile',
        'admin_my_doctor_profile': 'admin.my_doctor_profile',
        'profile': 'admin.profile',
        'admin.doctor_create': 'admin.create_doctor',
        'doctor_create': 'admin.create_doctor',
        'maintenance_patient': 'home.maintenance_patient',
        'maintenance_staff': 'home.maintenance_staff',
    }


    # Đăng ký alias vào app.view_functions để url_for cấp module/route hoạt động
    with app.app_context():
        for old_ep, new_ep in alias_map.items():
            if new_ep in app.view_functions and old_ep not in app.view_functions:
                app.view_functions[old_ep] = app.view_functions[new_ep]

    # Điều hướng đường dẫn đặt lịch chung
    @app.route('/booking')
    def legacy_booking():
        target = flask_url_for('patient.booking', **request.args)
        if not session.get('logged_in'):
            return redirect(flask_url_for('auth.login', next=target))
        user = session.get('user', {})
        if user.get('vai_tro') != 'BENHNHAN':
            return redirect(flask_url_for('admin.appointments'))
        return redirect(target)

    @app.route('/billing')
    def legacy_billing():
        if not session.get('logged_in'):
            return redirect(flask_url_for('home.pricing'))
        return redirect(flask_url_for('patient.billing'))

    @app.before_request
    def redirect_guest_billing():
        if request.path in ('/billing', '/patient/billing') and not session.get('logged_in'):
            return redirect(flask_url_for('home.pricing'))

    @app.before_request
    def maintenance_guard():
        # Bỏ qua request preflight CORS của Mobile, tài nguyên tĩnh, favicon
        if request.method == 'OPTIONS' or request.path.startswith('/static') or request.path == '/favicon.ico':
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

        # Kiểm tra chế độ bảo trì Cổng Bệnh nhân (Chỉ chặn khi truy cập phân hệ tài khoản/đặt lịch, cho phép vào trang Home)
        if settings.get('maintenance_patient'):
            is_patient_area = (
                request.path.startswith('/patient') or
                request.path.startswith('/booking') or
                request.path in ('/register', '/auth/register') or
                request.path.startswith('/api/patient') or
                request.path.startswith('/api/v1/mobile/patient')
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

        # Kiểm tra chế độ bảo trì Phân hệ Nhân viên y tế (Chỉ chặn khi truy cập nghiệp vụ nội bộ, cho phép vào trang Home)
        if settings.get('maintenance_staff'):
            is_staff_area = (
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

        return None


    # Context processor truyền thông tin người dùng, danh mục và resolver url_for vào templates
    @app.context_processor
    def inject_globals():
        from core.catalog import get_all_catalogs
        def smart_url_for(endpoint, **values):
            target = alias_map.get(endpoint, endpoint)
            try:
                return flask_url_for(target, **values)
            except Exception:
                try:
                    return flask_url_for(f"admin.{endpoint}", **values)
                except Exception:
                    return flask_url_for(endpoint, **values)

        import config
        clinic_info = {
            'address': getattr(config, 'CLINIC_ADDRESS', '140 Lê Trọng Tấn, Phường Tây Thạnh, Quận Tân Phú, TP. Hồ Chí Minh'),
            'lat': getattr(config, 'CLINIC_LATITUDE', 10.806689),
            'lng': getattr(config, 'CLINIC_LONGITUDE', 106.628581),
            'maps_api_key': getattr(config, 'GOOGLE_MAPS_API_KEY', ''),
            'maps_search_url': f"https://www.google.com/maps/search/?api=1&query={getattr(config, 'CLINIC_LATITUDE', 10.806689)},{getattr(config, 'CLINIC_LONGITUDE', 106.628581)}",
            'maps_dir_url': f"https://www.google.com/maps/dir/?api=1&destination=140+L%C3%AA+Tr%E1%BB%8Dng+T%E1%BA%A5n,+T%C3%A2y+Th%E1%BA%A1nh,+T%C3%A2n+Ph%C3%BA,+TP.+H%E1%BB%93+Ch%C3%AD+Minh"
        }

        return dict(
            current_user=session.get('user'),
            curr_user=session.get('user') or {},
            catalogs=get_all_catalogs(),
            clinic_info=clinic_info,
            url_for=smart_url_for,
            str=str
        )

    return app

def create_test_app(test_config=None):
    """CLI-friendly factory with real database access and notifications disabled."""
    settings = dict(test_config or {})
    settings['TESTING'] = True
    return create_app(settings)


app = create_app()

def start_runtime_services(app):
    """Explicit startup hook; never run schema updates or seed data here."""
    if app.testing or not app.config.get('NOTIFICATIONS_ENABLED', True):
        return
    if app.extensions.get('reminder_scheduler_started'):
        return
    from core.notification_service import NotificationService
    with app.app_context():
        worker = NotificationService.start_background_scheduler(interval_hours=2)
    if worker is not None:
        app.extensions['reminder_scheduler_started'] = True

if __name__ == '__main__':
    import os
    import sys
    import config
    from models.backup_model import BackupModel

    # Tu dong phuc hoi ban sao luu moi nhat khi khoi dong (chay mot lan trong tien trinh khoi dong chinh)
    should_restore = getattr(config, 'AUTO_RESTORE_ON_STARTUP', True) or ('--restore-latest' in sys.argv)
    is_main_startup = (os.environ.get('WERKZEUG_RUN_MAIN') is None) or (not getattr(config, 'DEBUG', False))

    if should_restore and is_main_startup:
        latest = BackupModel.get_latest_backup()
        if latest:
            print(f"[*] Khoi dong he thong: Dang nap ban sao luu moi nhat ({latest})...")
            ok, msg = BackupModel.restore_backup(latest, user_name='startup_auto_restore', create_safety_copy=False)
            if ok:
                print(f"[Thanh cong] Da dua ban luu gan nhat vao CSDL ({latest}).")
            else:
                print(f"[Canh bao] Khong the nap ban luu gan nhat: {msg}")
        else:
            print("[*] Chua co ban sao luu .bak nao trong thu muc backups/, giu nguyen CSDL hien hanh.")

    if is_main_startup:
        try:
            from models.clinic_model import ClinicModel
            ClinicModel.ensure_specialized_services()
        except Exception as seed_err:
            print(f"[Canh bao] Khong the dong bo danh muc dich vu chuyen nganh: {seed_err}")

    start_runtime_services(app)

    # Khoi chay tien trinh tu dong sao luu dinh ky moi 2 tieng
    auto_backup_hours = getattr(config, 'AUTO_BACKUP_INTERVAL_HOURS', 2)
    BackupModel.start_auto_backup_scheduler(interval_hours=auto_backup_hours)

    app.run(debug=True, port=5000)
