from datetime import datetime, date
from core.database import get_db
from core.audit import AuditLogger

class AppointmentModel:
    """Model quản lý lịch hẹn khám và tiếp nhận bệnh nhân."""

    @staticmethod
    def get_all():
        """Lấy toàn bộ danh sách lịch hẹn khám kèm thông tin bệnh nhân, bác sĩ và chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                lh.id, lh.ma_lich_hen, lh.ngay_hen, lh.gio_hen, lh.ly_do_kham, lh.trang_thai, lh.ngay_dat,
                lh.benh_nhan_id,
                bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                ck.id AS chuyen_khoa_id, ck.ten_khoa,
                pk.id AS phong_kham_id, pk.ten_phong,
                bs.id AS bac_si_id,
                nv.ho_ten AS ten_bac_si
            FROM lich_hen lh
            JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
            JOIN chuyen_khoa ck ON lh.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON lh.phong_kham_id = pk.id
            LEFT JOIN bac_si bs ON lh.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            ORDER BY lh.ngay_hen DESC, lh.gio_hen DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            item = dict(r)
            raw_tt = item.get('trang_thai') or ''
            if raw_tt in ['Đã khám', 'Hoàn thành']:
                status_code = 'completed'
            elif raw_tt in ['Đã tiếp nhận', 'Đã duyệt', 'Đã xác nhận']:
                status_code = 'confirmed'
            elif raw_tt == 'Đã hủy':
                status_code = 'cancelled'
            else:
                status_code = 'waiting'

            item['status_code'] = status_code
            item['trang_thai_code'] = status_code
            item['ma_hen'] = item.get('ma_lich_hen') or f"LH{item['id']}"
            item['gio_hen_short'] = str(item['gio_hen'])[:5] if item.get('gio_hen') else '08:30'
            item['benh_nhan'] = item.get('ten_benh_nhan') or 'Bệnh nhân'
            item['ma_bn'] = item.get('ma_benh_nhan') or 'BN'
            item['sdt'] = item.get('sdt_benh_nhan') or ''
            item['bac_si'] = item.get('ten_bac_si') or ''
            item['khoa'] = item.get('ten_khoa') or 'Khoa Nội Tổng Quát'
            item['ly_do'] = item.get('ly_do_kham') or 'Khám theo yêu cầu'
            results.append(item)

        return results

    @staticmethod
    def get_by_id(appointment_id):
        """Lấy thông tin chi tiết một lịch hẹn theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                lh.id, lh.ma_lich_hen, lh.ngay_hen, lh.gio_hen, lh.ly_do_kham, lh.trang_thai, lh.ngay_dat,
                lh.benh_nhan_id,
                bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                ck.id AS chuyen_khoa_id, ck.ten_khoa,
                pk.id AS phong_kham_id, pk.ten_phong,
                bs.id AS bac_si_id,
                nv.ho_ten AS ten_bac_si
            FROM lich_hen lh
            JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
            JOIN chuyen_khoa ck ON lh.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON lh.phong_kham_id = pk.id
            LEFT JOIN bac_si bs ON lh.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            WHERE lh.id = ?
        ''', (appointment_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None

        item = dict(row)
        raw_tt = item.get('trang_thai') or ''
        if raw_tt in ['Đã khám', 'Hoàn thành']:
            status_code = 'completed'
        elif raw_tt in ['Đã tiếp nhận', 'Đã duyệt', 'Đã xác nhận']:
            status_code = 'confirmed'
        elif raw_tt == 'Đã hủy':
            status_code = 'cancelled'
        else:
            status_code = 'waiting'

        item['status_code'] = status_code
        item['trang_thai_code'] = status_code
        item['ma_hen'] = item.get('ma_lich_hen') or f"LH{item['id']}"
        item['gio_hen_short'] = str(item['gio_hen'])[:5] if item.get('gio_hen') else '08:30'
        item['benh_nhan'] = item.get('ten_benh_nhan') or 'Bệnh nhân'
        item['ma_bn'] = item.get('ma_benh_nhan') or 'BN'
        item['sdt'] = item.get('sdt_benh_nhan') or ''
        item['bac_si'] = item.get('ten_bac_si') or ''
        item['khoa'] = item.get('ten_khoa') or 'Khoa Nội Tổng Quát'
        item['ly_do'] = item.get('ly_do_kham') or 'Khám theo yêu cầu'
        return item

    @staticmethod
    def get_by_patient(patient_id):
        """Lấy danh sách lịch hẹn của một bệnh nhân cụ thể."""
        all_appts = AppointmentModel.get_all()
        return [a for a in all_appts if a['benh_nhan_id'] == patient_id]

    @staticmethod
    def get_for_user(user):
        """Lấy danh sách lịch hẹn phù hợp theo vai trò người dùng:
        - Admin, Lễ tân: Xem tất cả lịch hẹn.
        - Bác sĩ: Xem lịch hẹn của chính mình VÀ những lịch hẹn chưa có người nhận (cùng chuyên khoa).
        """
        all_appts = AppointmentModel.get_all()
        if not user:
            return all_appts

        role = user.get('vai_tro')
        if role != 'BACSI':
            return all_appts

        doctor_id = user.get('bac_si_id')
        dept_id = user.get('chuyen_khoa_id')
        if not doctor_id and user.get('id'):
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT bs.id, bs.chuyen_khoa_id FROM bac_si bs JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id WHERE nv.tai_khoan_id = ?', (user['id'],))
            r = c.fetchone()
            conn.close()
            if r:
                doctor_id = r[0]
                dept_id = r[1]
        elif not dept_id and doctor_id:
            from models.user_model import UserModel
            doc = UserModel.get_doctor_by_id(doctor_id)
            if doc:
                dept_id = doc.get('chuyen_khoa_id')

        filtered = []
        for a in all_appts:
            # Bác sĩ chỉ thấy các lịch hẹn ĐÃ ĐƯỢC TIẾP NHẬN / DUYỆT bởi Admin hoặc Lễ tân
            if a.get('trang_thai') in ['Chờ tiếp nhận', 'Chờ xác nhận']:
                continue

            # 1. Lịch hẹn do chính bác sĩ phụ trách đã được tiếp nhận
            if doctor_id and a.get('bac_si_id') == doctor_id:
                filtered.append(a)
            # 2. Hoặc lịch hẹn chưa có người nhận nhưng cùng chuyên khoa đã được tiếp nhận
            elif not a.get('bac_si_id') and dept_id and a.get('chuyen_khoa_id') == dept_id:
                filtered.append(a)

        return filtered

    @staticmethod
    def get_doctors_by_shift(ngay_kham, gio_kham, chuyen_khoa_id=None):
        """Lấy danh sách các bác sĩ có ca trực tương ứng với ngày và giờ khám được chọn."""
        t = str(gio_kham).strip()
        if 'AM' in t or 'PM' in t:
            try:
                t = datetime.strptime(t, '%I:%M %p').strftime('%H:%M')
            except Exception:
                pass
        h_m = t[:5]
        if h_m in ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30']:
            shift = 1
        elif h_m in ['14:30', '15:00', '15:30', '16:00']:
            shift = 2
        elif h_m in ['18:30', '19:00', '19:30']:
            shift = 3
        else:
            try:
                hour = int(h_m.split(':')[0])
                if hour < 12:
                    shift = 1
                elif hour < 17:
                    shift = 2
                else:
                    shift = 3
            except Exception:
                shift = 1

        work_date_str = str(ngay_kham)[:10]

        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT 
                bs.id, bs.hoc_vi, bs.avatar, bs.kinh_nghiem, bs.gia_kham,
                nv.ho_ten, nv.sdt,
                ck.id AS chuyen_khoa_id, ck.ten_khoa,
                pk.id AS phong_kham_id, pk.ten_phong,
                llv.ca_lam, llv.gio_bat_dau, llv.gio_ket_thuc,
                llv.so_luong_kham_toi_da, llv.so_luong_da_dang_ky
            FROM lich_lam_viec llv
            JOIN bac_si bs ON llv.bac_si_id = bs.id
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            WHERE llv.ngay_lam = ? 
              AND llv.ca_lam = ?
              AND (llv.trang_thai_duyet = 'DA_DUYET' OR llv.trang_thai_duyet IS NULL)
              AND (llv.trang_thai = 1 OR llv.trang_thai IS NULL)
        '''
        params = [work_date_str, shift]
        if chuyen_khoa_id:
            sql += ' AND bs.chuyen_khoa_id = ?'
            params.append(int(chuyen_khoa_id))

        sql += ' ORDER BY bs.id'
        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows, shift

    @staticmethod
    def assign_doctor(appointment_id, doctor_id, user_info=None):
        """Phân công bác sĩ cho lịch hẹn hoặc bác sĩ tự nhận lịch hẹn."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT phong_kham_chinh_id FROM bac_si WHERE id = ?', (doctor_id,))
            doc_row = cursor.fetchone()
            phong_kham_id = doc_row.get('phong_kham_chinh_id') if doc_row else None

            cursor.execute('''
                UPDATE lich_hen
                SET bac_si_id = ?, phong_kham_id = COALESCE(?, phong_kham_id), trang_thai = 'Đã xác nhận'
                WHERE id = ?
            ''', (doctor_id, phong_kham_id, appointment_id))
            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appointment_id,
                action='ASSIGN_DOCTOR',
                performed_by=user_info.get('id') if user_info else None,
                performed_by_name=user_info.get('ho_ten') if user_info else 'Hệ thống',
                reason=f"Phân công bác sĩ ID {doctor_id} cho lịch hẹn #{appointment_id}"
            )
            return True, "Đã phân công bác sĩ thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def get_doctors_with_availability(chuyen_khoa_id, date_str=None):
        """Lấy danh sách bác sĩ thuộc chuyên khoa kèm số ca trực/lịch trống trong ngày để Admin phân lịch."""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                bs.id, bs.hoc_vi, bs.kinh_nghiem, bs.trang_thai_lam_viec,
                nv.ho_ten, nv.sdt,
                pk.id AS phong_kham_id, pk.ten_phong,
                ck.ten_khoa
            FROM bac_si bs
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON bs.phong_kham_chinh_id = pk.id
            WHERE bs.chuyen_khoa_id = ? AND bs.trang_thai_lam_viec = 'Đang làm việc'
            ORDER BY bs.id ASC
        ''', (chuyen_khoa_id,))
        docs = [dict(r) for r in cursor.fetchall()]

        # Lấy lịch trực và số lượt đã đặt trong ngày đó
        for d in docs:
            cursor.execute('''
                SELECT id, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky
                FROM lich_lam_viec
                WHERE bac_si_id = ? AND ngay_lam = ? AND trang_thai = 1
            ''', (d['id'], date_str))
            shift = cursor.fetchone()
            if shift:
                d['has_shift'] = True
                d['ca_lam'] = shift['ca_lam']
                d['gio_truc'] = f"{str(shift['gio_bat_dau'])[:5]} - {str(shift['gio_ket_thuc'])[:5]}"
                d['max_slots'] = shift['so_luong_kham_toi_da']
                d['booked_slots'] = shift['so_luong_da_dang_ky']
                d['available_slots'] = max(0, shift['so_luong_kham_toi_da'] - shift['so_luong_da_dang_ky'])
            else:
                d['has_shift'] = False
                d['gio_truc'] = 'Theo ca hành chính'
                # Đếm số ca hẹn thực tế trong ngày đó
                cursor.execute('''
                    SELECT COUNT(*) AS cnt FROM lich_hen
                    WHERE bac_si_id = ? AND ngay_hen = ? AND trang_thai != 'Đã hủy'
                ''', (d['id'], date_str))
                cnt_row = cursor.fetchone()
                d['booked_slots'] = cnt_row['cnt'] if cnt_row else 0
                d['max_slots'] = 20
                d['available_slots'] = max(0, 20 - d['booked_slots'])

        conn.close()
        return docs

    @staticmethod
    def create(benh_nhan_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do_kham, audit_user=None):
        """Tạo lịch hẹn khám mới kèm kiểm tra ca trực và gửi thông báo in-app."""
        # Kiểm tra ngày giờ hợp lệ (không cho đặt trong quá khứ)
        try:
            work_date_str = str(ngay_hen)[:10]
            work_time_str = str(gio_hen)[:5]
            appt_dt = datetime.strptime(f"{work_date_str} {work_time_str}", '%Y-%m-%d %H:%M')
            if appt_dt < datetime.now():
                return False, "Không thể đặt lịch hẹn vào thời gian trong quá khứ!"
        except Exception:
            return False, "Định dạng ngày hẹn hoặc giờ hẹn không hợp lệ (YYYY-MM-DD HH:MM)!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Kiểm tra chuyên khoa hoạt động
            cursor.execute('SELECT ten_khoa, trang_thai FROM chuyen_khoa WHERE id = ?', (chuyen_khoa_id,))
            ck = cursor.fetchone()
            if not ck or ck['trang_thai'] != 1:
                conn.close()
                return False, "Chuyên khoa khám này hiện đang tạm ngưng tiếp nhận!"

            # 2. Kiểm tra bác sĩ (nếu chỉ định bác sĩ)
            ten_bac_si = "Bác sĩ chuyên khoa"
            phong_kham_id = None
            if bac_si_id:
                cursor.execute('''
                    SELECT nv.ho_ten, bs.trang_thai_lam_viec, nv.trang_thai, bs.phong_kham_chinh_id 
                    FROM bac_si bs
                    JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                    WHERE bs.id = ?
                ''', (bac_si_id,))
                bs = cursor.fetchone()
                if not bs or bs['trang_thai'] != 1 or bs['trang_thai_lam_viec'] != 'Đang làm việc':
                    conn.close()
                    return False, "Bác sĩ được chọn hiện không có lịch làm việc hoặc đang nghỉ phép!"
                ten_bac_si = bs['ho_ten']
                phong_kham_id = bs.get('phong_kham_chinh_id')

            # 3. Kiểm tra và cập nhật ca trực trong lich_lam_viec (nếu có lịch trực)
            cursor.execute('''
                SELECT id, so_luong_kham_toi_da, so_luong_da_dang_ky, phong_kham_id
                FROM lich_lam_viec
                WHERE bac_si_id = ? AND ngay_lam = ? AND trang_thai = 1
            ''', (bac_si_id, work_date_str) if bac_si_id else (-1, work_date_str))
            schedule_row = cursor.fetchone()
            if schedule_row:
                if schedule_row['so_luong_da_dang_ky'] >= schedule_row['so_luong_kham_toi_da']:
                    conn.close()
                    return False, f"Ca khám của bác sĩ {ten_bac_si} ngày {work_date_str} đã hết lượt đăng ký (tối đa {schedule_row['so_luong_kham_toi_da']} lượt)!"
                cursor.execute('''
                    UPDATE lich_lam_viec
                    SET so_luong_da_dang_ky = so_luong_da_dang_ky + 1
                    WHERE id = ?
                ''', (schedule_row['id'],))
                if not phong_kham_id:
                    phong_kham_id = schedule_row.get('phong_kham_id')

            # 4. Tạo mã lịch hẹn
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM lich_hen')
            next_id = cursor.fetchone()['next_id']
            ma_lich_hen = f"LH2609{str(next_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ma_lich_hen, benh_nhan_id, bac_si_id if bac_si_id else None, chuyen_khoa_id, phong_kham_id, work_date_str, gio_hen, ly_do_kham, 'Chờ tiếp nhận'))
            created_appt_id = cursor.lastrowid

            # 5. Tạo thông báo In-App cho bệnh nhân
            cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (benh_nhan_id,))
            bn_row = cursor.fetchone()
            if bn_row and bn_row.get('tai_khoan_id'):
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, 'Đặt lịch hẹn', '/patient/dashboard', 0, ?)
                ''', (
                    bn_row['tai_khoan_id'],
                    f"Đăng ký khám thành công: {ma_lich_hen}",
                    f"Quý khách đã đặt lịch khám tại {ck['ten_khoa']} ({work_date_str} lúc {gio_hen}). Trạng thái: Chờ tiếp nhận.",
                    now_str
                ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=created_appt_id,
                action='BOOK_APPOINTMENT',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else (bn_row['ho_ten'] if bn_row else 'Bệnh nhân'),
                reason='Đặt lịch khám mới',
                after_data={'ma_lich_hen': ma_lich_hen, 'ngay_hen': work_date_str, 'gio_hen': gio_hen, 'chuyen_khoa_id': chuyen_khoa_id, 'bac_si_id': bac_si_id}
            )

            return True, ma_lich_hen
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def reschedule(appointment_id, new_date, new_time, ly_do=None, new_doctor_id=None, user_info=None):
        """Đổi ngày giờ lịch hẹn theo ràng buộc thời gian và quyền hạn."""
        appt = AppointmentModel.get_by_id(appointment_id)
        if not appt:
            return False, "Không tìm thấy thông tin lịch hẹn!"

        # Kiểm tra trạng thái hiện tại
        if appt['trang_thai'] in ['Đã hủy', 'Hoàn thành']:
            return False, f"Không thể đổi lịch hẹn đang ở trạng thái '{appt['trang_thai']}'!"

        # Quyền hạn và thời gian:
        is_staff = user_info and user_info.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI']
        user_role = user_info.get('vai_tro') if user_info else 'BENHNHAN'

        if user_role == 'BENHNHAN':
            # Bệnh nhân chỉ được thao tác trên lịch hẹn của chính mình
            patient_id = user_info.get('patient_id')
            if not patient_id or appt['benh_nhan_id'] != patient_id:
                return False, "Bạn chỉ được phép thay đổi lịch hẹn của chính mình!"

            # Kiểm tra thời gian trước giờ khám
            try:
                curr_appt_dt = datetime.strptime(f"{str(appt['ngay_hen'])[:10]} {str(appt['gio_hen'])[:5]}", '%Y-%m-%d %H:%M')
                if curr_appt_dt <= datetime.now():
                    return False, "Đã quá thời gian khám của lịch hẹn! Chỉ nhân viên y tế mới có quyền điều phối sau giờ khám."
            except Exception:
                pass

        # Kiểm tra ngày giờ mới phải là tương lai
        try:
            new_date_str = str(new_date)[:10]
            new_time_str = str(new_time)[:5]
            new_dt = datetime.strptime(f"{new_date_str} {new_time_str}", '%Y-%m-%d %H:%M')
            if new_dt <= datetime.now():
                return False, "Thời gian hẹn mới phải ở tương lai!"
        except Exception:
            return False, "Định dạng ngày hẹn hoặc giờ hẹn mới không hợp lệ (YYYY-MM-DD HH:MM)!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            doc_id = new_doctor_id or appt.get('bac_si_id')
            # Kiểm tra ca trực ngày mới nếu có bác sĩ
            if doc_id:
                cursor.execute('''
                    SELECT id, so_luong_kham_toi_da, so_luong_da_dang_ky
                    FROM lich_lam_viec
                    WHERE bac_si_id = ? AND ngay_lam = ? AND trang_thai = 1
                ''', (doc_id, new_date_str))
                new_sch = cursor.fetchone()
                if new_sch and new_sch['so_luong_da_dang_ky'] >= new_sch['so_luong_kham_toi_da']:
                    conn.close()
                    return False, f"Bác sĩ đã kín lịch vào ngày {new_date_str}!"

                # Tăng lượt đăng ký ca mới
                if new_sch:
                    cursor.execute('UPDATE lich_lam_viec SET so_luong_da_dang_ky = so_luong_da_dang_ky + 1 WHERE id = ?', (new_sch['id'],))

                # Giảm lượt ca cũ nếu ngày hoặc bác sĩ thay đổi
                if str(appt['ngay_hen'])[:10] != new_date_str or appt.get('bac_si_id') != doc_id:
                    cursor.execute('''
                        UPDATE lich_lam_viec 
                        SET so_luong_da_dang_ky = CASE WHEN so_luong_da_dang_ky > 0 THEN so_luong_da_dang_ky - 1 ELSE 0 END
                        WHERE bac_si_id = ? AND ngay_lam = ?
                    ''', (appt.get('bac_si_id'), str(appt['ngay_hen'])[:10]))

            new_ly_do = ly_do if ly_do else appt.get('ly_do_kham')
            cursor.execute('''
                UPDATE lich_hen
                SET ngay_hen = ?, gio_hen = ?, bac_si_id = ?, ly_do_kham = ?
                WHERE id = ?
            ''', (new_date_str, new_time_str, doc_id, new_ly_do, appointment_id))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appointment_id,
                action='RESCHEDULE_APPOINTMENT',
                performed_by=user_info.get('id') if user_info else None,
                performed_by_name=user_info.get('ho_ten') if user_info else 'Người dùng',
                reason=f"Đổi lịch khám sang {new_date_str} {new_time_str}",
                before_data={'ngay_hen': str(appt['ngay_hen']), 'gio_hen': str(appt['gio_hen'])},
                after_data={'ngay_hen': new_date_str, 'gio_hen': new_time_str, 'bac_si_id': doc_id}
            )

            return True, "Đổi lịch hẹn khám thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi đổi lịch hẹn: {str(e)}"

    @staticmethod
    def cancel(appointment_id, reason=None, user_info=None):
        """Hủy lịch hẹn khám: cập nhật trạng thái 'Đã hủy', giải phóng chỗ ca trực, ghi audit log."""
        appt = AppointmentModel.get_by_id(appointment_id)
        if not appt:
            return False, "Không tìm thấy thông tin lịch hẹn!"

        if appt['trang_thai'] == 'Đã hủy':
            return False, "Lịch hẹn này đã được hủy trước đó!"

        if appt['trang_thai'] == 'Hoàn thành':
            return False, "Không thể hủy lịch hẹn đã hoàn thành khám bệnh!"

        user_role = user_info.get('vai_tro') if user_info else 'BENHNHAN'

        # Nếu là bệnh nhân, kiểm tra quyền sở hữu và thời gian trước giờ khám
        if user_role == 'BENHNHAN':
            patient_id = user_info.get('patient_id')
            if not patient_id or appt['benh_nhan_id'] != patient_id:
                return False, "Bạn chỉ được phép hủy lịch hẹn của chính mình!"

            try:
                curr_appt_dt = datetime.strptime(f"{str(appt['ngay_hen'])[:10]} {str(appt['gio_hen'])[:5]}", '%Y-%m-%d %H:%M')
                if curr_appt_dt <= datetime.now():
                    return False, "Đã quá thời gian hẹn khám! Chỉ nhân viên y tế mới có quyền hủy lịch sau giờ khám."
            except Exception:
                pass

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Cập nhật trạng thái thành 'Đã hủy'
            cursor.execute("UPDATE lich_hen SET trang_thai = ? WHERE id = ?", ('Đã hủy', appointment_id))

            # 2. Giảm số lượng đăng ký ca trực nếu có
            if appt.get('bac_si_id'):
                cursor.execute('''
                    UPDATE lich_lam_viec
                    SET so_luong_da_dang_ky = CASE WHEN so_luong_da_dang_ky > 0 THEN so_luong_da_dang_ky - 1 ELSE 0 END
                    WHERE bac_si_id = ? AND ngay_lam = ?
                ''', (appt['bac_si_id'], str(appt['ngay_hen'])[:10]))

            # 3. Gửi thông báo cho bệnh nhân nếu hủy bởi nhân viên
            if user_role in ['ADMIN', 'LETAN', 'BACSI']:
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (appt['benh_nhan_id'],))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ly_do_text = f" Lý do: {reason}." if reason else ""
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, 'Hủy lịch hẹn', '/patient/dashboard', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Lịch hẹn {appt['ma_lich_hen']} đã bị hủy",
                        f"Phòng khám xin thông báo lịch hẹn ngày {appt['ngay_hen']} của bạn đã được hủy.{ly_do_text}",
                        now_str
                    ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appointment_id,
                action='CANCEL_APPOINTMENT',
                performed_by=user_info.get('id') if user_info else None,
                performed_by_name=user_info.get('ho_ten') if user_info else 'Người dùng',
                reason=reason or 'Hủy lịch hẹn khám',
                before_data={'trang_thai': appt['trang_thai']},
                after_data={'trang_thai': 'Đã hủy'}
            )

            return True, "Đã hủy lịch hẹn khám thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi hủy lịch hẹn: {str(e)}"

    @staticmethod
    def update_status(appointment_id, new_status, user_info=None):
        """Cập nhật trạng thái lịch hẹn khám và ghi audit trail."""
        appt = AppointmentModel.get_by_id(appointment_id)
        if not appt:
            return False, "Không tìm thấy lịch hẹn!"

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE lich_hen SET trang_thai = ? WHERE id = ?', (new_status, appointment_id))

            # Nếu tiếp nhận hoặc xác nhận lịch hẹn, tự động gửi thông báo in-app cho bệnh nhân
            if new_status in ['Đã tiếp nhận', 'Đã xác nhận']:
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (appt['benh_nhan_id'],))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    khoa_name = appt.get('ten_khoa') or 'Chuyên khoa'
                    bs_name = appt.get('ten_bac_si') or 'Bác sĩ phụ trách'
                    tieu_de = f"Tiếp nhận thành công lịch khám: {appt['ma_lich_hen']}"
                    noi_dung = (
                        f"Kính gửi {bn_row['ho_ten']}, lịch hẹn khám bệnh mã {appt['ma_lich_hen']} của bạn "
                        f"vào ngày {appt['ngay_hen']} lúc {str(appt['gio_hen'])[:5]} tại {khoa_name} ({bs_name}) "
                        f"đã được nhân viên Lễ tân tiếp nhận thành công. Xin vui lòng có mặt trước giờ khám 15 phút tại Quầy tiếp đón."
                    )
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Lịch hẹn', '/patient/booking', 0, ?)
                    ''', (bn_row['tai_khoan_id'], tieu_de, noi_dung, now_str))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appointment_id,
                action='UPDATE_APPOINTMENT_STATUS',
                performed_by=user_info.get('id') if user_info else None,
                performed_by_name=user_info.get('ho_ten') if user_info else 'Nhân viên',
                reason=f"Đổi trạng thái lịch {appt['ma_lich_hen']} sang '{new_status}'",
                before_data={'trang_thai': appt['trang_thai']},
                after_data={'trang_thai': new_status}
            )

            return True, 'Cập nhật trạng thái thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

