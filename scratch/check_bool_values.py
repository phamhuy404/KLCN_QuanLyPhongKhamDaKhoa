import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;')
c = conn.cursor()

tables = [
    'vai_tro', 'chuyen_khoa', 'phong_kham', 'dich_vu', 'thuoc',
    'tai_khoan', 'nhan_vien', 'bac_si', 'benh_nhan', 'lich_lam_viec',
    'chi_so_sinh_ton', 'lich_hen', 'phieu_kham', 'phieu_chi_dinh', 'chi_tiet_chi_dinh',
    'don_thuoc', 'chi_tiet_don_thuoc', 'hoa_don', 'chi_tiet_hoa_don',
    'thong_bao', 'phan_hoi', 'hom_thu_gop_y', 'banner', 'bai_viet'
]

for t in tables:
    c.execute(f"SELECT * FROM {t}")
    cols = [col[0] for col in c.description]
    for row in c.fetchall():
        for i, val in enumerate(row):
            if val is True or val is False:
                print(f"Table {t}, col {cols[i]}: native bool {val}")
                break
        else:
            continue
        break

conn.close()
