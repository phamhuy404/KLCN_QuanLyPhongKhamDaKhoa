# VietQR và bill H2T Care

## Chuẩn bị SQL Server

Chạy `database/migrations/20261107_vietqr_payment.sql` **một lần trên bản sao lưu được kiểm tra** trước khi bật webhook. Migration tạo `payment_events` với khóa duy nhất `(provider, event_id)` và đổi mặc định hóa đơn mới sang `Chưa thanh toán`. Nó cũng xóa thời gian/phương thức thu bị ghi mặc định ở các hóa đơn còn chờ. File `database/cosodulieu.sql` là script tạo lại CSDL và có thể xóa dữ liệu; không dùng file đó để nâng cấp CSDL đang chạy.

## Cấu hình

Đặt bốn biến môi trường trước khi chạy Flask:

```text
BANK_ID=MB
BANK_ACCOUNT_NO=<so_tai_khoan_thuc>
BANK_ACCOUNT_NAME=<ten_chu_tai_khoan_thuc>
PAYMENT_WEBHOOK_SECRET=<khoa_bi_mat_tu_SePay_hoac_Casso>
```

Không cấu hình đủ thì API không phát mã QR và webhook từ chối nhận. Số tiền QR lấy từ `hoa_don.thanh_tien`, nội dung là `H2T` + ID số của hóa đơn. Mã QR là ảnh do `img.vietqr.io` cung cấp; cần mạng và tài khoản ngân hàng thật để thử quét.

## Webhook

URL công khai HTTPS: `POST /api/payment/webhook`.

- **SePay:** chọn JSON, sự kiện tiền vào, xác thực API Key. Đặt API Key của webhook bằng `PAYMENT_WEBHOOK_SECRET`; header SePay là `Authorization: Apikey ...`.
- **Casso Webhook cũ:** chọn JSON, đặt Key bảo mật bằng `PAYMENT_WEBHOOK_SECRET`; Casso gửi header `secure-token`.
- **Casso Webhook V2:** đặt Key bảo mật bằng `PAYMENT_WEBHOOK_SECRET`; endpoint xác thực `X-Casso-Signature` SHA-512 theo tài liệu Casso.

Chỉ giao dịch tiền vào, đúng tài khoản nhận, có mã `H2T<id>` nguyên vẹn và đúng số tiền mới được xác nhận. Giao dịch được ghi cùng transaction với hóa đơn, thông báo và trạng thái đơn thuốc. Gửi lại cùng `provider` và `id` không thu lại. Giao dịch không đối soát được trả lỗi và cần kiểm tra ở nhà cung cấp webhook. `GET /api/payment/status/<invoice_id>` yêu cầu phiên Web hoặc Bearer token bệnh nhân, chỉ trả hóa đơn có quyền xem.

## Demo localhost

`POST /api/payment/simulate-confirm/<invoice_id>` chỉ hoạt động khi `DEBUG=True`, từ loopback `127.0.0.1`/`::1`, và có phiên Admin hoặc Lễ tân. Nó ghi giao dịch `SIMULATED` vào cùng luồng xác nhận. Không dùng endpoint giả lập để chứng minh đã nhận tiền thật.

Đặt `DEBUG=False` khi triển khai công khai; `config.py` hiện vẫn để `DEBUG=True` cho môi trường phát triển.

Web/App thăm dò trạng thái mỗi 3 giây trong 10 phút khi màn hình QR mở. Hết thời gian này chỉ dừng màn hình chờ; chuyển khoản đến sau vẫn có thể được webhook đối soát. Trang Web cho in/lưu PDF qua hộp thoại in của trình duyệt. App cho lưu/chia sẻ bill dạng HTML qua hệ điều hành.
