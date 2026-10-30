# Rà soát và cấu hình kiểm thử chỉ dùng MSSQL

## Kết quả xác minh mã nguồn/Git diff

Website chưa chuyển hệ quản trị: `config.DB_ENGINE='sqlserver'`, đường chạy bình thường của `core/database.py` vẫn kết nối Microsoft SQL Server bằng `pyodbc`. Không phát hiện SQLite/MySQL/PostgreSQL trong luồng runtime. Các cải tiến app factory không có tác dụng phụ, commit/rollback, xác thực/phân quyền, ảnh/dữ liệu y tế, lịch/đặt lịch và `lich_hen_id` được giữ lại.

Sai lệch có thật nằm trong bốn bộ test mới: `test_security_access`, `test_clinical_media`, `test_scheduling_safety`, `test_emr_workflow` đã dùng SQLite shared-memory. Adapter cũ dịch T-SQL và mô phỏng khóa SQL Server. Đã loại engine SQLite và các adapter đó, chuyển fixture sang T-SQL thực thi nguyên văn qua pyodbc trên MSSQL riêng. Không dùng database in-memory hay hệ quản trị thay thế. Không hoàn tác hàng loạt các thay đổi nghiệp vụ.

Kết quả test SQLite/RAM và trình duyệt ở các báo cáo trước là ghi chép lịch sử, KHÔNG phải bằng chứng MSSQL đã chạy thành công. Chúng không được dùng để nghiệm thu phiên bản MSSQL hiện tại.

## Cấu hình bắt buộc và cơ chế chặn nhầm DB

`core/mssql_test_database.py` không lấy thông tin kết nối dự phòng từ cấu hình vận hành. Các biến bắt buộc:

| Biến | Giá trị cần cung cấp |
|---|---|
| `CLINIC_MSSQL_TEST_DRIVER` | `ODBC Driver 17 for SQL Server` hoặc `ODBC Driver 18 for SQL Server`, không kèm dấu ngoặc |
| `CLINIC_MSSQL_TEST_SERVER` | Server/instance/port MSSQL test được xác nhận |
| `CLINIC_MSSQL_TEST_DATABASE` | Tên database riêng kết thúc `_test`, khác database chính |
| `CLINIC_MSSQL_TEST_USERNAME` | SQL login riêng, không dùng `sa`/sysadmin, default schema `dbo` |
| `CLINIC_MSSQL_TEST_PASSWORD` | Mật khẩu login test; không commit hoặc in log |
| `CLINIC_MSSQL_TEST_EXPECTED_SERVER` | Danh tính chính xác trả từ `SERVERPROPERTY('ServerName')`, do DBA xác nhận |
| `CLINIC_MSSQL_TEST_MARKER_TOKEN` | UUID marker độc lập do DBA cấp cho đúng DB test |
| `CLINIC_MSSQL_TEST_CONFIRMED` | `separate-disposable-mssql-test`, chỉ đặt sau khi xác nhận độc lập |
| `CLINIC_MSSQL_TEST_ALLOW_FIXTURES` | Chỉ khi cho phép dựng lại fixture: `rebuild-only-disposable-fixtures` |

Mẫu ở `tests/mssql_test.env.example` không tự được nạp; không có cấu hình bí mật hay kết nối thật đi kèm. Đặt biến trong terminal PowerShell bằng `$env:TEN_BIEN='giá trị đã được xác nhận'` hoặc cơ chế quản lý secret được phép.

Mỗi kết nối mới xác minh lại server thực tế, `DB_NAME()`, `ORIGINAL_LOGIN()`, không sysadmin, `HAS_DBACCESS(database chính)` không cấp quyền và đúng duy nhất marker tại `dbo.clinic_test_database_guard`. Sai danh tính/marker thì đóng kết nối ngay, không trả cho app/test ghi dữ liệu. Không thử server khác, không fallback localhost, không chuyển database tự động. Kết nối yêu cầu TLS có kiểm chứng chứng chỉ: `Encrypt=yes;TrustServerCertificate=no`; cần chứng chỉ/CA và tên host phù hợp.

DBA phải chuẩn bị một database test riêng có thể bỏ dữ liệu và login chỉ làm việc ở DB đó, không có quyền vào database chính. Marker do DBA quản lý, không cho test login sửa marker. Chỉ cấp quyền DDL/DML fixture trên DB test sau khi được duyệt, cùng quyền `sp_getapplock`. `database/migrations/review_mssql_test_guard.sql` chỉ chứa đề xuất trong comment để duyệt, không có DDL/DML thực thi. Không chạy file này hay migration/seed/restore nào trong đợt rà soát.

## Chạy độc lập, không cần database

Từ thư mục Website, dùng interpreter/dependency hiện có:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_startup_safety tests.test_mssql_test_database -v
```

Đây là unit/contract test dùng mock pyodbc. Kiểm tra import/app factory không gây DDL/DML/worker/SMTP, commit lỗi rollback, xác thực tại API, chặn cấu hình nguy hiểm, đóng kết nối khi xác minh sai, không ghi SQL trong bước xác minh và xử lý result set INSERT. Mock pass không chứng minh driver/server MSSQL hoạt động.

## Kiểm tra MSSQL chỉ đọc

Sau khi có cấu hình được DBA xác nhận, chưa cần cờ cho phép fixture:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_mssql_smoke -v
```

Chỉ SELECT danh tính/kết nối và tạo app test với factory MSSQL; không dựng schema, seed hoặc chạy worker. Kiểm tra kết nối trả raw `pyodbc.Connection`. Khi thiếu cấu hình, cả lớp báo SKIP, không kết nối database.

