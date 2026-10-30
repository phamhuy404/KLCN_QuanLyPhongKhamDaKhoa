# Auth Mobile v1 — Website chung tài khoản, MSSQL/pyodbc

## Endpoint và JSON

Không dùng cookie Flask làm token Mobile. Không dùng token Mobile để vượt các policy của API Website. Chỉ phạm vi auth Mobile được triển khai trong nhiệm vụ này; các phân hệ lâm sàng Mobile khác không được chứng nhận chạy E2E.

| Endpoint | Request | Thành công |
|---|---|---|
| POST `/api/v1/mobile/auth/register` | `ho_ten`, `sdt`, `ngay_sinh` YYYY-MM-DD, `gioi_tinh` Nam/Nữ/Khác, `password`, `email` tùy chọn | 201, user và token |
| POST `/api/v1/mobile/auth/login` | `identifier` (username/SĐT/email Website), `password` | 200, user và token |
| GET `/api/v1/mobile/auth/me` | Header `Authorization: Bearer <token>` | 200, user và thời hạn, không cấp token mới |
| POST `/api/v1/mobile/auth/logout` | Header Bearer | 200 khi đã ghi vô hiệu hóa hoặc yêu cầu lặp cùng token |

Payload thành công login/register có đúng các trường sau (ID do DB cấp, không cố định):

```json
{
  "success": true,
  "access_token": "<server-signed-token>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": 1793149200,
  "user": {
    "account_id": 11,
    "patient_id": 101,
    "role": "BENHNHAN",
    "name": "<tên bệnh nhân>",
    "email": "",
    "phone": "<SĐT>",
    "patient_code": "<mã bệnh nhân>"
  }
}
```

`account_id`/`patient_id` là số nguyên dương riêng biệt theo bảng `tai_khoan`/`benh_nhan`, không được hoán đổi hoặc mặc định 1. Entity Flutter tiếp tục dùng `User.id` là patient_id dạng chuỗi và `User.accountId` là account_id dạng chuỗi. `/me` trả `success,user,token_type,expires_at`, không `access_token`/`expires_in`. Các mốc thời gian là Unix UTC giây; ví dụ trên chỉ minh họa schema, không phải token/tài khoản demo dùng đăng nhập.

Lỗi JSON thống nhất: `{"success":false,"error_code":"INVALID_CREDENTIALS","message":"..."}`. Mọi response auth có `Cache-Control: no-store`.

| HTTP | error_code |
|---|---|
| 400 | VALIDATION_ERROR: trường thiếu/sai kiểu, ngày không hợp lệ, mật khẩu dưới 6 hoặc có khoảng trắng đầu/cuối |
| 409 | ACCOUNT_EXISTS: trùng SĐT/email/tài khoản/hồ sơ; không tự gắn một hồ sơ cũ chưa có tài khoản |
| 401 | INVALID_CREDENTIALS, ACCOUNT_UNAVAILABLE, TOKEN_REQUIRED, TOKEN_INVALID, TOKEN_EXPIRED, TOKEN_REVOKED |
| 403 | ROLE_NOT_ALLOWED, PASSWORD_CHANGE_REQUIRED |
| 503 | REGISTRATION_FAILED hoặc SERVICE_UNAVAILABLE: lỗi DB/commit/khóa ký; không trả SQL hay token chưa commit |

Đăng ký Mobile gọi chung `UserModel.register_patient`, lưu đúng ngày sinh/giới tính gửi lên, tạo cùng tài khoản/hồ sơ/sinh hiệu NULL như Website. Không thêm user store, không tạo dữ liệu y tế mẫu. Luồng form/redirect/cookie Website giữ nguyên; bổ sung transaction mutex cho hàm đăng ký chung để các request hợp tác không đua mã hồ sơ. Quy tắc mật khẩu dùng chung Website, chưa thay chính sách toàn hệ thống. Mobile từ chối tài khoản thiếu hồ sơ, nhiều hồ sơ liên kết không rõ, vai trò khác BENHNHAN hoặc buộc đổi mật khẩu trên Website.

## Token, logout và cấu hình

