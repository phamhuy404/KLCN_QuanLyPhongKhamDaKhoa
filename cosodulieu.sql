
-- Tắt kiểm tra khóa ngoại để tạo bảng không bị lỗi thứ tự
SET FOREIGN_KEY_CHECKS = 0;

-- ==========================================
-- NHÓM 1: PHÂN QUYỀN VÀ NGƯỜI DÙNG
-- ==========================================

CREATE TABLE vai_tro (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ten_vai_tro VARCHAR(50) NOT NULL, -- Admin, LeTan, BacSi, BenhNhan
    mo_ta VARCHAR(255)
);

CREATE TABLE tai_khoan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vai_tro_id INT NOT NULL,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    trang_thai TINYINT(1) DEFAULT 1, -- 1: Hoạt động, 0: Bị khóa
    FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id)
);

CREATE TABLE benh_nhan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tai_khoan_id INT NULL,
    ma_benh_nhan VARCHAR(20) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    ngay_sinh DATE NOT NULL,
    gioi_tinh TINYINT(1) NOT NULL, -- 1: Nam, 0: Nữ
    sdt VARCHAR(15) NOT NULL UNIQUE,
    cccd VARCHAR(20) UNIQUE,
    bhyt VARCHAR(30),
    dia_chi VARCHAR(255),
    tien_su_benh TEXT,
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
);

CREATE TABLE nhan_vien (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tai_khoan_id INT NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,
    sdt VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    vi_tri_cong_viec VARCHAR(100),
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
);

CREATE TABLE bac_si (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nhan_vien_id INT NOT NULL UNIQUE,
    chuyen_khoa_id INT NOT NULL,
    hoc_vi VARCHAR(50),
    kinh_nghiem TEXT,
    hinh_anh VARCHAR(255),
    FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

-- ==========================================
-- NHÓM 2: DANH MỤC & CƠ SỞ VẬT CHẤT
-- ==========================================

CREATE TABLE chuyen_khoa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ten_khoa VARCHAR(100) NOT NULL,
    mo_ta TEXT
);

CREATE TABLE phong_kham (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chuyen_khoa_id INT NOT NULL,
    ten_phong VARCHAR(100) NOT NULL,
    trang_thai TINYINT(1) DEFAULT 1, -- 1: Đang hoạt động, 0: Đang sửa chữa
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

CREATE TABLE dich_vu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chuyen_khoa_id INT NULL,
    ten_dich_vu VARCHAR(255) NOT NULL,
    don_gia DECIMAL(10, 2) NOT NULL,
    mo_ta VARCHAR(255),
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
);

CREATE TABLE thuoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ten_thuoc VARCHAR(255) NOT NULL,
    hoat_chat VARCHAR(255),
    don_vi_tinh VARCHAR(50) NOT NULL,
    don_gia DECIMAL(10, 2) NOT NULL,
    so_luong_ton INT DEFAULT 0,
    huong_dan_su_dung VARCHAR(255)
);

-- ==========================================
-- NHÓM 3: LỊCH LÀM VIỆC & LỊCH HẸN
-- ==========================================

CREATE TABLE lich_lam_viec (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bac_si_id INT NOT NULL,
    phong_kham_id INT NOT NULL,
    ngay_lam DATE NOT NULL,
    ca_lam TINYINT NOT NULL, -- 1: Sáng, 2: Chiều, 3: Tối
    so_luong_kham_toi_da INT DEFAULT 20,
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
);

CREATE TABLE lich_hen (
    id INT AUTO_INCREMENT PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NULL,
    chuyen_khoa_id INT NOT NULL,
    phieu_kham_truoc_id INT NULL, -- Dành cho lịch hẹn tái khám
    ngay_hen DATE NOT NULL,
    gio_hen TIME NOT NULL,
    ly_do_kham TEXT,
    loai_lich_hen TINYINT(1) DEFAULT 1, -- 1: Khám mới, 2: Tái khám
    trang_thai VARCHAR(50) DEFAULT 'Chờ xác nhận', 
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
    FOREIGN KEY (phieu_kham_truoc_id) REFERENCES phieu_kham(id)
);

CREATE TABLE thong_bao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tai_khoan_id INT NOT NULL,
    tieu_de VARCHAR(255) NOT NULL,
    noi_dung TEXT NOT NULL,
    da_doc TINYINT(1) DEFAULT 0,
    thoi_gian_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
);

-- ==========================================
-- NHÓM 4: BỆNH ÁN ĐIỆN TỬ & CẬN LÂM SÀNG
-- ==========================================

