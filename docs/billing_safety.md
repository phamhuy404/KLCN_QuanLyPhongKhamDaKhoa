# Hóa đơn và thu tiền thủ công

## Phạm vi và quyền

Không có cổng thanh toán thật, webhook, ngân hàng hoặc đối soát tự động. Đã bỏ QR tự ghép chuỗi, tài khoản mẫu và thao tác bệnh nhân tự đánh dấu đã trả. Không thay đổi schema/database hiện hữu.

- `GET /api/billing/invoice/<id hoặc mã>` dùng policy đọc hồ sơ chung: bệnh nhân chỉ hóa đơn của mình; quyền đọc nhân viên hiện có được giữ. Danh sách Website bệnh nhân lọc theo bệnh nhân ngay trong SQL, không nạp hóa đơn toàn hệ thống rồi lọc.
- `POST /api/billing/request` chỉ BENHNHAN/ADMIN/LETAN; bệnh nhân phải là chủ hóa đơn. Đây là yêu cầu đọc hướng dẫn, không phải giao dịch lưu bền: trả số tiền từ Backend, `gateway_enabled=false`, `payment_confirmed=false`; không ghi trạng thái, không gửi thông báo nhận tiền, không trả QR có khả năng chuyển khoản.
- `POST /api/billing/pay` chỉ ADMIN/LETAN với danh tính được kiểm tra lại từ tài khoản hiện hành. Model cũng yêu cầu vai trò thu ngân; tên thu ngân lấy từ danh tính, không từ JSON. Không thêm quyền thu cho bác sĩ/dược sĩ/KTV. Quyền nhân viên đọc dữ liệu rộng hiện có chưa thu hẹp khi chưa có xác nhận nghiệp vụ.

Ví dụ API xác nhận thu thủ công, chỉ sau khi thực nhận đủ tiền:

```json
{"invoice_id":123,"confirm_received":true,"expected_amount":150000,"hinh_thuc_thanh_toan":"Tiền mặt"}
```

`expected_amount` chỉ dùng phát hiện màn hình cũ, không quyết định số tiền lưu. Chỉ hỗ trợ `Tiền mặt` hoặc `Chuyển khoản` do thu ngân đối soát thủ công. Không nhận thẻ/VNPay/MoMo/VietQR như một cổng đã tích hợp. Website hỏi xác nhận thực nhận trước khi gửi yêu cầu. Gọi thiếu xác nhận/số tiền trả 400, sai quyền 403, danh tính thiếu/khóa/xóa 401. Hóa đơn không tồn tại, đã hủy, đã trả, sai giá hoặc lỗi commit trả thất bại (API thu trả 409); gọi lặp không thu lần nữa.

## Trạng thái, giá và transaction

- Chỉ hóa đơn `Chưa thanh toán` được thu. Khóa MSSQL `clinic.calendar.v1`, khóa dòng UPDLOCK/HOLDLOCK và UPDATE có điều kiện theo đúng một ID. Không UPDATE bằng `id OR ma_hoa_don`. ID dạng số chỉ hiểu là identity, mã dạng chữ dùng mã hóa đơn.
- Kiểm tra hóa đơn/phiếu khám cùng bệnh nhân; chi tiết không trống; số lượng nguyên dương; tiền không âm, hữu hạn, tối đa hai chữ số lẻ. `sum(so_luong*don_gia)=tong_tien`, và `thanh_tien=tong_tien-tien_bhyt-giam_gia`. Không clamp số tiền sai về 0.
- Giá khám mới lấy `bac_si.gia_kham` nếu khác NULL, nếu NULL lấy `chuyen_khoa.gia_kham_mac_dinh`. Giá 0 có chủ ý được giữ; thiếu cả hai bị từ chối, không giả định 150.000. Giá CLS lấy `dich_vu.don_gia`, có chỉ định thuộc lần khám; giá thuốc từ danh mục `thuoc.don_gia` khi sinh hóa đơn. Tính tiền bằng Decimal.
- Chính sách BHYT khám 80% cũ nay được cấu hình bằng `EXAM_INSURANCE_PERCENT` (mặc định 80); CLS dùng tỷ lệ cấu hình tại dịch vụ. Đây là chính sách hiện có của dự án, chưa chứng nhận tính đúng cho mọi quyền lợi BHYT thực tế. Khoản giảm giá đã lưu được kiểm tra phương trình/giới hạn, không thêm luồng cấp quyền giảm giá.
- Trước thu/lấy hướng dẫn: đối chiếu đơn giá với nguồn giá cấu hình hiện tại. Nếu giá đổi sau lập hóa đơn, chặn để thu ngân đối soát, không tự định giá lại hóa đơn hoặc sửa tiền đã thu. Hóa đơn đã trả vẫn xem được; gọi lại bị chặn trước bước đối chiếu nguồn giá và trước mọi UPDATE/thông báo.
- Hóa đơn thuốc phải khớp duy nhất một đơn cùng phiếu, đơn đã duyệt mua tại viện, chi tiết/tiền nhất quán. Lần thu đầu chỉ đổi chính đơn này sang chờ nhận. Gọi lại hóa đơn đã trả không đổi đơn đã nhận thuốc về chờ nhận, không gửi lại thông báo. Các ghi hóa đơn, đơn và thông báo cùng transaction; lỗi giữa chừng/commit rollback toàn bộ.
- Website không coi hóa đơn hủy là khoản đang chờ; thống kê thực thu của trang thu ngân chỉ tính hóa đơn đã trả.

