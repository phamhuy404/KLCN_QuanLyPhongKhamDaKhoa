from flask import Blueprint, render_template, request, abort
from models.article_model import ArticleModel
from models.clinic_model import ClinicModel
from models.banner_model import BannerModel
from models.user_model import UserModel
from models.feedback_model import FeedbackModel
from core.database import get_db
import random
home_bp = Blueprint('home', __name__)

@home_bp.route('/')

@home_bp.route('/home')

def home():
    """Trang chủ cổng thông tin bệnh viện / phòng khám."""
    # Lấy ngẫu nhiên bài viết tin tức y tế từ CSDL
    articles = ArticleModel.get_all(limit=6, random_order=True)
    # Lấy ngẫu nhiên cẩm nang và hướng dẫn y tế từ CSDL
    handbooks = ArticleModel.get_handbooks(limit=3, random_order=True)
    stats = ClinicModel.get_dashboard_stats()
    banners = BannerModel.get_active()
    banner_list = list(banners) if banners else []
    banner_count = len(banner_list) if len(banner_list) > 0 else 1
    departments = ClinicModel.get_all_departments(active_only=True)
    # Hiển thị ngẫu nhiên các bác sĩ chuyên khoa thực tế từ CSDL
    raw_doctors = UserModel.get_all_doctors()
    doctors = list(raw_doctors) if raw_doctors else []
    random.shuffle(doctors)
    selected_doctors = doctors[:6]
    # Lấy ngẫu nhiên các phản hồi tích cực từ bệnh nhân trong CSDL
    all_positive = [f for f in FeedbackModel.get_all() if f.get('diem_danh_gia', 0) >= 4]
    random.shuffle(all_positive)
    feedbacks = all_positive[:4]
    return render_template(
        'home.html',
        articles=articles,
        handbooks=handbooks,
        stats=stats,
        banners=banners,
        banner_list=banner_list,
        banner_count=banner_count,
        departments=departments,
        doctors=selected_doctors,
        feedbacks=feedbacks
    )

@home_bp.route('/articles')

@home_bp.route('/tin-tuc')

def articles():
    """Trang cẩm nang y tế và danh sách tin tức sức khỏe."""
    active_category = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()
    all_articles = ArticleModel.get_all(category=active_category if active_category else None, search=search_query if search_query else None)
    categories = ArticleModel.get_categories()
    related_articles = ArticleModel.get_all(limit=4)
    # Xử lý danh mục và phân loại bài viết nổi bật hoàn toàn tại BackEnd
    active_category_name = None
    if active_category:
        for cat in categories:
            if cat.get('slug') == active_category:
                active_category_name = cat.get('name')
                break
        if not active_category_name:
            active_category_name = active_category
    has_filter = bool(active_category or search_query)
    featured = None
    remaining_articles = all_articles
    if not has_filter and len(all_articles) > 0:
        featured = all_articles[0]
        remaining_articles = all_articles[1:]
    return render_template(
        'articles.html',
        articles=all_articles,
        categories=categories,
        related_articles=related_articles,
        active_category=active_category,
        active_category_name=active_category_name,
        featured=featured,
        remaining_articles=remaining_articles,
        total_articles=len(all_articles),
        total_pages=1,
        current_page=1,
    )

@home_bp.route('/articles/<slug>')

def article_detail(slug):
    """Trang xem chi tiết một bài viết theo slug."""
    article = ArticleModel.get_by_slug(slug)
    if article is None:
        abort(404)
    all_arts = ArticleModel.get_all(limit=6)
    related_articles = [a for a in all_arts if a['id'] != article['id']][:3]
    sidebar_latest = [a for a in all_arts if a['id'] != article['id']][:5]
    return render_template(
        'article_detail.html',
        article=article,
        related_articles=related_articles,
        prev_article=None,
        next_article=None,
        categories=ArticleModel.get_categories(),
        sidebar_latest=sidebar_latest,
    )


