-- CƠ SỞ DỮ LIỆU HỆ THỐNG QUẢN LÝ PHÒNG KHÁM ĐA KHOA (H2T HEALTHCARE HIS / EMR)
-- PHIÊN BẢN DÀNH CHO: MICROSOFT SQL SERVER 2016 / 2019 / 2022 (T-SQL)

-- 1. TẠO VÀ CHỌN CƠ SỞ DỮ LIỆU
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

-- 2. XÓA KHÓA NGOẠI VÀ BẢNG CŨ NẾU ĐÃ TỒN TẠI
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(s.name) + N'.' + QUOTENAME(t.name) + 
               N' DROP CONSTRAINT ' + QUOTENAME(f.name) + N';'
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

-- 3. TẠO CÁC BẢNG DỮ LIỆU CHUẨN T-SQL

-- Bảng Vai trò
CREATE TABLE vai_tro (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_vai_tro NVARCHAR(30) NOT NULL UNIQUE,
    ten_vai_tro NVARCHAR(50) NOT NULL,
    mo_ta NVARCHAR(255)
);

-- Bảng Chuyên khoa
CREATE TABLE chuyen_khoa (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_khoa NVARCHAR(20) NOT NULL UNIQUE,
    ten_khoa NVARCHAR(100) NOT NULL,
    mo_ta NVARCHAR(MAX),
    icon NVARCHAR(100) DEFAULT 'fa-stethoscope',
    gia_kham_mac_dinh DECIMAL(12, 2) DEFAULT 150000.00
);

-- Bảng Phòng khám vật lý
CREATE TABLE phong_kham (
    id INT IDENTITY(1,1) PRIMARY KEY,
    chuyen_khoa_id INT NOT NULL,
    ma_phong NVARCHAR(20) NOT NULL UNIQUE,
    ten_phong NVARCHAR(100) NOT NULL,
    vi_tri_tang NVARCHAR(50) DEFAULT N'Tầng 1',
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

-- Bảng Dịch vụ y tế
CREATE TABLE dich_vu (
    id INT IDENTITY(1,1) PRIMARY KEY,
    chuyen_khoa_id INT NULL,
    ma_dich_vu NVARCHAR(30) NOT NULL UNIQUE,
    ten_dich_vu NVARCHAR(255) NOT NULL,
    loai_dich_vu NVARCHAR(50) DEFAULT N'Khám bệnh',
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    bhyt_chi_tra_pt INT DEFAULT 0,
    mo_ta NVARCHAR(255),
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

-- Bảng Kho dược & Thuốc
CREATE TABLE thuoc (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_thuoc NVARCHAR(30) NOT NULL UNIQUE,
    ten_thuoc NVARCHAR(255) NOT NULL,
    hoat_chat NVARCHAR(255),
    ham_luong NVARCHAR(100),
    don_vi_tinh NVARCHAR(50) NOT NULL,
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    so_luong_ton INT DEFAULT 0,
    hang_san_xuat NVARCHAR(150),
    nuoc_san_xuat NVARCHAR(100),
    huong_dan_su_dung NVARCHAR(255),
    trang_thai BIT DEFAULT 1
);

-- Bảng Tài khoản người dùng
CREATE TABLE tai_khoan (
    id INT IDENTITY(1,1) PRIMARY KEY,
    vai_tro_id INT NOT NULL,
    username NVARCHAR(100) NOT NULL UNIQUE,
    password NVARCHAR(255) NOT NULL,
    email NVARCHAR(100),
    sdt NVARCHAR(15),
    trang_thai BIT DEFAULT 1,
    ngay_tao DATETIME DEFAULT GETDATE(),
    lan_dang_nhap_cuoi DATETIME NULL,
    FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id)
);

-- Bảng Nhân viên
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
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE CASCADE
);

-- Bảng Bác sĩ
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

-- Bảng Bệnh nhân
CREATE TABLE benh_nhan (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tai_khoan_id INT NULL,
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

-- Bảng Chỉ số sinh tồn
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

-- Bảng Lịch làm việc
CREATE TABLE lich_lam_viec (
    id INT IDENTITY(1,1) PRIMARY KEY,
    bac_si_id INT NOT NULL,
    phong_kham_id INT NOT NULL,
    ngay_lam DATE NOT NULL,
    ca_lam TINYINT NOT NULL,
    gio_bat_dau TIME DEFAULT '07:00:00',
    gio_ket_thuc TIME DEFAULT '11:30:00',
    so_luong_kham_toi_da INT DEFAULT 20,
    so_luong_da_dang_ky INT DEFAULT 0,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id) ON DELETE CASCADE,
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
);

-- Bảng Lịch hẹn khám
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

