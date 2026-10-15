from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    jsonify,
    redirect,
    url_for,
    session,
)
from core.security import roles_required
from models.article_model import ArticleModel
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.clinic_model import ClinicModel
from models.user_model import UserModel

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@roles_required("ADMIN", "BACSI", "LETAN", "DUOCSI", "KTV")
def admin_access_guard():
    """Bảo vệ phân hệ quản trị: Chỉ cho phép nhân viên y tế và admin truy cập."""
    pass


@admin_bp.route("/")
@admin_bp.route("/dashboard")
def dashboard():
    """Bảng điều khiển quản trị tổng quan toàn hệ thống."""
    stats = ClinicModel.get_dashboard_stats()
    patients = PatientModel.get_all()
    appointments = AppointmentModel.get_all()
    return render_template(
        "admin/dashboard.html",
        active_page="admin_dashboard",
        stats=stats,
        patients=patients,
        appointments=appointments,
    )


@admin_bp.route("/patients")
def patients():
    """Quản lý danh sách hồ sơ bệnh nhân."""
    patients_list = PatientModel.get_all()
    return render_template(
        "admin/patients.html", active_page="admin_patients", patients=patients_list
    )


@admin_bp.route("/patients/<int:patient_id>")
@admin_bp.route("/patient_details/<int:patient_id>")
@admin_bp.route("/patient-details/<int:patient_id>")
@admin_bp.route("/patient_detail/<int:patient_id>")
def patient_detail(patient_id):
    """Xem hồ sơ bệnh án 360 độ của một bệnh nhân."""
    patient = PatientModel.get_by_id(patient_id)
    if not patient:
        abort(404)
    return render_template(
        "admin/patient_detail.html", active_page="admin_patients", patient=patient
    )


@admin_bp.route("/patient_details")
@admin_bp.route("/patient-details")
def patient_details_default():
    """Xem hồ sơ bệnh nhân đầu tiên hoặc theo id từ query string."""
    patient_id = request.args.get("id", type=int)
    if patient_id:
        patient = PatientModel.get_by_id(patient_id)
    else:
        patients_list = PatientModel.get_all()
        patient = patients_list[0] if patients_list else None

    if not patient:
        abort(404)
    return render_template(
        "admin/patient_detail.html", active_page="admin_patients", patient=patient
    )


@admin_bp.route("/appointments")
def appointments():
    """Quản lý tiếp nhận và phân bổ lịch hẹn khám."""
    appointments_list = AppointmentModel.get_all()
    patients_list = PatientModel.get_all()
    return render_template(
        "admin/appointments.html",
        active_page="admin_appointments",
        appointments=appointments_list,
        patients=patients_list,
    )


@admin_bp.route("/reception")
def reception():
    """Phân hệ tiếp đón lễ tân, check-in và đăng ký người bệnh mới."""
    patients_list = PatientModel.get_all()
    appointments_list = AppointmentModel.get_all()
    departments = ClinicModel.get_all_departments()
    return render_template(
        "admin/reception.html",
        active_page="admin_reception",
        patients=patients_list,
        appointments=appointments_list,
        departments=departments,
    )


@admin_bp.route("/emr")
def emr():
    """Phân hệ bác sĩ: Bệnh án điện tử EMR, chẩn đoán ICD và ra y lệnh."""
    patients_list = PatientModel.get_all()
    medicines = PharmacyModel.get_all_medicines()
    services = ClinicModel.get_all_services()
    doctors = UserModel.get_all_doctors()
    return render_template(
        "admin/emr.html",
        active_page="admin_emr",
        patients=patients_list,
        medicines=medicines,
        services=services,
        doctors=doctors,
    )


@admin_bp.route("/lab")
def lab():
    """Phân hệ kỹ thuật viên: Thực hiện xét nghiệm và chẩn đoán hình ảnh."""
    patients_list = PatientModel.get_all()
    services = ClinicModel.get_all_services()
    lab_orders = MedicalRecordModel.get_all_lab_orders()
    return render_template(
        "admin/lab.html",
        active_page="admin_lab",
        patients=patients_list,
        services=services,
        lab_orders=lab_orders,
    )


