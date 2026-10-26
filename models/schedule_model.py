from datetime import datetime, date, timedelta
from core.database import get_db

class ScheduleModel:
    """Model quản lý lịch làm việc, phân ca trực, duyệt đăng ký và hủy ca trực."""

    CA_LAM_INFO = {
        1: {'ten': 'Ca sáng', 'bat_dau': '07:00:00', 'ket_thuc': '11:30:00'},
        2: {'ten': 'Ca chiều', 'bat_dau': '13:30:00', 'ket_thuc': '17:00:00'},
        3: {'ten': 'Ca tối', 'bat_dau': '17:30:00', 'ket_thuc': '20:30:00'}
    }

    @staticmethod
    def get_week_bounds(target_date=None):
        """Tính toán khoảng ngày của tuần hiện tại và 2 tuần tiếp theo."""
        if not target_date:
            today = date.today()
        elif isinstance(target_date, str):
            today = datetime.strptime(str(target_date)[:10], '%Y-%m-%d').date()
        else:
            today = target_date

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
              AND (llv.trang_thai_duyet = 'DA_DUYET' OR llv.trang_thai_duyet IS NULL)
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
              AND (llv.trang_thai_duyet = 'DA_DUYET' OR llv.trang_thai_duyet IS NULL)
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
            r['can_request_cancel'] = bool(is_mine and r['is_current_week'] and r.get('trang_thai_duyet') == 'DA_DUYET')

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
                ca_lam = ca_map.get(ca_lam.strip().lower(), 1)
            else:
                ca_lam = int(ca_lam)
            if ca_lam not in [1, 2, 3]:
                ca_lam = 1
            work_date = datetime.strptime(str(ngay_lam)[:10], '%Y-%m-%d').date()
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
        pk_id = phong_kham_id or staff_row.get('phong_kham_chinh_id') or 1

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

        new_status = 'DA_HUY' if approved else 'DA_DUYET'
        active_status = 0 if approved else 1

        cursor.execute('''
            UPDATE lich_lam_viec
            SET trang_thai_duyet = ?, trang_thai = ?, nguoi_duyet_id = ?, ngay_duyet = GETDATE()
            WHERE id = ?
        ''', (new_status, active_status, reviewer_user.get('id'), schedule_id))

        if approved:
            cursor.execute('SELECT bac_si_id, ngay_lam, ca_lam FROM lich_lam_viec WHERE id = ?', (schedule_id,))
            sch_info = cursor.fetchone()
            if sch_info and sch_info.get('bac_si_id'):
                # Chuyển các lịch hẹn chưa khám đã gán cho bác sĩ này về Chờ tiếp nhận để Lễ tân điều phối lại
                cursor.execute('''
                    UPDATE lich_hen
                    SET bac_si_id = NULL, trang_thai = N'Chờ tiếp nhận'
                    WHERE bac_si_id = ? AND ngay_hen = ? AND trang_thai IN (N'Chờ tiếp nhận', N'Đã tiếp nhận', N'Chờ xác nhận')
                ''', (sch_info['bac_si_id'], sch_info['ngay_lam']))

                from models.notification_model import NotificationModel
                NotificationModel.notify_admins_and_receptionists(
                    tieu_de="Điều phối lịch khám (Bác sĩ hủy ca)",
                    noi_dung=f"Bác sĩ đã được duyệt hủy ca trực ngày {sch_info['ngay_lam']}. Vui lòng kiểm tra và phân công bác sĩ thay thế cho các lịch hẹn.",
                    loai_thong_bao="Lịch khám",
                    lien_ket="/admin/reception"
                )

        conn.commit()
        conn.close()
        msg = "Đã duyệt hủy ca trực thành công!" if approved else "Đã từ chối đơn xin hủy, ca trực vẫn được duy trì."
        return True, msg

    @staticmethod
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

        if approved:
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

                if approved:
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
            except Exception:
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
        return True, f"Đã {action_msg} thành công {success_count} ca làm việc!", success_count

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
    def create_schedule(bac_si_id, phong_kham_id, ngay_lam, ca_lam=1, gio_bat_dau=None, gio_ket_thuc=None, so_luong_kham_toi_da=20, nhan_vien_id=None):
        """Admin sắp xếp phân ca trực cho bất kỳ nhân viên nào."""
        conn = get_db()
        cursor = conn.cursor()

        # Nếu chưa có nhan_vien_id nhưng có bac_si_id, tra cứu từ bac_si
        if not nhan_vien_id and bac_si_id:
            cursor.execute('SELECT nhan_vien_id FROM bac_si WHERE id = ?', (bac_si_id,))
            bs_row = cursor.fetchone()
            if bs_row:
                nhan_vien_id = bs_row['nhan_vien_id']

        # Nếu có nhan_vien_id nhưng chưa có bac_si_id, tra cứu nếu là bác sĩ
        if nhan_vien_id and not bac_si_id:
            cursor.execute('SELECT id FROM bac_si WHERE nhan_vien_id = ?', (nhan_vien_id,))
            bs_row = cursor.fetchone()
            if bs_row:
                bac_si_id = bs_row['id']

        if not nhan_vien_id and not bac_si_id:
            conn.close()
            return False, "Vui lòng chọn nhân viên hoặc bác sĩ để xếp lịch!"

        try:
            ca_lam = int(ca_lam)
            if ca_lam not in [1, 2, 3]:
                ca_lam = 1
            so_luong_kham_toi_da = int(so_luong_kham_toi_da) if so_luong_kham_toi_da else 20
            work_date = datetime.strptime(str(ngay_lam)[:10], '%Y-%m-%d').date()
        except Exception:
            conn.close()
            return False, "Thông tin ngày hoặc ca làm việc không hợp lệ!"

        ca_info = ScheduleModel.CA_LAM_INFO.get(ca_lam, ScheduleModel.CA_LAM_INFO[1])
        gio_bat_dau = gio_bat_dau or ca_info['bat_dau']
        gio_ket_thuc = gio_ket_thuc or ca_info['ket_thuc']

        if work_date < date.today():
            conn.close()
            return False, "Không thể phân ca trực cho ngày trong quá khứ!"

        # Lấy vai trò của nhân sự để kiểm tra giới hạn 5 người
        cursor.execute('''
            SELECT t.vai_tro_id, v.ten_vai_tro
            FROM nhan_vien nv
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN vai_tro v ON t.vai_tro_id = v.id
            WHERE nv.id = ?
        ''', (nhan_vien_id,))
        role_row = cursor.fetchone()
        if role_row:
            cnt, max_cap, is_full = ScheduleModel.check_role_shift_capacity(work_date, ca_lam, role_row['vai_tro_id'])
            if is_full:
                conn.close()
                return False, f"{ca_info['ten']} ngày {work_date} đã đủ tối đa {max_cap} người thuộc bộ phận {role_row['ten_vai_tro']}!"

        # Kiểm tra trùng ca cùng ngày
        cursor.execute('''
            SELECT id FROM lich_lam_viec
            WHERE nhan_vien_id = ? AND ngay_lam = ? AND ca_lam = ? AND (trang_thai_duyet != 'DA_HUY' OR trang_thai_duyet IS NULL)
        ''', (nhan_vien_id, str(work_date), ca_lam))
        if cursor.fetchone():
            conn.close()
            return False, f"Xung đột lịch trực: Nhân sự này đã có lịch trực vào {ca_info['ten']} ngày {work_date}!"

        # Nếu là bác sĩ và có phòng khám, kiểm tra xung đột phòng
        if bac_si_id and phong_kham_id:
            cursor.execute('''
                SELECT llv.id, nv.ho_ten
                FROM lich_lam_viec llv
                JOIN bac_si bs ON llv.bac_si_id = bs.id
                JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE llv.phong_kham_id = ? AND llv.ngay_lam = ? AND llv.ca_lam = ? AND (llv.trang_thai_duyet != 'DA_HUY' OR llv.trang_thai_duyet IS NULL)
            ''', (phong_kham_id, str(work_date), ca_lam))
            conflict_pk = cursor.fetchone()
            if conflict_pk:
                conn.close()
                return False, f"Xung đột phòng khám: Phòng khám này đã có bác sĩ '{conflict_pk['ho_ten']}' trực vào {ca_info['ten']} ngày {work_date}!"

        pk_id = phong_kham_id if phong_kham_id else (1 if bac_si_id else None)

        cursor.execute('''
            INSERT INTO lich_lam_viec (nhan_vien_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai, trang_thai_duyet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 'DA_DUYET')
        ''', (nhan_vien_id, bac_si_id, pk_id, str(work_date), ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da))

        conn.commit()
        sc_id = cursor.lastrowid
        conn.close()
        return True, sc_id

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
        """Bật hoặc tắt trạng thái kích hoạt của ca làm việc."""
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
    def delete_schedule(schedule_id, current_user=None):
        """Xóa ca trực (Nhân viên chỉ xóa được ca trong 2 tuần tiếp theo, Admin xóa mọi ca chưa có bệnh nhân)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
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
              AND (llv.trang_thai_duyet = 'DA_DUYET' OR llv.trang_thai_duyet IS NULL)
              AND bs.trang_thai_lam_viec = 'Đang làm việc'
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
    def register_multiple_schedules(user, shifts, phong_kham_id=None, ghi_chu=None, chuyen_khoa_id=None):
        """Nhân viên đăng ký nhiều ca làm việc cùng lúc trong 2 tuần tiếp theo."""
        if not user or not user.get('id'):
            return False, "Vui lòng đăng nhập để đăng ký ca trực!", []
        if not shifts or not isinstance(shifts, list):
            return False, "Vui lòng chọn ít nhất một ca làm việc!", []

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
            NotificationModel.notify_admins_and_receptionists(
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
