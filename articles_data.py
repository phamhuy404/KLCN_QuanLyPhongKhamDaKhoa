# -*- coding: utf-8 -*-
"""
articles_data.py - Dữ liệu mẫu + hàm hỗ trợ cho mục "Tin tức & Bài viết Y khoa".

Đặt file này CÙNG THƯ MỤC với app.py.
Sau này khi chuyển sang database thật, chỉ cần sửa các hàm ở cuối file
(get_categories, filter_articles, ...) mà không cần đụng vào app.py.
"""

# ─── Danh mục ────────────────────────────────────────────────────────────────
# slug phải trùng với các class .badge-<slug> trong CSS của template
_CATEGORIES = [
    {"slug": "tim-mach",           "name": "Tim mạch",           "icon": "fa-solid fa-heart"},
    {"slug": "nhi-khoa",           "name": "Nhi khoa",           "icon": "fa-solid fa-baby"},
    {"slug": "da-lieu",            "name": "Da liễu",            "icon": "fa-solid fa-hand-dots"},
    {"slug": "noi-tiet",           "name": "Nội tiết",           "icon": "fa-solid fa-vial"},
    {"slug": "xuong-khop",         "name": "Xương khớp",         "icon": "fa-solid fa-bone"},
    {"slug": "suc-khoe-tong-quat", "name": "Sức khoẻ tổng quát", "icon": "fa-solid fa-shield-heart"},
    {"slug": "tam-than",           "name": "Sức khoẻ tâm thần",  "icon": "fa-solid fa-brain"},
]
_CAT_BY_SLUG = {c["slug"]: c for c in _CATEGORIES}


def _a(id, slug, title, summary, content, cat, date, read_time, views, author, author_title, tags):
    """Tạo 1 bài viết; tự điền category_name / category_icon từ slug danh mục."""
    c = _CAT_BY_SLUG[cat]
    return {
        "id": id, "slug": slug, "title": title, "summary": summary, "content": content,
        "category_slug": cat, "category_name": c["name"], "category_icon": c["icon"],
        "image": "",            # tên file trong static/img/articles/ (để trống = ảnh mặc định)
        "published_at": date, "read_time": read_time, "views": views,
        "author": author, "author_title": author_title, "tags": tags,
    }