CREATE TABLE phieu_kham (
    id INT AUTO_INCREMENT PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    bac_si_id INT NOT NULL,
    phong_kham_id INT NOT NULL,
    lich_hen_id INT NULL,
    thoi_gian_kham DATETIME DEFAULT CURRENT_TIMESTAMP,
    mach VARCHAR(20),
    nhiet_do VARCHAR(20),
    huyet_ap VARCHAR(20),
    chieu_cao FLOAT,
    can_nang FLOAT,
    trieu_chung TEXT,
    chan_doan_so_bo TEXT,
    chan_doan_cuoi_cung TEXT,
    huong_dieu_tri TEXT,
    ngay_tai_kham DATE NULL,
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
    FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id),
    FOREIGN KEY (lich_hen_id) REFERENCES lich_hen(id)
);

CREATE TABLE phieu_chi_dinh (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phieu_kham_id INT NOT NULL,
    thoi_gian_chi_dinh DATETIME DEFAULT CURRENT_TIMESTAMP,
    ghi_chu VARCHAR(255),
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE chi_tiet_chi_dinh (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phieu_chi_dinh_id INT NOT NULL,
    dich_vu_id INT NOT NULL,
    ket_qua TEXT,
    file_ket_qua VARCHAR(255),
    trang_thai VARCHAR(50) DEFAULT 'Chờ làm',
    FOREIGN KEY (phieu_chi_dinh_id) REFERENCES phieu_chi_dinh(id),
    FOREIGN KEY (dich_vu_id) REFERENCES dich_vu(id)
);

CREATE TABLE don_thuoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phieu_kham_id INT NOT NULL UNIQUE,
    thoi_gian_ke DATETIME DEFAULT CURRENT_TIMESTAMP,
    loi_dan_bac_si TEXT,
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE chi_tiet_don_thuoc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    don_thuoc_id INT NOT NULL,
    thuoc_id INT NOT NULL,
    so_luong INT NOT NULL,
    lieu_dung VARCHAR(50),
    cach_dung VARCHAR(100),
    FOREIGN KEY (don_thuoc_id) REFERENCES don_thuoc(id),
    FOREIGN KEY (thuoc_id) REFERENCES thuoc(id)
);

-- ==========================================
-- NHÓM 5: VIỆN PHÍ & CHĂM SÓC KHÁCH HÀNG
-- ==========================================

CREATE TABLE hoa_don (
    id INT AUTO_INCREMENT PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NOT NULL,
    tong_tien DECIMAL(10, 2) NOT NULL,
    giam_gia DECIMAL(10, 2) DEFAULT 0,
    thanh_tien DECIMAL(10, 2) NOT NULL,
    hinh_thuc_thanh_toan VARCHAR(50),
    trang_thai VARCHAR(50) DEFAULT 'Chưa thanh toán',
    thoi_gian_thanh_toan DATETIME,
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

CREATE TABLE chi_tiet_hoa_don (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hoa_don_id INT NOT NULL,
    loai_khoan_thu VARCHAR(50) NOT NULL, -- VD: 'Khám bệnh', 'Xét nghiệm', 'Thuốc'
    tham_chieu_id INT NOT NULL, -- ID của dịch vụ hoặc thuốc
    so_luong INT NOT NULL DEFAULT 1,
    don_gia DECIMAL(10, 2) NOT NULL,
    thanh_tien DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(id)

);

CREATE TABLE phan_hoi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    benh_nhan_id INT NOT NULL,
    phieu_kham_id INT NOT NULL UNIQUE,
    diem_danh_gia TINYINT NOT NULL CHECK (diem_danh_gia BETWEEN 1 AND 5),
    noi_dung TEXT,
    thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
    FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
);

-- Bật lại kiểm tra khóa ngoại sau khi đã tạo xong bảng
SET FOREIGN_KEY_CHECKS = 1;


SET FOREIGN_KEY_CHECKS = 0;

-- 1. Bảng vai_tro (4 dòng)
INSERT INTO vai_tro (id, ten_vai_tro, mo_ta) VALUES
(1, 'Admin', 'Quản trị viên hệ thống'),
(2, 'LeTan', 'Nhân viên tiếp đón, thu ngân'),
(3, 'BacSi', 'Bác sĩ khám bệnh'),
(4, 'BenhNhan', 'Khách hàng / Bệnh nhân');