-- Bảng Phiếu khám bệnh
CREATE TABLE phieu_kham (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_phieu NVARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NOT NULL,
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

-- Bảng Phiếu chỉ định CLS
CREATE TABLE phieu_chi_dinh (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_chi_dinh NVARCHAR(30) NOT NULL UNIQUE,
    phieu_kham_id INT NOT NULL,
    bac_si_id INT NOT NULL,
    thoi_gian_chi_dinh DATETIME DEFAULT GETDATE(),
    ghi_chu NVARCHAR(255),
    trang_thai NVARCHAR(50) DEFAULT N'Chờ thực hiện',
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
);

-- Bảng Chi tiết chỉ định CLS
CREATE TABLE chi_tiet_chi_dinh (
    id INT IDENTITY(1,1) PRIMARY KEY,
    phieu_chi_dinh_id INT NOT NULL,
    dich_vu_id INT NOT NULL,
    ket_qua NVARCHAR(MAX),
    file_ket_qua NVARCHAR(255),
    ktv_thuc_hien NVARCHAR(100),
    thoi_gian_thuc_hien DATETIME NULL,
    trang_thai NVARCHAR(50) DEFAULT N'Chờ làm',
    FOREIGN KEY (phieu_chi_dinh_id) REFERENCES phieu_chi_dinh(id) ON DELETE CASCADE,
    FOREIGN KEY (dich_vu_id) REFERENCES dich_vu(id)
);

-- Bảng Đơn thuốc
CREATE TABLE don_thuoc (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ma_don_thuoc NVARCHAR(30) NOT NULL UNIQUE,
    phieu_kham_id INT NOT NULL UNIQUE,
    bac_si_id INT NOT NULL,
    thoi_gian_ke DATETIME DEFAULT GETDATE(),
    loi_dan NVARCHAR(MAX),
    trang_thai NVARCHAR(50) DEFAULT N'Đã cấp thuốc',
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
);

-- Bảng Chi tiết đơn thuốc
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

-- Bảng Hóa đơn viện phí
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
    trang_thai NVARCHAR(50) DEFAULT N'Chưa thanh toán',
    thoi_gian_thanh_toan DATETIME NULL,
    nhan_vien_thu NVARCHAR(100) DEFAULT N'Trần Thị Mai',
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

-- Bảng Chi tiết hóa đơn
CREATE TABLE chi_tiet_hoa_don (
    id INT IDENTITY(1,1) PRIMARY KEY,
    hoa_don_id INT NOT NULL,
    loai_khoan_thu NVARCHAR(50) NOT NULL,
    ten_khoan_thu NVARCHAR(255) NOT NULL,
    tham_chieu_id INT NULL,
    so_luong INT NOT NULL DEFAULT 1,
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    thanh_tien DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(id) ON DELETE CASCADE
);

-- Bảng Thông báo
CREATE TABLE thong_bao (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tai_khoan_id INT NOT NULL,
    tieu_de NVARCHAR(255) NOT NULL,
    noi_dung NVARCHAR(MAX) NOT NULL,
    loai_thong_bao NVARCHAR(50) DEFAULT N'Hệ thống',
    da_doc BIT DEFAULT 0,
    thoi_gian_tao DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE CASCADE
);

-- Bảng Phản hồi
CREATE TABLE phan_hoi (
    id INT IDENTITY(1,1) PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NULL,
    diem_danh_gia TINYINT NOT NULL CHECK (diem_danh_gia BETWEEN 1 AND 5),
    noi_dung NVARCHAR(MAX),
    thoi_gian DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE,
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

-- Bảng Hòm thư góp ý
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

-- Bảng Bài viết
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
GO

-- 4. TẠO CÁC CHỈ MỤC (INDEXES)
CREATE UNIQUE NONCLUSTERED INDEX uq_benhnhan_taikhoan ON benh_nhan(tai_khoan_id) WHERE tai_khoan_id IS NOT NULL;
CREATE INDEX idx_benhnhan_sdt ON benh_nhan(sdt);
CREATE INDEX idx_benhnhan_cccd ON benh_nhan(cccd);
CREATE INDEX idx_benhnhan_ma ON benh_nhan(ma_benh_nhan);
CREATE INDEX idx_lichhen_ngay ON lich_hen(ngay_hen);
CREATE INDEX idx_lichhen_trangthai ON lich_hen(trang_thai);
CREATE INDEX idx_phieukham_ngay ON phieu_kham(thoi_gian_kham);
CREATE INDEX idx_hoadon_ngay ON hoa_don(thoi_gian_thanh_toan);
GO

-- 5. TẠO CÁC VIEW BÁO CÁO (VIEWS)
CREATE OR ALTER VIEW v_danh_sach_benh_nhan AS
SELECT 
    b.id,
    b.ma_benh_nhan,
    b.ho_ten,
    b.ngay_sinh,
    DATEDIFF(YEAR, b.ngay_sinh, GETDATE()) AS tuoi,
    b.gioi_tinh,
    b.sdt,
    b.email,
    b.cccd,
    b.bhyt,
    b.dia_chi,
    b.nhom_mau,
    b.di_ung,
    b.tien_su_benh,
    b.tien_su_gia_dinh,
    b.nguoi_than_ho_ten,
    b.nguoi_than_sdt,
    b.nguoi_than_quan_he,
    b.co_tai_khoan,
    t.username,
    b.ngay_tao
FROM benh_nhan b
LEFT JOIN tai_khoan t ON b.tai_khoan_id = t.id;
GO

-- 6. NẠP DỮ LIỆU MẪU (SEED DATA)
SET IDENTITY_INSERT vai_tro ON;
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES
(1, 'ADMIN', N'Quản trị viên', N'Toàn quyền cấu hình và quản trị hệ thống phòng khám'),
(2, 'LETAN', N'Nhân viên lễ tân / Thu ngân', N'Tiếp đón bệnh nhân, sắp xếp lịch hẹn, thu ngân viện phí'),
(3, 'BACSI', N'Bác sĩ chuyên khoa', N'Khám bệnh, chẩn đoán, kê đơn thuốc và chỉ định cận lâm sàng'),
(4, 'DUOCSI', N'Dược sĩ / Thủ kho dược', N'Quản lý kho thuốc, cấp phát thuốc theo toa'),
(5, 'KTV', N'Kỹ thuật viên xét nghiệm', N'Thực hiện xét nghiệm, X-quang, chẩn đoán hình ảnh'),
(6, 'BENHNHAN', N'Bệnh nhân', N'Khách hàng sử dụng cổng thông tin y tế bệnh nhân');
SET IDENTITY_INSERT vai_tro OFF;
GO

SET IDENTITY_INSERT chuyen_khoa ON;
INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh) VALUES
(1, 'KHOA_NOI', N'Khoa Nội Tổng Quát', N'Khám, chẩn đoán và điều trị bệnh lý tim mạch, tiêu hóa, hô hấp, cơ xương khớp', 'fa-stethoscope', 150000.00),
(2, 'KHOA_NGOAI', N'Khoa Ngoại Tổng Quát', N'Khám và điều trị ngoại khoa, tiểu phẫu, xử lý vết thương', 'fa-syringe', 150000.00),
(3, 'KHOA_NHI', N'Khoa Nhi', N'Chăm sóc và điều trị chuyên sâu bệnh lý trẻ em, tư vấn dinh dưỡng', 'fa-baby', 120000.00),
(4, 'KHOA_RHM', N'Khoa Răng Hàm Mặt', N'Nha khoa tổng quát, nhổ răng khôn, niềng răng, cạo vôi răng', 'fa-tooth', 150000.00),
(5, 'KHOA_SAN', N'Khoa Sản - Phụ Khoa', N'Quản lý thai kỳ, siêu âm 4D, tầm soát và điều trị phụ khoa', 'fa-person-pregnant', 180000.00),
(6, 'KHOA_TMH', N'Khoa Tai Mũi Họng', N'Nội soi tai mũi họng, điều trị viêm xoang, viêm họng hạt, viêm amidan', 'fa-head-side-cough', 150000.00),
(7, 'KHOA_MAT', N'Khoa Mắt', N'Đo tật khúc xạ, khám và điều trị bệnh lý đáy mắt, giác mạc', 'fa-eye', 150000.00),
(8, 'KHOA_CLS', N'Khoa Cận Lâm Sàng', N'Trung tâm xét nghiệm hóa sinh, huyết học và chẩn đoán hình ảnh', 'fa-vial', 100000.00);
SET IDENTITY_INSERT chuyen_khoa OFF;
GO

SET IDENTITY_INSERT phong_kham ON;
INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES
(1, 1, 'PK101', N'Phòng Khám Nội 1', N'Tầng 1 - Khu A', 1),
(2, 1, 'PK102', N'Phòng Khám Nội 2', N'Tầng 1 - Khu A', 1),
(3, 2, 'PK103', N'Phòng Khám Ngoại & Tiểu Phẫu', N'Tầng 1 - Khu B', 1),
(4, 3, 'PK201', N'Phòng Khám Nhi 1', N'Tầng 2 - Khu A', 1),
(5, 4, 'PK202', N'Phòng Nha Khoa Kỹ Thuật Cao', N'Tầng 2 - Khu B', 1),
(6, 5, 'PK203', N'Phòng Khám Sản Phụ Khoa', N'Tầng 2 - Khu B', 1),
(7, 8, 'XN001', N'Phòng Xét Nghiệm Huyết Học - Hóa Sinh', N'Tầng 1 - Khu C', 1),
(8, 8, 'CDHA01', N'Phòng Siêu Âm Màu & Chụp X-Quang', N'Tầng 1 - Khu C', 1);
SET IDENTITY_INSERT phong_kham OFF;
GO

SET IDENTITY_INSERT dich_vu ON;
INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta) VALUES
(1, 1, 'DV_KHAM_NOI', N'Khám Nội Tổng Quát', N'Khám bệnh', 150000.00, 80, N'Khám và tư vấn toàn diện các bệnh lý nội khoa'),
(2, 3, 'DV_KHAM_NHI', N'Khám Nhi Khoa', N'Khám bệnh', 120000.00, 80, N'Khám và tư vấn sức khỏe trẻ em'),
(3, 2, 'DV_KHAM_NGOAI', N'Khám Ngoại Khoa', N'Khám bệnh', 150000.00, 80, N'Khám và tư vấn tiểu phẫu ngoại khoa'),
(4, 4, 'DV_NHO_RANG', N'Tiểu phẫu Nhổ răng khôn', N'Thủ thuật', 1000000.00, 0, N'Nhổ răng khôn mọc lệch, không đau'),
(5, 4, 'DV_CAO_VOI', N'Cạo vôi răng & Đánh bóng', N'Thủ thuật', 200000.00, 0, N'Làm sạch mảng bám cao răng bằng sóng siêu âm'),
(6, 8, 'DV_SIEU_AM', N'Siêu âm Doppler màu ổ bụng tổng quát', N'Chẩn đoán hình ảnh', 250000.00, 50, N'Khảo sát gan, mật, tụy, lách, thận, bàng quang'),
(7, 8, 'DV_XN_MAU', N'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', N'Xét nghiệm', 150000.00, 80, N'Kiểm tra hồng cầu, bạch cầu, tiểu cầu, thiếu máu'),
(8, 8, 'DV_XN_NT', N'Tổng phân tích nước tiểu 10 thông số', N'Xét nghiệm', 100000.00, 80, N'Kiểm tra đường, đạm, tế bào vi thể nước tiểu'),
(9, 8, 'DV_XQUANG', N'Chụp X-Quang Tim Phổi thẳng kỹ thuật số', N'Chẩn đoán hình ảnh', 200000.00, 70, N'Kiểm tra tổn thương nhu mô phổi, bóng tim'),
(10, 8, 'DV_ECG', N'Đo điện tim đồ 12 chuyển đạo (ECG)', N'Thăm dò chức năng', 150000.00, 70, N'Khảo sát nhịp xoang, rối loạn dẫn truyền tim'),
(11, 8, 'DV_NOISOI_DD', N'Nội soi dạ dày tá tràng ống mềm', N'Chẩn đoán hình ảnh', 600000.00, 50, N'Nội soi chẩn đoán viêm loét dạ dày kèm Test HP');
SET IDENTITY_INSERT dich_vu OFF;
GO

