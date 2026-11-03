import io
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db
from core.clinical_data import clinical_value, patient_request, published_results
from core.medical_media import protected_image_value

def bulk_get_patient_history(patient_id, approved_only=None):
    approved_only = patient_request() if approved_only is None else approved_only
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT 
                pk.id, pk.lich_hen_id, pk.bac_si_id, pk.phong_kham_id, pk.ma_phieu, pk.thoi_gian_kham, pk.ly_do_kham, pk.trieu_chung,
                pk.chan_doan_so_bo, pk.chan_doan_icd, pk.huong_dieu_tri, pk.loi_dan, pk.ngay_tai_kham,
                pk.hinh_anh_kham, pk.trang_thai,
                COALESCE(nv.ho_ten, N'Bác sĩ trực') AS bac_si,
                COALESCE(ck.ten_khoa, N'Khoa Nội Tổng Quát') AS khoa,
                COALESCE(p.ten_phong, N'Phòng Khám Nội 1') AS phong
            FROM phieu_kham pk
            LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
            LEFT JOIN chuyen_khoa ck ON p.chuyen_khoa_id = ck.id
            WHERE pk.benh_nhan_id = ?
            ORDER BY pk.thoi_gian_kham DESC
        ''', (patient_id,))
        encounters = [dict(r) for r in cursor.fetchall()]
    except Exception:
        cursor.execute('''
            SELECT 
                pk.id, pk.lich_hen_id, pk.bac_si_id, pk.phong_kham_id, pk.ma_phieu, pk.thoi_gian_kham, pk.ly_do_kham, pk.trieu_chung,
                pk.chan_doan_so_bo, pk.chan_doan_icd, pk.huong_dieu_tri, pk.loi_dan, pk.ngay_tai_kham,
                NULL AS hinh_anh_kham, pk.trang_thai,
                COALESCE(nv.ho_ten, N'Bác sĩ trực') AS bac_si,
                COALESCE(ck.ten_khoa, N'Khoa Nội Tổng Quát') AS khoa,
                COALESCE(p.ten_phong, N'Phòng Khám Nội 1') AS phong
            FROM phieu_kham pk
            LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            LEFT JOIN phong_kham p ON pk.phong_kham_id = p.id
            LEFT JOIN chuyen_khoa ck ON p.chuyen_khoa_id = ck.id
            WHERE pk.benh_nhan_id = ?
            ORDER BY pk.thoi_gian_kham DESC
        ''', (patient_id,))
        encounters = [dict(r) for r in cursor.fetchall()]

    if not encounters:
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

    conn.close()

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
            enc['hinh_anh_kham'] = protected_image_value(enc.get('hinh_anh_kham'))
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
            enc['lich_tai_kham'] = None

    return encounters

# Benchmark
from models.patient_model import PatientModel

t0 = time.time()
old_hist = PatientModel.get_patient_history(1)
t_old = (time.time() - t0) * 1000

t0 = time.time()
new_hist = bulk_get_patient_history(1)
t_new = (time.time() - t0) * 1000

print(f"Old get_patient_history: {t_old:.2f} ms ({len(old_hist)} encounters)")
print(f"New get_patient_history: {t_new:.2f} ms ({len(new_hist)} encounters)")
assert len(old_hist) == len(new_hist)
print(f"Speedup: {t_old/t_new:.1f}x faster!")
