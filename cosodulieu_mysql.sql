-- CƠ SỞ DỮ LIỆU HỆ THỐNG QUẢN LÝ PHÒNG KHÁM ĐA KHOA (H2T HEALTHCARE HIS / EMR)
-- PHIÊN BẢN CHUẨN: MYSQL / MARIADB (XAMPP / PHPMYADMIN / WORKBENCH)

CREATE DATABASE IF NOT EXISTS `quan_ly_phong_kham` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `quan_ly_phong_kham`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS chi_tiet_hoa_don;
DROP TABLE IF EXISTS hoa_don;
DROP TABLE IF EXISTS chi_tiet_don_thuoc;
DROP TABLE IF EXISTS don_thuoc;
DROP TABLE IF EXISTS chi_tiet_chi_dinh;
DROP TABLE IF EXISTS phieu_chi_dinh;
DROP TABLE IF EXISTS chi_so_sinh_ton;
DROP TABLE IF EXISTS phieu_kham;
DROP TABLE IF EXISTS lich_hen;
DROP TABLE IF EXISTS lich_lam_viec;
DROP TABLE IF EXISTS phan_hoi;
DROP TABLE IF EXISTS hom_thu_gop_y;
DROP TABLE IF EXISTS thong_bao;
DROP TABLE IF EXISTS bai_viet;
DROP TABLE IF EXISTS benh_nhan;
DROP TABLE IF EXISTS bac_si;
DROP TABLE IF EXISTS nhan_vien;
DROP TABLE IF EXISTS tai_khoan;
DROP TABLE IF EXISTS thuoc;
DROP TABLE IF EXISTS dich_vu;
DROP TABLE IF EXISTS phong_kham;
DROP TABLE IF EXISTS chuyen_khoa;
DROP TABLE IF EXISTS vai_tro;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE vai_tro (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_vai_tro VARCHAR(30) NOT NULL UNIQUE,
    ten_vai_tro VARCHAR(50) NOT NULL,
    mo_ta VARCHAR(255)
);

CREATE TABLE chuyen_khoa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_khoa VARCHAR(20) NOT NULL UNIQUE,
    ten_khoa VARCHAR(100) NOT NULL,
    mo_ta TEXT,
    icon VARCHAR(100) DEFAULT 'fa-stethoscope',
    gia_kham_mac_dinh DECIMAL(12, 2) DEFAULT 150000.00,
    trang_thai BIT DEFAULT 1
);

CREATE TABLE phong_kham (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chuyen_khoa_id INT NOT NULL,
    ma_phong VARCHAR(20) NOT NULL UNIQUE,
    ten_phong VARCHAR(100) NOT NULL,
    vi_tri_tang VARCHAR(50) DEFAULT 'Tầng 1',
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

CREATE TABLE dich_vu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chuyen_khoa_id INT NULL,
    ma_dich_vu VARCHAR(30) NOT NULL UNIQUE,
    ten_dich_vu VARCHAR(255) NOT NULL,
    loai_dich_vu VARCHAR(50) DEFAULT 'Khám bệnh',
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    bhyt_chi_tra_pt INT DEFAULT 0,
    mo_ta VARCHAR(255),
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);


CREATE TABLE thuoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_thuoc VARCHAR(30) NOT NULL UNIQUE,
    ten_thuoc VARCHAR(255) NOT NULL,
    hoat_chat VARCHAR(255),
    ham_luong VARCHAR(100),
    don_vi_tinh VARCHAR(50) NOT NULL,
    don_gia DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    so_luong_ton INT DEFAULT 0,
    hang_san_xuat VARCHAR(150),
    nuoc_san_xuat VARCHAR(100),
    huong_dan_su_dung VARCHAR(255),
    trang_thai BIT DEFAULT 1
);

CREATE TABLE tai_khoan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vai_tro_id INT NOT NULL,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    sdt VARCHAR(15),
    trang_thai BIT DEFAULT 1,
    ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
    lan_dang_nhap_cuoi DATETIME NULL,
    FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id)
);

CREATE TABLE nhan_vien (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tai_khoan_id INT NOT NULL UNIQUE,
    ma_nhan_vien VARCHAR(20) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    gioi_tinh BIT DEFAULT 1,
    ngay_sinh DATE NULL,
    sdt VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    cccd VARCHAR(20) UNIQUE,
    dia_chi VARCHAR(255),
    chuc_vu VARCHAR(100) NOT NULL,
    ngay_vao_lam DATE DEFAULT (CURRENT_DATE),
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
);