SET IDENTITY_INSERT thuoc ON;
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung) VALUES
(1, 'TH001', N'Paracetamol 500mg', 'Paracetamol', '500mg', N'Viên', 2000.00, 5000, N'Dược Hậu Giang', N'Việt Nam', N'Uống 1-2 viên khi sốt trên 38.5°C hoặc đau nhức, cách nhau 4-6 giờ'),
(2, 'TH002', N'Amoxicillin 500mg', 'Amoxicillin trihydrat', '500mg', N'Viên', 3000.00, 2000, 'Imexpharm', N'Việt Nam', N'Kháng sinh: Uống 1 viên sau ăn, ngày 2 lần, dùng đủ liệu trình 5-7 ngày'),
(3, 'TH003', N'Oresol 245', 'Glucose, Natri clorid, Kali clorid', '245 mOsm/L', N'Gói', 5000.00, 1000, 'Traphaco', N'Việt Nam', N'Pha đúng 1 gói với 200ml nước sôi để nguội, uống bù nước khi sốt hoặc tiêu chảy'),
(4, 'TH004', N'Loratadin 10mg', 'Loratadin', '10mg', N'Viên', 4000.00, 1500, 'Pymepharco', N'Việt Nam', N'Thuốc kháng histamin: Uống 1 viên vào buổi tối trước khi đi ngủ'),
(5, 'TH005', N'Esomeprazole 40mg', 'Esomeprazole magnesium', '40mg', N'Viên', 12000.00, 3000, 'AstraZeneca', N'Thụy Điển', N'Giảm tiết acid dạ dày: Uống 1 viên trước bữa ăn sáng 30 phút'),
(6, 'TH006', N'Phosphalugel 20g', 'Aluminium phosphate', '20g', N'Gói', 5000.00, 2500, 'Boehringer Ingelheim', N'Pháp', N'Uống 1 gói khi có cơn đau thượng vị hoặc 2 giờ sau bữa ăn'),
(7, 'TH007', N'Men vi sinh Enterogermina', 'Bacillus clausii', '2 tỷ bào tử/5ml', N'Ống', 9000.00, 1200, 'Sanofi', N'Ý', N'Lắc đều, uống trực tiếp 1-2 ống/ngày sau bữa ăn'),
(8, 'TH008', N'Ibuprofen 400mg', 'Ibuprofen', '400mg', N'Viên', 3500.00, 2500, 'Stada', N'Việt Nam', N'Kháng viêm giảm đau cơ xương khớp, uống 1 viên sau ăn no'),
(9, 'TH009', N'Siro ho thảo dược Prospan', 'Cao khô lá thường xuân', '100ml', N'Chai', 75000.00, 300, 'Engelhard', N'Đức', N'Uống 5ml/lần, ngày 3 lần sau ăn cho người lớn và trẻ em trên 6 tuổi'),
(10, 'TH010', N'Nước muối sinh lý NaCl 0.9%', 'Natri Clorid 0.9%', '500ml', N'Chai', 10000.00, 800, 'Pharmedic', N'Việt Nam', N'Dùng súc miệng họng hoặc rửa vết thương ngoài da');
SET IDENTITY_INSERT thuoc OFF;
GO

