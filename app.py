from flask import Flask, render_template, redirect, url_for, request, session, jsonify, abort, flash
import database

app = Flask(__name__)
app.secret_key = 'h2t_healthcare_clinic_secret_key_2026'

# Context processor truyền thông tin người dùng đang đăng nhập vào mọi template
@app.context_processor
def inject_user():
    return dict(current_user=session.get('user'))

# 1. TRANG CHỦ & BÀI VIẾT CÔNG KHAI
@app.route('/')
@app.route('/home')
def home():
    articles = database.get_articles(limit=5)
    stats = database.get_dashboard_stats()
    return render_template('home.html', articles=articles, stats=stats)

@app.route('/articles')
@app.route('/tin-tuc')
def articles():
    articles_list = database.get_articles(limit=20)
    return render_template('articles.html', articles=articles_list)

# 2. XÁC THỰC TÀI KHOẢN (AUTHENTICATION)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = database.authenticate_user(username, password)
        if not user:
            return render_template('auth/login.html', error='Tên đăng nhập hoặc mật khẩu không chính xác!')
        
        # Lưu phiên làm việc
        session['logged_in'] = True
        session['user'] = user

        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)

        # Điều hướng theo vai trò người dùng trong CSDL
        if user['vai_tro'] in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('patient_dashboard'))

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
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

        success, msg = database.register_patient_account(ho_ten, sdt, ngay_sinh, gioi_tinh, cccd, email, bhyt, password)
        if not success:
            return render_template('auth/register.html', error=msg)

        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# 3. ĐIỀU HƯỚNG ĐẶT LỊCH KHÁM
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if not session.get('logged_in'):
        return redirect(url_for('login', next=url_for('patient_booking')))
    return redirect(url_for('patient_booking'))

# 4. PHÂN HỆ BỆNH NHÂN (PATIENT PORTAL)
@app.route('/patient')
@app.route('/patient/dashboard')
def patient_dashboard():
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1
    patient = database.get_patient_by_id(patient_id)
    appointments = [a for a in database.get_all_appointments() if a['benh_nhan_id'] == patient_id]
    return render_template('patient/dashboard.html', active_page='dashboard', patient=patient, appointments=appointments)

@app.route('/patient/booking', methods=['GET', 'POST'])
def patient_booking():
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1

    if request.method == 'POST':
        chuyen_khoa_id = request.form.get('chuyen_khoa_id', 1, type=int)
        bac_si_id = request.form.get('bac_si_id', 1, type=int)
        ngay_hen = request.form.get('ngay_hen')
        gio_hen = request.form.get('gio_hen')
        ly_do = request.form.get('ly_do', '')
        database.create_appointment(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do)
        return redirect(url_for('patient_dashboard'))

    return render_template('patient/booking.html', active_page='booking')

@app.route('/patient/records')
def patient_records():
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1
    patient = database.get_patient_by_id(patient_id)
    return render_template('patient/records.html', active_page='records', patient=patient)

@app.route('/patient/lab-results')
def patient_lab_results():
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1
    patient = database.get_patient_by_id(patient_id)
    return render_template('patient/lab_results.html', active_page='lab_results', patient=patient)

@app.route('/patient/billing')
def patient_billing():
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1
    patient = database.get_patient_by_id(patient_id)
    invoices = [inv for inv in database.get_all_invoices() if inv['benh_nhan_id'] == patient_id]
    return render_template('patient/billing.html', active_page='billing', patient=patient, invoices=invoices)

@app.route('/patient/profile')
def patient_profile():
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1
    patient = database.get_patient_by_id(patient_id)
    return render_template('patient/profile.html', active_page='profile', patient=patient)

# 5. PHÂN HỆ QUẢN TRỊ & BÁC SĨ (ADMIN / CLINICAL PORTAL)
@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    stats = database.get_dashboard_stats()
    patients = database.get_all_patients()
    appointments = database.get_all_appointments()
    return render_template('admin/dashboard.html', active_page='admin_dashboard', stats=stats, patients=patients, appointments=appointments)

