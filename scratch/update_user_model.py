import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'user_model.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Cap nhat authenticate de them da_hoan_thien_ho_so
old_auth_block = """        user_info = {
            'id': user_row['id'],
            'username': user_row['username'],
            'vai_tro': user_row['ma_vai_tro'],
            'ten_vai_tro': user_row['ten_vai_tro'],
            'sdt': user_row['sdt']
        }"""

new_auth_block = """        user_info = {
            'id': user_row['id'],
            'username': user_row['username'],
            'vai_tro': user_row['ma_vai_tro'],
            'ten_vai_tro': user_row['ten_vai_tro'],
            'sdt': user_row['sdt'],
            'da_hoan_thien_ho_so': 1 if user_row.get('da_hoan_thien_ho_so') in (1, True, '1') else 0
        }"""

if old_auth_block in content:
    content = content.replace(old_auth_block, new_auth_block)
    print("Updated authenticate in user_model.py")
else:
    print("old_auth_block not found!")

# 2. Cap nhat register_patient va them complete_patient_profile
old_reg_block = """    @staticmethod
    def register_patient(ho_ten, sdt, ngay_sinh, gioi_tinh, cccd, email, bhyt, password):
        \"\"\"Đăng ký tài khoản và tạo hồ sơ bệnh nhân mới.\"\"\"
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
            return False, f'Lỗi hệ thống khi đăng ký: {str(e)}'"""

new_reg_block = """    @staticmethod
    def register_patient(ho_ten, sdt, password, email=None):
        \"\"\"Đăng ký tài khoản bệnh nhân mới trực tuyến (chưa hoàn thiện thông tin).\"\"\"
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id FROM tai_khoan WHERE username = ? OR sdt = ?', (sdt, sdt))
            if cursor.fetchone():
                conn.close()
                return False, 'Số điện thoại này đã được đăng ký tài khoản!'

            hashed_pwd = hash_password(password)
            cursor.execute('''
                INSERT INTO tai_khoan (vai_tro_id, username, password, email, sdt, trang_thai, da_hoan_thien_ho_so)
                VALUES (6, ?, ?, ?, ?, 1, 0)
            ''', (sdt, hashed_pwd, email, sdt))
            tai_khoan_id = cursor.lastrowid

            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM benh_nhan')
            next_id = cursor.fetchone()['next_id']
            ma_benh_nhan = f"BN2609{str(next_id).zfill(3)}"

            # Tạo hồ sơ sơ bộ, chờ bệnh nhân hoàn thiện sau khi đăng nhập lần đầu
            cursor.execute('''
                INSERT INTO benh_nhan (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, co_tai_khoan)
                VALUES (?, ?, ?, '2000-01-01', N'Nam', ?, ?, 1)
            ''', (tai_khoan_id, ma_benh_nhan, ho_ten, sdt, email))
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
                reason='Bệnh nhân đăng ký tài khoản mới trực tuyến'
            )

            return True, 'Đăng ký tài khoản thành công! Vui lòng đăng nhập để hoàn thiện thông tin cá nhân.'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi hệ thống khi đăng ký: {str(e)}'

    @staticmethod
    def complete_patient_profile(tai_khoan_id, data):
        \"\"\"Cập nhật và hoàn thiện thông tin cá nhân của bệnh nhân sau lần đăng nhập đầu tiên.\"\"\"
        conn = get_db()
        cursor = conn.cursor()

        try:
            ho_ten = data.get('ho_ten', '').strip()
            ngay_sinh = data.get('ngay_sinh', '').strip()
            gioi_tinh = data.get('gioi_tinh', 'Nam').strip()
            cccd = data.get('cccd', '').strip()
            bhyt = data.get('bhyt', '').strip()
            email = data.get('email', '').strip()
            dia_chi = data.get('dia_chi', '').strip()
            nhom_mau = data.get('nhom_mau', 'Chưa rõ').strip()
            ghi_chu_nhom_mau = data.get('ghi_chu_nhom_mau', '').strip()
            di_ung = data.get('di_ung', '').strip()
            tien_su_benh = data.get('tien_su_benh', '').strip()
            tien_su_gia_dinh = data.get('tien_su_gia_dinh', '').strip()
            nguoi_than_ho_ten = data.get('nguoi_than_ho_ten', '').strip()
            nguoi_than_sdt = data.get('nguoi_than_sdt', '').strip()
            nguoi_than_quan_he = data.get('nguoi_than_quan_he', '').strip()

            cursor.execute('''
                UPDATE benh_nhan SET
                    ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?, cccd = ?, bhyt = ?,
                    email = ?, dia_chi = ?, nhom_mau = ?, ghi_chu_nhom_mau = ?,
                    di_ung = ?, tien_su_benh = ?, tien_su_gia_dinh = ?,
                    nguoi_than_ho_ten = ?, nguoi_than_sdt = ?, nguoi_than_quan_he = ?
                WHERE tai_khoan_id = ?
            ''', (ho_ten, ngay_sinh, gioi_tinh, cccd, bhyt, email, dia_chi,
                  nhom_mau, ghi_chu_nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh,
                  nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, tai_khoan_id))

            cursor.execute('''
                UPDATE tai_khoan SET da_hoan_thien_ho_so = 1, email = ? WHERE id = ?
            ''', (email if email else None, tai_khoan_id))

            # Gui thong bao in-app chao mung benh nhan
            cursor.execute('''
                INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc)
                VALUES (?, N'Chào mừng bạn đến với H2T Healthcare!', N'Hồ sơ y tế điện tử của bạn đã được kích hoạt thành công. Bạn có thể đặt lịch khám trực tuyến và quản lý hồ sơ bệnh án mọi lúc mọi nơi.', N'Hệ thống', '/patient/booking', 0)
            ''', (tai_khoan_id,))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='benh_nhan',
                row_id=tai_khoan_id,
                action='COMPLETE_PROFILE',
                performed_by=tai_khoan_id,
                performed_by_name=ho_ten,
                reason='Bệnh nhân hoàn thiện thông tin cá nhân lần đầu'
            )

            return True, 'Hồ sơ cá nhân đã được hoàn thiện thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi khi cập nhật hồ sơ cá nhân: {str(e)}'"""

if old_reg_block in content:
    content = content.replace(old_reg_block, new_reg_block)
    print("Updated register_patient and added complete_patient_profile in user_model.py")
else:
    print("old_reg_block not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
