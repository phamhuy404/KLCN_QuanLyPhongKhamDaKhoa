from datetime import datetime
from core.database import get_db
from core.audit import AuditLogger
from core.pharmacy_safety import guarded, journal, validate_items
from core.scheduling import serialized, integer, CalendarError
from decimal import Decimal
from uuid import UUID

class PharmacyModel:
    """Model quản lý kho dược, danh mục thuốc và nghiệp vụ xuất cấp thuốc."""

    @staticmethod
    @serialized
    def receive_stock(medicine_id, quantity, reason, receipt_id, audit_user=None):
        """Explicit inventory receipt; UUID makes retries idempotent."""
        drug, qty = integer(medicine_id), integer(quantity)
        if drug <= 0 or qty <= 0 or qty > 2147483647 or not str(reason or '').strip():
            raise CalendarError('Thuốc, số lượng nhập dương và lý do là bắt buộc.')
        receipt = str(UUID(str(receipt_id)))
        cursor = get_db().cursor()
        cursor.execute("SELECT row_id, after_json FROM audit_log WHERE table_name='thuoc' AND action='STOCK_IN' AND JSON_VALUE(after_json, '$.receipt')=?", (receipt,))
        previous = cursor.fetchone()
        if previous:
            import json
            data = json.loads(previous['after_json'])
            if previous['row_id'] != drug or data['delta'] != qty:
                raise CalendarError('Mã nhập kho đã dùng cho nội dung khác.')
            return True, 'Phiếu nhập này đã được xử lý; không cộng kho lại.'
        cursor.execute('''UPDATE thuoc SET so_luong_ton=so_luong_ton+?
            OUTPUT deleted.so_luong_ton AS old_stock, inserted.so_luong_ton AS new_stock
            WHERE id=? AND trang_thai=1 AND so_luong_ton>=0 AND so_luong_ton<=?''',
            (qty, drug, 2147483647-qty))
        movement = cursor.fetchone()
        if not movement:
            raise CalendarError('Thuốc không hoạt động hoặc tồn kho không hợp lệ.')
        journal(cursor, drug, qty, movement['old_stock'], movement['new_stock'],
                audit_user, str(reason).strip(), receipt)
        return True, 'Đã nhập kho và ghi lịch sử.'

    @staticmethod
    def stock_history(medicine_id):
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 100 * FROM audit_log WHERE table_name='thuoc' AND row_id=? AND action IN ('STOCK_IN','STOCK_OUT') ORDER BY id DESC", (integer(medicine_id),))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_all_medicines():
        """Lấy toàn bộ danh mục thuốc trong kho."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                id,
                ma_thuoc, ma_thuoc AS ma,
                ten_thuoc, ten_thuoc AS ten,
                hoat_chat, ham_luong,
                don_vi_tinh, don_vi_tinh AS dvt,
                don_gia, don_gia AS gia,
                so_luong_ton, so_luong_ton AS ton,
                hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai
            FROM thuoc
            ORDER BY id ASC
        ''')
        medicines = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return medicines

    @staticmethod
    def get_prescription_detail(prescription_id):
        """Lấy chi tiết đơn thuốc và các mặt hàng thuốc trong đơn."""
        conn = get_db()
        cursor = conn.cursor()
        # Xác định loại ID: int hoặc mã chuỗi
        try:
            pid_int = int(prescription_id)
        except (ValueError, TypeError):
            pid_int = None

        if pid_int is not None:
            cursor.execute('''
                SELECT dt.*, pk.ma_phieu, pk.benh_nhan_id,
                       bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan,
                       COALESCE(nv.ho_ten, 'Bác sĩ chuyên khoa') AS ten_bac_si
                FROM don_thuoc dt
                JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON dt.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE dt.id = ? OR dt.ma_don_thuoc = ?
            ''', (pid_int, str(prescription_id)))
        else:
            # Tìm chỉ theo mã chuỗi
            cursor.execute('''
                SELECT dt.*, pk.ma_phieu, pk.benh_nhan_id,
                       bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan,
                       COALESCE(nv.ho_ten, 'Bác sĩ chuyên khoa') AS ten_bac_si
                FROM don_thuoc dt
                JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON dt.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE dt.ma_don_thuoc = ?
            ''', (str(prescription_id),))
        dt = cursor.fetchone()
        if not dt:
            conn.close()
            return None

        result = dict(dt)
        cursor.execute('''
            SELECT ct.*, t.ma_thuoc, t.ten_thuoc, t.don_vi_tinh, t.don_gia, t.so_luong_ton, t.trang_thai AS thuoc_active
            FROM chi_tiet_don_thuoc ct
            LEFT JOIN thuoc t ON ct.thuoc_id = t.id
            WHERE ct.don_thuoc_id = ?
        ''', (result['id'],))
        result['items'] = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return result

    @staticmethod
    def get_prescriptions_by_patient(patient_id):
        """Lấy danh sách các đơn thuốc của một bệnh nhân cụ thể."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dt.*, pk.ma_phieu, COALESCE(nv.ho_ten, 'Bác sĩ điều trị') AS ten_bac_si
            FROM don_thuoc dt
            JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
            LEFT JOIN bac_si bs ON dt.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            WHERE pk.benh_nhan_id = ?
            ORDER BY dt.id DESC
        ''', (patient_id,))
        rows = [dict(r) for r in cursor.fetchall()]

        for r in rows:
            cursor.execute('''
                SELECT ct.*, t.ten_thuoc, t.don_vi_tinh, t.don_gia
                FROM chi_tiet_don_thuoc ct
                LEFT JOIN thuoc t ON ct.thuoc_id = t.id
                WHERE ct.don_thuoc_id = ?
            ''', (r['id'],))
            r['items'] = [dict(it) for it in cursor.fetchall()]

        conn.close()
        return rows

    @staticmethod
    @serialized
    def add_medicine(ten_thuoc, hoat_chat, don_vi_tinh, so_luong_ton, don_gia, ham_luong='', hang_sx='Việt Nam', audit_user=None):
        """Thêm mới dược phẩm vào kho dược với kiểm tra ràng buộc chặt chẽ."""
        so_luong_ton = integer(so_luong_ton)
        if so_luong_ton < 0 or so_luong_ton > 2147483647 or not Decimal(str(don_gia)).is_finite() or Decimal(str(don_gia)) < 0:
            raise CalendarError('So luong hoac don gia khong hop le.')
        from core.validators import validate_medicine_data
        ok_med, err_med = validate_medicine_data({
            'ten_thuoc': ten_thuoc,
            'gia_ban': don_gia,
            'so_luong_ton': so_luong_ton
        })
        if not ok_med:
            return False, list(err_med.values())[0]

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM thuoc')
            next_id = cursor.fetchone()['next_id']
            ma_thuoc = f"TH{str(next_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO thuoc (ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_sx))

            t_id = cursor.lastrowid
            if so_luong_ton:
                journal(cursor, t_id, so_luong_ton, 0, so_luong_ton, audit_user, 'Initial stock')
            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='thuoc',
                row_id=t_id,
                action='ADD_MEDICINE',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Dược sĩ',
                reason='Thêm mới dược phẩm vào danh mục kho',
                after_data={'ma_thuoc': ma_thuoc, 'ten_thuoc': ten_thuoc, 'so_luong_ton': so_luong_ton}
            )

            return True, ma_thuoc
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    @guarded
    def update_prescription(prescription_id, medicines, advice=None, reason=None, audit_user=None):
        """Bác sĩ cập nhật đơn thuốc chưa cấp phát (kiểm tra thuốc hoạt động, tồn kho, liều dùng)."""
        dt = PharmacyModel.get_prescription_detail(prescription_id)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        # Đơn đã cấp phát thuốc không được chỉnh sửa trực tiếp!
        if dt['trang_thai'] in ['Đã cấp thuốc', 'Đã cấp phát', 'Đã nhận thuốc']:
            return False, 'Đơn thuốc này đã được cấp phát, không thể chỉnh sửa trực tiếp! Vui lòng dùng quy trình điều chỉnh/hủy đơn.'

        if dt['trang_thai'] == 'Đã hủy':
            return False, 'Đơn thuốc này đã bị hủy, không thể chỉnh sửa!'

        if not medicines or len(medicines) == 0:
            return False, 'Đơn thuốc phải có ít nhất 1 loại thuốc!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Kiểm tra từng thuốc: còn hoạt động và tồn kho
            for m in medicines:
                t_id = m.get('thuoc_id')
                qty = int(m.get('so_luong', 1))
                if qty <= 0:
                    conn.close()
                    return False, f"Số lượng thuốc phải lớn hơn 0!"

                cursor.execute('SELECT id, ten_thuoc, so_luong_ton, trang_thai FROM thuoc WHERE id = ?', (t_id,))
                th = cursor.fetchone()
                if not th:
                    conn.close()
                    return False, f"Không tìm thấy thuốc có mã ID {t_id}!"
                if th.get('trang_thai') == 0:
                    conn.close()
                    return False, f"Thuốc '{th['ten_thuoc']}' hiện đang tạm ngưng sử dụng!"
                if th['so_luong_ton'] < qty:
                    conn.close()
                    return False, f"Thuốc '{th['ten_thuoc']}' không đủ tồn kho (Còn {th['so_luong_ton']}, yêu cầu {qty})!"

            # 2. Xóa các mục thuốc cũ trong chi_tiet_don_thuoc
            cursor.execute('DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?', (dt['id'],))

            # 3. Thêm các mục thuốc mới
            for m in medicines:
                t_id = m.get('thuoc_id')
                qty = int(m.get('so_luong', 1))
                lieu_dung = m.get('lieu_dung', 'Ngày 2 lần, lần 1 viên')
                cach_dung = m.get('cach_dung', 'Uống sau ăn')
                cursor.execute('''
                    INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                    VALUES (?, ?, ?, ?, ?)
                ''', (dt['id'], t_id, qty, lieu_dung, cach_dung))

            # 4. Cập nhật lời dặn nếu có
            if advice is not None:
                cursor.execute('UPDATE don_thuoc SET loi_dan = ? WHERE id = ?', (advice, dt['id']))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='don_thuoc',
                row_id=dt['id'],
                action='UPDATE_PRESCRIPTION',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=audit_user.get('ho_ten') if audit_user else 'Bác sĩ',
                reason=reason or 'Chỉnh sửa danh mục thuốc trong đơn',
                before_data={'items': dt.get('items'), 'loi_dan': dt.get('loi_dan')},
                after_data={'items': medicines, 'loi_dan': advice}
            )

            return True, 'Cập nhật đơn thuốc thành công!'

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f'Lỗi cập nhật đơn thuốc: {str(e)}'

    @staticmethod
    @guarded
    def cancel_or_adjust_prescription(prescription_id, reason, restore_stock=True, audit_user=None):
        """Hủy hoặc điều chỉnh đơn thuốc có lưu vết và xử lý tồn kho an toàn."""
        dt = PharmacyModel.get_prescription_detail(prescription_id)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        if dt['trang_thai'] == 'Đã hủy':
            return False, 'Đơn thuốc này đã ở trạng thái Đã hủy!'

        if not reason or reason.strip() == '':
            return False, 'Vui lòng cung cấp lý do hủy / điều chỉnh đơn thuốc!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_name = audit_user.get('ho_ten') if audit_user else 'Bác sĩ'

            cursor.execute('''
                UPDATE don_thuoc
                SET trang_thai = ?, ly_do_huy = ?, nguoi_huy = ?, thoi_gian_huy = ?
                WHERE id = ?
            ''', ('Đã hủy', reason, user_name, now_str, dt['id']))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='don_thuoc',
                row_id=dt['id'],
                action='CANCEL_PRESCRIPTION',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=user_name,
                reason=reason,
                before_data={'trang_thai': dt['trang_thai']},
                after_data={'trang_thai': 'Đã hủy', 'restore_stock': False}
            )

            return True, f"Đã hủy đơn thuốc {dt['ma_don_thuoc']} và lưu vết kiểm toán thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi hủy đơn thuốc: {str(e)}"

    @staticmethod
    @guarded
    def dispense_prescription(prescription_id_or_code, audit_user=None):
        """Dược sĩ / Quản lý kho cấp phát thuốc: Kiểm tra hóa đơn đã thanh toán, trừ số lượng tồn kho và cập nhật Đã nhận thuốc."""
        dt = PharmacyModel.get_prescription_detail(prescription_id_or_code)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        dt_id = dt['id']

        # Chống cấp phát lặp lại
        if dt['trang_thai'] in ['Đã nhận thuốc', 'Đã cấp thuốc', 'Đã cấp phát']:
            return False, f"Đơn thuốc {dt['ma_don_thuoc']} đã được cấp phát trước đó! Không thể cấp phát lại để tránh trừ kho trùng lặp."

        if dt['trang_thai'] == 'Đã hủy':
            return False, f"Đơn thuốc {dt['ma_don_thuoc']} đã bị hủy, không thể cấp phát!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Kiểm tra hóa đơn tiền thuốc đã được thanh toán chưa
            cursor.execute('''
                SELECT TOP 1 id, ma_hoa_don, trang_thai 
                FROM hoa_don 
                WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%' AND trang_thai != N'Đã hủy'
                ORDER BY id DESC
            ''', (dt.get('phieu_kham_id'),))
            hd_row = cursor.fetchone()
            if not hd_row:
                conn.close()
                return False, "Không tìm thấy hóa đơn tiền thuốc hợp lệ của đơn thuốc này!"
            if hd_row['trang_thai'] != 'Đã thanh toán':
                conn.close()
                return False, f"Bệnh nhân chưa thanh toán hóa đơn tiền thuốc ({hd_row['ma_hoa_don']})! Vui lòng yêu cầu bệnh nhân thanh toán trước khi cấp phát thuốc."

            # 2. Kiểm tra tồn kho của TẤT CẢ các thuốc trong đơn trước khi trừ
            items = dt.get('items', [])
            for it in items:
                cursor.execute('SELECT ten_thuoc, so_luong_ton, trang_thai FROM thuoc WHERE id = ?', (it['thuoc_id'],))
                th = cursor.fetchone()
                if not th:
                    conn.close()
                    return False, f"Thuốc ID {it['thuoc_id']} không tồn tại trong kho!"
                if th['so_luong_ton'] < it['so_luong']:
                    conn.close()
                    return False, f"Thuốc '{th['ten_thuoc']}' không đủ số lượng trong kho (Còn: {th['so_luong_ton']}, Yêu cầu: {it['so_luong']})!"

            # 3. Trừ số lượng tồn kho từng loại thuốc tại kho viện
            for it in items:
                cursor.execute('''UPDATE thuoc SET so_luong_ton=so_luong_ton-?
                    OUTPUT deleted.so_luong_ton AS old_stock, inserted.so_luong_ton AS new_stock
                    WHERE id=? AND trang_thai=1 AND so_luong_ton>=?''',
                    (it['so_luong'], it['thuoc_id'], it['so_luong']))
                movement = cursor.fetchone()
                if not movement:
                    raise CalendarError('Khong du ton kho; giao dich bi huy.')
                journal(cursor, it['thuoc_id'], -it['so_luong'], movement['old_stock'],
                        movement['new_stock'], audit_user, 'Dispense', str(dt_id))

            # 4. Cập nhật trạng thái đơn thuốc thành 'Đã nhận thuốc'
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE don_thuoc SET trang_thai = ? WHERE id = ?", ('Đã nhận thuốc', dt_id))

            # 5. Cập nhật trên hóa đơn bệnh nhân: trang_thai_nhan_thuoc = 'Đã nhận thuốc'
            if hd_row:
                cursor.execute('''
                    UPDATE hoa_don 
                    SET trang_thai_nhan_thuoc = N'Đã nhận thuốc'
                    WHERE id = ?
                ''', (hd_row['id'],))

            # 6. Gửi thông báo cho bệnh nhân
            patient_id = dt.get('benh_nhan_id')
            if patient_id:
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Nhận thuốc', '/patient/records', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đã nhận thuốc: {dt['ma_don_thuoc']}",
                        f"Bạn đã nhận đầy đủ thuốc tại Quầy dược cho đơn {dt['ma_don_thuoc']}. Vui lòng đọc kỹ hướng dẫn sử dụng và tái khám đúng hẹn.",
                        now_str
                    ))

            conn.commit()
            conn.close()

            user_name = audit_user.get('ho_ten') if audit_user else 'Dược sĩ quản lý kho'
            AuditLogger.log(
                table_name='don_thuoc',
                row_id=dt_id,
                action='DISPENSE_PRESCRIPTION',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=user_name,
                reason=f"Cấp phát thuốc cho đơn {dt['ma_don_thuoc']}",
                before_data={'trang_thai': dt['trang_thai']},
                after_data={'trang_thai': 'Đã nhận thuốc'}
            )

            return True, f"Đã cấp phát thuốc thành công cho đơn {dt['ma_don_thuoc']}, trừ kho và cập nhật 'Đã nhận thuốc'!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cấp phát thuốc: {str(e)}"


    @staticmethod
    @guarded
    def choose_medicine_purchase_option(prescription_id_or_code, option='Mua tại bệnh viện', audit_user=None):
        """Xử lý lựa chọn mua thuốc của bệnh nhân:
        - 'Tự mua ngoài': Chuyển trạng thái 'Mua ngoài', tự động hủy hóa đơn thuốc chưa thanh toán nếu có. Chặn đổi nếu đơn đã được duyệt.
        - 'Mua tại bệnh viện': Sinh hóa đơn thuốc (không có đơn giá từng loại), chuyển đơn sang Chờ duyệt.
        """
        dt = PharmacyModel.get_prescription_detail(prescription_id_or_code)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            patient_id = dt.get('benh_nhan_id')
            items = dt.get('items', [])

            if option == 'Tự mua ngoài':
                # Chặn nếu đơn thuốc đã được tiếp tân/admin duyệt
                locked_statuses = [
                    'Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy',
                    'Đã duyệt thành công, xuống chỗ bán thuốc để lấy',
                    'Chờ nhận thuốc',
                    'Chưa nhận thuốc',
                    'Đã nhận thuốc',
                    'Đã cấp thuốc'
                ]
                if dt.get('trang_thai') in locked_statuses:
                    conn.close()
                    return False, "Đơn thuốc đã được tiếp tân/admin duyệt, bạn không thể đổi sang mua ngoài nữa! Vui lòng liên hệ quầy tiếp tân nếu cần hỗ trợ."

                cursor.execute('''
                    UPDATE don_thuoc
                    SET hinh_thuc_mua = ?, trang_thai = ?
                    WHERE id = ?
                ''', ('Tự mua ngoài', 'Mua ngoài', dt['id']))

                # Tự động hủy hóa đơn thuốc tạm đã tạo trước đó nếu chưa thanh toán
                if dt.get('phieu_kham_id'):
                    cursor.execute('''
                        UPDATE hoa_don
                        SET trang_thai = N'Đã hủy'
                        WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%' AND trang_thai = N'Chưa thanh toán'
                    ''', (dt['phieu_kham_id'],))

                # Gửi thông báo cho bệnh nhân
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Đơn thuốc', '/patient/records', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đơn thuốc {dt['ma_don_thuoc']}: Mua ngoài",
                        f"Bạn đã chọn tự mua thuốc ngoài cho đơn thuốc {dt['ma_don_thuoc']}. Bạn có thể xem và in đơn thuốc này để mua tại các nhà thuốc bên ngoài.",
                        now_str
                    ))

                conn.commit()
                conn.close()
                return True, "Đã ghi nhận lựa chọn: Bệnh nhân tự mua thuốc bên ngoài."

            elif option == 'Mua tại bệnh viện':
                # 1. Cập nhật trạng thái đơn thuốc thành 'Chờ duyệt' (chưa trừ kho, chờ Tiếp tân/Admin duyệt)
                cursor.execute('''
                    UPDATE don_thuoc
                    SET hinh_thuc_mua = ?, trang_thai = ?
                    WHERE id = ?
                ''', ('Mua tại bệnh viện', 'Chờ duyệt', dt['id']))

                # 2. Tính tổng tiền thuốc và sinh hóa đơn thuốc nếu chưa có
                cursor.execute('''
                    SELECT id FROM hoa_don 
                    WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%' AND trang_thai = N'Chưa thanh toán'
                ''', (dt.get('phieu_kham_id'),))
                existing_hd = cursor.fetchone()

                if not existing_hd:
                    tong_tien_thuoc = sum(Decimal(str(it['don_gia'])) * int(it['so_luong']) for it in items)

                    cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
                    hd_next = cursor.fetchone()['next_id']
                    ma_hd_thuoc = f"HDT2609{str(hd_next).zfill(3)}"

                    cursor.execute('''
                        INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai, trang_thai_nhan_thuoc)
                        VALUES (?, ?, ?, ?, ?, ?, ?, N'Chưa nhận thuốc')
                    ''', (ma_hd_thuoc, patient_id, dt.get('phieu_kham_id'), tong_tien_thuoc, 0.0, tong_tien_thuoc, 'Chưa thanh toán'))
                    hoa_don_id = cursor.lastrowid

                    # Lưu chi tiết hóa đơn: ghi nhận các thuốc trong đơn
                    for it in items:
                        tt = Decimal(str(it['don_gia'])) * int(it['so_luong'])
                        cursor.execute('''
                            INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (hoa_don_id, 'Thuốc', it['ten_thuoc'], it['thuoc_id'], it['so_luong'], it['don_gia'], tt))

                # 3. Gửi thông báo cho bệnh nhân
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Đơn thuốc', '/patient/records', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đơn thuốc {dt['ma_don_thuoc']}: Đang chờ duyệt",
                        f"Bạn đã chọn mua thuốc tại bệnh viện cho đơn {dt['ma_don_thuoc']}. Đơn thuốc đang ở trạng thái 'Chờ duyệt'. Khi Tiếp tân/Admin duyệt, bạn sẽ nhận được thông báo để thanh toán và lấy thuốc.",
                        now_str
                    ))

                # 4. Gửi thông báo cho Tiếp tân và Admin để duyệt đơn thuốc
                cursor.execute('SELECT id FROM tai_khoan WHERE vai_tro_id IN (1, 2) AND trang_thai = 1')
                reception_admins = cursor.fetchall()
                for ra in reception_admins:
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Duyệt đơn thuốc', '/admin/pharmacy?tab=dispensing', 0, ?)
                    ''', (
                        ra['id'],
                        f"Đơn thuốc mới chờ duyệt: {dt['ma_don_thuoc']}",
                        f"Bệnh nhân {bn_row['ho_ten'] if bn_row else ''} đăng ký mua thuốc tại BV ({dt['ma_don_thuoc']}). Vui lòng kiểm tra và duyệt đơn thuốc.",
                        now_str
                    ))

                conn.commit()
                conn.close()
                return True, f"Đã đăng ký mua thuốc tại bệnh viện thành công! Đơn thuốc đang chờ Tiếp tân/Admin duyệt."

            else:
                conn.close()
                return False, f"Tùy chọn mua thuốc không hợp lệ: {option}"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi xử lý tùy chọn mua thuốc: {str(e)}"

    @staticmethod
    @guarded
    def approve_prescription(prescription_id_or_code, reviewer_user=None):
        """Tiếp tân hoặc Admin duyệt đơn thuốc mua tại bệnh viện: Kiểm tra tồn kho, đổi trạng thái yêu cầu thanh toán (CHƯA trừ kho)."""
        dt = PharmacyModel.get_prescription_detail(prescription_id_or_code)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        approved_statuses = [
            'Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy',
            'Đã duyệt thành công, xuống chỗ bán thuốc để lấy',
            'Chờ nhận thuốc',
            'Chưa nhận thuốc',
            'Đã nhận thuốc',
            'Đã cấp thuốc'
        ]
        if dt['trang_thai'] in approved_statuses:
            return False, 'Đơn thuốc này đã được phê duyệt trước đó!'

        if dt['trang_thai'] == 'Đã hủy':
            return False, 'Đơn thuốc này đã bị hủy, không thể duyệt!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            items = dt.get('items', [])
            # 1. Kiểm tra tồn kho của TẤT CẢ các thuốc (chỉ kiểm tra xem đủ không, KHÔNG trừ kho ở bước này)
            for it in items:
                cursor.execute('SELECT ten_thuoc, so_luong_ton FROM thuoc WHERE id = ?', (it['thuoc_id'],))
                th = cursor.fetchone()
                if not th:
                    conn.close()
                    return False, f"Thuốc ID {it['thuoc_id']} không tồn tại trong kho viện!"
                if th['so_luong_ton'] < it['so_luong']:
                    conn.close()
                    return False, f"Thuốc '{th['ten_thuoc']}' không đủ tồn kho (còn {th['so_luong_ton']}, yêu cầu {it['so_luong']})!"

            # 2. Cập nhật trạng thái đơn thuốc (Tiếp tân/Admin KHÔNG trừ kho)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            reviewer_name = reviewer_user.get('ho_ten') if reviewer_user else 'Tiếp tân / Admin'
            new_status = 'Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy'

            cursor.execute('''
                UPDATE don_thuoc
                SET trang_thai = ?, nguoi_duyet = ?, ngay_duyet = ?
                WHERE id = ?
            ''', (new_status, reviewer_name, now_str, dt['id']))

            # 3. Gửi thông báo cho bệnh nhân đi thanh toán hóa đơn và nhận thuốc
            patient_id = dt.get('benh_nhan_id')
            if patient_id:
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Nhận thuốc', '/patient/invoices', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đơn thuốc {dt['ma_don_thuoc']}: Đã duyệt",
                        f"Đơn thuốc {dt['ma_don_thuoc']} đã được {reviewer_name} duyệt. Vui lòng thanh toán hóa đơn viện phí tiền thuốc và nhận thuốc tại quầy dược.",
                        now_str
                    ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='don_thuoc',
                row_id=dt['id'],
                action='APPROVE_PRESCRIPTION',
                performed_by=reviewer_user.get('id') if reviewer_user else None,
                performed_by_name=reviewer_name,
                reason='Tiếp tân/Admin duyệt đơn thuốc mua tại viện (chuyển trạng thái yêu cầu thanh toán)',
                before_data={'trang_thai': dt['trang_thai']},
                after_data={'trang_thai': new_status}
            )

            return True, f"Đã duyệt đơn thuốc {dt['ma_don_thuoc']}, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi phê duyệt đơn thuốc: {str(e)}"

    @staticmethod
    @guarded
    def reject_prescription(prescription_id_or_code, reason=None, reviewer_user=None):
        """Tiếp tân hoặc Admin từ chối duyệt đơn thuốc tại bệnh viện (ví dụ hết thuốc) và hủy hóa đơn thuốc chưa thanh toán."""
        dt = PharmacyModel.get_prescription_detail(prescription_id_or_code)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        if dt['trang_thai'] in ['Đã nhận thuốc', 'Đã cấp thuốc', 'Đã cấp phát']:
            return False, 'Đơn thuốc này đã cấp phát, không thể từ chối duyệt!'

        conn = get_db()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            reviewer_name = reviewer_user.get('ho_ten') if reviewer_user else 'Tiếp tân / Admin'
            ly_do_text = reason or 'Kho dược phòng khám tạm hết thuốc'
            new_status = 'Bị từ chối duyệt (Hết thuốc viện, vui lòng mua ngoài)'

            cursor.execute('''
                UPDATE don_thuoc
                SET trang_thai = ?, ly_do_huy = ?, nguoi_huy = ?, thoi_gian_huy = ?, nguoi_duyet = ?, ngay_duyet = ?
                WHERE id = ?
            ''', (new_status, ly_do_text, reviewer_name, now_str, reviewer_name, now_str, dt['id']))

            # Hủy hóa đơn tiền thuốc liên quan
            if dt.get('phieu_kham_id'):
                cursor.execute('''
                    UPDATE hoa_don
                    SET trang_thai = N'Đã hủy'
                    WHERE phieu_kham_id = ? AND ma_hoa_don LIKE 'HDT%' AND trang_thai = N'Chưa thanh toán'
                ''', (dt['phieu_kham_id'],))

            # Gửi thông báo cho bệnh nhân
            patient_id = dt.get('benh_nhan_id')
            if patient_id:
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Đơn thuốc', '/patient/records', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đơn thuốc {dt['ma_don_thuoc']}: Bị từ chối duyệt",
                        f"Đơn thuốc {dt['ma_don_thuoc']} không thể duyệt tại bệnh viện. Lý do: {ly_do_text}. Bạn có thể xem đơn thuốc và tự mua ngoài tại các nhà thuốc.",
                        now_str
                    ))

            conn.commit()
            conn.close()

            AuditLogger.log(
                table_name='don_thuoc',
                row_id=dt['id'],
                action='REJECT_PRESCRIPTION',
                performed_by=reviewer_user.get('id') if reviewer_user else None,
                performed_by_name=reviewer_name,
                reason=ly_do_text,
                before_data={'trang_thai': dt['trang_thai']},
                after_data={'trang_thai': new_status}
            )

            return True, f"Đã từ chối duyệt đơn thuốc {dt['ma_don_thuoc']} và hủy hóa đơn viện phí liên quan!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi từ chối duyệt đơn thuốc: {str(e)}"
