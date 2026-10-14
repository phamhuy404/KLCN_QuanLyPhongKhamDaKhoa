from datetime import datetime
from core.database import get_db

class NotificationModel:
    """Model quản lý thông báo in-app cho người dùng và bệnh nhân."""

    @staticmethod
    def get_user_notifications(tai_khoan_id, limit=20):
        """Lấy danh sách thông báo của tài khoản người dùng."""
        if not tai_khoan_id:
            return []
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM thong_bao
            WHERE tai_khoan_id = ?
            ORDER BY id DESC
        ''', (tai_khoan_id,))
        rows = [dict(r) for r in cursor.fetchall()[:limit]]
        conn.close()
        return rows

    @staticmethod
    def get_unread_count(tai_khoan_id):
        """Lấy số lượng thông báo chưa đọc của người dùng."""
        if not tai_khoan_id:
            return 0
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) AS cnt FROM thong_bao
            WHERE tai_khoan_id = ? AND da_doc = 0
        ''', (tai_khoan_id,))
        row = cursor.fetchone()
        conn.close()
        return row['cnt'] if row else 0

    @staticmethod
    def mark_as_read(notification_id, tai_khoan_id):
        """Đánh dấu một thông báo là đã đọc (bảo vệ quyền riêng tư theo tài khoản)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE thong_bao SET da_doc = 1
                WHERE id = ? AND tai_khoan_id = ?
            ''', (notification_id, tai_khoan_id))
            conn.commit()
            conn.close()
            return True, "Đã cập nhật trạng thái đã đọc!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def mark_all_as_read(tai_khoan_id):
        """Đánh dấu tất cả thông báo của tài khoản là đã đọc."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE thong_bao SET da_doc = 1
                WHERE tai_khoan_id = ? AND da_doc = 0
            ''', (tai_khoan_id,))
            conn.commit()
            conn.close()
            return True, "Đã đánh dấu tất cả là đã đọc!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def create(tai_khoan_id, tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Tạo thông báo mới trong hệ thống."""
        if not tai_khoan_id:
            return False, "Thiếu ID tài khoản!"
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                VALUES (?, ?, ?, ?, ?, 0, ?)
            ''', (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, now_str))
            conn.commit()
            conn.close()
            return True, "Tạo thông báo thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
