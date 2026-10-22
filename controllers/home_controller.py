from flask import Blueprint, render_template, request, abort
from models.article_model import ArticleModel
from models.clinic_model import ClinicModel
from models.banner_model import BannerModel
from models.user_model import UserModel
from models.feedback_model import FeedbackModel

import random

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@home_bp.route('/home')
def home():
    """Trang chủ cổng thông tin bệnh viện / phòng khám."""
    articles = ArticleModel.get_all(limit=8)
    stats = ClinicModel.get_dashboard_stats()
    banners = BannerModel.get_active()
    banner_list = list(banners) if banners else []
    banner_count = len(banner_list) if len(banner_list) > 0 else 1

    departments = ClinicModel.get_all_departments(active_only=True)
    
    # Hiển thị ngẫu nhiên (random) các tài khoản bác sĩ đang hoạt động
    raw_doctors = UserModel.get_all_doctors()
    doctors = list(raw_doctors) if raw_doctors else []
    random.shuffle(doctors)
    feedbacks = [f for f in FeedbackModel.get_all() if f.get('diem_danh_gia', 0) >= 4][:4]
    return render_template(
        'home.html',
        articles=articles,
        stats=stats,
        banners=banners,
        banner_list=banner_list,
        banner_count=banner_count,
        departments=departments,
        doctors=doctors,
        feedbacks=feedbacks
    )

@home_bp.route('/articles')
@home_bp.route('/tin-tuc')
def articles():
    """Trang cẩm nang y tế & danh sách tin tức sức khỏe."""
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
