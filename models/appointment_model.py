from datetime import datetime, date
from core.scheduling import (scheduling_db as get_db, serialized, shift_at, clock,
                             booking_target, schedule_for, sync_count, CalendarError)
from core.audit import AuditLogger

class AppointmentModel:
    @staticmethod
    def normalize_date(date_val):
        """Chuẩn hóa ngày sang chuỗi YYYY-MM-DD từ đa định dạng."""
        if not date_val:
            return None
        if isinstance(date_val, (datetime, date)):
            return date_val.strftime('%Y-%m-%d')
        s = str(date_val).strip()[:10]
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
            except ValueError:
                pass
        return s

    @staticmethod
    def normalize_time(time_val):
        """Chuẩn hóa giờ sang chuỗi HH:MM từ 12h/24h hoặc giờ lẻ."""
        try:
            return clock(time_val).strftime('%H:%M')
        except CalendarError:
            return None

    @staticmethod
    def get_shift_from_time(time_str):
        """Xác định ca làm việc (1: Sáng, 2: Chiều, 3: Tối) chuẩn xác theo giờ."""
        return shift_at(time_str)

    @staticmethod
    def get_time_slots_status(date_val, chuyen_khoa_id=None, bac_si_id=None):
        """Advisory only; booking validates again under the transaction lock."""
        day = AppointmentModel.normalize_date(date_val)
        conn = get_db()
        cursor = conn.cursor()
        shifts = []
        slots = {1: ['07:30','08:00','08:30','09:00','09:30','10:00','10:30','11:00'],
                 2: ['13:30','14:00','14:30','15:00','15:30','16:00','16:30'],
                 3: ['17:30','18:00','18:30','19:00','19:30','20:00']}
        try:
            departments = [chuyen_khoa_id] if chuyen_khoa_id else []
            if not departments:
                cursor.execute('SELECT id FROM chuyen_khoa WHERE trang_thai = 1')
                departments = [row['id'] for row in cursor.fetchall()]
            for shift, times in slots.items():
                items = []
                for value in times:
                    available = False
                    reason = 'Không có ca phù hợp hoặc đã hết chỗ.'
                    for department in departments:
                        try:
                            booking_target(cursor,None,department,bac_si_id,day,value,availability=True)
                            available = True
                            break
                        except CalendarError as exc:
                            reason = str(exc)
                    items.append({'time':value,'selectable':available,
                                  'status':'available' if available else 'off_duty',
                                  'color':'green' if available else 'red',
                                  'label':'Còn trống' if available else 'Không khả dụng',
                                  'reason':'Khung giờ khả dụng' if available else reason})
                shifts.append({'shift':shift,'name':{1:'Ca sáng',2:'Ca chiều',3:'Ca tối'}[shift],
                               'has_shift':any(item['selectable'] for item in items),'slots':items})
            return {'success':True,'date':day,'department_id':chuyen_khoa_id,'doctor_id':bac_si_id,'shifts':shifts}
        finally:
            conn.close()

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
            WHERE (TRY_CAST(? AS INT) IS NOT NULL AND lh.id = TRY_CAST(? AS INT)) OR lh.ma_lich_hen = ?
        ''', (str(appointment_id), str(appointment_id), str(appointment_id)))
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
        work_time_str = AppointmentModel.normalize_time(gio_kham)
        shift = AppointmentModel.get_shift_from_time(work_time_str)
        work_date_str = AppointmentModel.normalize_date(ngay_kham)
        if shift is None:
            return [], None

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
              AND llv.trang_thai_duyet = 'DA_DUYET'
              AND llv.trang_thai = 1
              AND nv.trang_thai = 1 AND ck.trang_thai = 1 AND pk.trang_thai = 1
        '''
        params = [work_date_str, shift]
        if chuyen_khoa_id:
            sql += ' AND bs.chuyen_khoa_id = ?'
            params.append(int(chuyen_khoa_id))

        sql += ' ORDER BY bs.id'
        cursor.execute(sql, tuple(params))
        candidates = [dict(row) for row in cursor.fetchall()]
        rows = []
        try:
            for row in candidates:
                try:
                    booking_target(cursor,None,row['chuyen_khoa_id'],row['id'],work_date_str,work_time_str,availability=True)
                except CalendarError:
                    continue
                now = datetime.now()
                row['is_active_now'] = (work_date_str == now.date().isoformat()
                                        and clock(row['gio_bat_dau']) <= now.time() < clock(row['gio_ket_thuc']))
                row['trang_thai_hoat_dong'] = 'Đang làm việc' if row['is_active_now'] else 'Ngoài giờ làm việc'
                rows.append(row)
        finally:
            conn.close()

        return rows, shift

    @staticmethod
    @serialized
    def assign_doctor(appointment_id, doctor_id, user_info=None):
        """Phân công bác sĩ cho lịch hẹn hoặc bác sĩ tự nhận lịch hẹn và cập nhật quota ca trực."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, ngay_hen, gio_hen, bac_si_id 
                FROM lich_hen 
                WHERE (TRY_CAST(? AS INT) IS NOT NULL AND id = TRY_CAST(? AS INT)) OR ma_lich_hen = ?
            ''', (str(appointment_id), str(appointment_id), str(appointment_id)))
            appt_row = cursor.fetchone()
            if not appt_row:
                conn.close()
                return False, "Không tìm thấy lịch hẹn khám!"

            real_id = appt_row['id']
            cursor.execute('SELECT * FROM lich_hen WHERE id = ?', (real_id,))
            original = cursor.fetchone()
            if original['trang_thai'] in ('Đã hủy', 'Hoàn thành', 'Đã khám'):
                raise CalendarError('Lịch hẹn đã kết thúc.')
            target = booking_target(cursor, original['benh_nhan_id'], original['chuyen_khoa_id'],
                                    doctor_id, str(original['ngay_hen'])[:10], original['gio_hen'], exclude=real_id)
            old = (schedule_for(cursor, original['bac_si_id'], str(original['ngay_hen'])[:10],
                                 original['gio_hen'], approved=False) if original.get('bac_si_id') else None)
            cursor.execute('UPDATE lich_hen SET bac_si_id = ?, phong_kham_id = ?, trang_thai = ? WHERE id = ?',
                           (target['bac_si_id'], target['phong_kham_id'], 'Đã tiếp nhận', real_id))
            sync_count(cursor, target)
            if old and old['id'] != target['id']:
                sync_count(cursor, old)
            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=real_id,
                action='ASSIGN_DOCTOR',
                performed_by=user_info.get('id') if user_info else None,
                performed_by_name=user_info.get('ho_ten') if user_info else 'Hệ thống',
                reason=f"Phân công bác sĩ ID {doctor_id} cho lịch hẹn #{real_id}"
            )
            return True, "Đã phân công bác sĩ và cập nhật ca trực thành công!"
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            return False, str(e)

    @staticmethod
    def get_doctors_with_availability(chuyen_khoa_id, date_str=None):
        """Aggregate actual approved shifts only."""
        from models.schedule_model import ScheduleModel
        rows = ScheduleModel.get_available_doctors(chuyen_khoa_id,date_str or date.today().isoformat())
        docs = {}
        for row in rows:
            doctor = docs.setdefault(row['bac_si_id'], dict(row,id=row['bac_si_id'],ho_ten=row['ten_bac_si'],
                                                           has_shift=True,booked_slots=0,max_slots=0,available_slots=0))
            doctor['booked_slots'] += row.get('so_luong_da_dang_ky') or 0
            doctor['max_slots'] += row.get('so_luong_kham_toi_da') or 0
            doctor['available_slots'] = max(0,doctor['max_slots']-doctor['booked_slots'])
            doctor['gio_truc'] = str(row['gio_bat_dau'])[:5]+' - '+str(row['gio_ket_thuc'])[:5]
        return list(docs.values())

    @staticmethod
    @serialized
    def create(benh_nhan_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do_kham, audit_user=None):
        """Tạo lịch hẹn khám mới kèm kiểm tra ca trực và gửi thông báo in-app."""
        # Kiểm tra ngày giờ hợp lệ (chuẩn hóa đa định dạng và không cho đặt trong quá khứ)
        work_date_str = AppointmentModel.normalize_date(ngay_hen)
        work_time_str = AppointmentModel.normalize_time(gio_hen)
        try:
            appt_dt = datetime.strptime(f"{work_date_str} {work_time_str}", '%Y-%m-%d %H:%M')
            if appt_dt < datetime.now():
                return False, "Không thể đặt lịch hẹn vào thời gian trong quá khứ!"
        except Exception:
            return False, "Định dạng ngày hẹn hoặc giờ hẹn không hợp lệ (YYYY-MM-DD HH:MM)!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            schedule_row = booking_target(cursor, benh_nhan_id, chuyen_khoa_id,
                                          bac_si_id, work_date_str, work_time_str)
            bac_si_id = schedule_row['bac_si_id']
            phong_kham_id = schedule_row['phong_kham_id']
            cursor.execute('SELECT ten_khoa FROM chuyen_khoa WHERE id = ?', (chuyen_khoa_id,))
            ck = cursor.fetchone()

            # 4. Tạo mã lịch hẹn
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM lich_hen')
            next_id = cursor.fetchone()['next_id']
            ma_lich_hen = f"LH2609{str(next_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ma_lich_hen, benh_nhan_id, bac_si_id if bac_si_id else None, chuyen_khoa_id, phong_kham_id, work_date_str, work_time_str, ly_do_kham, 'Chờ tiếp nhận'))
            created_appt_id = cursor.lastrowid
            sync_count(cursor, schedule_row)

            # 5. Tạo thông báo In-App cho bệnh nhân và Lễ tân/Admin
            cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (benh_nhan_id,))
            bn_row = cursor.fetchone()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if bn_row and bn_row.get('tai_khoan_id'):
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, 'Đặt lịch hẹn', '/patient/dashboard', 0, ?)
                ''', (
                    bn_row['tai_khoan_id'],
                    f"Đăng ký khám thành công: {ma_lich_hen}",
                    f"Quý khách đã đặt lịch khám tại {ck['ten_khoa']} ({work_date_str} lúc {gio_hen}). Trạng thái: Chờ tiếp nhận.",
                    now_str
                ))

            # Thông báo cho Tiếp tân và Admin có lịch khám mới cần tiếp nhận
            patient_name = bn_row['ho_ten'] if bn_row else 'Bệnh nhân'
            cursor.execute('''
                SELECT t.id FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                WHERE v.ma_vai_tro IN ('ADMIN', 'LETAN') AND t.trang_thai = 1
            ''')
            admin_letan_accs = cursor.fetchall()
            for adm in admin_letan_accs:
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, 'Lịch khám mới', '/admin/reception', 0, ?)
                ''', (
                    adm['id'],
                    f"Lịch hẹn khám mới: {ma_lich_hen}",
                    f"Bệnh nhân {patient_name} vừa đặt lịch khám tại {ck['ten_khoa']} ({work_date_str} lúc {gio_hen}). Vui lòng kiểm tra và tiếp nhận.",
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
    @serialized
    def reschedule(appointment_id, new_date, new_time, ly_do=None, new_doctor_id=None, user_info=None):
        """Đổi ngày giờ lịch hẹn theo ràng buộc thời gian và quyền hạn."""
        appt = AppointmentModel.get_by_id(appointment_id)
        if not appt:
            return False, "Không tìm thấy thông tin lịch hẹn!"

        if appt.get('trang_thai') in ['Đã khám', 'Hoàn thành', 'Đã hủy']:
            return False, f"Không thể đổi lịch hẹn đã ở trạng thái '{appt.get('trang_thai')}'!"

        # Kiểm tra trạng thái hiện tại
        if appt['trang_thai'] in ['Đã hủy', 'Hoàn thành']:
            return False, f"Không thể đổi lịch hẹn đang ở trạng thái '{appt['trang_thai']}'!"

        # Quyền hạn và thời gian:
        is_staff = user_info and user_info.get('vai_tro') in ['ADMIN', 'LETAN', 'BACSI']
        user_role = user_info.get('vai_tro') if user_info else 'BENHNHAN'

        if user_role == 'BENHNHAN':
            # Bệnh nhân chỉ được thao tác trên lịch hẹn của chính mình
            patient_id = (user_info or {}).get('patient_id')
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
            new_time_str = clock(new_time).strftime('%H:%M')
            new_dt = datetime.strptime(f"{new_date_str} {new_time_str}", '%Y-%m-%d %H:%M')
            if new_dt <= datetime.now():
                return False, "Thời gian hẹn mới phải ở tương lai!"
        except Exception:
            return False, "Định dạng ngày hẹn hoặc giờ hẹn mới không hợp lệ (YYYY-MM-DD HH:MM)!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            doc_id = new_doctor_id or appt.get('bac_si_id')
            new_sch = booking_target(cursor, appt['benh_nhan_id'], appt['chuyen_khoa_id'],
                                     doc_id, new_date_str, new_time_str, exclude=appt['id'])
            doc_id = new_sch['bac_si_id']
            old_sch = (schedule_for(cursor, appt['bac_si_id'], str(appt['ngay_hen'])[:10],
                                    appt['gio_hen'], approved=False)
                       if appt.get('bac_si_id') else None)

            new_ly_do = ly_do if ly_do else appt.get('ly_do_kham')
            cursor.execute('''
                UPDATE lich_hen
                SET ngay_hen = ?, gio_hen = ?, bac_si_id = ?, phong_kham_id = ?, ly_do_kham = ?
                WHERE id = ?
            ''', (new_date_str, new_time_str, doc_id, new_sch['phong_kham_id'], new_ly_do, appt['id']))

            sync_count(cursor, new_sch)
            if old_sch and old_sch['id'] != new_sch['id']:
                sync_count(cursor, old_sch)
            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appt['id'],
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
    @serialized
    def cancel(appointment_id, reason=None, user_info=None):
        """Hủy lịch hẹn khám: cập nhật trạng thái 'Đã hủy', giải phóng chỗ ca trực, ghi audit log."""
        appt = AppointmentModel.get_by_id(appointment_id)
        if not appt:
            return False, "Không tìm thấy thông tin lịch hẹn!"

        if appt['trang_thai'] == 'Đã hủy':
            return False, "Lịch hẹn này đã được hủy trước đó!"

        if appt['trang_thai'] in ('Hoàn thành','Đã khám'):
            return False, "Không thể hủy lịch hẹn đã hoàn thành khám bệnh!"

        user_role = user_info.get('vai_tro') if user_info else 'BENHNHAN'

        # Nếu là bệnh nhân, kiểm tra quyền sở hữu và thời gian trước giờ khám
        if user_role == 'BENHNHAN':
            patient_id = (user_info or {}).get('patient_id')
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
            cursor.execute("UPDATE lich_hen SET trang_thai = ? WHERE id = ?", ('Đã hủy', appt['id']))

            if appt.get('bac_si_id'):
                old_sch = schedule_for(cursor, appt['bac_si_id'], str(appt['ngay_hen'])[:10],
                                       appt['gio_hen'], approved=False)
                sync_count(cursor, old_sch)

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

            # 4. Tự động hủy hóa đơn tạm chưa thanh toán liên quan
            cursor.execute('''
                UPDATE hoa_don
                SET trang_thai = N'Đã hủy'
                WHERE benh_nhan_id = ?
                  AND trang_thai = N'Chưa thanh toán'
                  AND (
                      phieu_kham_id IN (SELECT id FROM phieu_kham WHERE lich_hen_id = ?)
                      OR id IN (SELECT hoa_don_id FROM chi_tiet_hoa_don WHERE loai_khoan_thu = N'Khám bệnh' AND tham_chieu_id = ?)
                  )
            ''', (appt['benh_nhan_id'], appt['id'], appt['id']))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appt['id'],
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
    @serialized
    def update_status(appointment_id, new_status, user_info=None):
        """Cập nhật trạng thái lịch hẹn khám và ghi audit trail."""
        appt = AppointmentModel.get_by_id(appointment_id)
        if not appt:
            return False, "Không tìm thấy lịch hẹn!"

        if new_status == 'Đã hủy':
            return AppointmentModel.cancel(appointment_id, user_info=user_info)
        if appt['trang_thai'] == 'Đã hủy':
            return False, 'Không thể khôi phục lịch đã hủy; vui lòng đặt lịch mới.'

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE lich_hen SET trang_thai = ? WHERE id = ?', (new_status, appt['id']))

            # Nếu tiếp nhận hoặc xác nhận lịch hẹn, tự động gửi thông báo in-app cho bệnh nhân và bác sĩ
            if new_status in ['Đã tiếp nhận', 'Đã xác nhận']:
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (appt['benh_nhan_id'],))
                bn_row = cursor.fetchone()
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                khoa_name = appt.get('ten_khoa') or 'Chuyên khoa'
                bs_name = appt.get('ten_bac_si') or 'Bác sĩ phụ trách'

                if bn_row and bn_row.get('tai_khoan_id'):
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

                # Thông báo cho bác sĩ ngay khi tiếp tân/admin duyệt tiếp nhận
                doctor_id = appt.get('bac_si_id')
                if doctor_id:
                    cursor.execute('''
                        SELECT nv.tai_khoan_id FROM bac_si bs
                        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                        WHERE bs.id = ?
                    ''', (doctor_id,))
                    doc_acc = cursor.fetchone()
                    if doc_acc and doc_acc.get('tai_khoan_id'):
                        patient_name = bn_row['ho_ten'] if bn_row else 'Bệnh nhân'
                        cursor.execute('''
                            INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                            VALUES (?, ?, ?, N'Lịch khám', '/admin/appointments', 0, ?)
                        ''', (
                            doc_acc['tai_khoan_id'],
                            f"Lịch khám mới tiếp nhận: {appt['ma_lich_hen']}",
                            f"Bệnh nhân {patient_name} đã được Lễ tân tiếp nhận lịch khám với bạn vào ngày {appt['ngay_hen']} lúc {str(appt['gio_hen'])[:5]}.",
                            now_str
                        ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='lich_hen',
                row_id=appt['id'],
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