-- 2. Bảng tai_khoan (15 dòng)
-- 1 Admin, 2 Lễ tân, 4 Bác sĩ, 8 Bệnh nhân (Mật khẩu mô phỏng chuỗi đã hash)
INSERT INTO tai_khoan (id, vai_tro_id, username, password, trang_thai) VALUES
(1, 1, 'admin', 'hashed_pwd_1', 1),
(2, 2, 'letan1', 'hashed_pwd_2', 1),
(3, 2, 'letan2', 'hashed_pwd_3', 1),
(4, 3, 'bs.tuan', 'hashed_pwd_4', 1),
(5, 3, 'bs.lan', 'hashed_pwd_5', 1),
(6, 3, 'bs.minh', 'hashed_pwd_6', 1),
(7, 3, 'bs.huong', 'hashed_pwd_7', 1),
(8, 4, '0901234567', 'hashed_pwd_8', 1),
(9, 4, '0912345678', 'hashed_pwd_9', 1),
(10, 4, '0923456789', 'hashed_pwd_10', 1),
(11, 4, '0934567890', 'hashed_pwd_11', 1),
(12, 4, '0945678901', 'hashed_pwd_12', 1),
(13, 4, '0956789012', 'hashed_pwd_13', 1),
(14, 4, '0967890123', 'hashed_pwd_14', 1),
(15, 4, '0978901234', 'hashed_pwd_15', 1);

-- 3. Bảng nhan_vien (7 dòng)
INSERT INTO nhan_vien (id, tai_khoan_id, ho_ten, sdt, email, vi_tri_cong_viec) VALUES
(1, 1, 'Quản Trị Hệ Thống', '0999999999', 'admin@phongkham.com', 'Admin'),
(2, 2, 'Trần Thị Mai', '0988888888', 'mai.tt@phongkham.com', 'Lễ tân'),
(3, 3, 'Lê Văn Khang', '0977777777', 'khang.lv@phongkham.com', 'Lễ tân'),
(4, 4, 'Nguyễn Anh Tuấn', '0966666666', 'tuan.na@phongkham.com', 'Bác sĩ'),
(5, 5, 'Phạm Phương Lan', '0955555555', 'lan.pp@phongkham.com', 'Bác sĩ'),
(6, 6, 'Vũ Quang Minh', '0944444444', 'minh.vq@phongkham.com', 'Bác sĩ'),
(7, 7, 'Bùi Thu Hương', '0933333333', 'huong.bt@phongkham.com', 'Bác sĩ');

-- 4. Bảng chuyen_khoa (5 dòng)
INSERT INTO chuyen_khoa (id, ten_khoa, mo_ta) VALUES
(1, 'Khoa Nội', 'Khám và điều trị các bệnh lý nội khoa'),
(2, 'Khoa Ngoại', 'Khám và tiểu phẫu ngoại khoa'),
(3, 'Khoa Nhi', 'Khám và điều trị bệnh cho trẻ em'),
(4, 'Khoa Răng Hàm Mặt', 'Chăm sóc sức khỏe răng miệng'),
(5, 'Khoa Sản - Phụ khoa', 'Khám thai và bệnh lý phụ khoa');

-- 5. Bảng bac_si (4 dòng - Liên kết 1-1 với nhân viên từ 4->7)
INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, hoc_vi, kinh_nghiem, hinh_anh) VALUES
(1, 4, 1, 'Thạc sĩ', '10 năm kinh nghiệm tại BV Chợ Rẫy', 'tuan.jpg'),
(2, 5, 3, 'BS CKI', '7 năm kinh nghiệm tại BV Nhi Đồng 1', 'lan.jpg'),
(3, 6, 2, 'Tiến sĩ', '15 năm kinh nghiệm chấn thương chỉnh hình', 'minh.jpg'),
(4, 7, 4, 'BS CKI', '5 năm kinh nghiệm nha khoa thẩm mỹ', 'huong.jpg');

