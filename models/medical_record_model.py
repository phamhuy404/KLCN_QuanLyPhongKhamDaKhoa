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
                bn.id AS patient_id, bn.ma_benh_nhan, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan, bn.sdt AS sdt_benh_nhan,
                COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                dv.id AS dich_vu_id, dv.ten_dich_vu AS dich_vu, dv.loai_dich_vu AS loai, dv.don_gia,
                ct.id AS chi_tiet_id, ct.ket_qua, ct.file_ket_qua, ct.ktv_thuc_hien, ct.thoi_gian_thuc_hien,
                ct.trang_thai, ct.bac_si_duyet, ct.thoi_gian_duyet, ct.ghi_chu_duyet,
                COALESCE(
                    (SELECT TOP 1 hd.trang_thai 
                     FROM hoa_don hd 
                     WHERE hd.phieu_kham_id = pk.id AND hd.ma_hoa_don NOT LIKE 'HDT%' AND hd.trang_thai != N'Đã hủy'
                     ORDER BY hd.id ASC),
                    N'Chưa thanh toán'
                ) AS trang_thai_thanh_toan
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
                        f"Đã có kết quả Cận lâm sàng: {item['ten_dich_vu']}",
                        f"Bác sĩ {doc_str} đã phê duyệt kết quả {item['ten_dich_vu']}. Vui lòng quay trở lại Phòng khám ban đầu để Bác sĩ đọc kết quả, kết luận chẩn đoán và tư vấn phác đồ điều trị.",
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
                dt.hinh_thuc_mua, dt.nguoi_duyet, dt.ngay_duyet,
                dt.ly_do_huy, dt.nguoi_huy, dt.thoi_gian_huy,
                bn.id AS patient_id, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan,
                COALESCE(nv.ho_ten, 'Bác sĩ trực') AS bac_si,
                t.id AS thuoc_id, t.ten_thuoc, t.don_vi_tinh,
                ct.id AS chi_tiet_id, ct.so_luong, ct.lieu_dung, ct.cach_dung,
                (SELECT TOP 1 hd.trang_thai FROM hoa_don hd WHERE hd.phieu_kham_id = pk.id AND hd.ma_hoa_don LIKE 'HDT%' AND hd.trang_thai != N'Đã hủy' ORDER BY hd.id DESC) AS trang_thai_hoa_don,
                (SELECT TOP 1 hd.trang_thai_nhan_thuoc FROM hoa_don hd WHERE hd.phieu_kham_id = pk.id AND hd.ma_hoa_don LIKE 'HDT%' AND hd.trang_thai != N'Đã hủy' ORDER BY hd.id DESC) AS trang_thai_nhan_thuoc,
                (SELECT TOP 1 hd.ma_hoa_don FROM hoa_don hd WHERE hd.phieu_kham_id = pk.id AND hd.ma_hoa_don LIKE 'HDT%' AND hd.trang_thai != N'Đã hủy' ORDER BY hd.id DESC) AS ma_hoa_don
            FROM don_thuoc dt
            JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
            JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
            LEFT JOIN bac_si bs ON dt.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN chi_tiet_don_thuoc ct ON dt.id = ct.don_thuoc_id
            LEFT JOIN thuoc t ON ct.thuoc_id = t.id
            ORDER BY dt.id DESC
        ''')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Nhóm theo từng mã đơn thuốc
        grouped = {}
        for r in rows:
            dt_id = r['id']
            if dt_id not in grouped:
                item_copy = dict(r)
                item_copy['medicines_list'] = []
                grouped[dt_id] = item_copy
            if r.get('ten_thuoc'):
                med_str = f"{r['ten_thuoc']} ({r['so_luong']} {r.get('don_vi_tinh') or 'viên'})"
                grouped[dt_id]['medicines_list'].append(med_str)

        prescriptions = list(grouped.values())
        for p in prescriptions:
            p['thuoc'] = ", ".join(p['medicines_list']) if p['medicines_list'] else 'Theo đơn bác sĩ'

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
    def finish_examination(record_id, diagnosis, icd, treatment, advice, reexam_date=None, medicines=None, images=None, audit_user=None):
        """Bác sĩ kết luận chẩn đoán xác định, kê đơn thuốc và hoàn tất phiên khám sau khi có kết quả CLS."""
        old_rec = MedicalRecordModel.get_examination_by_id(record_id)
        if not old_rec:
            return False, "Không tìm thấy hồ sơ bệnh án!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Cập nhật phiếu khám sang Hoàn thành
            import json
            images_json = json.dumps(images, ensure_ascii=False) if isinstance(images, list) else (str(images) if images else None)
            cursor.execute('''
                UPDATE phieu_kham
                SET chan_doan_so_bo = ?, chan_doan_icd = ?, huong_dieu_tri = ?, loi_dan = ?, ngay_tai_kham = ?,
                    hinh_anh_kham = COALESCE(?, hinh_anh_kham), trang_thai = N'Hoàn thành'
                WHERE id = ?
            ''', (diagnosis, icd, treatment, advice, reexam_date, images_json, record_id))

            # 2. Cập nhật lịch hẹn sang Đã khám
            cursor.execute('''
                UPDATE TOP (1) lich_hen
                SET trang_thai = N'Đã khám'
                WHERE benh_nhan_id = ? AND trang_thai IN (N'Chờ kết quả CLS', N'Đang khám', N'Đã tiếp nhận')
            ''', (old_rec['benh_nhan_id'],))

            # 3. Kê đơn thuốc nếu có
            if medicines and len(medicines) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai, hinh_thuc_mua)
                    VALUES (?, ?, ?, ?, N'Chờ bệnh nhân xác nhận mua', N'Chưa chọn')
                ''', (ma_dt, record_id, old_rec.get('bac_si_id'), advice))
                don_thuoc_id = cursor.lastrowid

                for m in medicines:
                    thuoc_id = m.get('thuoc_id')
                    so_luong = int(m.get('so_luong', 1))
                    lieu_dung = m.get('lieu_dung', 'Theo hướng dẫn bác sĩ')
                    cach_dung = m.get('cach_dung', 'Uống sau ăn')
                    cursor.execute('''
                        INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung))

            # Gửi thông báo hoàn tất phiên khám cho bệnh nhân
            if old_rec.get('benh_nhan_id'):
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (old_rec['benh_nhan_id'],))
                bn_fin = cursor.fetchone()
                if bn_fin and bn_fin.get('tai_khoan_id'):
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, 'Khám bệnh', '/patient/records', 0, ?)
                    ''', (
                        bn_fin['tai_khoan_id'],
                        f"Hoàn thành khám bệnh: {old_rec.get('ma_phieu')}",
                        f"Bác sĩ đã có kết quả cận lâm sàng và kết luận chẩn đoán: {icd}. Vui lòng kiểm tra hồ sơ bệnh án và đơn thuốc.",
                        now_str
                    ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='phieu_kham',
                row_id=record_id,
                action='FINISH_EXAMINATION',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Bác sĩ',
                reason='Bác sĩ hoàn tất phiên khám sau khi có kết quả CLS',
                after_data={'trang_thai': 'Hoàn thành', 'chan_doan_icd': icd}
            )

            return True, "Hoàn tất phiên khám thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi hoàn tất phiên khám: {str(e)}"

    @staticmethod
    def save_examination(patient_id, doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date=None, lab_service_ids=None, medicines=None, images=None, audit_user=None):
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

            # 0. Kiểm tra tồn kho trước khi kê đơn thuốc
            validated_medicines = []
            if medicines and len(medicines) > 0:
                for m in medicines:
                    thuoc_id = m.get('thuoc_id')
                    so_luong = int(m.get('so_luong', 1))
                    cursor.execute('SELECT id, ten_thuoc, so_luong_ton, don_vi_tinh, don_gia, ton_kho_toi_thieu FROM thuoc WHERE id = ?', (thuoc_id,))
                    th_row = cursor.fetchone()
                    if not th_row:
                        conn.close()
                        return False, f"Thuốc ID {thuoc_id} không tồn tại trong kho dược!"
                    if so_luong > th_row['so_luong_ton']:
                        conn.close()
                        return False, f"Thuốc '{th_row['ten_thuoc']}' chỉ còn tồn {th_row['so_luong_ton']} {th_row['don_vi_tinh']}, không đủ số lượng kê ({so_luong})!"
                    validated_medicines.append({
                        'thuoc_id': thuoc_id,
                        'ten_thuoc': th_row['ten_thuoc'],
                        'so_luong': so_luong,
                        'don_gia': float(th_row['don_gia']),
                        'don_vi_tinh': th_row['don_vi_tinh'],
                        'lieu_dung': m.get('lieu_dung', 'Uống 1 viên/lần, ngày 2 lần'),
                        'cach_dung': m.get('cach_dung', 'Uống sau bữa ăn no 30 phút')
                    })

            # 1. Tạo phiếu khám bệnh (Nếu có CLS thì để 'Chờ kết quả CLS', không có thì 'Hoàn thành')
            has_cls = bool(lab_service_ids and len(lab_service_ids) > 0)
            initial_pk_status = 'Chờ kết quả CLS' if has_cls else 'Hoàn thành'
            appt_status = 'Chờ kết quả CLS' if has_cls else 'Đã khám'

            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_kham')
            pk_id = cursor.fetchone()['next_id']
            ma_phieu = f"PK2609{str(pk_id).zfill(3)}"

            import json
            images_json = json.dumps(images, ensure_ascii=False) if isinstance(images, list) else (str(images) if images else None)
            cursor.execute('''
                INSERT INTO phieu_kham (ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, hinh_anh_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ma_phieu, patient_id, valid_doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date, images_json, initial_pk_status))
            phieu_kham_id = cursor.lastrowid

            # Cập nhật lịch hẹn tương ứng
            cursor.execute('''
                UPDATE TOP (1) lich_hen
                SET trang_thai = ?
                WHERE benh_nhan_id = ? 
                  AND trang_thai IN (N'Đã tiếp nhận', N'Đang khám', N'Chờ tiếp nhận', N'Chờ kết quả CLS')
            ''', (appt_status, patient_id))

            cursor.execute('SELECT bhyt FROM benh_nhan WHERE id = ?', (patient_id,))
            p_check = cursor.fetchone()
            has_bhyt = bool(p_check and p_check.get('bhyt') and str(p_check.get('bhyt')).strip())

            # Khoản thu ban đầu: Tiền khám bệnh chuyên khoa (BHYT chi trả 80% nếu có BHYT)
            tong_tien_kham = 150000.0
            tien_bhyt = 120000.0 if has_bhyt else 0.0
            invoice_items = [
                ('Khám bệnh', 'Khám Chuyên Khoa Ngoại Trú', phieu_kham_id, 1, 150000.0, 150000.0)
            ]

            # 2. Tạo chỉ định cận lâm sàng nếu có (Trạng thái: 'Chờ thực hiện' để KTV thực hiện)
            if lab_service_ids and len(lab_service_ids) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, ?)
                ''', (ma_cd, phieu_kham_id, valid_doctor_id, 'Chờ thực hiện'))
                chi_dinh_id = cursor.lastrowid

                assigned_lab_names = []
                for s_id in lab_service_ids:
                    cursor.execute('SELECT ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt FROM dich_vu WHERE id = ?', (s_id,))
                    dv_row = cursor.fetchone()
                    if dv_row:
                        assigned_lab_names.append(dv_row['ten_dich_vu'])
                        dg = float(dv_row['don_gia'])
                        bh_pt = (float(dv_row['bhyt_chi_tra_pt']) / 100.0) if has_bhyt else 0.0
                        tong_tien_kham += dg
                        tien_bhyt += dg * bh_pt
                        invoice_items.append((dv_row['loai_dich_vu'] or 'Cận lâm sàng', dv_row['ten_dich_vu'], s_id, 1, dg, dg))

                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, NULL, ?)
                    ''', (chi_dinh_id, s_id, 'Chờ thực hiện'))

                # Gửi thông báo chuyển cận lâm sàng cho bệnh nhân
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_cls_row = cursor.fetchone()
                if bn_cls_row and bn_cls_row.get('tai_khoan_id'):
                    now_cls_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Chỉ định Cận lâm sàng', '/patient/lab-results', 0, ?)
                    ''', (
                        bn_cls_row['tai_khoan_id'],
                        f"Hoàn tất khám lâm sàng và Chuyển Cận lâm sàng: {ma_cd}",
                        f"Bác sĩ đã hoàn tất khám lâm sàng và chỉ định thực hiện Cận lâm sàng ({ma_cd}) gồm: {', '.join(assigned_lab_names)}. Vui lòng di chuyển đến Khu Cận lâm sàng để kỹ thuật viên thực hiện xét nghiệm/chẩn đoán hình ảnh.",
                        now_cls_str
                    ))

            # 3. Tạo đơn thuốc nếu có: Trạng thái ban đầu 'Chờ bệnh nhân xác nhận mua'
            # (Bệnh nhân có quyền chọn Mua tại bệnh viện hoặc Tự mua ngoài)
            if validated_medicines:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai, hinh_thuc_mua)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ma_dt, phieu_kham_id, valid_doctor_id, advice, 'Chờ bệnh nhân xác nhận mua', 'Chưa chọn'))
                don_thuoc_id = cursor.lastrowid

                for vm in validated_medicines:
                    cursor.execute('''
                        INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (don_thuoc_id, vm['thuoc_id'], vm['so_luong'], vm['lieu_dung'], vm['cach_dung']))

            # 4. Tự động sinh hóa đơn viện phí ban đầu (Tiền khám + Tiền Cận lâm sàng nếu có)
            # Tiền thuốc sẽ sinh hóa đơn riêng khi bệnh nhân chọn 'Mua tại bệnh viện'
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
            hd_next = cursor.fetchone()['next_id']
            ma_hd = f"HD2609{str(hd_next).zfill(3)}"
            thanh_tien = max(0.0, tong_tien_kham - tien_bhyt)

            cursor.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien, 'Chưa thanh toán'))
            hoa_don_id = cursor.lastrowid

            # Lưu từng dòng chi tiết hóa đơn
            for l_khoan, ten_khoan, tham_chieu, sl, dg, tt in invoice_items:
                cursor.execute('''
                    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (hoa_don_id, l_khoan, ten_khoan, tham_chieu, sl, dg, tt))

            # 5. Gửi các thông báo in-app cho tài khoản bệnh nhân
            cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
            bn_row = cursor.fetchone()
            if bn_row and bn_row.get('tai_khoan_id'):
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                p_uid = bn_row['tai_khoan_id']

                # Chỉ gửi thông báo hoàn tất khám nếu KHÔNG có chỉ định CLS (nếu có CLS thì đã gửi thông báo đi làm CLS ở trên)
                if not has_cls:
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, 'Khám bệnh', '/patient/records', 0, ?)
                    ''', (
                        p_uid,
                        f"Hoàn thành khám bệnh: {ma_phieu}",
                        f"Bác sĩ đã hoàn tất phiên khám cho bạn (Chẩn đoán: {icd}). Vui lòng kiểm tra hồ sơ bệnh án và hướng điều trị.",
                        now_str
                    ))

                # Thông báo có đơn thuốc kê (nếu có đơn thuốc)
                if validated_medicines:
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, 'Đơn thuốc', '/patient/prescriptions', 0, ?)
                    ''', (
                        p_uid,
                        f"Bác sĩ đã kê đơn thuốc mới: {ma_dt}",
                        f"Đơn thuốc điều trị gồm {len(validated_medicines)} loại thuốc đã được tạo. Bạn có thể chọn Mua tại bệnh viện hoặc Tự mua ngoài.",
                        now_str
                    ))

                # Thông báo thanh toán viện phí
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, 'Thanh toán', '/patient/invoices', 0, ?)
                ''', (
                    p_uid,
                    f"Thông báo thanh toán viện phí: {ma_hd}",
                    f"Hóa đơn viện phí khám bệnh của bạn đã được khởi tạo. Số tiền cần thanh toán: {int(thanh_tien):,} VNĐ. Vui lòng thanh toán tại Quầy hoặc qua cổng trực tuyến.",
                    now_str
                ))

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

