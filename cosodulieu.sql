-- CO SO DU LIEU HE THONG QUAN LY PHONG KHAM DA KHOA (H2T HEALTHCARE HIS / EMR)
-- PHIEN BAN CHUAN 100%: MICROSOFT SQL SERVER 2016 / 2019 / 2022 (T-SQL)

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'quan_ly_phong_kham')
BEGIN
    CREATE DATABASE quan_ly_phong_kham;
END
GO

USE quan_ly_phong_kham;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- XOA KHOA NGOAI VA BANG CU
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(s.name) + N'.' + QUOTENAME(t.name) + N' DROP CONSTRAINT ' + QUOTENAME(f.name) + N';'
FROM sys.foreign_keys f
INNER JOIN sys.tables t ON f.parent_object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id;
EXEC sp_executesql @sql;
GO

IF OBJECT_ID('chi_tiet_hoa_don', 'U') IS NOT NULL DROP TABLE chi_tiet_hoa_don;
IF OBJECT_ID('hoa_don', 'U') IS NOT NULL DROP TABLE hoa_don;
IF OBJECT_ID('chi_tiet_don_thuoc', 'U') IS NOT NULL DROP TABLE chi_tiet_don_thuoc;
IF OBJECT_ID('don_thuoc', 'U') IS NOT NULL DROP TABLE don_thuoc;
IF OBJECT_ID('chi_tiet_chi_dinh', 'U') IS NOT NULL DROP TABLE chi_tiet_chi_dinh;
IF OBJECT_ID('phieu_chi_dinh', 'U') IS NOT NULL DROP TABLE phieu_chi_dinh;
IF OBJECT_ID('chi_so_sinh_ton', 'U') IS NOT NULL DROP TABLE chi_so_sinh_ton;
IF OBJECT_ID('phieu_kham', 'U') IS NOT NULL DROP TABLE phieu_kham;
IF OBJECT_ID('lich_hen', 'U') IS NOT NULL DROP TABLE lich_hen;
IF OBJECT_ID('lich_lam_viec', 'U') IS NOT NULL DROP TABLE lich_lam_viec;
IF OBJECT_ID('phan_hoi', 'U') IS NOT NULL DROP TABLE phan_hoi;
IF OBJECT_ID('hom_thu_gop_y', 'U') IS NOT NULL DROP TABLE hom_thu_gop_y;
IF OBJECT_ID('thong_bao', 'U') IS NOT NULL DROP TABLE thong_bao;
IF OBJECT_ID('lich_su_nhac_nho', 'U') IS NOT NULL DROP TABLE lich_su_nhac_nho;
IF OBJECT_ID('lich_su_sao_luu', 'U') IS NOT NULL DROP TABLE lich_su_sao_luu;
IF OBJECT_ID('banner', 'U') IS NOT NULL DROP TABLE banner;
IF OBJECT_ID('audit_log', 'U') IS NOT NULL DROP TABLE audit_log;
IF OBJECT_ID('bai_viet', 'U') IS NOT NULL DROP TABLE bai_viet;
IF OBJECT_ID('benh_nhan', 'U') IS NOT NULL DROP TABLE benh_nhan;
IF OBJECT_ID('bac_si', 'U') IS NOT NULL DROP TABLE bac_si;
IF OBJECT_ID('nhan_vien', 'U') IS NOT NULL DROP TABLE nhan_vien;
IF OBJECT_ID('tai_khoan', 'U') IS NOT NULL DROP TABLE tai_khoan;
IF OBJECT_ID('thuoc', 'U') IS NOT NULL DROP TABLE thuoc;
IF OBJECT_ID('dich_vu', 'U') IS NOT NULL DROP TABLE dich_vu;
IF OBJECT_ID('phong_kham', 'U') IS NOT NULL DROP TABLE phong_kham;
IF OBJECT_ID('chuyen_khoa', 'U') IS NOT NULL DROP TABLE chuyen_khoa;
IF OBJECT_ID('vai_tro', 'U') IS NOT NULL DROP TABLE vai_tro;
GO

-- CAU TRUC BANG DU LIEU
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

-- DU LIEU: vai_tro
SET IDENTITY_INSERT vai_tro ON;
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (1, N'ADMIN', N'Quản trị viên', N'Toàn quyền cấu hình và quản trị hệ thống phòng khám');
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (2, N'LETAN', N'Nhân viên lễ tân / Thu ngân', N'Tiếp đón bệnh nhân, sắp xếp lịch hẹn, thu ngân viện phí');
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (3, N'BACSI', N'Bác sĩ chuyên khoa', N'Khám bệnh, chẩn đoán, kê đơn thuốc và chỉ định cận lâm sàng');
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (4, N'DUOCSI', N'Dược sĩ / Thủ kho dược', N'Quản lý kho thuốc, cấp phát thuốc theo toa');
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (5, N'KTV', N'Kỹ thuật viên cận lâm sàng', N'Thực hiện xét nghiệm, X-quang, chẩn đoán hình ảnh');
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (6, N'BENHNHAN', N'Bệnh nhân', N'Khách hàng sử dụng cổng thông tin y tế bệnh nhân');
SET IDENTITY_INSERT vai_tro OFF;
GO