- Dùng `itsdangerous` đã có theo Flask, SHA-256 với salt Mobile riêng; token có chữ ký, không phải JWT và không được client tự coi nội dung giải mã là danh tính. Claims chỉ có account/patient ID, iat/exp, jti ngẫu nhiên và HMAC dấu phiên bản mật khẩu; không có mật khẩu hoặc dữ liệu y tế.
- Mặc định TTL 3600 giây, không refresh token, không gia hạn ngầm qua `/me`. `MOBILE_TOKEN_TTL_SECONDS` trong cấu hình app phải là int từ 60 đến 86400. Hết hạn phải đăng nhập lại.
- Ký bằng `MOBILE_TOKEN_SECRET` nếu có, nếu không dùng SECRET_KEY của app. Cần khóa bí mật ổn định tối thiểu 32 byte, dùng chung giữa worker/instance phục vụ cùng hệ thống. Xoay khóa sẽ vô hiệu hóa mọi token. Không ghi khóa/token vào Git hoặc log. Khóa debug ngẫu nhiên theo process chỉ dành cho phát triển; restart có thể buộc đăng nhập lại.
- `/me` xác minh chữ ký/thời hạn, tài khoản còn tồn tại/hoạt động, vai trò BENHNHAN, hồ sơ khớp, cờ đổi mật khẩu và dấu mật khẩu hiện hành. Đổi mật khẩu, xóa hồ sơ, đổi vai trò hoặc khóa tài khoản làm token bị từ chối. Khóa tài khoản là từ chối trong thời gian khóa; muốn vô hiệu hóa vĩnh viễn phiên còn hạn cần logout/đổi mật khẩu/xoay khóa, không giả định mở khóa tự tạo version mới.
- Logout ghi `MOBILE_LOGOUT` và jti/expiry vào `audit_log` hiện có, không lưu bearer token. Việc vô hiệu hóa được kiểm tra trên DB nên có hiệu lực giữa các process/restart. Gọi lặp không ghi lần hai; chỉ logout token đó, không tự đăng xuất thiết bị khác. Token còn chữ ký/thời hạn được phép tự revoke kể cả tài khoản đã khóa/xóa; nhánh này không cấp quyền xem dữ liệu.
- Không thêm bảng/migration. Cần schema audit hiện có và MSSQL hỗ trợ JSON_VALUE (SQL Server 2016+). Login/register không cấp token nếu không đọc được kho revoke. Không tự dọn audit hoặc thay dữ liệu cũ. Kiểm thử cạnh tranh/hiệu năng audit trên MSSQL vẫn chưa chạy.

## Flutter

- Giữ `flutter_secure_storage`/Dio đã có, không đổi dependency. Chỉ lưu token và expiry trong một JSON secure-storage entry; không lưu mật khẩu hoặc coi thông tin cache là danh tính.
- Restore gọi `/me`; 401/403 hoặc dữ liệu phiên hỏng thì xóa phiên. Lỗi mạng/timeout/503 không khôi phục user, giữ token để có thể thử lại. Token cũ `auth_token` chỉ được chuyển sang định dạng mới sau `/me` thành công.
- Connect/send/receive timeout 15 giây, không follow redirect và không bỏ kiểm chứng TLS. Bản release bắt buộc HTTPS. HTTP emulator chỉ dành cho debug; Android main có INTERNET, tắt backup, chỉ debug cho cleartext.
- Logout xóa danh tính local và đưa token cần revoke vào secure storage trước khi gọi server. Khi offline, UI báo chưa được server xác nhận; lần login/restore sau thử revoke lại. Không hứa logout server thành công khi chỉ xóa local. Token còn có thể dùng đến lúc server revoke hoặc hết TTL. Lỗi native secure storage không được đổi sang lưu plaintext.
- Repository tuần tự hóa các thao tác phiên; viewmodel bỏ kết quả async cũ để restore/login trễ không ghi đè logout mới. Các plugin Keychain/Keystore/backup trên thiết bị thật vẫn cần kiểm tra.

## Chạy và kiểm thử an toàn