@home_bp.route('/departments')
@home_bp.route('/chuyen-khoa')
def departments():
    """Trang danh sách toàn bộ các chuyên khoa y tế mũi nhọn."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai
        FROM chuyen_khoa
        WHERE trang_thai = 1
        ORDER BY id ASC
    """)
    depts = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang
        FROM phong_kham
        WHERE trang_thai = 1
        ORDER BY id ASC
    """)
    rooms = cursor.fetchall()
    rooms_by_dept = {}
    for r in rooms:
        rooms_by_dept.setdefault(r['chuyen_khoa_id'], []).append(dict(r))

    cursor.execute("""
        SELECT id, chuyen_khoa_id, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt
        FROM dich_vu
        WHERE trang_thai = 1
        ORDER BY id ASC
    """)
    services = cursor.fetchall()
    services_by_dept = {}
    for s in services:
        services_by_dept.setdefault(s['chuyen_khoa_id'], []).append(dict(s))
    conn.close()

    raw_doctors = UserModel.get_all_doctors()
    doctors_by_dept = {}
    for d in (raw_doctors or []):
        doctors_by_dept.setdefault(d.get('chuyen_khoa_id'), []).append(d)

    for dep in depts:
        dep_id = dep['id']
        dep['rooms'] = rooms_by_dept.get(dep_id, [])
        dep['doctors'] = doctors_by_dept.get(dep_id, [])
        dep['services'] = services_by_dept.get(dep_id, [])
        dep['room_count'] = len(dep['rooms'])
        dep['doctor_count'] = len(dep['doctors'])
        dep['service_count'] = len(dep['services'])
        dep['gia_kham_val'] = float(dep.get('gia_kham_mac_dinh') or 150000)

    return render_template(
        'departments.html',
        departments=depts,
        total_departments=len(depts)
    )

@home_bp.route('/doctors')
@home_bp.route('/doi-ngu-bac-si')
def doctors():
    """Trang danh sách đội ngũ y bác sĩ và nhân viên y tế."""
    raw_doctors = UserModel.get_all_doctors()
    doctors_list = list(raw_doctors) if raw_doctors else []

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nv.id, nv.ho_ten, nv.chuc_vu, nv.sdt, nv.email, v.ma_vai_tro, v.ten_vai_tro
        FROM nhan_vien nv
        JOIN tai_khoan tk ON nv.tai_khoan_id = tk.id
        JOIN vai_tro v ON tk.vai_tro_id = v.id
        WHERE v.ma_vai_tro IN ('LETAN', 'DUOCSI', 'KTV')
          AND nv.trang_thai = 1
          AND nv.ho_ten NOT LIKE '%Test%' AND nv.ho_ten NOT LIKE N'%Kiểm Thử%'
        ORDER BY v.id, nv.id
    """)
    other_staff = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Nhóm bác sĩ theo từng chuyên khoa
    departments_doctors = []
    dept_map = {}
    for d in doctors_list:
        ck_id = d.get('chuyen_khoa_id') or 0
        ck_name = d.get('ten_khoa') or 'Chuyên khoa khác'
        if ck_id not in dept_map:
            dept_obj = {
                'id': ck_id,
                'ten_khoa': ck_name,
                'doctors': []
            }
            dept_map[ck_id] = dept_obj
            departments_doctors.append(dept_obj)
        dept_map[ck_id]['doctors'].append(d)

    # Phân nhóm nhân viên y tế hỗ trợ
    support_staff = {
        'ktv': [s for s in other_staff if s['ma_vai_tro'] == 'KTV'],
        'duocsi': [s for s in other_staff if s['ma_vai_tro'] == 'DUOCSI'],
        'letan': [s for s in other_staff if s['ma_vai_tro'] == 'LETAN'],
    }

    return render_template(
        'doctors.html',
        departments_doctors=departments_doctors,
        support_staff=support_staff,
        total_doctors=len(doctors_list),
        total_staff=len(other_staff),
        total_personnel=len(doctors_list) + len(other_staff)
    )

@home_bp.route('/services')
@home_bp.route('/bang-gia')
@home_bp.route('/pricing')
def pricing():
    """Bảng giá dịch vụ khám chữa bệnh và viện phí niêm yết công khai."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dv.id, dv.chuyen_khoa_id, dv.ma_dich_vu, dv.ten_dich_vu, dv.loai_dich_vu,
               dv.don_gia, dv.bhyt_chi_tra_pt, dv.mo_ta, dv.trang_thai,
               ck.ten_khoa, ck.icon, ck.ma_khoa
        FROM dich_vu dv
        LEFT JOIN chuyen_khoa ck ON dv.chuyen_khoa_id = ck.id
        WHERE dv.trang_thai = 1
        ORDER BY COALESCE(ck.id, 999), dv.loai_dich_vu, dv.id
    """)
    services = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Nhóm dịch vụ theo chuyên khoa và loại khám
    departments_pricing = []
    departments_map = {}
    for s in services:
        don_gia = float(s.get('don_gia') or 0)
        bhyt_pt = int(s.get('bhyt_chi_tra_pt') or 0)
        tien_bhyt = don_gia * (bhyt_pt / 100.0)
        gia_sau_bhyt = don_gia - tien_bhyt
        s['don_gia_val'] = don_gia
        s['tien_bhyt_val'] = tien_bhyt
        s['gia_sau_bhyt_val'] = gia_sau_bhyt
        s['has_bhyt'] = bhyt_pt > 0

        ck_id = s.get('chuyen_khoa_id') or 0
        ck_name = s.get('ten_khoa') or 'Dịch Vụ Đa Khoa & Cận Lâm Sàng'
        ck_icon = s.get('icon') or 'fa-stethoscope'
        ck_ma = s.get('ma_khoa') or 'CHUNG'

        if ck_id not in departments_map:
            dept_obj = {
                'id': ck_id,
                'ten_khoa': ck_name,
                'ma_khoa': ck_ma,
                'icon': ck_icon,
                'groups': {},
                'services_count': 0
            }
            departments_map[ck_id] = dept_obj
            departments_pricing.append(dept_obj)

        dept_obj = departments_map[ck_id]
        dept_obj['services_count'] += 1
        loai = s.get('loai_dich_vu') or 'Khám bệnh'
        if loai not in dept_obj['groups']:
            dept_obj['groups'][loai] = []
        dept_obj['groups'][loai].append(s)

    total_services = len(services)
    bhyt_supported = sum(1 for s in services if s['has_bhyt'])

    return render_template(
        'pricing.html',
        departments_pricing=departments_pricing,
        total_services=total_services,
        bhyt_supported=bhyt_supported,
        dept_count=len(departments_pricing)
    )