@admin_bp.route("/pharmacy")
def pharmacy():
    """Phân hệ dược sĩ: Quản lý kho dược và xuất cấp thuốc theo đơn."""
    medicines = PharmacyModel.get_all_medicines()
    prescriptions = MedicalRecordModel.get_all_prescriptions()
    return render_template(
        "admin/pharmacy.html",
        active_page="admin_pharmacy",
        medicines=medicines,
        prescriptions=prescriptions,
    )


@admin_bp.route("/billing")
def billing():
    """Phân hệ thu ngân: Viện phí, chi trả BHYT và xuất hóa đơn điện tử."""
    invoices = BillingModel.get_all()
    patients_list = PatientModel.get_all()
    return render_template(
        "admin/billing.html",
        active_page="admin_billing",
        invoices=invoices,
        patients=patients_list,
    )


@admin_bp.route("/reports")
def reports():
    """Báo cáo thống kê doanh thu, lưu lượng bệnh nhân và hiệu suất phòng khám."""
    stats = ClinicModel.get_dashboard_stats()
    invoices = BillingModel.get_all()
    return render_template(
        "admin/reports.html",
        active_page="admin_reports",
        stats=stats,
        invoices=invoices,
    )


@admin_bp.route("/catalogs")
@roles_required("ADMIN")
def catalogs():
    """Quản lý danh mục y tế: Chuyên khoa, Phòng khám vật lý, Dịch vụ kỹ thuật."""
    departments = ClinicModel.get_all_departments(active_only=False)
    rooms = ClinicModel.get_all_rooms(active_only=False)
    services = ClinicModel.get_all_services(active_only=False)
    return render_template(
        "admin/catalogs.html",
        active_page="admin_catalogs",
        departments=departments,
        rooms=rooms,
        services=services,
    )


@admin_bp.route("/staff")
@roles_required("ADMIN")
def staff():
    """Quản lý nhân sự y tế, bác sĩ chuyên khoa và lịch làm việc / phân ca trực."""
    from models.schedule_model import ScheduleModel

    staff_list = UserModel.get_all_staff()
    doctors = UserModel.get_all_doctors()
    schedules = ScheduleModel.get_all()
    roles = UserModel.get_all_roles()
    departments = ClinicModel.get_all_departments(active_only=True)
    rooms = ClinicModel.get_all_rooms(active_only=True)
    accounts = UserModel.get_accounts()
    return render_template(
        "admin/staff.html",
        active_page="admin_staff",
        staff_list=staff_list,
        doctors=doctors,
        schedules=schedules,
        roles=roles,
        departments=departments,
        rooms=rooms,
        accounts=accounts,
    )


@admin_bp.route("/feedbacks")
@roles_required("ADMIN", "LETAN", "BACSI")
def feedbacks():
    """Tiếp nhận, xử lý và phản hồi ý kiến đóng góp của người bệnh."""
    from models.feedback_model import FeedbackModel

    status_filter = request.args.get("status", "ALL")
    topic_filter = request.args.get("topic", "ALL")
    feedback_list = FeedbackModel.get_all(
        filter_status=status_filter, filter_topic=topic_filter
    )
    return render_template(
        "admin/feedbacks.html",
        active_page="admin_feedbacks",
        feedbacks=feedback_list,
        current_status=status_filter,
        current_topic=topic_filter,
    )


@admin_bp.route("/backups")
@roles_required("ADMIN")
def backups():
    """Quản lý sao lưu và phục hồi cơ sở dữ liệu an toàn (Dành riêng cho Quản trị viên)."""
    from models.backup_model import BackupModel

    backup_data = BackupModel.list_backups()
    return render_template(
        "admin/backups.html", active_page="admin_backups", backup_data=backup_data
    )


# ==========================================
# 1. QUẢN LÝ TÀI KHOẢN (IMPORT/EXPORT EXCEL & CSV)
# ==========================================
@admin_bp.route("/accounts")
@roles_required("ADMIN")
def accounts():
    role_filter = request.args.get("role", "ALL")
    search_query = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)

    accounts_data = UserModel.get_accounts(
        role=role_filter, search=search_query, page=page, per_page=100
    )
    roles = UserModel.get_all_roles()
    stats = UserModel.get_account_stats()

    return render_template(
        "admin/accounts.html",
        active_page="admin_accounts",
        accounts=accounts_data["accounts"],
        total=accounts_data["total"],
        roles=roles,
        stats=stats,
        current_role=role_filter,
        current_search=search_query,
    )


