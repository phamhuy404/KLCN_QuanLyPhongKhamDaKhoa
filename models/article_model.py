import unicodedata
import re
from core.database import get_db

def remove_vietnamese_tones(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[ÌÍỊỈĨ]', 'I', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[ỲÝỴỶỸ]', 'Y', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()

def fuzzy_match_article(query, text):
    if not query or not query.strip():
        return True
    q_clean = remove_vietnamese_tones(query).strip()
    t_clean = remove_vietnamese_tones(text).strip()
    if q_clean in t_clean:
        return True
    q_tokens = [tok for tok in re.split(r'[^a-z0-9]+', q_clean) if tok]
    t_words = [w for w in re.split(r'[^a-z0-9]+', t_clean) if w]
    if not q_tokens:
        return True
    for q_tok in q_tokens:
        matched = False
        for t_word in t_words:
            if q_tok in t_word or t_word.startswith(q_tok):
                matched = True
                break
        if not matched:
            return False
    return True

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
        """Lấy danh sách bài viết từ CSDL kèm lọc theo danh mục và tìm kiếm gần đúng."""
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

        sql += ' ORDER BY bv.ngay_dang DESC'

        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Áp dụng tìm kiếm gần đúng nếu có search
        if search and search.strip():
            filtered_rows = []
            for r in rows:
                full_text = f"{r.get('tieu_de', '')} {r.get('tom_tat', '')} {r.get('noi_dung', '')} {r.get('danh_muc', '')} {r.get('tac_gia', '')}"
                if fuzzy_match_article(search, full_text):
                    filtered_rows.append(r)
            rows = filtered_rows

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
