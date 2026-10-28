# Kê đơn, hóa đơn và tồn kho

## Quy tắc

- MSSQL/pyodbc; không thêm engine hoặc tự thay schema. Tất cả thao tác đơn thuốc, thu tiền, nhập kho và nhập CSV thuốc dùng transaction và khóa `clinic.calendar.v1` hiện có, chung với EMR. Khóa transaction trên SQL Server có hiệu lực giữa các tiến trình cùng database. Đây là khóa toàn cục, đổi lại an toàn nhưng có thể giảm thông lượng.
- Thuốc phải tồn tại, hoạt động; số lượng phải là số nguyên dương, không chấp nhận boolean/phân số/mặc định 1 khi thiếu. Kiểm tra tổng lượng theo thuốc để các dòng trùng không vượt tồn. EMR tiếp tục từ chối dòng trùng.
- Chọn nơi mua chỉ từ trạng thái chờ bệnh nhân/chờ duyệt/mua ngoài/bị từ chối. Duyệt chỉ khi chờ duyệt mua tại viện, có hóa đơn duy nhất và đủ tồn; duyệt chưa giữ chỗ tồn kho. Khi cấp phát phải kiểm tra lại.
- Chỉ cấp đơn đã duyệt, mua tại viện, có hóa đơn thuốc đã thanh toán và khớp chi tiết. UPDATE kho có điều kiện `trang_thai=1 AND so_luong_ton>=quantity`; ghi xuất kho, đổi trạng thái đơn/hóa đơn trong cùng transaction. Thiếu tồn, lỗi ghi audit hoặc commit đều phải trả thất bại và rollback.
- Đơn chưa duyệt và chưa có hóa đơn còn hiệu lực được sửa. Có hóa đơn chưa thanh toán: khóa sửa; có thể hủy đơn và hóa đơn cùng transaction, không thay số tiền. Đơn đã thanh toán hoặc cấp phát: khóa sửa, hủy, đổi nơi mua và tự hoàn kho, không tự hoàn tiền. `restore_stock` không còn cho phép hủy đơn đã cấp để cộng kho. Gọi lại không cộng/trừ kho lần nữa.
- Chưa triển khai quy trình nhận trả thuốc, đánh giá thuốc trả có tái nhập được hay không và hoàn tiền. Cần xác nhận nghiệp vụ/tài chính trước khi mở khóa; không dùng nhập tồn thường để lách quy trình trả thuốc.
- Schema hiện liên kết hóa đơn thuốc theo phiếu khám, chưa có FK trực tiếp đến đơn. Chỉ xử lý khi phiếu có đúng một đơn và tối đa một hóa đơn HDT còn hiệu lực. Dữ liệu cũ nhiều đơn/hóa đơn, đơn giá bằng 0 nhưng thành tiền khác 0 hoặc chi tiết không khớp bị từ chối để đối soát; không tự sửa dữ liệu/tiền cũ.
- Hóa đơn mới dùng đơn giá thật tại lúc lập và Decimal để tính tiền; cấp phát đối chiếu lượng và tính nhất quán nội bộ của hóa đơn, không định giá lại theo giá danh mục mới.

## Nhập kho và lịch sử

Trang `/admin/pharmacy` có nút nhập tồn/lịch sử cho thuốc hiện hữu. API chỉ ADMIN/DUOCSI:

```text
POST /api/pharmacy/receive-stock
{"medicine_id":1,"quantity":3,"reason":"Số chứng từ thực tế","receipt_id":"UUID duy nhất"}
GET /api/pharmacy/stock-history/1
```

UUID được lưu trong `audit_log.after_json`, gửi lại cùng thuốc/lượng không cộng kho lần nữa, đổi nội dung bị từ chối. Mã này chống gửi lại yêu cầu, không thay số chứng từ nghiệp vụ. Lịch sử 100 lần gần nhất lưu `STOCK_IN`/`STOCK_OUT`, tồn trước/sau, delta, người thao tác và lý do. Tồn đầu mới, nhập thuốc hiện hữu, CSV và cấp phát đều ghi lịch sử trong transaction. Không suy dựng lịch sử cũ, không thay đổi file/database hiện hữu. Cần bảng audit hiện tại và SQL Server 2016+ cho `JSON_VALUE`; không có tự tạo bảng khi import/chạy app. Nhập CSV mỗi lần là một phiếu nhập mới, gửi lại tệp sẽ cộng lại; dùng API có UUID cho yêu cầu cần retry an toàn.

## Chạy và kiểm tra

Website giữ `python -B app.py` với cấu hình MSSQL và SECRET_KEY hiện có. Không dùng lệnh này để thử trên database thật. Khởi tạo `create_test_app()` không bật worker/schema/SMTP; mặc định không mở database.

Unit/Flask render/JavaScript và hồi quy startup, không dùng DB:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_pharmacy_safety tests.test_startup_safety tests.test_mssql_test_database -v
```

Tích hợp chỉ sau khi DBA xác nhận database MSSQL test riêng theo [hướng dẫn](mssql_test_environment.md), các biến `CLINIC_MSSQL_TEST_*`, marker UUID, login không truy cập database chính. Suite tạo/xóa fixture trong database test: chỉ bật `CLINIC_MSSQL_TEST_ALLOW_FIXTURES=rebuild-only-disposable-fixtures` khi được phép tái tạo các bảng test. Không chạy trên database hiện tại hoặc chạy toàn bộ suite cũ.

```powershell
$env:PYTHONPATH='tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_mssql_smoke tests.test_pharmacy_mssql tests.test_emr_workflow tests.test_scheduling_safety tests.test_security_access tests.test_clinical_media -v
```

Các ca MSSQL chuẩn bị: chọn mua → duyệt → thanh toán giả lập trên test DB → cấp phát, cấp lặp/hoàn kho lặp bị chặn, cạnh tranh cấp phát cùng đơn, thiếu tồn, trigger audit gây lỗi để kiểm tra rollback, hóa đơn chặn sửa/hủy đồng bộ và nhập tồn chống retry. Thiếu cấu hình xác nhận: SKIP trước kết nối/DDL/DML. Chưa có bằng chứng chạy MSSQL thực tế, cạnh tranh SQL Server hoặc thao tác trình duyệt → API → MSSQL. Mock pass không thay thế các bước này.
