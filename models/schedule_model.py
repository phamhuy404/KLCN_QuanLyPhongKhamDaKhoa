from datetime import datetime, date, timedelta
from core.scheduling import (scheduling_db as get_db, serialized, validate_schedule,
                             appointments, in_schedule, sync_count, CalendarError)

class ScheduleModel:
    """Model quản lý lịch làm việc, phân ca trực, duyệt đăng ký và hủy ca trực."""

    CA_LAM_INFO = {
        1: {'ten': 'Ca sáng', 'bat_dau': '07:00:00', 'ket_thuc': '11:30:00'},
        2: {'ten': 'Ca chiều', 'bat_dau': '13:30:00', 'ket_thuc': '17:00:00'},
        3: {'ten': 'Ca tối', 'bat_dau': '17:30:00', 'ket_thuc': '20:30:00'}
    }

    @staticmethod
    def get_week_bounds(target_date=None):
        """Tính toán khoảng ngày của tuần hiện tại và 2 tuần tiếp theo tương thích đa định dạng."""
        if not target_date:
            today = date.today()
        elif isinstance(target_date, (datetime, date)):
            today = target_date.date() if isinstance(target_date, datetime) else target_date
        else:
            s = str(target_date).strip()[:10]
            today = None
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                try:
                    today = datetime.strptime(s, fmt).date()
                    break
                except ValueError:
                    pass
            if not today:
                today = date.today()

        start_cur = today - timedelta(days=today.weekday())
        end_cur = start_cur + timedelta(days=6)

        start_w1 = start_cur + timedelta(days=7)
        end_w1 = start_w1 + timedelta(days=6)

        start_w2 = start_cur + timedelta(days=14)
        end_w2 = start_w2 + timedelta(days=6)

        return {
            'current_week': (start_cur, end_cur),
            'next_week_1': (start_w1, end_w1),
            'next_week_2': (start_w2, end_w2)
        }

    @staticmethod
    def check_role_shift_capacity(ngay_lam, ca_lam, vai_tro_id, exclude_schedule_id=None):
        """Kiểm tra số người cùng vai trò trong một ca (tối đa 5 người/ca cho mỗi role)."""
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT COUNT(*) AS cnt
            FROM lich_lam_viec llv WITH (NOLOCK)
            JOIN nhan_vien nv WITH (NOLOCK) ON llv.nhan_vien_id = nv.id
            JOIN tai_khoan t WITH (NOLOCK) ON nv.tai_khoan_id = t.id
            WHERE llv.ngay_lam = ? 
              AND llv.ca_lam = ? 
              AND t.vai_tro_id = ?
              AND llv.trang_thai_duyet = 'DA_DUYET'
              AND (llv.trang_thai = 1 OR llv.trang_thai IS NULL)
        '''
        params = [str(ngay_lam)[:10], int(ca_lam), int(vai_tro_id)]
        if exclude_schedule_id:
            sql += ' AND llv.id != ?'
            params.append(exclude_schedule_id)

        cursor.execute(sql, tuple(params))
        row = cursor.fetchone()
        conn.close()
        cnt = row['cnt'] if row else 0
        return cnt, 5, cnt >= 5

    @staticmethod
    def check_doctor_dept_capacity(ngay_lam, ca_lam, chuyen_khoa_id, exclude_schedule_id=None):
        """Kiểm tra số bác sĩ cùng chuyên khoa trong một ca trực (tối đa 3 bác sĩ/khoa/ca)."""
        if not chuyen_khoa_id:
            return 0, 3, False
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT COUNT(*) AS cnt
            FROM lich_lam_viec llv WITH (NOLOCK)
            JOIN nhan_vien nv WITH (NOLOCK) ON llv.nhan_vien_id = nv.id
            JOIN bac_si bs WITH (NOLOCK) ON bs.nhan_vien_id = nv.id
            WHERE llv.ngay_lam = ? 
              AND llv.ca_lam = ? 
              AND bs.chuyen_khoa_id = ?
              AND llv.trang_thai_duyet = 'DA_DUYET'
              AND (llv.trang_thai = 1 OR llv.trang_thai IS NULL)
        '''
        params = [str(ngay_lam)[:10], int(ca_lam), int(chuyen_khoa_id)]
        if exclude_schedule_id:
            sql += ' AND llv.id != ?'
            params.append(exclude_schedule_id)

        cursor.execute(sql, tuple(params))
        row = cursor.fetchone()
        conn.close()
        cnt = row['cnt'] if row else 0
        return cnt, 3, cnt >= 3

    @staticmethod
    def get_all(filter_doctor_id=None, filter_room_id=None, filter_date=None, from_date=None, to_date=None, current_user=None):
        """Lấy danh sách các ca làm việc của toàn bộ nhân viên y tế kèm ưu tiên hiển thị."""
        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT 
                llv.*,
                nv.id AS staff_id, nv.ma_nhan_vien, nv.ho_ten AS ten_nhan_vien, nv.sdt AS sdt_nhan_vien, nv.chuc_vu,
                t.id AS tai_khoan_id, t.username, v.id AS vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                bs.id AS bac_si_id, bs.hoc_vi, bs.avatar, bs.trang_thai_lam_viec,
                pk.id AS phong_kham_id, pk.ma_phong, pk.ten_phong, pk.vi_tri_tang,
                ck.id AS chuyen_khoa_id, ck.ten_khoa
            FROM lich_lam_viec llv
            LEFT JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
            LEFT JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            LEFT JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE 1=1 AND (v.ma_vai_tro IS NULL OR v.ma_vai_tro != 'ADMIN')
        '''
        params = []
        if filter_doctor_id:
            sql += ' AND (llv.bac_si_id = ? OR bs.id = ?)'
            params.extend([filter_doctor_id, filter_doctor_id])
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

        bounds = ScheduleModel.get_week_bounds()
        end_current_week = bounds['current_week'][1]
        start_w1 = bounds['next_week_1'][0]
        end_w2 = bounds['next_week_2'][1]

        my_staff_id = current_user.get('staff_id') if current_user else None
        my_acc_id = current_user.get('id') if current_user else None
        is_admin = current_user.get('vai_tro') == 'ADMIN' if current_user else False

        for r in rows:
            ca = r.get('ca_lam', 1)
            info = ScheduleModel.CA_LAM_INFO.get(ca, ScheduleModel.CA_LAM_INFO[1])
            r['ten_ca'] = info['ten']
            r['ten_bac_si'] = r.get('ten_nhan_vien') or 'Chưa phân công'
            r['ho_ten'] = r.get('ten_nhan_vien') or ''
            r['sdt'] = r.get('sdt_nhan_vien') or ''

            # Xác định ca này có phải của bản thân người dùng đăng nhập không
            is_mine = False
            if my_staff_id and r.get('staff_id') == my_staff_id:
                is_mine = True
            elif my_acc_id and r.get('tai_khoan_id') == my_acc_id:
                is_mine = True
            r['is_my_shift'] = is_mine

            # Tính toán phân loại tuần
            w_date = r['ngay_lam']
            if isinstance(w_date, str):
                w_date = datetime.strptime(w_date[:10], '%Y-%m-%d').date()

            r['is_current_week'] = bool(w_date <= end_current_week)
            r['is_next_2_weeks'] = bool(start_w1 <= w_date <= end_w2)

            # Quyền sửa trực tiếp: Admin hoặc chính mình trong 2 tuần tiếp theo
            r['can_modify'] = bool(is_admin or (is_mine and r['is_next_2_weeks']))
            # Quyền gửi đơn hủy: Chính mình trong tuần hiện tại khi ca đã duyệt
            r['can_request_cancel'] = bool(is_mine and r.get('trang_thai_duyet') == 'DA_DUYET')

        # Ưu tiên đưa ca trực của bản thân lên đầu danh sách nếu không phải admin
        if current_user and not is_admin:
            my_shifts = [r for r in rows if r['is_my_shift']]
            other_shifts = [r for r in rows if not r['is_my_shift']]
            return my_shifts + other_shifts

        return rows

    @staticmethod
    def get_by_id(schedule_id):
        """Lấy chi tiết một ca làm việc theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                llv.*,
                nv.id AS staff_id, nv.ho_ten AS ten_nhan_vien, nv.sdt,
                t.id AS tai_khoan_id, t.username, v.id AS vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                bs.id AS bac_si_id, bs.hoc_vi, bs.avatar,
                pk.ma_phong, pk.ten_phong,
                ck.id AS chuyen_khoa_id, ck.ten_khoa
            FROM lich_lam_viec llv
            LEFT JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
            LEFT JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            LEFT JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE llv.id = ?
        ''', (schedule_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    @serialized
    def register_schedule(user, ngay_lam, ca_lam, phong_kham_id=None, ghi_chu=None, chuyen_khoa_id=None):
        """Nhân sự tự đăng ký ca làm trong 2 tuần tiếp theo với giới hạn tối đa 5 người/ca/role và 3 bác sĩ/khoa/ca."""
        if not user or not user.get('id'):
            return False, "Vui lòng đăng nhập để đăng ký ca trực!"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nv.id AS staff_id, nv.ho_ten, t.vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                   bs.id AS bac_si_id, bs.phong_kham_chinh_id, bs.chuyen_khoa_id, ck.ten_khoa
            FROM nhan_vien nv
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE t.id = ?
        ''', (user['id'],))
        staff_row = cursor.fetchone()
        if not staff_row:
            conn.close()
            return False, "Không tìm thấy hồ sơ nhân viên y tế liên kết với tài khoản này!"

        try:
            if isinstance(ca_lam, str):
                ca_map = {'sáng': 1, 'sang': 1, 'chiều': 2, 'chieu': 2, 'tối': 3, 'toi': 3, '1': 1, '2': 2, '3': 3}
                ca_lam = ca_map.get(ca_lam.strip().lower(), 0)
            else:
                ca_lam = int(ca_lam)
            if ca_lam not in [1, 2, 3]:
                raise ValueError("Invalid shift")
            work_date = None
            if isinstance(ngay_lam, (datetime, date)):
                work_date = ngay_lam.date() if isinstance(ngay_lam, datetime) else ngay_lam
            else:
                s = str(ngay_lam).strip()[:10]
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                    try:
                        work_date = datetime.strptime(s, fmt).date()
                        break
                    except ValueError:
                        pass
            if not work_date:
                conn.close()
                return False, "Ngày làm hoặc ca làm việc không hợp lệ!"
        except Exception:
            conn.close()
            return False, "Ngày làm hoặc ca làm việc không hợp lệ!"

        # Tài khoản Admin không cần đăng ký ca trực
        if staff_row.get('ma_vai_tro') == 'ADMIN':
            conn.close()
            return False, "Tài khoản Quản trị viên (Admin) không cần đăng ký ca trực và không xuất hiện trên lịch làm việc!"

        bounds = ScheduleModel.get_week_bounds()
        start_w1 = bounds['next_week_1'][0]
        end_w2 = bounds['next_week_2'][1]

        # Kiểm tra quy tắc 2 tuần tiếp theo (tuần hiện tại đã khóa cứng)
        if not (start_w1 <= work_date <= end_w2):
            conn.close()
            return False, f"Chỉ được đăng ký lịch trong 2 tuần tiếp theo ({start_w1.strftime('%d/%m')} - {end_w2.strftime('%d/%m/%Y')})! Tuần hiện tại đã khóa cứng."

        # Kiểm tra trùng ca cùng ngày của nhân sự
        cursor.execute('''
            SELECT id FROM lich_lam_viec
            WHERE nhan_vien_id = ? AND ngay_lam = ? AND ca_lam = ? AND (trang_thai_duyet != 'DA_HUY' OR trang_thai_duyet IS NULL)
        ''', (staff_row['staff_id'], str(work_date), ca_lam))
        if cursor.fetchone():
            conn.close()
            return False, f"Bạn đã đăng ký ca {ca_lam} vào ngày {work_date} rồi!"

        # 1. Kiểm tra tối đa 5 người/ca cho mỗi vai trò
        cnt, max_cap, is_full = ScheduleModel.check_role_shift_capacity(work_date, ca_lam, staff_row['vai_tro_id'])
        if is_full:
            conn.close()
            ca_name = ScheduleModel.CA_LAM_INFO.get(ca_lam, {}).get('ten', f'Ca {ca_lam}')
            return False, f"{ca_name} ngày {work_date} đã đủ tối đa {max_cap} nhân sự thuộc bộ phận {staff_row['ten_vai_tro']}!"

        # 2. Kiểm tra tối đa 3 bác sĩ cùng chuyên khoa trong một ca
        effective_dept_id = chuyen_khoa_id or staff_row.get('chuyen_khoa_id')
        if effective_dept_id:
            bs_cnt, bs_cap, bs_full = ScheduleModel.check_doctor_dept_capacity(work_date, ca_lam, effective_dept_id)
            if bs_full:
                conn.close()
                ca_name = ScheduleModel.CA_LAM_INFO.get(ca_lam, {}).get('ten', f'Ca {ca_lam}')
                dept_name = staff_row.get('ten_khoa') or 'chuyên khoa này'
                return False, f"{ca_name} ngày {work_date} đã đủ tối đa {bs_cap} bác sĩ thuộc {dept_name}!"

        ca_info = ScheduleModel.CA_LAM_INFO.get(ca_lam, ScheduleModel.CA_LAM_INFO[1])
        bs_id = staff_row.get('bac_si_id')
        if staff_row.get('phong_kham_chinh_id'):
            pk_id = int(staff_row['phong_kham_chinh_id'])
        elif phong_kham_id:
            pk_id = int(phong_kham_id)
            if effective_dept_id:
                cursor.execute('SELECT chuyen_khoa_id FROM phong_kham WHERE id = ?', (pk_id,))
                rm_row = cursor.fetchone()
                if rm_row and rm_row.get('chuyen_khoa_id') and int(rm_row['chuyen_khoa_id']) != int(effective_dept_id):
                    conn.close()
                    return False, "Phòng làm việc đã chọn không thuộc chuyên khoa của bạn!"
        elif effective_dept_id:
            cursor.execute('SELECT TOP 1 id FROM phong_kham WHERE chuyen_khoa_id = ? AND trang_thai = 1 ORDER BY id ASC', (effective_dept_id,))
            rm_row = cursor.fetchone()
            pk_id = rm_row['id'] if rm_row else None
        else:
            pk_id = None

        if chuyen_khoa_id and str(chuyen_khoa_id) != str(staff_row.get('chuyen_khoa_id')):
            raise CalendarError('Chuyên khoa không khớp hồ sơ nhân viên.')
        validate_schedule(cursor, staff_row['staff_id'], bs_id, pk_id, work_date, ca_lam)

        # Lễ tân tự động phê duyệt ngay khi đăng ký
        is_letan = staff_row.get('ma_vai_tro') == 'LETAN'
        status_duyet = 'DA_DUYET' if is_letan else 'CHO_DUYET'
        nguoi_duyet = user.get('id') if is_letan else None
        now_duyet = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if is_letan else None

        cursor.execute('''
            INSERT INTO lich_lam_viec (nhan_vien_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai, trang_thai_duyet, nguoi_duyet_id, ngay_duyet, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?, 20, 0, 1, ?, ?, ?, ?)
        ''', (staff_row['staff_id'], bs_id, pk_id, str(work_date), ca_lam, ca_info['bat_dau'], ca_info['ket_thuc'], status_duyet, nguoi_duyet, now_duyet, ghi_chu))

        conn.commit()
        conn.close()
        if is_letan:
            return True, "Lễ tân đăng ký ca làm việc thành công (Đã tự động phê duyệt)!"
        return True, "Đăng ký ca làm việc thành công, đang chờ Quản trị / Tiếp tân duyệt!"

    @staticmethod
    @serialized
    def request_cancellation(schedule_id, user, reason):
        """Gửi đơn xin hủy ca trực trong tuần hiện tại chờ Lễ tân hoặc Admin duyệt."""
        if not reason or not reason.strip():
            return False, "Vui lòng nhập lý do xin hủy ca trực!"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT llv.*, nv.tai_khoan_id
            FROM lich_lam_viec llv
            LEFT JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
            WHERE llv.id = ?
        ''', (schedule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Không tìm thấy ca trực cần xin hủy!"

        is_admin = user.get('vai_tro') == 'ADMIN'
        if not is_admin and row.get('tai_khoan_id') != user.get('id'):
            conn.close()
            return False, "Bạn chỉ có thể gửi đơn xin hủy ca trực của chính mình!"

        cursor.execute('''
            UPDATE lich_lam_viec
            SET trang_thai_duyet = 'CHO_HUY', ly_do_huy = ?
            WHERE id = ?
        ''', (reason.strip(), schedule_id))
        conn.commit()
        conn.close()
        return True, "Đã gửi đơn xin hủy ca trực! Vui lòng chờ Tiếp tân hoặc Admin duyệt."

    @staticmethod
    @serialized
    def approve_cancellation(schedule_id, reviewer_user, approved=True):
        """Duyệt hoặc từ chối đơn xin hủy ca trực (dành cho Admin và Tiếp tân)."""
        reviewer_role = reviewer_user.get('vai_tro') if reviewer_user else ''
        if reviewer_role not in ['ADMIN', 'LETAN']:
            return False, "Chỉ Quản trị viên hoặc Tiếp tân mới có quyền duyệt đơn xin hủy ca!"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, trang_thai_duyet FROM lich_lam_viec WHERE id = ?', (schedule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Không tìm thấy ca trực!"

        cursor.execute('SELECT * FROM lich_lam_viec WHERE id = ?', (schedule_id,))
        schedule = cursor.fetchone()
        if schedule.get('bac_si_id') and any(in_schedule(item, schedule) for item in appointments(cursor,str(schedule['ngay_lam'])[:10])):
            raise CalendarError('Ca còn lịch hẹn. Vui lòng đổi/hủy từng lịch hẹn trước.')
        if not approved:
            validate_schedule(cursor,schedule['nhan_vien_id'],schedule.get('bac_si_id'),schedule.get('phong_kham_id'),
                              schedule['ngay_lam'],schedule['ca_lam'],schedule['gio_bat_dau'],schedule['gio_ket_thuc'],
                              schedule['so_luong_kham_toi_da'],exclude=schedule['id'])
        cursor.execute("UPDATE lich_lam_viec SET trang_thai_duyet=?,trang_thai=?,nguoi_duyet_id=?,ngay_duyet=GETDATE() WHERE id=?",
                       ('DA_HUY' if approved else 'DA_DUYET',0 if approved else 1,reviewer_user.get('id'),schedule_id))
        conn.commit()
        conn.close()
        msg = "Đã duyệt hủy ca trực thành công!" if approved else "Đã từ chối đơn xin hủy, ca trực vẫn được duy trì."
        return True, msg

    @staticmethod
    @serialized
    def approve_schedule(schedule_id, reviewer_user, approved=True):
        """Duyệt yêu cầu đăng ký ca làm mới kèm kiểm tra hạn mức 5 người/ca/role và 3 bác sĩ/khoa/ca."""
        reviewer_role = reviewer_user.get('vai_tro') if reviewer_user else ''
        if reviewer_role not in ['ADMIN', 'LETAN']:
            return False, "Chỉ Quản trị viên hoặc Tiếp tân mới có quyền duyệt ca trực!"

        from models.notification_model import NotificationModel

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT llv.*, t.id AS tai_khoan_id, t.vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                   bs.id AS bac_si_id, bs.chuyen_khoa_id, ck.ten_khoa
            FROM lich_lam_viec llv
            JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON (llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id)
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE llv.id = ?
        ''', (schedule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Không tìm thấy ca trực cần duyệt!"

        if not approved and row.get('bac_si_id') and any(in_schedule(item,row) for item in appointments(cursor,str(row['ngay_lam'])[:10])):
            raise CalendarError('Ca còn lịch hẹn; cần điều phối trước.')
        if approved:
            validate_schedule(cursor, row['nhan_vien_id'], row.get('bac_si_id'), row.get('phong_kham_id'),
                              row['ngay_lam'], row['ca_lam'], row['gio_bat_dau'], row['gio_ket_thuc'],
                              row['so_luong_kham_toi_da'], exclude=row['id'])
            # 1. Kiểm tra hạn mức 5 người/role
            cnt, max_cap, is_full = ScheduleModel.check_role_shift_capacity(row['ngay_lam'], row['ca_lam'], row['vai_tro_id'], exclude_schedule_id=schedule_id)
            if is_full:
                conn.close()
                ca_name = ScheduleModel.CA_LAM_INFO.get(row['ca_lam'], {}).get('ten', f"Ca {row['ca_lam']}")
                return False, f"{ca_name} ngày {row['ngay_lam']} đã đủ tối đa {max_cap} người thuộc bộ phận {row['ten_vai_tro']}!"

            # 2. Kiểm tra hạn mức tối đa 3 bác sĩ cùng chuyên khoa
            if row.get('chuyen_khoa_id'):
                bs_cnt, bs_cap, bs_full = ScheduleModel.check_doctor_dept_capacity(row['ngay_lam'], row['ca_lam'], row['chuyen_khoa_id'], exclude_schedule_id=schedule_id)
                if bs_full:
                    conn.close()
                    ca_name = ScheduleModel.CA_LAM_INFO.get(row['ca_lam'], {}).get('ten', f"Ca {row['ca_lam']}")
                    dept_name = row.get('ten_khoa') or 'chuyên khoa'
                    return False, f"{ca_name} ngày {row['ngay_lam']} đã đủ tối đa {bs_cap} bác sĩ thuộc {dept_name}!"

            cursor.execute('''
                UPDATE lich_lam_viec
                SET trang_thai_duyet = 'DA_DUYET', trang_thai = 1, nguoi_duyet_id = ?, ngay_duyet = GETDATE()
                WHERE id = ?
            ''', (reviewer_user.get('id'), schedule_id))
            msg = "Đã duyệt ca trực thành công!"

            # Thông báo lại cho bác sĩ/nhân viên: chỉ cần thông báo không cần kèm ca đã xác nhận
            if row.get('tai_khoan_id'):
                NotificationModel.create(
                    tai_khoan_id=row['tai_khoan_id'],
                    tieu_de="Phê duyệt lịch làm việc",
                    noi_dung="Lịch làm việc của bạn đã được phê duyệt thành công!",
                    loai_thong_bao="Lịch trực",
                    lien_ket="/admin/staff?tab=schedules"
                )
        else:
            cursor.execute('''
                UPDATE lich_lam_viec
                SET trang_thai_duyet = 'TU_CHOI', trang_thai = 0, nguoi_duyet_id = ?, ngay_duyet = GETDATE()
                WHERE id = ?
            ''', (reviewer_user.get('id'), schedule_id))
            msg = "Đã từ chối đăng ký ca trực."

            if row.get('tai_khoan_id'):
                NotificationModel.create(
                    tai_khoan_id=row['tai_khoan_id'],
                    tieu_de="Từ chối lịch làm việc",
                    noi_dung="Đăng ký ca làm việc của bạn đã bị từ chối.",
                    loai_thong_bao="Lịch trực",
                    lien_ket="/admin/staff?tab=schedules"
                )

        conn.commit()
        conn.close()
        return True, msg

    @staticmethod
    @serialized
    def bulk_approve_schedules(schedule_ids, reviewer_user, approved=True):
        """Duyệt hoặc từ chối hàng loạt ca làm việc và gom nhóm thông báo (1 thông báo duy nhất/nhân sự)."""
        reviewer_role = reviewer_user.get('vai_tro') if reviewer_user else ''
        if reviewer_role not in ['ADMIN', 'LETAN']:
            return False, "Chỉ Quản trị viên hoặc Tiếp tân mới có quyền duyệt ca trực!", 0

        if not schedule_ids or not isinstance(schedule_ids, list):
            return False, "Danh sách ca trực trống!", 0

        from models.notification_model import NotificationModel

        conn = get_db()
        cursor = conn.cursor()
        success_count = 0
        notified_accounts = set()

        for s_id in schedule_ids:
            try:
                cursor.execute('''
                    SELECT llv.*, t.id AS tai_khoan_id, t.vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                           bs.id AS bac_si_id, bs.chuyen_khoa_id, ck.ten_khoa
                    FROM lich_lam_viec llv
                    JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
                    JOIN tai_khoan t ON nv.tai_khoan_id = t.id
                    JOIN vai_tro v ON t.vai_tro_id = v.id
                    LEFT JOIN bac_si bs ON (llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id)
                    LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
                    WHERE llv.id = ?
                ''', (s_id,))
                row = cursor.fetchone()
                if not row:
                    continue

                if not approved and row.get('bac_si_id') and any(in_schedule(item,row) for item in appointments(cursor,str(row['ngay_lam'])[:10])):
                    raise CalendarError('Ca còn lịch hẹn; cần điều phối trước.')
                if approved:
                    validate_schedule(cursor, row['nhan_vien_id'], row.get('bac_si_id'), row.get('phong_kham_id'),
                                      row['ngay_lam'], row['ca_lam'], row['gio_bat_dau'], row['gio_ket_thuc'],
                                      row['so_luong_kham_toi_da'], exclude=row['id'])
                    cnt, max_cap, is_full = ScheduleModel.check_role_shift_capacity(row['ngay_lam'], row['ca_lam'], row['vai_tro_id'], exclude_schedule_id=s_id)
                    if is_full:
                        continue

                    if row.get('chuyen_khoa_id'):
                        bs_cnt, bs_cap, bs_full = ScheduleModel.check_doctor_dept_capacity(row['ngay_lam'], row['ca_lam'], row['chuyen_khoa_id'], exclude_schedule_id=s_id)
                        if bs_full:
                            continue

                    cursor.execute('''
                        UPDATE lich_lam_viec
                        SET trang_thai_duyet = 'DA_DUYET', trang_thai = 1, nguoi_duyet_id = ?, ngay_duyet = GETDATE()
                        WHERE id = ?
                    ''', (reviewer_user.get('id'), s_id))
                else:
                    cursor.execute('''
                        UPDATE lich_lam_viec
                        SET trang_thai_duyet = 'TU_CHOI', trang_thai = 0, nguoi_duyet_id = ?, ngay_duyet = GETDATE()
                        WHERE id = ?
                    ''', (reviewer_user.get('id'), s_id))

                conn.commit()
                success_count += 1
                if row.get('tai_khoan_id'):
                    notified_accounts.add(row['tai_khoan_id'])
            except CalendarError:
                continue

        conn.commit()
        conn.close()

        # Gom nhóm: Gửi đúng 1 thông báo duy nhất cho mỗi nhân sự
        for acc_id in notified_accounts:
            if approved:
                NotificationModel.create(
                    tai_khoan_id=acc_id,
                    tieu_de="Phê duyệt lịch làm việc",
                    noi_dung="Lịch làm việc của bạn đã được phê duyệt thành công!",
                    loai_thong_bao="Lịch trực",
                    lien_ket="/admin/staff?tab=schedules"
                )
            else:
                NotificationModel.create(
                    tai_khoan_id=acc_id,
                    tieu_de="Từ chối lịch làm việc",
                    noi_dung="Đăng ký ca làm việc của bạn đã bị từ chối.",
                    loai_thong_bao="Lịch trực",
                    lien_ket="/admin/staff?tab=schedules"
                )

        action_msg = "phê duyệt" if approved else "từ chối"
        return success_count > 0, f"Đã {action_msg} thành công {success_count} ca làm việc!", success_count

    @staticmethod
    def get_pending_approvals(filter_role=None, filter_ca=None):
        """Lấy danh sách các đơn chờ duyệt đăng ký hoặc xin hủy ca trực."""
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT 
                llv.*,
                nv.ho_ten AS ten_nhan_vien, nv.sdt, nv.chuc_vu,
                t.username, v.id AS vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                bs.hoc_vi, pk.ten_phong, ck.ten_khoa
            FROM lich_lam_viec llv
            JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE llv.trang_thai_duyet IN ('CHO_HUY', 'CHO_DUYET')
        '''
        params = []
        if filter_role:
            sql += ' AND v.ma_vai_tro = ?'
            params.append(filter_role)
        if filter_ca:
            sql += ' AND llv.ca_lam = ?'
            params.append(int(filter_ca))

        sql += ' ORDER BY llv.ngay_lam ASC, llv.ca_lam ASC'
        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        for r in rows:
            ca = r.get('ca_lam', 1)
            r['ten_ca'] = ScheduleModel.CA_LAM_INFO.get(ca, {}).get('ten', f'Ca {ca}')
        return rows

    @staticmethod
    @serialized
    def assign_doctor_room(doctor_id, room_id):
        cursor = get_db().cursor()
        cursor.execute('SELECT chuyen_khoa_id FROM bac_si WHERE id = ?', (doctor_id,))
        doctor = cursor.fetchone()
        if not doctor:
            raise CalendarError('Không tìm thấy bác sĩ.')
        room_id = int(room_id) if room_id is not None else None
        if room_id == 0:
            room_id = None
        name = 'Chưa phân phòng'
        if room_id:
            cursor.execute('SELECT ten_phong,chuyen_khoa_id,trang_thai FROM phong_kham WHERE id = ?', (room_id,))
            room = cursor.fetchone()
            if not room or room['trang_thai'] != 1 or room['chuyen_khoa_id'] != doctor['chuyen_khoa_id']:
                raise CalendarError('Phòng không hoạt động hoặc không đúng chuyên khoa.')
            name = room['ten_phong']
            cursor.execute('SELECT * FROM lich_lam_viec WHERE bac_si_id = ? AND ngay_lam >= ?', (doctor_id,date.today().isoformat()))
            rows = cursor.fetchall()
            for row in rows:
                if row.get('trang_thai_duyet') in ('DA_HUY','TU_CHOI') or str(row.get('phong_kham_id')) == str(room_id):
                    continue
                ok, message = ScheduleModel.update_schedule(row['id'],doctor_id,room_id,row['ngay_lam'],row['ca_lam'],
                    row['gio_bat_dau'],row['gio_ket_thuc'],row['so_luong_kham_toi_da'],row['trang_thai'])
                if not ok:
                    return False, message
        cursor.execute('UPDATE bac_si SET phong_kham_chinh_id = ? WHERE id = ?', (room_id,doctor_id))
        return True, {'message':'Đã phân công phòng: '+name,'phong_kham_chinh_id':room_id,'ten_phong':name}

    @staticmethod
    @serialized
    def create_schedule(bac_si_id, phong_kham_id, ngay_lam, ca_lam=1, gio_bat_dau=None, gio_ket_thuc=None, so_luong_kham_toi_da=20, nhan_vien_id=None):
        conn = get_db()
        cursor = conn.cursor()
        if nhan_vien_id and not bac_si_id:
            cursor.execute('SELECT id FROM bac_si WHERE nhan_vien_id = ?', (nhan_vien_id,))
            doctor = cursor.fetchone()
            bac_si_id = doctor['id'] if doctor else None
        staff, day, shift, start, end, capacity = validate_schedule(
            cursor, nhan_vien_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam,
            gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da)
        cursor.execute("""INSERT INTO lich_lam_viec
            (nhan_vien_id,bac_si_id,phong_kham_id,ngay_lam,ca_lam,gio_bat_dau,gio_ket_thuc,
             so_luong_kham_toi_da,so_luong_da_dang_ky,trang_thai,trang_thai_duyet)
            VALUES (?,?,?,?,?,?,?,?,0,1,'DA_DUYET')""",
            (staff,bac_si_id,phong_kham_id,day,shift,start,end,capacity))
        return True, cursor.lastrowid

    @staticmethod
    @serialized
    def update_schedule(schedule_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam=1, gio_bat_dau=None, gio_ket_thuc=None, so_luong_kham_toi_da=20, trang_thai=1):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM lich_lam_viec WHERE id = ?', (schedule_id,))
        old = cursor.fetchone()
        if not old:
            return False, 'Không tìm thấy ca.'
        staff = old.get('nhan_vien_id') if not bac_si_id else None
        if staff and not bac_si_id:
            cursor.execute('SELECT id FROM bac_si WHERE nhan_vien_id = ?', (staff,))
            doctor = cursor.fetchone()
            bac_si_id = doctor['id'] if doctor else None
        staff, day, shift, start, end, capacity = validate_schedule(
            cursor, staff, bac_si_id, phong_kham_id, ngay_lam, ca_lam,
            gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, exclude=old['id'])
        status = int(trang_thai)
        if status not in (0,1):
            raise CalendarError('Trạng thái ca không hợp lệ.')
        booked = [row for row in appointments(cursor,str(old['ngay_lam'])[:10]) if in_schedule(row,old)] if old.get('bac_si_id') else []
        if capacity < len(booked):
            raise CalendarError('Sức chứa nhỏ hơn số lịch hẹn hiện có.')
        changed = (str(old.get('bac_si_id')) != str(bac_si_id) or str(old.get('phong_kham_id')) != str(phong_kham_id)
                   or str(old['ngay_lam'])[:10] != day or old['ca_lam'] != shift
                   or str(old['gio_bat_dau'])[:8] != start or str(old['gio_ket_thuc'])[:8] != end or status != 1)
        if booked and changed:
            raise CalendarError('Ca có lịch hẹn; phải điều phối lịch hẹn trước khi thay đổi ca.')
        cursor.execute("""UPDATE lich_lam_viec SET nhan_vien_id=?,bac_si_id=?,phong_kham_id=?,ngay_lam=?,
            ca_lam=?,gio_bat_dau=?,gio_ket_thuc=?,so_luong_kham_toi_da=?,trang_thai=?,so_luong_da_dang_ky=? WHERE id=?""",
            (staff,bac_si_id,phong_kham_id,day,shift,start,end,capacity,status,len(booked),old['id']))
        return True, 'Cập nhật ca thành công.'

    @staticmethod
    @serialized
    def toggle_status(schedule_id):
        """Bật hoặc tắt trạng thái kích hoạt của ca làm việc."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM lich_lam_viec WHERE id = ?', (schedule_id,))
            existing = cursor.fetchone()
            if existing and existing.get('bac_si_id') and any(in_schedule(item,existing) for item in appointments(cursor,str(existing['ngay_lam'])[:10])):
                raise CalendarError('Ca còn lịch hẹn; cần điều phối trước.')
            if existing and not existing['trang_thai']:
                validate_schedule(cursor,existing['nhan_vien_id'],existing.get('bac_si_id'),existing.get('phong_kham_id'),
                                  existing['ngay_lam'],existing['ca_lam'],existing['gio_bat_dau'],existing['gio_ket_thuc'],
                                  existing['so_luong_kham_toi_da'],exclude=existing['id'])
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
    @serialized
    def delete_schedule(schedule_id, current_user=None):
        """Xóa ca trực (Nhân viên chỉ xóa được ca trong 2 tuần tiếp theo, Admin xóa mọi ca chưa có bệnh nhân)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM lich_lam_viec WHERE id = ?', (schedule_id,))
            existing = cursor.fetchone()
            if existing and existing.get('bac_si_id') and any(in_schedule(item,existing) for item in appointments(cursor,str(existing['ngay_lam'])[:10])):
                raise CalendarError('Ca còn lịch hẹn; cần điều phối trước.')
            cursor.execute('''
                SELECT llv.*, nv.tai_khoan_id
                FROM lich_lam_viec llv
                LEFT JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
                WHERE llv.id = ?
            ''', (schedule_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Không tìm thấy lịch làm việc!"

            is_admin = current_user.get('vai_tro') == 'ADMIN' if current_user else False
            if current_user and not is_admin:
                if row.get('tai_khoan_id') != current_user.get('id'):
                    conn.close()
                    return False, "Bạn không có quyền xóa ca trực của người khác!"

                bounds = ScheduleModel.get_week_bounds()
                end_cur = bounds['current_week'][1]
                w_date = row['ngay_lam']
                if isinstance(w_date, str):
                    w_date = datetime.strptime(w_date[:10], '%Y-%m-%d').date()

                if w_date <= end_cur:
                    conn.close()
                    return False, "Lịch trực tuần hiện tại đã khóa cứng! Vui lòng gửi đơn xin hủy lịch để được duyệt."

            if row.get('so_luong_da_dang_ky', 0) > 0:
                conn.close()
                return False, f"Không thể xóa vì đã có {row['so_luong_da_dang_ky']} lượt bệnh nhân đăng ký vào ca này!"

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
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            WHERE llv.ngay_lam = ?
              AND bs.chuyen_khoa_id = ?
              AND (llv.trang_thai = 1 OR llv.trang_thai IS NULL)
              AND llv.trang_thai_duyet = 'DA_DUYET'
              AND bs.trang_thai_lam_viec = N'Đang làm việc'
              AND llv.so_luong_da_dang_ky < llv.so_luong_kham_toi_da
            ORDER BY llv.ca_lam ASC, bs.id ASC
        ''', (str(ngay_hen)[:10], chuyen_khoa_id))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_week_days(start_date=None):
        """Trả về danh sách 7 ngày trong tuần từ Thứ 2 đến Chủ nhật."""
        if not start_date:
            today = date.today()
        elif isinstance(start_date, str):
            today = datetime.strptime(str(start_date)[:10], '%Y-%m-%d').date()
        else:
            today = start_date

        monday = today - timedelta(days=today.weekday())
        day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        today_str = str(date.today())

        days = []
        for i in range(7):
            d = monday + timedelta(days=i)
            d_str = str(d)
            days.append({
                'date_str': d_str,
                'day_name': day_names[i],
                'display_date': d.strftime('%d/%m/%Y'),
                'short_date': d.strftime('%d/%m'),
                'is_today': (d_str == today_str)
            })
        return days

    @staticmethod
    @serialized
    def register_multiple_schedules(user, shifts, phong_kham_id=None, ghi_chu=None, chuyen_khoa_id=None):
        """Nhân viên đăng ký nhiều ca làm việc cùng lúc trong 2 tuần tiếp theo."""
        if not user or not user.get('id'):
            return False, "Vui lòng đăng nhập để đăng ký ca trực!", 0, []
        if not shifts or not isinstance(shifts, list):
            return False, "Vui lòng chọn ít nhất một ca làm việc!", 0, []

        success_count = 0
        errors = []
        for s in shifts:
            ngay = s.get('ngay_lam')
            ca = s.get('ca_lam')
            pk = s.get('phong_kham_id') or phong_kham_id
            note = s.get('ghi_chu') or ghi_chu
            ck_id = s.get('chuyen_khoa_id') or chuyen_khoa_id
            ok, msg = ScheduleModel.register_schedule(user, ngay, ca, pk, note, chuyen_khoa_id=ck_id)
            if ok:
                success_count += 1
            else:
                ca_name = ScheduleModel.CA_LAM_INFO.get(int(ca or 1), {}).get('ten', f'Ca {ca}')
                errors.append(f"{ngay} ({ca_name}): {msg}")

        if success_count > 0 and user.get('vai_tro') != 'LETAN':
            from models.notification_model import NotificationModel
            staff_name = user.get('ho_ten') or user.get('username') or 'Nhân sự y tế'
            role_name = user.get('chuc_vu') or user.get('ten_vai_tro') or 'Nhân sự'
            NotificationModel.notify_admins(
                tieu_de="Đăng ký ca làm việc mới",
                noi_dung=f"{role_name} {staff_name} vừa đăng ký {success_count} ca làm việc mới, đang chờ duyệt.",
                loai_thong_bao="Lịch trực",
                lien_ket="/admin/staff?tab=approvals"
            )

        if success_count == len(shifts):
            return True, f"Đăng ký thành công toàn bộ {success_count} ca làm việc!", success_count, errors
        elif success_count > 0:
            return True, f"Đã đăng ký thành công {success_count}/{len(shifts)} ca! (Chi tiết lỗi: {'; '.join(errors)})", success_count, errors
        else:
            return False, f"Đăng ký thất bại: {'; '.join(errors)}", 0, errors

    @staticmethod
    def _calc_shift_hours(gio_bat_dau, gio_ket_thuc, ca_lam):
        """Tính số giờ làm việc của ca trực từ giờ bắt đầu đến giờ kết thúc."""
        from core.scheduling import clock
        defaults = {1: 4.5, 2: 3.5, 3: 3.0}
        try:
            st = clock(gio_bat_dau)
            et = clock(gio_ket_thuc)
            diff = (et.hour * 60 + et.minute) - (st.hour * 60 + st.minute)
            if diff > 0:
                return round(diff / 60.0, 2)
        except Exception:
            pass
        return defaults.get(int(ca_lam or 1), 4.0)

    @staticmethod
    def get_work_statistics_and_history(current_user, selected_month=None, scope=None, filter_staff_id=None, months_back=6):
        """Thống kê giờ công theo tháng/nhiều tháng, số ca khám hoàn thành và lịch sử đăng ký ca cũ theo phân quyền."""
        from core.scheduling import clock
        user = current_user or {}
        user_role = user.get('vai_tro') or ''
        can_view_all = user_role in ('ADMIN', 'LETAN')

        conn = get_db()
        cursor = conn.cursor()
        try:
            own_staff_id = user.get('staff_id') or user.get('nhan_vien_id')
            if not own_staff_id and user.get('id'):
                cursor.execute('SELECT id FROM nhan_vien WHERE tai_khoan_id = ?', (user['id'],))
                nv_own = cursor.fetchone()
                if nv_own:
                    own_staff_id = nv_own['id']

            if not can_view_all:
                effective_scope = 'mine'
                target_staff_ids = {int(own_staff_id)} if own_staff_id else {-1}
            else:
                effective_scope = scope if scope in ('mine', 'all') else 'all'
                if effective_scope == 'mine':
                    target_staff_ids = {int(own_staff_id)} if own_staff_id else {-1}
                elif filter_staff_id and str(filter_staff_id).isdigit():
                    target_staff_ids = {int(filter_staff_id)}
                else:
                    target_staff_ids = None

            today = date.today()
            now_time = datetime.now().time()
            today_iso = today.isoformat()
            cur_month_key = today.strftime('%Y-%m')

            recent_months = []
            y_cur, m_cur = today.year, today.month
            for i in range(max(int(months_back or 6), 6)):
                m_val = m_cur - i
                y_val = y_cur
                while m_val <= 0:
                    m_val += 12
                    y_val -= 1
                recent_months.append(f"{y_val:04d}-{m_val:02d}")

            cursor.execute('''
                SELECT nv.id AS nhan_vien_id, nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.trang_thai,
                       t.id AS tai_khoan_id, v.ma_vai_tro, v.ten_vai_tro,
                       bs.id AS bac_si_id, bs.hoc_vi, ck.ten_khoa
                FROM nhan_vien nv
                LEFT JOIN tai_khoan t ON nv.tai_khoan_id = t.id
                LEFT JOIN vai_tro v ON t.vai_tro_id = v.id
                LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
                LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
                ORDER BY CASE WHEN v.ma_vai_tro = 'BACSI' THEN 0 ELSE 1 END, nv.id ASC
            ''')
            all_staff_rows = [dict(r) for r in cursor.fetchall()]

            cursor.execute('''
                SELECT llv.*, nv.ma_nhan_vien, nv.ho_ten AS ten_nhan_vien, nv.chuc_vu,
                       v.ma_vai_tro, v.ten_vai_tro,
                       pk.ten_phong, ck.ten_khoa,
                       nv_duyet.ho_ten AS nguoi_duyet_ten
                FROM lich_lam_viec llv
                LEFT JOIN nhan_vien nv ON llv.nhan_vien_id = nv.id
                LEFT JOIN tai_khoan t ON nv.tai_khoan_id = t.id
                LEFT JOIN vai_tro v ON t.vai_tro_id = v.id
                LEFT JOIN bac_si bs ON llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id OR pk.chuyen_khoa_id = ck.id
                LEFT JOIN tai_khoan tk_duyet ON llv.nguoi_duyet_id = tk_duyet.id
                LEFT JOIN nhan_vien nv_duyet ON nv_duyet.tai_khoan_id = tk_duyet.id
                ORDER BY llv.ngay_lam DESC, llv.ca_lam DESC, llv.id DESC
            ''')
            raw_shifts = [dict(r) for r in cursor.fetchall()]

            cursor.execute('''
                SELECT pk.id, pk.bac_si_id,
                       CONVERT(VARCHAR(7), COALESCE(pk.thoi_gian_kham, GETDATE()), 120) AS month_key
                FROM phieu_kham pk
                WHERE pk.trang_thai = N'Hoàn thành' AND pk.bac_si_id IS NOT NULL
            ''')
            completed_pk = [dict(r) for r in cursor.fetchall()]

            cursor.execute('''
                SELECT lh.id, lh.bac_si_id,
                       SUBSTRING(CONVERT(VARCHAR(10), lh.ngay_hen, 120), 1, 7) AS month_key
                FROM lich_hen lh
                WHERE lh.trang_thai IN (N'Đã khám', N'Hoàn thành')
                  AND lh.bac_si_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM phieu_kham pk
                      WHERE pk.lich_hen_id = lh.id AND pk.trang_thai = N'Hoàn thành'
                  )
            ''')
            completed_unlinked_lh = [dict(r) for r in cursor.fetchall()]

            cursor.execute('''
                SELECT ct.ktv_thuc_hien,
                       CONVERT(VARCHAR(7), COALESCE(ct.thoi_gian_thuc_hien, GETDATE()), 120) AS month_key
                FROM chi_tiet_chi_dinh ct
                LEFT JOIN dich_vu dv ON ct.dich_vu_id = dv.id
                WHERE ct.ktv_thuc_hien IS NOT NULL
                  AND LTRIM(RTRIM(ct.ktv_thuc_hien)) != ''
                  AND (dv.loai_dich_vu IS NULL OR dv.loai_dich_vu NOT IN (N'Khám bệnh', N'Khám chuyên khoa', N'Thủ thuật'))
            ''')
            completed_cls = [dict(r) for r in cursor.fetchall()]

            cursor.execute('''
                SELECT dt.nguoi_duyet,
                       CONVERT(VARCHAR(7), COALESCE(dt.ngay_duyet, dt.thoi_gian_ke, GETDATE()), 120) AS month_key
                FROM don_thuoc dt
                WHERE dt.trang_thai = N'Đã phát'
            ''')
            completed_rx = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

        doc_to_staff = {r['bac_si_id']: r['nhan_vien_id'] for r in all_staff_rows if r.get('bac_si_id')}
        name_to_staff = {(r.get('ho_ten') or '').strip().lower(): r['nhan_vien_id'] for r in all_staff_rows if r.get('ho_ten')}

        discovered_months = set(recent_months)
        for sh in raw_shifts:
            d_str = str(sh.get('ngay_lam') or '')[:7]
            if len(d_str) == 7 and d_str[4] == '-':
                discovered_months.add(d_str)
        for pk_item in completed_pk + completed_unlinked_lh:
            mk = str(pk_item.get('month_key') or '')[:7]
            if len(mk) == 7 and mk[4] == '-':
                discovered_months.add(mk)

        available_months = sorted(discovered_months, reverse=True)
        if not selected_month:
            selected_month = cur_month_key if cur_month_key in available_months else (available_months[0] if available_months else cur_month_key)
        selected_month = str(selected_month).strip()
        is_all_months = selected_month.upper() == 'ALL'

        def staff_allowed(nv_id):
            if target_staff_ids is None:
                return True
            return nv_id in target_staff_ids

        status_labels = {
            'DA_DUYET': 'Đã duyệt',
            'CHO_DUYET': 'Chờ duyệt',
            'CHO_HUY': 'Chờ duyệt hủy',
            'TU_CHOI': 'Từ chối',
            'DA_HUY': 'Đã hủy'
        }

        month_buckets = {
            mk: {
                'month_key': mk,
                'month_label': f"Tháng {mk[5:7]}/{mk[:4]}",
                'so_ca_dang_ky': 0,
                'so_ca_da_duyet': 0,
                'so_ca_da_lam': 0,
                'gio_cong_da_lam': 0.0,
                'tong_gio_duyet': 0.0,
                'so_ca_kham_hoan_thanh': 0
            }
            for mk in available_months
        }

        per_staff = {}
        for st in all_staff_rows:
            nv_id = st['nhan_vien_id']
            if not staff_allowed(nv_id):
                continue
            per_staff[nv_id] = {
                'id': nv_id,
                'nhan_vien_id': nv_id,
                'ma_nhan_vien': st.get('ma_nhan_vien') or f"NV{nv_id:03d}",
                'ho_ten': st.get('ho_ten') or 'Nhân viên',
                'vai_tro': st.get('ma_vai_tro') or 'NHANVIEN',
                'ten_vai_tro': st.get('ten_vai_tro') or st.get('chuc_vu') or 'Nhân sự',
                'chuc_vu': st.get('chuc_vu') or '',
                'ten_khoa': st.get('ten_khoa') or 'Khối Vận Hành / Hành Chính',
                'ten_chuyen_khoa': st.get('ten_khoa') or 'Khối Vận Hành / Hành Chính',
                'bac_si_id': st.get('bac_si_id'),
                'is_me': (own_staff_id is not None and int(nv_id) == int(own_staff_id)),
                'so_ca_dang_ky_ky': 0,
                'so_ca_da_duyet_ky': 0,
                'so_ca_da_lam_ky': 0,
                'ca_da_duyet': 0,
                'ca_cho_duyet': 0,
                'ca_tu_choi': 0,
                'tong_ca_dang_ky': 0,
                'gio_cong_da_lam_ky': 0.0,
                'tong_gio_duyet_ky': 0.0,
                'tong_gio_cong_tich_luy': 0.0,
                'tong_so_ca_lich_su': 0,
                'so_ca_kham_hoan_thanh_ky': 0,
                'tong_ca_kham_hoan_thanh': 0,
                'so_nghiep_vu_phu_ky': 0,
                'tong_nghiep_vu_phu': 0
            }

        shift_history = []
        for sh in raw_shifts:
            nv_id = sh.get('nhan_vien_id')
            if not nv_id and sh.get('bac_si_id'):
                nv_id = doc_to_staff.get(sh['bac_si_id'])
            if not nv_id or not staff_allowed(nv_id):
                continue

            day_str = str(sh.get('ngay_lam') or '')[:10]
            mk = day_str[:7]
            ca_num = int(sh.get('ca_lam') or 1)
            ca_meta = ScheduleModel.CA_LAM_INFO.get(ca_num, ScheduleModel.CA_LAM_INFO[1])
            g_start = str(sh.get('gio_bat_dau') or ca_meta['bat_dau'])[:5]
            g_end = str(sh.get('gio_ket_thuc') or ca_meta['ket_thuc'])[:5]
            hours = ScheduleModel._calc_shift_hours(g_start, g_end, ca_num)

            tt_duyet = (sh.get('trang_thai_duyet') or 'DA_DUYET').strip()
            active_flag = sh.get('trang_thai')
            if active_flag == 0 and tt_duyet == 'DA_DUYET':
                tt_duyet = 'DA_HUY'

            is_approved = (tt_duyet in ('DA_DUYET', 'CHO_HUY') and (active_flag == 1 or active_flag is None))
            is_past_day = day_str < today_iso
            is_today_done = False
            if day_str == today_iso:
                try:
                    is_today_done = clock(g_end) <= now_time
                except Exception:
                    is_today_done = False
            is_worked = is_approved and (is_past_day or is_today_done)
            in_period = is_all_months or (mk == selected_month)

            if mk in month_buckets:
                month_buckets[mk]['so_ca_dang_ky'] += 1
                if is_approved:
                    month_buckets[mk]['so_ca_da_duyet'] += 1
                    month_buckets[mk]['tong_gio_duyet'] = round(month_buckets[mk]['tong_gio_duyet'] + hours, 2)
                if is_worked:
                    month_buckets[mk]['so_ca_da_lam'] += 1
                    month_buckets[mk]['gio_cong_da_lam'] = round(month_buckets[mk]['gio_cong_da_lam'] + hours, 2)

            if nv_id in per_staff:
                ps = per_staff[nv_id]
                ps['tong_so_ca_lich_su'] += 1
                if is_worked:
                    ps['tong_gio_cong_tich_luy'] = round(ps['tong_gio_cong_tich_luy'] + hours, 2)
                if in_period:
                    ps['so_ca_dang_ky_ky'] += 1
                    ps['tong_ca_dang_ky'] += 1
                    if is_approved:
                        ps['so_ca_da_duyet_ky'] += 1
                        ps['ca_da_duyet'] += 1
                        ps['tong_gio_duyet_ky'] = round(ps['tong_gio_duyet_ky'] + hours, 2)
                    elif tt_duyet in ('CHO_DUYET', 'CHỜ DUYỆT'):
                        ps['ca_cho_duyet'] += 1
                    elif tt_duyet in ('TU_CHOI', 'TỪ CHỐI'):
                        ps['ca_tu_choi'] += 1
                    if is_worked:
                        ps['so_ca_da_lam_ky'] += 1
                        ps['gio_cong_da_lam_ky'] = round(ps['gio_cong_da_lam_ky'] + hours, 2)

            try:
                day_fmt = datetime.strptime(day_str, '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                day_fmt = day_str

            note_parts = [p for p in [sh.get('ghi_chu'), sh.get('ly_do_tu_choi'), sh.get('ly_do_huy')] if p and str(p).strip()]
            shift_history.append({
                'id': sh.get('id'),
                'nhan_vien_id': nv_id,
                'ma_nhan_vien': sh.get('ma_nhan_vien') or f"NV{nv_id:03d}",
                'ho_ten': sh.get('ten_nhan_vien') or 'Nhân viên',
                'vai_tro': sh.get('ma_vai_tro') or 'NHANVIEN',
                'ten_vai_tro': sh.get('ten_vai_tro') or sh.get('chuc_vu') or 'Nhân sự',
                'ten_khoa': sh.get('ten_khoa') or '',
                'ten_phong': sh.get('ten_phong') or 'Theo phân công',
                'ngay_lam': day_str,
                'ngay_lam_fmt': day_fmt,
                'month_key': mk,
                'ca_lam': ca_num,
                'ten_ca': ca_meta['ten'],
                'khung_gio': f"{g_start} - {g_end}",
                'so_gio': hours,
                'trang_thai_duyet': tt_duyet,
                'trang_thai_label': status_labels.get(tt_duyet, tt_duyet),
                'is_past': (is_past_day or is_today_done),
                'is_worked': is_worked,
                'in_selected_month': in_period,
                'nguoi_duyet_ten': sh.get('nguoi_duyet_ten') or '',
                'ghi_chu': ' | '.join(str(x).strip() for x in note_parts),
                'ngay_tao': str(sh.get('ngay_tao') or '')[:16]
            })

        for exam_item in completed_pk + completed_unlinked_lh:
            nv_id = doc_to_staff.get(exam_item.get('bac_si_id'))
            if not nv_id or not staff_allowed(nv_id):
                continue
            mk = str(exam_item.get('month_key') or '')[:7]
            if mk in month_buckets:
                month_buckets[mk]['so_ca_kham_hoan_thanh'] += 1
            if nv_id in per_staff:
                per_staff[nv_id]['tong_ca_kham_hoan_thanh'] += 1
                if is_all_months or mk == selected_month:
                    per_staff[nv_id]['so_ca_kham_hoan_thanh_ky'] += 1

        for cls_item in completed_cls:
            ktv_key = (cls_item.get('ktv_thuc_hien') or '').strip().lower()
            nv_id = name_to_staff.get(ktv_key)
            if nv_id and nv_id in per_staff:
                mk = str(cls_item.get('month_key') or '')[:7]
                per_staff[nv_id]['tong_nghiep_vu_phu'] += 1
                if is_all_months or mk == selected_month:
                    per_staff[nv_id]['so_nghiep_vu_phu_ky'] += 1

        for rx_item in completed_rx:
            rx_key = (rx_item.get('nguoi_duyet') or '').strip().lower()
            nv_id = name_to_staff.get(rx_key)
            if nv_id and nv_id in per_staff:
                mk = str(rx_item.get('month_key') or '')[:7]
                per_staff[nv_id]['tong_nghiep_vu_phu'] += 1
                if is_all_months or mk == selected_month:
                    per_staff[nv_id]['so_nghiep_vu_phu_ky'] += 1

        staff_stats_list = list(per_staff.values())
        for item in staff_stats_list:
            if item['vai_tro'] == 'KTV':
                item['nhan_nghiep_vu_phu'] = 'ca xét nghiệm/CLS'
            elif item['vai_tro'] == 'DUOCSI':
                item['nhan_nghiep_vu_phu'] = 'đơn thuốc đã phát'
            else:
                item['nhan_nghiep_vu_phu'] = ''

        monthly_summary = [month_buckets[mk] for mk in available_months]
        totals = {
            'gio_cong_da_lam_ky': round(sum(s['gio_cong_da_lam_ky'] for s in staff_stats_list), 2),
            'tong_gio_duyet_ky': round(sum(s['tong_gio_duyet_ky'] for s in staff_stats_list), 2),
            'tong_gio_cong_tich_luy': round(sum(s['tong_gio_cong_tich_luy'] for s in staff_stats_list), 2),
            'so_ca_kham_hoan_thanh_ky': sum(s['so_ca_kham_hoan_thanh_ky'] for s in staff_stats_list),
            'tong_ca_kham_hoan_thanh': sum(s['tong_ca_kham_hoan_thanh'] for s in staff_stats_list),
            'tong_luot_dang_ky_lich_su': len(shift_history)
        }

        return {
            'can_view_all': can_view_all,
            'scope': effective_scope,
            'own_staff_id': own_staff_id,
            'selected_month': selected_month,
            'available_months': [
                {'key': mk, 'label': f"Tháng {mk[5:7]}/{mk[:4]}"}
                for mk in available_months
            ],
            'totals': totals,
            'monthly_summary': monthly_summary,
            'staff_stats': staff_stats_list,
            'shift_history': shift_history[:500]
        }
