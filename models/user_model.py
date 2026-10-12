from datetime import datetime
from core.database import get_db
from core.security import hash_password, verify_password

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
                SELECT nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.email, bs.id AS bac_si_id, bs.hoc_vi
                FROM nhan_vien nv
                LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
                WHERE nv.tai_khoan_id = ?
            ''', (user_row['id'],))
            staff_row = cursor.fetchone()
            if staff_row:
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
            return True, 'Đăng ký tài khoản thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi hệ thống khi đăng ký: {str(e)}'

    @staticmethod
    def reset_patient_password(patient_id, new_password):
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
            if patient.get('tai_khoan_id'):
                cursor.execute('UPDATE tai_khoan SET password = ? WHERE id = ?', (hashed, patient['tai_khoan_id']))
            else:
                sdt = patient['sdt']
                cursor.execute('''
                    INSERT INTO tai_khoan (vai_tro_id, username, password, sdt, trang_thai)
                    VALUES (6, ?, ?, ?, 1)
                ''', (sdt, hashed, sdt))
                new_tk_id = cursor.lastrowid
                cursor.execute('UPDATE benh_nhan SET tai_khoan_id = ?, co_tai_khoan = 1 WHERE id = ?', (new_tk_id, patient_id))

            conn.commit()
            conn.close()
            return True, f'Đã cập nhật mật khẩu mới cho bệnh nhân {patient["ho_ten"]}!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi đặt lại mật khẩu: {str(e)}'

    @staticmethod
    def get_all_doctors():
        """Lấy danh sách bác sĩ chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bs.id, bs.hoc_vi, bs.kinh_nghiem, bs.avatar, bs.gia_kham, bs.trang_thai_lam_viec,
                   nv.ho_ten, nv.sdt, nv.email,
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