SET IDENTITY_INSERT tai_khoan ON;
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt) VALUES
(1, 1, 'admin', 'scrypt:32768:8:1$wte2IwGnBVO1lRWL$3da8cd29b71656229c22086ff7164745647f790916b2f3949a826972b6c8f4896f4fd90b2856affb5af79c1274b86fc0d20e1ee0da464623a7117faa4984e03c', 'admin@phongkham.com', '0999999999'),
(2, 2, 'letan.mai', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'mai.tt@phongkham.com', '0988888888'),
(3, 2, 'letan.khang', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'khang.lv@phongkham.com', '0977777777'),
(4, 3, 'dr.quan', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'quan.tm@phongkham.com', '0966666666'),
(5, 3, 'dr.lan', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'lan.pp@phongkham.com', '0955555555'),
(6, 3, 'dr.minh', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'minh.vq@phongkham.com', '0944444444'),
(7, 3, 'dr.huong', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'huong.bt@phongkham.com', '0933333333'),
(8, 6, '0901234567', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'baonam@gmail.com', '0901234567'),
(9, 6, '0912345678', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'ngoctram@gmail.com', '0912345678'),
(10, 6, '0923456789', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'vanquyet@gmail.com', '0923456789'),
(11, 6, '0934567890', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'thaomy@gmail.com', '0934567890'),
(12, 6, '0945678901', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'trongthang@gmail.com', '0945678901'),
(13, 6, '0956789012', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'thanhtruc@gmail.com', '0956789012'),
(14, 6, '0967890123', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'kienhao@gmail.com', '0967890123'),
(15, 6, '0978901234', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'nhaky@gmail.com', '0978901234');
SET IDENTITY_INSERT tai_khoan OFF;
GO

SET IDENTITY_INSERT nhan_vien ON;
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu) VALUES
(1, 1, 'NV001', N'Admin Hệ Thống', 1, '1988-01-01', '0999999999', 'admin@phongkham.com', '079088000001', N'140 Lê Trọng Tấn, Tân Phú, TP.HCM', N'Quản trị viên'),
(2, 2, 'NV002', N'Trần Thị Mai', 0, '1996-05-15', '0988888888', 'mai.tt@phongkham.com', '079096000002', N'Quận Tân Bình, TP.HCM', N'Trưởng quầy Tiếp tân & Thu ngân'),
(3, 3, 'NV003', N'Lê Văn Khang', 1, '1998-09-20', '0977777777', 'khang.lv@phongkham.com', '079098000003', N'Quận 12, TP.HCM', N'Nhân viên lễ tân'),
(4, 4, 'BS001', N'BS. CKII. Trần Minh Quân', 1, '1982-03-10', '0966666666', 'quan.tm@phongkham.com', '079082000004', N'Quận 10, TP.HCM', N'Trưởng Khoa Nội'),
(5, 5, 'BS002', N'BS. ThS. Phạm Phương Lan', 0, '1989-11-25', '0955555555', 'lan.pp@phongkham.com', '079089000005', N'Quận Tân Phú, TP.HCM', N'Bác sĩ chuyên khoa Nhi'),
(6, 6, 'BS003', N'BS. TS. Vũ Quang Minh', 1, '1979-07-08', '0944444444', 'minh.vq@phongkham.com', '079079000006', N'Quận 3, TP.HCM', N'Trưởng Khoa Ngoại'),
(7, 7, 'BS004', N'BS. CKI. Bùi Thu Hương', 0, '1991-04-18', '0933333333', 'huong.bt@phongkham.com', '079091000007', N'Quận Bình Thạnh, TP.HCM', N'Bác sĩ Răng Hàm Mặt');
SET IDENTITY_INSERT nhan_vien OFF;
GO

SET IDENTITY_INSERT bac_si ON;
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES
(1, 4, 1, 1, 'BS. CKII', N'15 năm kinh nghiệm chuyên sâu nội tiêu hóa, từng công tác tại BV Chợ Rẫy', 'dr_quan.jpg', 150000.00, N'Đang làm việc'),
(2, 5, 3, 4, N'Thạc sĩ - BS Nhi', N'10 năm kinh nghiệm điều trị nhi khoa tại BV Nhi Đồng 1, mát tay và ân cần', 'dr_lan.jpg', 120000.00, N'Đang làm việc'),
(3, 6, 2, 3, N'Tiến sĩ - BS Ngoại', N'18 năm kinh nghiệm phẫu thuật nội soi và chấn thương chỉnh hình', 'dr_minh.jpg', 180000.00, N'Đang làm việc'),
(4, 7, 4, 5, 'BS. CKI', N'8 năm kinh nghiệm chỉnh nha thẩm mỹ và phẫu thuật răng hàm mặt', 'dr_huong.jpg', 150000.00, N'Đang làm việc');
SET IDENTITY_INSERT bac_si OFF;
GO

