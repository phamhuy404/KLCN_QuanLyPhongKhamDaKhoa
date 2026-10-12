from core.database import get_db

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
    def add_medicine(ten_thuoc, hoat_chat, don_vi_tinh, so_luong_ton, don_gia, ham_luong='', hang_sx='Việt Nam'):
        """Thêm mới dược phẩm vào kho dược."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM thuoc')
            next_id = cursor.fetchone()['next_id']
            ma_thuoc = f"TH{str(next_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO thuoc (ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_sx))

            conn.commit()
            conn.close()
            return True, ma_thuoc
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def dispense_prescription(prescription_id_or_code):
        """Cấp phát thuốc theo đơn và tự động trừ số lượng tồn kho."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            # Tìm đơn thuốc
            cursor.execute('''
                SELECT id FROM don_thuoc WHERE id = ? OR ma_don_thuoc = ?
            ''', (prescription_id_or_code, str(prescription_id_or_code)))
            dt = cursor.fetchone()
            if not dt:
                conn.close()
                return False, 'Không tìm thấy đơn thuốc!'

            dt_id = dt['id']

            # Lấy danh sách thuốc trong đơn để trừ kho
            cursor.execute('SELECT thuoc_id, so_luong FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?', (dt_id,))
            items = cursor.fetchall()
            for it in items:
                cursor.execute('''
                    UPDATE thuoc 
                    SET so_luong_ton = MAX(0, so_luong_ton - ?) 
                    WHERE id = ?
                ''', (it['so_luong'], it['thuoc_id']))

            cursor.execute("UPDATE don_thuoc SET trang_thai = 'Đã cấp thuốc' WHERE id = ?", (dt_id,))

            conn.commit()
            conn.close()
            return True, 'Đã xuất dược và trừ kho thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
