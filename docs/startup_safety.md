# Khởi tạo ứng dụng và kiểm thử an toàn

## Chạy Website hiện tại

Từ thư mục gốc Website, dùng môi trường Python đã có các dependency trong
[requirements.txt](../requirements.txt):

```powershell
python -B app.py
```

Website vẫn phục vụ tại http://127.0.0.1:5000, bật debug/reloader như trước.
Lệnh này gọi `start_runtime_services(app)` rõ ràng; scheduler nhắc lịch chỉ
khởi động trong tiến trình con của reloader. Scheduler thật có thể ghi thông
báo và gửi email theo cấu hình hiện hành. Không dùng lệnh này để chạy test.

Import `app:app` hoặc gọi `create_app()` chỉ tạo Flask app và đăng ký đầy đủ
blueprint, route, alias, context processor; không kết nối database, cập nhật
schema, nạp dữ liệu hay chạy scheduler. `get_db()` chỉ mở kết nối, không tự
cập nhật schema. Database vận hành phải có schema phù hợp từ trước. Không có
migration/seed nào được thực hiện như một phần của thay đổi này.

Nếu dùng Flask CLI/WSGI thay vì `python app.py`, Website vẫn có đủ route nhưng
scheduler không tự chạy khi import. Muốn có scheduler, gọi
`start_runtime_services(app)` tại hook khởi động tiến trình được chỉ định của
host, sau khi tạo app, và chỉ trong một tiến trình. Cờ idempotent chỉ có hiệu
lực trong cùng một app/process, không phải khóa phân tán giữa nhiều worker.

## Cấu hình test

```python
from app import create_app

app = create_app({
    'TESTING': True,
    'SECRET_KEY': 'isolated-test-only',
    # Optional: callable returning a mock or independently verified test connection.
    # 'DATABASE_CONNECTION_FACTORY': make_test_connection,
})
```

Trong app/request context của app test, `get_db()` báo lỗi nếu thiếu factory;
không fallback sang SQL Server đã cấu hình. `TESTING=True` buộc tắt truy cập
database thật và SMTP kể cả khi caller truyền cờ bật. Factory được gọi nguyên
trạng, không chạy schema hoặc seed. Người viết test phải đảm bảo factory chỉ
trỏ tới mock hoặc database test đã xác nhận độc lập.

Gửi email trả `(False, 'Notifications disabled')`; quét reminder và cập nhật
schema bị từ chối trong context test; hàm khởi động scheduler không chạy worker.
Các hàm chạy ngoài Flask context vẫn là công cụ vận hành hiện có: không gọi
chúng ngoài context trong test. Thông báo in-app được ghi qua connection factory
nếu nghiệp vụ có ghi thông báo; không được cấp factory nối database thật.

Để mở HTTP server test với đầy đủ route, không worker, không kết nối thật:

```powershell
python -B -m flask --app app:create_test_app run --host 127.0.0.1 --port 5001 --no-reload --no-debugger
```

Trang `/login` render được; các route cần dữ liệu sẽ báo lỗi khi chưa cấp
factory. Đây là cấu hình kiểm thử cô lập, không phải môi trường nghiệm thu
nghiệp vụ với SQL Server.

## Chạy riêng test an toàn

```powershell
python -B -m unittest discover -s tests -p test_startup_safety.py -v
```

Không chạy `unittest discover -s tests` không có bộ lọc: các test cũ có thể kết
nối database thật. Bộ test mới chặn `pyodbc.connect`, SMTP/SMTP_SSL và khởi động
thread trước khi import mã ứng dụng. Test HTTP riêng chỉ tạo server loopback
tạm thời, vẫn chặn DB/SMTP, và đóng server sau khi kiểm tra. Test transaction
dùng connection giả, không cần schema hoặc dữ liệu vận hành.

Commit thất bại được rollback rồi ném lại exception gốc; nếu rollback cũng lỗi,
kết nối bị đóng. Commit trên kết nối đã đóng báo lỗi. Context manager luôn đóng
kết nối kể cả khi commit thất bại. Test kiểm tra cả model và API phản hồi,
giữ nguyên lớp kiểm tra đăng nhập/trạng thái tài khoản với kết nối giả.

Các test này không thay thế tích hợp SQL Server. Cần một instance/database test
đã xác nhận độc lập, schema có sẵn và cấu hình kết nối được duyệt trước khi chạy
luồng ghi dữ liệu thật. Chưa kiểm chứng commit/rollback với lỗi driver hoặc SQL
Server thực tế, hay gửi reminder trong môi trường vận hành.
