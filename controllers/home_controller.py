from flask import Blueprint, render_template, request, abort
from models.article_model import ArticleModel
from models.clinic_model import ClinicModel
from models.banner_model import BannerModel

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@home_bp.route('/home')
def home():
    """Trang chủ cổng thông tin bệnh viện / phòng khám."""
    articles = ArticleModel.get_all(limit=5)
    stats = ClinicModel.get_dashboard_stats()
    banners = BannerModel.get_active()
    return render_template('home.html', articles=articles, stats=stats, banners=banners)

@home_bp.route('/articles')
@home_bp.route('/tin-tuc')
def articles():
    """Trang cẩm nang y tế & danh sách tin tức sức khỏe."""
    active_category = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()

    all_articles = ArticleModel.get_all(category=active_category if active_category else None, search=search_query if search_query else None)
    categories = ArticleModel.get_categories()
    related_articles = ArticleModel.get_all(limit=4)

    return render_template(
        'articles.html',
        articles=all_articles,
        categories=categories,
        related_articles=related_articles,
        active_category=active_category,
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