# ─── Bài viết mẫu (mới nhất đứng trước) ──────────────────────────────────────
ARTICLES_DATA = [
    _a(1, "phong-ngua-benh-tim-mach-hieu-qua",
       "10 Cách Phòng Ngừa Bệnh Tim Mạch Hiệu Quả Bạn Nên Biết",
       "Bệnh tim mạch là nguyên nhân tử vong hàng đầu trên thế giới, nhưng phần lớn ca bệnh có thể phòng ngừa nếu chú ý lối sống và dinh dưỡng.",
       """<h2>1. Duy trì cân nặng hợp lý</h2>
<p>Béo phì là yếu tố nguy cơ chính của bệnh tim mạch. Chỉ số BMI lý tưởng nên dưới 25.</p>
<h2>2. Tập thể dục đều đặn</h2>
<p>Tối thiểu 30 phút mỗi ngày, 5 ngày một tuần. Đi bộ nhanh, bơi lội, đạp xe rất có lợi cho tim.</p>
<h2>3. Chế độ ăn lành mạnh</h2>
<ul><li>Tăng rau xanh, trái cây, ngũ cốc nguyên hạt</li><li>Hạn chế muối (dưới 5g/ngày)</li><li>Giảm chất béo bão hòa</li></ul>
<h2>4. Không hút thuốc lá</h2>
<p>Ngừng hút thuốc giúp giảm đáng kể nguy cơ nhồi máu cơ tim chỉ sau 1 năm.</p>""",
       "tim-mach", "01/10/2026", 5, 234, "BS. Nguyễn Văn An", "Bác sĩ Chuyên khoa Tim mạch",
       ["tim mạch", "phòng bệnh", "sức khoẻ"]),

    _a(2, "dieu-tri-cao-huyet-ap",
       "Cao Huyết Áp: Nguyên Nhân, Triệu Chứng và Hướng Điều Trị",
       "Cao huyết áp là tình trạng áp lực máu trong động mạch tăng kéo dài, gây tổn thương tim, não và thận nếu không được kiểm soát.",
       """<h2>Huyết áp bình thường là bao nhiêu?</h2>
<p>Dưới 120/80 mmHg. Từ 130/80 mmHg trở lên được xem là tăng huyết áp.</p>
<h2>Nguyên nhân</h2>
<ul><li>Ăn nhiều muối</li><li>Thiếu vận động, thừa cân</li><li>Căng thẳng kéo dài</li><li>Di truyền</li></ul>
<h2>Điều trị</h2>
<p>Gồm thay đổi lối sống và dùng thuốc theo chỉ định của bác sĩ. Không tự ý dừng thuốc.</p>""",
       "tim-mach", "28/09/2026", 6, 178, "BS. Trần Thị Lan", "Bác sĩ Nội Tim mạch",
       ["cao huyết áp", "tim mạch", "điều trị"]),

    _a(3, "che-do-dinh-duong-cho-tre-em",
       "Chế Độ Dinh Dưỡng Chuẩn Cho Trẻ Em Từ 1-10 Tuổi",
       "Dinh dưỡng quyết định sự phát triển thể chất và trí tuệ của trẻ. Hướng dẫn thực đơn cân bằng cho từng độ tuổi.",
       """<h2>Trẻ 1-3 tuổi</h2><p>Ăn đa dạng ngũ cốc, rau củ, thịt, cá, trứng và sữa.</p>
<h2>Trẻ 4-6 tuổi</h2><p>Khuyến khích ăn rau xanh, hạn chế đồ ngọt và thức ăn nhanh.</p>
<h2>Trẻ 7-10 tuổi</h2><p>Bữa sáng đặc biệt quan trọng cho khả năng tập trung học tập.</p>""",
       "nhi-khoa", "25/09/2026", 4, 312, "BS. Lê Minh Tú", "Bác sĩ Nhi khoa",
       ["nhi khoa", "dinh dưỡng", "trẻ em"]),

    _a(4, "cham-soc-da-mua-kho",
       "Bí Quyết Chăm Sóc Da Mùa Khô: Giữ Da Ẩm Và Khoẻ Mạnh",
       "Thời tiết hanh khô khiến da mất nước, bong tróc và ngứa. Cách chăm sóc da đúng từ chuyên gia da liễu.",
       """<h2>Vì sao da khô vào mùa hanh?</h2><p>Độ ẩm thấp làm da mất nước nhanh; tắm nước nóng làm hỏng hàng rào bảo vệ da.</p>
<h2>Nguyên tắc chăm sóc</h2>
<ul><li>Dưỡng ẩm ngay sau khi tắm</li><li>Chọn kem có ceramide, hyaluronic acid</li><li>Uống đủ nước</li><li>Tránh tắm nước quá nóng</li></ul>""",
       "da-lieu", "20/09/2026", 3, 195, "BS. Phạm Thu Hương", "Bác sĩ Da liễu",
       ["da liễu", "chăm sóc da", "mùa khô"]),

    _a(5, "phong-ngua-benh-xuong-khop",
       "Phòng Ngừa Viêm Khớp: Bảo Vệ Xương Khớp Từ Sớm",
       "Viêm khớp không chỉ là bệnh của người cao tuổi. Ít vận động, thừa cân và thiếu canxi gây thoái hoá khớp sớm.",
       """<h2>Bệnh xương khớp thường gặp</h2><p>Thoái hoá khớp, viêm khớp dạng thấp, gout và loãng xương.</p>
<h2>Phòng ngừa</h2>
<p>Tập nhẹ nhàng đều đặn (bơi, yoga, đi bộ), bổ sung canxi và vitamin D, kiểm soát cân nặng, giữ tư thế đúng khi làm việc.</p>""",
       "xuong-khop", "15/09/2026", 5, 267, "BS. Nguyễn Đức Thắng", "Bác sĩ Cơ xương khớp",
       ["xương khớp", "viêm khớp", "phòng bệnh"]),

    _a(6, "quan-ly-stress-hieu-qua",
       "Quản Lý Căng Thẳng (Stress) Hiệu Quả: Kỹ Thuật Thư Giãn",
       "Căng thẳng mãn tính ảnh hưởng nghiêm trọng đến sức khoẻ thể chất và tinh thần. Các kỹ thuật thư giãn giúp kiểm soát stress.",
       """<h2>Stress ảnh hưởng cơ thể thế nào?</h2><p>Kéo dài có thể gây mất ngủ, tăng huyết áp, suy giảm miễn dịch.</p>
<h2>Kỹ thuật thở 4-7-8</h2><p>Hít vào 4 giây, giữ hơi 7 giây, thở ra 8 giây. Lặp lại 4 lần.</p>
<h2>Thiền chánh niệm</h2><p>10-15 phút mỗi ngày giúp cải thiện giấc ngủ và giảm căng thẳng.</p>""",
       "tam-than", "10/09/2026", 4, 421, "ThS. Vũ Thị Mai", "Chuyên viên Tâm lý lâm sàng",
       ["stress", "tâm thần", "thư giãn"]),

    _a(7, "suc-khoe-tong-quat-hang-nam",
       "Vì Sao Nên Khám Sức Khoẻ Tổng Quát Định Kỳ Mỗi Năm?",
       "Khám định kỳ giúp phát hiện bệnh sớm, theo dõi chỉ số sinh lý và điều chỉnh lối sống trước khi bệnh xuất hiện.",
       """<h2>Lợi ích</h2>
<ul><li>Phát hiện bệnh ở giai đoạn sớm</li><li>Theo dõi huyết áp, đường huyết, mỡ máu</li><li>Tư vấn phòng bệnh cá nhân hoá</li></ul>
<h2>Nên khám những gì?</h2>
<p>Xét nghiệm máu, chức năng gan-thận, siêu âm bụng, điện tâm đồ, đo huyết áp và tư vấn dinh dưỡng.</p>""",
       "suc-khoe-tong-quat", "05/09/2026", 3, 389, "BS. CK2 Hoàng Văn Bình", "Trưởng khoa Nội tổng hợp",
       ["khám sức khoẻ", "định kỳ", "phòng bệnh"]),

    _a(8, "tieu-duong-type-2-va-che-do-an",
       "Tiểu Đường Tuýp 2: Chế Độ Ăn Và Lối Sống Kiểm Soát Đường Huyết",
       "Người tiểu đường tuýp 2 vẫn sống khoẻ nếu ăn đúng và luyện tập đều đặn.",
       """<h2>Chế độ ăn</h2><p>Ưu tiên thực phẩm GI thấp: rau xanh, đậu, ngũ cốc nguyên hạt. Hạn chế cơm trắng, đồ ngọt, nước ngọt có ga.</p>
<h2>Tập luyện</h2><p>Đi bộ 30 phút sau bữa ăn giúp kiểm soát đường huyết.</p>
<h2>Theo dõi tại nhà</h2><p>Đo đường huyết trước ăn và 2 giờ sau ăn theo hướng dẫn của bác sĩ.</p>""",
       "noi-tiet", "01/09/2026", 6, 503, "BS. Nguyễn Thị Phương", "Bác sĩ Nội tiết",
       ["tiểu đường", "nội tiết", "đường huyết"]),
]


