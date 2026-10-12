-- CƠ SỞ DỮ LIỆU HỆ THỐNG QUẢN LÝ PHÒNG KHÁM ĐA KHOA (H2T HEALTHCARE HIS / EMR)
-- PHIÊN BẢN CHUẨN: MICROSOFT SQL SERVER 2016 / 2019 / 2022 (T-SQL)

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

-- 3. TẠO CÁC BẢNG DỮ LIỆU
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
    gia_kham_mac_dinh DECIMAL(12, 2) DEFAULT 150000.00
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
    da_doc BIT DEFAULT 0,
    thoi_gian_tao DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE CASCADE
);

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
CREATE INDEX idx_benhnhan_sdt ON benh_nhan(sdt);
CREATE INDEX idx_benhnhan_cccd ON benh_nhan(cccd);
CREATE INDEX idx_benhnhan_ma ON benh_nhan(ma_benh_nhan);
CREATE INDEX idx_lichhen_ngay ON lich_hen(ngay_hen);
CREATE INDEX idx_lichhen_trangthai ON lich_hen(trang_thai);
CREATE INDEX idx_phieukham_ngay ON phieu_kham(thoi_gian_kham);
CREATE INDEX idx_hoadon_ngay ON hoa_don(thoi_gian_thanh_toan);
GO

-- 5. NẠP DỮ LIỆU BAN ĐẦU (CHỈ 1 ADMIN VÀ 1 BỆNH NHÂN)
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
(10, 8, 'DV_ECG', N'Đo điện tim đồ 12 chuyển đạo (ECG)', N'Thăm dò chức năng', 150000.00, 70, N'Khảo sát nhịp xoang, rối loạn dẫn truyền tim');
SET IDENTITY_INSERT dich_vu OFF;
GO

SET IDENTITY_INSERT thuoc ON;
INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung) VALUES
(1, 'TH001', N'Paracetamol 500mg', 'Paracetamol', '500mg', N'Viên', 2000.00, 5000, N'Dược Hậu Giang', N'Việt Nam', N'Uống 1-2 viên khi sốt trên 38.5°C hoặc đau nhức'),
(2, 'TH002', N'Amoxicillin 500mg', 'Amoxicillin trihydrat', '500mg', N'Viên', 3000.00, 2000, 'Imexpharm', N'Việt Nam', N'Kháng sinh: Uống 1 viên sau ăn, ngày 2 lần'),
(3, 'TH003', N'Oresol 245', 'Glucose, Natri clorid, Kali clorid', '245 mOsm/L', N'Gói', 5000.00, 1000, 'Traphaco', N'Việt Nam', N'Pha đúng 1 gói với 200ml nước sôi để nguội'),
(4, 'TH004', N'Loratadin 10mg', 'Loratadin', '10mg', N'Viên', 4000.00, 1500, 'Pymepharco', N'Việt Nam', N'Thuốc kháng histamin: Uống 1 viên vào buổi tối'),
(5, 'TH005', N'Esomeprazole 40mg', 'Esomeprazole magnesium', '40mg', N'Viên', 12000.00, 3000, 'AstraZeneca', N'Thụy Điển', N'Giảm tiết acid dạ dày: Uống 1 viên trước bữa ăn sáng 30 phút'),
(6, 'TH006', N'Phosphalugel 20g', 'Aluminium phosphate', '20g', N'Gói', 5000.00, 2500, 'Boehringer Ingelheim', N'Pháp', N'Uống 1 gói khi có cơn đau thượng vị'),
(7, 'TH007', N'Men vi sinh Enterogermina', 'Bacillus clausii', '2 tỷ bào tử/5ml', N'Ống', 9000.00, 1200, 'Sanofi', N'Ý', N'Uống trực tiếp 1-2 ống/ngày sau bữa ăn'),
(8, 'TH008', N'Ibuprofen 400mg', 'Ibuprofen', '400mg', N'Viên', 3500.00, 2500, 'Stada', N'Việt Nam', N'Kháng viêm giảm đau cơ xương khớp, uống sau ăn no'),
(9, 'TH009', N'Siro ho thảo dược Prospan', 'Cao khô lá thường xuân', '100ml', N'Chai', 75000.00, 300, 'Engelhard', N'Đức', N'Uống 5ml/lần, ngày 3 lần sau ăn'),
(10, 'TH010', N'Nước muối sinh lý NaCl 0.9%', 'Natri Clorid 0.9%', '500ml', N'Chai', 10000.00, 800, 'Pharmedic', N'Việt Nam', N'Dùng súc miệng họng hoặc rửa vết thương');
SET IDENTITY_INSERT thuoc OFF;
GO

-- TÀI KHOẢN DUY NHẤT: 1 ADMIN VÀ 1 BỆNH NHÂN
SET IDENTITY_INSERT tai_khoan ON;
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt) VALUES
(1, 1, 'admin', 'scrypt:32768:8:1$wte2IwGnBVO1lRWL$3da8cd29b71656229c22086ff7164745647f790916b2f3949a826972b6c8f4896f4fd90b2856affb5af79c1274b86fc0d20e1ee0da464623a7117faa4984e03c', 'admin@phongkham.com', '0999999999'),
(2, 6, '0901234567', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'baonam@gmail.com', '0901234567');
SET IDENTITY_INSERT tai_khoan OFF;
GO

SET IDENTITY_INSERT nhan_vien ON;
INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu) VALUES
(1, 1, 'NV001', N'Admin Hệ Thống', 1, '1988-01-01', '0999999999', 'admin@phongkham.com', '079088000001', N'140 Lê Trọng Tấn, Tân Phú, TP.HCM', N'Quản trị viên');
SET IDENTITY_INSERT nhan_vien OFF;
GO

SET IDENTITY_INSERT benh_nhan ON;
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, co_tai_khoan) VALUES
(1, 2, 'BN2609001', N'Hoàng Bảo Nam', '1990-05-12', N'Nam', '0901234567', 'baonam@gmail.com', '079090000001', 'GD4797931100001', N'Quận 1, TP.HCM', 'O+', N'Không có', N'Đau dạ dày nhẹ', 1);
SET IDENTITY_INSERT benh_nhan OFF;
GO

SET IDENTITY_INSERT chi_so_sinh_ton ON;
INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi) VALUES
(1, 1, N'75 lần/phút', '36.8 °C', '120/80 mmHg', '99 %', N'18 lần/phút', '170 cm', '65 kg', N'22.5 (Bình thường)');
SET IDENTITY_INSERT chi_so_sinh_ton OFF;
GO

SET IDENTITY_INSERT bai_viet ON;
INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai) VALUES
(1, 1, N'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', 'benh-cam-cum-mua-giao-mua', N'Cẩm Nang Y Tế', N'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', N'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', 'cam-cum.jpg', 320, '2026-09-20 08:00:00', 1),
(2, 1, N'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', 'cham-soc-rang-mieng-cho-tre', N'Nhi Khoa', N'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', N'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng phù hợp lứa tuổi...', 'rang-mieng-tre.jpg', 215, '2026-09-21 09:30:00', 1),
(3, 1, N'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', 'kham-suc-khoe-tong-quat-dinh-ky', N'Tin Tức Phòng Khám', N'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', N'Nội dung chi tiết về các gói khám tổng quát tại H2T Healthcare...', 'kham-tong-quat.jpg', 580, '2026-09-23 10:00:00', 1);
SET IDENTITY_INSERT bai_viet OFF;
GO
