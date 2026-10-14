from datetime import datetime
from core.database import get_db
from core.audit import AuditLogger

class MedicalRecordModel:
    """Model quản lý hồ sơ bệnh án điện tử EMR, phiếu khám, chỉ định CLS và đơn thuốc."""

    @staticmethod
    def get_all_lab_orders():
        """Lấy toàn bộ danh sách phiếu chỉ định cận lâm sàng kèm chi tiết từng dịch vụ."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                cd.id, cd.ma_chi_dinh, cd.thoi_gian_chi_dinh, cd.trang_thai AS trang_thai_phieu, cd.ghi_chu,
                bn.id AS patient_id, bn.ma_benh_nhan, bn.ho_ten AS benh_nhan, bn.sdt AS sdt_benh_nhan,
                COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                dv.id AS dich_vu_id, dv.ten_dich_vu AS dich_vu, dv.loai_dich_vu AS loai, dv.don_gia,
                ct.id AS chi_tiet_id, ct.ket_qua, ct.file_ket_qua, ct.ktv_thuc_hien, ct.thoi_gian_thuc_hien,
                ct.trang_thai, ct.bac_si_duyet, ct.thoi_gian_duyet, ct.ghi_chu_duyet
            FROM phieu_chi_dinh cd
            JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            LEFT JOIN bac_si bs ON cd.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
            LEFT JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            ORDER BY cd.id DESC, ct.id ASC
        ''')
        orders = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return orders

    @staticmethod
    def get_lab_orders_by_patient(patient_id, approved_only=True):
        """Lấy danh sách kết quả xét nghiệm của bệnh nhân (bệnh nhân chỉ xem kết quả đã duyệt)."""
        all_orders = MedicalRecordModel.get_all_lab_orders()
        patient_orders = [o for o in all_orders if o.get('patient_id') == patient_id]
        if approved_only:
            # Bệnh nhân chỉ xem các dịch vụ đã duyệt
            return [o for o in patient_orders if o.get('trang_thai') == 'Đã duyệt']
        return patient_orders

    @staticmethod
    def get_lab_item_by_id(chi_tiet_id):
        """Lấy chi tiết một mục xét nghiệm theo ID chi tiết chỉ định."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ct.*, cd.ma_chi_dinh, cd.phieu_kham_id, cd.bac_si_id,
                   dv.ten_dich_vu, dv.loai_dich_vu,
                   bn.id AS patient_id, bn.ho_ten AS ten_benh_nhan, bn.ma_benh_nhan
            FROM chi_tiet_chi_dinh ct
            JOIN phieu_chi_dinh cd ON ct.phieu_chi_dinh_id = cd.id
            JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            WHERE ct.id = ?
        ''', (chi_tiet_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_lab_result(chi_tiet_id, ket_qua, file_ket_qua=None, ktv_name=None, audit_user=None):
        """KTV cập nhật kết quả xét nghiệm. Không cho phép sửa nếu kết quả đã được bác sĩ duyệt."""
        item = MedicalRecordModel.get_lab_item_by_id(chi_tiet_id)
        if not item:
            return False, "Không tìm thấy chỉ định xét nghiệm!"

        if item.get('trang_thai') == 'Đã duyệt':
            return False, "Kết quả xét nghiệm này đã được bác sĩ duyệt nội bộ, không thể chỉnh sửa!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ktv_str = ktv_name or (audit_user.get('ho_ten') if audit_user else 'Kỹ thuật viên')

            cursor.execute('''
                UPDATE chi_tiet_chi_dinh
                SET ket_qua = ?, file_ket_qua = COALESCE(?, file_ket_qua), ktv_thuc_hien = ?, nguoi_nhap = ?,
                    thoi_gian_thuc_hien = ?, trang_thai = ?
                WHERE id = ?
            ''', (ket_qua, file_ket_qua, ktv_str, ktv_str, now_str, 'Chờ duyệt', chi_tiet_id))

            # Cập nhật trạng thái phiếu cha thành 'Đang thực hiện'
            cursor.execute('''
                UPDATE phieu_chi_dinh SET trang_thai = ? WHERE id = ?
            ''', ('Đang thực hiện', item['phieu_chi_dinh_id']))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='chi_tiet_chi_dinh',
                row_id=chi_tiet_id,
                action='UPDATE_LAB_RESULT',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=ktv_str,
                reason=f"Nhập kết quả xét nghiệm {item.get('ten_dich_vu')}",
                before_data={'ket_qua': item.get('ket_qua'), 'trang_thai': item.get('trang_thai')},
                after_data={'ket_qua': ket_qua, 'trang_thai': 'Chờ duyệt', 'ktv': ktv_str}
            )

            return True, "Cập nhật kết quả xét nghiệm thành công và đã chuyển sang trạng thái 'Chờ duyệt'!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi lưu kết quả: {str(e)}"

    @staticmethod
    def approve_lab_result(chi_tiet_id, doctor_name=None, approval_note=None, audit_user=None):
        """Bác sĩ duyệt kết quả cận lâm sàng (xác nhận duyệt nội bộ)."""
        item = MedicalRecordModel.get_lab_item_by_id(chi_tiet_id)
        if not item:
            return False, "Không tìm thấy chỉ định xét nghiệm!"

        if not item.get('ket_qua') or item.get('ket_qua').strip() == '':
            return False, "Chưa có kết quả xét nghiệm từ KTV, không thể duyệt!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            doc_str = doctor_name or (audit_user.get('ho_ten') if audit_user else 'Bác sĩ chuyên khoa')

            cursor.execute('''
                UPDATE chi_tiet_chi_dinh
                SET trang_thai = ?, bac_si_duyet = ?, thoi_gian_duyet = ?, ghi_chu_duyet = ?
                WHERE id = ?
            ''', ('Đã duyệt', doc_str, now_str, approval_note, chi_tiet_id))

            # Kiểm tra nếu tất cả các dịch vụ trong phiếu chỉ định đã duyệt thì hoàn tất phiếu
            cursor.execute('''
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN trang_thai = ? THEN 1 ELSE 0 END) AS approved_count
                FROM chi_tiet_chi_dinh
                WHERE phieu_chi_dinh_id = ?
            ''', ('Đã duyệt', item['phieu_chi_dinh_id']))
            st = cursor.fetchone()
            if st and st['total'] == st['approved_count']:
                cursor.execute("UPDATE phieu_chi_dinh SET trang_thai = ? WHERE id = ?", ('Đã duyệt', item['phieu_chi_dinh_id']))


            # Gửi thông báo in-app cho bệnh nhân
            if item.get('patient_id'):
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (item['patient_id'],))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, 'Kết quả xét nghiệm', '/patient/dashboard', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đã có kết quả xét nghiệm: {item['ten_dich_vu']}",
                        f"Bác sĩ {doc_str} đã duyệt kết quả xét nghiệm {item['ten_dich_vu']} của bạn. Bạn có thể xem kết quả chi tiết trong hồ sơ cá nhân.",
                        now_str
                    ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='chi_tiet_chi_dinh',
                row_id=chi_tiet_id,
                action='APPROVE_LAB_RESULT',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=doc_str,
                reason=approval_note or 'Xác nhận duyệt kết quả xét nghiệm nội bộ',
                before_data={'trang_thai': item.get('trang_thai')},
                after_data={'trang_thai': 'Đã duyệt', 'bac_si_duyet': doc_str}
            )

            return True, f"Đã xác nhận duyệt kết quả {item['ten_dich_vu']} thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi duyệt kết quả: {str(e)}"

    @staticmethod
    def get_all_prescriptions():
        """Lấy toàn bộ danh sách đơn thuốc."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                dt.id, dt.ma_don_thuoc AS ma_don, dt.thoi_gian_ke AS gio, dt.loi_dan, dt.trang_thai,
                dt.ly_do_huy, dt.nguoi_huy, dt.thoi_gian_huy,
                bn.id AS patient_id, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan,
                COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                t.id AS thuoc_id, t.ten_thuoc AS thuoc,
                ct.id AS chi_tiet_id, ct.so_luong, ct.lieu_dung, ct.cach_dung
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
    def get_examination_by_id(record_id):
        """Lấy thông tin chi tiết một phiếu khám bệnh EMR."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pk.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                   nv.ho_ten AS ten_bac_si, p.ten_phong
            FROM phieu_kham pk
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
            WHERE pk.id = ?
        ''', (record_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_examination(record_id, doctor_id, diagnosis, icd, treatment, advice, reexam_date=None, reason=None, audit_user=None):
        """Bác sĩ chỉnh sửa hồ sơ bệnh án EMR: Lưu thay đổi và ghi nhận lịch sử trước/sau có vết kiểm toán."""
        old_rec = MedicalRecordModel.get_examination_by_id(record_id)
        if not old_rec:
            return False, "Không tìm thấy hồ sơ bệnh án!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE phieu_kham
                SET chan_doan_so_bo = ?, chan_doan_icd = ?, huong_dieu_tri = ?, loi_dan = ?, ngay_tai_kham = ?
                WHERE id = ?
            ''', (diagnosis, icd, treatment, advice, reexam_date, record_id))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='phieu_kham',
                row_id=record_id,
                action='UPDATE_EMR',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Bác sĩ',
                reason=reason or 'Bác sĩ cập nhật hồ sơ bệnh án chuyên môn',
                before_data={
                    'chan_doan_so_bo': old_rec.get('chan_doan_so_bo'),
                    'chan_doan_icd': old_rec.get('chan_doan_icd'),
                    'huong_dieu_tri': old_rec.get('huong_dieu_tri'),
                    'loi_dan': old_rec.get('loi_dan'),
                    'ngay_tai_kham': str(old_rec.get('ngay_tai_kham'))
                },
                after_data={
                    'chan_doan_so_bo': diagnosis,
                    'chan_doan_icd': icd,
                    'huong_dieu_tri': treatment,
                    'loi_dan': advice,
                    'ngay_tai_kham': str(reexam_date) if reexam_date else None
                }
            )

            return True, "Cập nhật hồ sơ bệnh án điện tử thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cập nhật bệnh án: {str(e)}"

    @staticmethod
    def save_examination(patient_id, doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date=None, lab_service_ids=None, medicines=None, audit_user=None):
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

            # 2. Tạo chỉ định cận lâm sàng nếu có (Trạng thái khởi tạo: 'Chờ thực hiện')
            if lab_service_ids and len(lab_service_ids) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, ?)
                ''', (ma_cd, phieu_kham_id, valid_doctor_id, 'Chờ thực hiện'))
                chi_dinh_id = cursor.lastrowid

                for s_id in lab_service_ids:
                    cursor.execute('SELECT don_gia, bhyt_chi_tra_pt FROM dich_vu WHERE id = ?', (s_id,))
                    dv_row = cursor.fetchone()
                    if dv_row:
                        tong_tien_kham += float(dv_row['don_gia'])
                        tien_bhyt += float(dv_row['don_gia']) * (float(dv_row['bhyt_chi_tra_pt']) / 100.0)

                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, NULL, ?)
                    ''', (chi_dinh_id, s_id, 'Chờ thực hiện'))

            # 3. Tạo đơn thuốc nếu có (Trạng thái khởi tạo: 'Chưa cấp phát')
            if medicines and len(medicines) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ma_dt, phieu_kham_id, valid_doctor_id, advice, 'Chưa cấp phát'))
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

            AuditLogger.log(
                table_name='phieu_kham',
                row_id=phieu_kham_id,
                action='CREATE_EXAMINATION',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Bác sĩ',
                reason='Bác sĩ hoàn thành phiên khám bệnh',
                after_data={'ma_phieu': ma_phieu, 'patient_id': patient_id, 'icd': icd, 'diagnosis': diagnosis}
            )

            return True, ma_phieu
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