Website giữ `python -B app.py`, có thể khởi động worker thật nên không dùng để test. Không chạy migration/seed hoặc toàn bộ test cũ.

Backend unit/contract (mock SQL protocol, không phải MSSQL tích hợp):

```powershell
$env:PYTHONPATH='tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_mobile_auth_contract tests.test_startup_safety tests.test_billing_safety tests.test_pharmacy_safety tests.test_mssql_test_database -v
```

Tích hợp chỉ sau khi cấu hình DB MSSQL test riêng có marker/login không truy cập DB chính theo [hướng dẫn MSSQL](mssql_test_environment.md). Cần các biến CLINIC_MSSQL_TEST_* và cờ fixture cho phép tái tạo bảng; thiếu thì SKIP trước kết nối/DDL/DML:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_mobile_auth_mssql -v
```

Để Flutter kết nối server test dùng schema test đã được chuẩn bị/duyệt, đặt MOBILE_TOKEN_SECRET bí mật dành riêng môi trường test (ít nhất 32 byte), rồi chạy:

```powershell
& C:/laragon/bin/python/python-3.13/python.exe -B run_mobile_auth_test_server.py
```

Script chỉ dùng factory MSSQL đã xác nhận, xác minh marker trước khi listen 127.0.0.1:5001, không tạo schema/seed/worker/SMTP. Không có cấu hình thì dừng, không fallback database Website. Các lần register/logout sẽ ghi vào DB test đã xác nhận khi bạn thực sự sử dụng API.

Từ thư mục Flutter, dùng SDK/package hiện có:

```powershell
flutter --no-version-check test --no-pub test/auth_repository_contract_test.dart test/widget_test.dart
flutter --no-version-check analyze --no-pub lib/data/repositories/auth_repository_impl.dart lib/presentation/viewmodels/auth_viewmodel.dart lib/screens/profile/profile_screen.dart test/auth_repository_contract_test.dart
flutter run --no-pub --dart-define=API_BASE_URL=http://10.0.2.2:5001
```

Lệnh run cần Android SDK/emulator đã được người dùng chuẩn bị. Thiết bị thật cần URL test server được phép và cấu hình TLS/mạng phù hợp; script mặc định chỉ listen loopback, không tự mở ra LAN. Không dùng URL DB vận hành để nghiệm thu.

Đã kiểm tra: Backend contract/hồi quy, Flutter repository mock Dio/secure storage, analyzer. Build Android thất bại do chưa có Android SDK; không tự cài. Build bundle host `flutter --no-version-check build bundle --debug --no-pub --target-platform=windows-x64` đạt, chỉ chứng minh biên dịch Dart/asset, không phải APK hay E2E. Chưa có MSSQL test xác nhận nên suite tích hợp SKIP; chưa chứng minh đăng ký từ Flutter → Backend → MSSQL, đăng nhập Website cùng tài khoản trên DB thật hoặc native secure storage trên Android/iOS. Lưu token thành công không phải bằng chứng đăng nhập E2E.

Kết quả ngày 2026-10-28: 73 test Backend cô lập/hồi quy đạt (11 Mobile contract, 18 startup, 20 billing, 15 pharmacy, 9 MSSQL guard); 3 lớp Mobile/security/smoke MSSQL SKIP. Flutter đạt 11 test repository/viewmodel và 1 widget test mở/thoát auth. Có test secure storage lỗi và login trả muộn sau logout. Server test đã được kiểm tra dừng khi thiếu cấu hình, không fallback DB chính. Không chạy test cũ có tác động DB thật.

## File liên quan

[mobile_auth.py](../core/mobile_auth.py), [mobile_auth_controller.py](../controllers/mobile_auth_controller.py), [app.py](../app.py), [config.py](../config.py), [UserModel](../models/user_model.py), [server test](../run_mobile_auth_test_server.py), [contract test](../tests/test_mobile_auth_contract.py), [MSSQL test](../tests/test_mobile_auth_mssql.py), [startup test](../tests/test_startup_safety.py). Flutter: AuthRepositoryImpl, AuthViewModel, ProfileScreen, Android manifests và test repository trong dự án Mobile.
