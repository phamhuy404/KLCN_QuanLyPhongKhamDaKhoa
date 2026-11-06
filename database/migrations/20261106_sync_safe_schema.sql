-- Migration đồng bộ an toàn: Bổ sung các bảng và cột mới mà KHÔNG xóa dữ liệu cũ
-- Thích hợp chạy khi kéo mã nguồn git pull mà muốn giữ nguyên dữ liệu đã tạo

USE quan_ly_phong_kham;

-- 1. Bảng cài đặt hệ thống và chế độ bảo trì (cai_dat_he_thong)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'cai_dat_he_thong')
BEGIN
    CREATE TABLE cai_dat_he_thong (
        khoa NVARCHAR(100) PRIMARY KEY,
        gia_tri NVARCHAR(MAX),
        mo_ta NVARCHAR(255),
        cap_nhat_luc DATETIME DEFAULT GETDATE(),
        nguoi_cap_nhat NVARCHAR(100) DEFAULT 'system'
    );
END

-- Nạp cấu hình mặc định nếu chưa có
IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'insurance_fixed_reduction')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'insurance_fixed_reduction', N'50000', N'Mức giảm trừ BHYT cố định', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_patient')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_patient', N'0', N'Bảo trì Cổng Bệnh nhân', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_staff')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_staff', N'0', N'Bảo trì Cổng Nhân viên', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_message_patient')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_message_patient', N'Cổng Dịch vụ Bệnh nhân H2T Care+ đang được nâng cấp tính năng và bảo trì định kỳ. Quý khách vui lòng quay lại sau.', N'Thông báo bảo trì bệnh nhân', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_message_staff')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_message_staff', N'Phân hệ Quản lý Y tế Nội bộ đang tạm dừng để bảo trì nâng cấp máy chủ và đồng bộ cơ sở dữ liệu. Vui lòng quay lại sau.', N'Thông báo bảo trì nhân viên', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_eta')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_eta', N'23:00 Hôm nay', N'Thời gian dự kiến hoàn tất bảo trì', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_hotline')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_hotline', N'1900 1234 - (028) 3810 0000', N'Hotline hỗ trợ', GETDATE(), N'system');

IF NOT EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = 'maintenance_pages')
    INSERT INTO cai_dat_he_thong (khoa, gia_tri, mo_ta, cap_nhat_luc, nguoi_cap_nhat)
    VALUES (N'maintenance_pages', N'{"patient_booking": false, "patient_records": false, "patient_lab": false, "patient_billing": false, "patient_feedbacks": false, "patient_profile": false, "admin_emr": false, "admin_reception": false, "admin_appointments": false, "admin_lab": false, "admin_pharmacy": false, "admin_billing": false, "admin_reports": false, "admin_staff": false}', N'Cài đặt bảo trì từng trang nhỏ', GETDATE(), N'system');

-- 2. Bổ sung các cột kiểm toán và quản lý trạng thái
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('hoa_don') AND name = 'trang_thai_nhan_thuoc')
    ALTER TABLE hoa_don ADD trang_thai_nhan_thuoc NVARCHAR(50) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('hoa_don') AND name = 'giam_gia')
    ALTER TABLE hoa_don ADD giam_gia DECIMAL(18,2) DEFAULT 0;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phieu_kham') AND name = 'ngay_tai_kham')
    ALTER TABLE phieu_kham ADD ngay_tai_kham DATE NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_hen') AND name = 'phong_kham_id')
    ALTER TABLE lich_hen ADD phong_kham_id INT NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'hinh_thuc_mua')
    ALTER TABLE don_thuoc ADD hinh_thuc_mua NVARCHAR(50) DEFAULT N'Chưa chọn';

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'nguoi_duyet')
    ALTER TABLE don_thuoc ADD nguoi_duyet NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'ngay_duyet')
    ALTER TABLE don_thuoc ADD ngay_duyet DATETIME NULL;