-- 6. Bảng benh_nhan (10 dòng - 8 dòng có tài khoản, 2 dòng bệnh nhân vãng lai)
INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, dia_chi, tien_su_benh) VALUES
(1, 8, 'BN2609001', 'Hoàng Bảo Nam', '1990-05-12', 1, '0901234567', 'Quận 1, TP.HCM', 'Không có'),
(2, 9, 'BN2609002', 'Lê Ngọc Trâm', '1995-08-22', 0, '0912345678', 'Quận 3, TP.HCM', 'Dị ứng hải sản'),
(3, 10, 'BN2609003', 'Trần Văn Quyết', '1985-11-30', 1, '0923456789', 'Quận Tân Bình, TP.HCM', 'Huyết áp cao'),
(4, 11, 'BN2609004', 'Phạm Thảo My', '2015-02-14', 0, '0934567890', 'Quận Gò Vấp, TP.HCM', 'Suyễn'),
(5, 12, 'BN2609005', 'Đinh Trọng Thắng', '1978-04-10', 1, '0945678901', 'Quận 10, TP.HCM', 'Tiểu đường type 2'),
(6, 13, 'BN2609006', 'Võ Thanh Trúc', '1998-09-09', 0, '0956789012', 'Quận Bình Thạnh, TP.HCM', 'Đau dạ dày'),
(7, 14, 'BN2609007', 'Ngô Kiến Hào', '2010-12-25', 1, '0967890123', 'Quận 7, TP.HCM', 'Không có'),
(8, 15, 'BN2609008', 'Lý Nhã Kỳ', '1982-07-19', 0, '0978901234', 'Quận 2, TP.HCM', 'Không có'),
(9, NULL, 'BN2609009', 'Châu Gia Kiệt', '1992-01-01', 1, '0981234567', 'Thủ Đức, TP.HCM', 'Viêm xoang'),
(10, NULL, 'BN2609010', 'Bảo Thy', '1999-03-03', 0, '0991234567', 'Quận 5, TP.HCM', 'Không có');

-- 7. Bảng phong_kham (6 dòng)
INSERT INTO phong_kham (id, chuyen_khoa_id, ten_phong, trang_thai) VALUES
(1, 1, 'Phòng Khám Nội 1', 1),
(2, 1, 'Phòng Khám Nội 2', 1),
(3, 2, 'Phòng Khám Ngoại 1', 1),
(4, 3, 'Phòng Khám Nhi 1', 1),
(5, 4, 'Phòng Răng Hàm Mặt', 1),
(6, 1, 'Phòng Siêu Âm', 1);

-- 8. Bảng dich_vu (10 dòng)
INSERT INTO dich_vu (id, chuyen_khoa_id, ten_dich_vu, don_gia, mo_ta) VALUES
(1, 1, 'Khám Nội Tổng Quát', 150000, 'Khám và tư vấn bệnh lý nội khoa'),
(2, 3, 'Khám Nhi', 120000, 'Khám và tư vấn bệnh lý trẻ em'),
(3, 2, 'Khám Ngoại', 150000, 'Khám và tư vấn ngoại khoa'),
(4, 4, 'Nhổ răng khôn', 1000000, 'Tiểu phẫu nhổ răng khôn mọc lệch'),
(5, 4, 'Cạo vôi răng', 200000, 'Làm sạch mảng bám răng'),
(6, NULL, 'Siêu âm ổ bụng', 250000, 'Siêu âm 2D/3D màu ổ bụng'),
(7, NULL, 'Xét nghiệm Máu cơ bản', 350000, 'Kiểm tra 10 thông số huyết học'),
(8, NULL, 'Xét nghiệm Nước tiểu', 100000, 'Tổng phân tích nước tiểu'),
(9, NULL, 'X-Quang Phổi thẳng', 200000, 'Chụp X-quang kỹ thuật số'),
(10, NULL, 'Điện tâm đồ (ECG)', 150000, 'Đo điện tim đồ 12 chuyển đạo');

-- 9. Bảng thuoc (10 dòng)
INSERT INTO thuoc (id, ten_thuoc, hoat_chat, don_vi_tinh, don_gia, so_luong_ton, huong_dan_su_dung) VALUES
(1, 'Paracetamol 500mg', 'Paracetamol', 'Viên', 2000, 5000, 'Uống khi sốt hoặc đau'),
(2, 'Amoxicillin 500mg', 'Amoxicillin', 'Viên', 3000, 2000, 'Kháng sinh uống sau ăn'),
(3, 'Oresol', 'Glucose, Natri', 'Gói', 5000, 1000, 'Pha với 200ml nước đun sôi để nguội'),
(4, 'Loratadin 10mg', 'Loratadin', 'Viên', 4000, 1500, 'Chống dị ứng, uống buổi tối'),
(5, 'Omeprazol 20mg', 'Omeprazol', 'Viên', 5000, 3000, 'Trị viêm loét dạ dày, uống trước ăn 30p'),
(6, 'Vitamin C 500mg', 'Ascorbic acid', 'Viên', 1500, 4000, 'Uống ban ngày'),
(7, 'Men tiêu hóa Enterogermina', 'Bào tử lợi khuẩn', 'Ống', 8000, 1000, 'Uống trực tiếp hoặc pha với nước'),
(8, 'Ibuprofen 400mg', 'Ibuprofen', 'Viên', 3500, 2500, 'Kháng viêm giảm đau, uống sau ăn no'),
(9, 'Siro ho Prospan', 'Dịch chiết lá Thường Xuân', 'Chai', 75000, 200, 'Uống 5ml/lần'),
(10, 'Nước muối sinh lý NaCl 0.9%', 'Natri Clorid 0.9%', 'Chai', 10000, 500, 'Súc miệng hoặc rửa mũi');

