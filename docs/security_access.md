# Xác thực và quyền sở hữu hồ sơ

> Cấu hình test hiện tại chỉ dùng MSSQL: xem [môi trường kiểm thử MSSQL](mssql_test_environment.md).
> Các đoạn SQLite/RAM và số test đạt bên dưới là ghi chép lịch sử trước khi điều chỉnh, không phải hướng dẫn chạy hiện tại hay bằng chứng MSSQL đã chạy thành công.


## Thay đổi đã áp dụng

- `login_required` và `roles_required` cùng đọc lại định danh bằng
  `UserModel.get_session_user()` mỗi request (cache chỉ trong request).
  Vai trò, trạng thái, liên kết bệnh nhân/bác sĩ và cờ đổi mật khẩu lấy từ DB;
  không lấy quyền từ các giá trị cũ trong cookie session.
- Tài khoản mất, bị khóa, vai trò không hỗ trợ, bệnh nhân mất hồ sơ, nhân viên
  mất hồ sơ/bị khóa hoặc bác sĩ thiếu bản ghi bác sĩ bị từ chối. API trả 401;
  trình duyệt chuyển đến đăng nhập và phiên cũ bị xóa.
- Đặt lịch yêu cầu đăng nhập. Bệnh nhân chỉ đặt cho chính mình. ADMIN/LETAN
  phải chỉ rõ bệnh nhân đang tồn tại. Bác sĩ tuân theo phạm vi chuyên khoa
  hiện có và không được giả mạo bác sĩ/chuyên khoa khi đặt lịch tại quầy.
  Không còn fallback sang bệnh nhân 1.
- Cập nhật hồ sơ cá nhân và chọn nơi mua thuốc chỉ cho bệnh nhân có hồ sơ
  liên kết hiện tại; chọn mua phải đúng chủ đơn. Form hồ sơ luôn dùng ID chủ
  phiên đã xác minh; API từ chối khi client truyền ID của người khác.
- Policy chung trong [security.py](../core/security.py) được dùng cho danh
  sách/chi tiết hồ sơ quản trị và alias, danh sách/chi tiết lịch hẹn, EMR,
  CLS, đơn thuốc và lịch sử liên quan đã sửa. Bác sĩ dùng tập bệnh nhân từ
  `PatientModel.get_by_department()` như danh sách bệnh nhân trước đây;
  thiếu chuyên khoa trả tập rỗng thay vì toàn bộ bệnh nhân. ADMIN/LETAN giữ
  phạm vi hiện có. Cập nhật hồ sơ bệnh nhân bởi bác sĩ cũng kiểm tra tập này.
  Phần hồ sơ bệnh nhân lồng trong chi tiết tài khoản dùng cùng policy; danh sách
  tài khoản lọc bệnh nhân ngoài phạm vi trước khi tính tổng và phân trang.
- `next` chỉ nhận đường dẫn nội bộ bắt đầu bằng một `/`, chặn URL ngoài,
  backslash, control character và các biến thể percent encoding lồng nhau.
  Đăng nhập thành công xóa dữ liệu phiên cũ trước khi tạo phiên mới.

## Điểm cần xác nhận về quyền nhân viên

Chưa tự thay đổi các quyền nghiệp vụ chưa rõ sau đây:

1. Dược sĩ/KTV hiện có quyền đọc rộng hồ sơ bệnh nhân 360 độ qua phân hệ
   quản trị/API. Có giới hạn về đơn thuốc/CLS được giao, theo khoa hay toàn
   phòng khám không? Hiện vẫn giữ phạm vi đọc đó cho tài khoản còn hoạt động
   và có hồ sơ nhân viên phù hợp.
2. Các route `/admin/doctors/<id>/update` và `/avatar` trước đây cho nhân viên
   không phải bác sĩ sửa hồ sơ bác sĩ khác. Bác sĩ chỉ được sửa chính mình;
   kiểm tra này nay dùng ID mới đọc từ DB. Có thu hẹp quyền sửa của Dược sĩ/KTV
   về chỉ ADMIN/LETAN hay vai trò nào khác không? Chưa thay phạm vi này khi
   chưa có xác nhận.
