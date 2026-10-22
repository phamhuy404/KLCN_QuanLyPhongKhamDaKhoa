from flask import Blueprint, render_template, request, abort, jsonify, redirect, url_for, session, flash
from core.security import roles_required
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.clinic_model import ClinicModel
from models.user_model import UserModel

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def admin_access_guard():
    """Bảo vệ phân hệ quản trị: Chỉ cho phép nhân viên y tế và admin truy cập."""
    pass

@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    """Bảng điều khiển quản trị tổng quan toàn hệ thống."""
    stats = ClinicModel.get_dashboard_stats()
    patients = PatientModel.get_all()
    appointments = AppointmentModel.get_all()
    return render_template('admin/dashboard.html', active_page='admin_dashboard', stats=stats, patients=patients, appointments=appointments)

@admin_bp.route('/patients')
def patients():
    """Quản lý danh sách hồ sơ bệnh nhân theo phân quyền."""
    curr_user = session.get('user', {})
    user_role = curr_user.get('vai_tro')
    if user_role == 'BACSI':
        dept_id = curr_user.get('chuyen_khoa_id')
        if not dept_id and curr_user.get('bac_si_id'):
            doc_info = UserModel.get_doctor_by_id(curr_user.get('bac_si_id'))
            if doc_info:
                dept_id = doc_info.get('chuyen_khoa_id')
        patients_list = PatientModel.get_by_department(dept_id) if dept_id else PatientModel.get_all()
    else:
        patients_list = PatientModel.get_all()
    return render_template('admin/patients.html', active_page='admin_patients', patients=patients_list)

@admin_bp.route('/patients/<int:patient_id>')
@admin_bp.route('/patient_details/<int:patient_id>')
@admin_bp.route('/patient-details/<int:patient_id>')
@admin_bp.route('/patient_detail/<int:patient_id>')
def patient_detail(patient_id):
    """Xem hồ sơ bệnh án 360 độ của một bệnh nhân."""
    patient = PatientModel.get_by_id(patient_id)
    if not patient:
        abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@admin_bp.route('/patient_details')
@admin_bp.route('/patient-details')
def patient_details_default():
    """Xem hồ sơ bệnh nhân đầu tiên hoặc theo id từ query string."""
    patient_id = request.args.get('id', type=int)
    if patient_id:
        patient = PatientModel.get_by_id(patient_id)
    else:
        patients_list = PatientModel.get_all()
        patient = patients_list[0] if patients_list else None

    if not patient:
        abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@admin_bp.route('/appointments')
def appointments():
    """Quản lý tiếp nhận và phân bổ lịch hẹn khám theo phân quyền."""
    curr_user = session.get('user', {})
    appointments_list = AppointmentModel.get_for_user(curr_user)
    patients_list = PatientModel.get_all()
    doctors = UserModel.get_all_doctors()
    departments = ClinicModel.get_all_departments()
    return render_template('admin/appointments.html', active_page='admin_appointments', appointments=appointments_list, patients=patients_list, doctors=doctors, departments=departments)

@admin_bp.route('/reception')
def reception():
    """Phân hệ tiếp đón lễ tân, check-in và đăng ký người bệnh mới."""
    patients_list = PatientModel.get_all()
    appointments_list = AppointmentModel.get_all()
    departments = ClinicModel.get_all_departments()
    return render_template('admin/reception.html', active_page='admin_reception', patients=patients_list, appointments=appointments_list, departments=departments)

@admin_bp.route('/emr')
def emr():
    """Phân hệ bác sĩ: Bệnh án điện tử EMR, chẩn đoán ICD và ra y lệnh."""
    patients_list = PatientModel.get_all()
    medicines = PharmacyModel.get_all_medicines()
    services = ClinicModel.get_all_services()
    doctors = UserModel.get_all_doctors()
    return render_template('admin/emr.html', active_page='admin_emr', patients=patients_list, medicines=medicines, services=services, doctors=doctors)

