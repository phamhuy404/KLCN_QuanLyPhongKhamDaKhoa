from datetime import datetime, date
from core.database import get_db

class ScheduleModel:
    """Model quản lý lịch làm việc, phân ca trực của bác sĩ và kiểm soát xung đột lịch."""

    CA_LAM_INFO = {
        1: {'ten': 'Ca sáng', 'bat_dau': '07:00:00', 'ket_thuc': '11:30:00'},
        2: {'ten': 'Ca chiều', 'bat_dau': '13:30:00', 'ket_thuc': '17:00:00'},
        3: {'ten': 'Ca tối', 'bat_dau': '17:30:00', 'ket_thuc': '20:30:00'}
    }

    @staticmethod
    def get_all(filter_doctor_id=None, filter_room_id=None, filter_date=None, from_date=None, to_date=None):
        """Lấy danh sách các ca làm việc kèm thông tin bác sĩ, phòng khám và chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT 
                llv.*,
                bs.hoc_vi, bs.avatar, bs.trang_thai_lam_viec,
                nv.ho_ten AS ten_bac_si, nv.sdt AS sdt_bac_si,
                pk.ma_phong, pk.ten_phong, pk.vi_tri_tang,
                ck.id AS chuyen_khoa_id, ck.ten_khoa
            FROM lich_lam_viec llv
            JOIN bac_si bs ON llv.bac_si_id = bs.id
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE 1=1
        '''
        params = []
        if filter_doctor_id:
            sql += ' AND llv.bac_si_id = ?'
            params.append(filter_doctor_id)
        if filter_room_id:
            sql += ' AND llv.phong_kham_id = ?'
            params.append(filter_room_id)
        if filter_date:
            sql += ' AND llv.ngay_lam = ?'
            params.append(filter_date)
        if from_date:
            sql += ' AND llv.ngay_lam >= ?'
            params.append(from_date)
        if to_date:
            sql += ' AND llv.ngay_lam <= ?'
            params.append(to_date)

        sql += ' ORDER BY llv.ngay_lam DESC, llv.ca_lam ASC, llv.id DESC'

        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        for r in rows:
            ca = r.get('ca_lam', 1)
            info = ScheduleModel.CA_LAM_INFO.get(ca, ScheduleModel.CA_LAM_INFO[1])
            r['ten_ca'] = info['ten']

        return rows

    @staticmethod
    def get_by_id(schedule_id):
        """Lấy chi tiết một ca làm việc theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                llv.*,
                bs.hoc_vi, nv.ho_ten AS ten_bac_si,
                pk.ma_phong, pk.ten_phong,
                ck.id AS chuyen_khoa_id, ck.ten_khoa
            FROM lich_lam_viec llv
            JOIN bac_si bs ON llv.bac_si_id = bs.id
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE llv.id = ?
        ''', (schedule_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create_schedule(bac_si_id, phong_kham_id, ngay_lam, ca_lam=1, gio_bat_dau=None, gio_ket_thuc=None, so_luong_kham_toi_da=20):
        """Thêm ca trực mới với cơ chế kiểm tra xung đột lịch chặt chẽ."""
        if not bac_si_id or not phong_kham_id or not ngay_lam:
            return False, "Bác sĩ, phòng khám và ngày làm là bắt buộc!"

        try:
            ca_lam = int(ca_lam)
            if ca_lam not in [1, 2, 3]:
                ca_lam = 1
            so_luong_kham_toi_da = int(so_luong_kham_toi_da)
            if so_luong_kham_toi_da <= 0:
                so_luong_kham_toi_da = 20
        except (ValueError, TypeError):
            ca_lam = 1
            so_luong_kham_toi_da = 20

        # Kiểm tra ngày làm không được trong quá khứ
        try:
            work_date = datetime.strptime(str(ngay_lam)[:10], '%Y-%m-%d').date()
            if work_date < date.today():
                return False, f"Không thể xếp lịch làm việc cho ngày trong quá khứ ({ngay_lam})!"
        except Exception:
            return False, "Định dạng ngày làm không hợp lệ (chuẩn: YYYY-MM-DD)!"

        ca_info = ScheduleModel.CA_LAM_INFO.get(ca_lam, ScheduleModel.CA_LAM_INFO[1])
        gio_bat_dau = gio_bat_dau or ca_info['bat_dau']
        gio_ket_thuc = gio_ket_thuc or ca_info['ket_thuc']

        conn = get_db()
        cursor = conn.cursor()
        try:
            # 1. KIỂM TRA XUNG ĐỘT BÁC SĨ: Bác sĩ đã có lịch ở bất kỳ phòng nào vào cùng ngày và ca này chưa?
            cursor.execute('''
                SELECT llv.id, pk.ten_phong
                FROM lich_lam_viec llv
                JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                WHERE llv.bac_si_id = ? AND llv.ngay_lam = ? AND llv.ca_lam = ?
            ''', (bac_si_id, str(work_date), ca_lam))
            conflict_bs = cursor.fetchone()
            if conflict_bs:
                conn.close()
                return False, f"Xung đột lịch bác sĩ: Bác sĩ này đã có lịch trực tại '{conflict_bs['ten_phong']}' vào {ca_info['ten']} ngày {work_date}!"

            # 2. KIỂM TRA XUNG ĐỘT PHÒNG KHÁM: Phòng khám này đã có bác sĩ khác trực vào cùng ngày và ca này chưa?
            cursor.execute('''
                SELECT llv.id, nv.ho_ten
                FROM lich_lam_viec llv
                JOIN bac_si bs ON llv.bac_si_id = bs.id
                JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE llv.phong_kham_id = ? AND llv.ngay_lam = ? AND llv.ca_lam = ?
            ''', (phong_kham_id, str(work_date), ca_lam))
            conflict_pk = cursor.fetchone()
            if conflict_pk:
                conn.close()
                return False, f"Xung đột phòng khám: Phòng này đã được phân công cho bác sĩ '{conflict_pk['ho_ten']}' vào {ca_info['ten']} ngày {work_date}!"

            # Lưu vào CSDL
            cursor.execute('''
                INSERT INTO lich_lam_viec (bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1)
            ''', (bac_si_id, phong_kham_id, str(work_date), ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da))

            conn.commit()
            sc_id = cursor.lastrowid
            conn.close()
            return True, sc_id

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi tạo lịch làm việc: {str(e)}"

    @staticmethod
    def update_schedule(schedule_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam=1, gio_bat_dau=None, gio_ket_thuc=None, so_luong_kham_toi_da=20, trang_thai=1):
        """Cập nhật lịch làm việc kèm kiểm tra xung đột ngoại trừ chính lịch đang sửa."""
        try:
            ca_lam = int(ca_lam)
            so_luong_kham_toi_da = int(so_luong_kham_toi_da)
            trang_thai = int(trang_thai)
            work_date = datetime.strptime(str(ngay_lam)[:10], '%Y-%m-%d').date()
        except Exception:
            return False, "Thông tin cập nhật không hợp lệ!"

        ca_info = ScheduleModel.CA_LAM_INFO.get(ca_lam, ScheduleModel.CA_LAM_INFO[1])
        gio_bat_dau = gio_bat_dau or ca_info['bat_dau']
        gio_ket_thuc = gio_ket_thuc or ca_info['ket_thuc']

        conn = get_db()
        cursor = conn.cursor()
        try:
            # Kiểm tra xung đột bác sĩ
            cursor.execute('''
                SELECT llv.id, pk.ten_phong
                FROM lich_lam_viec llv
                JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                WHERE llv.bac_si_id = ? AND llv.ngay_lam = ? AND llv.ca_lam = ? AND llv.id != ?
            ''', (bac_si_id, str(work_date), ca_lam, schedule_id))
            if cursor.fetchone():
                conn.close()
                return False, f"Xung đột lịch bác sĩ: Bác sĩ đã có lịch trực khác vào {ca_info['ten']} ngày {work_date}!"

            # Kiểm tra xung đột phòng khám
            cursor.execute('''
                SELECT llv.id, nv.ho_ten
                FROM lich_lam_viec llv
                JOIN bac_si bs ON llv.bac_si_id = bs.id
                JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE llv.phong_kham_id = ? AND llv.ngay_lam = ? AND llv.ca_lam = ? AND llv.id != ?
            ''', (phong_kham_id, str(work_date), ca_lam, schedule_id))
            if cursor.fetchone():
                conn.close()
                return False, f"Xung đột phòng khám: Phòng đã có bác sĩ khác trực vào {ca_info['ten']} ngày {work_date}!"

            cursor.execute('''
                UPDATE lich_lam_viec
                SET bac_si_id = ?, phong_kham_id = ?, ngay_lam = ?, ca_lam = ?, gio_bat_dau = ?, gio_ket_thuc = ?, so_luong_kham_toi_da = ?, trang_thai = ?
                WHERE id = ?
            ''', (bac_si_id, phong_kham_id, str(work_date), ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, trang_thai, schedule_id))

            conn.commit()
            conn.close()
            return True, "Cập nhật lịch làm việc thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cập nhật lịch: {str(e)}"

    @staticmethod
    def toggle_status(schedule_id):
        """Bật/tắt trạng thái ca làm việc."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT trang_thai FROM lich_lam_viec WHERE id = ?', (schedule_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Không tìm thấy lịch làm việc!"
            new_status = 0 if row['trang_thai'] else 1
            cursor.execute('UPDATE lich_lam_viec SET trang_thai = ? WHERE id = ?', (new_status, schedule_id))
            conn.commit()
            conn.close()
            return True, new_status
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def delete_schedule(schedule_id):
        """Xóa ca trực (chỉ cho phép khi chưa có lượt bệnh nhân đăng ký)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT so_luong_da_dang_ky FROM lich_lam_viec WHERE id = ?', (schedule_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Không tìm thấy lịch làm việc!"

            if row['so_luong_da_dang_ky'] > 0:
                conn.close()
                return False, f"Không thể xóa vì đã có {row['so_luong_da_dang_ky']} lượt bệnh nhân đăng ký vào ca này! Vui lòng chuyển trạng thái sang Vô hiệu hóa."

            cursor.execute('DELETE FROM lich_lam_viec WHERE id = ?', (schedule_id,))
            conn.commit()
            conn.close()
            return True, "Đã xóa ca trực thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi xóa lịch: {str(e)}"

    @staticmethod
    def get_available_doctors(chuyen_khoa_id, ngay_hen):
        """Lấy danh sách các bác sĩ có lịch trực thực tế và còn chỗ tiếp nhận vào ngày hẹn."""
        if not ngay_hen:
            return []

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT
                bs.id AS bac_si_id, bs.hoc_vi, bs.gia_kham, bs.avatar,
                nv.ho_ten AS ten_bac_si, nv.sdt,
                ck.id AS chuyen_khoa_id, ck.ten_khoa,
                pk.id AS phong_kham_id, pk.ten_phong,
                llv.id AS lich_lam_viec_id, llv.ca_lam, llv.gio_bat_dau, llv.gio_ket_thuc,
                llv.so_luong_kham_toi_da, llv.so_luong_da_dang_ky
            FROM lich_lam_viec llv
            JOIN bac_si bs ON llv.bac_si_id = bs.id
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            WHERE llv.ngay_lam = ?
              AND bs.chuyen_khoa_id = ?
              AND llv.trang_thai = 1
              AND bs.trang_thai_lam_viec = 'Đang làm việc'
              AND llv.so_luong_da_dang_ky < llv.so_luong_kham_toi_da
            ORDER BY llv.ca_lam ASC, bs.id ASC
        ''', (str(ngay_hen)[:10], chuyen_khoa_id))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
