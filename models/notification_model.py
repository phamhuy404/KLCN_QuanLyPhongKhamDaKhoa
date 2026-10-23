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

    @staticmethod
    def notify_admins_and_receptionists(tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Gửi thông báo tới toàn bộ tài khoản Admin và Lễ tân."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT t.id FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                WHERE v.ma_vai_tro IN ('ADMIN', 'LETAN') AND t.trang_thai = 1
            ''')
            accounts = cursor.fetchall()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for acc in accounts:
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                ''', (acc['id'], tieu_de, noi_dung, loai_thong_bao, lien_ket, now_str))
            conn.commit()
            conn.close()
            return True, "Đã gửi thông báo cho Ban Quản trị và Lễ tân"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def notify_doctor(bac_si_id, tieu_de, noi_dung, loai_thong_bao='Lịch khám', lien_ket=''):
        """Gửi thông báo tới tài khoản của bác sĩ theo bac_si_id."""
        if not bac_si_id:
            return False, "Thiếu ID bác sĩ"
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT nv.tai_khoan_id
                FROM bac_si bs
                JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE bs.id = ?
            ''', (bac_si_id,))
            row = cursor.fetchone()
            if row and row['tai_khoan_id']:
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                ''', (row['tai_khoan_id'], tieu_de, noi_dung, loai_thong_bao, lien_ket, now_str))
                conn.commit()
                conn.close()
                return True, "Đã gửi thông báo cho bác sĩ"
            conn.close()
            return False, "Bác sĩ chưa liên kết tài khoản"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def notify_patient(benh_nhan_id, tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Gửi thông báo tới tài khoản của bệnh nhân theo benh_nhan_id."""
        if not benh_nhan_id:
            return False, "Thiếu ID bệnh nhân"
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (benh_nhan_id,))
            row = cursor.fetchone()
            if row and row['tai_khoan_id']:
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                ''', (row['tai_khoan_id'], tieu_de, noi_dung, loai_thong_bao, lien_ket, now_str))
                conn.commit()
                conn.close()
                return True, "Đã gửi thông báo cho bệnh nhân"
            conn.close()
            return False, "Bệnh nhân chưa liên kết tài khoản"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def get_poll_updates(tai_khoan_id, last_id=0):
        """Lấy thông báo mới hơn last_id và đếm số lượng chưa đọc phục vụ polling realtime."""
        if not tai_khoan_id:
            return {'unread_count': 0, 'new_notifications': [], 'recent_list': []}
        conn = get_db()
        cursor = conn.cursor()
        try:
            # 1. Đếm chưa đọc
            cursor.execute('SELECT COUNT(*) AS cnt FROM thong_bao WHERE tai_khoan_id = ? AND da_doc = 0', (tai_khoan_id,))
            unread_cnt = cursor.fetchone()['cnt']

            # 2. Lấy thông báo mới hơn last_id (nếu last_id > 0)
            new_notifications = []
            if last_id and int(last_id) > 0:
                cursor.execute('''
                    SELECT id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc,
                           CONVERT(VARCHAR(19), thoi_gian_tao, 120) AS thoi_gian_tao
                    FROM thong_bao
                    WHERE tai_khoan_id = ? AND id > ?
                    ORDER BY id DESC
                ''', (tai_khoan_id, int(last_id)))
                new_notifications = [dict(r) for r in cursor.fetchall()]

            # 3. Lấy 10 thông báo gần nhất để cập nhật dropdown list
            cursor.execute('''
                SELECT TOP 10 id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc,
                       CONVERT(VARCHAR(19), thoi_gian_tao, 120) AS thoi_gian_tao
                FROM thong_bao
                WHERE tai_khoan_id = ?
                ORDER BY id DESC
            ''', (tai_khoan_id,))
            recent_list = [dict(r) for r in cursor.fetchall()]

            conn.close()
            return {
                'unread_count': unread_cnt,
                'new_notifications': new_notifications,
                'recent_list': recent_list
            }
        except Exception as e:
            conn.close()
            return {'unread_count': 0, 'new_notifications': [], 'recent_list': [], 'error': str(e)}