CREATE TABLE bac_si (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nhan_vien_id INT NOT NULL UNIQUE,
    chuyen_khoa_id INT NOT NULL,
    phong_kham_chinh_id INT NULL,
    hoc_vi VARCHAR(50) DEFAULT 'Bác sĩ',
    kinh_nghiem TEXT,
    avatar VARCHAR(255) DEFAULT 'default_doctor.png',
    gia_kham DECIMAL(12, 2) DEFAULT 150000.00,
    trang_thai_lam_viec VARCHAR(50) DEFAULT 'Đang làm việc',
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id) ON DELETE CASCADE,
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
    FOREIGN KEY (phong_kham_chinh_id) REFERENCES phong_kham(id)
);

CREATE TABLE benh_nhan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tai_khoan_id INT NULL UNIQUE,
    ma_benh_nhan VARCHAR(20) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    ngay_sinh DATE NOT NULL,
    gioi_tinh VARCHAR(10) NOT NULL DEFAULT 'Nam',
    sdt VARCHAR(15) NOT NULL,
    email VARCHAR(100),
    cccd VARCHAR(20),
    bhyt VARCHAR(30),
    dia_chi VARCHAR(255),
    nhom_mau VARCHAR(10) DEFAULT 'Chưa rõ',
    di_ung TEXT,
    tien_su_benh TEXT,
    tien_su_gia_dinh TEXT,
    nguoi_than_ho_ten VARCHAR(100),
    nguoi_than_sdt VARCHAR(15),
    nguoi_than_quan_he VARCHAR(50),
    co_tai_khoan BIT DEFAULT 0,
    ngay_tao DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE SET NULL
);

CREATE TABLE chi_so_sinh_ton (
    id INT AUTO_INCREMENT PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    mach VARCHAR(20) DEFAULT '75 lần/phút',
    nhiet_do VARCHAR(20) DEFAULT '36.8 °C',
    huyet_ap VARCHAR(20) DEFAULT '120/80 mmHg',
    spo2 VARCHAR(20) DEFAULT '99 %',
    nhip_tho VARCHAR(20) DEFAULT '18 lần/phút',
    chieu_cao VARCHAR(20) DEFAULT '170 cm',
    can_nang VARCHAR(20) DEFAULT '65 kg',
    bmi VARCHAR(50) DEFAULT '22.5 (Bình thường)',
    thoi_gian_do DATETIME DEFAULT CURRENT_TIMESTAMP,
    ghi_chu VARCHAR(255),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE
);

CREATE TABLE lich_lam_viec (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_lich_hen VARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NULL,
    chuyen_khoa_id INT NOT NULL,
    phong_kham_id INT NULL,
    ngay_hen DATE NOT NULL,
    gio_hen TIME NOT NULL,
    ly_do_kham TEXT,
    loai_lich_hen TINYINT DEFAULT 1,
    trang_thai VARCHAR(50) DEFAULT 'Chờ xác nhận',
    ngay_dat DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
);

CREATE TABLE phieu_kham (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_phieu VARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NULL,
    phong_kham_id INT NOT NULL,
    lich_hen_id INT NULL,
    thoi_gian_kham DATETIME DEFAULT CURRENT_TIMESTAMP,
    ly_do_kham TEXT,
    trieu_chung TEXT,
    chan_doan_so_bo TEXT,
    chan_doan_icd VARCHAR(255),
    huong_dieu_tri TEXT,
    loi_dan TEXT,
    ngay_tai_kham DATE NULL,
    trang_thai VARCHAR(50) DEFAULT 'Hoàn thành',
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id),
    FOREIGN KEY (lich_hen_id) REFERENCES lich_hen(id)
);

CREATE TABLE phieu_chi_dinh (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_chi_dinh VARCHAR(30) NOT NULL UNIQUE,
    phieu_kham_id INT NOT NULL,
    bac_si_id INT NULL,
    thoi_gian_chi_dinh DATETIME DEFAULT CURRENT_TIMESTAMP,
    ghi_chu VARCHAR(255),
    trang_thai VARCHAR(50) DEFAULT 'Hoàn thành',
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
);

