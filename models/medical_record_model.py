from datetime import datetime
from core.scheduling import scheduling_db as get_db, serialized, CalendarError, integer
from core.emr_workflow import resolve, ensure_results_ready, validated_medicines as validate_medicines
from core.clinical_data import clinical_value, published_results
from core.medical_media import protected_image_value
from core.audit import AuditLogger
from core.billing_policy import consultation_price, exam_insurance_percent, money
from decimal import Decimal, ROUND_HALF_UP

def normalize_reexam_date(reexam_date):
    """Chuẩn hóa ngày tái khám sang chuỗi YYYY-MM-DD hoặc None nếu rỗng/không hợp lệ."""
    if not reexam_date:
        return None
    s = str(reexam_date).strip()
    if not s or s.lower() in ['none', 'null', '']:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(s[:10], fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

class MedicalRecordModel:
    """Model quản lý hồ sơ bệnh án điện tử EMR, phiếu khám, chỉ định CLS và đơn thuốc."""

    @staticmethod
    @serialized
    def save_step(patient_id, doctor_id=None, room_id=None, symptoms=None, icd=None, step=1,
                  di_ung=None, tien_su_benh=None, appointment_id=None, record_id=None,
                  walk_in=False, encounter_key=None, audit_user=None):
        cursor = get_db().cursor()
        step = integer(step)
        if step not in (1, 2, 3, 4):
            raise CalendarError('Bước khám không hợp lệ.')
        record, appointment, patient_id, doctor_id, room_id, code = resolve(
            cursor, patient_id, doctor_id, room_id, appointment_id, record_id, walk_in, encounter_key, audit_user)
        if record and step == 4:
            ensure_results_ready(cursor, record['id'])
        state = (record['trang_thai'] if record and record['trang_thai'] in ('Chờ kết quả CLS', 'Chờ kết luận')
                 else ('Đang kê đơn' if step == 4 else 'Đang khám'))
        if not record:
            if not code:
                cursor.execute('SELECT COALESCE(MAX(id),0)+1 AS next_id FROM phieu_kham')
                code = 'PK2609' + str(cursor.fetchone()['next_id']).zfill(3)
            cursor.execute('''INSERT INTO phieu_kham(ma_phieu,benh_nhan_id,bac_si_id,phong_kham_id,lich_hen_id,
                trieu_chung,chan_doan_so_bo,chan_doan_icd,trang_thai) VALUES(?,?,?,?,?,?,?,?,?)''',
                (code, patient_id, doctor_id, room_id, appointment['id'] if appointment else None, symptoms, icd, icd, state))
            identifier = cursor.lastrowid
        else:
            identifier, code = record['id'], record['ma_phieu']
            cursor.execute('''UPDATE phieu_kham SET trieu_chung=COALESCE(?,trieu_chung),
                chan_doan_so_bo=COALESCE(?,chan_doan_so_bo),chan_doan_icd=COALESCE(?,chan_doan_icd),trang_thai=? WHERE id=?''',
                (symptoms, icd, icd, state, identifier))
        if di_ung is not None or tien_su_benh is not None:
            cursor.execute('UPDATE benh_nhan SET di_ung=COALESCE(?,di_ung),tien_su_benh=COALESCE(?,tien_su_benh) WHERE id=?',
                           (di_ung, tien_su_benh, patient_id))
        if appointment:
            cursor.execute('UPDATE lich_hen SET trang_thai=? WHERE id=?',
                           ('Chờ kết quả CLS' if state == 'Chờ kết quả CLS' else 'Đang khám', appointment['id']))
        return True, {'record_id': identifier, 'ma_phieu': code, 'step': step}

    @staticmethod
    def get_all_lab_orders():
        """Lấy toàn bộ danh sách phiếu chỉ định cận lâm sàng kèm chi tiết từng dịch vụ."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                cd.id, cd.ma_chi_dinh, cd.thoi_gian_chi_dinh, cd.trang_thai AS trang_thai_phieu, cd.ghi_chu,
                bn.id AS patient_id, bn.ma_benh_nhan, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan, bn.sdt AS sdt_benh_nhan,
                COALESCE(nv.ho_ten, N'Bác sĩ trực') AS bac_si,
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
        for item in orders:
            item['ket_qua'] = clinical_value(item.get('ket_qua'))
            item['file_ket_qua'] = protected_image_value(item.get('file_ket_qua'))
        return orders

    @staticmethod
    def get_lab_orders_by_patient(patient_id, approved_only=True):
        """Lấy danh sách kết quả xét nghiệm của bệnh nhân (bệnh nhân chỉ xem kết quả đã duyệt)."""
        all_orders = MedicalRecordModel.get_all_lab_orders()
        patient_orders = [o for o in all_orders if o.get('patient_id') == patient_id]
        if approved_only:
            # Bệnh nhân chỉ xem các dịch vụ đã duyệt
            return published_results(patient_orders)
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
        if row:
            item = dict(row)
            item['ket_qua'] = clinical_value(item.get('ket_qua'))
            item['file_ket_qua'] = protected_image_value(item.get('file_ket_qua'))
            return item
        return None

    @staticmethod
    @serialized
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
    @serialized
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
                        VALUES (?, ?, ?, N'Kết quả xét nghiệm', '/patient/dashboard', 0, ?)
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
                COALESCE(nv.ho_ten, N'Bác sĩ trực') AS bac_si,
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
        """Lấy thông tin chi tiết một phiếu khám bệnh EMR theo ID hoặc mã phiếu."""
        if not record_id:
            return None
        conn = get_db()
        cursor = conn.cursor()
        if str(record_id).isdigit():
            cursor.execute('''
                SELECT pk.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                       nv.ho_ten AS ten_bac_si, p.ten_phong
                FROM phieu_kham pk
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
                WHERE pk.id = ? OR pk.ma_phieu = ?
            ''', (int(record_id), str(record_id)))
        else:
            cursor.execute('''
                SELECT pk.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                       nv.ho_ten AS ten_bac_si, p.ten_phong
                FROM phieu_kham pk
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
                WHERE pk.ma_phieu = ?
            ''', (str(record_id),))
        row = cursor.fetchone()
        conn.close()
        if row:
            record = dict(row)
            record['hinh_anh_kham'] = protected_image_value(record.get('hinh_anh_kham'))
            return record
        return None

    @staticmethod
    @serialized
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
            ''', (diagnosis, icd, treatment, advice, normalize_reexam_date(reexam_date), record_id))

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
    @serialized
    def finish_examination(record_id, diagnosis, icd, treatment, advice, reexam_date=None, medicines=None, images=None, audit_user=None):
        """Bác sĩ kết luận chẩn đoán xác định, kê đơn thuốc và hoàn tất phiên khám sau khi có kết quả CLS."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            old_rec = MedicalRecordModel.get_examination_by_id(record_id)
            if not old_rec:
                return False, 'Không tìm thấy phiếu khám.'
            record, appointment, patient, doctor, room, code = resolve(cursor,old_rec['benh_nhan_id'],
                record_id=old_rec['id'],audit_user=audit_user)
            record_id = record['id']
            if not str(diagnosis or '').strip():
                raise CalendarError('Vui lòng ghi nhận chẩn đoán.')
            ensure_results_ready(cursor,record_id)
            medicines = validate_medicines(cursor,[] if medicines is None else medicines)
            cursor.execute("SELECT id FROM hoa_don WHERE phieu_kham_id=? AND trang_thai != ? AND ma_hoa_don NOT LIKE 'HDT%'",(record_id,'Đã hủy'))
            bills = cursor.fetchall()
            if not bills:
                return MedicalRecordModel.save_examination(patient,doctor,room,record.get('ly_do_kham'),
                    record.get('trieu_chung'),diagnosis,icd,treatment,advice,reexam_date,
                    medicines=medicines,images=images,audit_user=audit_user,record_id=record_id)
            if len(bills) != 1:
                raise CalendarError('Hóa đơn phiếu khám không duy nhất; cần kiểm tra dữ liệu.')
            cursor.execute('SELECT id FROM don_thuoc WHERE phieu_kham_id=?',(record_id,))
            if cursor.fetchone() and medicines:
                raise CalendarError('Phiếu đã có đơn thuốc; không tạo thêm đơn khi hoàn tất.')
            # 1. Cập nhật phiếu khám sang Hoàn thành
            import json
            images_json = json.dumps(images, ensure_ascii=False) if isinstance(images, list) else (str(images) if images else None)
            cursor.execute('''
                UPDATE phieu_kham
                SET chan_doan_so_bo = ?, chan_doan_icd = ?, huong_dieu_tri = ?, loi_dan = ?, ngay_tai_kham = ?,
                    hinh_anh_kham = COALESCE(?, hinh_anh_kham), trang_thai = N'Hoàn thành'
                WHERE id = ?
            ''', (diagnosis, icd, treatment, advice, normalize_reexam_date(reexam_date), images_json, record_id))

            # 2. Cập nhật lịch hẹn sang Đã khám
            if appointment:
                cursor.execute('UPDATE lich_hen SET trang_thai=? WHERE id=?',('Đã khám',appointment['id']))

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
                        VALUES (?, ?, ?, N'Khám bệnh', '/patient/records', 0, ?)
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
    @serialized
    def save_examination(patient_id, doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date=None, lab_service_ids=None, medicines=None, images=None, audit_user=None, appointment_id=None, record_id=None, walk_in=False, encounter_key=None):
        """Lưu toàn bộ phiên khám EMR (Phiếu khám, chỉ định CLS, đơn thuốc và hóa đơn viện phí)."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            ok, draft = MedicalRecordModel.save_step(patient_id,doctor_id,room_id,symptoms,icd,
                appointment_id=appointment_id,record_id=record_id,walk_in=walk_in,
                encounter_key=encounter_key,audit_user=audit_user)
            if not ok:
                return False, draft
            phieu_kham_id, ma_phieu = draft['record_id'], draft['ma_phieu']
            cursor.execute('SELECT * FROM phieu_kham WHERE id=?',(phieu_kham_id,))
            record = cursor.fetchone()
            valid_doctor_id,room_id,patient_id = record['bac_si_id'],record['phong_kham_id'],record['benh_nhan_id']
            for table in ('hoa_don','don_thuoc','phieu_chi_dinh'):
                cursor.execute('SELECT id FROM '+table+' WHERE phieu_kham_id=?',(phieu_kham_id,))
                if cursor.fetchone():
                    raise CalendarError('Phiếu đã lưu chỉ định/đơn/hóa đơn; dùng hoàn tất sau CLS, không lưu lại.')
            if not str(diagnosis or '').strip():
                raise CalendarError('Vui lòng ghi nhận chẩn đoán.')
            validated_medicines = validate_medicines(cursor, [] if medicines is None else medicines)
            if lab_service_ids is not None and not isinstance(lab_service_ids, list):
                raise CalendarError('Danh sách chỉ định CLS không hợp lệ.')
            lab_service_ids = [integer(value) for value in (lab_service_ids or [])]
            if len(set(lab_service_ids)) != len(lab_service_ids):
                raise CalendarError('Chỉ định CLS bị trùng.')
            for identifier in lab_service_ids:
                cursor.execute('SELECT id FROM dich_vu WHERE id=?',(identifier,))
                if not cursor.fetchone():
                    raise CalendarError('Dịch vụ CLS không tồn tại.')

            # 1. Tạo phiếu khám bệnh (Nếu có CLS thì để 'Chờ kết quả CLS', không có thì 'Hoàn thành')
            has_cls = bool(lab_service_ids and len(lab_service_ids) > 0)
            initial_pk_status = 'Chờ kết quả CLS' if has_cls else 'Hoàn thành'
            appt_status = 'Chờ kết quả CLS' if has_cls else 'Đã khám'

            import json
            images_json = json.dumps(images,ensure_ascii=False) if images else None
            cursor.execute("""UPDATE phieu_kham SET ly_do_kham=?,trieu_chung=?,chan_doan_so_bo=?,chan_doan_icd=?,
                huong_dieu_tri=?,loi_dan=?,ngay_tai_kham=?,hinh_anh_kham=COALESCE(?,hinh_anh_kham),trang_thai=? WHERE id=?""",
                (reason,symptoms,diagnosis,icd,treatment,advice,normalize_reexam_date(reexam_date),images_json,initial_pk_status,phieu_kham_id))
            if record.get('lich_hen_id'):
                cursor.execute('UPDATE lich_hen SET trang_thai=? WHERE id=?',(appt_status,record['lich_hen_id']))

            cursor.execute('SELECT bhyt FROM benh_nhan WHERE id = ?', (patient_id,))
            p_check = cursor.fetchone()
            has_bhyt = bool(p_check and p_check.get('bhyt') and str(p_check.get('bhyt')).strip())

            # Khoản thu ban đầu: Tiền khám bệnh chuyên khoa (BHYT chi trả 80% nếu có BHYT)
            tong_tien_kham = consultation_price(cursor, valid_doctor_id)
            tien_bhyt = (tong_tien_kham * exam_insurance_percent()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if has_bhyt else Decimal(0)
            invoice_items = [
                ('Khám bệnh', 'Khám Chuyên Khoa Ngoại Trú', phieu_kham_id, 1, tong_tien_kham, tong_tien_kham)
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
                        dg = money(dv_row['don_gia'])
                        bh_percent = money(dv_row['bhyt_chi_tra_pt'])
                        if bh_percent > 100:
                            raise CalendarError('Ty le BHYT dich vu khong hop le.')
                        bh_pt = bh_percent / Decimal(100) if has_bhyt else Decimal(0)
                        tong_tien_kham += dg
                        tien_bhyt += (dg * bh_pt).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
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
            thanh_tien = tong_tien_kham - tien_bhyt

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
                        VALUES (?, ?, ?, N'Khám bệnh', '/patient/records', 0, ?)
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
                        VALUES (?, ?, ?, N'Đơn thuốc', '/patient/prescriptions', 0, ?)
                    ''', (
                        p_uid,
                        f"Bác sĩ đã kê đơn thuốc mới: {ma_dt}",
                        f"Đơn thuốc điều trị gồm {len(validated_medicines)} loại thuốc đã được tạo. Bạn có thể chọn Mua tại bệnh viện hoặc Tự mua ngoài.",
                        now_str
                    ))

                # Thông báo thanh toán viện phí
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, N'Thanh toán', '/patient/invoices', 0, ?)
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

