import os
import sys

# Script tự động đồng bộ kịch bản T-SQL hoàn chỉnh cho cosodulieu.sql
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from werkzeug.security import generate_password_hash

def export_sql():
    sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cosodulieu.sql')
    
    # Đọc lại dữ liệu chuẩn từ SQL Server để sinh file .sql hoàn chỉnh
    import config
    cfg = config.SQLSERVER_CONFIG
    conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE={cfg['database']};Trusted_Connection=yes;"
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()

    content = []
    content.append("-- CO SO DU LIEU HE THONG QUAN LY PHONG KHAM DA KHOA (H2T HEALTHCARE HIS / EMR)")
    content.append("-- PHIEN BAN CHUAN 100%: MICROSOFT SQL SERVER 2016 / 2019 / 2022 (T-SQL)")
    content.append("")
    content.append("IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'quan_ly_phong_kham')")
    content.append("BEGIN")
    content.append("    CREATE DATABASE quan_ly_phong_kham;")
    content.append("END")
    content.append("GO")
    content.append("")
    content.append("USE quan_ly_phong_kham;")
    content.append("GO")
    content.append("")
    content.append("SET ANSI_NULLS ON;")
    content.append("SET QUOTED_IDENTIFIER ON;")
    content.append("GO")
    content.append("")
    content.append("-- XOA KHOA NGOAI VA BANG CU")
    content.append("DECLARE @sql NVARCHAR(MAX) = N'';")
    content.append("SELECT @sql += N'ALTER TABLE ' + QUOTENAME(s.name) + N'.' + QUOTENAME(t.name) + N' DROP CONSTRAINT ' + QUOTENAME(f.name) + N';'")
    content.append("FROM sys.foreign_keys f")
    content.append("INNER JOIN sys.tables t ON f.parent_object_id = t.object_id")
    content.append("INNER JOIN sys.schemas s ON t.schema_id = s.schema_id;")
    content.append("EXEC sp_executesql @sql;")
    content.append("GO")
    content.append("")

    tables = [
        'chi_tiet_hoa_don', 'hoa_don', 'chi_tiet_don_thuoc', 'don_thuoc',
        'chi_tiet_chi_dinh', 'phieu_chi_dinh', 'chi_so_sinh_ton', 'phieu_kham',
        'lich_hen', 'lich_lam_viec', 'phan_hoi', 'hom_thu_gop_y', 'thong_bao',
        'lich_su_nhac_nho', 'lich_su_sao_luu', 'banner', 'audit_log', 'bai_viet',
        'benh_nhan', 'bac_si', 'nhan_vien', 'tai_khoan', 'thuoc', 'dich_vu',
        'phong_kham', 'chuyen_khoa', 'vai_tro'
    ]
    for t in tables:
        content.append(f"IF OBJECT_ID('{t}', 'U') IS NOT NULL DROP TABLE {t};")
    content.append("GO")
    content.append("")

    # Schema definition
    ddl = """-- CAU TRUC BANG DU LIEU
CREATE TABLE vai_tro (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_vai_tro NVARCHAR(30) NOT NULL UNIQUE,
    ten_vai_tro NVARCHAR(50) NOT NULL,
    mo_ta NVARCHAR(255)
);

CREATE TABLE chuyen_khoa (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_khoa NVARCHAR(20) NOT NULL UNIQUE,
    ten_khoa NVARCHAR(100) NOT NULL,
    mo_ta NVARCHAR(MAX),
    icon NVARCHAR(100) DEFAULT 'fa-stethoscope',
    gia_kham_mac_dinh DECIMAL(12, 2) DEFAULT 150000.00,
    trang_thai BIT DEFAULT 1
);

CREATE TABLE phong_kham (
    id INT IDENTITY(1,1) PRIMARY KEY,
    chuyen_khoa_id INT NOT NULL,
    ma_phong NVARCHAR(20) NOT NULL UNIQUE,
    ten_phong NVARCHAR(100) NOT NULL,
    vi_tri_tang NVARCHAR(50) DEFAULT N'Tầng 1',
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

CREATE TABLE dich_vu (
    id INT IDENTITY(1,1) PRIMARY KEY,
    chuyen_khoa_id INT NULL,
    ma_dich_vu NVARCHAR(30) NOT NULL UNIQUE,
    ten_dich_vu NVARCHAR(255) NOT NULL,
    loai_dich_vu NVARCHAR(50) DEFAULT N'Khám bệnh',
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    bhyt_chi_tra_pt INT DEFAULT 0,
    mo_ta NVARCHAR(255),
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

CREATE TABLE thuoc (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_thuoc NVARCHAR(30) NOT NULL UNIQUE,
    ten_thuoc NVARCHAR(255) NOT NULL,
    hoat_chat NVARCHAR(255),
    ham_luong NVARCHAR(100),
    don_vi_tinh NVARCHAR(50) NOT NULL,
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    so_luong_ton INT DEFAULT 0,
    ton_kho_toi_thieu INT DEFAULT 20,
    hang_san_xuat NVARCHAR(150),
    nuoc_san_xuat NVARCHAR(100),
    huong_dan_su_dung NVARCHAR(255),
    trang_thai BIT DEFAULT 1
);

CREATE TABLE tai_khoan (
    id INT IDENTITY(1,1) PRIMARY KEY,
    vai_tro_id INT NOT NULL,
    username NVARCHAR(100) NOT NULL UNIQUE,
    password NVARCHAR(255) NOT NULL,
    email NVARCHAR(100),
    sdt NVARCHAR(15),
    trang_thai BIT DEFAULT 1,
    da_hoan_thien_ho_so BIT DEFAULT 0,
    ngay_tao DATETIME DEFAULT GETDATE(),
    lan_dang_nhap_cuoi DATETIME NULL,
    FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id)
);

CREATE TABLE nhan_vien (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tai_khoan_id INT NOT NULL UNIQUE,
    ma_nhan_vien NVARCHAR(20) NOT NULL UNIQUE,
    ho_ten NVARCHAR(100) NOT NULL,
    gioi_tinh BIT DEFAULT 1,
    ngay_sinh DATE NULL,
    sdt NVARCHAR(15) NOT NULL UNIQUE,
    email NVARCHAR(100),
    cccd NVARCHAR(20) UNIQUE,
    dia_chi NVARCHAR(255),
    chuc_vu NVARCHAR(100) NOT NULL,
    ngay_vao_lam DATE DEFAULT CAST(GETDATE() AS DATE),
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
);

CREATE TABLE bac_si (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nhan_vien_id INT NOT NULL UNIQUE,
    chuyen_khoa_id INT NOT NULL,
    phong_kham_chinh_id INT NULL,
    hoc_vi NVARCHAR(50) DEFAULT N'Bác sĩ',
    kinh_nghiem NVARCHAR(MAX),
    avatar NVARCHAR(255) DEFAULT 'default_doctor.png',
    gia_kham DECIMAL(12, 2) DEFAULT 150000.00,
    trang_thai_lam_viec NVARCHAR(50) DEFAULT N'Đang làm việc',
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id) ON DELETE CASCADE,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
    FOREIGN KEY (phong_kham_chinh_id) REFERENCES phong_kham(id)
);

CREATE TABLE benh_nhan (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tai_khoan_id INT NULL UNIQUE,
    ma_benh_nhan NVARCHAR(20) NOT NULL UNIQUE,
    ho_ten NVARCHAR(100) NOT NULL,
    ngay_sinh DATE NOT NULL,
    gioi_tinh NVARCHAR(10) NOT NULL DEFAULT N'Nam',
    sdt NVARCHAR(15) NOT NULL,
    email NVARCHAR(100),
    cccd NVARCHAR(20),
    bhyt NVARCHAR(30),
    dia_chi NVARCHAR(255),
    nhom_mau NVARCHAR(10) DEFAULT N'Chưa rõ',
    ghi_chu_nhom_mau NVARCHAR(255) NULL,
    avatar NVARCHAR(500) NULL,
    di_ung NVARCHAR(MAX),
    tien_su_benh NVARCHAR(MAX),
    tien_su_gia_dinh NVARCHAR(MAX),
    nguoi_than_ho_ten NVARCHAR(100),
    nguoi_than_sdt NVARCHAR(15),
    nguoi_than_quan_he NVARCHAR(50),
    co_tai_khoan BIT DEFAULT 0,
    ngay_tao DATE DEFAULT CAST(GETDATE() AS DATE),
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE SET NULL
);

CREATE TABLE chi_so_sinh_ton (
    id INT IDENTITY(1,1) PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    mach NVARCHAR(20) DEFAULT N'75 lần/phút',
    nhiet_do NVARCHAR(20) DEFAULT N'36.8 °C',
    huyet_ap NVARCHAR(20) DEFAULT N'120/80 mmHg',
    spo2 NVARCHAR(20) DEFAULT N'99 %',
    nhip_tho NVARCHAR(20) DEFAULT N'18 lần/phút',
    chieu_cao NVARCHAR(20) DEFAULT N'170 cm',
    can_nang NVARCHAR(20) DEFAULT N'65 kg',
    bmi NVARCHAR(50) DEFAULT N'22.5 (Bình thường)',
    thoi_gian_do DATETIME DEFAULT GETDATE(),
    ghi_chu NVARCHAR(255),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE
);

CREATE TABLE lich_lam_viec (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nhan_vien_id INT NULL,
    bac_si_id INT NULL,
    phong_kham_id INT NULL,
    ngay_lam DATE NOT NULL,
    ca_lam TINYINT NOT NULL,
    gio_bat_dau TIME DEFAULT '07:00:00',
    gio_ket_thuc TIME DEFAULT '11:30:00',
    so_luong_kham_toi_da INT DEFAULT 20,
    so_luong_da_dang_ky INT DEFAULT 0,
    trang_thai BIT DEFAULT 1,
    trang_thai_duyet NVARCHAR(50) DEFAULT 'DA_DUYET',
    ly_do_huy NVARCHAR(MAX) NULL,
    nguoi_duyet_id INT NULL,
    ngay_duyet DATETIME NULL,
    ghi_chu NVARCHAR(MAX) NULL,
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
);

CREATE TABLE lich_hen (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_lich_hen NVARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NULL,
    chuyen_khoa_id INT NOT NULL,
    phong_kham_id INT NULL,
    ngay_hen DATE NOT NULL,
    gio_hen TIME NOT NULL,
    ly_do_kham NVARCHAR(MAX),
    loai_lich_hen TINYINT DEFAULT 1,
    trang_thai NVARCHAR(50) DEFAULT N'Chờ xác nhận',
    ngay_dat DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
);

CREATE TABLE phieu_kham (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_phieu NVARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NULL,
    phong_kham_id INT NOT NULL,
    lich_hen_id INT NULL,
    thoi_gian_kham DATETIME DEFAULT GETDATE(),
    ly_do_kham NVARCHAR(MAX),
    trieu_chung NVARCHAR(MAX),
    chan_doan_so_bo NVARCHAR(MAX),
    chan_doan_icd NVARCHAR(255),
    huong_dieu_tri NVARCHAR(MAX),
    loi_dan NVARCHAR(MAX),
    ngay_tai_kham DATE NULL,
    trang_thai NVARCHAR(50) DEFAULT N'Hoàn thành',
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id),
    FOREIGN KEY (lich_hen_id) REFERENCES lich_hen(id)
);

CREATE TABLE phieu_chi_dinh (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_chi_dinh NVARCHAR(30) NOT NULL UNIQUE,
    phieu_kham_id INT NOT NULL,
    bac_si_id INT NULL,
    thoi_gian_chi_dinh DATETIME DEFAULT GETDATE(),
    ghi_chu NVARCHAR(255),
    trang_thai NVARCHAR(50) DEFAULT N'Hoàn thành',
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
);

CREATE TABLE chi_tiet_chi_dinh (
    id INT IDENTITY(1,1) PRIMARY KEY,
    phieu_chi_dinh_id INT NOT NULL,
    dich_vu_id INT NOT NULL,
    ket_qua NVARCHAR(MAX),
    file_ket_qua NVARCHAR(255),
    ktv_thuc_hien NVARCHAR(100),
    thoi_gian_thuc_hien DATETIME,
    trang_thai NVARCHAR(50) DEFAULT N'Hoàn thành',
    bac_si_duyet NVARCHAR(100) NULL,
    thoi_gian_duyet DATETIME NULL,
    ghi_chu_duyet NVARCHAR(MAX) NULL,
    nguoi_nhap NVARCHAR(100) NULL,
    FOREIGN KEY (phieu_chi_dinh_id) REFERENCES phieu_chi_dinh(id) ON DELETE CASCADE,
    FOREIGN KEY (dich_vu_id) REFERENCES dich_vu(id)
);

CREATE TABLE don_thuoc (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_don_thuoc NVARCHAR(30) NOT NULL UNIQUE,
    phieu_kham_id INT NOT NULL,
    bac_si_id INT NULL,
    thoi_gian_ke DATETIME DEFAULT GETDATE(),
    loi_dan NVARCHAR(MAX),
    trang_thai NVARCHAR(50) DEFAULT N'Đã cấp thuốc',
    ly_do_huy NVARCHAR(MAX) NULL,
    nguoi_huy NVARCHAR(100) NULL,
    thoi_gian_huy DATETIME NULL,
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
);

CREATE TABLE chi_tiet_don_thuoc (
    id INT IDENTITY(1,1) PRIMARY KEY,
    don_thuoc_id INT NOT NULL,
    thuoc_id INT NOT NULL,
    so_luong INT NOT NULL DEFAULT 1,
    lieu_dung NVARCHAR(100),
    cach_dung NVARCHAR(255),
    FOREIGN KEY (don_thuoc_id) REFERENCES don_thuoc(id) ON DELETE CASCADE,
    FOREIGN KEY (thuoc_id) REFERENCES thuoc(id)
);

CREATE TABLE hoa_don (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_hoa_don NVARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NULL,
    tong_tien DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    tien_bhyt DECIMAL(12, 2) DEFAULT 0.00,
    giam_gia DECIMAL(12, 2) DEFAULT 0.00,
    thanh_tien DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    hinh_thuc_thanh_toan NVARCHAR(50) DEFAULT N'Tiền mặt',
    trang_thai NVARCHAR(50) DEFAULT N'Đã thanh toán',
    thoi_gian_thanh_toan DATETIME DEFAULT GETDATE(),
    nhan_vien_thu NVARCHAR(100),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE chi_tiet_hoa_don (
    id INT IDENTITY(1,1) PRIMARY KEY,
    hoa_don_id INT NOT NULL,
    loai_khoan_thu NVARCHAR(50) NOT NULL,
    ten_khoan_thu NVARCHAR(255) NOT NULL,
    tham_chieu_id INT NULL,
    so_luong INT DEFAULT 1,
    don_gia DECIMAL(12, 2) DEFAULT 0.00,
    thanh_tien DECIMAL(12, 2) DEFAULT 0.00,
    FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(id) ON DELETE CASCADE
);

CREATE TABLE thong_bao (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tai_khoan_id INT NOT NULL,
    tieu_de NVARCHAR(200) NOT NULL,
    noi_dung NVARCHAR(MAX) NOT NULL,
    loai_thong_bao NVARCHAR(50) DEFAULT N'Hệ thống',
    lien_ket NVARCHAR(255) NULL,
    da_doc BIT DEFAULT 0,
    thoi_gian_tao DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE CASCADE
);

CREATE TABLE phan_hoi (
    id INT IDENTITY(1,1) PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NULL,
    chu_de NVARCHAR(100) DEFAULT N'Dịch vụ khám bệnh',
    diem_danh_gia TINYINT NOT NULL CHECK (diem_danh_gia BETWEEN 1 AND 5),
    noi_dung NVARCHAR(MAX),
    trang_thai NVARCHAR(50) DEFAULT N'Chờ tiếp nhận',
    tra_loi NVARCHAR(MAX) NULL,
    ngay_tra_loi DATETIME NULL,
    nguoi_tra_loi NVARCHAR(100) NULL,
    thoi_gian DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE,
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE hom_thu_gop_y (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ho_ten NVARCHAR(100) NOT NULL,
    email NVARCHAR(100),
    sdt NVARCHAR(15),
    chu_de NVARCHAR(200),
    noi_dung NVARCHAR(MAX) NOT NULL,
    ngay_gui DATETIME DEFAULT GETDATE(),
    trang_thai NVARCHAR(50) DEFAULT N'Chưa xử lý'
);

CREATE TABLE lich_su_nhac_nho (
    id INT IDENTITY(1,1) PRIMARY KEY,
    lich_hen_id INT NULL,
    phieu_kham_id INT NULL,
    benh_nhan_id INT NULL,
    loai_nhac NVARCHAR(50) NOT NULL,
    ngay_nhac DATE NULL,
    kenh_gui NVARCHAR(20) DEFAULT 'IN_APP',
    trang_thai NVARCHAR(50) DEFAULT 'THANH_CONG',
    loi_gui NVARCHAR(MAX) NULL,
    thoi_gian_gui DATETIME DEFAULT GETDATE()
);

CREATE TABLE lich_su_sao_luu (
    id INT IDENTITY(1,1) PRIMARY KEY,
    loai_thao_tac NVARCHAR(20) NOT NULL,
    ten_tap_tin NVARCHAR(255) NOT NULL,
    duong_dan NVARCHAR(500) NULL,
    loai_csdl NVARCHAR(50) NOT NULL,
    dung_luong BIGINT DEFAULT 0,
    nguoi_thuc_hien NVARCHAR(100) NULL,
    trang_thai NVARCHAR(50) DEFAULT 'SUCCESS',
    ghi_chu NVARCHAR(MAX) NULL,
    thoi_gian DATETIME DEFAULT GETDATE()
);

CREATE TABLE bai_viet (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tac_gia_id INT NULL,
    tieu_de NVARCHAR(255) NOT NULL,
    slug NVARCHAR(255) NOT NULL UNIQUE,
    danh_muc NVARCHAR(100) DEFAULT N'Cẩm Nang Y Tế',
    tom_tat NVARCHAR(MAX),
    noi_dung NVARCHAR(MAX),
    hinh_anh NVARCHAR(255),
    luot_xem INT DEFAULT 0,
    ngay_dang DATETIME DEFAULT GETDATE(),
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (tac_gia_id) REFERENCES nhan_vien(id)
);

CREATE TABLE banner (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tieu_de NVARCHAR(255) NOT NULL,
    phu_de NVARCHAR(255) NULL,
    mo_ta NVARCHAR(MAX) NULL,
    hinh_anh NVARCHAR(500) NOT NULL,
    link_lien_ket NVARCHAR(255) DEFAULT '/booking',
    text_nut NVARCHAR(50) DEFAULT N'Đăng ký khám ngay',
    thu_tu INT DEFAULT 0,
    trang_thai BIT DEFAULT 1,
    ngay_tao DATETIME DEFAULT GETDATE()
);

CREATE TABLE audit_log (
    id INT IDENTITY(1,1) PRIMARY KEY,
    table_name NVARCHAR(50) NOT NULL,
    row_id INT NOT NULL,
    action NVARCHAR(50) NOT NULL,
    performed_by INT NULL,
    performed_by_name NVARCHAR(100) NULL,
    performed_at DATETIME DEFAULT GETDATE(),
    reason NVARCHAR(MAX) NULL,
    before_json NVARCHAR(MAX) NULL,
    after_json NVARCHAR(MAX) NULL
);
GO

-- TAO CHI MUC (INDEXES)
CREATE INDEX idx_benhnhan_sdt ON benh_nhan(sdt);
CREATE INDEX idx_benhnhan_cccd ON benh_nhan(cccd);
CREATE INDEX idx_benhnhan_ma ON benh_nhan(ma_benh_nhan);
CREATE INDEX idx_lichhen_ngay ON lich_hen(ngay_hen);
CREATE INDEX idx_lichhen_trangthai ON lich_hen(trang_thai);
CREATE INDEX idx_phieukham_ngay ON phieu_kham(thoi_gian_kham);
CREATE INDEX idx_hoadon_ngay ON hoa_don(thoi_gian_thanh_toan);
CREATE INDEX idx_lichlamviec_ngay ON lich_lam_viec(ngay_lam);
GO
"""
    content.append(ddl)

    # Function để escape chuỗi SQL Server
    def esc(val):
        if val is None:
            return "NULL"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, bool):
            return "1" if val else "0"
        s = str(val).replace("'", "''")
        return f"N'{s}'"

    # Export DML cho tung bang
    export_tables = [
        'vai_tro', 'chuyen_khoa', 'phong_kham', 'dich_vu', 'thuoc',
        'tai_khoan', 'nhan_vien', 'bac_si', 'benh_nhan', 'chi_so_sinh_ton',
        'lich_hen', 'phieu_kham', 'phieu_chi_dinh', 'chi_tiet_chi_dinh',
        'don_thuoc', 'chi_tiet_don_thuoc', 'hoa_don', 'chi_tiet_hoa_don',
        'thong_bao', 'banner', 'bai_viet'
    ]

    for tbl in export_tables:
        cur.execute(f"SELECT * FROM {tbl} ORDER BY id")
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        if not rows:
            continue
        content.append(f"-- DU LIEU: {tbl}")
        content.append(f"SET IDENTITY_INSERT {tbl} ON;")
        for r in rows:
            vals = [esc(v) for v in r]
            col_str = ", ".join(cols)
            val_str = ", ".join(vals)
            content.append(f"INSERT INTO {tbl} ({col_str}) VALUES ({val_str});")
        content.append(f"SET IDENTITY_INSERT {tbl} OFF;")
        content.append("GO\n")

    conn.close()

    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))
    print(f"Xuat thanh cong cosodulieu.sql ({len(content)} dong)!")

if __name__ == '__main__':
    export_sql()
