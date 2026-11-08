from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from core.scheduling import scheduling_db as get_db, serialized, CalendarError, integer, clock, sync_count
from core.emr_workflow import resolve, ensure_results_ready, validated_medicines as validate_medicines
from core.clinical_data import clinical_value, published_results
from core.medical_media import protected_image_value
from core.audit import AuditLogger
from core.billing_policy import consultation_price, invoice_totals, money

CLINICAL_DIRECT_SERVICE_TYPES = ('Khám bệnh', 'Khám chuyên khoa', 'Thủ thuật')


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
    def get_all_lab_orders(page=None, limit=None, search=None, status=None):
        """Lấy danh sách phiếu chỉ định cận lâm sàng kèm phân trang T-SQL OFFSET FETCH."""
        conn = get_db()
        cursor = conn.cursor()

        where_extra = []
        params = []
        if status and str(status).strip():
            where_extra.append("ct.trang_thai = ?")
            params.append(str(status).strip())
        if search and str(search).strip():
            q = f"%{str(search).strip()}%"
            where_extra.append("(cd.ma_chi_dinh LIKE ? OR bn.ho_ten LIKE ? OR bn.ma_benh_nhan LIKE ? OR dv.ten_dich_vu LIKE ?)")
            params.extend([q, q, q, q])

        where_sql = ("AND " + " AND ".join(where_extra)) if where_extra else ""

        pagination_sql = ""
        if page is not None and limit is not None:
            p = max(1, int(page))
            lim = max(1, int(limit))
            offset = (p - 1) * lim
            pagination_sql = f"OFFSET {offset} ROWS FETCH NEXT {lim} ROWS ONLY"

        query = f'''
            SELECT 
                cd.id, cd.ma_chi_dinh, cd.thoi_gian_chi_dinh, cd.trang_thai AS trang_thai_phieu, cd.ghi_chu,
                bn.id AS patient_id, bn.ma_benh_nhan, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan, bn.sdt AS sdt_benh_nhan,
                COALESCE(nv.ho_ten, N'Bác sĩ trực') AS bac_si,
                dv.id AS dich_vu_id, dv.ten_dich_vu AS dich_vu, dv.loai_dich_vu AS loai, dv.don_gia,
                ct.id AS chi_tiet_id, ct.ket_qua, ct.file_ket_qua, ct.ktv_thuc_hien, ct.thoi_gian_thuc_hien,
                ct.trang_thai, ct.bac_si_duyet, ct.thoi_gian_duyet, ct.ghi_chu_duyet,
                ct.is_panic, ct.gia_tri_do, ct.ktv_duoc_chon_id, ct.phong_ktv_id, ct.ly_do_lam_lai,
                dv.chi_so_binh_thuong, dv.nguong_binh_thuong_min, dv.nguong_binh_thuong_max,
                dv.nguong_nguy_kich_min, dv.nguong_nguy_kich_max, dv.don_vi_do,
                pk_ktv.ten_phong AS ten_phong_ktv, nv_ktv.ho_ten AS ten_ktv_duoc_chon,
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
            LEFT JOIN phong_kham pk_ktv ON ct.phong_ktv_id = pk_ktv.id
            LEFT JOIN nhan_vien nv_ktv ON ct.ktv_duoc_chon_id = nv_ktv.id
            WHERE ct.id IS NOT NULL {where_sql}
            ORDER BY cd.id DESC, ct.id ASC
            {pagination_sql}
        '''
        cursor.execute(query, params)
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
            return published_results(patient_orders)
        return patient_orders

    @staticmethod
    def get_lab_order_detail(order_id_or_code):
        """Lấy chi tiết phiếu chỉ định cận lâm sàng và toàn bộ dịch vụ đi kèm."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            oid_int = int(order_id_or_code)
        except (ValueError, TypeError):
            oid_int = None

        if oid_int is not None:
            cursor.execute('''
                SELECT cd.*, pk.ma_phieu, pk.trieu_chung, pk.chan_doan_so_bo, pk.chan_doan_icd,
                       bn.id AS benh_nhan_id, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan,
                       bn.gioi_tinh, bn.ngay_sinh, bn.sdt AS sdt_benh_nhan, bn.dia_chi, bn.bhyt AS so_bhyt, bn.cccd,
                       COALESCE(nv.ho_ten, N'Bác sĩ chuyên khoa') AS ten_bac_si,
                       pk_room.ten_phong AS phong_kham_bs
                FROM phieu_chi_dinh cd
                JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON cd.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham pk_room ON pk.phong_kham_id = pk_room.id
                WHERE cd.id = ? OR cd.ma_chi_dinh = ?
            ''', (oid_int, str(order_id_or_code)))
        else:
            cursor.execute('''
                SELECT cd.*, pk.ma_phieu, pk.trieu_chung, pk.chan_doan_so_bo, pk.chan_doan_icd,
                       bn.id AS benh_nhan_id, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan,
                       bn.gioi_tinh, bn.ngay_sinh, bn.sdt AS sdt_benh_nhan, bn.dia_chi, bn.bhyt AS so_bhyt, bn.cccd,
                       COALESCE(nv.ho_ten, N'Bác sĩ chuyên khoa') AS ten_bac_si,
                       pk_room.ten_phong AS phong_kham_bs
                FROM phieu_chi_dinh cd
                JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON cd.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham pk_room ON pk.phong_kham_id = pk_room.id
                WHERE cd.ma_chi_dinh = ?
            ''', (str(order_id_or_code),))

        order = cursor.fetchone()
        if not order:
            conn.close()
            return None
        res = dict(order)
        cursor.execute('''
            SELECT ct.*, dv.ma_dich_vu, dv.ten_dich_vu, dv.loai_dich_vu, dv.don_gia, dv.chi_so_binh_thuong, dv.don_vi_do,
                   dv.nguong_binh_thuong_min, dv.nguong_binh_thuong_max, dv.nguong_nguy_kich_min, dv.nguong_nguy_kich_max,
                   pk_ktv.ten_phong AS ten_phong_ktv, nv_ktv.ho_ten AS ten_ktv_thuc_hien
            FROM chi_tiet_chi_dinh ct
            JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            LEFT JOIN phong_kham pk_ktv ON ct.phong_ktv_id = pk_ktv.id
            LEFT JOIN nhan_vien nv_ktv ON ct.ktv_duoc_chon_id = nv_ktv.id
            WHERE ct.phieu_chi_dinh_id = ?
            ORDER BY ct.id ASC
        ''', (res['id'],))
        res['items'] = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res

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
        """KTV cập nhật kết quả xét nghiệm. Đo ngưỡng nguy kịch, bôi đỏ và cảnh báo tức thì về EMR bác sĩ."""
        import re
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
            
            # Trích xuất giá trị số đo đạc để so khớp ngưỡng nguy kịch
            num_match = re.search(r'[-+]?\d+(?:\.\d+)?', str(ket_qua or ''))
            gia_tri_do = float(num_match.group(0)) if num_match else None
            
            # Lấy thông tin ngưỡng từ dịch vụ
            cursor.execute('''
                SELECT nguong_binh_thuong_min, nguong_binh_thuong_max,
                       nguong_nguy_kich_min, nguong_nguy_kich_max, don_vi_do
                FROM dich_vu WHERE id = ?
            ''', (item['dich_vu_id'],))
            dv_thresholds = cursor.fetchone()
            
            is_panic = 0
            if dv_thresholds and gia_tri_do is not None:
                nk_min = dv_thresholds.get('nguong_nguy_kich_min')
                nk_max = dv_thresholds.get('nguong_nguy_kich_max')
                if (nk_min is not None and gia_tri_do < float(nk_min)) or (nk_max is not None and gia_tri_do > float(nk_max)):
                    is_panic = 1
            
            cursor.execute('''
                UPDATE chi_tiet_chi_dinh
                SET ket_qua = ?, gia_tri_do = ?, is_panic = ?, file_ket_qua = COALESCE(?, file_ket_qua),
                    ktv_thuc_hien = ?, nguoi_nhap = ?, thoi_gian_thuc_hien = ?, trang_thai = ?
                WHERE id = ?
            ''', (ket_qua, gia_tri_do, is_panic, file_ket_qua, ktv_str, ktv_str, now_str, 'Chờ duyệt', chi_tiet_id))
            
            cursor.execute('''
                UPDATE phieu_chi_dinh SET trang_thai = ? WHERE id = ?
            ''', ('Đang thực hiện', item['phieu_chi_dinh_id']))
            
            # Nếu vượt ngưỡng nguy kịch (Panic Value), đẩy thông báo khẩn cấp tức thì về màn hình EMR của bác sĩ
            if is_panic == 1:
                cursor.execute('''
                    SELECT bs.id AS bac_si_id, nv.tai_khoan_id, nv.ho_ten AS ten_bac_si
                    FROM phieu_chi_dinh cd
                    JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
                    LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
                    LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                    WHERE cd.id = ?
                ''', (item['phieu_chi_dinh_id'],))
                doc_target = cursor.fetchone()
                if doc_target and doc_target.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'NguyKich', ?, 0, ?)
                    ''', (
                        doc_target['tai_khoan_id'],
                        f"[NGUY KỊCH] Cảnh báo kết quả xét nghiệm {item.get('ten_dich_vu')}",
                        f"Bệnh nhân {item.get('ten_benh_nhan')} có kết quả {item.get('ten_dich_vu')} = {ket_qua} vượt ngưỡng nguy kịch! KTV {ktv_str} đã cập nhật, đề nghị bác sĩ kiểm tra và xử trí khẩn cấp.",
                        f"/admin/emr?patient_id={item.get('patient_id')}",
                        now_str
                    ))
            
            # Kiểm tra xem toàn bộ các mục CLS trong phiếu đã hoàn thành chưa để cập nhật trạng thái phiếu khám
            cursor.execute('''
                SELECT COUNT(*) AS total_items,
                       SUM(CASE WHEN ket_qua IS NOT NULL AND RTRIM(LTRIM(ket_qua)) != '' THEN 1 ELSE 0 END) AS done_items
                FROM chi_tiet_chi_dinh
                WHERE phieu_chi_dinh_id = ?
            ''', (item['phieu_chi_dinh_id'],))
            prog = cursor.fetchone()
            if prog and prog['total_items'] == prog['done_items']:
                cursor.execute("UPDATE phieu_chi_dinh SET trang_thai = N'Chờ duyệt' WHERE id = ?", (item['phieu_chi_dinh_id'],))
                cursor.execute('''
                    UPDATE phieu_kham
                    SET ktv_hoan_thanh = 1, buoc_hien_tai = 3, trang_thai = N'Đã có kết quả CLS'
                    WHERE id = (SELECT phieu_kham_id FROM phieu_chi_dinh WHERE id = ?)
                ''', (item['phieu_chi_dinh_id'],))
            
            conn.commit()
            conn.close()
            AuditLogger.log(
                table_name='chi_tiet_chi_dinh',
                row_id=chi_tiet_id,
                action='UPDATE_LAB_RESULT',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=ktv_str,
                reason=f"Nhập kết quả xét nghiệm {item.get('ten_dich_vu')}{' [NGUY KỊCH]' if is_panic else ''}",
                before_data={'ket_qua': item.get('ket_qua'), 'trang_thai': item.get('trang_thai')},
                after_data={'ket_qua': ket_qua, 'gia_tri_do': gia_tri_do, 'is_panic': is_panic, 'trang_thai': 'Chờ duyệt', 'ktv': ktv_str}
            )
            panic_msg = " [CẢNH BÁO NGUY KỊCH: Đã kích hoạt chuông cảnh báo tới Bác sĩ điều trị]" if is_panic else ""
            return True, f"Cập nhật kết quả xét nghiệm thành công và đã chuyển sang trạng thái 'Chờ duyệt'!{panic_msg}"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi lưu kết quả: {str(e)}"

    @staticmethod
    @serialized
    def request_redo_lab_result(chi_tiet_id, reason=None, audit_user=None):
        """Bác sĩ yêu cầu kỹ thuật viên làm lại xét nghiệm hoặc chụp chiếu."""
        item = MedicalRecordModel.get_lab_item_by_id(chi_tiet_id)
        if not item:
            return False, "Không tìm thấy chỉ định xét nghiệm!"
        conn = get_db()
        cursor = conn.cursor()
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            doc_str = audit_user.get('ho_ten') if audit_user else 'Bác sĩ chuyên khoa'
            ly_do = reason or 'Bác sĩ yêu cầu đo đạc/chụp lại mẫu xét nghiệm do chưa đạt yêu cầu chuyên môn'
            cursor.execute('''
                UPDATE chi_tiet_chi_dinh
                SET trang_thai = N'Chờ thực hiện', ly_do_lam_lai = ?, ket_qua = NULL, file_ket_qua = NULL,
                    thoi_gian_duyet = NULL, bac_si_duyet = NULL, is_panic = 0
                WHERE id = ?
            ''', (ly_do, chi_tiet_id))
            cursor.execute("UPDATE phieu_chi_dinh SET trang_thai = N'Đang thực hiện' WHERE id = ?", (item['phieu_chi_dinh_id'],))
            
            # Cập nhật phiếu khám quay lại trạng thái chờ KTV
            cursor.execute('''
                UPDATE phieu_kham
                SET ktv_hoan_thanh = 0, buoc_hien_tai = 2, trang_thai = N'Chờ kết quả CLS'
                WHERE id = (SELECT phieu_kham_id FROM phieu_chi_dinh WHERE id = ?)
            ''', (item['phieu_chi_dinh_id'],))
            
            # Gửi thông báo đến tài khoản KTV phụ trách
            if item.get('ktv_duoc_chon_id'):
                cursor.execute('SELECT tai_khoan_id FROM nhan_vien WHERE id = ?', (item['ktv_duoc_chon_id'],))
                ktv_acc = cursor.fetchone()
                if ktv_acc and ktv_acc.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'YeuCauLamLai', '/admin/lab', 0, ?)
                    ''', (
                        ktv_acc['tai_khoan_id'],
                        f"Yêu cầu làm lại CLS: {item.get('ten_dich_vu')}",
                        f"Bác sĩ {doc_str} yêu cầu làm lại xét nghiệm {item.get('ten_dich_vu')} cho bệnh nhân {item.get('ten_benh_nhan')}. Lý do: {ly_do}",
                        now_str
                    ))
            conn.commit()
            conn.close()
            AuditLogger.log(
                table_name='chi_tiet_chi_dinh',
                row_id=chi_tiet_id,
                action='REQUEST_REDO_LAB',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=doc_str,
                reason=ly_do,
                before_data={'trang_thai': item.get('trang_thai')},
                after_data={'trang_thai': 'Chờ thực hiện', 'ly_do_lam_lai': ly_do}
            )
            return True, f"Đã gửi yêu cầu làm lại kết quả {item.get('ten_dich_vu')} tới Kỹ thuật viên!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi yêu cầu làm lại: {str(e)}"

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
            cursor.execute('''
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN trang_thai = ? THEN 1 ELSE 0 END) AS approved_count
                FROM chi_tiet_chi_dinh
                WHERE phieu_chi_dinh_id = ?
            ''', ('Đã duyệt', item['phieu_chi_dinh_id']))
            st = cursor.fetchone()
            if st and st['total'] == st['approved_count']:
                cursor.execute("UPDATE phieu_chi_dinh SET trang_thai = ? WHERE id = ?", ('Đã duyệt', item['phieu_chi_dinh_id']))
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
    def _unique_appointment_code(cursor):
        """Sinh mã lịch hẹn duy nhất không trùng lặp trong bảng lich_hen."""
        cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM lich_hen')
        seq = int(cursor.fetchone()['next_id'] or 1)
        while True:
            code = f"LH2609{str(seq).zfill(3)}"
            cursor.execute('SELECT 1 AS ok FROM lich_hen WHERE ma_lich_hen = ?', (code,))
            if not cursor.fetchone():
                return code
            seq += 1

    @staticmethod
    def _create_reexamination_appointment(cursor, patient_id, doctor_id, room_id, reexam_date, reexam_time='08:30', diagnosis=None, exclude_lich_hen_id=None):
        """Tạo bản ghi lịch hẹn tái khám mới hoàn toàn (không đè lịch cũ), duyệt sẵn và đồng bộ ca trực."""
        norm_date = normalize_reexam_date(reexam_date)
        if not norm_date or not doctor_id:
            return None
        from models.appointment_model import AppointmentModel
        norm_time = AppointmentModel.normalize_time(reexam_time) or '08:30'
        cursor.execute('''
            SELECT bs.id, bs.chuyen_khoa_id, bs.phong_kham_chinh_id, nv.ho_ten, nv.tai_khoan_id, ck.ten_khoa
            FROM bac_si bs
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE bs.id = ?
        ''', (doctor_id,))
        doc_info = cursor.fetchone()
        if not doc_info:
            return None
        chuyen_khoa_id = doc_info['chuyen_khoa_id']
        assigned_room = room_id or doc_info.get('phong_kham_chinh_id')
        params = [patient_id, doctor_id, norm_date]
        excl_sql = ''
        if exclude_lich_hen_id:
            excl_sql = ' AND id != ?'
            params.append(int(exclude_lich_hen_id))
        cursor.execute(f'''
            SELECT id, ma_lich_hen, gio_hen FROM lich_hen
            WHERE benh_nhan_id = ? AND bac_si_id = ? AND ngay_hen = ?
              AND (trang_thai IS NULL OR trang_thai NOT IN (N'Đã hủy', N'Đã khám', N'Hoàn thành')){excl_sql}
        ''', tuple(params))
        minutes = lambda v: clock(v).hour * 60 + clock(v).minute
        target_min = minutes(norm_time)
        for row in cursor.fetchall():
            try:
                if abs(minutes(row['gio_hen']) - target_min) < 30:
                    return row['ma_lich_hen']
            except CalendarError:
                pass
        shift_num = AppointmentModel.get_shift_from_time(norm_time)
        has_shift = None
        if shift_num:
            cursor.execute('''
                SELECT * FROM lich_lam_viec
                WHERE bac_si_id = ? AND ngay_lam = ? AND ca_lam = ? AND trang_thai = 1
            ''', (doctor_id, norm_date, shift_num))
            candidates = [dict(r) for r in cursor.fetchall()
                          if not r.get('trang_thai_duyet') or r.get('trang_thai_duyet') == 'DA_DUYET']
            if candidates:
                has_shift = candidates[0]
                if has_shift.get('phong_kham_id'):
                    assigned_room = has_shift['phong_kham_id']
        ma_lich_hen = MedicalRecordModel._unique_appointment_code(cursor)
        ly_do = f"[Bác sĩ hẹn mới] Tái khám: {diagnosis}" if diagnosis else "[Bác sĩ hẹn mới] Tái khám theo hẹn của bác sĩ"
        cursor.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, N'Đã duyệt')
        ''', (ma_lich_hen, patient_id, doctor_id, chuyen_khoa_id, assigned_room, norm_date, norm_time, ly_do))
        if has_shift:
            sync_count(cursor, has_shift)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (patient_id,))
        bn = cursor.fetchone()
        if bn and bn.get('tai_khoan_id'):
            cursor.execute('''
                INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                VALUES (?, ?, ?, N'Lịch tái khám', '/patient/appointments', 0, ?)
            ''', (
                bn['tai_khoan_id'],
                f"Lịch hẹn mới đã được duyệt sẵn: {ma_lich_hen}",
                f"Bác sĩ {doc_info['ho_ten']} đã hẹn lịch khám mới #{ma_lich_hen} cho bạn vào ngày {norm_date} lúc {norm_time} tại {doc_info['ten_khoa']}. Lịch đã được duyệt sẵn.",
                now_str
            ))
        if not has_shift and doc_info.get('tai_khoan_id'):
            cursor.execute('''
                INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                VALUES (?, ?, ?, N'Nhắc nhở ca trực', '/admin/staff', 0, ?)
            ''', (
                doc_info['tai_khoan_id'],
                "Nhắc nhở đăng ký ca làm việc",
                f"Bạn có lịch khám mới #{ma_lich_hen} cho bệnh nhân vào ngày {norm_date} lúc {norm_time} nhưng chưa đăng ký ca làm vào giờ đó, vui lòng đăng ký.",
                now_str
            ))
        return ma_lich_hen

    @staticmethod
    def update_examination(record_id, doctor_id, diagnosis, icd, treatment, advice, reexam_date=None, reason=None, audit_user=None, reexam_time=None):
        """Bác sĩ chỉnh sửa hồ sơ bệnh án EMR và tạo lịch hẹn tái khám mới riêng biệt nếu có."""
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
            if reexam_date:
                doc_to_assign = doctor_id or old_rec.get('bac_si_id')
                MedicalRecordModel._create_reexamination_appointment(
                    cursor=cursor,
                    patient_id=old_rec['benh_nhan_id'],
                    doctor_id=doc_to_assign,
                    room_id=old_rec.get('phong_kham_id'),
                    reexam_date=reexam_date,
                    reexam_time=reexam_time or '08:30',
                    diagnosis=diagnosis,
                    exclude_lich_hen_id=old_rec.get('lich_hen_id')
                )
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
    def finish_examination(record_id, diagnosis, icd, treatment, advice, reexam_date=None, medicines=None, images=None, audit_user=None, reexam_time=None):
        """Bác sĩ kết luận chẩn đoán xác định, kê đơn thuốc và hoàn tất phiên khám sau khi có kết quả CLS."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            old_rec = MedicalRecordModel.get_examination_by_id(record_id)
            if not old_rec:
                return False, 'Không tìm thấy phiếu khám.'
            record, appointment, patient, doctor, room, code = resolve(
                cursor, old_rec['benh_nhan_id'], record_id=old_rec['id'], audit_user=audit_user)
            record_id = record['id']
            if not str(diagnosis or '').strip():
                raise CalendarError('Vui lòng ghi nhận chẩn đoán.')
            ensure_results_ready(cursor, record_id)
            medicines = validate_medicines(cursor, [] if medicines is None else medicines)
            cursor.execute("SELECT id FROM hoa_don WHERE phieu_kham_id=? AND trang_thai != ? AND ma_hoa_don NOT LIKE 'HDT%'", (record_id, 'Đã hủy'))
            bills = cursor.fetchall()
            if not bills:
                return MedicalRecordModel.save_examination(
                    patient, doctor, room, record.get('ly_do_kham'),
                    record.get('trieu_chung'), diagnosis, icd, treatment, advice, reexam_date,
                    medicines=medicines, images=images, audit_user=audit_user,
                    reexam_time=reexam_time, record_id=record_id)
            if len(bills) != 1:
                raise CalendarError('Hóa đơn phiếu khám không duy nhất; cần kiểm tra dữ liệu.')
            cursor.execute('SELECT id FROM don_thuoc WHERE phieu_kham_id=?', (record_id,))
            if cursor.fetchone() and medicines:
                raise CalendarError('Phiếu đã có đơn thuốc; không tạo thêm đơn khi hoàn tất.')
            import json
            images_json = json.dumps(images, ensure_ascii=False) if isinstance(images, list) else (str(images) if images else None)
            cursor.execute('''
                UPDATE phieu_kham
                SET chan_doan_so_bo = ?, chan_doan_icd = ?, huong_dieu_tri = ?, loi_dan = ?, ngay_tai_kham = ?,
                    hinh_anh_kham = COALESCE(?, hinh_anh_kham), trang_thai = N'Hoàn thành'
                WHERE id = ?
            ''', (diagnosis, icd, treatment, advice, normalize_reexam_date(reexam_date), images_json, record_id))
            if appointment:
                cursor.execute('UPDATE lich_hen SET trang_thai=? WHERE id=?', ('Đã khám', appointment['id']))
            if reexam_date:
                MedicalRecordModel._create_reexamination_appointment(
                    cursor=cursor,
                    patient_id=old_rec['benh_nhan_id'],
                    doctor_id=old_rec.get('bac_si_id'),
                    room_id=old_rec.get('phong_kham_id'),
                    reexam_date=reexam_date,
                    reexam_time=reexam_time or '08:30',
                    diagnosis=diagnosis,
                    exclude_lich_hen_id=appointment['id'] if appointment else old_rec.get('lich_hen_id')
                )
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
    def save_examination(patient_id, doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date=None, lab_service_ids=None, medicines=None, images=None, audit_user=None, reexam_time=None, appointment_id=None, record_id=None, walk_in=False, encounter_key=None):
        """Lưu toàn bộ phiên khám EMR (Phiếu khám, khám chuyên ngành/chỉ định CLS, đơn thuốc và hóa đơn viện phí)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            if appointment_id is None and not walk_in:
                walk_in = True
            if walk_in and not encounter_key:
                import uuid
                encounter_key = str(uuid.uuid4())
            ok, draft = MedicalRecordModel.save_step(
                patient_id, doctor_id, room_id, symptoms, icd,
                appointment_id=appointment_id, record_id=record_id, walk_in=walk_in,
                encounter_key=encounter_key, audit_user=audit_user)
            if not ok:
                return False, draft
            phieu_kham_id, ma_phieu = draft['record_id'], draft['ma_phieu']
            cursor.execute('SELECT * FROM phieu_kham WHERE id=?', (phieu_kham_id,))
            record = cursor.fetchone()
            valid_doctor_id, room_id, patient_id = record['bac_si_id'], record['phong_kham_id'], record['benh_nhan_id']
            for table in ('hoa_don', 'don_thuoc', 'phieu_chi_dinh'):
                cursor.execute('SELECT id FROM ' + table + ' WHERE phieu_kham_id=?', (phieu_kham_id,))
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

            selected_services = []
            cursor.execute('SELECT chuyen_khoa_id FROM bac_si WHERE id=?', (valid_doctor_id,))
            service_department = cursor.fetchone()['chuyen_khoa_id']
            for identifier in lab_service_ids:
                cursor.execute('SELECT id, chuyen_khoa_id, ten_dich_vu, loai_dich_vu, don_gia FROM dich_vu WHERE id=? AND trang_thai=1', (identifier,))
                dv_row = cursor.fetchone()
                if not dv_row:
                    raise CalendarError('Dịch vụ CLS không tồn tại.')
                if dv_row['loai_dich_vu'] in CLINICAL_DIRECT_SERVICE_TYPES and dv_row['chuyen_khoa_id'] not in (None, service_department):
                    raise CalendarError('Dịch vụ khám/thủ thuật không thuộc khoa đang khám. Vui lòng chuyển đến khoa phù hợp.')
                selected_services.append(dict(dv_row))

            has_cls = any(s['loai_dich_vu'] not in CLINICAL_DIRECT_SERVICE_TYPES for s in selected_services)
            initial_pk_status = 'Chờ kết quả CLS' if has_cls else 'Hoàn thành'
            appt_status = 'Chờ kết quả CLS' if has_cls else 'Đã khám'

            import json
            images_json = json.dumps(images, ensure_ascii=False) if images else record.get('hinh_anh_kham')
            cursor.execute("""UPDATE phieu_kham SET ly_do_kham=?,trieu_chung=?,chan_doan_so_bo=?,chan_doan_icd=?,
                huong_dieu_tri=?,loi_dan=?,ngay_tai_kham=?,hinh_anh_kham=?,trang_thai=? WHERE id=?""",
                (reason, symptoms, diagnosis, icd, treatment, advice, normalize_reexam_date(reexam_date), images_json, initial_pk_status, phieu_kham_id))
            if record.get('lich_hen_id'):
                cursor.execute('UPDATE lich_hen SET trang_thai=? WHERE id=?', (appt_status, record['lich_hen_id']))
            if reexam_date and valid_doctor_id:
                MedicalRecordModel._create_reexamination_appointment(
                    cursor=cursor,
                    patient_id=patient_id,
                    doctor_id=valid_doctor_id,
                    room_id=room_id,
                    reexam_date=reexam_date,
                    reexam_time=reexam_time or '08:30',
                    diagnosis=diagnosis,
                    exclude_lich_hen_id=record.get('lich_hen_id')
                )
            cursor.execute('SELECT bhyt FROM benh_nhan WHERE id = ?', (patient_id,))
            p_check = cursor.fetchone()
            has_bhyt = bool(p_check and p_check.get('bhyt') and str(p_check.get('bhyt')).strip())

            from core.exam_services import visit_exam
            primary_exam = visit_exam(cursor, phieu_kham_id, valid_doctor_id)
            if primary_exam and primary_exam['id'] in lab_service_ids:
                raise CalendarError('Dịch vụ khám chính đã có trong lịch hẹn; không được tính phí hai lần.')
            tong_tien_kham = money(primary_exam['don_gia']) if primary_exam else consultation_price(cursor, valid_doctor_id)
            tien_bhyt = Decimal(0)
            exam_label = primary_exam['ten_dich_vu'] if primary_exam else 'Khám Chuyên Khoa Ngoại Trú'
            exam_label = exam_label[:230] + (' [Có BHYT]' if has_bhyt else ' [Không BHYT]')
            invoice_items = [
                ('Khám bệnh', exam_label, phieu_kham_id, 1, tong_tien_kham, tong_tien_kham)
            ]

            if selected_services:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"
                cd_status = 'Chờ thực hiện' if has_cls else 'Đã duyệt'
                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, ?)
                ''', (ma_cd, phieu_kham_id, valid_doctor_id, cd_status))
                chi_dinh_id = cursor.lastrowid
                now_exec_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                doc_name = audit_user.get('ho_ten') if audit_user else 'Bác sĩ chuyên khoa'
                assigned_cls_names = []

                for dv_row in selected_services:
                    s_id = dv_row['id']
                    dg = money(dv_row['don_gia'])
                    tong_tien_kham += dg
                    raw_loai = dv_row.get('loai_dich_vu') or 'Cận lâm sàng'
                    item_kind = raw_loai if raw_loai != 'Khám bệnh' else 'Khám chuyên khoa'
                    invoice_items.append((item_kind, dv_row['ten_dich_vu'], s_id, 1, dg, dg))

                    assigned_cls_names.append(dv_row['ten_dich_vu'])
                    is_direct = dv_row['loai_dich_vu'] in CLINICAL_DIRECT_SERVICE_TYPES
                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, ?, ?)
                    ''', (chi_dinh_id, s_id, 'Đã thực hiện tại phòng khám' if is_direct else None, 'Đã duyệt' if is_direct else 'Chờ thực hiện'))

                if has_cls:
                    cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                    bn_cls_row = cursor.fetchone()
                    p_name = bn_cls_row['ho_ten'] if bn_cls_row else 'Bệnh nhân'
                    if bn_cls_row and bn_cls_row.get('tai_khoan_id'):
                        cursor.execute('''
                            INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                            VALUES (?, ?, ?, N'Chỉ định Cận lâm sàng', '/patient/lab-results', 0, ?)
                        ''', (
                            bn_cls_row['tai_khoan_id'],
                            f"Hoàn tất khám lâm sàng và Chuyển Cận lâm sàng: {ma_cd}",
                            f"Bác sĩ đã hoàn tất khám lâm sàng và chỉ định thực hiện Cận lâm sàng ({ma_cd}) gồm: {', '.join(assigned_cls_names)}. Vui lòng di chuyển đến Khu Cận lâm sàng để kỹ thuật viên thực hiện xét nghiệm/chẩn đoán hình ảnh.",
                            now_exec_str
                        ))
                    from models.notification_model import NotificationModel
                    NotificationModel.notify_role(
                        'KTV',
                        tieu_de=f"Chỉ định Cận lâm sàng mới: {ma_cd}",
                        noi_dung=f"Bác sĩ vừa chỉ định cận lâm sàng cho bệnh nhân {p_name} ({', '.join(assigned_cls_names)}). Vui lòng tiếp nhận thực hiện.",
                        loai_thong_bao='Cận lâm sàng',
                        lien_ket='/admin/emr?tab=tests'
                    )

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

            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
            hd_next = cursor.fetchone()['next_id']
            ma_hd = f"HD2609{str(hd_next).zfill(3)}"
            totals = invoice_totals(tong_tien_kham, has_bhyt)
            tien_bhyt, thanh_tien = totals['tien_bhyt'], totals['thanh_tien']
            cursor.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien, 'Chưa thanh toán'))
            hoa_don_id = cursor.lastrowid
            for l_khoan, ten_khoan, tham_chieu, sl, dg, tt in invoice_items:
                cursor.execute('''
                    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (hoa_don_id, l_khoan, ten_khoan, tham_chieu, sl, dg, tt))

            cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
            bn_row = cursor.fetchone()
            if bn_row and bn_row.get('tai_khoan_id'):
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                p_uid = bn_row['tai_khoan_id']
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
