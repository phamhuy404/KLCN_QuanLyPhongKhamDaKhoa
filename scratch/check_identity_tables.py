import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;')
c = conn.cursor()

tables = [
    'vai_tro', 'chuyen_khoa', 'phong_kham', 'dich_vu', 'thuoc',
    'tai_khoan', 'nhan_vien', 'bac_si', 'benh_nhan', 'lich_lam_viec',
    'chi_so_sinh_ton', 'lich_hen', 'phieu_kham', 'phieu_chi_dinh', 'chi_tiet_chi_dinh',
    'don_thuoc', 'chi_tiet_don_thuoc', 'hoa_don', 'chi_tiet_hoa_don',
    'thong_bao', 'phan_hoi', 'hom_thu_gop_y', 'banner', 'bai_viet', 'audit_log'
]

for t in tables:
    c.execute(f"SELECT COLUMNPROPERTY(OBJECT_ID('{t}'), 'id', 'IsIdentity')")
    row = c.fetchone()
    is_ident = row[0] if row else None
    print(f"{t}: has_identity_id = {is_ident}")

conn.close()