-- 10. Bảng lich_lam_viec (10 dòng)
INSERT INTO lich_lam_viec (id, bac_si_id, phong_kham_id, ngay_lam, ca_lam) VALUES
(1, 1, 1, '2026-09-22', 1),
(2, 1, 1, '2026-09-22', 2),
(3, 2, 4, '2026-09-22', 1),
(4, 2, 4, '2026-09-23', 1),
(5, 3, 3, '2026-09-22', 2),
(6, 4, 5, '2026-09-23', 1),
(7, 4, 5, '2026-09-23', 2),
(8, 1, 1, '2026-09-24', 1),
(9, 2, 4, '2026-09-24', 2),
(10, 3, 3, '2026-09-25', 1);

-- 11. Bảng lich_hen (12 dòng)
INSERT INTO lich_hen (id, benh_nhan_id, bac_si_id, chuyen_khoa_id, ngay_hen, gio_hen, loai_lich_hen, trang_thai) VALUES
(1, 1, 1, 1, '2026-09-22', '08:30', 1, 'Đã khám'),
(2, 2, 1, 1, '2026-09-22', '09:00', 1, 'Đã khám'),
(3, 3, 1, 1, '2026-09-22', '10:00', 1, 'Đã khám'),
(4, 4, 2, 3, '2026-09-22', '08:00', 1, 'Đã khám'),
(5, 5, 3, 2, '2026-09-22', '14:00', 1, 'Đã khám'),
(6, 6, 1, 1, '2026-09-22', '14:30', 1, 'Đã hủy'),
(7, 7, 2, 3, '2026-09-23', '08:30', 2, 'Đã duyệt'),
(8, 8, 4, 4, '2026-09-23', '09:30', 1, 'Đã duyệt'),
(9, 9, 1, 1, '2026-09-24', '10:00', 1, 'Chờ xác nhận'),
(10, 10, 2, 3, '2026-09-24', '15:00', 2, 'Chờ xác nhận'),
(11, 1, 1, 1, '2026-09-29', '08:30', 2, 'Đã duyệt'),
(12, 5, 3, 2, '2026-09-29', '14:00', 2, 'Đã duyệt');

-- 12. Bảng phieu_kham (10 dòng)
INSERT INTO phieu_kham (id, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, mach, nhiet_do, huyet_ap, trieu_chung, chan_doan_so_bo, chan_doan_cuoi_cung, huong_dieu_tri, ngay_tai_kham) VALUES
(1, 1, 1, 1, 1, '80', '37', '120/80', 'Đau đầu, mệt mỏi', 'Viêm họng cấp', 'Viêm họng cấp', 'Uống thuốc, nghỉ ngơi', '2026-09-29'),
(2, 2, 1, 1, 2, '85', '38.5', '110/70', 'Đau bụng quanh rốn', 'Rối loạn tiêu hóa', 'Viêm dạ dày cấp', 'Truyền dịch, dùng thuốc', NULL),
(3, 3, 1, 1, 3, '90', '37', '150/90', 'Chóng mặt', 'Cao huyết áp', 'Tăng huyết áp vô căn', 'Điều chỉnh thuốc hạ áp', '2026-10-22'),
(4, 4, 2, 4, 4, '100', '39', '90/60', 'Ho đờm, khò khè', 'Viêm phế quản', 'Viêm phế quản cấp', 'Uống siro, kháng sinh nhẹ', '2026-09-25'),
(5, 5, 3, 3, 5, '75', '36.8', '130/80', 'Đau gót chân phải', 'Bong gân', 'Chấn thương phần mềm', 'Băng thun, thuốc giảm đau', '2026-09-29'),
(6, 6, 1, 1, NULL, '82', '37.5', '115/75', 'Ho khan kéo dài', 'Viêm xoang', 'Viêm đường hô hấp trên', 'Uống thuốc', NULL),
(7, 7, 2, 4, NULL, '95', '38', '100/65', 'Tiêu chảy', 'Nhiễm trùng đường ruột', 'Tiêu chảy cấp', 'Uống Oresol, men tiêu hóa', NULL),
(8, 8, 4, 5, NULL, '80', '37', '120/80', 'Đau răng khôn hàm dưới', 'Răng khôn mọc lệch', 'Viêm quanh thân răng 48', 'Nhổ răng', NULL),
(9, 9, 1, 1, NULL, '88', '37.2', '110/80', 'Mất ngủ, căng thẳng', 'Suy nhược thần kinh', 'Suy nhược cơ thể', 'Bổ sung vitamin, an thần', NULL),
(10, 10, 3, 3, NULL, '78', '37', '110/70', 'Sưng khớp gối', 'Tràn dịch khớp', 'Viêm khớp gối', 'Hút dịch, uống thuốc', '2026-09-27');