@admin_bp.route('/lab')
def lab():
    """Phân hệ kỹ thuật viên: Thực hiện xét nghiệm và chẩn đoán hình ảnh."""
    patients_list = PatientModel.get_all()
    services = ClinicModel.get_all_services()
    lab_orders = MedicalRecordModel.get_all_lab_orders()
    return render_template('admin/lab.html', active_page='admin_lab', patients=patients_list, services=services, lab_orders=lab_orders)

@admin_bp.route('/pharmacy')
def pharmacy():
    """Phân hệ dược sĩ: Quản lý kho dược và xuất cấp thuốc theo đơn."""
    medicines = PharmacyModel.get_all_medicines()
    prescriptions = MedicalRecordModel.get_all_prescriptions()
    return render_template('admin/pharmacy.html', active_page='admin_pharmacy', medicines=medicines, prescriptions=prescriptions)

@admin_bp.route('/billing')
def billing():
    """Phân hệ thu ngân: Viện phí, chi trả BHYT và xuất hóa đơn điện tử."""
    invoices = BillingModel.get_all()
    
    # Tiền xử lý dữ liệu: Đảm bảo mọi hóa đơn đều có key 'tien_bhyt_chi_tra' với giá trị hợp lệ
    # Điều này giúp tránh lỗi Jinja2 khi dùng bộ lọc sum() trên file HTML
    for inv in invoices:
        if 'tien_bhyt_chi_tra' not in inv or inv['tien_bhyt_chi_tra'] is None:
            inv['tien_bhyt_chi_tra'] = 0
            
    patients_list = PatientModel.get_all()
    return render_template('admin/billing.html', active_page='admin_billing', invoices=invoices, patients=patients_list)

@admin_bp.route('/reports')
def reports():
    """Báo cáo thống kê doanh thu, lưu lượng bệnh nhân và hiệu suất phòng khám."""
    stats = ClinicModel.get_dashboard_stats()
    report_stats = ClinicModel.get_report_stats()
    invoices = BillingModel.get_all()
    return render_template('admin/reports.html', active_page='admin_reports', stats=stats, report_stats=report_stats, invoices=invoices)

@admin_bp.route('/catalogs')
@roles_required('ADMIN', 'LETAN', 'DUOCSI')
def catalogs():
    """Quản lý danh mục y tế: Chuyên khoa, Phòng khám vật lý, Dịch vụ kỹ thuật."""
    departments = ClinicModel.get_all_departments(active_only=False)
    rooms = ClinicModel.get_all_rooms(active_only=False)
    services = ClinicModel.get_all_services(active_only=False)
    return render_template('admin/catalogs.html', active_page='admin_catalogs', departments=departments, rooms=rooms, services=services)