SET IDENTITY_INSERT benh_nhan ON;
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan) VALUES
(1, 8, 'BN2609001', N'Hoàng Bảo Nam', '1990-05-12', N'Nam', '0901234567', 'baonam@gmail.com', '079090000001', 'GD4797931100001', N'Quận 1, TP.HCM', 'O+', N'Không có', N'Đau dạ dày nhẹ', N'Không có tiền sử bệnh lý di truyền', N'Hoàng Tuấn Kiệt', '0909111222', N'Bố', 1),
(2, 9, 'BN2609002', N'Lê Ngọc Trâm', '1995-08-22', N'Nữ', '0912345678', 'ngoctram@gmail.com', '079095000002', 'GD4797931100002', N'Quận 3, TP.HCM', 'A+', N'Dị ứng hải sản, Paracetamol', N'Viêm xoang dị ứng', N'Mẹ có tiền sử hen phế quản', N'Lê Quang Liêm', '0919222333', N'Bố', 1),
(3, 10, 'BN2609003', N'Trần Văn Quyết', '1985-11-30', N'Nam', '0923456789', 'vanquyet@gmail.com', '079085000003', 'GD4797931100003', N'Quận Tân Bình, TP.HCM', 'B+', N'Không có', N'Tăng huyết áp vô căn độ 1', N'Bố có tiền sử tăng huyết áp', N'Trần Thị Hà', '0929333444', N'Vợ', 1),
(4, 11, 'BN2609004', N'Phạm Thảo My', '2015-02-14', N'Nữ', '0934567890', 'thaomy@gmail.com', '079115000004', 'TE1797931100004', N'Quận Gò Vấp, TP.HCM', 'AB+', N'Không có', N'Viêm phế quản co thắt', N'Chị gái có tiền sử viêm mũi dị ứng', N'Phạm Minh Nhật', '0939444555', N'Bố', 1),
(5, 12, 'BN2609005', N'Đinh Trọng Thắng', '1978-04-10', N'Nam', '0945678901', 'trongthang@gmail.com', '079078000005', 'DN4797931100005', N'Quận 10, TP.HCM', 'O-', N'Không có', N'Đái tháo đường Type 2, Rối loạn lipid máu', N'Gia đình có tiền sử đái tháo đường', N'Đinh Lan Anh', '0949555666', N'Vợ', 1),
(6, 13, 'BN2609006', N'Võ Thanh Trúc', '1998-09-09', N'Nữ', '0956789012', 'thanhtruc@gmail.com', '079098000006', 'SV4797931100006', N'Quận Bình Thạnh, TP.HCM', 'A+', N'Dị ứng phấn hoa', N'Đau dạ dày, viêm đại tràng co thắt', N'Không có', N'Võ Hải Đăng', '0959666777', N'Anh trai', 1),
(7, 14, 'BN2609007', N'Ngô Kiến Hào', '2010-12-25', N'Nam', '0967890123', 'kienhao@gmail.com', '079110000007', 'HS4797931100007', N'Quận 7, TP.HCM', 'O+', N'Không có', N'Không có', N'Không có', N'Ngô Bảo Châu', '0969777888', N'Mẹ', 1),
(8, 15, 'BN2609008', N'Lý Nhã Kỳ', '1982-07-19', N'Nữ', '0978901234', 'nhaky@gmail.com', '079082000008', 'DN4797931100008', N'Quận 2, TP.HCM', 'B-', N'Không có', N'Không có tiền sử bệnh lý mạn tính', N'Không có', N'Lý Đại Nghĩa', '0979888999', N'Em trai', 1),
(9, NULL, 'BN2609009', N'Châu Gia Kiệt', '1992-01-01', N'Nam', '0981234567', 'giakiet@gmail.com', '079092000009', '', N'TP. Thủ Đức, TP.HCM', 'O+', N'Không có', N'Viêm xoang mạn tính', N'Không có', N'Châu Ánh Nguyệt', '0989000111', N'Chị gái', 0),
(10, NULL, 'BN2609010', N'Bảo Thy', '1999-03-03', N'Nữ', '0991234567', 'baothy@gmail.com', '079099000010', '', N'Quận 5, TP.HCM', 'A+', N'Không có', N'Không có', N'Không có', N'Bảo Quốc', '0999111222', N'Bố', 0);
SET IDENTITY_INSERT benh_nhan OFF;
GO

SET IDENTITY_INSERT chi_so_sinh_ton ON;
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi) VALUES
(1, 1, N'76 lần/phút', '36.8 °C', '120/80 mmHg', '99 %', N'18 lần/phút', '172 cm', '68 kg', N'23.0 (Bình thường)'),
(2, 2, N'82 lần/phút', '37.0 °C', '115/75 mmHg', '98 %', N'19 lần/phút', '160 cm', '50 kg', N'19.5 (Bình thường)'),
(3, 3, N'88 lần/phút', '36.7 °C', '145/90 mmHg', '97 %', N'20 lần/phút', '168 cm', '74 kg', N'26.2 (Tiền béo phì)'),
(4, 4, N'96 lần/phút', '37.8 °C', '95/60 mmHg', '98 %', N'24 lần/phút', '130 cm', '28 kg', N'16.6 (Bình thường)'),
(5, 5, N'74 lần/phút', '36.6 °C', '135/85 mmHg', '96 %', N'18 lần/phút', '170 cm', '78 kg', N'27.0 (Béo phì độ 1)'),
(6, 6, N'78 lần/phút', '36.9 °C', '110/70 mmHg', '99 %', N'17 lần/phút', '162 cm', '48 kg', N'18.3 (Gầy nhẹ)'),
(7, 7, N'80 lần/phút', '36.5 °C', '105/65 mmHg', '99 %', N'19 lần/phút', '155 cm', '45 kg', N'18.7 (Bình thường)'),
(8, 8, N'72 lần/phút', '36.7 °C', '120/80 mmHg', '99 %', N'16 lần/phút', '165 cm', '53 kg', N'19.5 (Bình thường)'),
(9, 9, N'76 lần/phút', '36.8 °C', '125/80 mmHg', '98 %', N'18 lần/phút', '174 cm', '70 kg', N'23.1 (Bình thường)'),
(10, 10, N'70 lần/phút', '36.6 °C', '110/70 mmHg', '99 %', N'16 lần/phút', '163 cm', '49 kg', N'18.4 (Gầy nhẹ)');
SET IDENTITY_INSERT chi_so_sinh_ton OFF;
GO