# ─── Hàm hỗ trợ (app.py chỉ gọi các hàm này) ─────────────────────────────────
def get_categories():
    """Danh mục kèm số bài thực tế (cat.count dùng trong template)."""
    return [
        {**c, "count": sum(1 for a in ARTICLES_DATA if a["category_slug"] == c["slug"])}
        for c in _CATEGORIES
    ]


def filter_articles(category="", search=""):
    """Lọc theo chuyên mục và/hoặc từ khoá (tiêu đề, tóm tắt, tag)."""
    result = ARTICLES_DATA[:]
    if category:
        result = [a for a in result if a["category_slug"] == category]
    kw = search.strip().lower()
    if kw:
        result = [
            a for a in result
            if kw in a["title"].lower()
            or kw in a["summary"].lower()
            or any(kw in t.lower() for t in a["tags"])
        ]
    return result


def get_sidebar_related(category=""):
    """Sidebar trang danh sách: cùng chuyên mục nếu đang lọc, không thì xem nhiều nhất."""
    if category:
        return [a for a in ARTICLES_DATA if a["category_slug"] == category][:4]
    return sorted(ARTICLES_DATA, key=lambda a: a["views"], reverse=True)[:4]


def get_article_by_slug(slug):
    return next((a for a in ARTICLES_DATA if a["slug"] == slug), None)


def get_related_for(article, limit=3):
    """Bài liên quan cuối trang chi tiết: cùng chuyên mục, thiếu thì bù bài khác."""
    same = [a for a in ARTICLES_DATA
            if a["category_slug"] == article["category_slug"] and a["id"] != article["id"]]
    if len(same) < limit:
        extra = [a for a in ARTICLES_DATA if a["id"] != article["id"] and a not in same]
        same += extra[: limit - len(same)]
    return same[:limit]


def get_prev_next(article):
    """Bài trước / bài sau theo thứ tự trong danh sách."""
    i = ARTICLES_DATA.index(article)
    prev_a = ARTICLES_DATA[i - 1] if i > 0 else None
    next_a = ARTICLES_DATA[i + 1] if i < len(ARTICLES_DATA) - 1 else None
    return prev_a, next_a


def get_latest(exclude_id=None, limit=4):
    items = [a for a in sorted(ARTICLES_DATA, key=lambda a: a["id"]) if a["id"] != exclude_id]
    return items[:limit]