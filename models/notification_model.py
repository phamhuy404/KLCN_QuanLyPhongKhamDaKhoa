from datetime import datetime
from core.database import get_db

class NotificationModel:
    """Model quản lý thông báo in-app cho người dùng và bệnh nhân."""

    @staticmethod
    def get_user_notifications(tai_khoan_id, limit=None, loai=None, unread_only=False):
        """Lấy danh sách thông báo của tài khoản (limit=None trả về toàn bộ lịch sử)."""
        if not tai_khoan_id:
            return []
        conn = get_db()
        cursor = conn.cursor()
        
        sql = '''
            SELECT id, tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc,
                   CONVERT(VARCHAR(19), thoi_gian_tao, 120) AS thoi_gian_tao
            FROM thong_bao
            WHERE tai_khoan_id = ?
        '''
        params = [tai_khoan_id]

        if unread_only:
            sql += ' AND da_doc = 0'

        if loai and loai != 'all':
            if loai == 'appointment':
                sql += " AND (loai_thong_bao LIKE '%lịch%' OR loai_thong_bao LIKE '%hẹn%' OR loai_thong_bao LIKE '%tiếp nhận%')"
            elif loai == 'shift':
                sql += " AND (loai_thong_bao LIKE '%trực%' OR loai_thong_bao LIKE '%ca làm%' OR loai_thong_bao LIKE '%phê duyệt%')"
            elif loai == 'exam':
                sql += " AND (loai_thong_bao LIKE '%khám%' OR loai_thong_bao LIKE '%cận lâm sàng%' OR loai_thong_bao LIKE '%xét nghiệm%')"
            elif loai == 'pharmacy_billing':
                sql += " AND (loai_thong_bao LIKE '%thuốc%' OR loai_thong_bao LIKE '%dược%' OR loai_thong_bao LIKE '%thanh toán%' OR loai_thong_bao LIKE '%hóa đơn%')"
            else:
                sql += ' AND loai_thong_bao = ?'
                params.append(loai)

        sql += f' ORDER BY id DESC'
        cursor.execute(sql, tuple(params))
        all_rows = cursor.fetchall()
        if limit and int(limit) > 0:
            rows = [dict(r) for r in all_rows[:int(limit)]]
        else:
            rows = [dict(r) for r in all_rows]
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
        """Đánh dấu một thông báo là đã đọc."""
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
        """Tạo thông báo mới đích danh cho một tài khoản."""
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
    def notify_admins(tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Gửi thông báo chỉ tới tài khoản Quản trị viên (ADMIN)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT t.id FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                WHERE v.ma_vai_tro = 'ADMIN' AND t.trang_thai = 1
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
            return True, "Đã gửi thông báo cho Ban Quản trị"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def notify_receptionists(tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Gửi thông báo tới nhân viên Lễ tân (LETAN)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT t.id FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                WHERE v.ma_vai_tro = 'LETAN' AND t.trang_thai = 1
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
            return True, "Đã gửi thông báo cho bộ phận Lễ tân"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def notify_role(role_code, tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Gửi thông báo tới toàn bộ tài khoản thuộc một vai trò cụ thể (KTV, DUOCSI, LETAN, ADMIN, BACSI)."""
        if not role_code:
            return False, "Thiếu mã vai trò!"
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT t.id FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                WHERE v.ma_vai_tro = ? AND t.trang_thai = 1
            ''', (role_code,))
            accounts = cursor.fetchall()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for acc in accounts:
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                ''', (acc['id'], tieu_de, noi_dung, loai_thong_bao, lien_ket, now_str))
            conn.commit()
            conn.close()
            return True, f"Đã gửi thông báo cho vai trò {role_code}"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def notify_admins_and_receptionists(tieu_de, noi_dung, loai_thong_bao='Hệ thống', lien_ket=''):
        """Gửi thông báo tới Admin và Lễ tân trực."""
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
        """Gửi thông báo đích danh tới tài khoản của bác sĩ theo bac_si_id."""
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
        """Gửi thông báo đích danh tới tài khoản của bệnh nhân theo benh_nhan_id."""
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
    def get_poll_updates(tai_khoan_id, last_id=0, is_init=False):
        """Lấy thông báo mới và danh sách gần nhất phục vụ polling realtime có cơ chế chống spam toast."""
        if not tai_khoan_id:
            return {'unread_count': 0, 'new_notifications': [], 'recent_list': [], 'latest_id': 0}
        conn = get_db()
        cursor = conn.cursor()
        try:
            # 1. Đếm chưa đọc
            cursor.execute('SELECT COUNT(*) AS cnt FROM thong_bao WHERE tai_khoan_id = ? AND da_doc = 0', (tai_khoan_id,))
            unread_cnt = cursor.fetchone()['cnt']

            # 2. Lấy ID thông báo lớn nhất hiện tại của người dùng
            cursor.execute('SELECT COALESCE(MAX(id), 0) AS max_id FROM thong_bao WHERE tai_khoan_id = ?', (tai_khoan_id,))
            latest_id = cursor.fetchone()['max_id']

            # 3. Lấy thông báo mới hơn last_id (chỉ khi không phải phiên khởi tạo lần đầu và last_id > 0)
            new_notifications = []
            if not is_init and last_id and int(last_id) > 0 and int(last_id) < latest_id:
                cursor.execute('''
                    SELECT TOP 5 id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc,
                           CONVERT(VARCHAR(19), thoi_gian_tao, 120) AS thoi_gian_tao
                    FROM thong_bao
                    WHERE tai_khoan_id = ? AND id > ?
                    ORDER BY id DESC
                ''', (tai_khoan_id, int(last_id)))
                new_notifications = [dict(r) for r in cursor.fetchall()]

            # 4. Lấy 10 thông báo gần nhất để hiển thị dropdown menu
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
                'recent_list': recent_list,
                'latest_id': latest_id
            }
        except Exception as e:
            conn.close()
            return {'unread_count': 0, 'new_notifications': [], 'recent_list': [], 'latest_id': 0, 'error': str(e)}