SET IDENTITY_INSERT lich_hen ON;
INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai) VALUES
(1, 'LH2609001', 1, 1, 1, 1, '2026-09-20', '08:30:00', N'Đau âm ỉ thượng vị, ợ chua, đầy bụng khó tiêu', 1, N'Đã khám'),
(2, 'LH2609002', 2, 1, 1, 1, '2026-09-21', '09:00:00', N'Đau rát họng, sốt nhẹ, nghẹt mũi', 1, N'Đã khám'),
(3, 'LH2609003', 3, 1, 1, 1, '2026-09-22', '10:00:00', N'Tái khám định kỳ huyết áp, chóng mặt buổi sáng', 2, N'Đã khám'),
(4, 'LH2609004', 4, 2, 3, 4, '2026-09-23', '08:30:00', N'Bé ho đờm nhiều, thở khò khè về đêm', 1, N'Đã khám'),
(5, 'LH2609005', 5, 3, 2, 3, '2026-09-24', '14:00:00', N'Đau sưng cổ chân phải sau khi trượt ngã', 1, N'Đã khám'),
(6, 'LH2609006', 6, 1, 1, 1, '2026-09-25', '14:30:00', N'Rối loạn tiêu hóa, đau quặn bụng sau ăn hải sản', 1, N'Đã khám'),
(7, 'LH2609007', 7, 2, 3, 4, '2026-09-28', '08:30:00', N'Khám sức khỏe tổng quát đầu năm học', 1, N'Đã duyệt'),
(8, 'LH2609008', 8, 4, 4, 5, '2026-09-28', '09:30:00', N'Đau nhức vùng hàm dưới, răng khôn mọc lệch', 1, N'Đã duyệt'),
(9, 'LH2609009', 9, 1, 1, 1, '2026-09-28', '10:30:00', N'Mất ngủ kéo dài, suy nhược cơ thể', 1, N'Chờ xác nhận'),
(10, 'LH2609010', 10, 3, 2, 3, '2026-09-29', '14:00:00', N'Khám nốt ruồi bất thường vùng cánh tay', 1, N'Chờ xác nhận');
SET IDENTITY_INSERT lich_hen OFF;
GO

SET IDENTITY_INSERT phieu_kham ON;
INSERT INTO phieu_kham (id, ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai) VALUES
(1, 'PK2609001', 1, 1, 1, 1, '2026-09-20 08:30:00', N'Đau âm ỉ vùng thượng vị, ợ chua, chướng bụng sau ăn', N'Bệnh nhân tỉnh táo, tiếp xúc tốt. Ấn đau tức nhẹ vùng thượng vị, bụng mềm, không đề kháng thành bụng.', N'Nghi ngờ viêm dạ dày HP (-)', 'K29.5 - Viêm dạ dày mạn tính, không xác định', N'Điều trị nội khoa bằng thuốc ức chế bơm proton và bao niêm mạc', N'Ăn uống đúng bữa, hạn chế đồ cay nóng và rượu bia. Tái khám sau 14 ngày.', '2026-10-04', N'Hoàn thành'),
(2, 'PK2609002', 2, 1, 1, 2, '2026-09-21 09:15:00', N'Đau họng, sốt nhẹ, ho khan', N'Họng đỏ sung huyết, amidan không phì đại, không giả mạc. Hạch góc hàm không sưng.', N'Viêm họng cấp do virus', 'J02.9 - Viêm họng cấp, không xác định', N'Điều trị triệu chứng, hạ sốt, bù nước điện giải', N'Súc miệng nước muối sinh lý ấm ngày 3-4 lần, giữ ấm cổ họng.', '2026-09-28', N'Hoàn thành'),
(3, 'PK2609003', 3, 1, 1, 3, '2026-09-22 10:10:00', N'Tái khám huyết áp, chóng mặt khi thức dậy', N'Huyết áp đo tại phòng khám 145/90 mmHg, tim đều, không âm thổi bệnh lý.', N'Tăng huyết áp nguyên phát độ 1', 'I10 - Tăng huyết áp vô căn (nguyên phát)', N'Điều chỉnh liều thuốc hạ áp, theo dõi huyết áp tại nhà ngày 2 lần', N'Ăn nhạt dưới 5g muối/ngày, tập thể dục nhẹ nhàng 30 phút/ngày.', '2026-10-22', N'Hoàn thành'),
(4, 'PK2609004', 4, 2, 4, 4, '2026-09-23 08:45:00', N'Bé ho có đờm, thở khò khè', N'Họng đỏ nhẹ, nghe phổi có ít ran rít rải rác hai phế trường, không co kéo cơ hô hấp phụ.', N'Viêm phế quản cấp', 'J20.9 - Viêm phế quản cấp, không xác định', N'Kháng sinh đường uống, siro ho thảo dược, khí dung nếu khó thở', N'Uống nhiều nước ấm, theo dõi nhịp thở của bé. Tái khám ngay nếu sốt cao hoặc thở nhanh.', '2026-09-30', N'Hoàn thành'),
(5, 'PK2609005', 5, 3, 3, 5, '2026-09-24 14:20:00', N'Đau nhức cổ chân phải sau té ngã', N'Cổ chân phải sưng nề nhẹ vùng mắt cá ngoài, ấn đau chói nhẹ, biên độ vận động hạn chế do đau.', N'Bong gân cổ chân phải độ 1', 'S93.4 - Bong gân và căng cơ khớp cổ chân', N'Nghỉ ngơi, chườm đá lạnh, băng ép thun cố định, thuốc giảm đau kháng viêm', N'Hạn chế đi lại tì đè chân đau trong 5-7 ngày đầu.', '2026-10-01', N'Hoàn thành');
SET IDENTITY_INSERT phieu_kham OFF;
GO

