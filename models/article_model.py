from core.database import get_db

class ArticleModel:
    """Model quản lý tin tức y tế, cẩm nang sức khỏe từ cơ sở dữ liệu."""

    _CATEGORIES = [
        {"slug": "tim-mach",           "name": "Tim mạch",           "icon": "fa-solid fa-heart"},
        {"slug": "nhi-khoa",           "name": "Nhi khoa",           "icon": "fa-solid fa-baby"},
        {"slug": "da-lieu",            "name": "Da liễu",            "icon": "fa-solid fa-hand-dots"},
        {"slug": "noi-tiet",           "name": "Nội tiết",           "icon": "fa-solid fa-vial"},
        {"slug": "xuong-khop",         "name": "Xương khớp",         "icon": "fa-solid fa-bone"},
        {"slug": "suc-khoe-tong-quat", "name": "Sức khoẻ tổng quát", "icon": "fa-solid fa-shield-heart"},
        {"slug": "tam-than",           "name": "Sức khoẻ tâm thần",  "icon": "fa-solid fa-brain"},
    ]

    @classmethod
    def get_categories(cls):
        return cls._CATEGORIES

    @staticmethod
    def get_all(limit=None, category=None, search=None):
        """Lấy danh sách bài viết từ CSDL kèm lọc theo danh mục và tìm kiếm."""
        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT bv.*, nv.ho_ten AS tac_gia, nv.chuc_vu AS tac_gia_chuc_vu
            FROM bai_viet bv
            LEFT JOIN nhan_vien nv ON bv.tac_gia_id = nv.id
            WHERE bv.trang_thai = 1
        '''
        params = []

        if category:
            sql += ' AND (bv.danh_muc = ? OR bv.danh_muc LIKE ?)'
            params.extend([category, f'%{category}%'])

        if search:
            sql += ' AND (bv.tieu_de LIKE ? OR bv.tom_tat LIKE ? OR bv.noi_dung LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

        sql += ' ORDER BY bv.ngay_dang DESC'

        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        articles = []
        for r in rows:
            articles.append({
                'id': r['id'],
                'slug': r['slug'],
                'title': r['tieu_de'],
                'summary': r.get('tom_tat') or '',
                'content': r.get('noi_dung') or '',
                'category_slug': 'suc-khoe-tong-quat',
                'category_name': r.get('danh_muc') or 'Cẩm Nang Y Tế',
                'category_icon': 'fa-solid fa-shield-heart',
                'image': r.get('hinh_anh') or '',
                'published_at': str(r.get('ngay_dang') or '')[:10],
                'read_time': 5,
                'views': r.get('luot_xem', 0),
                'author': r.get('tac_gia') or 'H2T Healthcare',
                'author_title': r.get('tac_gia_chuc_vu') or 'Ban Biên Tập Y Khoa',
                'tags': ['sức khoẻ', 'y tế', 'phòng khám']
            })

        if limit and isinstance(limit, int):
            return articles[:limit]
        return articles

    @staticmethod
    def get_by_slug(slug):
        """Lấy chi tiết một bài viết theo slug và tăng lượt xem."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT bv.*, nv.ho_ten AS tac_gia, nv.chuc_vu AS tac_gia_chuc_vu
            FROM bai_viet bv
            LEFT JOIN nhan_vien nv ON bv.tac_gia_id = nv.id
            WHERE bv.slug = ? AND bv.trang_thai = 1
        ''', (slug,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Tăng lượt xem
        cursor.execute('UPDATE bai_viet SET luot_xem = luot_xem + 1 WHERE id = ?', (row['id'],))
        conn.commit()
        conn.close()

        r = dict(row)
        return {
            'id': r['id'],
            'slug': r['slug'],
            'title': r['tieu_de'],
            'summary': r.get('tom_tat') or '',
            'content': r.get('noi_dung') or '',
            'category_slug': 'suc-khoe-tong-quat',
            'category_name': r.get('danh_muc') or 'Cẩm Nang Y Tế',
            'category_icon': 'fa-solid fa-shield-heart',
            'image': r.get('hinh_anh') or '',
            'published_at': str(r.get('ngay_dang') or '')[:10],
            'read_time': 5,
            'views': r.get('luot_xem', 0) + 1,
            'author': r.get('tac_gia') or 'H2T Healthcare',
            'author_title': r.get('tac_gia_chuc_vu') or 'Ban Biên Tập Y Khoa',
            'tags': ['sức khoẻ', 'y tế', 'phòng khám']
        }