## File thay đổi trong nhiệm vụ

Nghiệp vụ: [billing_model.py](../models/billing_model.py), [billing_policy.py](../core/billing_policy.py), nguồn lập hóa đơn [medical_record_model.py](../models/medical_record_model.py), [config.py](../config.py).

Route/giao diện: [api_controller.py](../controllers/api_controller.py), [patient_controller.py](../controllers/patient_controller.py), [admin_controller.py](../controllers/admin_controller.py), [bệnh nhân](../templates/patient/billing.html), [thu ngân](../templates/admin/billing.html).

Test mới: [test_billing_safety.py](../tests/test_billing_safety.py), [test_billing_mssql.py](../tests/test_billing_mssql.py). Điều chỉnh fixture/caller hồi quy trong [test_emr_workflow.py](../tests/test_emr_workflow.py), [test_pharmacy_mssql.py](../tests/test_pharmacy_mssql.py), [test_pharmacy_safety.py](../tests/test_pharmacy_safety.py).

## Lệnh chạy và kiểm chứng

Website vẫn `python -B app.py`, dùng MSSQL/pyodbc, SECRET_KEY và cấu hình hiện tại. Lệnh này có thể chạy worker thật; không dùng cho kiểm thử. Dùng `create_test_app()` để tắt worker/SMTP và chặn fallback database.

```powershell
$env:PYTHONPATH='tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_billing_safety tests.test_pharmacy_safety tests.test_startup_safety tests.test_mssql_test_database -v
```

Tích hợp chỉ sau khi có MSSQL riêng được xác nhận theo [hướng dẫn test MSSQL](mssql_test_environment.md), đầy đủ `CLINIC_MSSQL_TEST_DRIVER/SERVER/DATABASE/USERNAME/PASSWORD/EXPECTED_SERVER/MARKER_TOKEN/CONFIRMED`. Login không được truy cập DB chính, marker phải khớp. Các suite fixture tái tạo bảng test, cần xác nhận thêm `CLINIC_MSSQL_TEST_ALLOW_FIXTURES=rebuild-only-disposable-fixtures`.

```powershell
$env:PYTHONPATH='tests'
& C:/laragon/bin/python/python-3.13/python.exe -B -m unittest tests.test_billing_mssql tests.test_pharmacy_mssql tests.test_emr_workflow tests.test_mssql_smoke -v
```

Hiện thiếu cấu hình MSSQL test xác nhận nên các nhóm tích hợp SKIP trước kết nối/DDL/DML. Đã chuẩn bị ca chủ sở hữu/người khác, thu ngân thu/gọi lại/hóa đơn hủy, giá/tổng sai, cấp phát rồi gọi lại và hai yêu cầu thu đồng thời. Chưa chứng minh các ca này chạy trên SQL Server hay trình duyệt → API → MSSQL. Unit/Flask render/Node pass không thay thế tích hợp. Chưa có thanh toán thật, webhook hoặc xác nhận nhận tiền tự động.

Kết quả kiểm tra ngày 2026-10-28: 62 test cô lập đạt (20 billing, 15 pharmacy, 18 startup, 9 bảo vệ MSSQL test); 7 nhóm tích hợp SKIP do thiếu cấu hình xác nhận. Flask render hai giao diện và Node kiểm tra cú pháp JavaScript đạt; HTTP server ở chế độ test khởi động/đáp ứng qua test startup. Không chạy test cũ tác động database thật.
