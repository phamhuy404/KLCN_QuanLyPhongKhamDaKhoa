from datetime import datetime, date
from core.database import get_db

def calculate_patient_age(birth_date):
    """Tính tuổi chính xác theo ngày tháng năm sinh, tương thích đa định dạng."""
    if not birth_date:
        return 30
    try:
        s = str(birth_date).strip()
        dt = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                dt = datetime.strptime(s[:10], fmt).date()
                break
            except ValueError:
                pass
        if not dt:
            import re
            m = re.search(r'\b(19\d{2}|20\d{2})\b', s)
            if m:
                return max(0, datetime.now().year - int(m.group(1)))
            return 30
        today = date.today()
        age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
        return max(0, age)
    except Exception:
        return 30

class PatientModel:
    """Model quản lý hồ sơ bệnh nhân, sinh hiệu và lịch sử điều trị."""

    @staticmethod
    def get_all(include_history=False):
        """Lấy danh sách tất cả bệnh nhân kèm sinh hiệu mới nhất."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                b.*,
                t.username,
                s.mach, s.nhiet_do, s.huyet_ap, s.spo2, s.nhip_tho, s.chieu_cao, s.can_nang, s.bmi
            FROM benh_nhan b
            LEFT JOIN tai_khoan t ON b.tai_khoan_id = t.id
            LEFT JOIN chi_so_sinh_ton s ON b.id = s.benh_nhan_id
            ORDER BY b.id ASC
        ''')
        rows = cursor.fetchall()

        patients_list = []
        for r in rows:
            p = dict(r)
            p['tuoi'] = calculate_patient_age(p.get('ngay_sinh'))
            p['vitals'] = {
                'mach': p.get('mach') or '75 lần/phút',
                'nhiet_do': p.get('nhiet_do') or '36.8 °C',
                'huyet_ap': p.get('huyet_ap') or '120/80 mmHg',
                'spo2': p.get('spo2') or '99 %',
                'nhip_tho': p.get('nhip_tho') or '18 lần/phút',
                'chieu_cao': p.get('chieu_cao') or '170 cm',
                'can_nang': p.get('can_nang') or '65 kg',
                'bmi': p.get('bmi') or '22.5 (Bình thường)'
            }
            if include_history:
                p['lich_su_kham'] = PatientModel.get_patient_history(p['id'])
            else:
                p['lich_su_kham'] = []
            patients_list.append(p)

        conn.close()
        return patients_list

    @staticmethod
    def get_by_department(chuyen_khoa_id, include_history=False):
        """Lấy danh sách bệnh nhân đã từng khám hoặc có lịch hẹn tại một chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT
                b.*,
                t.username,
                s.mach, s.nhiet_do, s.huyet_ap, s.spo2, s.nhip_tho, s.chieu_cao, s.can_nang, s.bmi
            FROM benh_nhan b
            LEFT JOIN tai_khoan t ON b.tai_khoan_id = t.id
            LEFT JOIN chi_so_sinh_ton s ON b.id = s.benh_nhan_id
            WHERE b.id IN (
                SELECT benh_nhan_id FROM lich_hen WHERE chuyen_khoa_id = ?
                UNION
                SELECT pk.benh_nhan_id FROM phieu_kham pk 
                JOIN phong_kham ph ON pk.phong_kham_id = ph.id 
                WHERE ph.chuyen_khoa_id = ?
                UNION
                SELECT pk.benh_nhan_id FROM phieu_kham pk
                JOIN bac_si bs ON pk.bac_si_id = bs.id
                WHERE bs.chuyen_khoa_id = ?
            )
            ORDER BY b.id ASC
        ''', (chuyen_khoa_id, chuyen_khoa_id, chuyen_khoa_id))
        rows = cursor.fetchall()

        patients_list = []
        for r in rows:
            p = dict(r)
            p['tuoi'] = calculate_patient_age(p.get('ngay_sinh'))
            p['vitals'] = {
                'mach': p.get('mach') or '75 lần/phút',
                'nhiet_do': p.get('nhiet_do') or '36.8 °C',
                'huyet_ap': p.get('huyet_ap') or '120/80 mmHg',
                'spo2': p.get('spo2') or '99 %',
                'nhip_tho': p.get('nhip_tho') or '18 lần/phút',
                'chieu_cao': p.get('chieu_cao') or '170 cm',
                'can_nang': p.get('can_nang') or '65 kg',
                'bmi': p.get('bmi') or '22.5 (Bình thường)'
            }
            if include_history:
                p['lich_su_kham'] = PatientModel.get_patient_history(p['id'])
            else:
                p['lich_su_kham'] = []
            patients_list.append(p)

        conn.close()
        return patients_list

    @staticmethod
    def get_by_id(patient_id):
        """Lấy chi tiết hồ sơ 360 độ của một bệnh nhân theo ID."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                b.*,
                t.username,
                s.mach, s.nhiet_do, s.huyet_ap, s.spo2, s.nhip_tho, s.chieu_cao, s.can_nang, s.bmi
            FROM benh_nhan b
            LEFT JOIN tai_khoan t ON b.tai_khoan_id = t.id
            LEFT JOIN chi_so_sinh_ton s ON b.id = s.benh_nhan_id
            WHERE b.id = ?
        ''', (patient_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        p = dict(row)
        p['tuoi'] = calculate_patient_age(p.get('ngay_sinh'))
        p['vitals'] = {
            'mach': p.get('mach') or '75 lần/phút',
            'nhiet_do': p.get('nhiet_do') or '36.8 °C',
            'huyet_ap': p.get('huyet_ap') or '120/80 mmHg',
            'spo2': p.get('spo2') or '99 %',
            'nhip_tho': p.get('nhip_tho') or '18 lần/phút',
            'chieu_cao': p.get('chieu_cao') or '170 cm',
            'can_nang': p.get('can_nang') or '65 kg',
            'bmi': p.get('bmi') or '22.5 (Bình thường)'
        }
        conn.close()
        p['lich_su_kham'] = PatientModel.get_patient_history(p['id'])
        return p

    @staticmethod
    def get_patient_history(patient_id):
        """Lấy danh sách các phiếu khám, đơn thuốc và cận lâm sàng của bệnh nhân."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT 
                    pk.id, pk.ma_phieu, pk.thoi_gian_kham, pk.ly_do_kham, pk.trieu_chung,
                    pk.chan_doan_so_bo, pk.chan_doan_icd, pk.huong_dieu_tri, pk.loi_dan, pk.ngay_tai_kham,
                    pk.hinh_anh_kham, pk.trang_thai,
                    COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                    COALESCE(ck.ten_khoa, 'Khoa Nội Tổng Quát') AS khoa,
                    COALESCE(p.ten_phong, 'Phòng Khám Nội 1') AS phong
                FROM phieu_kham pk
                LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
                LEFT JOIN chuyen_khoa ck ON p.chuyen_khoa_id = ck.id
                WHERE pk.benh_nhan_id = ?
                ORDER BY pk.thoi_gian_kham DESC
            ''', (patient_id,))
            encounters = [dict(r) for r in cursor.fetchall()]
        except Exception:
            cursor.execute('''
                SELECT 
                    pk.id, pk.ma_phieu, pk.thoi_gian_kham, pk.ly_do_kham, pk.trieu_chung,
                    pk.chan_doan_so_bo, pk.chan_doan_icd, pk.huong_dieu_tri, pk.loi_dan, pk.ngay_tai_kham,
                    NULL AS hinh_anh_kham, pk.trang_thai,
                    COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                    COALESCE(ck.ten_khoa, 'Khoa Nội Tổng Quát') AS khoa,
                    COALESCE(p.ten_phong, 'Phòng Khám Nội 1') AS phong
                FROM phieu_kham pk
                LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
                LEFT JOIN chuyen_khoa ck ON p.chuyen_khoa_id = ck.id
                WHERE pk.benh_nhan_id = ?
                ORDER BY pk.thoi_gian_kham DESC
            ''', (patient_id,))
            encounters = [dict(r) for r in cursor.fetchall()]

        for enc in encounters:
            # Lấy cận lâm sàng
            cursor.execute('''
                SELECT 
                    ct.id AS chi_tiet_id,
                    dv.ten_dich_vu AS ten,
                    dv.loai_dich_vu AS loai,
                    ct.ket_qua,
                    ct.file_ket_qua,
                    ct.ktv_thuc_hien AS bac_si_thuc_hien,
                    ct.trang_thai
                FROM phieu_chi_dinh cd
                JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
                JOIN dich_vu dv ON ct.dich_vu_id = dv.id
                WHERE cd.phieu_kham_id = ?
            ''', (enc['id'],))
            enc['can_lam_sang'] = [dict(r) for r in cursor.fetchall()]

            # Lấy thông tin đơn thuốc và hình thức mua
            cursor.execute('''
                SELECT id AS don_thuoc_id, ma_don_thuoc, trang_thai AS trang_thai_don_thuoc, hinh_thuc_mua
                FROM don_thuoc
                WHERE phieu_kham_id = ?
            ''', (enc['id'],))
            dt_info = cursor.fetchone()
            if dt_info:
                enc['don_thuoc_id'] = dt_info['don_thuoc_id']
                enc['ma_don_thuoc'] = dt_info['ma_don_thuoc']
                enc['trang_thai_don_thuoc'] = dt_info['trang_thai_don_thuoc']
                enc['hinh_thuc_mua'] = dt_info.get('hinh_thuc_mua') or 'Chưa chọn'
            else:
                enc['don_thuoc_id'] = None
                enc['ma_don_thuoc'] = None
                enc['trang_thai_don_thuoc'] = None
                enc['hinh_thuc_mua'] = None

            # Lấy chi tiết các loại thuốc trong đơn
            cursor.execute('''
                SELECT 
                    t.ten_thuoc AS ten,
                    t.hoat_chat,
                    ct.so_luong,
                    t.don_vi_tinh,
                    ct.cach_dung
                FROM don_thuoc dt
                JOIN chi_tiet_don_thuoc ct ON dt.id = ct.don_thuoc_id
                JOIN thuoc t ON ct.thuoc_id = t.id
                WHERE dt.phieu_kham_id = ?
            ''', (enc['id'],))
            dt_rows = [dict(r) for r in cursor.fetchall()]
            for dt_row in dt_rows:
                dt_row['so_luong'] = f"{dt_row['so_luong']} {dt_row['don_vi_tinh']}"
            enc['don_thuoc'] = dt_rows

            if enc.get('ngay_tai_kham'):
                try:
                    kham_d = datetime.strptime(str(enc.get('thoi_gian_kham'))[:10], '%Y-%m-%d').date()
                    tai_d = datetime.strptime(str(enc.get('ngay_tai_kham'))[:10], '%Y-%m-%d').date()
                    delta = (tai_d - kham_d).days
                    if delta > 0:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Sau {delta} ngày)"
                    elif delta == 0:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Trong ngày)"
                    else:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']}"
                except Exception:
                    enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']}"
            else:
                enc['lich_tai_kham'] = None

        conn.close()
        return encounters

    @staticmethod
    def get_all_lab_results(patient_id):
        """Lấy toàn bộ kết quả Cận lâm sàng của bệnh nhân và tổng hợp số liệu tại BackEnd."""
        history = PatientModel.get_patient_history(patient_id)
        all_cls = []
        for enc in history:
            for cls in enc.get('can_lam_sang', []):
                all_cls.append({
                    'cls': cls,
                    'enc': enc,
                    'ten': cls.get('ten'),
                    'loai': cls.get('loai') or 'Xét nghiệm',
                    'ket_qua': cls.get('ket_qua') or 'Bình thường trong giới hạn tham chiếu',
                    'bac_si_thuc_hien': cls.get('bac_si_thuc_hien') or enc.get('bac_si') or 'KTV Xét nghiệm',
                    'file_ket_qua': cls.get('file_ket_qua'),
                    'trang_thai': cls.get('trang_thai') or 'Đã có kết quả',
                    'ma_phieu': enc.get('ma_phieu'),
                    'thoi_gian_kham': enc.get('thoi_gian_kham')
                })
        cls_stats = {
            'tong_cls': len(all_cls),
            'da_co_ket_qua': len([x for x in all_cls if x.get('trang_thai') in ['Đã có kết quả', 'Đã duyệt']]),
            'dot_kham_lien_quan': len(history)
        }
        return all_cls, cls_stats

    @staticmethod
    def create_patient(data):
        """Thêm mới bệnh nhân từ quầy tiếp nhận lễ tân."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            from core.validators import validate_name, validate_phone, validate_cccd, validate_bhyt, validate_birth_date
            ok_name, res_name = validate_name(data.get('ho_ten', ''), 'Họ và tên bệnh nhân')
            if not ok_name:
                conn.close()
                return False, None, res_name
            data['ho_ten'] = res_name

            ok_phone, res_phone = validate_phone(data.get('sdt', ''), 'Số điện thoại')
            if not ok_phone:
                conn.close()
                return False, None, res_phone
            data['sdt'] = res_phone

            if data.get('cccd'):
                ok_cccd, res_cccd = validate_cccd(data.get('cccd'), required=False)
                if not ok_cccd:
                    conn.close()
                    return False, None, res_cccd
                data['cccd'] = res_cccd

            if data.get('bhyt'):
                ok_bhyt, res_bhyt = validate_bhyt(data.get('bhyt'), required=False)
                if not ok_bhyt:
                    conn.close()
                    return False, None, res_bhyt
                data['bhyt'] = res_bhyt

            if data.get('ngay_sinh'):
                ok_ns, res_ns = validate_birth_date(str(data.get('ngay_sinh')), is_staff=False, required=False)
                if not ok_ns:
                    conn.close()
                    return False, None, res_ns

            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM benh_nhan')
            next_id = cursor.fetchone()['next_id']
            ma_benh_nhan = f"BN2609{str(next_id).zfill(3)}"

            tai_khoan_id = None
            co_tai_khoan = 0
            if data.get('create_account'):
                sdt = data.get('sdt')
                from core.security import hash_password
                cursor.execute('SELECT id FROM tai_khoan WHERE username = ? OR sdt = ?', (sdt, sdt))
                existing_acc = cursor.fetchone()
                if not existing_acc:
                    pwd = data.get('password') or '123'
                    cursor.execute('''
                        INSERT INTO tai_khoan (vai_tro_id, username, password, email, sdt, trang_thai)
                        VALUES (6, ?, ?, ?, ?, 1)
                    ''', (sdt, hash_password(pwd), data.get('email', ''), sdt))
                    tai_khoan_id = cursor.lastrowid
                    co_tai_khoan = 1
                else:
                    tai_khoan_id = existing_acc['id']
                    co_tai_khoan = 1

            cursor.execute('''
                INSERT INTO benh_nhan (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, ghi_chu_nhom_mau, di_ung, tien_su_benh, co_tai_khoan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tai_khoan_id,
                ma_benh_nhan,
                data.get('ho_ten'),
                data.get('ngay_sinh', '1990-01-01'),
                data.get('gioi_tinh', 'Nam'),
                data.get('sdt'),
                data.get('email', ''),
                data.get('cccd', ''),
                data.get('bhyt') or data.get('so_bhyt', ''),
                data.get('dia_chi', ''),
                data.get('nhom_mau', 'Chưa rõ'),
                data.get('ghi_chu_nhom_mau') or data.get('nhom_mau_bien_the', ''),
                data.get('di_ung') or data.get('tien_su_di_ung', 'Không có'),
                data.get('tien_su_benh') or data.get('benh_ly_nen', 'Không có'),
                co_tai_khoan
            ))
            patient_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO chi_so_sinh_ton (benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                data.get('mach', '75 lần/phút'),
                data.get('nhiet_do', '36.8 °C'),
                data.get('huyet_ap', '120/80 mmHg'),
                data.get('spo2', '99 %'),
                data.get('nhip_tho', '18 lần/phút'),
                data.get('chieu_cao', '170 cm'),
                data.get('can_nang', '65 kg'),
                data.get('bmi', '22.5 (Bình thường)')
            ))

            conn.commit()
            conn.close()
            return True, patient_id, ma_benh_nhan
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, None, str(e)

    @staticmethod
    def update_profile(patient_id, data):
        """Cập nhật thông tin cá nhân và hồ sơ y tế của bệnh nhân với kiểm tra ràng buộc chặt chẽ."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            from core.validators import validate_name, validate_phone, validate_cccd, validate_bhyt, validate_birth_date, validate_email
            if data.get('username'):
                new_username = str(data.get('username')).strip()
                if ' ' in new_username:
                    conn.close()
                    return False, "Tên đăng nhập không được chứa khoảng cách!"
                if len(new_username) < 3 or len(new_username) > 50:
                    conn.close()
                    return False, "Tên đăng nhập phải từ 3 đến 50 ký tự!"
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    acc_id = bn_row['tai_khoan_id']
                    cursor.execute('SELECT id FROM tai_khoan WHERE username = ? AND id != ?', (new_username, acc_id))
                    if cursor.fetchone():
                        conn.close()
                        return False, "Tên đăng nhập này đã được sử dụng bởi tài khoản khác!"
                    cursor.execute('UPDATE tai_khoan SET username = ? WHERE id = ?', (new_username, acc_id))

            if data.get('ho_ten'):
                ok_name, res_name = validate_name(data.get('ho_ten'), 'Họ và tên bệnh nhân')
                if not ok_name:
                    conn.close()
                    return False, res_name
                data['ho_ten'] = res_name

            if data.get('sdt'):
                ok_phone, res_phone = validate_phone(data.get('sdt'), 'Số điện thoại', required=False)
                if not ok_phone:
                    conn.close()
                    return False, res_phone
                data['sdt'] = res_phone

            if data.get('cccd'):
                ok_cccd, res_cccd = validate_cccd(data.get('cccd'), required=False)
                if not ok_cccd:
                    conn.close()
                    return False, res_cccd
                data['cccd'] = res_cccd

            if data.get('bhyt'):
                ok_bhyt, res_bhyt = validate_bhyt(data.get('bhyt'), required=False)
                if not ok_bhyt:
                    conn.close()
                    return False, res_bhyt
                data['bhyt'] = res_bhyt

            if data.get('email'):
                ok_email, res_email = validate_email(data.get('email'), required=False)
                if not ok_email:
                    conn.close()
                    return False, res_email
                data['email'] = res_email

            if data.get('ngay_sinh'):
                ok_ns, res_ns = validate_birth_date(str(data.get('ngay_sinh')), is_staff=False, required=False)
                if not ok_ns:
                    conn.close()
                    return False, res_ns

            if data.get('nguoi_than_ho_ten'):
                ok_nth, res_nth = validate_name(data.get('nguoi_than_ho_ten'), 'Họ tên người thân')
                if not ok_nth:
                    conn.close()
                    return False, res_nth
                data['nguoi_than_ho_ten'] = res_nth

            if data.get('nguoi_than_sdt'):
                ok_nts, res_nts = validate_phone(data.get('nguoi_than_sdt'), 'Số điện thoại người thân', required=False)
                if not ok_nts:
                    conn.close()
                    return False, res_nts
                data['nguoi_than_sdt'] = res_nts

            cursor.execute('''
                UPDATE benh_nhan
                SET ho_ten = COALESCE(NULLIF(?, ''), ho_ten),
                    ngay_sinh = COALESCE(?, ngay_sinh),
                    gioi_tinh = COALESCE(NULLIF(?, ''), gioi_tinh),
                    sdt = COALESCE(NULLIF(?, ''), sdt),
                    email = COALESCE(?, email),
                    cccd = COALESCE(NULLIF(?, ''), cccd),
                    bhyt = COALESCE(?, bhyt),
                    dia_chi = COALESCE(?, dia_chi),
                    nhom_mau = COALESCE(NULLIF(?, ''), nhom_mau),
                    ghi_chu_nhom_mau = COALESCE(?, ghi_chu_nhom_mau),
                    di_ung = COALESCE(?, di_ung),
                    tien_su_benh = COALESCE(?, tien_su_benh),
                    nguoi_than_ho_ten = COALESCE(?, nguoi_than_ho_ten),
                    nguoi_than_sdt = COALESCE(?, nguoi_than_sdt),
                    nguoi_than_quan_he = COALESCE(?, nguoi_than_quan_he)
                WHERE id = ?
            ''', (
                data.get('ho_ten'),
                data.get('ngay_sinh'),
                data.get('gioi_tinh'),
                data.get('sdt'),
                data.get('email'),
                data.get('cccd'),
                data.get('bhyt') or data.get('so_bhyt'),
                data.get('dia_chi'),
                data.get('nhom_mau'),
                data.get('ghi_chu_nhom_mau') or data.get('nhom_mau_bien_the'),
                data.get('di_ung') or data.get('tien_su_di_ung'),
                data.get('tien_su_benh') or data.get('benh_ly_nen'),
                data.get('nguoi_than_ho_ten'),
                data.get('nguoi_than_sdt'),
                data.get('nguoi_than_quan_he'),
                patient_id
            ))

            cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (patient_id,))
            p_row = cursor.fetchone()
            if p_row and p_row.get('tai_khoan_id'):
                cursor.execute('''
                    UPDATE tai_khoan
                    SET email = COALESCE(NULLIF(?, ''), email),
                        sdt = COALESCE(NULLIF(?, ''), sdt)
                    WHERE id = ?
                ''', (data.get('email', ''), data.get('sdt', ''), p_row['tai_khoan_id']))

            conn.commit()
            conn.close()
            return True, "Cập nhật hồ sơ thành công"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def update_patient_avatar(patient_id, avatar_path):
        """Cập nhật đường dẫn ảnh đại diện cho hồ sơ bệnh nhân."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE benh_nhan SET avatar = ? WHERE id = ?', (avatar_path, patient_id))
            conn.commit()
            conn.close()
            return True, "Cập nhật ảnh đại diện thành công."
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)