@admin_bp.route('/staff')
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def staff():
    """Quản lý nhân sự y tế, bác sĩ chuyên khoa và lịch làm việc / phân ca trực."""
    from models.schedule_model import ScheduleModel
    curr_user = session.get('user', {})
    user_role = curr_user.get('vai_tro', 'ADMIN')

    staff_list = UserModel.get_all_staff(user_info=curr_user)
    doctors = UserModel.get_all_doctors()
    schedules = ScheduleModel.get_all(current_user=curr_user)
    roles = UserModel.get_all_roles()
    departments = ClinicModel.get_all_departments(active_only=True)
    rooms = ClinicModel.get_all_rooms(active_only=True)
    week_bounds = ScheduleModel.get_week_bounds()
    current_week_days = ScheduleModel.get_week_days(week_bounds['current_week'][0])
    next_week_1_days = ScheduleModel.get_week_days(week_bounds['next_week_1'][0])
    next_week_2_days = ScheduleModel.get_week_days(week_bounds['next_week_2'][0])
    shifts_info = [
        {'id': 1, 'ca_id': 1, 'ten': 'Sáng', 'ten_ca': 'Sáng', 'gio': '07:00 - 11:30', 'gio_lam_viec': '07:00 - 11:30', 'icon': 'fa-solid fa-sun', 'icon_color': 'text-amber-500'},
        {'id': 2, 'ca_id': 2, 'ten': 'Chiều', 'ten_ca': 'Chiều', 'gio': '13:30 - 17:00', 'gio_lam_viec': '13:30 - 17:00', 'icon': 'fa-solid fa-cloud-sun', 'icon_color': 'text-amber-600'},
        {'id': 3, 'ca_id': 3, 'ten': 'Tối', 'ten_ca': 'Tối', 'gio': '17:30 - 20:30', 'gio_lam_viec': '17:30 - 20:30', 'icon': 'fa-solid fa-moon', 'icon_color': 'text-indigo-900'},
    ]

    pending_approvals = []
    if user_role in ['ADMIN', 'LETAN']:
        filter_role = request.args.get('pending_role')
        filter_ca = request.args.get('pending_ca')
        pending_approvals = ScheduleModel.get_pending_approvals(filter_role=filter_role, filter_ca=filter_ca)

    active_tab = request.args.get('tab', 'staff')

    return render_template(
        'admin/staff.html',
        active_page='admin_staff',
        curr_user=curr_user,
        user_role=user_role,
        staff_list=staff_list,
        doctors=doctors,
        schedules=schedules,
        roles=roles,
        departments=departments,
        rooms=rooms,
        week_bounds=week_bounds,
        current_week_days=current_week_days,
        next_week_1_days=next_week_1_days,
        next_week_2_days=next_week_2_days,
        shifts_info=shifts_info,
        pending_approvals=pending_approvals,
        active_tab=active_tab
    )

@admin_bp.route('/feedbacks')
@roles_required('ADMIN', 'LETAN', 'BACSI')
def feedbacks():
    """Tiếp nhận, xử lý và phản hồi ý kiến đóng góp của người bệnh."""
    from models.feedback_model import FeedbackModel
    status_filter = request.args.get('status', 'ALL')
    topic_filter = request.args.get('topic', 'ALL')
    feedback_list = FeedbackModel.get_all(filter_status=status_filter, filter_topic=topic_filter)
    return render_template('admin/feedbacks.html', active_page='admin_feedbacks', feedbacks=feedback_list, current_status=status_filter, current_topic=topic_filter)

@admin_bp.route('/backups')
@roles_required('ADMIN')
def backups():
    """Quản lý sao lưu và phục hồi cơ sở dữ liệu an toàn (Dành riêng cho Quản trị viên)."""
    from models.backup_model import BackupModel
    backup_data = BackupModel.list_backups()
    return render_template('admin/backups.html', active_page='admin_backups', backup_data=backup_data)

@admin_bp.route('/accounts')
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def accounts():
    """Điều hướng hợp nhất sang phân hệ Quản lý Nhân sự & Lịch trực."""
    return redirect(url_for('admin.staff', tab='staff'))

@admin_bp.route('/accounts/reset-password', methods=['POST'])
@roles_required('ADMIN', 'BACSI', 'LETAN', 'DUOCSI', 'KTV')
def reset_account_password():
    """Đặt lại mật khẩu cho tài khoản người dùng (Admin toàn quyền, nhân sự chỉ đổi của chính mình)."""
    req_json = request.get_json(silent=True) or {}
    account_id = req_json.get('account_id') or request.form.get('account_id', type=int)
    new_password = req_json.get('new_password') or request.form.get('new_password')
    curr_user = session.get('user', {})
    user_role = curr_user.get('vai_tro')

    if not account_id:
        return jsonify({'success': False, 'message': 'Thiếu mã tài khoản!'}), 400

    # Nếu không phải Admin thì chỉ được phép đổi mật khẩu cho chính mình
    if user_role != 'ADMIN' and int(curr_user.get('id', 0)) != int(account_id):
        return jsonify({'success': False, 'message': 'Bạn chỉ có quyền đổi mật khẩu cho chính tài khoản của mình!'}), 403

    success, msg = UserModel.reset_account_password(int(account_id), new_password, audit_user=curr_user)
    if success:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@admin_bp.route('/accounts/toggle-status/<int:account_id>', methods=['POST'])