3. API danh sách/chi tiết tài khoản nhân viên hiện có phạm vi rộng, chỉ che
   username cho một số vai trò. Cần quy định quyền xem dữ liệu nhân sự của
   người khác trước khi thu hẹp phạm vi đó.

Đây là các phần chưa chốt chính sách, không phải cam kết toàn bộ phân quyền
nhân viên đã hoàn tất. Cần xác nhận thêm luồng chuyển bác sĩ/CLS khác khoa khi
nghiệm thu chính sách chuyên khoa hiện có.

## Khóa phiên và cách chạy

[config.py](../config.py) không còn khóa phiên mặc định công khai.
Đặt biến môi trường `SECRET_KEY` bằng giá trị ngẫu nhiên riêng, ít nhất 32 ký
tự, dùng cùng giá trị cho các process của cùng một deployment. Ví dụ tạo khóa
trong PowerShell mà không in khóa ra màn hình:

```powershell
$keyBytes = New-Object byte[] 32
$keyGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$keyGenerator.GetBytes($keyBytes)
$keyGenerator.Dispose()
$env:SECRET_KEY = [Convert]::ToBase64String($keyBytes)
python -B app.py
```

Cần lưu khóa an toàn trong cấu hình triển khai để dùng lại sau restart. Đoạn
trên chỉ giữ khóa trong tiến trình shell hiện tại. Không đưa khóa vào Git.

Nếu thiếu khóa, debug/test dùng khóa ngẫu nhiên trong RAM của process; restart
sẽ làm phiên cũ mất hiệu lực. Ngoài debug/test, thiếu khóa làm app từ chối tạo.
Khóa mặc định công khai cũ luôn bị từ chối. Khi đổi khóa, người dùng phải đăng
nhập lại. Cách chạy Website và hook scheduler xem
[startup_safety.md](startup_safety.md). Không dùng lệnh Website để chạy test.

## Chạy kiểm tra an toàn

Từ thư mục gốc Website, dùng Python/dependency đã cài:

```powershell
python -B -m unittest discover -s tests -p test_security_access.py -v
python -B -m unittest discover -s tests -p test_startup_safety.py -v
```

Không chạy test discovery không có bộ lọc vì test cũ có thể chạm DB thật.
Chế độ HTTP cô lập không cấp DB:

```powershell
python -B -m flask --app app:create_test_app run --port 5001 --no-reload --no-debugger
```

Test bảo mật chặn `pyodbc.connect`, SMTP và thread ứng dụng trước khi import.
DB fixture có tên riêng `file:security_<uuid>?mode=memory&cache=shared`, kiểm
tra `PRAGMA database_list` ở từng connection để xác minh không có file DB.
DDL/DML chỉ tạo fixture và kiểm tra dữ liệu trong SQLite RAM, không chạy
migration/seed của ứng dụng. Adapter test chuyển duy nhất `SELECT TOP 1` sang
`LIMIT 1`; không thay SQL sản xuất hoặc tắt validation/quyền.

Luồng HTTP test khởi động server loopback tạm thời, mở trang đăng nhập, gửi
thông tin fixture qua `UserModel.authenticate()` với mật khẩu băm, nhận cookie,
cập nhật hồ sơ qua API và đọc lại DB. Query định danh, policy chuyên khoa và
model cập nhật hồ sơ là mã thật. Test view danh sách/chi tiết bắt dữ liệu render;
một số test form cô lập phần lịch sử bệnh án ngoài mục tiêu kiểm tra.
Nghiệp vụ tạo lịch hẹn/chọn mua thuốc được mock tại biên model để kiểm tra
quyền mà không tạo lịch/thanh toán/thông báo thật.

Chưa nghiệm thu các luồng ghi đặt lịch/chọn mua trên SQL Server, behavior của
driver thực tế, multi-process session hoặc thiết bị Flutter. Cần SQL Server
test độc lập đã xác nhận, schema sẵn có và quyền thử nghiệm phù hợp trước khi
chạy tích hợp các luồng đó. Không thay đổi schema vận hành trong nhiệm vụ này.