SET IDENTITY_INSERT phieu_chi_dinh ON;
INSERT INTO phieu_chi_dinh (id, ma_chi_dinh, phieu_kham_id, bac_si_id, thoi_gian_chi_dinh, ghi_chu, trang_thai) VALUES
(1, 'CD2609001', 1, 1, '2026-09-20 08:45:00', N'Nội soi dạ dày và tổng phân tích tế bào máu', N'Hoàn thành'),
(2, 'CD2609002', 2, 1, '2026-09-21 09:30:00', N'Xét nghiệm công thức máu', N'Hoàn thành'),
(3, 'CD2609003', 3, 1, '2026-09-22 10:25:00', N'Đo điện tim đồ 12 chuyển đạo', N'Hoàn thành'),
(4, 'CD2609004', 4, 2, '2026-09-23 09:00:00', N'Chụp X-quang tim phổi thẳng', N'Hoàn thành'),
(5, 'CD2609005', 5, 3, '2026-09-24 14:35:00', N'Chụp X-quang khớp cổ chân thẳng - nghiêng', N'Hoàn thành');
SET IDENTITY_INSERT phieu_chi_dinh OFF;
GO

SET IDENTITY_INSERT chi_tiet_chi_dinh ON;
INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, file_ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai) VALUES
(1, 1, 11, N'Niêm mạc hang vị phù nề, sung huyết nhẹ. Test Clo HP: Âm tính (-)', 'noisoi_bn01.jpg', N'BS. CKI. Nguyễn Trọng Nghĩa', '2026-09-20 09:30:00', N'Hoàn thành'),
(2, 1, 7, N'Hồng cầu: 4.85 T/L, Bạch cầu: 6.8 G/L, Tiểu cầu: 235 G/L. Các chỉ số trong giới hạn bình thường.', 'xn_mau_bn01.pdf', N'KTV. Lê Thị Thu', '2026-09-20 09:15:00', N'Hoàn thành'),
(3, 2, 7, N'Bạch cầu hơi tăng 10.2 G/L (ưu thế lympho), CRP bình thường.', 'xn_mau_bn02.pdf', N'KTV. Lê Thị Thu', '2026-09-21 10:00:00', N'Hoàn thành'),
(4, 3, 10, N'Nhịp xoang đều 78 lần/phút, trục trung gian, không thấy dấu hiệu thiếu máu cơ tim cục bộ.', 'ecg_bn03.pdf', N'KTV. Trần Văn Đức', '2026-09-22 10:45:00', N'Hoàn thành'),
(5, 4, 9, N'Tăng đậm các nhánh phế quản rốn phổi hai bên, không thấy nốt thâm nhiễm nhu mô phổi.', 'xquang_bn04.jpg', N'KTV. Trần Văn Đức', '2026-09-23 09:20:00', N'Hoàn thành'),
(6, 5, 9, N'Không thấy hình ảnh gãy xương hoặc trật khớp cổ chân. Khe khớp mắt cá bình thường.', 'xquang_bn05.jpg', N'KTV. Trần Văn Đức', '2026-09-24 14:55:00', N'Hoàn thành');
SET IDENTITY_INSERT chi_tiet_chi_dinh OFF;
GO

SET IDENTITY_INSERT don_thuoc ON;
INSERT INTO don_thuoc (id, ma_don_thuoc, phieu_kham_id, bac_si_id, thoi_gian_ke, loi_dan, trang_thai) VALUES
(1, 'DT2609001', 1, 1, '2026-09-20 09:45:00', N'Uống thuốc đúng giờ, kiêng chua cay, rượu bia', N'Đã cấp thuốc'),
(2, 'DT2609002', 2, 1, '2026-09-21 10:15:00', N'Uống nhiều nước ấm, súc họng nước muối', N'Đã cấp thuốc'),
(3, 'DT2609003', 3, 1, '2026-09-22 11:00:00', N'Kiêng ăn mặn, uống thuốc hạ áp mỗi sáng', N'Đã cấp thuốc'),
(4, 'DT2609004', 4, 2, '2026-09-23 09:45:00', N'Uống siro ho và kháng sinh đúng liều lượng', N'Đã cấp thuốc'),
(5, 'DT2609005', 5, 3, '2026-09-24 15:15:00', N'Uống thuốc giảm đau sau ăn no, chườm lạnh', N'Đã cấp thuốc');
SET IDENTITY_INSERT don_thuoc OFF;
GO

SET IDENTITY_INSERT chi_tiet_don_thuoc ON;
INSERT INTO chi_tiet_don_thuoc (id, don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung) VALUES
(1, 1, 5, 28, N'Ngày 1 viên', N'Uống 1 viên trước ăn sáng 30 phút'),
(2, 1, 6, 20, N'Ngày 2 gói', N'Uống 1 gói sau ăn 2 giờ hoặc khi đau tức bụng'),
(3, 2, 1, 15, N'Ngày 2-3 lần, lần 1 viên', N'Uống khi sốt hoặc đau rát họng, sau ăn'),
(4, 2, 4, 10, N'Ngày 1 viên', N'Uống 1 viên trước khi đi ngủ'),
(5, 2, 10, 2, N'Ngày 3-4 lần', N'Súc miệng họng sâu bằng nước muối sinh lý'),
(6, 4, 2, 14, N'Ngày 2 lần, lần 1 viên', N'Uống sau bữa ăn sáng và tối'),
(7, 4, 9, 1, N'Ngày 3 lần, lần 5ml', N'Uống sau ăn 15 phút'),
(8, 5, 8, 14, N'Ngày 2 lần, lần 1 viên', N'Uống sau ăn no trưa và tối');
SET IDENTITY_INSERT chi_tiet_don_thuoc OFF;
GO