CREATE TABLE chi_tiet_chi_dinh (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phieu_chi_dinh_id INT NOT NULL,
    dich_vu_id INT NOT NULL,
    ket_qua TEXT,
    file_ket_qua VARCHAR(255),
    ktv_thuc_hien VARCHAR(100),
    thoi_gian_thuc_hien DATETIME,
    trang_thai VARCHAR(50) DEFAULT 'Hoàn thành',
    FOREIGN KEY (phieu_chi_dinh_id) REFERENCES phieu_chi_dinh(id) ON DELETE CASCADE,
    FOREIGN KEY (dich_vu_id) REFERENCES dich_vu(id)
);

CREATE TABLE don_thuoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_don_thuoc VARCHAR(30) NOT NULL UNIQUE,
    phieu_kham_id INT NOT NULL,
    bac_si_id INT NULL,
    thoi_gian_ke DATETIME DEFAULT CURRENT_TIMESTAMP,
    loi_dan TEXT,
    trang_thai VARCHAR(50) DEFAULT 'Đã cấp thuốc',
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
);

CREATE TABLE chi_tiet_don_thuoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    don_thuoc_id INT NOT NULL,
    thuoc_id INT NOT NULL,
    so_luong INT NOT NULL DEFAULT 1,
    lieu_dung VARCHAR(100),
    cach_dung VARCHAR(255),
    FOREIGN KEY (don_thuoc_id) REFERENCES don_thuoc(id) ON DELETE CASCADE,
    FOREIGN KEY (thuoc_id) REFERENCES thuoc(id)
);

CREATE TABLE hoa_don (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_hoa_don VARCHAR(30) NOT NULL UNIQUE,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NULL,
    tong_tien DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    tien_bhyt DECIMAL(12, 2) DEFAULT 0.00,
    giam_gia DECIMAL(12, 2) DEFAULT 0.00,
    thanh_tien DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    hinh_thuc_thanh_toan VARCHAR(50) DEFAULT 'Tiền mặt',
    trang_thai VARCHAR(50) DEFAULT 'Đã thanh toán',
    thoi_gian_thanh_toan DATETIME DEFAULT CURRENT_TIMESTAMP,
    nhan_vien_thu VARCHAR(100),
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE chi_tiet_hoa_don (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hoa_don_id INT NOT NULL,
    loai_khoan_thu VARCHAR(50) NOT NULL,
    ten_khoan_thu VARCHAR(255) NOT NULL,
    tham_chieu_id INT NULL,
    so_luong INT DEFAULT 1,
    don_gia DECIMAL(12, 2) DEFAULT 0.00,
    thanh_tien DECIMAL(12, 2) DEFAULT 0.00,
    FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(id) ON DELETE CASCADE
);

CREATE TABLE thong_bao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tai_khoan_id INT NOT NULL,
    tieu_de VARCHAR(200) NOT NULL,
    noi_dung TEXT NOT NULL,
    loai_thong_bao VARCHAR(50) DEFAULT 'Hệ thống',
    lien_ket VARCHAR(255) NULL,
    da_doc BIT DEFAULT 0,
    thoi_gian_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id) ON DELETE CASCADE
);

CREATE TABLE phan_hoi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NULL,
    chu_de VARCHAR(100) DEFAULT 'Dịch vụ khám bệnh',
    diem_danh_gia TINYINT NOT NULL CHECK (diem_danh_gia BETWEEN 1 AND 5),
    noi_dung TEXT,
    trang_thai VARCHAR(50) DEFAULT 'Chờ tiếp nhận',
    tra_loi TEXT NULL,
    ngay_tra_loi DATETIME NULL,
    nguoi_tra_loi VARCHAR(100) NULL,
    thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE,
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE hom_thu_gop_y (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ho_ten VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    sdt VARCHAR(15),
    chu_de VARCHAR(200),
    noi_dung TEXT NOT NULL,
    ngay_gui DATETIME DEFAULT CURRENT_TIMESTAMP,
    trang_thai VARCHAR(50) DEFAULT 'Chưa xử lý'
);

CREATE TABLE lich_su_nhac_nho (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lich_hen_id INT NULL,
    phieu_kham_id INT NULL,
    benh_nhan_id INT NOT NULL,
    loai_nhac VARCHAR(50) NOT NULL,
    ngay_nhac DATE NULL,
    kenh_gui VARCHAR(20) DEFAULT 'IN_APP',
    trang_thai VARCHAR(50) DEFAULT 'THANH_CONG',
    loi_gui TEXT NULL,
    thoi_gian_gui DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lich_hen_id) REFERENCES lich_hen(id) ON DELETE SET NULL,
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE SET NULL,
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id) ON DELETE CASCADE
);

