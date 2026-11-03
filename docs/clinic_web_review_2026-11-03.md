# Rà soát web phòng khám — 03/11/2026

## Cấu trúc và luồng được kiểm tra

Ứng dụng Flask đăng ký các blueprint trong `controllers/` từ `app.py`, dùng model trong `models/` và SQL Server. Các bản `api_controller.py`, `user_model.py`, `mobile_patient_api.py` ở thư mục gốc là bản cũ, không phải blueprint mà ứng dụng hiện đăng ký; không sửa các bản đó.

Luồng liên quan: danh mục → đặt lịch/tiếp nhận → phiếu khám → chỉ định và hóa đơn chờ thanh toán → thu tiền. Bản xem trước và bản sau thanh toán sử dụng cùng số tiền đã lưu trên hóa đơn.

## Các thay đổi

1. **Khoa và dịch vụ:** giữ nguồn danh mục SQL dùng chung. Admin có nút **Bổ sung 8 khoa chuyên sâu**, tạo bổ sung Tim mạch, Tiêu hóa - Gan mật, Nội tiết - Đái tháo đường, Hô hấp, Cơ xương khớp, Da liễu, Thần kinh, Tiết niệu. Mỗi mẫu có mô tả, phòng và dịch vụ khám cùng giá mặc định. Thao tác có giao dịch, chạy lại không ghi đè bản ghi đang tồn tại. Khoa/phòng mới mặc định tắt, cần Admin bố trí người phụ trách, vị trí phòng và lịch làm việc, rồi bật hoạt động. Không tự chuyển bác sĩ đang khám sang khoa khác.
2. **Chọn dịch vụ:** danh sách đặt lịch chỉ lấy dịch vụ khám đang hoạt động thuộc khoa đang hoạt động. Gửi mã dịch vụ từ đặt lịch bệnh nhân, tạo lịch của nhân viên và tiếp nhận. Máy chủ kiểm tra loại dịch vụ, khoa và trạng thái. Lựa chọn được lưu bằng mã trong trường lý do hiện có, tra lại phía máy chủ khi lập hóa đơn; dịch vụ khám chính thay giá khám tiêu chuẩn, không thu đồng thời hai khoản. Không cho chọn lặp dịch vụ chính trong chỉ định. Khám/thủ thuật trực tiếp phải phù hợp khoa bác sĩ; xét nghiệm/chẩn đoán hình ảnh có thể chỉ định sang khoa CLS. Dịch vụ thực hiện tại phòng không làm bệnh nhân bị chờ kết quả CLS không tồn tại.
3. **BHYT:** `core/billing_policy.py` có một công thức dùng Decimal:

   `khoản giảm = có BHYT ? min(tổng tiền gốc, mức giảm cấu hình) : 0`

   `phải trả = tổng tiền gốc - khoản giảm`

   Mức mặc định 50.000 VNĐ; Admin thay ở **Sao lưu & Bảo trì → Mức giảm BHYT mô phỏng**, rồi bấm **Lưu cấu hình BHYT & Bảo trì**. Chấp nhận số nguyên VNĐ không âm, kể cả 0. Không lấy mức phần trăm từ bác sĩ hoặc dịch vụ để tính tiền khám mới. Giữ cột phần trăm cũ trong CSDL để không phá dữ liệu hoặc các công cụ nhập cũ.
4. **Bảng giá:** giá gốc và giá minh họa có BHYT dùng cùng công thức. Chú thích rõ giá sau giảm chỉ minh họa hóa đơn một dịch vụ; hóa đơn nhiều dịch vụ phải cộng giá gốc rồi trừ một lần. Bỏ nội dung hứa hẹn đúng tuyến/trái tuyến và quyền lợi 80%/20% trong các trang liên quan.
5. **Xem/in:** nhân viên và bệnh nhân dùng chung mẫu `templates/invoice_preview.html`. Hóa đơn chưa thanh toán in nhãn **TẠM TÍNH — CHƯA THANH TOÁN**; sau thu in hóa đơn/biên lai. Có đối tượng, chi tiết dịch vụ/số lượng/giá gốc, tổng, giảm và phải trả. Xem/in không ghi nhận thanh toán. Kiểm tra quyền sở hữu của bệnh nhân và quyền truy cập hồ sơ của nhân viên. Thu tiền đối chiếu `expected_amount`, không tính lại mức giảm hiện tại.
6. **Bảo trì:** giữ cờ và thông báo riêng cho bệnh nhân/nhân viên, bổ sung bao phủ các API dùng chung như đặt lịch, thanh toán, kho dược và danh mục. Admin vẫn truy cập để tắt bảo trì; khách vẫn đến trang đăng nhập. API nghiệp vụ bị chặn trả JSON 503. Không chấp nhận chuỗi `"false"` làm trạng thái boolean. Cache ghi bằng thay thế tệp nguyên tử, nhận biết thay đổi từ tiến trình khác và có thời hạn đọc lại CSDL. Lưu cấu hình thất bại không báo thành công.
7. **Hoạt ảnh:** giữ hiệu ứng hiện có, bổ sung thời lượng chuyển tiếp nhẹ và quy tắc chung cho `prefers-reduced-motion`, kể cả phần tử reveal để không bị ẩn nội dung.