SET IDENTITY_INSERT hoa_don ON;
INSERT INTO hoa_don (id, ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu) VALUES
(1, 'HD2609001', 1, 1, 1336000.00, 300000.00, 0.00, 1036000.00, 'Momo', N'Đã thanh toán', '2026-09-20 10:00:00', N'Trần Thị Mai'),
(2, 'HD2609002', 2, 2, 400000.00, 120000.00, 0.00, 280000.00, N'Chuyển khoản', N'Đã thanh toán', '2026-09-21 10:30:00', N'Trần Thị Mai'),
(3, 'HD2609003', 3, 3, 300000.00, 105000.00, 0.00, 195000.00, N'Tiền mặt', N'Đã thanh toán', '2026-09-22 11:15:00', N'Lê Văn Khang'),
(4, 'HD2609004', 4, 4, 437000.00, 140000.00, 0.00, 297000.00, N'Chuyển khoản', N'Đã thanh toán', '2026-09-23 10:00:00', N'Trần Thị Mai'),
(5, 'HD2609005', 5, 5, 399000.00, 0.00, 50000.00, 349000.00, N'Tiền mặt', N'Đã thanh toán', '2026-09-24 15:30:00', N'Lê Văn Khang');
SET IDENTITY_INSERT hoa_don OFF;
GO

SET IDENTITY_INSERT chi_tiet_hoa_don ON;
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES
(1, 1, N'Khám bệnh', N'Khám Nội Tổng Quát', 1, 1, 150000.00, 150000.00),
(2, 1, N'Dịch vụ CLS', N'Nội soi dạ dày tá tràng ống mềm', 11, 1, 600000.00, 600000.00),
(3, 1, N'Dịch vụ CLS', N'Tổng phân tích tế bào máu ngoại vi', 7, 1, 150000.00, 150000.00),
(4, 1, N'Thuốc', N'Esomeprazole 40mg (28 Viên)', 5, 28, 12000.00, 336000.00),
(5, 1, N'Thuốc', N'Phosphalugel 20g (20 Gói)', 6, 20, 5000.00, 100000.00),
(6, 2, N'Khám bệnh', N'Khám Nội Tổng Quát', 1, 1, 150000.00, 150000.00),
(7, 2, N'Dịch vụ CLS', N'Tổng phân tích tế bào máu ngoại vi', 7, 1, 150000.00, 150000.00),
(8, 2, N'Thuốc', N'Toa thuốc điều trị viêm họng cấp', NULL, 1, 100000.00, 100000.00),
(9, 3, N'Khám bệnh', N'Khám Nội Tổng Quát (Tái khám)', 1, 1, 150000.00, 150000.00),
(10, 3, N'Dịch vụ CLS', N'Đo điện tim đồ 12 chuyển đạo', 10, 1, 150000.00, 150000.00),
(11, 4, N'Khám bệnh', N'Khám Nhi Khoa', 2, 1, 120000.00, 120000.00),
(12, 4, N'Dịch vụ CLS', N'Chụp X-Quang Tim Phổi thẳng', 9, 1, 200000.00, 200000.00),
(13, 4, N'Thuốc', N'Toa thuốc viêm phế quản', NULL, 1, 117000.00, 117000.00),
(14, 5, N'Khám bệnh', N'Khám Ngoại Khoa', 3, 1, 150000.00, 150000.00),
(15, 5, N'Dịch vụ CLS', N'Chụp X-Quang khớp cổ chân', 9, 1, 200000.00, 200000.00),
(16, 5, N'Thuốc', N'Ibuprofen 400mg (14 Viên)', 8, 14, 3500.00, 49000.00);
SET IDENTITY_INSERT chi_tiet_hoa_don OFF;
GO

SET IDENTITY_INSERT bai_viet ON;
INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai) VALUES
(1, 4, N'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', 'benh-cam-cum-mua-giao-mua', N'Cẩm Nang Y Tế', N'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', N'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', 'cam-cum.jpg', 320, '2026-09-20 08:00:00', 1),
(2, 5, N'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', 'cham-soc-rang-mieng-cho-tre', N'Nhi Khoa', N'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', N'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng chứa flour phù hợp lứa tuổi, hạn chế bánh kẹo ngọt trước khi đi ngủ...', 'rang-mieng-tre.jpg', 215, '2026-09-21 09:30:00', 1),
(3, 6, N'Dấu hiệu thoái hóa khớp gối và phương pháp điều trị mới', 'dau-hieu-thoai-hoa-khop-goi', N'Cơ Xương Khớp', N'Thoái hóa khớp gối là căn bệnh phổ biến ở người trung niên và cao tuổi. Phát hiện sớm các dấu hiệu đau khớp khi leo cầu thang, lục khục khi vận động giúp bảo tồn sụn khớp tối ưu.', N'Nội dung chi tiết về các giải pháp điều trị thoái hóa khớp gối: vật lý trị liệu, tiêm chất nhờn nhân tạo, kiểm soát cân nặng và các bài tập tăng cường sức cơ đùi...', 'thoai-hoa-khop.jpg', 410, '2026-09-22 14:15:00', 1),
(4, 4, N'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', 'kham-suc-khoe-tong-quat-dinh-ky', N'Tin Tức Phòng Khám', N'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', N'Nội dung chi tiết về gói khám tổng quát tại H2T Healthcare: bao gồm xét nghiệm máu tổng thể, siêu âm ổ bụng, chụp X-quang tim phổi và đo điện tim đồ...', 'kham-tong-quat.jpg', 580, '2026-09-23 10:00:00', 1),
(5, 7, N'Những điều cần biết trước khi nhổ răng khôn mọc lệch', 'nhung-dieu-can-biet-khi-nho-rang-khon', N'Răng Hàm Mặt', N'Răng khôn mọc ngầm, mọc lệch gây giắt thức ăn, sâu răng bên cạnh và viêm lợi trùm. Tìm hiểu quy trình nhổ răng không đau với công nghệ máy siêu âm hiện đại.', N'Nội dung chi tiết về chỉ định nhổ răng khôn, quy trình chụp phim CT Cone Beam 3D, xét nghiệm máu trước tiểu phẫu và chế độ ăn mềm sau khi nhổ...', 'nho-rang-khon.jpg', 190, '2026-09-24 16:00:00', 1);
SET IDENTITY_INSERT bai_viet OFF;
GO