CREATE TABLE lich_su_sao_luu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loai_thao_tac VARCHAR(20) NOT NULL,
    ten_tap_tin VARCHAR(255) NOT NULL,
    duong_dan VARCHAR(500) NULL,
    loai_csdl VARCHAR(50) NOT NULL,
    dung_luong BIGINT DEFAULT 0,
    nguoi_thuc_hien VARCHAR(100) NULL,
    trang_thai VARCHAR(50) DEFAULT 'SUCCESS',
    ghi_chu TEXT NULL,
    thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE bai_viet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tac_gia_id INT NULL,
    tieu_de VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    danh_muc VARCHAR(100) DEFAULT 'Cẩm Nang Y Tế',
    tom_tat TEXT,
    noi_dung TEXT,
    hinh_anh VARCHAR(255),
    luot_xem INT DEFAULT 0,
    ngay_dang DATETIME DEFAULT CURRENT_TIMESTAMP,
    trang_thai BIT DEFAULT 1,
    FOREIGN KEY (tac_gia_id) REFERENCES nhan_vien(id)
);

CREATE INDEX idx_benhnhan_sdt ON benh_nhan(sdt);
CREATE INDEX idx_benhnhan_cccd ON benh_nhan(cccd);
CREATE INDEX idx_benhnhan_ma ON benh_nhan(ma_benh_nhan);
CREATE INDEX idx_lichhen_ngay ON lich_hen(ngay_hen);
CREATE INDEX idx_lichhen_trangthai ON lich_hen(trang_thai);
CREATE INDEX idx_phieukham_ngay ON phieu_kham(thoi_gian_kham);
CREATE INDEX idx_hoadon_ngay ON hoa_don(thoi_gian_thanh_toan);

-- DỮ LIỆU BAN ĐẦU
INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES
(1, 'ADMIN', 'Quản trị viên', 'Toàn quyền cấu hình và quản trị hệ thống phòng khám'),
(2, 'LETAN', 'Nhân viên lễ tân / Thu ngân', 'Tiếp đón bệnh nhân, sắp xếp lịch hẹn, thu ngân viện phí'),
(3, 'BACSI', 'Bác sĩ chuyên khoa', 'Khám bệnh, chẩn đoán, kê đơn thuốc và chỉ định cận lâm sàng'),
(4, 'DUOCSI', 'Dược sĩ / Thủ kho dược', 'Quản lý kho thuốc, cấp phát thuốc theo toa'),
(5, 'KTV', 'Kỹ thuật viên xét nghiệm', 'Thực hiện xét nghiệm, X-quang, chẩn đoán hình ảnh'),
(6, 'BENHNHAN', 'Bệnh nhân', 'Khách hàng sử dụng cổng thông tin y tế bệnh nhân');

INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh) VALUES
(1, 'KHOA_NOI', 'Khoa Nội Tổng Quát', 'Khám, chẩn đoán và điều trị bệnh lý tim mạch, tiêu hóa, hô hấp, cơ xương khớp', 'fa-stethoscope', 150000.00),
(2, 'KHOA_NGOAI', 'Khoa Ngoại Tổng Quát', 'Khám và điều trị ngoại khoa, tiểu phẫu, xử lý vết thương', 'fa-syringe', 150000.00),
(3, 'KHOA_NHI', 'Khoa Nhi', 'Chăm sóc và điều trị chuyên sâu bệnh lý trẻ em, tư vấn dinh dưỡng', 'fa-baby', 120000.00),
(4, 'KHOA_RHM', 'Khoa Răng Hàm Mặt', 'Nha khoa tổng quát, nhổ răng khôn, niềng răng, cạo vôi răng', 'fa-tooth', 150000.00),
(5, 'KHOA_SAN', 'Khoa Sản - Phụ Khoa', 'Quản lý thai kỳ, siêu âm 4D, tầm soát và điều trị phụ khoa', 'fa-person-pregnant', 180000.00),
(6, 'KHOA_TMH', 'Khoa Tai Mũi Họng', 'Nội soi tai mũi họng, điều trị viêm xoang, viêm họng hạt, viêm amidan', 'fa-head-side-cough', 150000.00),
(7, 'KHOA_MAT', 'Khoa Mắt', 'Đo tật khúc xạ, khám và điều trị bệnh lý đáy mắt, giác mạc', 'fa-eye', 150000.00),
(8, 'KHOA_CLS', 'Khoa Cận Lâm Sàng', 'Trung tâm xét nghiệm hóa sinh, huyết học và chẩn đoán hình ảnh', 'fa-vial', 100000.00);

INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES
(1, 1, 'PK101', 'Phòng Khám Nội 1', 'Tầng 1 - Khu A', 1),
(2, 1, 'PK102', 'Phòng Khám Nội 2', 'Tầng 1 - Khu A', 1),
(3, 2, 'PK103', 'Phòng Khám Ngoại & Tiểu Phẫu', 'Tầng 1 - Khu B', 1),
(4, 3, 'PK201', 'Phòng Khám Nhi 1', 'Tầng 2 - Khu A', 1),
(5, 4, 'PK202', 'Phòng Nha Khoa Kỹ Thuật Cao', 'Tầng 2 - Khu B', 1),
(6, 5, 'PK203', 'Phòng Khám Sản Phụ Khoa', 'Tầng 2 - Khu B', 1),
(7, 8, 'XN001', 'Phòng Xét Nghiệm Huyết Học - Hóa Sinh', 'Tầng 1 - Khu C', 1),
(8, 8, 'CDHA01', 'Phòng Siêu Âm Màu & Chụp X-Quang', 'Tầng 1 - Khu C', 1);

INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta) VALUES
(1, 1, 'DV_KHAM_NOI', 'Khám Nội Tổng Quát', 'Khám bệnh', 150000.00, 80, 'Khám và tư vấn toàn diện các bệnh lý nội khoa'),
(2, 3, 'DV_KHAM_NHI', 'Khám Nhi Khoa', 'Khám bệnh', 120000.00, 80, 'Khám và tư vấn sức khỏe trẻ em'),
(3, 2, 'DV_KHAM_NGOAI', 'Khám Ngoại Khoa', 'Khám bệnh', 150000.00, 80, 'Khám và tư vấn tiểu phẫu ngoại khoa'),
(4, 4, 'DV_NHO_RANG', 'Tiểu phẫu Nhổ răng khôn', 'Thủ thuật', 1000000.00, 0, 'Nhổ răng khôn mọc lệch, không đau'),
(5, 4, 'DV_CAO_VOI', 'Cạo vôi răng & Đánh bóng', 'Thủ thuật', 200000.00, 0, 'Làm sạch mảng bám cao răng bằng sóng siêu âm'),
(6, 8, 'DV_SIEU_AM', 'Siêu âm Doppler màu ổ bụng tổng quát', 'Chẩn đoán hình ảnh', 250000.00, 50, 'Khảo sát gan, mật, tụy, lách, thận, bàng quang'),
(7, 8, 'DV_XN_MAU', 'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', 'Xét nghiệm', 150000.00, 80, 'Kiểm tra hồng cầu, bạch cầu, tiểu cầu, thiếu máu'),
(8, 8, 'DV_XN_NT', 'Tổng phân tích nước tiểu 10 thông số', 'Xét nghiệm', 100000.00, 80, 'Kiểm tra đường, đạm, tế bào vi thể nước tiểu'),
(9, 8, 'DV_XQUANG', 'Chụp X-Quang Tim Phổi thẳng kỹ thuật số', 'Chẩn đoán hình ảnh', 200000.00, 70, 'Kiểm tra tổn thương nhu mô phổi, bóng tim'),
(10, 8, 'DV_ECG', 'Đo điện tim đồ 12 chuyển đạo (ECG)', 'Thăm dò chức năng', 150000.00, 70, 'Khảo sát nhịp xoang, rối loạn dẫn truyền tim');

INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung) VALUES
(1, 'TH001', 'Paracetamol 500mg', 'Paracetamol', '500mg', 'Viên', 2000.00, 5000, 'Dược Hậu Giang', 'Việt Nam', 'Uống 1-2 viên khi sốt trên 38.5°C hoặc đau nhức'),
(2, 'TH002', 'Amoxicillin 500mg', 'Amoxicillin trihydrat', '500mg', 'Viên', 3000.00, 2000, 'Imexpharm', 'Việt Nam', 'Kháng sinh: Uống 1 viên sau ăn, ngày 2 lần'),
(3, 'TH003', 'Oresol 245', 'Glucose, Natri clorid, Kali clorid', '245 mOsm/L', 'Gói', 5000.00, 1000, 'Traphaco', 'Việt Nam', 'Pha đúng 1 gói với 200ml nước sôi để nguội'),
(4, 'TH004', 'Loratadin 10mg', 'Loratadin', '10mg', 'Viên', 4000.00, 1500, 'Pymepharco', 'Việt Nam', 'Thuốc kháng histamin: Uống 1 viên vào buổi tối'),
(5, 'TH005', 'Esomeprazole 40mg', 'Esomeprazole magnesium', '40mg', 'Viên', 12000.00, 3000, 'AstraZeneca', 'Thụy Điển', 'Giảm tiết acid dạ dày: Uống 1 viên trước bữa ăn sáng 30 phút'),
(6, 'TH006', 'Phosphalugel 20g', 'Aluminium phosphate', '20g', 'Gói', 5000.00, 2500, 'Boehringer Ingelheim', 'Pháp', 'Uống 1 gói khi có cơn đau thượng vị'),
(7, 'TH007', 'Men vi sinh Enterogermina', 'Bacillus clausii', '2 tỷ bào tử/5ml', 'Ống', 9000.00, 1200, 'Sanofi', 'Ý', 'Uống trực tiếp 1-2 ống/ngày sau bữa ăn'),
(8, 'TH008', 'Ibuprofen 400mg', 'Ibuprofen', '400mg', 'Viên', 3500.00, 2500, 'Stada', 'Việt Nam', 'Kháng viêm giảm đau cơ xương khớp, uống sau ăn no'),
(9, 'TH009', 'Siro ho thảo dược Prospan', 'Cao khô lá thường xuân', '100ml', 'Chai', 75000.00, 300, 'Engelhard', 'Đức', 'Uống 5ml/lần, ngày 3 lần sau ăn'),
(10, 'TH010', 'Nước muối sinh lý NaCl 0.9%', 'Natri Clorid 0.9%', '500ml', 'Chai', 10000.00, 800, 'Pharmedic', 'Việt Nam', 'Dùng súc miệng họng hoặc rửa vết thương');

-- TÀI KHOẢN DUY NHẤT: 1 ADMIN VÀ 1 BỆNH NHÂN
INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt) VALUES
(1, 1, 'admin', 'scrypt:32768:8:1$wte2IwGnBVO1lRWL$3da8cd29b71656229c22086ff7164745647f790916b2f3949a826972b6c8f4896f4fd90b2856affb5af79c1274b86fc0d20e1ee0da464623a7117faa4984e03c', 'admin@phongkham.com', '0999999999'),
(2, 6, '0901234567', 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79', 'baonam@gmail.com', '0901234567');

INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu) VALUES
(1, 1, 'NV001', 'Admin Hệ Thống', 1, '1988-01-01', '0999999999', 'admin@phongkham.com', '079088000001', '140 Lê Trọng Tấn, Tân Phú, TP.HCM', 'Quản trị viên');

INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, co_tai_khoan) VALUES
(1, 2, 'BN2609001', 'Hoàng Bảo Nam', '1990-05-12', 'Nam', '0901234567', 'baonam@gmail.com', '079090000001', 'GD4797931100001', 'Quận 1, TP.HCM', 'O+', 'Không có', 'Đau dạ dày nhẹ', 1);

INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi) VALUES
(1, 1, '75 lần/phút', '36.8 °C', '120/80 mmHg', '99 %', '18 lần/phút', '170 cm', '65 kg', '22.5 (Bình thường)');

INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai) VALUES
(1, 1, 'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', 'benh-cam-cum-mua-giao-mua', 'Cẩm Nang Y Tế', 'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', 'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', 'cam-cum.jpg', 320, '2026-09-20 08:00:00', 1),
(2, 1, 'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', 'cham-soc-rang-mieng-cho-tre', 'Nhi Khoa', 'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', 'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng phù hợp lứa tuổi...', 'rang-mieng-tre.jpg', 215, '2026-09-21 09:30:00', 1),
(3, 1, 'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', 'kham-suc-khoe-tong-quat-dinh-ky', 'Tin Tức Phòng Khám', 'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', 'Nội dung chi tiết về các gói khám tổng quát tại H2T Healthcare...', 'kham-tong-quat.jpg', 580, '2026-09-23 10:00:00', 1);