@admin_bp.route('/accounts/toggle-status', methods=['POST'])
@roles_required('ADMIN')
def toggle_account_status(account_id=None):
    """Bật/tắt trạng thái hoạt động của tài khoản (Chặn vô hiệu hóa tài khoản Admin)."""
    if not account_id:
        req_json = request.get_json(silent=True) or {}
        account_id = req_json.get('account_id') or request.form.get('account_id', type=int)
    curr_user = session.get('user')
    success, res = UserModel.toggle_account_status(account_id, audit_user=curr_user)
    if not success:
        return jsonify({'success': False, 'message': res}), 400
    return jsonify({'success': True, 'new_status': res, 'status': res, 'message': 'Đã thay đổi trạng thái thành công'})

@admin_bp.route('/accounts/create-staff', methods=['POST'])
@roles_required('ADMIN')
def create_staff_account():
    """Tạo mới tài khoản nhân viên / tiếp tân / bác sĩ."""
    data = request.form.to_dict()
    curr_user = session.get('user')
    success, res = UserModel.create_staff(data, audit_user=curr_user)
    if success:
        flash(f"Đã tạo thành công tài khoản cho {data.get('ho_ten')}!", 'success')
    else:
        flash(f"Lỗi tạo tài khoản: {res}", 'error')

    return redirect(url_for('admin.staff', tab='staff'))