-- DU LIEU: chuyen_khoa
SET IDENTITY_INSERT chuyen_khoa ON;
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (1, N'KHOA_NOI', N'Khoa Nội Tổng Quát', N'Khám, chẩn đoán và điều trị bệnh lý tim mạch, tiêu hóa, hô hấp, cơ xương khớp, thần kinh', N'fa-stethoscope', N'150000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (2, N'KHOA_NGOAI', N'Khoa Ngoại Tổng Quát', N'Khám và điều trị ngoại khoa, chấn thương chỉnh hình, phẫu thuật tiêu hóa, tiểu phẫu vết thương', N'fa-syringe', N'150000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (3, N'KHOA_NHI', N'Khoa Nhi', N'Chăm sóc và điều trị chuyên sâu bệnh lý trẻ em, tư vấn dinh dưỡng và theo dõi phát triển toàn diện', N'fa-baby', N'120000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (4, N'KHOA_RHM', N'Khoa Răng Hàm Mặt', N'Nha khoa tổng quát, phục hình răng sứ, niềng răng thẩm mỹ, cấy ghép implant, nhổ răng khôn không đau', N'fa-tooth', N'150000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (5, N'KHOA_SAN', N'Khoa Sản - Phụ Khoa', N'Quản lý thai kỳ, siêu âm 4D hình thái học, tầm soát ung thư cổ tử cung và điều trị bệnh phụ khoa', N'fa-person-pregnant', N'180000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (6, N'KHOA_TMH', N'Khoa Tai Mũi Họng', N'Nội soi tai mũi họng dải tần hẹp, điều trị viêm xoang, viêm tai giữa, khàn tiếng và amidan', N'fa-head-side-cough', N'150000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (7, N'KHOA_MAT', N'Khoa Mắt', N'Đo tật khúc xạ cận - viễn - loạn thị, kiểm soát cận thị Ortho-K, điều trị cườm khô, cườm nước và đáy mắt', N'fa-eye', N'150000.00', True);
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (8, N'KHOA_CLS', N'Khoa Cận Lâm Sàng & CĐHA', N'Trung tâm xét nghiệm hóa sinh - huyết học - vi sinh tự động và chẩn đoán hình ảnh kỹ thuật số', N'fa-vial', N'100000.00', True);
SET IDENTITY_INSERT chuyen_khoa OFF;
GO

-- DU LIEU: phong_kham
SET IDENTITY_INSERT phong_kham ON;
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (1, 1, N'PK101', N'Phòng Khám Nội 1', N'Tầng 1 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (2, 1, N'PK102', N'Phòng Khám Nội 2', N'Tầng 1 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (3, 1, N'PK103', N'Phòng Khám Nội 3', N'Tầng 1 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (4, 1, N'PK104', N'Phòng Khám Nội 4', N'Tầng 1 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (5, 1, N'PK105', N'Phòng Khám Nội 5', N'Tầng 1 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (6, 2, N'PK201', N'Phòng Khám Ngoại & Tiểu Phẫu 1', N'Tầng 1 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (7, 2, N'PK202', N'Phòng Khám Ngoại & Tiểu Phẫu 2', N'Tầng 1 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (8, 2, N'PK203', N'Phòng Khám Ngoại & Tiểu Phẫu 3', N'Tầng 1 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (9, 2, N'PK204', N'Phòng Khám Ngoại & Tiểu Phẫu 4', N'Tầng 1 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (10, 2, N'PK205', N'Phòng Khám Ngoại & Tiểu Phẫu 5', N'Tầng 1 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (11, 3, N'PK301', N'Phòng Khám Nhi Khoa 1', N'Tầng 2 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (12, 3, N'PK302', N'Phòng Khám Nhi Khoa 2', N'Tầng 2 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (13, 3, N'PK303', N'Phòng Khám Nhi Khoa 3', N'Tầng 2 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (14, 3, N'PK304', N'Phòng Khám Nhi Khoa 4', N'Tầng 2 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (15, 3, N'PK305', N'Phòng Khám Nhi Khoa 5', N'Tầng 2 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (16, 4, N'PK401', N'Phòng Khám Nha Khoa Kỹ Thuật Cao 1', N'Tầng 2 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (17, 4, N'PK402', N'Phòng Khám Nha Khoa Kỹ Thuật Cao 2', N'Tầng 2 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (18, 4, N'PK403', N'Phòng Khám Nha Khoa Kỹ Thuật Cao 3', N'Tầng 2 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (19, 4, N'PK404', N'Phòng Khám Nha Khoa Kỹ Thuật Cao 4', N'Tầng 2 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (20, 4, N'PK405', N'Phòng Khám Nha Khoa Kỹ Thuật Cao 5', N'Tầng 2 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (21, 5, N'PK501', N'Phòng Khám Sản Phụ Khoa 1', N'Tầng 2 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (22, 5, N'PK502', N'Phòng Khám Sản Phụ Khoa 2', N'Tầng 2 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (23, 5, N'PK503', N'Phòng Khám Sản Phụ Khoa 3', N'Tầng 2 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (24, 5, N'PK504', N'Phòng Khám Sản Phụ Khoa 4', N'Tầng 2 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (25, 5, N'PK505', N'Phòng Khám Sản Phụ Khoa 5', N'Tầng 2 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (26, 6, N'PK601', N'Phòng Khám Tai Mũi Họng & Nội Soi 1', N'Tầng 3 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (27, 6, N'PK602', N'Phòng Khám Tai Mũi Họng & Nội Soi 2', N'Tầng 3 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (28, 6, N'PK603', N'Phòng Khám Tai Mũi Họng & Nội Soi 3', N'Tầng 3 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (29, 6, N'PK604', N'Phòng Khám Tai Mũi Họng & Nội Soi 4', N'Tầng 3 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (30, 6, N'PK605', N'Phòng Khám Tai Mũi Họng & Nội Soi 5', N'Tầng 3 - Khu A', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (31, 7, N'PK701', N'Phòng Khám Mắt & Khúc Xạ 1', N'Tầng 3 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (32, 7, N'PK702', N'Phòng Khám Mắt & Khúc Xạ 2', N'Tầng 3 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (33, 7, N'PK703', N'Phòng Khám Mắt & Khúc Xạ 3', N'Tầng 3 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (34, 7, N'PK704', N'Phòng Khám Mắt & Khúc Xạ 4', N'Tầng 3 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (35, 7, N'PK705', N'Phòng Khám Mắt & Khúc Xạ 5', N'Tầng 3 - Khu B', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (36, 8, N'CLS_XN01', N'Phòng Xét Nghiệm Huyết Học - Hóa Sinh Tự Động', N'Tầng 1 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (37, 8, N'CLS_XQ01', N'Phòng Chụp X-Quang Kỹ Thuật Số DR', N'Tầng 1 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (38, 8, N'CLS_SA01', N'Phòng Siêu Âm Màu 4D & Doppler Tim Mạch', N'Tầng 1 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (39, 8, N'CLS_TD01', N'Phòng Thăm Dò Chức Năng & Điện Tim ECG', N'Tầng 1 - Khu C', True);
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (40, 8, N'CLS_VS01', N'Phòng Xét Nghiệm Vi Sinh - Nước Tiểu', N'Tầng 1 - Khu C', True);
SET IDENTITY_INSERT phong_kham OFF;
GO

-- DU LIEU: dich_vu
SET IDENTITY_INSERT dich_vu ON;
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (1, 1, N'DV_KHAM_NOI', N'Khám Chuyên Khoa Nội Tổng Quát', N'Khám bệnh', N'150000.00', 80, N'Khám và tư vấn toàn diện các bệnh lý nội khoa mạn tính và cấp tính', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (2, 2, N'DV_KHAM_NGOAI', N'Khám Chuyên Khoa Ngoại Tổng Quát', N'Khám bệnh', N'150000.00', 80, N'Khám chấn thương, cơ xương khớp và hội chẩn ngoại khoa', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (3, 3, N'DV_KHAM_NHI', N'Khám Chuyên Khoa Nhi', N'Khám bệnh', N'120000.00', 80, N'Khám sức khỏe trẻ em, dinh dưỡng và tiêm chủng', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (4, 4, N'DV_KHAM_RHM', N'Khám Nha Khoa Tổng Quát', N'Khám bệnh', N'100000.00', 80, N'Khám răng hàm mặt và chụp X-quang răng cận chóp', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (5, 5, N'DV_KHAM_SAN', N'Khám Sản - Phụ Khoa', N'Khám bệnh', N'180000.00', 80, N'Khám thai, tư vấn chăm sóc tiền sản và bệnh phụ khoa', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (6, 6, N'DV_KHAM_TMH', N'Khám Tai Mũi Họng & Nội Soi', N'Khám bệnh', N'150000.00', 80, N'Khám nội soi tầm soát viêm tai, mũi, họng và thanh quản', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (7, 7, N'DV_KHAM_MAT', N'Khám Mắt & Đo Thị Lực Khúc Xạ', N'Khám bệnh', N'150000.00', 80, N'Kiểm tra thị lực bằng máy đo khúc xạ tự động và khám đáy mắt', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (8, 8, N'DV_XN_MAU_CBC', N'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', N'Xét nghiệm', N'150000.00', 80, N'Đánh giá số lượng hồng cầu, bạch cầu, tiểu cầu, tầm soát thiếu máu và nhiễm trùng', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (9, 8, N'DV_XN_DUONG_HUYET', N'Định lượng Glucose máu (Đường huyết lúc đói)', N'Xét nghiệm', N'60000.00', 80, N'Tầm soát và theo dõi bệnh đái tháo đường', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (10, 8, N'DV_XN_MEN_GAN', N'Đo hoạt độ Men gan (AST / ALT)', N'Xét nghiệm', N'100000.00', 80, N'Đánh giá chức năng và tổn thương tế bào gan', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (11, 8, N'DV_XN_THAN_URE', N'Định lượng Ure & Creatinine máu', N'Xét nghiệm', N'100000.00', 80, N'Khảo sát và theo dõi chức năng lọc của cầu thận', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (12, 8, N'DV_XN_NUOCTIEU', N'Tổng phân tích nước tiểu 10 thông số tự động', N'Xét nghiệm', N'80000.00', 80, N'Phát hiện sớm bệnh lý thận, đường tiết niệu và chuyển hóa', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (13, 8, N'DV_XQUANG_PHOI', N'Chụp X-Quang Ngực thẳng kỹ thuật số (DR)', N'Chẩn đoán hình ảnh', N'200000.00', 70, N'Khảo sát nhu mô phổi, phế quản, màng phổi và bóng tim', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (14, 8, N'DV_XQUANG_KHOP', N'Chụp X-Quang Khớp xương (Gối/Háng/Cột sống)', N'Chẩn đoán hình ảnh', N'220000.00', 70, N'Đánh giá thoái hóa khớp, gãy xương và bất thường cấu trúc xương', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (15, 8, N'DV_SIEU_AM_BUNG', N'Siêu âm Doppler màu ổ bụng tổng quát', N'Chẩn đoán hình ảnh', N'250000.00', 50, N'Khảo sát chi tiết gan, mật, tụy, lách, thận, bàng quang và tiền liệt tuyến', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (16, 8, N'DV_SIEU_AM_THAI', N'Siêu âm Doppler màu thai nhi 4D hình thái học', N'Chẩn đoán hình ảnh', N'350000.00', 50, N'Đánh giá sự phát triển và tầm soát dị tật thai nhi', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (17, 8, N'DV_DIEN_TIM_ECG', N'Đo điện tim đồ 12 chuyển đạo (ECG)', N'Thăm dò chức năng', N'120000.00', 70, N'Phát hiện rối loạn nhịp tim, thiếu máu cục bộ cơ tim và phì đại tâm thất', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (18, 4, N'DV_CAO_VOI_RANG', N'Cạo vôi răng & Đánh bóng hai hàm bằng sóng siêu âm', N'Thủ thuật', N'200000.00', 0, N'Loại bỏ mảng bám vi khuẩn, phòng ngừa viêm lợi và nha chu', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (19, 4, N'DV_NHO_RANG_KHON', N'Tiểu phẫu Nhổ răng khôn mọc lệch / ngầm', N'Thủ thuật', N'1200000.00', 0, N'Phẫu thuật nhổ răng khôn bằng máy Piezotome không đau', True);
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (20, 2, N'DV_TIEU_PHAU_VET_THUONG', N'Xử lý và khâu thẩm mỹ vết thương phần mềm', N'Thủ thuật', N'300000.00', 70, N'Sát trùng, cắt lọc mô hoại tử và khâu phục hồi vết thương', True);
SET IDENTITY_INSERT dich_vu OFF;
GO

-- DU LIEU: thuoc
SET IDENTITY_INSERT thuoc ON;
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (1, N'TH_CANH_BAO_1', N'Azithromycin 500mg (Kháng sinh)', N'Azithromycin dihydrat', N'500mg', N'Viên', N'18000.00', 8, N'Pfizer', N'Mỹ', N'Kháng sinh phổ rộng: Uống 1 viên duy nhất/ngày trước ăn 1h', True, 20);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (2, N'TH_CANH_BAO_2', N'Cefpodoxime 200mg', N'Cefpodoxime proxetil', N'200mg', N'Viên', N'22000.00', 12, N'Sanofi', N'Pháp', N'Kháng sinh hô hấp: Uống 1 viên x 2 lần/ngày sau bữa ăn', True, 20);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (3, N'TH_CANH_BAO_3', N'Ventolin Inhaler 100mcg (Xịt hen)', N'Salbutamol sulfat', N'100mcg/liều', N'Chai', N'115000.00', 5, N'GSK', N'Anh', N'Cắt cơn hen phế quản: Xịt 1-2 nhát khi khó thở', True, 15);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (4, N'TH_CANH_BAO_4', N'Nexium Mups 40mg', N'Esomeprazole magnesium', N'40mg', N'Viên', N'24000.00', 14, N'AstraZeneca', N'Thụy Điển', N'Loét dạ dày tá tràng nặng: Uống 1 viên trước ăn sáng', True, 25);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (5, N'TH_CANH_BAO_5', N'Insulin Mixtard 30 Penfill', N'Insulin Human', N'100IU/ml 3ml', N'Bút', N'165000.00', 6, N'Novo Nordisk', N'Đan Mạch', N'Hạ đường huyết: Tiêm dưới da theo hướng dẫn của bác sĩ', True, 20);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (6, N'TH_PARACETAMOL', N'Paracetamol 500mg Hậu Giang', N'Paracetamol', N'500mg', N'Viên', N'2000.00', 5000, N'Dược Hậu Giang', N'Việt Nam', N'Giảm đau, hạ sốt: Uống 1-2 viên mỗi 4-6h khi sốt trên 38.5°C', True, 50);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (7, N'TH_AMOXICILLIN', N'Amoxicillin 500mg', N'Amoxicillin trihydrat', N'500mg', N'Viên', N'3000.00', 2500, N'Imexpharm', N'Việt Nam', N'Kháng sinh nhiễm khuẩn đường hô hấp, tiết niệu: Uống 1 viên x 3 lần/ngày', True, 50);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (8, N'TH_AUGMENTIN', N'Augmentin 1g (Amoxicillin/Clavulanate)', N'Amoxicillin + Acid clavulanic', N'1000mg', N'Viên', N'25000.00', 1500, N'GSK', N'Anh', N'Kháng sinh thế hệ mới: Uống 1 viên vào đầu bữa ăn, ngày 2 lần', True, 30);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (9, N'TH_IBUPROFEN', N'Ibuprofen 400mg Stada', N'Ibuprofen', N'400mg', N'Viên', N'3500.00', 3000, N'Stada', N'Việt Nam', N'Kháng viêm giảm đau cơ xương khớp: Uống 1 viên sau ăn no', True, 40);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (10, N'TH_LORATADIN', N'Loratadin 10mg Pymepharco', N'Loratadin', N'10mg', N'Viên', N'4000.00', 2000, N'Pymepharco', N'Việt Nam', N'Chống dị ứng, viêm mũi dị ứng, mề đay: Uống 1 viên vào buổi tối', True, 30);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (11, N'TH_ESOMEPRAZOLE', N'Esomeprazole 20mg Stada', N'Esomeprazole', N'20mg', N'Viên', N'8000.00', 2800, N'Stada', N'Việt Nam', N'Ức chế tiết acid dạ dày: Uống 1 viên trước bữa ăn sáng 30 phút', True, 30);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (12, N'TH_PHOSPHALUGEL', N'Phosphalugel 20g (Thuốc dạ dày chữ P)', N'Aluminium phosphate', N'20g', N'Gói', N'5500.00', 3500, N'Boehringer Ingelheim', N'Pháp', N'Trung hòa acid dịch vị: Uống 1 gói khi đau hoặc sau ăn 1-2 giờ', True, 50);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (13, N'TH_ENTEROGERMINA', N'Men vi sinh Enterogermina 2 tỷ', N'Bacillus clausii', N'2 tỷ bào tử/5ml', N'Ống', N'9500.00', 1800, N'Sanofi', N'Ý', N'Cân bằng hệ vi sinh đường ruột: Uống 1-2 ống/ngày sau bữa ăn', True, 40);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (14, N'TH_ORESOL', N'Oresol 245 bù nước điện giải', N'Glucose, Natri clorid, Kali clorid', N'245 mOsm/L', N'Gói', N'5000.00', 4000, N'Traphaco', N'Việt Nam', N'Pha chính xác 1 gói với 200ml nước đun sôi để nguội', True, 50);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (15, N'TH_PROSPAN', N'Siro ho thảo dược Prospan 100ml', N'Cao khô lá thường xuân', N'100ml', N'Chai', N'78000.00', 600, N'Engelhard', N'Đức', N'Trị ho viêm phế quản: Uống 5ml x 3 lần/ngày', True, 20);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (16, N'TH_AMLODIPINE', N'Amlodipine 5mg', N'Amlodipine besylate', N'5mg', N'Viên', N'5000.00', 2200, N'Dược Hậu Giang', N'Việt Nam', N'Điều trị tăng huyết áp và đau thắt ngực: Uống 1 viên mỗi sáng', True, 30);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (17, N'TH_METFORMIN', N'Metformin 850mg (Glucophage)', N'Metformin hydroclorid', N'850mg', N'Viên', N'6000.00', 1900, N'Merck', N'Đức', N'Hạ đường huyết đái tháo đường type 2: Uống 1 viên cùng bữa ăn', True, 30);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (18, N'TH_ATORVASTATIN', N'Atorvastatin 20mg (Lipitor)', N'Atorvastatin calci', N'20mg', N'Viên', N'16000.00', 1400, N'Pfizer', N'Mỹ', N'Hạ cholesterol máu: Uống 1 viên vào buổi tối trước khi đi ngủ', True, 25);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (19, N'TH_BERBERIN', N'Berberin 100mg Dược Hà Tĩnh', N'Berberin clorid', N'100mg', N'Viên', N'1000.00', 5000, N'Hadiphar', N'Việt Nam', N'Nhiễm khuẩn đường ruột, tiêu chảy: Uống 2-4 viên/lần sau ăn', True, 50);
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai, ton_kho_toi_thieu) VALUES (20, N'TH_NACL_09', N'Nước muối sinh lý NaCl 0.9% 500ml', N'Natri Clorid 0.9%', N'500ml', N'Chai', N'10000.00', 1200, N'Pharmedic', N'Việt Nam', N'Súc họng, rửa mũi hoặc sát khuẩn vết thương ngoài da', True, 30);
SET IDENTITY_INSERT thuoc OFF;
GO

-- DU LIEU: tai_khoan
SET IDENTITY_INSERT tai_khoan ON;
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (1, 1, N'admin', N'scrypt:32768:8:1$y54pJFn9BdiWieKx$1f45ee256e90ead56bdd06bf79cffb9e75d21e602e1b3f32642050260d053087cb54b98f9bf7399c00a7fd8466f4ab2e5744d7fd8595c5bda4d9717abd142471', N'admin@h2tcare.vn', N'0999999999', True, N'2026-10-22 19:40:51.110000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (2, 2, N'letan_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'lan.letan@h2tcare.vn', N'0908111221', True, N'2026-10-22 19:40:51.110000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (3, 2, N'letan_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'huyen.letan@h2tcare.vn', N'0908111222', True, N'2026-10-22 19:40:51.113000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (4, 2, N'letan_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'thao.letan@h2tcare.vn', N'0908111223', True, N'2026-10-22 19:40:51.117000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (5, 2, N'letan_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bich.letan@h2tcare.vn', N'0908111224', True, N'2026-10-22 19:40:51.117000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (6, 2, N'letan_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'ha.letan@h2tcare.vn', N'0908111225', True, N'2026-10-22 19:40:51.120000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (7, 4, N'duocsi_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'minh.duocsi@h2tcare.vn', N'0908222331', True, N'2026-10-22 19:40:51.120000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (8, 4, N'duocsi_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'oanh.duocsi@h2tcare.vn', N'0908222332', True, N'2026-10-22 19:40:51.120000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (9, 4, N'duocsi_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'trong.duocsi@h2tcare.vn', N'0908222333', True, N'2026-10-22 19:40:51.123000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (10, 4, N'duocsi_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'truc.duocsi@h2tcare.vn', N'0908222334', True, N'2026-10-22 19:40:51.123000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (11, 4, N'duocsi_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'phuc.duocsi@h2tcare.vn', N'0908222335', True, N'2026-10-22 19:40:51.123000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (12, 5, N'ktv_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'duc.ktv@h2tcare.vn', N'0908333441', True, N'2026-10-22 19:40:51.127000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (13, 5, N'ktv_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'cuong.ktv@h2tcare.vn', N'0908333442', True, N'2026-10-22 19:40:51.130000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (14, 5, N'ktv_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'linh.ktv@h2tcare.vn', N'0908333443', True, N'2026-10-22 19:40:51.130000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (15, 5, N'ktv_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'tuan.ktv@h2tcare.vn', N'0908333444', True, N'2026-10-22 19:40:51.133000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (16, 5, N'ktv_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'trang.ktv@h2tcare.vn', N'0908333445', True, N'2026-10-22 19:40:51.133000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (17, 3, N'bs_noi_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_noi_1@h2tcare.vn', N'0912111001', True, N'2026-10-22 19:40:51.137000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (18, 3, N'bs_noi_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_noi_2@h2tcare.vn', N'0912111002', True, N'2026-10-22 19:40:51.137000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (19, 3, N'bs_noi_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_noi_3@h2tcare.vn', N'0912111003', True, N'2026-10-22 19:40:51.137000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (20, 3, N'bs_noi_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_noi_4@h2tcare.vn', N'0912111004', True, N'2026-10-22 19:40:51.137000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (21, 3, N'bs_noi_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_noi_5@h2tcare.vn', N'0912111005', True, N'2026-10-22 19:40:51.137000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (22, 3, N'bs_ngoai_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_ngoai_1@h2tcare.vn', N'0912222001', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (23, 3, N'bs_ngoai_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_ngoai_2@h2tcare.vn', N'0912222002', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (24, 3, N'bs_ngoai_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_ngoai_3@h2tcare.vn', N'0912222003', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (25, 3, N'bs_ngoai_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_ngoai_4@h2tcare.vn', N'0912222004', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (26, 3, N'bs_ngoai_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_ngoai_5@h2tcare.vn', N'0912222005', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (27, 3, N'bs_nhi_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_nhi_1@h2tcare.vn', N'0912333001', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (28, 3, N'bs_nhi_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_nhi_2@h2tcare.vn', N'0912333002', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (29, 3, N'bs_nhi_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_nhi_3@h2tcare.vn', N'0912333003', True, N'2026-10-22 19:40:51.140000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (30, 3, N'bs_nhi_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_nhi_4@h2tcare.vn', N'0912333004', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (31, 3, N'bs_nhi_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_nhi_5@h2tcare.vn', N'0912333005', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (32, 3, N'bs_rhm_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_rhm_1@h2tcare.vn', N'0912444001', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (33, 3, N'bs_rhm_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_rhm_2@h2tcare.vn', N'0912444002', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (34, 3, N'bs_rhm_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_rhm_3@h2tcare.vn', N'0912444003', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (35, 3, N'bs_rhm_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_rhm_4@h2tcare.vn', N'0912444004', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (36, 3, N'bs_rhm_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_rhm_5@h2tcare.vn', N'0912444005', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (37, 3, N'bs_san_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_san_1@h2tcare.vn', N'0912555001', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (38, 3, N'bs_san_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_san_2@h2tcare.vn', N'0912555002', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (39, 3, N'bs_san_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_san_3@h2tcare.vn', N'0912555003', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (40, 3, N'bs_san_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_san_4@h2tcare.vn', N'0912555004', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (41, 3, N'bs_san_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_san_5@h2tcare.vn', N'0912555005', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (42, 3, N'bs_tmh_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_tmh_1@h2tcare.vn', N'0912666001', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (43, 3, N'bs_tmh_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_tmh_2@h2tcare.vn', N'0912666002', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (44, 3, N'bs_tmh_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_tmh_3@h2tcare.vn', N'0912666003', True, N'2026-10-22 19:40:51.143000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (45, 3, N'bs_tmh_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_tmh_4@h2tcare.vn', N'0912666004', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (46, 3, N'bs_tmh_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_tmh_5@h2tcare.vn', N'0912666005', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (47, 3, N'bs_mat_1', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_mat_1@h2tcare.vn', N'0912777001', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (48, 3, N'bs_mat_2', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_mat_2@h2tcare.vn', N'0912777002', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (49, 3, N'bs_mat_3', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_mat_3@h2tcare.vn', N'0912777003', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (50, 3, N'bs_mat_4', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_mat_4@h2tcare.vn', N'0912777004', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (51, 3, N'bs_mat_5', N'scrypt:32768:8:1$wMqKWZ0dHBu7h8DZ$facecc259627024af9e89eef0c6b439458e26036f85f2ce8ea288dec4fdb6f3cd962b9a21b0fe8bdf0a25e1da654be351c8f0c6e8c8814653941f0c5dd33a7fc', N'bs_mat_5@h2tcare.vn', N'0912777005', True, N'2026-10-22 19:40:51.147000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (52, 6, N'0901234561', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'baonam@gmail.com', N'0901234561', True, N'2026-10-22 19:40:51.153000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (53, 6, N'0901234562', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'thuha.tran95@gmail.com', N'0901234562', True, N'2026-10-22 19:40:51.153000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (54, 6, N'0901234563', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'hung.nguyen86@gmail.com', N'0901234563', True, N'2026-10-22 19:40:51.157000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (55, 6, N'0901234564', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'minhanh.le01@gmail.com', N'0901234564', True, N'2026-10-22 19:40:51.157000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (56, 6, N'0901234565', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'trong.pham78@gmail.com', N'0901234565', True, N'2026-10-22 19:40:51.160000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (57, 6, N'0901234566', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'ngan.dobich@gmail.com', N'0901234566', True, N'2026-10-22 19:40:51.160000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (58, 6, N'0901234567', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'khang.vudinh@gmail.com', N'0901234567', True, N'2026-10-22 19:40:51.160000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (59, 6, N'0901234568', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'tuyetmai.bui@gmail.com', N'0901234568', True, N'2026-10-22 19:40:51.160000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (60, 6, N'0901234569', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'quocbao.dang04@gmail.com', N'0901234569', True, N'2026-10-22 19:40:51.160000', NULL, True);
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, ngay_tao, lan_dang_nhap_cuoi, da_hoan_thien_ho_so) VALUES (61, 6, N'0901234570', N'scrypt:32768:8:1$usPNVdyYgTWK0O1E$4be355f22a77ddfeb5840b1e0fce348f06d32f5da33b37c717732ad59e7ea7f75d7e042547b2f68a69379e8a5df82e5bc71cf71f48f6533042a963c8c9ca771f', N'myduyen.phan97@gmail.com', N'0901234570', True, N'2026-10-22 19:40:51.160000', NULL, True);
SET IDENTITY_INSERT tai_khoan OFF;
GO

-- DU LIEU: nhan_vien
SET IDENTITY_INSERT nhan_vien ON;
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (1, 1, N'NV001', N'Admin Quản Trị Hệ Thống', True, N'1985-01-01', N'0999999999', N'admin@h2tcare.vn', N'079085000001', N'140 Lê Trọng Tấn, Tây Thạnh, Tân Phú, TP.HCM', N'Giám đốc Điều hành & Quản trị Hệ thống', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (2, 2, N'NV_LT01', N'Nguyễn Thị Lan', False, N'1995-04-12', N'0908111221', N'lan.letan@h2tcare.vn', N'079195000101', N'TP. Hồ Chí Minh', N'Lễ tân trưởng - Quầy tiếp đón Tầng 1', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (3, 3, N'NV_LT02', N'Trần Thu Huyền', False, N'1997-08-20', N'0908111222', N'huyen.letan@h2tcare.vn', N'079197000102', N'TP. Hồ Chí Minh', N'Tiếp đón & Điều phối lịch hẹn - Quầy A', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (4, 4, N'NV_LT03', N'Lê Phương Thảo', False, N'1996-11-05', N'0908111223', N'thao.letan@h2tcare.vn', N'079196000103', N'TP. Hồ Chí Minh', N'Thu ngân viện phí & Tiếp nhận BHYT - Quầy B', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (5, 5, N'NV_LT04', N'Phạm Ngọc Bích', False, N'1998-02-14', N'0908111224', N'bich.letan@h2tcare.vn', N'079198000104', N'TP. Hồ Chí Minh', N'Chăm sóc khách hàng & Hướng dẫn khám', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (6, 6, N'NV_LT05', N'Đỗ Thu Hà', False, N'1994-06-30', N'0908111225', N'ha.letan@h2tcare.vn', N'079194000105', N'TP. Hồ Chí Minh', N'Lễ tân ca trực & Điều phối bệnh nhân cấp cứu', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (7, 7, N'NV_DS01', N'Dược sĩ Phạm Hoàng Minh', True, N'1992-03-15', N'0908222331', N'minh.duocsi@h2tcare.vn', N'079192000201', N'TP. Hồ Chí Minh', N'Dược sĩ trưởng - Trưởng kho Dược chính', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (8, 8, N'NV_DS02', N'Dược sĩ Nguyễn Thị Kim Oanh', False, N'1994-07-19', N'0908222332', N'oanh.duocsi@h2tcare.vn', N'079194000202', N'TP. Hồ Chí Minh', N'Dược sĩ cấp phát thuốc ngoại trú & BHYT', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (9, 9, N'NV_DS03', N'Dược sĩ Vũ Đình Trọng', True, N'1990-10-10', N'0908222333', N'trong.duocsi@h2tcare.vn', N'079190000203', N'TP. Hồ Chí Minh', N'Dược sĩ quản lý tồn kho & Kiểm kê định kỳ', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (10, 10, N'NV_DS04', N'Dược sĩ Hoàng Thanh Trúc', False, N'1995-12-25', N'0908222334', N'truc.duocsi@h2tcare.vn', N'079195000204', N'TP. Hồ Chí Minh', N'Dược sĩ tư vấn sử dụng thuốc và tương tác thuốc', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (11, 11, N'NV_DS05', N'Dược sĩ Trần Văn Phúc', True, N'1993-05-08', N'0908222335', N'phuc.duocsi@h2tcare.vn', N'079193000205', N'TP. Hồ Chí Minh', N'Dược sĩ phụ trách nhà thuốc bệnh viện', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (12, 12, N'NV_KTV01', N'KTV. Võ Anh Đức', True, N'1993-07-22', N'0908333441', N'duc.ktv@h2tcare.vn', N'079193000301', N'TP. Hồ Chí Minh', N'KTV Trưởng Xét nghiệm Huyết học - Hóa sinh', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (13, 13, N'NV_KTV02', N'KTV. Hoàng Văn Cường', True, N'1991-09-18', N'0908333442', N'cuong.ktv@h2tcare.vn', N'079191000302', N'TP. Hồ Chí Minh', N'KTV Chẩn đoán hình ảnh - Chụp X-Quang kỹ thuật số', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (14, 14, N'NV_KTV03', N'KTV. Đặng Mỹ Linh', False, N'1996-03-30', N'0908333443', N'linh.ktv@h2tcare.vn', N'079196000303', N'TP. Hồ Chí Minh', N'KTV Siêu âm tổng quát & Doppler mạch máu', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (15, 15, N'NV_KTV04', N'KTV. Bùi Quốc Tuấn', True, N'1994-11-12', N'0908333444', N'tuan.ktv@h2tcare.vn', N'079194000304', N'TP. Hồ Chí Minh', N'KTV Thăm dò chức năng & Điện tâm đồ ECG', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (16, 16, N'NV_KTV05', N'KTV. Lê Thùy Trang', False, N'1997-01-25', N'0908333445', N'trang.ktv@h2tcare.vn', N'079197000305', N'TP. Hồ Chí Minh', N'KTV Xét nghiệm Vi sinh - Nước tiểu', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (17, 17, N'BS001', N'BS. Trần Minh Quân', True, N'1985-06-15', N'0912111001', N'bs_noi_1@h2tcare.vn', N'079085001001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nội Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (18, 18, N'BS002', N'BS. Phạm Anh Tuấn', True, N'1982-12-08', N'0912111002', N'bs_noi_2@h2tcare.vn', N'079082001002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nội Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (19, 19, N'BS003', N'BS. Nguyễn Thu Trang', False, N'1989-03-24', N'0912111003', N'bs_noi_3@h2tcare.vn', N'079089001003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nội Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (20, 20, N'BS004', N'BS. Vũ Quốc Hưng', True, N'1988-11-17', N'0912111004', N'bs_noi_4@h2tcare.vn', N'079088001004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nội Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (21, 21, N'BS005', N'BS. Lê Hoài An', True, N'1987-08-05', N'0912111005', N'bs_noi_5@h2tcare.vn', N'079087001005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nội Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (22, 22, N'BS006', N'BS. Nguyễn Hoàng Nam', True, N'1980-03-25', N'0912222001', N'bs_ngoai_1@h2tcare.vn', N'079080002001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Ngoại Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (23, 23, N'BS007', N'BS. Phan Thanh Phong', True, N'1984-07-12', N'0912222002', N'bs_ngoai_2@h2tcare.vn', N'079084002002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Ngoại Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (24, 24, N'BS008', N'BS. Đinh Văn Hùng', True, N'1989-05-19', N'0912222003', N'bs_ngoai_3@h2tcare.vn', N'079089002003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Ngoại Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (25, 25, N'BS009', N'BS. Hoàng Đức Lâm', True, N'1986-10-30', N'0912222004', N'bs_ngoai_4@h2tcare.vn', N'079086002004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Ngoại Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (26, 26, N'BS010', N'BS. Trịnh Văn Long', True, N'1990-01-14', N'0912222005', N'bs_ngoai_5@h2tcare.vn', N'079090002005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Ngoại Tổng Quát', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (27, 27, N'BS011', N'BS. Lê Thị Mai', False, N'1989-09-20', N'0912333001', N'bs_nhi_1@h2tcare.vn', N'079089003001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nhi', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (28, 28, N'BS012', N'BS. Dương Diệu Linh', False, N'1991-04-18', N'0912333002', N'bs_nhi_2@h2tcare.vn', N'079091003002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nhi', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (29, 29, N'BS013', N'BS. Ngô Đình Quân', True, N'1987-11-23', N'0912333003', N'bs_nhi_3@h2tcare.vn', N'079087003003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nhi', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (30, 30, N'BS014', N'BS. Phạm Thúy Hằng', False, N'1992-06-09', N'0912333004', N'bs_nhi_4@h2tcare.vn', N'079092003004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nhi', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (31, 31, N'BS015', N'BS. Đỗ Tuấn Nghĩa', True, N'1983-02-15', N'0912333005', N'bs_nhi_5@h2tcare.vn', N'079083003005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Nhi', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (32, 32, N'BS016', N'BS. Hoàng Đức Duy', True, N'1988-09-20', N'0912444001', N'bs_rhm_1@h2tcare.vn', N'079088004001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Răng Hàm Mặt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (33, 33, N'BS017', N'BS. Đoàn Minh Khang', True, N'1986-04-11', N'0912444002', N'bs_rhm_2@h2tcare.vn', N'079086004002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Răng Hàm Mặt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (34, 34, N'BS018', N'BS. Vũ Hồng Loan', False, N'1990-12-03', N'0912444003', N'bs_rhm_3@h2tcare.vn', N'079090004003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Răng Hàm Mặt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (35, 35, N'BS019', N'BS. Mai Văn Trọng', True, N'1989-08-27', N'0912444004', N'bs_rhm_4@h2tcare.vn', N'079089004004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Răng Hàm Mặt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (36, 36, N'BS020', N'BS. Nguyễn Bích Thủy', False, N'1993-05-16', N'0912444005', N'bs_rhm_5@h2tcare.vn', N'079093004005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Răng Hàm Mặt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (37, 37, N'BS021', N'BS. Đặng Thu Hương', False, N'1985-05-12', N'0912555001', N'bs_san_1@h2tcare.vn', N'079085005001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Sản - Phụ Khoa', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (38, 38, N'BS022', N'BS. Trần Kiều Nga', False, N'1981-10-29', N'0912555002', N'bs_san_2@h2tcare.vn', N'079081005002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Sản - Phụ Khoa', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (39, 39, N'BS023', N'BS. Nguyễn Thanh Huyền', False, N'1988-02-14', N'0912555003', N'bs_san_3@h2tcare.vn', N'079088005003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Sản - Phụ Khoa', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (40, 40, N'BS024', N'BS. Bùi Thị Minh Tâm', False, N'1990-07-07', N'0912555004', N'bs_san_4@h2tcare.vn', N'079090005004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Sản - Phụ Khoa', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (41, 41, N'BS025', N'BS. Lê Tuyết Lan', False, N'1992-09-18', N'0912555005', N'bs_san_5@h2tcare.vn', N'079092005005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Sản - Phụ Khoa', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (42, 42, N'BS026', N'BS. Võ Thanh Bình', True, N'1984-01-20', N'0912666001', N'bs_tmh_1@h2tcare.vn', N'079084006001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Tai Mũi Họng', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (43, 43, N'BS027', N'BS. Hoàng Quốc Tuấn', True, N'1987-06-14', N'0912666002', N'bs_tmh_2@h2tcare.vn', N'079087006002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Tai Mũi Họng', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (44, 44, N'BS028', N'BS. Nguyễn Thị Thục Anh', False, N'1989-12-05', N'0912666003', N'bs_tmh_3@h2tcare.vn', N'079089006003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Tai Mũi Họng', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (45, 45, N'BS029', N'BS. Trương Hoài Nam', True, N'1991-08-30', N'0912666004', N'bs_tmh_4@h2tcare.vn', N'079091006004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Tai Mũi Họng', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (46, 46, N'BS030', N'BS. Chu Đức Cảnh', True, N'1986-03-22', N'0912666005', N'bs_tmh_5@h2tcare.vn', N'079086006005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Tai Mũi Họng', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (47, 47, N'BS031', N'BS. Đỗ Viết Thắng', True, N'1982-05-18', N'0912777001', N'bs_mat_1@h2tcare.vn', N'079082007001', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Mắt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (48, 48, N'BS032', N'BS. Lê Khánh Linh', False, N'1990-10-09', N'0912777002', N'bs_mat_2@h2tcare.vn', N'079090007002', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Mắt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (49, 49, N'BS033', N'BS. Nguyễn Hữu Đạt', True, N'1986-07-26', N'0912777003', N'bs_mat_3@h2tcare.vn', N'079086007003', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Mắt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (50, 50, N'BS034', N'BS. Phạm Hồng Nhung', False, N'1992-02-17', N'0912777004', N'bs_mat_4@h2tcare.vn', N'079092007004', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Mắt', N'2026-10-22', True);
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, ngay_vao_lam, trang_thai) VALUES (51, 51, N'BS035', N'BS. Vũ Văn Hải', True, N'1988-12-11', N'0912777005', N'bs_mat_5@h2tcare.vn', N'079088007005', N'TP. Hồ Chí Minh', N'Bác sĩ chuyên khoa - Khoa Mắt', N'2026-10-22', True);
SET IDENTITY_INSERT nhan_vien OFF;
GO

-- DU LIEU: bac_si
SET IDENTITY_INSERT bac_si ON;
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (1, 17, 1, 1, N'ThS.BS', N'15 năm kinh nghiệm chẩn đoán và điều trị bệnh lý tim mạch, tăng huyết áp và nội tiết tại BV Chợ Rẫy.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (2, 18, 1, 2, N'BSCKII', N'18 năm kinh nghiệm điều trị bệnh tim thiếu máu cục bộ, suy tim mạn và rối loạn lipid máu phức tạp.', N'default_doctor.png', N'180000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (3, 19, 1, 3, N'ThS.BS', N'10 năm chuyên sâu bệnh lý tiêu hóa, trào ngược dạ dày thực quản, viêm loét HP và gan nhiễm mỡ.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (4, 20, 1, 4, N'BSCKI', N'9 năm kinh nghiệm điều trị viêm phế quản, hen suyễn, COPD và các bệnh lý dị ứng - miễn dịch.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (5, 21, 1, 5, N'ThS.BS', N'11 năm kinh nghiệm chuyên khoa Cơ xương khớp, thoái hóa khớp gối, viêm khớp dạng thấp và Gout.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (6, 22, 2, 6, N'BSCKII', N'17 năm phẫu thuật ngoại khoa tổng quát, xử lý chấn thương chỉnh hình và tiểu phẫu u lành da.', N'default_doctor.png', N'180000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (7, 23, 2, 7, N'ThS.BS', N'13 năm kinh nghiệm phẫu thuật thoát vị đĩa đệm, chấn thương thể thao và nội soi khớp gối.', N'default_doctor.png', N'160000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (8, 24, 2, 8, N'BSCKI', N'9 năm chuyên tiểu phẫu bướu bã, u mỡ, móng chọc thịt và khâu thẩm mỹ vết thương phức tạp.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (9, 25, 2, 9, N'ThS.BS', N'11 năm kinh nghiệm khám và điều trị sỏi tiết niệu, u xơ tiền liệt tuyến và nam học ngoại khoa.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (10, 26, 2, 10, N'BSCKI', N'8 năm kinh nghiệm khám bệnh lý hậu môn trực tràng, trĩ nội, trĩ ngoại và rò hậu môn.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (11, 27, 3, 11, N'BSCKI', N'10 năm công tác tại BV Nhi Đồng, chuyên sâu hô hấp, tiêu hóa và nhiễm khuẩn trẻ em.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (12, 28, 3, 12, N'ThS.BS', N'8 năm chuyên khoa Dị ứng - Miễn dịch nhi khoa, hen phế quản trẻ em và viêm da cơ địa.', N'default_doctor.png', N'140000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (13, 29, 3, 13, N'BSCKI', N'11 năm kinh nghiệm chăm sóc trẻ sơ sinh, theo dõi vàng da, rối loạn tiêu hóa và biếng ăn.', N'default_doctor.png', N'140000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (14, 30, 3, 14, N'ThS.BS', N'7 năm tư vấn dinh dưỡng trẻ nhỏ, tầm soát còi xương, chậm lớn và phát triển thể chất.', N'default_doctor.png', N'130000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (15, 31, 3, 15, N'BSCKII', N'16 năm chuyên gia Nhi tổng quát, tầm soát tim bẩm sinh và xử trí co giật do sốt cao.', N'default_doctor.png', N'160000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (16, 32, 4, 16, N'ThS.BS', N'Tốt nghiệp ThS ĐHYD TP.HCM, chuyên gia phục hình răng sứ, chỉnh nha và cấy ghép Implant.', N'default_doctor.png', N'160000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (17, 33, 4, 17, N'BSCKI', N'12 năm kinh nghiệm chỉnh nha mắc cài kim loại, sứ và niềng răng trong suốt Invisalign.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (18, 34, 4, 18, N'ThS.BS', N'9 năm điều trị bệnh lý nha chu, tụt lợi, phẫu thuật cười hở lợi và làm trắng răng laser.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (19, 35, 4, 19, N'BSCKI', N'10 năm chuyên tiểu phẫu răng khôn mọc lệch ngầm bằng sóng siêu âm không sưng đau.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (20, 36, 4, 20, N'ThS.BS', N'8 năm chuyên khoa Nha khoa Trẻ em, tiền chỉnh nha và điều trị tủy răng sữa nhẹ nhàng.', N'default_doctor.png', N'140000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (21, 37, 5, 21, N'BSCKI', N'14 năm kinh nghiệm quản lý thai kỳ nguy cơ cao, tầm soát tiền sản giật và dị tật thai nhi.', N'default_doctor.png', N'180000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (22, 38, 5, 22, N'BSCKII', N'19 năm công tác tại BV Từ Dũ, chuyên sâu phẫu thuật nội soi phụ khoa và tầm soát ung thư.', N'default_doctor.png', N'200000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (23, 39, 5, 23, N'ThS.BS', N'11 năm tư vấn hiếm muộn vô sinh, siêu âm canh noãn và điều trị hội chứng buồng trứng đa nang.', N'default_doctor.png', N'170000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (24, 40, 5, 24, N'BSCKI', N'9 năm chuyên gia Siêu âm hình thái học thai 4D, đo độ mờ da gáy và kiểm tra doppler rốn.', N'default_doctor.png', N'160000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (25, 41, 5, 25, N'ThS.BS', N'8 năm điều trị viêm nhiễm âm đạo mạn tính, lộ tuyến cổ tử cung và tư vấn tiền hôn nhân.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (26, 42, 6, 26, N'BSCKII', N'15 năm chuyên khoa Tai Mũi Họng, nội soi ống mềm NBI phát hiện sớm ung thư vòm họng.', N'default_doctor.png', N'170000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (27, 43, 6, 27, N'ThS.BS', N'11 năm điều trị viêm xoang mũi mạn tính, polyp mũi và phẫu thuật nội soi xoang FESS.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (28, 44, 6, 28, N'BSCKI', N'10 năm chuyên khoa Tai thính học, đo thính lực đồ, điều trị viêm tai giữa và ù tai kéo dài.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (29, 45, 6, 29, N'ThS.BS', N'8 năm điều trị khàn tiếng, hạt xơ dây thanh, trào ngược họng thanh quản LPR.', N'default_doctor.png', N'140000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (30, 46, 6, 30, N'BSCKI', N'12 năm chuyên Tai Mũi Họng Nhi khoa, nạo VA và cắt Amidan bằng công nghệ dao Coblator.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (31, 47, 7, 31, N'BSCKII', N'18 năm phẫu thuật Phaco điều trị đục thủy tinh thể và đặt kính nội nhãn đa tiêu sắc.', N'default_doctor.png', N'180000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (32, 48, 7, 32, N'ThS.BS', N'10 năm chuyên gia Tật khúc xạ cận - loạn thị học đường, fitting kính áp tròng Ortho-K.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (33, 49, 7, 33, N'BSCKI', N'12 năm khám và điều trị bệnh võng mạc đái tháo đường, thoái hóa hoàng điểm tuổi già.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (34, 50, 7, 34, N'ThS.BS', N'8 năm điều trị Glaucoma (cườm nước), kiểm soát nhãn áp và theo dõi thị trường mắt.', N'default_doctor.png', N'140000.00', N'Đang làm việc');
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (35, 51, 7, 35, N'BSCKI', N'11 năm kinh nghiệm khám viêm loét giác mạc, khô mắt mạn tính và mộng thịt tái phát.', N'default_doctor.png', N'150000.00', N'Đang làm việc');
SET IDENTITY_INSERT bac_si OFF;
GO

-- DU LIEU: benh_nhan
SET IDENTITY_INSERT benh_nhan ON;
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (1, 52, N'BN0001', N'Hoàng Bảo Nam', N'1990-05-12', N'Nam', N'0901234561', N'baonam@gmail.com', N'079090000001', N'GD4797931100001', N'120 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP.HCM', N'O+', N'Không có', N'Đau dạ dày nhẹ, trào ngược thực quản', N'Không', N'Hoàng Văn Bảy', N'0901999881', N'Bố', True, N'2026-10-22', N'ABO: O, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (2, 53, N'BN0002', N'Trần Thị Thu Hà', N'1995-04-18', N'Nữ', N'0901234562', N'thuha.tran95@gmail.com', N'079195000301', N'DN4791950003011', N'36 Tân Hương, P. Tân Quý, Q. Tân Phú, TP.HCM', N'A+', N'Aspirin, Tôm cua hải sản có vỏ', N'Viêm xoang mũi dị ứng mạn tính, Viêm loét dạ dày tá tràng', N'Mẹ bị đái tháo đường type 2', N'Trần Văn Cường', N'0901999882', N'Bố đẻ', True, N'2026-10-22', N'ABO: A, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (3, 54, N'BN0003', N'Nguyễn Văn Hùng', N'1986-10-25', N'Nam', N'0901234563', N'hung.nguyen86@gmail.com', N'079186000302', N'GD479860003022', N'128 Cộng Hòa, Phường 12, Quận Tân Bình, TP.HCM', N'O+', N'Không ghi nhận dị ứng thuốc', N'Tăng huyết áp độ 1, Rối loạn mỡ máu (Dyslipidemia)', N'Bố bị tai biến mạch máu não', N'Lê Thị Mai', N'0901999883', N'Vợ', True, N'2026-10-22', N'ABO: O, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (4, 55, N'BN0004', N'Lê Minh Anh', N'2001-08-14', N'Nữ', N'0901234564', N'minhanh.le01@gmail.com', N'079201000303', N'SV4792010003033', N'45/8 Lê Trọng Tấn, P. Tây Thạnh, Q. Tân Phú, TP.HCM', N'B+', N'Kháng sinh Penicillin (phù Quincke)', N'Viêm da cơ địa, Thiếu máu thiếu sắt nhẹ', N'Không có bệnh lý di truyền', N'Lê Quốc Bảo', N'0901999884', N'Anh trai', True, N'2026-10-22', N'ABO: B, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (5, 56, N'BN0005', N'Phạm Đức Trọng', N'1978-02-09', N'Nam', N'0901234565', N'trong.pham78@gmail.com', N'079178000305', N'GD4791780003055', N'84 Sư Vạn Hạnh, Phường 12, Quận 10, TP.HCM', N'AB+', N'Paracetamol (nổi mày đay nhẹ)', N'Thoái hóa đốt sống cổ C5-C6, Đau thần kinh tọa', N'Gia đình có người bị thoái hóa khớp', N'Nguyễn Thị Bích Lan', N'0901999885', N'Vợ', True, N'2026-10-22', N'ABO: AB, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (6, 57, N'BN0006', N'Đỗ Thị Bích Ngân', N'1993-11-30', N'Nữ', N'0901234566', N'ngan.dobich@gmail.com', N'079193000306', N'DN4791930003066', N'215 Kinh Dương Vương, Phường 12, Quận 6, TP.HCM', N'A+', N'Không ghi nhận', N'Viêm amidan hốc mủ mạn, Trào ngược LPR', N'Không có tiền sử đặc biệt', N'Đỗ Thành Vinh', N'0901999886', N'Em trai', True, N'2026-10-22', N'ABO: A, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (7, 58, N'BN0007', N'Vũ Đình Khang', N'1968-06-17', N'Nam', N'0901234567', N'khang.vudinh@gmail.com', N'079168000307', N'HT4791680003077', N'92 Cách Mạng Tháng Tám, Phường 6, Quận 3, TP.HCM', N'O+', N'Không dị ứng thuốc', N'Đái tháo đường type 2, Gan nhiễm mỡ độ 2, Men gan cao', N'Bố mẹ đều mắc đái tháo đường', N'Vũ Đình Hoàng', N'0901999887', N'Con trai', True, N'2026-10-22', N'ABO: O, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (8, 59, N'BN0008', N'Bùi Tuyết Mai', N'1988-09-05', N'Nữ', N'0901234568', N'tuyetmai.bui@gmail.com', N'079188000308', N'DN4791880003088', N'56 Phan Xích Long, Phường 2, Quận Phú Nhuận, TP.HCM', N'B+', N'Dị ứng phấn hoa và lông động vật', N'Rối loạn tiền đình, Thiếu máu não thoáng qua', N'Mẹ bị đau nửa đầu Migraine', N'Trần Văn Hoàng', N'0901999888', N'Chồng', True, N'2026-10-22', N'ABO: B, Rh: Dương (Rh+)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (9, 60, N'BN0009', N'Đặng Quốc Bảo', N'2004-12-22', N'Nam', N'0901234569', N'quocbao.dang04@gmail.com', N'079204000309', N'SV4792040003099', N'18 Quang Trung, Phường 10, Quận Gò Vấp, TP.HCM', N'O-', N'Không có', N'Cận thị khúc xạ 3.5 độ hai mắt, Viêm lợi nhẹ', N'Không', N'Nguyễn Thị Kim Loan', N'0901999889', N'Mẹ', True, N'2026-10-22', N'ABO: O, Rh: Âm (Rh- cực hiếm)', NULL);
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao, ghi_chu_nhom_mau, avatar) VALUES (10, 61, N'BN0010', N'Phan Mỹ Duyên', N'1997-03-14', N'Nữ', N'0901234570', N'myduyen.phan97@gmail.com', N'079197000310', N'DN4791970003100', N'78 Gò Dầu, Phường Tân Quý, Quận Tân Phú, TP.HCM', N'AB-', N'Kháng sinh nhóm Sulfamid', N'Hội chứng ruột kích thích (IBS), Viêm bàng quang', N'Không có bệnh lý gia đình', N'Phan Văn Đức', N'0901999890', N'Bố', True, N'2026-10-22', N'ABO: AB, Rh: Âm (Rh- hiếm)', NULL);
SET IDENTITY_INSERT benh_nhan OFF;
GO

-- DU LIEU: chi_so_sinh_ton
SET IDENTITY_INSERT chi_so_sinh_ton ON;
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (1, 1, N'75 lần/phút', N'36.8 °C', N'120/80 mmHg', N'99 %', N'18 lần/phút', N'170 cm', N'65 kg', N'22.5 (Bình thường)', N'2026-10-22 19:40:51.363000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (2, 2, N'80 lần/phút', N'37.0 °C', N'110/70 mmHg', N'98 %', N'19 lần/phút', N'158 cm', N'48 kg', N'19.2 (Bình thường)', N'2026-10-22 19:40:51.363000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (3, 3, N'85 lần/phút', N'36.6 °C', N'135/85 mmHg', N'98 %', N'18 lần/phút', N'172 cm', N'74 kg', N'25.0 (Tiền béo phì)', N'2026-10-22 19:40:51.367000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (4, 4, N'72 lần/phút', N'36.7 °C', N'115/75 mmHg', N'99 %', N'17 lần/phút', N'162 cm', N'50 kg', N'19.0 (Bình thường)', N'2026-10-22 19:40:51.367000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (5, 5, N'76 lần/phút', N'36.8 °C', N'125/80 mmHg', N'99 %', N'18 lần/phút', N'168 cm', N'68 kg', N'24.1 (Bình thường)', N'2026-10-22 19:40:51.367000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (6, 6, N'74 lần/phút', N'36.5 °C', N'110/70 mmHg', N'99 %', N'18 lần/phút', N'160 cm', N'52 kg', N'20.3 (Bình thường)', N'2026-10-22 19:40:51.367000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (7, 7, N'82 lần/phút', N'36.7 °C', N'130/80 mmHg', N'97 %', N'19 lần/phút', N'165 cm', N'70 kg', N'25.7 (Tiền béo phì)', N'2026-10-22 19:40:51.367000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (8, 8, N'78 lần/phút', N'36.9 °C', N'105/65 mmHg', N'99 %', N'18 lần/phút', N'156 cm', N'46 kg', N'18.9 (Bình thường)', N'2026-10-22 19:40:51.370000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (9, 9, N'70 lần/phút', N'36.6 °C', N'118/75 mmHg', N'100 %', N'16 lần/phút', N'175 cm', N'62 kg', N'20.2 (Bình thường)', N'2026-10-22 19:40:51.370000', NULL);
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu) VALUES (10, 10, N'76 lần/phút', N'36.8 °C', N'110/70 mmHg', N'99 %', N'18 lần/phút', N'163 cm', N'51 kg', N'19.2 (Bình thường)', N'2026-10-22 19:40:51.370000', NULL);
SET IDENTITY_INSERT chi_so_sinh_ton OFF;
GO

-- DU LIEU: lich_hen
SET IDENTITY_INSERT lich_hen ON;
INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat) VALUES (1, N'LH26090001', 1, 1, 1, 1, N'2026-10-22', N'08:30:00', N'Đau âm ỉ vùng thượng vị kèm ợ chua nhiều tuần nay', 1, N'Đã hoàn thành', N'2026-10-21 19:40:51.377000');
INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat) VALUES (2, N'LH26090002', 1, 2, 1, 2, N'2026-10-23', N'09:00:00', N'Tái khám định kỳ theo dõi chỉ số huyết áp và mỡ máu', 1, N'Đã tiếp nhận', N'2026-10-22 19:40:51.380000');
INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat) VALUES (3, N'LH26090003', 2, 11, 3, 11, N'2026-10-24', N'10:00:00', N'Bé sốt nhẹ về chiều và ho khan có đờm', 1, N'Chờ tiếp nhận', N'2026-10-22 19:40:51.383000');
SET IDENTITY_INSERT lich_hen OFF;
GO

-- DU LIEU: phieu_kham
SET IDENTITY_INSERT phieu_kham ON;
INSERT INTO phieu_kham (id, ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai) VALUES (1, N'PK26090001', 1, 1, 1, 1, N'2026-10-22 19:40:51.387000', N'Đau thượng vị ợ chua', N'Đau âm ỉ vùng thượng vị sau ăn no hoặc lúc đói, ợ chua, buồn nôn nhẹ, bụng chướng hơi.', N'Theo dõi Viêm loét dạ dày tá tràng / Trào ngược dạ dày thực quản (GERD)', N'K29.7 - Viêm d? dày không d?c hi?u', N'Chỉ định nội soi dạ dày, xét nghiệm vi khuẩn HP và công thức máu. Kê đơn thuốc giảm tiết acid.', N'Kiêng ăn đồ cay nóng chua cay, không thức khuya, uống thuốc đúng giờ trước bữa ăn 30 phút.', N'2026-11-05', N'Hoàn thành');
SET IDENTITY_INSERT phieu_kham OFF;
GO

-- DU LIEU: phieu_chi_dinh
SET IDENTITY_INSERT phieu_chi_dinh ON;
INSERT INTO phieu_chi_dinh (id, ma_chi_dinh, phieu_kham_id, bac_si_id, thoi_gian_chi_dinh, ghi_chu, trang_thai) VALUES (1, N'CD26090001', 1, 1, N'2026-10-22 19:40:51.390000', N'Thực hiện gấp trong buổi sáng để chẩn đoán', N'Hoàn thành');
SET IDENTITY_INSERT phieu_chi_dinh OFF;
GO

-- DU LIEU: chi_tiet_chi_dinh
SET IDENTITY_INSERT chi_tiet_chi_dinh ON;
INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, file_ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai, bac_si_duyet, thoi_gian_duyet, ghi_chu_duyet, nguoi_nhap) VALUES (1, 1, 8, N'RBC: 4.8 T/L, Hb: 145 g/L, WBC: 7.2 G/L (Bình thường), PLT: 250 G/L. Kết luận: Công thức máu trong giới hạn sinh lý bình thường.', NULL, N'KTV. Võ Anh Đức', N'2026-10-22 19:40:51.390000', N'Hoàn thành', N'BS. Trần Minh Quân', N'2026-10-22 19:40:51.390000', N'Chỉ số bình thường, không có dấu hiệu nhiễm trùng cấp', NULL);
INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, file_ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai, bac_si_duyet, thoi_gian_duyet, ghi_chu_duyet, nguoi_nhap) VALUES (2, 1, 13, N'Hình ảnh X-Quang phổi: Không thấy tổn thương thâm nhiễm nhu mô phổi hai bên. Khung sườn và bóng tim bình thường.', NULL, N'KTV. Hoàng Văn Cường', N'2026-10-22 19:40:51.393000', N'Hoàn thành', N'BS. Trần Minh Quân', N'2026-10-22 19:40:51.393000', N'X-quang lồng ngực bình thường', NULL);
SET IDENTITY_INSERT chi_tiet_chi_dinh OFF;
GO

-- DU LIEU: don_thuoc
SET IDENTITY_INSERT don_thuoc ON;
INSERT INTO don_thuoc (id, ma_don_thuoc, phieu_kham_id, bac_si_id, thoi_gian_ke, loi_dan, trang_thai, ly_do_huy, nguoi_huy, thoi_gian_huy) VALUES (1, N'DT26090001', 1, 1, N'2026-10-22 19:40:51.397000', N'Uống thuốc đúng theo hướng dẫn, tái khám sau 2 tuần', N'Đã cấp thuốc', NULL, NULL, NULL);
SET IDENTITY_INSERT don_thuoc OFF;
GO

-- DU LIEU: chi_tiet_don_thuoc
SET IDENTITY_INSERT chi_tiet_don_thuoc ON;
INSERT INTO chi_tiet_don_thuoc (id, don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung) VALUES (1, 1, 11, 28, N'Uống 1 viên/lần, ngày 2 lần', N'Uống trước ăn sáng và ăn tối 30 phút');
INSERT INTO chi_tiet_don_thuoc (id, don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung) VALUES (2, 1, 12, 14, N'Uống 1 gói/lần khi đau tức thượng vị', N'Uống trực tiếp sau khi ăn 1 giờ');
SET IDENTITY_INSERT chi_tiet_don_thuoc OFF;
GO

-- DU LIEU: hoa_don
SET IDENTITY_INSERT hoa_don ON;
INSERT INTO hoa_don (id, ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu) VALUES (1, N'HD26090001', 1, 1, N'801000.00', N'380000.00', N'0.00', N'421000.00', N'Chuyển khoản QR Code', N'Đã thanh toán', N'2026-10-22 19:40:51.403000', N'Lê Phương Thảo');
SET IDENTITY_INSERT hoa_don OFF;
GO

-- DU LIEU: chi_tiet_hoa_don
SET IDENTITY_INSERT chi_tiet_hoa_don ON;
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES (1, 1, N'Khám bệnh', N'Khám Chuyên Khoa Nội Tổng Quát', 1, 1, N'150000.00', N'150000.00');
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES (2, 1, N'Xét nghiệm', N'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', 8, 1, N'150000.00', N'150000.00');
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES (3, 1, N'Chẩn đoán hình ảnh', N'Chụp X-Quang Ngực thẳng kỹ thuật số (DR)', 13, 1, N'200000.00', N'200000.00');
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES (4, 1, N'Thuốc', N'Esomeprazole 20mg Stada', 11, 28, N'8000.00', N'224000.00');
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES (5, 1, N'Thuốc', N'Phosphalugel 20g (Thuốc dạ dày chữ P)', 12, 14, N'5500.00', N'77000.00');
SET IDENTITY_INSERT chi_tiet_hoa_don OFF;
GO

-- DU LIEU: thong_bao
SET IDENTITY_INSERT thong_bao ON;
INSERT INTO thong_bao (id, tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, da_doc, thoi_gian_tao, lien_ket) VALUES (1, 48, N'Tiếp nhận lịch khám thành công!', N'Lịch hẹn khám mã LH26090002 của bạn vào ngày mai lúc 09:00 tại Chuyên khoa Nội đã được bộ phận Lễ tân tiếp nhận. Vui lòng có mặt trước 15 phút tại Quầy tiếp đón.', N'Lịch hẹn', False, N'2026-10-22 19:40:51.413000', N'/patient/booking');
INSERT INTO thong_bao (id, tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, da_doc, thoi_gian_tao, lien_ket) VALUES (2, 48, N'Hoàn thành đợt khám bệnh', N'Hồ sơ khám bệnh EMR và kết quả xét nghiệm mã PK26090001 đã có kết quả đầy đủ. Bạn có thể tra cứu và tải toa thuốc trên cổng bệnh nhân.', N'Khám bệnh', False, N'2026-10-22 19:40:51.413000', N'/patient/records');
SET IDENTITY_INSERT thong_bao OFF;
GO

-- DU LIEU: banner
SET IDENTITY_INSERT banner ON;
INSERT INTO banner (id, tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai, ngay_tao) VALUES (1, N'Chăm sóc bằng tài năng, y đức và sự thấu cảm', N'Tiêu chuẩn chất lượng quốc tế', N'Bệnh viện Đa khoa Quốc tế H2T Healthcare mang đến trải nghiệm khám chữa bệnh chuẩn mực với 35 bác sĩ chuyên khoa giàu kinh nghiệm và hệ thống bệnh án điện tử EMR 360°.', N'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1600', N'/booking', N'ĐĂNG KÝ KHÁM NGAY', 1, True, N'2026-10-22 19:40:51.413000');
INSERT INTO banner (id, tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai, ngay_tao) VALUES (2, N'Đội ngũ 35 Bác sĩ chuyên khoa đầu ngành', N'Chuyên môn vững vàng', N'Hội tụ 35 bác sĩ chuyên khoa ThS.BS, BSCKII tại 7 chuyên khoa lâm sàng, tận tâm đồng hành vì sức khỏe toàn diện của gia đình bạn.', N'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=1600', N'#bac-si', N'TÌM BÁC SĨ CHUYÊN KHOA', 2, True, N'2026-10-22 19:40:51.417000');
INSERT INTO banner (id, tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai, ngay_tao) VALUES (3, N'Hệ thống Bệnh án điện tử EMR 360°', N'Công nghệ y tế số 4.0', N'Tra cứu trực tuyến lịch sử khám bệnh, kết quả xét nghiệm, phim X-quang và đơn thuốc tiện lợi, bảo mật tuyệt đối.', N'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1600', N'/patient', N'CỔNG THÔNG TIN BỆNH NHÂN', 3, True, N'2026-10-22 19:40:51.417000');
SET IDENTITY_INSERT banner OFF;
GO

-- DU LIEU: bai_viet
SET IDENTITY_INSERT bai_viet ON;
INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai) VALUES (1, 1, N'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', N'benh-cam-cum-mua-giao-mua', N'Cẩm Nang Y Tế', N'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', N'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', N'cam-cum.jpg', 320, N'2026-10-22 19:40:51.420000', True);
INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai) VALUES (2, 1, N'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', N'cham-soc-rang-mieng-cho-tre', N'Nhi Khoa', N'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', N'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng phù hợp lứa tuổi...', N'rang-mieng-tre.jpg', 215, N'2026-10-22 19:40:51.423000', True);
INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai) VALUES (3, 1, N'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', N'kham-suc-khoe-tong-quat-dinh-ky', N'Tin Tức Phòng Khám', N'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', N'Nội dung chi tiết về các gói khám tổng quát tại H2T Healthcare...', N'kham-tong-quat.jpg', 580, N'2026-10-22 19:40:51.427000', True);
SET IDENTITY_INSERT bai_viet OFF;
GO