-- 13. Bảng phieu_chi_dinh (8 dòng)
INSERT INTO phieu_chi_dinh (id, phieu_kham_id, ghi_chu) VALUES
(1, 1, 'XN máu thường quy'),
(2, 2, 'Siêu âm ổ bụng kiểm tra tiêu hóa'),
(3, 3, 'Làm điện tâm đồ'),
(4, 4, 'Chụp X-Quang phổi'),
(5, 5, 'Chụp X-Quang gót chân phải'),
(6, 7, 'XN phân, XN Máu'),
(7, 8, 'Chụp X-Quang răng toàn cảnh'),
(8, 10, 'Siêu âm khớp gối');

-- 14. Bảng chi_tiet_chi_dinh (15 dòng)
INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai) VALUES
(1, 1, 7, 'Bạch cầu hơi tăng, tiểu cầu bình thường', 'Đã có kết quả'),
(2, 2, 6, 'Dạ dày có vết loét nhỏ, các tạng khác bình thường', 'Đã có kết quả'),
(3, 2, 7, 'Glucose máu bình thường', 'Đã có kết quả'),
(4, 3, 10, 'Nhịp xoang đều, không có dấu hiệu thiếu máu cơ tim', 'Đã có kết quả'),
(5, 4, 9, 'Tổn thương thâm nhiễm hai phế trường', 'Đã có kết quả'),
(6, 5, 9, 'Không thấy tổn thương gãy xương', 'Đã có kết quả'),
(7, 6, 7, 'Bạch cầu tăng cao, CRP tăng', 'Đã có kết quả'),
(8, 6, 8, 'Nước tiểu bình thường', 'Đã có kết quả'),
(9, 7, 9, 'Răng 48 mọc ngầm lệch 90 độ', 'Đã có kết quả'),
(10, 8, 6, 'Có ít dịch khớp gối phải', 'Đã có kết quả'),
(11, 1, 8, 'Không phát hiện bất thường', 'Đã có kết quả'),
(12, 3, 7, 'Cholesterol hơi cao', 'Đã có kết quả'),
(13, 5, 6, 'Giãn dây chằng cổ chân', 'Đã có kết quả'),
(14, 7, 7, 'Máu khó đông: Âm tính', 'Đã có kết quả'),
(15, 8, 9, 'Gai mâm chày gối phải', 'Đã có kết quả');

-- 15. Bảng don_thuoc (10 dòng)
INSERT INTO don_thuoc (id, phieu_kham_id, loi_dan_bac_si) VALUES
(1, 1, 'Uống nhiều nước, súc miệng nước muối'),
(2, 2, 'Ăn chín uống sôi, kiêng đồ chua cay'),
(3, 3, 'Kiêng ăn mặn, tập thể dục nhẹ nhàng'),
(4, 4, 'Giữ ấm cổ, uống thuốc đúng giờ'),
(5, 5, 'Chườm đá lạnh, hạn chế đi lại'),
(6, 6, 'Uống nhiều nước ấm'),
(7, 7, 'Bù nước liên tục'),
(8, 8, 'Ngậm bông gòn 30p, ăn cháo nguội'),
(9, 9, 'Tránh thức khuya, tập yoga'),
(10, 10, 'Nghỉ ngơi, kê cao chân khi ngủ');

