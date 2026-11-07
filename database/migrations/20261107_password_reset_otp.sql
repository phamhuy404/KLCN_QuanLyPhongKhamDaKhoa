IF OBJECT_ID('dbo.password_reset_otp', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.password_reset_otp (
        account_id INT NOT NULL PRIMARY KEY,
        otp_hash CHAR(64) NOT NULL,
        expires_at DATETIME2 NOT NULL,
        sent_at DATETIME2 NOT NULL,
        attempts TINYINT NOT NULL DEFAULT 0,
        verified BIT NOT NULL DEFAULT 0,
        CONSTRAINT FK_password_reset_account FOREIGN KEY (account_id)
            REFERENCES dbo.tai_khoan(id) ON DELETE CASCADE
    );
END;
