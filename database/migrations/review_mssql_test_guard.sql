-- REVIEW ONLY. No executable DDL/DML is present in this file.
-- DBA must independently confirm a separate DISPOSABLE MSSQL database ending _test.
-- Use a dedicated SQL login (not sa/sysadmin), default schema dbo, no access to
-- quan_ly_phong_kham. Never create this marker in the application database.
-- Review the proposed SQL below; replace UUID only after confirming the target.
/*
USE [clinic_integration_test];
IF DB_NAME() <> N'clinic_integration_test'
    THROW 51000, 'Wrong database for clinic integration tests', 1;
CREATE TABLE dbo.clinic_test_database_guard (
    marker_token uniqueidentifier NOT NULL,
    purpose nvarchar(100) NOT NULL
);
INSERT INTO dbo.clinic_test_database_guard(marker_token,purpose)
VALUES ('REPLACE_WITH_DBA_APPROVED_UUID',N'isolated-disposable-clinic-tests');
-- Login must be denied access to the application database and must not be sysadmin.
-- Grant only test DB permissions needed for approved fixture DDL/DML and sp_getapplock.
-- This marker table must not be writable by the application test login.
*/