-- 16. Bảng chi_tiet_don_thuoc (20 dòng)
INSERT INTO chi_tiet_don_thuoc (id, don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung) VALUES
(1, 1, 1, 10, 'Sáng 1, Chiều 1', 'Uống sau ăn'),
(2, 1, 2, 14, 'Sáng 1, Chiều 1', 'Uống sau ăn'),
(3, 1, 10, 2, 'Sáng, Trưa, Chiều', 'Súc họng 3 lần/ngày'),
(4, 2, 5, 14, 'Sáng 1, Tối 1', 'Uống trước ăn 30 phút'),
(5, 2, 7, 10, 'Sáng 1, Chiều 1', 'Uống sau ăn 2 tiếng'),
(6, 3, 6, 30, 'Sáng 1', 'Uống hằng ngày'),
(7, 4, 9, 1, 'Sáng, Trưa, Tối', 'Uống mỗi lần 5ml'),
(8, 4, 2, 10, 'Sáng 1, Chiều 1', 'Pha với nước uống'),
(9, 5, 8, 10, 'Sáng 1, Chiều 1', 'Uống sau ăn no'),
(10, 5, 1, 10, 'Sáng 1, Tối 1', 'Uống khi đau'),
(11, 6, 2, 15, 'Sáng 1, Chiều 1', 'Uống sau ăn'),
(12, 6, 6, 10, 'Sáng 1', 'Uống sủi bọt vào buổi sáng'),
(13, 7, 3, 10, 'Theo nhu cầu', 'Pha 1 gói với 200ml nước'),
(14, 7, 7, 10, 'Sáng 1, Tối 1', 'Uống sau ăn'),
(15, 8, 1, 6, 'Sáng 1, Chiều 1', 'Uống giảm đau'),
(16, 8, 2, 10, 'Sáng 1, Chiều 1', 'Chống nhiễm trùng'),
(17, 9, 6, 15, 'Sáng 1', 'Uống sau ăn'),
(18, 10, 8, 14, 'Sáng 1, Chiều 1', 'Uống sau ăn no'),
(19, 10, 5, 14, 'Sáng 1', 'Bảo vệ dạ dày'),
(20, 10, 1, 10, 'Sáng 1, Tối 1', 'Uống khi thấy đau nhức');

-- 17. Bảng hoa_don (10 dòng)
INSERT INTO hoa_don (id, benh_nhan_id, phieu_kham_id, tong_tien, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai) VALUES
(1, 1, 1, 582000, 0, 582000, 'Momo', 'Đã thanh toán'),
(2, 2, 2, 820000, 0, 820000, 'Chuyển khoản', 'Đã thanh toán'),
(3, 3, 3, 345000, 0, 345000, 'Tiền mặt', 'Đã thanh toán'),
(4, 4, 4, 425000, 0, 425000, 'Chuyển khoản', 'Đã thanh toán'),
(5, 5, 5, 405000, 50000, 355000, 'Tiền mặt', 'Đã thanh toán'),
(6, 6, 6, 210000, 0, 210000, 'Tiền mặt', 'Đã thanh toán'),
(7, 7, 7, 600000, 0, 600000, 'Chuyển khoản', 'Đã thanh toán'),
(8, 8, 8, 1242000, 100000, 1142000, 'Thẻ tín dụng', 'Đã thanh toán'),
(9, 9, 9, 172500, 0, 172500, 'Tiền mặt', 'Đã thanh toán'),
(10, 10, 10, 519000, 0, 519000, 'Momo', 'Đã thanh toán');

