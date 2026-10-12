from flask import Flask, session, url_for as flask_url_for, redirect
import config
from core.database import init_db
from controllers.home_controller import home_bp
from controllers.auth_controller import auth_bp
from controllers.patient_controller import patient_bp
from controllers.admin_controller import admin_bp
from controllers.api_controller import api_bp

def create_app():
    """Khởi tạo ứng dụng Flask theo mô hình kiến trúc MVC."""
    app = Flask(__name__)
    app.config.from_object(config)

    # 1. Khởi tạo và kiểm tra kết nối cơ sở dữ liệu
    init_db()

    # 2. Đăng ký các Controller (Blueprints)
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # 3. Bảng ánh xạ tương thích ngược cho url_for trong toàn bộ templates
    alias_map = {
        'home': 'home.home',
        'articles': 'home.articles',
        'article_detail': 'home.article_detail',
        'booking': 'patient.booking',
        'login': 'auth.login',
        'register': 'auth.register',
        'logout': 'auth.logout',
        'patient_dashboard': 'patient.dashboard',
        'patient_booking': 'patient.booking',
        'patient_records': 'patient.records',
        'patient_lab_results': 'patient.lab_results',
        'patient_billing': 'patient.billing',
        'patient_profile': 'patient.profile',
        'admin_dashboard': 'admin.dashboard',
        'admin_patients': 'admin.patients',
        'admin_appointments': 'admin.appointments',
        'admin_reception': 'admin.reception',
        'admin_emr': 'admin.emr',
        'admin_lab': 'admin.lab',
        'admin_pharmacy': 'admin.pharmacy',
        'admin_billing': 'admin.billing',
        'admin_reports': 'admin.reports',
    }

    # Đăng ký alias vào app.view_functions để url_for cấp module/route hoạt động
    with app.app_context():
        for old_ep, new_ep in alias_map.items():
            if new_ep in app.view_functions and old_ep not in app.view_functions:
                app.view_functions[old_ep] = app.view_functions[new_ep]

    # Điều hướng đường dẫn đặt lịch chung
    @app.route('/booking')
    def legacy_booking():
        if not session.get('logged_in'):
            return redirect(flask_url_for('auth.login', next=flask_url_for('patient.booking')))
        return redirect(flask_url_for('patient.booking'))

    # Context processor truyền thông tin người dùng và resolver url_for vào templates
    @app.context_processor
    def inject_globals():
        def smart_url_for(endpoint, **values):
            target = alias_map.get(endpoint, endpoint)
            try:
                return flask_url_for(target, **values)
            except Exception:
                return flask_url_for(endpoint, **values)

        return dict(
            current_user=session.get('user'),
            url_for=smart_url_for
        )

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
