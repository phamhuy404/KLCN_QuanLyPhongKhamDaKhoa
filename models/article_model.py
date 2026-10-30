import unicodedata
import re
from datetime import datetime
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
        {"slug": "cam-nang-y-te",       "name": "Cẩm Nang Y Tế",       "icon": "fa-solid fa-book-medical"},
        {"slug": "huong-dan-kham-benh", "name": "Hướng Dẫn Khám Bệnh", "icon": "fa-solid fa-notes-medical"},
        {"slug": "tin-tuc-phong-kham",  "name": "Tin Tức Phòng Khám",  "icon": "fa-solid fa-hospital"},
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
        """Lấy danh sách chuyên mục kèm số lượng bài viết thực tế trong CSDL."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT danh_muc, COUNT(*) AS cnt
                FROM bai_viet
                WHERE trang_thai = 1
                GROUP BY danh_muc
            ''')
            counts = {r['danh_muc']: r['cnt'] for r in cursor.fetchall()}
            conn.close()
        except Exception:
            counts = {}
        res = []
        for cat in cls._CATEGORIES:
            c = dict(cat)
            c['count'] = counts.get(cat['name'], 0)
            res.append(c)
        return res

    @staticmethod

    def get_all(limit=None, category=None, search=None, random_order=False):
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
            cat_map = {
                'cam-nang-y-te': 'Cẩm Nang Y Tế',
                'huong-dan-kham-benh': 'Hướng Dẫn Khám Bệnh',
                'tin-tuc-phong-kham': 'Tin Tức Phòng Khám',
                'tim-mach': 'Tim mạch',
                'nhi-khoa': 'Nhi khoa',
                'da-lieu': 'Da liễu',
                'noi-tiet': 'Nội tiết',
                'xuong-khop': 'Xương khớp',
                'suc-khoe-tong-quat': 'Sức khoẻ tổng quát',
                'tam-than': 'Sức khoẻ tâm thần'
            }
            resolved_cat = cat_map.get(category, category)
            sql += ' AND (bv.danh_muc = ? OR bv.danh_muc LIKE ?)'
            params.extend([resolved_cat, f'%{resolved_cat}%'])
        if random_order:
            sql += ' ORDER BY NEWID()'
        else:
            sql += ' ORDER BY bv.ngay_dang DESC'
        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if search and search.strip():
            filtered_rows = []
            for r in rows:
                full_text = f"{r.get('tieu_de', '')} {r.get('tom_tat', '')} {r.get('noi_dung', '')} {r.get('danh_muc', '')} {r.get('tac_gia', '')}"
                if fuzzy_match_article(search, full_text):
                    filtered_rows.append(r)
            rows = filtered_rows
        articles = []
        for r in rows:
            cat_name = r.get('danh_muc') or 'Cẩm Nang Y Tế'
            cat_icon = 'fa-solid fa-book-medical' if 'Cẩm Nang' in cat_name else (
                'fa-solid fa-notes-medical' if 'Hướng Dẫn' in cat_name else (
                    'fa-solid fa-heart' if 'Tim' in cat_name else (
                        'fa-solid fa-baby' if 'Nhi' in cat_name else (
                            'fa-solid fa-bone' if 'Xương' in cat_name else 'fa-solid fa-newspaper'
                        )
                    )
                )
            )
            cat_slug = 'cam-nang-y-te' if 'Cẩm Nang' in cat_name else remove_vietnamese_tones(cat_name).replace(' ', '-')
            articles.append({
                'id': r['id'],
                'slug': r['slug'],
                'title': r['tieu_de'],
                'summary': r.get('tom_tat') or '',
                'content': r.get('noi_dung') or '',
                'category_slug': cat_slug,
                'category_name': cat_name,
                'category_icon': cat_icon,
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

    def get_handbooks(limit=None, random_order=True):
        """Lấy danh sách cẩm nang và hướng dẫn y tế chuẩn từ CSDL."""
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT bv.*, nv.ho_ten AS tac_gia, nv.chuc_vu AS tac_gia_chuc_vu
            FROM bai_viet bv
            LEFT JOIN nhan_vien nv ON bv.tac_gia_id = nv.id
            WHERE bv.trang_thai = 1
              AND (bv.danh_muc LIKE N'%Cẩm Nang%' OR bv.danh_muc LIKE N'%Hướng Dẫn%')
        '''
        if random_order:
            sql += ' ORDER BY NEWID()'
        else:
            sql += ' ORDER BY bv.ngay_dang DESC'
        cursor.execute(sql)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        handbooks = []
        for r in rows:
            cat_name = r.get('danh_muc') or 'Cẩm Nang Y Tế'
            cat_icon = 'fa-solid fa-notes-medical' if 'Hướng Dẫn' in cat_name else 'fa-solid fa-book-medical'
            handbooks.append({
                'id': r['id'],
                'slug': r['slug'],
                'title': r['tieu_de'],
                'summary': r.get('tom_tat') or '',
                'content': r.get('noi_dung') or '',
                'category_slug': 'cam-nang-y-te',
                'category_name': cat_name,
                'category_icon': cat_icon,
                'image': r.get('hinh_anh') or '',
                'published_at': str(r.get('ngay_dang') or '')[:10],
                'read_time': 5,
                'views': r.get('luot_xem', 0),
                'author': r.get('tac_gia') or 'H2T Healthcare',
                'author_title': r.get('tac_gia_chuc_vu') or 'Ban Biên Tập Y Khoa',
            })
        if limit and isinstance(limit, int):
            return handbooks[:limit]
        return handbooks

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

    @staticmethod

    def get_by_id(article_id):
        """Lấy thông tin chi tiết một bài viết theo ID phục vụ trang sửa bài."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bv.*, nv.ho_ten AS tac_gia, nv.chuc_vu AS tac_gia_chuc_vu
            FROM bai_viet bv
            LEFT JOIN nhan_vien nv ON bv.tac_gia_id = nv.id
            WHERE bv.id = ?
        ''', (article_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod

    def get_all_admin(category=None, search=None, status='ALL', group=None):
        """Lấy tất cả bài viết cho trang Quản trị Admin có lọc theo phân nhóm (cẩm nang / tin tức)."""
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT bv.*, nv.ho_ten AS tac_gia, nv.chuc_vu AS tac_gia_chuc_vu
            FROM bai_viet bv
            LEFT JOIN nhan_vien nv ON bv.tac_gia_id = nv.id
            WHERE 1=1
        '''
        params = []
        if status != 'ALL':
            sql += ' AND bv.trang_thai = ?'
            params.append(int(status))
        if group == 'cam_nang':
            sql += " AND (bv.danh_muc LIKE N'%Cẩm Nang%' OR bv.danh_muc LIKE N'%Hướng Dẫn%')"
        elif group == 'tin_tuc':
            sql += " AND (bv.danh_muc NOT LIKE N'%Cẩm Nang%' AND bv.danh_muc NOT LIKE N'%Hướng Dẫn%')"
        if category and category != 'ALL':
            sql += ' AND (bv.danh_muc = ? OR bv.danh_muc LIKE ?)'
            params.extend([category, f'%{category}%'])
        if search and search.strip():
            s = f"%{search.strip()}%"
            sql += ' AND (bv.tieu_de LIKE ? OR bv.tom_tat LIKE ? OR nv.ho_ten LIKE ?)'
            params.extend([s, s, s])
        sql += ' ORDER BY bv.id DESC'
        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod

    def create(data):
        """Thêm bài viết mới vào CSDL."""
        tieu_de = data.get('tieu_de', '').strip()
        slug = data.get('slug', '').strip()
        tom_tat = data.get('tom_tat', '').strip()
        noi_dung = data.get('noi_dung', '').strip()
        danh_muc = data.get('danh_muc', 'Sức khoẻ tổng quát').strip()
        hinh_anh = data.get('hinh_anh', '').strip()
        tac_gia_id = data.get('tac_gia_id') or 1
        trang_thai = int(data.get('trang_thai', 1))
        if not tieu_de or not noi_dung:
            return False, 'Tiêu đề và nội dung bài viết không được để trống!'
        if not slug:
            slug = remove_vietnamese_tones(tieu_de)
            slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
            slug = f"{slug}-{int(datetime.now().timestamp())}"
        conn = get_db()
        cursor = conn.cursor()
        try:
            ngay_dang = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO bai_viet (tieu_de, slug, tom_tat, noi_dung, danh_muc, hinh_anh, ngay_dang, luot_xem, tac_gia_id, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            ''', (tieu_de, slug, tom_tat, noi_dung, danh_muc, hinh_anh, ngay_dang, tac_gia_id, trang_thai))
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True, new_id
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi lưu bài viết: {str(e)}'

    @staticmethod

    def update(article_id, data):
        """Cập nhật bài viết."""
        tieu_de = data.get('tieu_de', '').strip()
        tom_tat = data.get('tom_tat', '').strip()
        noi_dung = data.get('noi_dung', '').strip()
        danh_muc = data.get('danh_muc', '').strip()
        hinh_anh = data.get('hinh_anh', '').strip()
        trang_thai = int(data.get('trang_thai', 1))
        if not tieu_de or not noi_dung:
            return False, 'Tiêu đề và nội dung không được để trống!'
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE bai_viet
                SET tieu_de = ?, tom_tat = ?, noi_dung = ?, danh_muc = ?, hinh_anh = ?, trang_thai = ?
                WHERE id = ?
            ''', (tieu_de, tom_tat, noi_dung, danh_muc, hinh_anh, trang_thai, article_id))
            conn.commit()
            conn.close()
            return True, 'Cập nhật bài viết thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi cập nhật bài viết: {str(e)}'

    @staticmethod

    def delete(article_id):
        """Xóa bài viết."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM bai_viet WHERE id = ?', (article_id,))
            conn.commit()
            conn.close()
            return True, 'Đã xóa bài viết thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi xóa bài viết: {str(e)}'
