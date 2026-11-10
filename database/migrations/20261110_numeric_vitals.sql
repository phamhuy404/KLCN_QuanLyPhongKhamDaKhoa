-- Add numeric vital-sign columns to existing databases without changing recorded readings.
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.chi_so_sinh_ton', N'U') IS NULL
        THROW 51000, 'Missing dbo.chi_so_sinh_ton table', 1;

    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'huyet_ap_tam_thu') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD huyet_ap_tam_thu SMALLINT NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'huyet_ap_tam_truong') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD huyet_ap_tam_truong SMALLINT NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'mach_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD mach_num SMALLINT NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'nhiet_do_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD nhiet_do_num DECIMAL(4,1) NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'spo2_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD spo2_num TINYINT NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'nhip_tho_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD nhip_tho_num SMALLINT NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'chieu_cao_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD chieu_cao_num DECIMAL(5,1) NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'can_nang_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD can_nang_num DECIMAL(5,1) NULL;
    IF COL_LENGTH(N'dbo.chi_so_sinh_ton', N'bmi_num') IS NULL
        ALTER TABLE dbo.chi_so_sinh_ton ADD bmi_num DECIMAL(4,1) NULL;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