## Kiểm thử tích hợp nghiệp vụ

**Chỉ chạy khi DBA/user đã cho phép DDL/DML fixture trên database MSSQL riêng dùng để bỏ dữ liệu.** Các test sẽ DROP/CREATE các bảng fixture đã liệt kê trong `tests/mssql_support.py` và chèn dữ liệu test trên database đó. Không trỏ vào DB thật, bản sao cần giữ dữ liệu hoặc DB test dùng chung với việc khác. Có session application lock `clinic.integration.fixture` để không cho hai runner đồng thời dựng lại fixture; không xóa marker. Cờ fixture riêng là điều kiện bắt buộc ngoài cờ xác nhận database.

```powershell
$env:PYTHONPATH='tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest test_security_access test_clinical_media test_scheduling_safety test_emr_workflow -v
```

App test dùng `TESTING=True`, `DATABASE_CONNECTION_FACTORY` trả kết nối MSSQL đã xác minh, tắt SMTP/worker. Không còn thay `GETDATE`, `TOP`, `TRY_CAST`, `SCOPE_IDENTITY`, transaction hay `sp_getapplock` bằng cú pháp/hành vi giả. Fixture dùng `IDENTITY`, `NVARCHAR`, `DATE`, `TIME`, `DATETIME2`, `DECIMAL`, `SET IDENTITY_INSERT`, `THROW` theo T-SQL. Helper chỉ chuẩn hóa hàng kết quả để assertion có thể dùng tên cột/chỉ số; không dịch câu SQL. Các mock nghiệp vụ có sẵn trong bài kiểm tra quyền và mock gây lỗi commit/khóa vẫn là mock có chủ đích, không phải bằng chứng engine.

Không chạy `unittest discover`/pytest toàn repo: các test cũ ngoài phạm vi có thể kết nối DB vận hành. Không import/chạy script trong thư mục scratch hay seed/restore để thử cấu hình.

## Rà soát MSSQL/transaction và thay đổi thực tế

- `UnifiedCursor` trước đây lấy `@@IDENTITY` bằng batch khác và nuốt lỗi lấy ID. Đã chuyển sang `SCOPE_IDENTITY()` cùng batch INSERT, duyệt tới result set có alias riêng, bỏ qua result set của trigger; thiếu ID result set thì ném lỗi. Tránh gắn nhầm ID phiếu/lịch/đơn khi trigger có INSERT khác. Chưa chạy trigger MSSQL thực tế.
- Bổ sung tiền tố `N'...'` cho literal SQL tiếng Việt trong `ScheduleModel`, `AppointmentModel`, `UserModel`, `PatientModel`, `MedicalRecordModel`; giữ nguyên điều kiện nghiệp vụ và tham số. Tránh phụ thuộc code page khi so sánh trạng thái. Fixture trigger được commit trước khi gọi model từ kết nối khác để không giữ khóa schema chưa commit.
- Giữ `UnifiedConnection.commit()` ném lỗi, rollback và đóng khi cần. Giữ khóa `sys.sp_getapplock`, `BEGIN TRANSACTION`, `XACT_ABORT` và connection dùng chung trong nghiệp vụ lịch/EMR. Không thay bằng mutex Python/mock trong luồng tích hợp.
- Script review defaults sinh hiệu vẫn chỉ SELECT từ `sys.default_constraints`, dùng `QUOTENAME`, không thay schema. Cột/FK `phieu_kham.lich_hen_id` đã có trong schema dự án; không thêm migration/backfill.
- Các truy vấn kiểm tra quyền, công bố kết quả, lịch/đặt lịch và liên kết lần khám không bị hoàn tác. Runtime Website vẫn `python app.py` với cấu hình MSSQL hiện có; chưa chạy lệnh này vì nó dùng runtime vận hành.
- Các file chính thay trong nhiệm vụ: `core/mssql_test_database.py`, `core/database.py`, `tests/mssql_support.py`, bốn bộ test tích hợp, unit test startup/guard và smoke mới, mẫu cấu hình/script review và các tài liệu dẫn hướng. Giữ các diff có sẵn của người dùng từ trước nhiệm vụ.

## Trạng thái xác minh

Chưa có biến cấu hình MSSQL test được cung cấp trong môi trường khi rà soát. Không kết nối database thật/test, không chạy fixture DDL/DML, migration, seed hay restore. Unit/contract test chạy độc lập; các lớp tích hợp phải SKIP và không được tính là PASS nghiệp vụ MSSQL.

Kết quả chạy cuối: **27 unit/contract test đạt; 5 lớp smoke/tích hợp SKIP, 0 bài tích hợp thực thi**. Không còn unit test thất bại. Kiểm tra diff không lỗi whitespace; editor không báo lỗi trong các file Python đã kiểm tra. Đã kiểm tra `pyodbc.drivers()` không kết nối database: máy có cả ODBC Driver 17 và 18 for SQL Server; không cài/nâng cấp dependency.

Còn thiếu: server/instance, tên database MSSQL test riêng, lựa chọn driver trong cấu hình, login/mật khẩu riêng không truy cập database chính, danh tính server thực tế, marker DBA và CA/chứng chỉ TLS phù hợp. Muốn chạy test nghiệp vụ còn cần cho phép dựng lại fixture tại DB test. Các fixture đã được đổi nguồn sang T-SQL nhưng chưa được thực thi trên server, nên có thể cần điều chỉnh tiếp sau khi có môi trường. Chưa nghiệm thu cạnh tranh nhiều process, timeout/deadlock, commit mất kết nối hoặc UI → API → MSSQL. Kết quả SQLite cũ không lấp các khoảng trống này.
