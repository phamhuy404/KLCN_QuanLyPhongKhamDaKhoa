-- REVIEW ONLY. This script only SELECTs proposed DDL; it performs no schema/data change.
-- Existing stored values cannot safely be inferred to be measured or fabricated.
-- Review the output separately before deciding whether to execute any proposed statement.
SELECT
    c.name AS column_name,
    dc.definition AS current_default,
    N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(dc.parent_object_id)) + N'.'
        + QUOTENAME(OBJECT_NAME(dc.parent_object_id))
        + N' DROP CONSTRAINT ' + QUOTENAME(dc.name) + N';' AS proposed_sql
FROM sys.default_constraints dc
JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
WHERE dc.parent_object_id = OBJECT_ID(N'dbo.chi_so_sinh_ton')
  AND c.name IN (N'mach', N'nhiet_do', N'huyet_ap', N'spo2', N'nhip_tho', N'chieu_cao', N'can_nang', N'bmi')
ORDER BY c.column_id;
