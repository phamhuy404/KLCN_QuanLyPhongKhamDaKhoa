from datetime import datetime
from core.database import get_db

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
            birth_year = int(str(p['ngay_sinh'])[:4]) if p.get('ngay_sinh') else 1990
            p['tuoi'] = datetime.now().year - birth_year
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
        birth_year = int(str(p['ngay_sinh'])[:4]) if p.get('ngay_sinh') else 1990
        p['tuoi'] = datetime.now().year - birth_year
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

        cursor.execute('''
            SELECT 
                pk.id, pk.ma_phieu, pk.thoi_gian_kham, pk.ly_do_kham, pk.trieu_chung,
                pk.chan_doan_so_bo, pk.chan_doan_icd, pk.huong_dieu_tri, pk.loi_dan, pk.ngay_tai_kham,
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
                    dv.ten_dich_vu AS ten,
                    dv.loai_dich_vu AS loai,
                    ct.ket_qua,
                    ct.ktv_thuc_hien AS bac_si_thuc_hien,
                    ct.trang_thai
                FROM phieu_chi_dinh cd
                JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
                JOIN dich_vu dv ON ct.dich_vu_id = dv.id
                WHERE cd.phieu_kham_id = ?
            ''', (enc['id'],))
            enc['can_lam_sang'] = [dict(r) for r in cursor.fetchall()]

            # Lấy đơn thuốc
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
                enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Sau 14 ngày)"
            else:
                enc['lich_tai_kham'] = None

        conn.close()
        return encounters

    @staticmethod
    def create_patient(data):
        """Thêm mới bệnh nhân từ quầy tiếp nhận lễ tân."""
        conn = get_db()
        cursor = conn.cursor()

        try:
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
                    pwd = data.get('password') or '123456'
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
                INSERT INTO benh_nhan (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, co_tai_khoan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tai_khoan_id,
                ma_benh_nhan,
                data.get('ho_ten'),
                data.get('ngay_sinh', '1990-01-01'),
                data.get('gioi_tinh', 'Nam'),
                data.get('sdt'),
                data.get('email', ''),
                data.get('cccd', ''),
                data.get('bhyt', ''),
                data.get('dia_chi', ''),
                data.get('nhom_mau', 'Chưa rõ'),
                data.get('di_ung', 'Không có'),
                data.get('tien_su_benh', 'Không có'),
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
