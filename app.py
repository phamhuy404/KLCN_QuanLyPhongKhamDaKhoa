from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

# ==================== ĐIỀU HƯỚNG TRANG CHỦ ====================
@app.route('/')
def index():
    return redirect(url_for('patient_dashboard'))

# ==================== XÁC THỰC TÀI KHOẢN (AUTH) ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Giả lập đăng nhập thành công -> chuyển về dashboard bệnh nhân
        return redirect(url_for('patient_dashboard'))
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Giả lập đăng ký thành công -> chuyển về login
        return redirect(url_for('login'))
    return render_template('auth/register.html')

# ==================== PHÂN HỆ BỆNH NHÂN (PATIENT PORTAL) ====================
@app.route('/patient')
@app.route('/patient/dashboard')
def patient_dashboard():
    return render_template('patient/dashboard.html', active_page='dashboard')

@app.route('/patient/booking')
def patient_booking():
    return render_template('patient/booking.html', active_page='booking')

@app.route('/patient/records')
def patient_records():
    return render_template('patient/records.html', active_page='records')

@app.route('/patient/lab-results')
def patient_lab_results():
    return render_template('patient/lab_results.html', active_page='lab_results')

@app.route('/patient/billing')
def patient_billing():
    return render_template('patient/billing.html', active_page='billing')

@app.route('/patient/profile')
def patient_profile():
    return render_template('patient/profile.html', active_page='profile')

# ==================== PHÂN HỆ QUẢN TRỊ / BÁC SĨ (ADMIN) ====================
@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html', active_page='admin_dashboard')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
