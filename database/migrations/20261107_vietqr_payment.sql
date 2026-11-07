-- Run once against the existing clinic database. Keep historical paid timestamps.
SET XACT_ABORT ON;
BEGIN TRY
BEGIN TRANSACTION;
IF OBJECT_ID('dbo.payment_events', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.payment_events (
        id INT IDENTITY(1,1) PRIMARY KEY,
        provider NVARCHAR(20) NOT NULL,
        event_id NVARCHAR(100) NOT NULL,
        invoice_id INT NOT NULL REFERENCES dbo.hoa_don(id),
        amount DECIMAL(18,2) NOT NULL,
        transfer_content NVARCHAR(1000) NULL,
        received_at DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_payment_events_provider_event UNIQUE (provider, event_id)
    );
END;

DECLARE @constraint_name sysname;
SELECT @constraint_name = dc.name FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id=dc.parent_object_id AND c.column_id=dc.parent_column_id
WHERE dc.parent_object_id=OBJECT_ID('dbo.hoa_don') AND c.name='trang_thai';
IF @constraint_name IS NOT NULL EXEC(N'ALTER TABLE dbo.hoa_don DROP CONSTRAINT ' + QUOTENAME(@constraint_name));
ALTER TABLE dbo.hoa_don ADD CONSTRAINT DF_hoa_don_trang_thai_pending DEFAULT N'Chưa thanh toán' FOR trang_thai;

SET @constraint_name = NULL;
SELECT @constraint_name = dc.name FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id=dc.parent_object_id AND c.column_id=dc.parent_column_id
WHERE dc.parent_object_id=OBJECT_ID('dbo.hoa_don') AND c.name='thoi_gian_thanh_toan';
IF @constraint_name IS NOT NULL EXEC(N'ALTER TABLE dbo.hoa_don DROP CONSTRAINT ' + QUOTENAME(@constraint_name));
IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.hoa_don') AND name='idx_hoadon_ngay')
    DROP INDEX idx_hoadon_ngay ON dbo.hoa_don;
ALTER TABLE dbo.hoa_don ALTER COLUMN thoi_gian_thanh_toan DATETIME NULL;
CREATE INDEX idx_hoadon_ngay ON dbo.hoa_don(thoi_gian_thanh_toan);
UPDATE dbo.hoa_don SET thoi_gian_thanh_toan=NULL WHERE trang_thai=N'Chưa thanh toán';

SET @constraint_name = NULL;
SELECT @constraint_name = dc.name FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id=dc.parent_object_id AND c.column_id=dc.parent_column_id
WHERE dc.parent_object_id=OBJECT_ID('dbo.hoa_don') AND c.name='hinh_thuc_thanh_toan';
IF @constraint_name IS NOT NULL EXEC(N'ALTER TABLE dbo.hoa_don DROP CONSTRAINT ' + QUOTENAME(@constraint_name));
ALTER TABLE dbo.hoa_don ALTER COLUMN hinh_thuc_thanh_toan NVARCHAR(50) NULL;
UPDATE dbo.hoa_don SET hinh_thuc_thanh_toan=NULL WHERE trang_thai=N'Chưa thanh toán';
COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
