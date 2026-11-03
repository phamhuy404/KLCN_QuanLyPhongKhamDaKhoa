import io
import sys
import os
import time

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db

conn = get_db()
cur = conn.cursor()

indexes = [
    # 1. Bệnh án và khám bệnh
    ("idx_phieukham_benhnhan", "phieu_kham", "(benh_nhan_id, thoi_gian_kham DESC)"),
    ("idx_phieukham_bacsi", "phieu_kham", "(bac_si_id)"),
    ("idx_phieukham_lichhen", "phieu_kham", "(lich_hen_id)"),
    
    # 2. Cận lâm sàng
    ("idx_phieuchidinh_pk", "phieu_chi_dinh", "(phieu_kham_id)"),
    ("idx_chitietchidinh_phieu", "chi_tiet_chi_dinh", "(phieu_chi_dinh_id)"),
    ("idx_chitietchidinh_dichvu", "chi_tiet_chi_dinh", "(dich_vu_id)"),
    
    # 3. Đơn thuốc
    ("idx_donthuoc_pk", "don_thuoc", "(phieu_kham_id)"),
    ("idx_chitietdonthuoc_don", "chi_tiet_don_thuoc", "(don_thuoc_id)"),
    ("idx_chitietdonthuoc_thuoc", "chi_tiet_don_thuoc", "(thuoc_id)"),
    
    # 4. Sinh hiệu
    ("idx_chisosinhton_bn", "chi_so_sinh_ton", "(benh_nhan_id, id DESC)"),
    
    # 5. Hóa đơn và chi tiết
    ("idx_hoadon_benhnhan", "hoa_don", "(benh_nhan_id, trang_thai)"),
    ("idx_hoadon_pk", "hoa_don", "(phieu_kham_id)"),
    ("idx_chitiethoadon_hd", "chi_tiet_hoa_don", "(hoa_don_id)"),
    
    # 6. Đánh giá phản hồi và thông báo
    ("idx_phanhoi_bn", "phan_hoi", "(benh_nhan_id)"),
    ("idx_phanhoi_pk", "phan_hoi", "(phieu_kham_id)"),
    ("idx_thongbao_user", "thong_bao", "(tai_khoan_id, thoi_gian_tao DESC)"),
    
    # 7. Lịch hẹn
    ("idx_lichhen_bn", "lich_hen", "(benh_nhan_id, ngay_hen)"),
    ("idx_lichhen_bs", "lich_hen", "(bac_si_id, ngay_hen)"),
    ("idx_lichhen_khoa", "lich_hen", "(chuyen_khoa_id, ngay_hen)"),
    
    # 8. Lịch làm việc và ca trực
    ("idx_lichlamviec_lookup", "lich_lam_viec", "(ngay_lam, ca_lam, bac_si_id, nhan_vien_id, trang_thai_duyet)"),
    ("idx_lichlamviec_nhanvien", "lich_lam_viec", "(nhan_vien_id, ngay_lam)"),
    ("idx_lichlamviec_bacsi", "lich_lam_viec", "(bac_si_id, ngay_lam)")
]

created_count = 0
for idx_name, tbl_name, cols in indexes:
    try:
        sql = f"""
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = '{idx_name}' AND object_id = OBJECT_ID('{tbl_name}'))
        BEGIN
            CREATE NONCLUSTERED INDEX {idx_name} ON {tbl_name} {cols};
        END
        """
        t0 = time.time()
        cur.execute(sql)
        conn.commit()
        created_count += 1
        print(f"Index {idx_name:<30} on {tbl_name:<20} OK ({(time.time()-t0)*1000:.1f} ms)")
    except Exception as e:
        print(f"Error creating {idx_name} on {tbl_name}: {e}")

conn.close()
print(f"\nĐã kiểm tra và tạo thành công {created_count} chỉ mục (Indexes) trên SQL Server!")
