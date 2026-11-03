import io
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. Patch models/patient_model.py for bulk get_patient_history
with open('models/patient_model.py', 'r', encoding='utf-8') as f:
    code = f.read()

target_old_loop = """        for enc in encounters:
            # Lấy cận lâm sàng
            cursor.execute('''
                SELECT 
                    ct.id AS chi_tiet_id,
                    dv.ten_dich_vu AS ten,
                    dv.loai_dich_vu AS loai,
                    ct.ket_qua,
                    ct.file_ket_qua,
                    ct.ktv_thuc_hien AS bac_si_thuc_hien,
                    ct.trang_thai
                FROM phieu_chi_dinh cd
                JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
                JOIN dich_vu dv ON ct.dich_vu_id = dv.id
                WHERE cd.phieu_kham_id = ?
            ''', (enc['id'],))
            enc['can_lam_sang'] = [dict(r) for r in cursor.fetchall()]
            if approved_only:
                enc['can_lam_sang'] = published_results(enc['can_lam_sang'])
            enc['hinh_anh_kham'] = protected_image_value(enc.get('hinh_anh_kham'))
            for item in enc['can_lam_sang']:
                item['ket_qua'] = clinical_value(item.get('ket_qua'))
                item['file_ket_qua'] = protected_image_value(item.get('file_ket_qua'))

            # Lấy thông tin đơn thuốc và hình thức mua
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
            enc['don_thuoc'] = dt_rows

            if enc.get('ngay_tai_kham'):
                try:
                    kham_d = datetime.strptime(str(enc.get('thoi_gian_kham'))[:10], '%Y-%m-%d').date()
                    tai_d = datetime.strptime(str(enc.get('ngay_tai_kham'))[:10], '%Y-%m-%d').date()
                    delta = (tai_d - kham_d).days
                    if delta > 0:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Sau {delta} ngày)"
                    elif delta == 0:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Trong ngày)"
                    else:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']}"
                except Exception:
                    enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']}"
            else:
                enc['lich_tai_kham'] = None"""

replacement_bulk_loop = """        if not encounters:
            conn.close()
            return []

        pk_ids = [e['id'] for e in encounters]
        placeholders = ','.join('?' * len(pk_ids))

        # 1. Bulk CLS
        cursor.execute(f'''
            SELECT 
                cd.phieu_kham_id,
                ct.id AS chi_tiet_id,
                dv.ten_dich_vu AS ten,
                dv.loai_dich_vu AS loai,
                ct.ket_qua,
                ct.file_ket_qua,
                ct.ktv_thuc_hien AS bac_si_thuc_hien,
                ct.trang_thai
            FROM phieu_chi_dinh cd
            JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
            JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            WHERE cd.phieu_kham_id IN ({placeholders})
        ''', pk_ids)
        cls_map = {}
        for r in cursor.fetchall():
            item = dict(r)
            item['ket_qua'] = clinical_value(item.get('ket_qua'))
            item['file_ket_qua'] = protected_image_value(item.get('file_ket_qua'))
            cls_map.setdefault(item['phieu_kham_id'], []).append(item)

        # 2. Bulk Prescriptions
        cursor.execute(f'''
            SELECT id AS don_thuoc_id, phieu_kham_id, ma_don_thuoc, trang_thai AS trang_thai_don_thuoc, hinh_thuc_mua
            FROM don_thuoc
            WHERE phieu_kham_id IN ({placeholders})
        ''', pk_ids)
        dt_map = {r['phieu_kham_id']: dict(r) for r in cursor.fetchall()}

        # 3. Bulk Prescription Items
        cursor.execute(f'''
            SELECT 
                dt.phieu_kham_id,
                t.ten_thuoc AS ten,
                t.hoat_chat,
                ct.so_luong,
                t.don_vi_tinh,
                ct.cach_dung
            FROM don_thuoc dt
            JOIN chi_tiet_don_thuoc ct ON dt.id = ct.don_thuoc_id
            JOIN thuoc t ON ct.thuoc_id = t.id
            WHERE dt.phieu_kham_id IN ({placeholders})
        ''', pk_ids)
        items_map = {}
        for r in cursor.fetchall():
            row = dict(r)
            row['so_luong'] = f"{row['so_luong']} {row['don_vi_tinh']}"
            items_map.setdefault(row['phieu_kham_id'], []).append(row)

        for enc in encounters:
            eid = enc['id']
            raw_cls = cls_map.get(eid, [])
            enc['can_lam_sang'] = published_results(raw_cls) if approved_only else raw_cls
            enc['hinh_anh_kham'] = protected_image_value(enc.get('hinh_anh_kham'))

            dt_info = dt_map.get(eid)
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

            enc['don_thuoc'] = items_map.get(eid, [])

            if enc.get('ngay_tai_kham'):
                try:
                    kham_d = datetime.strptime(str(enc.get('thoi_gian_kham'))[:10], '%Y-%m-%d').date()
                    tai_d = datetime.strptime(str(enc.get('ngay_tai_kham'))[:10], '%Y-%m-%d').date()
                    delta = (tai_d - kham_d).days
                    if delta > 0:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Sau {delta} ngày)"
                    elif delta == 0:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Trong ngày)"
                    else:
                        enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']}"
                except Exception:
                    enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']}"
            else:
                enc['lich_tai_kham'] = None"""

assert target_old_loop in code, "target_old_loop not found"
code = code.replace(target_old_loop, replacement_bulk_loop, 1)

with open('models/patient_model.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully optimized models/patient_model.py!")
