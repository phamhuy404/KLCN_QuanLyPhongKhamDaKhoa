with open('models/patient_model.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = """            # Lấy đơn thuốc
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
            enc['don_thuoc'] = dt_rows"""

replacement = """            # Lấy thông tin đơn thuốc & hình thức mua
            cursor.execute('''
                SELECT id AS don_thuoc_id, ma_don_thuoc, trang_thai AS trang_thai_don_thuoc, hinh_thuc_mua
                FROM don_thuoc
                WHERE phieu_kham_id = ?
            ''', (enc['id'],))
            dt_info = cursor.fetchone()
            if dt_info:
                enc['don_thuoc_id'] = dt_info['don_thuoc_id']
                enc['ma_don_thuoc'] = dt_info['ma_don_thuoc']
                enc['trang_thai_don_thuoc'] = dt_info['trang_thai_don_thuoc']
                enc['hinh_thuc_mua'] = dt_info.get('hinh_thuc_mua') or 'Chưa chọn'
            else:
                enc['don_thuoc_id'] = None
                enc['ma_don_thuoc'] = None
                enc['trang_thai_don_thuoc'] = None
                enc['hinh_thuc_mua'] = None

            # Lấy chi tiết các loại thuốc trong đơn
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
            enc['don_thuoc'] = dt_rows"""

c = c.replace(target, replacement).replace(target.replace('\n', '\r\n'), replacement.replace('\n', '\r\n'))

with open('models/patient_model.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated patient_model.py successfully!')
