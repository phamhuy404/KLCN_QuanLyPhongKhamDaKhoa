-- Migration: Bổ sung bảng audit_log và các trường kiểm toán cho kết quả xét nghiệm, đơn thuốc
-- Tương thích: Microsoft SQL Server, SQLite, MySQL

-- 1. Bảng audit_log
-- SQL Server:
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_log')
BEGIN
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
END

-- 2. Bổ sung các cột kiểm toán kết quả cận lâm sàng (chi_tiet_chi_dinh)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'bac_si_duyet')
    ALTER TABLE chi_tiet_chi_dinh ADD bac_si_duyet NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'thoi_gian_duyet')
    ALTER TABLE chi_tiet_chi_dinh ADD thoi_gian_duyet DATETIME NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'ghi_chu_duyet')
    ALTER TABLE chi_tiet_chi_dinh ADD ghi_chu_duyet NVARCHAR(MAX) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'nguoi_nhap')
    ALTER TABLE chi_tiet_chi_dinh ADD nguoi_nhap NVARCHAR(100) NULL;

-- 3. Bổ sung các cột hủy/điều chỉnh đơn thuốc (don_thuoc)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'ly_do_huy')
    ALTER TABLE don_thuoc ADD ly_do_huy NVARCHAR(MAX) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'nguoi_huy')
    ALTER TABLE don_thuoc ADD nguoi_huy NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'thoi_gian_huy')
    ALTER TABLE don_thuoc ADD thoi_gian_huy DATETIME NULL;