@app.route('/admin/patients')
def admin_patients():
    patients = database.get_all_patients()
    return render_template('admin/patients.html', active_page='admin_patients', patients=patients)

@app.route('/admin/patients/<int:patient_id>')
@app.route('/admin/patient_details/<int:patient_id>')
@app.route('/admin/patient-details/<int:patient_id>')
@app.route('/admin/patient_detail/<int:patient_id>')
@app.route('/admin/patient-detail/<int:patient_id>')
@app.route('/patient_details/<int:patient_id>')
@app.route('/patient-details/<int:patient_id>')
def admin_patient_detail(patient_id):
    patient = database.get_patient_by_id(patient_id)
    if not patient:
        abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@app.route('/admin/patient_details')
@app.route('/admin/patient-details')
@app.route('/admin/patient_detail')
@app.route('/admin/patient-detail')
@app.route('/patient_details')
@app.route('/patient-details')
def patient_details_default():
    patient_id = request.args.get('id', 1, type=int)
    patient = database.get_patient_by_id(patient_id)
    if not patient:
        patients = database.get_all_patients()
        if patients:
            patient = patients[0]
        else:
            abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@app.route('/admin/appointments')
def admin_appointments():
    appointments = database.get_all_appointments()
    patients = database.get_all_patients()
    return render_template('admin/appointments.html', active_page='admin_appointments', appointments=appointments, patients=patients)

@app.route('/admin/reception')
def admin_reception():
    patients = database.get_all_patients()
    appointments = database.get_all_appointments()
    return render_template('admin/reception.html', active_page='admin_reception', patients=patients, appointments=appointments)

@app.route('/admin/emr')
def admin_emr():
    patients = database.get_all_patients()
    medicines = database.get_all_medicines()
    services = database.get_all_services()
    return render_template('admin/emr.html', active_page='admin_emr', patients=patients, medicines=medicines, services=services)

@app.route('/admin/lab')
def admin_lab():
    patients = database.get_all_patients()
    services = database.get_all_services()
    lab_orders = database.get_all_lab_orders()
    return render_template('admin/lab.html', active_page='admin_lab', patients=patients, services=services, lab_orders=lab_orders)

@app.route('/admin/pharmacy')
def admin_pharmacy():
    medicines = database.get_all_medicines()
    prescriptions = database.get_all_prescriptions()
    return render_template('admin/pharmacy.html', active_page='admin_pharmacy', medicines=medicines, prescriptions=prescriptions)

@app.route('/admin/billing')
def admin_billing():
    invoices = database.get_all_invoices()
    patients = database.get_all_patients()
    return render_template('admin/billing.html', active_page='admin_billing', invoices=invoices, patients=patients)

@app.route('/admin/reports')
def admin_reports():
    stats = database.get_dashboard_stats()
    invoices = database.get_all_invoices()
    return render_template('admin/reports.html', active_page='admin_reports', stats=stats, invoices=invoices)

# 6. REST API NỘI BỘ
@app.route('/api/admin/reset-password', methods=['POST'])
def api_reset_password():
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    new_password = data.get('new_password')
    if not patient_id or not new_password:
        return jsonify({'success': False, 'message': 'Thiếu thông tin yêu cầu!'}), 400

    success, msg = database.reset_patient_password(patient_id, new_password)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/appointment/book', methods=['POST'])
def api_book_appointment():
    data = request.get_json() or {}
    user = session.get('user')
    patient_id = user.get('patient_id', 1) if user else 1

    chuyen_khoa_id = data.get('chuyen_khoa_id', 1)
    bac_si_id = data.get('bac_si_id', 1)
    ngay_hen = data.get('ngay_hen', '2026-09-29')
    gio_hen = data.get('gio_hen', '08:30:00')
    ly_do = data.get('ly_do', 'Khám theo yêu cầu')

    success, code = database.create_appointment(patient_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do)
    return jsonify({'success': success, 'ma_lich_hen': code})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