-- 18. Bảng chi_tiet_hoa_don (25 dòng - Liên kết với ID dịch vụ hoặc ID thuốc)
-- VD Hóa đơn 1 (Tổng 582k): Khám(150) + Xét nghiệm Máu(350) + Nước tiểu(100) + Thuốc(62k) = 662k (Đã fix số cho khớp logic)
INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien) VALUES
(1, 1, 'Khám bệnh', 1, 1, 150000, 150000), -- Khám nội (ID 1)
(2, 1, 'Dịch vụ CLS', 7, 1, 350000, 350000), -- Xét nghiệm máu (ID 7)
(3, 1, 'Thuốc', 1, 10, 2000, 20000), -- Para
(4, 1, 'Thuốc', 2, 14, 3000, 42000), -- Amox
(5, 1, 'Thuốc', 10, 2, 10000, 20000), -- Nước muối
(6, 2, 'Khám bệnh', 1, 1, 150000, 150000),
(7, 2, 'Dịch vụ CLS', 6, 1, 250000, 250000), -- Siêu âm
(8, 2, 'Dịch vụ CLS', 7, 1, 350000, 350000), -- XN Máu
(9, 2, 'Thuốc', 5, 14, 5000, 70000), -- Omeprazol
(10, 3, 'Khám bệnh', 1, 1, 150000, 150000),
(11, 3, 'Dịch vụ CLS', 10, 1, 150000, 150000), -- Điện tâm đồ
(12, 3, 'Thuốc', 6, 30, 1500, 45000), -- Vit C
(13, 4, 'Khám bệnh', 2, 1, 120000, 120000), -- Khám Nhi
(14, 4, 'Dịch vụ CLS', 9, 1, 200000, 200000), -- XQ Phổi
(15, 4, 'Thuốc', 9, 1, 75000, 75000), -- Siro
(16, 4, 'Thuốc', 2, 10, 3000, 30000), -- Amox
(17, 5, 'Khám bệnh', 3, 1, 150000, 150000), -- Khám Ngoại
(18, 5, 'Dịch vụ CLS', 9, 1, 200000, 200000), -- XQ 
(19, 5, 'Thuốc', 8, 10, 3500, 35000), -- Ibuprofen
(20, 5, 'Thuốc', 1, 10, 2000, 20000), -- Para
(21, 6, 'Khám bệnh', 1, 1, 150000, 150000),
(22, 6, 'Thuốc', 2, 15, 3000, 45000),
(23, 6, 'Thuốc', 6, 10, 1500, 15000),
(24, 7, 'Khám bệnh', 2, 1, 120000, 120000),
(25, 7, 'Dịch vụ CLS', 7, 1, 350000, 350000);

-- 19. Bảng phan_hoi (8 dòng)
INSERT INTO phan_hoi (id, benh_nhan_id, phieu_kham_id, diem_danh_gia, noi_dung) VALUES
(1, 1, 1, 5, 'Bác sĩ Tuấn khám rất nhiệt tình và kỹ lưỡng.'),
(2, 2, 2, 4, 'Dịch vụ tốt, siêu âm rõ nét nhưng chờ hơi lâu ở quầy thuốc.'),
(3, 3, 3, 5, 'Phòng khám sạch sẽ, nhân viên lễ tân thân thiện.'),
(4, 4, 4, 5, 'Bác sĩ Lan khám nhi rất mát tay, bé nhà mình hết khóc ngay.'),
(5, 5, 5, 4, 'Chụp X-Quang nhanh, tư vấn điều trị tốt.'),
(6, 6, 6, 3, 'Giá khám hơi cao so với mặt bằng chung.'),
(7, 7, 7, 5, 'Tuyệt vời, có kết quả xét nghiệm gửi ngay qua App rất tiện.'),
(8, 8, 8, 5, 'Bác sĩ nhổ răng không đau, cảm ơn phòng khám!');

-- 20. Bảng thong_bao (10 dòng)
INSERT INTO thong_bao (id, tai_khoan_id, tieu_de, noi_dung, da_doc) VALUES
(1, 8, 'Đặt lịch thành công', 'Bạn đã đặt lịch khám thành công ngày 22/09 lúc 08:30.', 1),
(2, 9, 'Đặt lịch thành công', 'Bạn đã đặt lịch khám thành công ngày 22/09 lúc 09:00.', 1),
(3, 8, 'Nhắc lịch tái khám', 'Bạn có lịch tái khám với bác sĩ Nguyễn Anh Tuấn vào ngày 29/09.', 0),
(4, 10, 'Kết quả xét nghiệm', 'Kết quả xét nghiệm máu của bạn đã có, vui lòng kiểm tra mục Hồ sơ.', 1),
(5, 11, 'Thông báo từ BS', 'Bác sĩ Lan đã kê đơn thuốc mới cho bạn.', 1),
(6, 12, 'Đặt lịch thành công', 'Bạn đã đặt lịch khám thành công ngày 22/09 lúc 14:00.', 1),
(7, 12, 'Nhắc lịch tái khám', 'Bạn có lịch tái khám vào ngày 29/09 lúc 14:00.', 0),
(8, 14, 'Đặt lịch thành công', 'Lịch khám của bạn ngày 23/09 lúc 08:30 đã được duyệt.', 0),
(9, 15, 'Hủy lịch khám', 'Lịch khám của bạn vào ngày 22/09 lúc 14:30 đã bị hủy theo yêu cầu.', 1),
(10, 8, 'Khuyến mãi tháng 9', 'Phòng khám giảm 10% phí xét nghiệm cho khách hàng đặt lịch qua App.', 1);

SET FOREIGN_KEY_CHECKS = 1;