from core.database import get_db
from core.image_service import save_and_compress_image, delete_uploaded_image

class BannerModel:
    """Model quản lý các banner quảng bá trên trang chủ phòng khám."""

    @staticmethod
    def get_all(status=None):
        """Lấy toàn bộ danh sách banner theo thứ tự ưu tiên."""
        conn = get_db()
        cursor = conn.cursor()
        sql = 'SELECT * FROM banner'
        params = []

        if status == 'ACTIVE':
            sql += ' WHERE trang_thai = 1'
        elif status == 'INACTIVE':
            sql += ' WHERE trang_thai = 0'

        sql += ' ORDER BY thu_tu ASC, id ASC'
        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_active():
        """Lấy các banner đang kích hoạt để hiển thị trang chủ."""
        return BannerModel.get_all(status='ACTIVE')

    @staticmethod
    def get_by_id(banner_id):
        """Lấy thông tin chi tiết một banner theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM banner WHERE id = ?', (banner_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create(data, image_file=None):
        """Tạo banner mới hỗ trợ upload ảnh nén WebP hoặc nhập URL trực tiếp."""
        tieu_de = (data.get('tieu_de') or '').strip()
        if not tieu_de:
            return False, 'Tiêu đề banner là bắt buộc.'

        hinh_anh = (data.get('hinh_anh') or '').strip()

        # Nhận diện và xử lý mọi nguồn ảnh (file máy tính, URL mạng, data URI)
        from core.image_service import process_image_input
        source = image_file if (image_file and getattr(image_file, 'filename', None)) else hinh_anh
        if source:
            web_path, err = process_image_input(source, category='banners', quality=82)
            if err and image_file:
                return False, err
            if web_path:
                hinh_anh = web_path

        if not hinh_anh:
            hinh_anh = 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1600'

        phu_de = (data.get('phu_de') or '').strip()
        mo_ta = (data.get('mo_ta') or '').strip()
        link_lien_ket = (data.get('link_lien_ket') or '/booking').strip()
        text_nut = (data.get('text_nut') or 'Đăng ký khám ngay').strip()
        
        try:
            thu_tu = int(data.get('thu_tu') or 0)
        except (ValueError, TypeError):
            thu_tu = 0

        trang_thai = 1 if str(data.get('trang_thai', '1')) in ['1', 'true', 'True'] else 0

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO banner (tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai))
            conn.commit()
            conn.close()
            return True, 'Đã tạo banner mới thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi tạo banner: {str(e)}'

    @staticmethod
    def update(banner_id, data, image_file=None):
        """Cập nhật thông tin banner."""
        banner = BannerModel.get_by_id(banner_id)
        if not banner:
            return False, 'Banner không tồn tại.'

        tieu_de = (data.get('tieu_de') or '').strip()
        if not tieu_de:
            return False, 'Tiêu đề banner là bắt buộc.'

        hinh_anh = (data.get('hinh_anh') or banner.get('hinh_anh') or '').strip()

        # Nhận diện và xử lý mọi nguồn ảnh khi chỉnh sửa
        from core.image_service import process_image_input
        source = image_file if (image_file and getattr(image_file, 'filename', None)) else data.get('hinh_anh')
        if source and source != banner.get('hinh_anh'):
            web_path, err = process_image_input(source, category='banners', quality=82)
            if err and image_file:
                return False, err
            if web_path:
                if banner.get('hinh_anh') != web_path:
                    delete_uploaded_image(banner.get('hinh_anh'))
                hinh_anh = web_path


        phu_de = (data.get('phu_de') or '').strip()
        mo_ta = (data.get('mo_ta') or '').strip()
        link_lien_ket = (data.get('link_lien_ket') or '/booking').strip()
        text_nut = (data.get('text_nut') or 'Đăng ký khám ngay').strip()

        try:
            thu_tu = int(data.get('thu_tu') or 0)
        except (ValueError, TypeError):
            thu_tu = 0

        trang_thai = 1 if str(data.get('trang_thai', '1')) in ['1', 'true', 'True'] else 0

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE banner 
                SET tieu_de = ?, phu_de = ?, mo_ta = ?, hinh_anh = ?, link_lien_ket = ?, text_nut = ?, thu_tu = ?, trang_thai = ?
                WHERE id = ?
            ''', (tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai, banner_id))
            conn.commit()
            conn.close()
            return True, 'Đã cập nhật banner thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi cập nhật banner: {str(e)}'

    @staticmethod
    def delete(banner_id):
        """Xóa banner và xóa file ảnh cục bộ nếu có."""
        banner = BannerModel.get_by_id(banner_id)
        if not banner:
            return False, 'Banner không tồn tại.'

        delete_uploaded_image(banner.get('hinh_anh'))

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM banner WHERE id = ?', (banner_id,))
            conn.commit()
            conn.close()
            return True, 'Đã xóa banner thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi xóa banner: {str(e)}'

    @staticmethod
    def toggle_status(banner_id):
        """Bật hoặc tắt trạng thái hiển thị của banner."""
        banner = BannerModel.get_by_id(banner_id)
        if not banner:
            return False, 'Banner không tồn tại.'

        new_status = 0 if banner.get('trang_thai') == 1 else 1
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE banner SET trang_thai = ? WHERE id = ?', (new_status, banner_id))
            conn.commit()
            conn.close()
            return True, new_status
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