@admin_bp.route(
    "/accounts/toggle-status/<int:account_id>",
    methods=["POST"],
)
@roles_required("ADMIN")
def toggle_account_status(account_id):
    curr_user = session.get("user", {})
    success, res = UserModel.toggle_account_status(account_id, audit_user=curr_user)
    return jsonify(
        {
            "success": success,
            "new_status": res if success else None,
            "message": str(res),
        }
    )


@admin_bp.route(
    "/accounts/reset-password",
    methods=["POST"],
)
@roles_required("ADMIN")
def reset_account_password():
    data = request.get_json() or {}
    account_id = data.get("account_id")
    new_password = data.get("new_password")
    curr_user = session.get("user", {})
    success, message = UserModel.reset_account_password(
        account_id, new_password, audit_user=curr_user
    )
    return jsonify({"success": success, "message": message})


# ==========================================
# 2. QUẢN LÝ BÁC SĨ (DANH SÁCH & CHI TIẾT 360)
# ==========================================
@admin_bp.route("/doctors")
def doctors():
    doctors_list = UserModel.get_all_doctors()
    departments = ClinicModel.get_all_departments(active_only=True)
    return render_template(
        "admin/doctors.html",
        active_page="admin_doctors",
        doctors=doctors_list,
        departments=departments,
    )


@admin_bp.route("/doctors/<int:doctor_id>")
def doctor_detail(doctor_id):
    doctor = UserModel.get_doctor_by_id(doctor_id)
    if not doctor:
        abort(404)
    return render_template(
        "admin/doctor_detail.html", active_page="admin_doctors", doctor=doctor
    )


# ==========================================
# 3. QUẢN LÝ & ĐĂNG BÀI VIẾT Y KHOA
# ==========================================
@admin_bp.route("/articles")
def articles():
    category = request.args.get("category", "ALL")
    status = request.args.get("status", "ALL")
    search = request.args.get("search", "")

    articles_list = ArticleModel.get_all_admin(
        category=category, search=search, status=status
    )
    categories = ArticleModel.get_categories()
    return render_template(
        "admin/articles.html",
        active_page="admin_articles",
        articles=articles_list,
        categories=categories,
        current_cat=category,
        current_status=status,
    )


@admin_bp.route(
    "/articles/create", methods=["GET", "POST"]
)
def article_create():
    if request.method == "POST":
        curr_user = session.get("user", {})
        data = request.form.to_dict()
        data["tac_gia_id"] = curr_user.get("staff_id") or 1

        success, res = ArticleModel.create(data)
        if success:
            return redirect(url_for("admin.articles"))
        return render_template(
            "admin/article_editor.html",
            active_page="admin_articles",
            error=res,
            categories=ArticleModel.get_categories(),
            article=data,
        )

    categories = ArticleModel.get_categories()
    return render_template(
        "admin/article_editor.html",
        active_page="admin_articles",
        categories=categories,
        article=None,
    )


@admin_bp.route(
    "/articles/edit/<int:article_id>",
    methods=["GET", "POST"]
)
def article_edit(article_id):
    article = ArticleModel.get_by_id(article_id)
    if not article:
        abort(404)

    if request.method == "POST":
        data = request.form.to_dict()
        success, res = ArticleModel.update(article_id, data)
        if success:
            return redirect(url_for("admin.articles"))
        return render_template(
            "admin/article_editor.html",
            active_page="admin_articles",
            error=res,
            categories=ArticleModel.get_categories(),
            article=article,
        )

    categories = ArticleModel.get_categories()
    return render_template(
        "admin/article_editor.html",
        active_page="admin_articles",
        categories=categories,
        article=article,
    )


@admin_bp.route(
    "/articles/delete/<int:article_id>",
    methods=["POST"]
)
def article_delete(article_id):
    success, msg = ArticleModel.delete(article_id)
    return jsonify({"success": success, "message": msg})