@admin_bp.route('/sample-csv/<string:module>')
@roles_required('ADMIN', 'LETAN', 'DUOCSI')
def download_sample_csv(module):
    """Tải tệp CSV mẫu chuẩn UTF-8-SIG."""
    from core.csv_service import CSVService
    from flask import Response
    content, filename = CSVService.get_sample_csv(module)
    if not content:
        flash(filename, 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@admin_bp.route('/export-csv/<string:module>')
@roles_required('ADMIN', 'LETAN', 'DUOCSI')
def export_csv(module):
    """Xuất toàn bộ dữ liệu thực tế ra tệp CSV có BOM tiếng Việt."""
    from core.csv_service import CSVService
    from flask import Response
    content, filename = CSVService.export_csv(module)
    if not content:
        flash(filename, 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@admin_bp.route('/import-csv/<string:module>', methods=['POST'])
@roles_required('ADMIN', 'LETAN', 'DUOCSI')
def import_csv(module):
    """Nhập dữ liệu hàng loạt từ tệp CSV kèm kiểm tra thông minh chống trùng lặp."""
    from core.csv_service import CSVService
    file = request.files.get('csv_file')
    if not file or not file.filename:
        flash('Vui lòng chọn một tệp CSV để nhập dữ liệu!', 'warning')
        return redirect(request.referrer or url_for('admin.dashboard'))

    curr_user = session.get('user', {})
    success, msg, inserted, updated = CSVService.import_csv(module, file.stream, current_user=curr_user)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')

    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/doctors')
def doctors():
    """Danh sách đội ngũ bác sĩ chuyên khoa."""
    doctors_list = UserModel.get_all_doctors()
    departments = ClinicModel.get_all_departments(active_only=True)
    return render_template('admin/doctors.html', active_page='admin_doctors', doctors=doctors_list, departments=departments)

@admin_bp.route('/doctors/<int:doctor_id>')
def doctor_detail(doctor_id):
    """Hồ sơ chi tiết y khoa 360 độ của bác sĩ kèm kiểm soát quyền truy cập."""
    curr_user = session.get('user', {})
    user_role = curr_user.get('vai_tro')
    user_doctor_id = curr_user.get('bac_si_id')

    # Bác sĩ chỉ có quyền xem hồ sơ và bệnh nhân của chính mình
    if user_role == 'BACSI':
        if not user_doctor_id or int(user_doctor_id) != int(doctor_id):
            flash('Bạn chỉ có quyền xem hồ sơ và danh sách bệnh nhân của chính mình.', 'warning')
            if user_doctor_id:
                return redirect(url_for('admin.doctor_detail', doctor_id=user_doctor_id))
            abort(403)

    doctor = UserModel.get_doctor_by_id(doctor_id)
    if not doctor:
        abort(404)

    # Lấy lịch làm việc/ca trực của bác sĩ
    from models.schedule_model import ScheduleModel
    schedules = ScheduleModel.get_all(filter_doctor_id=doctor_id)

    # Lấy danh sách bệnh nhân đặt lịch hẹn
    appointments = UserModel.get_doctor_appointments(doctor_id)

    # Lấy danh sách bệnh nhân đã thăm khám EMR
    visits = UserModel.get_doctor_visits(doctor_id)

    return render_template(
        'admin/doctor_detail.html',
        active_page='admin_doctors',
        doctor=doctor,
        schedules=schedules,
        appointments=appointments,
        visits=visits
    )

@admin_bp.route('/my-doctor-profile')
def my_doctor_profile():
    """Điều hướng nhanh đến hồ sơ của bác sĩ đang đăng nhập."""
    curr_user = session.get('user', {})
    doctor_id = curr_user.get('bac_si_id')
    if not doctor_id:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.doctor_detail', doctor_id=doctor_id))

@admin_bp.route('/doctors/<int:doctor_id>/avatar', methods=['POST'])
def doctor_update_avatar(doctor_id):
    """Cập nhật ảnh đại diện bác sĩ hỗ trợ upload nén WebP hoặc dán URL."""
    curr_user = session.get('user', {})
    user_role = curr_user.get('vai_tro')
    user_doctor_id = curr_user.get('bac_si_id')

    if user_role == 'BACSI' and (not user_doctor_id or int(user_doctor_id) != int(doctor_id)):
        abort(403)

    image_file = request.files.get('avatar_file')
    avatar_url = (request.form.get('avatar_url') or '').strip()

    source = image_file if (image_file and getattr(image_file, 'filename', None)) else avatar_url
    if not source:
        flash('Vui lòng chọn ảnh hoặc nhập URL hợp lệ.', 'warning')
        return redirect(url_for('admin.doctor_detail', doctor_id=doctor_id))

    from core.image_service import process_image_input
    final_path, err = process_image_input(source, category='bac_si', quality=85)
    if err:
        flash(err, 'error')
        return redirect(url_for('admin.doctor_detail', doctor_id=doctor_id))

    if not final_path:
        final_path = avatar_url

    UserModel.update_doctor_avatar(doctor_id, final_path)
    flash('Đã cập nhật ảnh đại diện bác sĩ thành công!', 'success')
    return redirect(url_for('admin.doctor_detail', doctor_id=doctor_id))

@admin_bp.route('/articles')
def articles():
    """Quản lý danh sách bài viết cẩm nang y tế."""
    from models.article_model import ArticleModel
    category = request.args.get('category', 'ALL')
    status = request.args.get('status', 'ALL')
    search = request.args.get('search', '')

    articles_list = ArticleModel.get_all_admin(category=category, search=search, status=status)
    categories = ArticleModel.get_categories()
    return render_template(
        'admin/articles.html',
        active_page='admin_articles',
        articles=articles_list,
        categories=categories,
        current_cat=category,
        current_status=status
    )

@admin_bp.route('/articles/create', methods=['GET', 'POST'])
def article_create():
    """Soạn thảo và đăng tải bài viết mới."""
    from models.article_model import ArticleModel
    if request.method == 'POST':
        curr_user = session.get('user', {})
        data = request.form.to_dict()
        data['tac_gia_id'] = curr_user.get('staff_id') or curr_user.get('id') or 1

        # Xử lý tệp ảnh bìa nếu upload từ máy tính hoặc dán link URL
        image_file = request.files.get('image_file')
        raw_image_url = (data.get('hinh_anh') or '').strip()
        source = image_file if (image_file and getattr(image_file, 'filename', None)) else raw_image_url
        if source:
            from core.image_service import process_image_input
            web_path, err = process_image_input(source, category='bai_viet', quality=82)
            if not err and web_path:
                data['hinh_anh'] = web_path

        success, res = ArticleModel.create(data)
        if success:
            return redirect(url_for('admin.articles'))
        return render_template(
            'admin/article_editor.html',
            active_page='admin_articles',
            error=res,
            categories=ArticleModel.get_categories(),
            article=data
        )

    categories = ArticleModel.get_categories()
    return render_template('admin/article_editor.html', active_page='admin_articles', categories=categories, article=None)

@admin_bp.route('/articles/edit/<int:article_id>', methods=['GET', 'POST'])
def article_edit(article_id):
    """Chỉnh sửa bài viết đã có."""
    from models.article_model import ArticleModel
    article = ArticleModel.get_by_id(article_id)
    if not article:
        abort(404)

    if request.method == 'POST':
        data = request.form.to_dict()
        image_file = request.files.get('image_file')
        raw_image_url = (data.get('hinh_anh') or '').strip()
        source = image_file if (image_file and getattr(image_file, 'filename', None)) else raw_image_url
        if source and source != article.get('hinh_anh'):
            from core.image_service import process_image_input
            web_path, err = process_image_input(source, category='bai_viet', quality=82)
            if not err and web_path:
                data['hinh_anh'] = web_path

        success, res = ArticleModel.update(article_id, data)
        if success:
            return redirect(url_for('admin.articles'))
        return render_template(
            'admin/article_editor.html',
            active_page='admin_articles',
            error=res,
            categories=ArticleModel.get_categories(),
            article=article
        )

    categories = ArticleModel.get_categories()
    return render_template('admin/article_editor.html', active_page='admin_articles', categories=categories, article=article)

@admin_bp.route('/articles/delete/<int:article_id>', methods=['POST'])
def article_delete(article_id):
    """Xóa bài viết."""
    from models.article_model import ArticleModel
    success, msg = ArticleModel.delete(article_id)
    return jsonify({'success': success, 'message': msg})

@admin_bp.route('/banners')
@roles_required('ADMIN')
def banners():
    """Trang quản trị các banner slider trang chủ."""
    from models.banner_model import BannerModel
    all_banners = BannerModel.get_all()
    active_count = len([b for b in all_banners if b.get('trang_thai') == 1])
    return render_template(
        'admin/banners.html',
        active_page='admin_banners',
        banners=all_banners,
        active_count=active_count
    )

@admin_bp.route('/banners/create', methods=['POST'])
@roles_required('ADMIN')
def banner_create():
    """Tạo banner mới."""
    from models.banner_model import BannerModel
    data = request.form.to_dict()
    image_file = request.files.get('image_file')
    success, msg = BannerModel.create(data, image_file=image_file)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('admin.banners'))

@admin_bp.route('/banners/edit/<int:banner_id>', methods=['POST'])
@roles_required('ADMIN')
def banner_edit(banner_id):
    """Cập nhật banner."""
    from models.banner_model import BannerModel
    data = request.form.to_dict()
    image_file = request.files.get('image_file')
    success, msg = BannerModel.update(banner_id, data, image_file=image_file)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('admin.banners'))

@admin_bp.route('/banners/delete/<int:banner_id>', methods=['POST'])
@roles_required('ADMIN')
def banner_delete(banner_id):
    """Xóa banner."""
    from models.banner_model import BannerModel
    success, msg = BannerModel.delete(banner_id)
    return jsonify({'success': success, 'message': msg})

@admin_bp.route('/banners/toggle/<int:banner_id>', methods=['POST'])
@roles_required('ADMIN')
def banner_toggle(banner_id):
    """Bật hoặc tắt trạng thái hiển thị của banner."""
    from models.banner_model import BannerModel
    success, res = BannerModel.toggle_status(banner_id)
    return jsonify({'success': success, 'status': res})



