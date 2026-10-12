from datetime import datetime
from core.database import get_db

class MedicalRecordModel:
    """Model quản lý hồ sơ bệnh án điện tử EMR, phiếu khám, chỉ định CLS và đơn thuốc."""

    @staticmethod
    def get_all_lab_orders():
        """Lấy toàn bộ danh sách phiếu chỉ định cận lâm sàng."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                cd.id, cd.ma_chi_dinh, cd.thoi_gian_chi_dinh, cd.trang_thai,
                bn.id AS patient_id, bn.ma_benh_nhan, bn.ho_ten AS benh_nhan,
                COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                dv.ten_dich_vu AS dich_vu, dv.loai_dich_vu AS loai,
                ct.id AS chi_tiet_id, ct.ket_qua, ct.ktv_thuc_hien
            FROM phieu_chi_dinh cd
            JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            LEFT JOIN bac_si bs ON cd.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
            LEFT JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            ORDER BY cd.id DESC
        ''')
        orders = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return orders

    @staticmethod
    def get_all_prescriptions():
        """Lấy toàn bộ danh sách đơn thuốc."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                dt.id, dt.ma_don_thuoc AS ma_don, dt.thoi_gian_ke AS gio, dt.loi_dan, dt.trang_thai,
                bn.id AS patient_id, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan,
                COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                t.ten_thuoc AS thuoc,
                ct.so_luong, ct.lieu_dung, ct.cach_dung
            FROM don_thuoc dt
            JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            LEFT JOIN bac_si bs ON dt.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN chi_tiet_don_thuoc ct ON dt.id = ct.don_thuoc_id
            LEFT JOIN thuoc t ON ct.thuoc_id = t.id
            ORDER BY dt.id DESC
        ''')
        prescriptions = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return prescriptions

    @staticmethod
    def save_examination(patient_id, doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date=None, lab_service_ids=None, medicines=None):
        """Lưu toàn bộ phiên khám EMR (Phiếu khám, chỉ định CLS, đơn thuốc và hóa đơn viện phí)."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            # Kiểm tra doctor_id có tồn tại trong bảng bac_si không
            valid_doctor_id = None
            if doctor_id:
                cursor.execute('SELECT id FROM bac_si WHERE id = ?', (doctor_id,))
                if cursor.fetchone():
                    valid_doctor_id = doctor_id

            # 1. Tạo phiếu khám bệnh
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_kham')
            pk_id = cursor.fetchone()['next_id']
            ma_phieu = f"PK2609{str(pk_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO phieu_kham (ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Hoàn thành')
            ''', (ma_phieu, patient_id, valid_doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date))
            phieu_kham_id = cursor.lastrowid

            tong_tien_kham = 150000.0
            tien_bhyt = 120000.0

            # 2. Tạo chỉ định cận lâm sàng nếu có
            if lab_service_ids and len(lab_service_ids) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, 'Hoàn thành')
                ''', (ma_cd, phieu_kham_id, valid_doctor_id))
                chi_dinh_id = cursor.lastrowid

                for s_id in lab_service_ids:
                    cursor.execute('SELECT don_gia, bhyt_chi_tra_pt FROM dich_vu WHERE id = ?', (s_id,))
                    dv_row = cursor.fetchone()
                    if dv_row:
                        tong_tien_kham += float(dv_row['don_gia'])
                        tien_bhyt += float(dv_row['don_gia']) * (float(dv_row['bhyt_chi_tra_pt']) / 100.0)

                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, 'Chỉ số bình thường', 'Hoàn thành')
                    ''', (chi_dinh_id, s_id))

            # 3. Tạo đơn thuốc nếu có
            if medicines and len(medicines) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai)
                    VALUES (?, ?, ?, ?, 'Chờ phát thuốc')
                ''', (ma_dt, phieu_kham_id, valid_doctor_id, advice))
                don_thuoc_id = cursor.lastrowid

                for m in medicines:
                    thuoc_id = m.get('thuoc_id')
                    so_luong = int(m.get('so_luong', 1))
                    lieu_dung = m.get('lieu_dung', 'Ngày 2 lần, lần 1 viên')
                    cach_dung = m.get('cach_dung', 'Uống sau ăn')

                    cursor.execute('SELECT don_gia FROM thuoc WHERE id = ?', (thuoc_id,))
                    th_row = cursor.fetchone()
                    if th_row:
                        tong_tien_kham += float(th_row['don_gia']) * so_luong

                    cursor.execute('''
                        INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung))

            # 4. Tự động sinh hóa đơn viện phí
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
            hd_next = cursor.fetchone()['next_id']
            ma_hd = f"HD2609{str(hd_next).zfill(3)}"
            thanh_tien = max(0.0, tong_tien_kham - tien_bhyt)

            cursor.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, 'Chưa thanh toán')
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien))

            conn.commit()
            conn.close()
            return True, ma_phieu
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
