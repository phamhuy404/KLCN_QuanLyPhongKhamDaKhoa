import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'controllers', 'patient_controller.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_dash_code = """@patient_bp.route('/')
@patient_bp.route('/dashboard')
@login_required
def dashboard():
    \"\"\"Bảng điều khiển tổng quan cổng bệnh nhân.\"\"\"
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    appointments = AppointmentModel.get_by_patient(patient_id)
    return render_template('patient/dashboard.html', active_page='dashboard', patient=patient, appointments=appointments)"""

new_dash_code = """@patient_bp.route('/')
@patient_bp.route('/dashboard')
@login_required
def dashboard():
    \"\"\"Bảng điều khiển tổng quan cổng bệnh nhân kèm quét nhắc lịch khám tự động.\"\"\"
    patient_id = _get_current_patient_id()
    patient = PatientModel.get_by_id(patient_id)
    appointments = AppointmentModel.get_by_patient(patient_id)

    # Tự động quét và nhắc nhở lịch khám trong 24h - 48h tới
    try:
        from core.notification_service import NotificationService
        NotificationService.run_all_reminders()
    except Exception as e:
        pass

    user = session.get('user', {})
    tai_khoan_id = user.get('id')
    recent_notifs = []
    if tai_khoan_id:
        try:
            from models.notification_model import NotificationModel
            recent_notifs = NotificationModel.get_user_notifications(tai_khoan_id, limit=5)
        except Exception:
            pass

    return render_template('patient/dashboard.html', active_page='dashboard', patient=patient, appointments=appointments, recent_notifications=recent_notifs)"""

if old_dash_code in content:
    content = content.replace(old_dash_code, new_dash_code)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated dashboard in patient_controller.py successfully!")
else:
    print("old_dash_code not found in patient_controller.py!")
