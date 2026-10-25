Pfrom datetime import datetime
from core.database import get_db
from core.security import hash_password, verify_password
from core.audit import AuditLogger

class UserModel:
    """Model quản lý tài khoản người dùng, phân quyền và nhân sự."""

    @staticmethod
    def authenticate(username, password):
        """Xác thực đăng nhập tài khoản theo tên đăng nhập hoặc số điện thoại."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.*, v.ma_vai_tro, v.ten_vai_tro
            FROM tai_khoan t
            JOIN vai_tro v ON t.vai_tro_id = v.id
            WHERE t.username = ? OR t.sdt = ?
        ''', (username, username))
        user_row = cursor.fetchone()

        if not user_row or not verify_password(user_row['password'], password):
            conn.close()
            return None

        # Kiểm tra tài khoản có bị vô hiệu hóa không
        if user_row.get('trang_thai') == 0 or user_row.get('trang_thai') is False:
            conn.close()
            return None

        # Cập nhật thời gian đăng nhập cuối
        cursor.execute('''
            UPDATE tai_khoan SET lan_dang_nhap_cuoi = ? WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_row['id']))
        conn.commit()

        user_info = {
            'id': user_row['id'],
            'username': user_row['username'],
            'vai_tro': user_row['ma_vai_tro'],
            'ten_vai_tro': user_row['ten_vai_tro'],
            'sdt': user_row['sdt']
        }

        # Nếu là Bác sĩ hoặc Nhân viên nội bộ
        if user_row['ma_vai_tro'] in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
            cursor.execute('''
                SELECT nv.id AS staff_id, nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.email, nv.trang_thai AS staff_status,
                       bs.id AS bac_si_id, bs.hoc_vi
                FROM nhan_vien nv
                LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
                WHERE nv.tai_khoan_id = ?
            ''', (user_row['id'],))
            staff_row = cursor.fetchone()
            if staff_row:
                # Nếu nhân viên bị vô hiệu hóa
                if staff_row.get('staff_status') == 0 or staff_row.get('staff_status') is False:
                    conn.close()
                    return None
                user_info['staff_id'] = staff_row.get('staff_id')
                user_info['ho_ten'] = staff_row['ho_ten']
                user_info['chuc_vu'] = staff_row['chuc_vu']
                user_info['ma_nhan_vien'] = staff_row.get('ma_nhan_vien')
                user_info['email'] = staff_row.get('email') or user_row.get('email')
                user_info['bac_si_id'] = staff_row.get('bac_si_id')
                user_info['hoc_vi'] = staff_row.get('hoc_vi')
            else:
                user_info['ho_ten'] = user_row['username']

        # Nếu là Bệnh nhân
        elif user_row['ma_vai_tro'] == 'BENHNHAN':
            cursor.execute('''
                SELECT id, ma_benh_nhan, ho_ten, sdt, email, cccd, bhyt, nhom_mau
                FROM benh_nhan WHERE tai_khoan_id = ?
            ''', (user_row['id'],))
            patient_row = cursor.fetchone()
            if patient_row:
                user_info['ho_ten'] = patient_row['ho_ten']
                user_info['patient_id'] = patient_row['id']
                user_info['ma_benh_nhan'] = patient_row['ma_benh_nhan']
            else:
                user_info['ho_ten'] = user_row['username']

        conn.close()
        return user_info

    @staticmethod
    def check_account_active(account_id):
        """Kiểm tra tài khoản còn đang hoạt động hay đã bị vô hiệu hóa."""
        if not account_id:
            return True
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT trang_thai FROM tai_khoan WHERE id = ?', (account_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return True
        return bool(row['trang_thai'])

    @staticmethod
    def get_mobile_identity(account_id):
        """Resolve the current active account role and linked patient for Mobile auth."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.id AS account_id, t.username, t.email, t.sdt,
                   t.trang_thai AS account_status, v.ma_vai_tro AS vai_tro,
                   bn.id AS patient_id, bn.ma_benh_nhan, bn.ho_ten
            FROM tai_khoan t
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN benh_nhan bn ON bn.tai_khoan_id = t.id
            WHERE t.id = ?
        ''', (account_id,))
        row = cursor.fetchone()
        conn.close()
        if not row or not bool(row.get('account_status')):
            return None
        return dict(row)


    @staticmethod
    def register_patient(ho_ten, sdt, ngay_sinh, gioi_tinh, cccd, email, bhyt, password):
        """Đăng ký tài khoản và tạo hồ sơ bệnh nhân mới."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id FROM tai_khoan WHERE username = ? OR sdt = ?', (sdt, sdt))
            if cursor.fetchone():
                conn.close()
                return False, 'Số điện thoại này đã được đăng ký tài khoản!'

            hashed_pwd = hash_password(password)
            cursor.execute('''
                INSERT INTO tai_khoan (vai_tro_id, username, password, email, sdt, trang_thai)
                VALUES (6, ?, ?, ?, ?, 1)
            ''', (sdt, hashed_pwd, email, sdt))
            tai_khoan_id = cursor.lastrowid

            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM benh_nhan')
            next_id = cursor.fetchone()['next_id']
            ma_benh_nhan = f"BN2609{str(next_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO benh_nhan (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, co_tai_khoan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt))
            benh_nhan_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO chi_so_sinh_ton (benh_nhan_id) VALUES (?)
            ''', (benh_nhan_id,))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='tai_khoan',
                row_id=tai_khoan_id,
                action='REGISTER_PATIENT',
                performed_by=tai_khoan_id,
                performed_by_name=ho_ten,
                reason='Bệnh nhân đăng ký tài khoản trực tuyến'
            )

            return True, 'Đăng ký tài khoản thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi hệ thống khi đăng ký: {str(e)}'

    @staticmethod
    def reset_patient_password(patient_id, new_password, audit_user=None):
        """Đặt lại mật khẩu cho tài khoản liên kết với bệnh nhân."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT tai_khoan_id, ho_ten, sdt FROM benh_nhan WHERE id = ?', (patient_id,))
            patient = cursor.fetchone()
            if not patient:
                conn.close()
                return False, 'Không tìm thấy hồ sơ bệnh nhân!'

            hashed = hash_password(new_password)
            tk_id = patient.get('tai_khoan_id')
            if tk_id:
                cursor.execute('UPDATE tai_khoan SET password = ? WHERE id = ?', (hashed, tk_id))
            else:
                sdt = patient['sdt']
                cursor.execute('''
                    INSERT INTO tai_khoan (vai_tro_id, username, password, sdt, trang_thai)
                    VALUES (6, ?, ?, ?, 1)
                ''', (sdt, hashed, sdt))
                tk_id = cursor.lastrowid
                cursor.execute('UPDATE benh_nhan SET tai_khoan_id = ?, co_tai_khoan = 1 WHERE id = ?', (tk_id, patient_id))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='tai_khoan',
                row_id=tk_id,
                action='RESET_PASSWORD',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Hệ thống',
                reason=f'Đặt lại mật khẩu bệnh nhân {patient["ho_ten"]}'
            )

            return True, f'Đã cập nhật mật khẩu mới cho bệnh nhân {patient["ho_ten"]}!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi đặt lại mật khẩu: {str(e)}'

    @staticmethod
    def get_all_roles():
        """Lấy danh sách tất cả các vai trò hiện có trong CSDL."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, ma_vai_tro, ten_vai_tro, mo_ta FROM vai_tro ORDER BY id ASC')
        roles = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return roles

    @staticmethod
    def get_all_doctors():
        """Lấy danh sách bác sĩ chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bs.id, bs.hoc_vi, bs.kinh_nghiem, bs.avatar, bs.gia_kham, bs.trang_thai_lam_viec,
                   nv.id AS nhan_vien_id, nv.ho_ten, nv.sdt, nv.email,
                   ck.id AS chuyen_khoa_id, ck.ten_khoa,
                   pk.id AS phong_kham_id, pk.ten_phong
            FROM bac_si bs
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON bs.phong_kham_chinh_id = pk.id
            ORDER BY bs.id ASC
        ''')
        doctors = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return doctors

    @staticmethod
    def get_all_staff(user_info=None):
        """Lấy danh sách nhân viên y tế theo phân quyền vai trò."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nv.*, t.username, t.vai_tro_id, t.trang_thai AS account_active, v.ma_vai_tro, v.ten_vai_tro,
                   bs.id AS bac_si_id, bs.chuyen_khoa_id, bs.phong_kham_chinh_id, bs.hoc_vi,
                   ck.ten_khoa, pk.ten_phong
            FROM nhan_vien nv
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON bs.phong_kham_chinh_id = pk.id
            ORDER BY nv.id DESC
        ''')
        staff_list = [dict(r) for r in cursor.fetchall()]
        conn.close()

        if not user_info:
            return staff_list

        role = user_info.get('vai_tro')
        if role == 'ADMIN':
            return staff_list
        elif role == 'BACSI':
            dept_id = user_info.get('chuyen_khoa_id')
            if not dept_id and user_info.get('bac_si_id'):
                doc = UserModel.get_doctor_by_id(user_info.get('bac_si_id'))
                if doc:
                    dept_id = doc.get('chuyen_khoa_id')
            if dept_id:
                res = [s for s in staff_list if s.get('ma_vai_tro') == 'ADMIN' or (s.get('ma_vai_tro') == 'BACSI' and s.get('chuyen_khoa_id') == dept_id)]
            else:
                res = [s for s in staff_list if s.get('ma_vai_tro') == 'ADMIN' or s.get('ma_vai_tro') == 'BACSI']
            return sorted(res, key=lambda s: (0 if s.get('ma_vai_tro') == 'ADMIN' else 1))
        elif role in ['LETAN', 'DUOCSI', 'KTV']:
            res = [s for s in staff_list if s.get('ma_vai_tro') == 'ADMIN' or s.get('ma_vai_tro') == role]
            return sorted(res, key=lambda s: (0 if s.get('ma_vai_tro') == 'ADMIN' else 1))

        res = [s for s in staff_list if s.get('ma_vai_tro') == 'ADMIN' or s.get('ma_vai_tro') == role]
        return sorted(res, key=lambda s: (0 if s.get('ma_vai_tro') == 'ADMIN' else 1))

    @staticmethod
    def get_staff_by_id(staff_id):
        """Lấy thông tin chi tiết một nhân viên y tế theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nv.*, t.username, t.vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                   bs.id AS bac_si_id, bs.chuyen_khoa_id, bs.phong_kham_chinh_id, bs.hoc_vi,
                   ck.ten_khoa, pk.ten_phong
            FROM nhan_vien nv
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON bs.phong_kham_chinh_id = pk.id
            WHERE nv.id = ?
        ''', (staff_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create_staff(data, audit_user=None):
        """Thêm mới nhân viên y tế, tạo tài khoản và gán vai trò."""
        ho_ten = data.get('ho_ten', '').strip()
        sdt = data.get('sdt', '').strip()
        chuc_vu = data.get('chuc_vu', '').strip()
        vai_tro_id = data.get('vai_tro_id', 2)
        email = data.get('email', '').strip() or None
        username = data.get('username', '').strip() or sdt
        password = data.get('password', 'Staff@123')
        cccd = data.get('cccd', '').strip() or None
        gioi_tinh = int(data.get('gioi_tinh', 1))
        ngay_sinh = data.get('ngay_sinh')
        dia_chi = data.get('dia_chi', '').strip()
        chuyen_khoa_id = data.get('chuyen_khoa_id')
        phong_kham_id = data.get('phong_kham_id')
        hoc_vi = data.get('hoc_vi', 'Bác sĩ')

        if not ho_ten or not sdt or not chuc_vu:
            return False, 'Họ tên, số điện thoại và chức vụ là bắt buộc!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Kiểm tra trùng username hoặc sdt trong tai_khoan
            cursor.execute('SELECT id FROM tai_khoan WHERE username = ? OR sdt = ?', (username, sdt))
            if cursor.fetchone():
                conn.close()
                return False, 'Tên đăng nhập hoặc số điện thoại đã tồn tại trong hệ thống!'

            # Tạo tài khoản
            hashed_pwd = hash_password(password)
            cursor.execute('''
                INSERT INTO tai_khoan (vai_tro_id, username, password, email, sdt, trang_thai)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (vai_tro_id, username, hashed_pwd, email, sdt))
            tk_id = cursor.lastrowid

            # Sinh mã nhân viên
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM nhan_vien')
            nv_next = cursor.fetchone()['next_id']
            ma_nv = f"NV{str(nv_next).zfill(4)}"

            cursor.execute('''
                INSERT INTO nhan_vien (tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (tk_id, ma_nv, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu))
            nv_id = cursor.lastrowid

            # Kiểm tra vai trò nếu là bác sĩ (vai_tro_id = 3 hoặc ma_vai_tro = 'BACSI')
            cursor.execute('SELECT ma_vai_tro FROM vai_tro WHERE id = ?', (vai_tro_id,))
            v_row = cursor.fetchone()
            if v_row and v_row['ma_vai_tro'] == 'BACSI':
                ck_id = chuyen_khoa_id or 1
                cursor.execute('''
                    INSERT INTO bac_si (nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, trang_thai_lam_viec)
                    VALUES (?, ?, ?, ?, 'Đang làm việc')
                ''', (nv_id, ck_id, phong_kham_id, hoc_vi))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='nhan_vien',
                row_id=nv_id,
                action='CREATE_STAFF',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason=f'Tạo hồ sơ nhân viên mới: {ho_ten} ({chuc_vu})',
                after_data={'ma_nv': ma_nv, 'ho_ten': ho_ten, 'chuc_vu': chuc_vu, 'vai_tro_id': vai_tro_id}
            )

            return True, nv_id

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi tạo nhân sự: {str(e)}'

    @staticmethod
    def update_staff(staff_id, data, audit_user=None):
        """Cập nhật thông tin nhân sự y tế."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM nhan_vien WHERE id = ?', (staff_id,))
            old_nv = cursor.fetchone()
            if not old_nv:
                conn.close()
                return False, 'Không tìm thấy hồ sơ nhân viên!'

            ho_ten = data.get('ho_ten', old_nv['ho_ten']).strip()
            sdt = data.get('sdt', old_nv['sdt']).strip()
            chuc_vu = data.get('chuc_vu', old_nv['chuc_vu']).strip()
            email = data.get('email', old_nv.get('email', '')).strip()
            dia_chi = data.get('dia_chi', old_nv.get('dia_chi', '')).strip()
            cccd = data.get('cccd', old_nv.get('cccd', '')).strip()
            vai_tro_id = data.get('vai_tro_id')

            cursor.execute('''
                UPDATE nhan_vien
                SET ho_ten = ?, sdt = ?, chuc_vu = ?, email = ?, dia_chi = ?, cccd = ?
                WHERE id = ?
            ''', (ho_ten, sdt, chuc_vu, email, dia_chi, cccd, staff_id))

            # Cập nhật thông tin tài khoản liên kết nếu có thay đổi vai trò hoặc email/sdt
            if vai_tro_id:
                cursor.execute('''
                    UPDATE tai_khoan SET vai_tro_id = ?, email = ?, sdt = ? WHERE id = ?
                ''', (vai_tro_id, email, sdt, old_nv['tai_khoan_id']))
            else:
                cursor.execute('''
                    UPDATE tai_khoan SET email = ?, sdt = ? WHERE id = ?
                ''', (email, sdt, old_nv['tai_khoan_id']))

            # Cập nhật thông tin bác sĩ nếu là bác sĩ
            if 'chuyen_khoa_id' in data or 'phong_kham_id' in data or 'hoc_vi' in data:
                cursor.execute('SELECT id FROM bac_si WHERE nhan_vien_id = ?', (staff_id,))
                bs = cursor.fetchone()
                if bs:
                    ck_id = data.get('chuyen_khoa_id') or 1
                    pk_id = data.get('phong_kham_id')
                    hoc_vi = data.get('hoc_vi', 'Bác sĩ')
                    cursor.execute('''
                        UPDATE bac_si SET chuyen_khoa_id = ?, phong_kham_chinh_id = ?, hoc_vi = ? WHERE id = ?
                    ''', (ck_id, pk_id, hoc_vi, bs['id']))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='nhan_vien',
                row_id=staff_id,
                action='UPDATE_STAFF',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason='Cập nhật thông tin nhân sự',
                before_data=dict(old_nv),
                after_data={'ho_ten': ho_ten, 'sdt': sdt, 'chuc_vu': chuc_vu, 'email': email}
            )

            return True, 'Cập nhật thông tin nhân sự thành công!'

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi cập nhật nhân sự: {str(e)}'

    @staticmethod
    def toggle_staff_status(staff_id, audit_user=None):
        """Bật/tắt trạng thái làm việc của nhân viên và tài khoản liên kết."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id, tai_khoan_id, ho_ten, trang_thai FROM nhan_vien WHERE id = ?', (staff_id,))
            nv = cursor.fetchone()
            if not nv:
                conn.close()
                return False, 'Không tìm thấy hồ sơ nhân viên!'

            current_st = int(nv['trang_thai'] or 0)
            new_st = 0 if current_st == 1 else 1

            cursor.execute('UPDATE nhan_vien SET trang_thai = ? WHERE id = ?', (new_st, staff_id))
            if nv.get('tai_khoan_id'):
                cursor.execute('UPDATE tai_khoan SET trang_thai = ? WHERE id = ?', (new_st, nv['tai_khoan_id']))

            # Cập nhật trạng thái làm việc bác sĩ nếu có
            work_st = 'Đang làm việc' if new_st == 1 else 'Tạm nghỉ'
            cursor.execute('UPDATE bac_si SET trang_thai_lam_viec = ? WHERE nhan_vien_id = ?', (work_st, staff_id))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='nhan_vien',
                row_id=staff_id,
                action='TOGGLE_STAFF_STATUS',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason=f"Đổi trạng thái nhân sự {nv['ho_ten']} thành {'Hoạt động' if new_st == 1 else 'Khóa'}"
            )

            return True, new_st

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def delete_staff(staff_id, audit_user=None):
        """Xóa nhân viên y tế (kiểm tra an toàn dữ liệu tham chiếu)."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id, tai_khoan_id, ho_ten FROM nhan_vien WHERE id = ?', (staff_id,))
            nv = cursor.fetchone()
            if not nv:
                conn.close()
                return False, 'Không tìm thấy hồ sơ nhân viên!'

            # Kiểm tra xem có lịch khám EMR nào của bác sĩ này không
            cursor.execute('''
                SELECT COUNT(*) AS cnt FROM phieu_kham pk
                JOIN bac_si bs ON pk.bac_si_id = bs.id
                WHERE bs.nhan_vien_id = ?
            ''', (staff_id,))
            pk_cnt = cursor.fetchone()['cnt']
            if pk_cnt > 0:
                conn.close()
                return False, f"Không thể xóa vì nhân sự đã phát sinh {pk_cnt} hồ sơ khám bệnh! Vui lòng chuyển trạng thái sang Vô hiệu hóa."

            # Xóa liên kết bác sĩ
            cursor.execute('DELETE FROM bac_si WHERE nhan_vien_id = ?', (staff_id,))
            # Xóa nhân viên
            cursor.execute('DELETE FROM nhan_vien WHERE id = ?', (staff_id,))
            # Xóa tài khoản
            if nv.get('tai_khoan_id'):
                cursor.execute('DELETE FROM tai_khoan WHERE id = ?', (nv['tai_khoan_id'],))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='nhan_vien',
                row_id=staff_id,
                action='DELETE_STAFF',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason=f"Xóa hồ sơ nhân sự {nv['ho_ten']}"
            )

            return True, 'Đã xóa nhân viên y tế thành công!'

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi xóa nhân sự: {str(e)}'

    @staticmethod
    def get_accounts(role=None, status=None, search=None, page=1, per_page=20, allowed_roles=None, doctor_dept_id=None):
        """Xem danh sách tài khoản bệnh nhân và nhân viên, tìm kiếm và phân trang."""
        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT t.id, t.username, t.email, t.sdt, t.trang_thai, t.ngay_tao, t.lan_dang_nhap_cuoi,
                   v.id AS vai_tro_id, v.ma_vai_tro, v.ten_vai_tro,
                   COALESCE(nv.ho_ten, bn.ho_ten, t.username) AS ho_ten,
                   COALESCE(nv.ma_nhan_vien, bn.ma_benh_nhan, '---') AS ma_dinh_danh,
                   bn.id AS patient_id,
                   CASE 
                       WHEN nv.id IS NOT NULL THEN 'NHAN_VIEN'
                       WHEN bn.id IS NOT NULL THEN 'BENH_NHAN'
                       ELSE 'HE_THONG'
                   END AS loai_doi_tuong
            FROM tai_khoan t
            JOIN vai_tro v ON t.vai_tro_id = v.id
            LEFT JOIN nhan_vien nv ON nv.tai_khoan_id = t.id
            LEFT JOIN benh_nhan bn ON bn.tai_khoan_id = t.id
            WHERE 1=1
        '''
        params = []

        if allowed_roles:
            placeholders = ', '.join(['?'] * len(allowed_roles))
            sql += f' AND v.ma_vai_tro IN ({placeholders})'
            params.extend(allowed_roles)

        if role and role != 'ALL':
            sql += ' AND v.ma_vai_tro = ?'
            params.append(role)

        if doctor_dept_id and (role == 'BENHNHAN' or (allowed_roles and 'BENHNHAN' in allowed_roles)):
            sql += ''' AND (v.ma_vai_tro != 'BENHNHAN' OR bn.id IN (
                SELECT benh_nhan_id FROM lich_hen WHERE chuyen_khoa_id = ?
                UNION
                SELECT pk.benh_nhan_id FROM phieu_kham pk 
                JOIN phong_kham ph ON pk.phong_kham_id = ph.id 
                WHERE ph.chuyen_khoa_id = ?
                UNION
                SELECT pk.benh_nhan_id FROM phieu_kham pk
                JOIN bac_si bs ON pk.bac_si_id = bs.id
                WHERE bs.chuyen_khoa_id = ?
            ))'''
            params.extend([doctor_dept_id, doctor_dept_id, doctor_dept_id])

        if status is not None and str(status).upper() != 'ALL':
            sql += ' AND t.trang_thai = ?'
            params.append(int(status))

        if search:
            s = f"%{search.strip()}%"
            sql += ' AND (t.username LIKE ? OR t.sdt LIKE ? OR t.email LIKE ? OR nv.ho_ten LIKE ? OR bn.ho_ten LIKE ?)'
            params.extend([s, s, s, s, s])

        sql += ' ORDER BY t.id DESC'

        cursor.execute(sql, tuple(params))
        all_rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        total = len(all_rows)
        page = max(1, int(page))
        per_page = max(1, int(per_page))
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        items = all_rows[start_idx:end_idx]

        return {
            'accounts': items,
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    @staticmethod
    def get_account_detail(account_id):
        """Xem chi tiết một tài khoản và hồ sơ liên kết (bệnh nhân hoặc nhân viên)."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.id, t.username, t.email, t.sdt, t.trang_thai, t.ngay_tao, t.lan_dang_nhap_cuoi,
                   v.id AS vai_tro_id, v.ma_vai_tro, v.ten_vai_tro
            FROM tai_khoan t
            JOIN vai_tro v ON t.vai_tro_id = v.id
            WHERE t.id = ?
        ''', (account_id,))
        acc = cursor.fetchone()
        if not acc:
            conn.close()
            return None

        result = dict(acc)
        # Kiểm tra nhân viên liên kết
        cursor.execute('''
            SELECT nv.*, bs.id AS bac_si_id, bs.hoc_vi, ck.ten_khoa, pk.ten_phong
            FROM nhan_vien nv
            LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON bs.phong_kham_chinh_id = pk.id
            WHERE nv.tai_khoan_id = ?
        ''', (account_id,))
        nv = cursor.fetchone()
        if nv:
            result['nhan_vien'] = dict(nv)
        else:
            result['nhan_vien'] = None

        # Kiểm tra bệnh nhân liên kết
        cursor.execute('SELECT * FROM benh_nhan WHERE tai_khoan_id = ?', (account_id,))
        bn = cursor.fetchone()
        if bn:
            result['benh_nhan'] = dict(bn)
        else:
            result['benh_nhan'] = None

        conn.close()
        return result

    @staticmethod
    def toggle_account_status(account_id, audit_user=None):
        """Bật/tắt kích hoạt tài khoản và đồng bộ trạng thái thực thể liên kết."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT t.id, t.username, t.trang_thai, t.vai_tro_id, v.ma_vai_tro 
                FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                WHERE t.id = ?
            ''', (account_id,))
            acc = cursor.fetchone()
            if not acc:
                conn.close()
                return False, 'Không tìm thấy tài khoản!'

            if acc.get('ma_vai_tro') == 'ADMIN' or acc.get('vai_tro_id') == 1 or acc.get('username') == 'admin':
                conn.close()
                return False, 'Không thể vô hiệu hóa tài khoản Quản trị viên hệ thống!'

            curr = int(acc['trang_thai'] or 0)
            new_st = 0 if curr == 1 else 1

            cursor.execute('UPDATE tai_khoan SET trang_thai = ? WHERE id = ?', (new_st, account_id))
            # Đồng bộ sang nhan_vien nếu có
            cursor.execute('UPDATE nhan_vien SET trang_thai = ? WHERE tai_khoan_id = ?', (new_st, account_id))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='tai_khoan',
                row_id=account_id,
                action='TOGGLE_ACCOUNT_STATUS',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason=f"Đổi trạng thái tài khoản {acc['username']} sang {'Hoạt động' if new_st == 1 else 'Vô hiệu hóa'}"
            )

            return True, new_st
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def reset_account_password(account_id, new_password, audit_user=None):
        """Quản trị viên đặt lại mật khẩu cho bất kỳ tài khoản nào (không hiển thị mật khẩu hiện tại)."""
        if not new_password or len(new_password) < 6:
            return False, 'Mật khẩu mới phải có tối thiểu 6 ký tự!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT t.id, t.username, t.vai_tro_id, v.ma_vai_tro 
                FROM tai_khoan t 
                LEFT JOIN vai_tro v ON t.vai_tro_id = v.id 
                WHERE t.id = ?
            ''', (account_id,))
            acc = cursor.fetchone()
            if not acc:
                conn.close()
                return False, 'Không tìm thấy tài khoản!'

            # Chặn tuyệt đối việc non-admin can thiệp hoặc đổi mật khẩu tài khoản Admin
            if acc.get('ma_vai_tro') == 'ADMIN' or acc.get('vai_tro_id') == 1 or acc.get('username') == 'admin':
                if audit_user and audit_user.get('vai_tro') != 'ADMIN':
                    conn.close()
                    return False, 'Tài khoản Quản trị viên được bảo vệ tuyệt đối, không thể can thiệp!'

            hashed = hash_password(new_password)
            cursor.execute('UPDATE tai_khoan SET password = ? WHERE id = ?', (hashed, account_id))
            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='tai_khoan',
                row_id=account_id,
                action='ADMIN_RESET_PASSWORD',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason=f"Đặt lại mật khẩu cho tài khoản {acc['username']}"
            )

            return True, f"Đặt lại mật khẩu cho tài khoản {acc['username']} thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def set_account_role(account_id, role_id, audit_user=None):
        """Quản trị viên gán vai trò theo danh sách vai trò hiện có trong CSDL."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id, username, vai_tro_id FROM tai_khoan WHERE id = ?', (account_id,))
            acc = cursor.fetchone()
            if not acc:
                conn.close()
                return False, 'Không tìm thấy tài khoản!'

            cursor.execute('SELECT id, ma_vai_tro, ten_vai_tro FROM vai_tro WHERE id = ?', (role_id,))
            role = cursor.fetchone()
            if not role:
                conn.close()
                return False, 'Vai trò chỉ định không tồn tại trong CSDL!'

            old_role_id = acc['vai_tro_id']
            cursor.execute('UPDATE tai_khoan SET vai_tro_id = ? WHERE id = ?', (role_id, account_id))
            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='tai_khoan',
                row_id=account_id,
                action='CHANGE_ROLE',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Quản trị viên',
                reason=f"Đổi vai trò tài khoản {acc['username']} sang {role['ten_vai_tro']} ({role['ma_vai_tro']})",
                before_data={'vai_tro_id': old_role_id},
                after_data={'vai_tro_id': role_id, 'ma_vai_tro': role['ma_vai_tro']}
            )

            return True, f"Đã gán vai trò '{role['ten_vai_tro']}' thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def get_doctor_by_id(doctor_id):
        """Lấy thông tin chi tiết đầy đủ của một bác sĩ phục vụ trang hồ sơ bác sĩ 360 độ."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bs.id, bs.hoc_vi, bs.kinh_nghiem, bs.avatar, bs.gia_kham, bs.trang_thai_lam_viec,
                   nv.id AS nhan_vien_id, nv.ma_nhan_vien, nv.ho_ten, nv.sdt, nv.email, nv.gioi_tinh,
                   nv.ngay_sinh, nv.cccd, nv.dia_chi, nv.chuc_vu, nv.trang_thai,
                   t.id AS tai_khoan_id, t.username, t.ngay_tao, t.lan_dang_nhap_cuoi,
                   ck.id AS chuyen_khoa_id, ck.ten_khoa,
                   pk.id AS phong_kham_id, pk.ten_phong
            FROM bac_si bs
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN tai_khoan t ON nv.tai_khoan_id = t.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON bs.phong_kham_chinh_id = pk.id
            WHERE bs.id = ?
        ''', (doctor_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        doctor = dict(row)

        # Đếm số ca khám
        cursor.execute("SELECT COUNT(*) AS total_visits FROM phieu_kham WHERE bac_si_id = ?", (doctor_id,))
        cnt_row = cursor.fetchone()
        doctor["total_visits"] = cnt_row["total_visits"] if cnt_row else 0

        # Lấy 5 ca khám gần nhất (tương thích đa CSDL)
        cursor.execute('''
            SELECT pk.id, pk.ma_phieu, pk.thoi_gian_kham, pk.chan_doan_icd,
                   bn.id AS benh_nhan_id, bn.ma_benh_nhan, bn.ho_ten AS benh_nhan_ten, bn.gioi_tinh, bn.sdt
            FROM phieu_kham pk
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            WHERE pk.bac_si_id = ?
            ORDER BY pk.thoi_gian_kham DESC
        ''', (doctor_id,))
        recent = cursor.fetchall()
        doctor["recent_patients"] = [dict(r) for r in recent[:5]] if recent else []

        conn.close()
        return doctor

    @staticmethod
    def get_doctor_appointments(doctor_id):
        """Lấy danh sách các lịch hẹn bệnh nhân đăng ký khám với bác sĩ."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT lh.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan,
                   bn.gioi_tinh, bn.ngay_sinh, bn.nhom_mau, bn.di_ung, bn.tien_su_benh,
                   ck.ten_khoa
            FROM lich_hen lh
            JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
            LEFT JOIN chuyen_khoa ck ON lh.chuyen_khoa_id = ck.id
            WHERE lh.bac_si_id = ?
            ORDER BY lh.ngay_hen DESC, lh.gio_hen DESC
        ''', (doctor_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_doctor_visits(doctor_id):
        """Lấy toàn bộ lịch sử các ca khám bệnh do bác sĩ đảm nhiệm."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pk.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan,
                   bn.gioi_tinh, bn.ngay_sinh, bn.nhom_mau, bn.di_ung, bn.tien_su_benh,
                   ph.ten_phong
            FROM phieu_kham pk
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            LEFT JOIN phong_kham ph ON pk.phong_kham_id = ph.id
            WHERE pk.bac_si_id = ?
            ORDER BY pk.thoi_gian_kham DESC
        ''', (doctor_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def update_doctor_avatar(doctor_id, avatar_path):
        """Cập nhật ảnh đại diện bác sĩ."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE bac_si SET avatar = ? WHERE id = ?', (avatar_path, doctor_id))
            conn.commit()
            conn.close()
            return True, 'Cập nhật ảnh đại diện thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def get_account_stats():
        """Thống kê số lượng tài khoản theo vai trò."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM tai_khoan")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS active FROM tai_khoan WHERE trang_thai = 1")
        active = cursor.fetchone()["active"]

        cursor.execute('''
            SELECT v.ma_vai_tro, COUNT(t.id) AS count
            FROM tai_khoan t
            JOIN vai_tro v ON t.vai_tro_id = v.id
            GROUP BY v.ma_vai_tro
        ''')
        role_counts = {r["ma_vai_tro"]: r["count"] for r in cursor.fetchall()}
        conn.close()

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "admin": role_counts.get("ADMIN", 0),
            "doctor": role_counts.get("BACSI", 0),
            "letan": role_counts.get("LETAN", 0),
            "duocsi": role_counts.get("DUOCSI", 0),
            "ktv": role_counts.get("KTV", 0),
            "staff": role_counts.get("LETAN", 0) + role_counts.get("DUOCSI", 0) + role_counts.get("KTV", 0),
            "patient": role_counts.get("BENHNHAN", 0),
        }
