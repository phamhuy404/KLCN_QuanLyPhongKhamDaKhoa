from datetime import datetime
from core.database import get_db
from core.audit import AuditLogger

class PharmacyModel:
    """Model quản lý kho dược, danh mục thuốc và nghiệp vụ xuất cấp thuốc."""

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
            JOIN thuoc t ON ct.thuoc_id = t.id
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
                JOIN thuoc t ON ct.thuoc_id = t.id
                WHERE ct.don_thuoc_id = ?
            ''', (r['id'],))
            r['items'] = [dict(it) for it in cursor.fetchall()]

        conn.close()
        return rows

    @staticmethod
    def add_medicine(ten_thuoc, hoat_chat, don_vi_tinh, so_luong_ton, don_gia, ham_luong='', hang_sx='Việt Nam', audit_user=None):
        """Thêm mới dược phẩm vào kho dược."""
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

            conn.commit()
            t_id = cursor.lastrowid
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
    def update_prescription(prescription_id, medicines, advice=None, reason=None, audit_user=None):
        """Bác sĩ cập nhật đơn thuốc chưa cấp phát (kiểm tra thuốc hoạt động, tồn kho, liều dùng)."""
        dt = PharmacyModel.get_prescription_detail(prescription_id)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        # Đơn đã cấp phát thuốc không được chỉnh sửa trực tiếp!
        if dt['trang_thai'] in ['Đã cấp thuốc', 'Đã cấp phát']:
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

            # Nếu đơn đã cấp thuốc và yêu cầu hoàn kho
            if dt['trang_thai'] in ['Đã cấp thuốc', 'Đã cấp phát'] and restore_stock:
                for item in dt.get('items', []):
                    cursor.execute('''
                        UPDATE thuoc
                        SET so_luong_ton = so_luong_ton + ?
                        WHERE id = ?
                    ''', (item['so_luong'], item['thuoc_id']))

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
                after_data={'trang_thai': 'Đã hủy', 'restore_stock': restore_stock}
            )

            return True, f"Đã hủy đơn thuốc {dt['ma_don_thuoc']} và lưu vết kiểm toán thành công!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi hủy đơn thuốc: {str(e)}"

    @staticmethod
    def dispense_prescription(prescription_id_or_code, audit_user=None):
        """Cấp phát thuốc theo đơn: Chống trừ kho lặp lại, kiểm tra số lượng tồn và trừ an toàn."""
        dt = PharmacyModel.get_prescription_detail(prescription_id_or_code)
        if not dt:
            return False, 'Không tìm thấy đơn thuốc!'

        dt_id = dt['id']

        # Chống cấp phát lặp lại
        if dt['trang_thai'] in ['Đã cấp thuốc', 'Đã cấp phát']:
            return False, f"Đơn thuốc {dt['ma_don_thuoc']} đã được cấp phát trước đó! Không thể cấp phát lại để tránh trừ kho trùng lặp."

        if dt['trang_thai'] == 'Đã hủy':
            return False, f"Đơn thuốc {dt['ma_don_thuoc']} đã bị hủy, không thể cấp phát!"

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Kiểm tra tồn kho của TẤT CẢ các thuốc trong đơn trước khi trừ
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

            # 2. Trừ số lượng tồn kho từng loại thuốc
            for it in items:
                cursor.execute('''
                    UPDATE thuoc 
                    SET so_luong_ton = so_luong_ton - ? 
                    WHERE id = ?
                ''', (it['so_luong'], it['thuoc_id']))

            # 3. Cập nhật trạng thái đơn thuốc
            cursor.execute("UPDATE don_thuoc SET trang_thai = ? WHERE id = ?", ('Đã cấp thuốc', dt_id))

            conn.commit()
            conn.close()

            user_name = audit_user.get('ho_ten') if audit_user else 'Dược sĩ'
            AuditLogger.log(
                table_name='don_thuoc',
                row_id=dt_id,
                action='DISPENSE_PRESCRIPTION',
                performed_by=audit_user.get('id') if audit_user else None,
                performed_by_name=user_name,
                reason=f"Cấp phát thuốc cho đơn {dt['ma_don_thuoc']}",
                before_data={'trang_thai': dt['trang_thai']},
                after_data={'trang_thai': 'Đã cấp thuốc'}
            )

            return True, f"Đã xuất dược và trừ kho thành công cho đơn {dt['ma_don_thuoc']}!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cấp phát thuốc: {str(e)}"