Tắt mặc định phục hồi backup khi khởi động để tránh ghi đè dữ liệu hiện tại ngoài ý muốn. Vẫn có thể chủ động bật cấu hình hoặc dùng `--restore-latest` theo cơ chế cũ.

## Kết quả kiểm tra

- `C:/laragon/bin/python/python-3.13/python.exe -B -m unittest discover -s tests -v`: **33/33 ca qua**, gồm 14 ca API di động có sẵn và 19 ca hồi quy mới.
- Kiểm tra cú pháp Python các module controller/model/core và parse toàn bộ mẫu Jinja: qua.
- Kiểm tra chẩn đoán trình soạn thảo đối với các vùng mã được sửa: không có lỗi được trả về.
- Kiểm thử dùng dữ liệu giả lập và cấu hình test; không seed, phục hồi hoặc chỉnh dữ liệu khám thật.

Các ca chính: giảm một lần trên tổng nhiều dịch vụ; không BHYT; mức giảm 0; tổng nhỏ hơn mức giảm; dữ liệu tiền không hợp lệ; dịch vụ sai khoa/sai loại; không chèn được mã dịch vụ qua lý do tự nhập; luồng `save_examination` ghi đúng tổng 400.000, giảm 50.000, phải trả 350.000; thu đúng số đã xem và từ chối số cũ; giá công khai 200.000/150.000; quyền xem/in hóa đơn; hai cờ bảo trì độc lập; API nhân viên dùng chung; API di động; Admin đăng nhập; cấu hình sai; lỗi lưu cấu hình; thêm danh mục không ghi đè bản ghi có sẵn.

## Kiểm tra vận hành cần thực hiện trên môi trường SQL Server thử nghiệm

1. Admin bổ sung khoa, bố trí bác sĩ đúng chuyên môn, phòng và ca trực; bật khoa/phòng. Đối chiếu khoa/dịch vụ trên trang công khai, đặt lịch và quản trị.
2. Đặt lịch theo dịch vụ chuyên khoa; kiểm tra tiếp nhận hiển thị mã/tên dịch vụ trong lý do. Đổi khoa kiểm tra danh sách dịch vụ được lọc và API từ chối dịch vụ khoa cũ.
3. Cấu hình giảm 50.000; lập phiếu có nhiều dịch vụ cho hai bệnh nhân có/không BHYT. So sánh hóa đơn tạm tính, bản in và sau thu. Kiểm tra thêm mức 0 và mức lớn hơn tổng.
4. Bật lần lượt từng cờ bảo trì; kiểm tra trực tiếp các API qua tài khoản bệnh nhân/nhân viên, rồi đăng nhập Admin và tắt. Kiểm tra thông báo riêng, nhiều tiến trình nếu có.
5. Kiểm tra bố cục bản in trên A4, điện thoại và chế độ giảm chuyển động của hệ điều hành/trình duyệt.

## Giới hạn và quyết định giữ tương thích

- Chưa chạy kiểm thử tích hợp trên SQL Server thật, chưa kiểm tra hình ảnh giao diện hoặc máy in thực tế. Bộ test không chứng minh được các ràng buộc/trigger riêng của CSDL đang triển khai.
- Chưa bấm bổ sung dữ liệu trên CSDL hiện tại. Việc bố trí bác sĩ đủ chuyên môn và bật 8 khoa mới cần người quản trị thực hiện trong Admin; chức năng bổ sung không tạo bác sĩ giả hoặc tự đổi phân công hiện có.
- Mức giảm áp dụng cho hóa đơn khám + dịch vụ/CLS của lượt khám. Hóa đơn thuốc tách riêng giữ cơ chế hiện có và không được giảm thêm lần thứ hai cho cùng lượt khám.
- Hóa đơn đã lập giữ nguyên tiền đã lưu, kể cả hóa đơn lịch sử tính theo chính sách cũ; không hồi tố tính lại. Nếu bảng giá nguồn thay đổi trước khi thu, cơ chế đối soát cũ vẫn có thể từ chối thu thay vì tự sửa hóa đơn.
- Chưa thêm cột riêng cho dịch vụ trên lịch hẹn; mã dịch vụ lưu trong trường lý do hiện có để không cần đổi schema. Không xóa/sửa thủ công dấu `[Dịch vụ #...]` bằng công cụ ngoài ứng dụng.
- Hóa đơn mới lưu nhãn `[Có BHYT]`/`[Không BHYT]` trên khoản khám chính để giữ đối tượng kể cả mức giảm 0, không cần thay schema. Hóa đơn cũ chưa có nhãn dùng khoản giảm và hồ sơ hiện tại làm phương án tương thích; không hồi tố chỉnh lịch sử.
- Mô phỏng này không xác minh thẻ, không xử lý tuyến, tỷ lệ hưởng hoặc quyết toán BHYT; không phải chính sách BHYT thực tế.
