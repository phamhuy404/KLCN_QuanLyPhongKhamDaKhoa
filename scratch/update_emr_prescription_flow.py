import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Cập nhật models/pharmacy_model.py: thêm choose_medicine_purchase_option
with open('models/pharmacy_model.py', 'r', encoding='utf-8') as f:
    pharmacy_code = f.read()

new_purchase_method = """    @staticmethod
    def choose_medicine_purchase_option(prescription_id_or_code, option='Mua tại bệnh viện', audit_user=None):
        \"\"\"Xử lý lựa chọn mua thuốc của bệnh nhân:
        - 'Tự mua ngoài': Không sinh hóa đơn thuốc, không trừ kho của bệnh viện.
        - 'Mua tại bệnh viện': Sinh hóa đơn thuốc (không có đơn giá từng loại), chuyển đơn sang Chờ cấp phát và trừ số lượng thuốc tồn kho của bệnh viện.
        \"\"\"
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
                cursor.execute('''
                    UPDATE don_thuoc
                    SET hinh_thuc_mua = ?, trang_thai = ?
                    WHERE id = ?
                ''', ('Tự mua ngoài', 'Tự mua ngoài', dt['id']))

                # Gửi thông báo cho bệnh nhân
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Đơn thuốc', '/patient/records', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đơn thuốc {dt['ma_don_thuoc']}: Tự mua ngoài",
                        f"Bạn đã chọn tự mua thuốc ngoài cho đơn thuốc {dt['ma_don_thuoc']}. Bạn có thể xem và in đơn thuốc này để mua tại các nhà thuốc bên ngoài.",
                        now_str
                    ))

                conn.commit()
                conn.close()
                return True, "Đã ghi nhận lựa chọn: Bệnh nhân tự mua thuốc bên ngoài."

            elif option == 'Mua tại bệnh viện':
                # Kiểm tra tồn kho của tất cả các thuốc trước khi trừ
                for it in items:
                    cursor.execute('SELECT ten_thuoc, so_luong_ton FROM thuoc WHERE id = ?', (it['thuoc_id'],))
                    th = cursor.fetchone()
                    if not th:
                        conn.close()
                        return False, f"Thuốc ID {it['thuoc_id']} không tồn tại trong kho viện!"
                    if th['so_luong_ton'] < it['so_luong']:
                        conn.close()
                        return False, f"Thuốc '{th['ten_thuoc']}' không đủ số lượng trong kho bệnh viện (còn tồn {th['so_luong_ton']}, cần {it['so_luong']})!"

                # 1. Trừ số lượng tồn kho của bệnh viện
                for it in items:
                    cursor.execute('''
                        UPDATE thuoc
                        SET so_luong_ton = so_luong_ton - ?
                        WHERE id = ?
                    ''', (it['so_luong'], it['thuoc_id']))

                # 2. Cập nhật trạng thái đơn thuốc thành 'Chờ cấp phát' (hoặc Đã cấp thuốc nếu trừ luôn)
                cursor.execute('''
                    UPDATE don_thuoc
                    SET hinh_thuc_mua = ?, trang_thai = ?
                    WHERE id = ?
                ''', ('Mua tại bệnh viện', 'Đã cấp thuốc', dt['id']))

                # 3. Tính tổng tiền thuốc và sinh hóa đơn thuốc
                tong_tien_thuoc = sum(float(it.get('don_gia', 0)) * int(it.get('so_luong', 1)) for it in items)

                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
                hd_next = cursor.fetchone()['next_id']
                ma_hd_thuoc = f"HDT2609{str(hd_next).zfill(3)}"

                # Sinh hóa đơn thuốc (theo yêu cầu: hóa đơn thuốc hiển thị danh sách thuốc không có đơn giá)
                cursor.execute('''
                    INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ma_hd_thuoc, patient_id, dt.get('phieu_kham_id'), tong_tien_thuoc, 0.0, tong_tien_thuoc, 'Chưa thanh toán'))
                hoa_don_id = cursor.lastrowid

                # Lưu chi tiết hóa đơn: ghi nhận các thuốc trong đơn
                for it in items:
                    tt = float(it.get('don_gia', 0)) * int(it.get('so_luong', 1))
                    # Lưu tên thuốc, số lượng, lưu đơn giá 0 hoặc don_gia để tính toán
                    cursor.execute('''
                        INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (hoa_don_id, 'Thuốc', it['ten_thuoc'], it['thuoc_id'], it['so_luong'], 0.0, tt))

                # Gửi thông báo cho bệnh nhân
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Đơn thuốc', '/patient/records', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Đã đăng ký mua thuốc tại bệnh viện: {dt['ma_don_thuoc']}",
                        f"Đơn thuốc {dt['ma_don_thuoc']} đã được chuyển sang Quầy Dược để chuẩn bị và hóa đơn {ma_hd_thuoc} đã được tạo ({tong_tien_thuoc:,.0f} đ). Đã tự động cập nhật trừ tồn kho của bệnh viện.",
                        now_str
                    ))

                conn.commit()
                conn.close()
                return True, f"Đã đăng ký mua thuốc tại bệnh viện thành công! Đã tạo hóa đơn {ma_hd_thuoc} và trừ tồn kho."

            else:
                conn.close()
                return False, f"Tùy chọn mua thuốc không hợp lệ: {option}"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi xử lý tùy chọn mua thuốc: {str(e)}"
"""

if "def choose_medicine_purchase_option" not in pharmacy_code:
    # Thêm vào cuối class PharmacyModel
    pharmacy_code += "\n" + new_purchase_method
    with open('models/pharmacy_model.py', 'w', encoding='utf-8') as f:
        f.write(pharmacy_code)
    print("Added choose_medicine_purchase_option to models/pharmacy_model.py")
else:
    print("choose_medicine_purchase_option already exists in models/pharmacy_model.py")
