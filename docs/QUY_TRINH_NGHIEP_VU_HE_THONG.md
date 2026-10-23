# HỆ THỐNG QUẢN LÝ PHÒNG KHÁM ĐA KHOA (H2T HEALTHCARE HIS / EMR)
# TỔNG HỢP VÀ ĐÁNH GIÁ TOÀN BỘ CÁC QUY TRÌNH NGHIỆP VỤ Y TẾ KHÉP KÍN

Tài liệu này mô tả chi tiết 10 quy trình nghiệp vụ đã được triển khai, chuẩn hóa và kiểm thử tự động 100% trên nền tảng Microsoft SQL Server và kiến trúc MVC của hệ thống.

---

## 1. QUY TRÌNH 1: ĐĂNG KÝ, ĐĂNG NHẬP & BẮT BUỘC HOÀN THIỆN HỒ SƠ (PATIENT ONBOARDING)
- **Tác nhân tham gia**: Bệnh nhân.
- **Mục tiêu**: Đảm bảo 100% người bệnh trong hệ thống có đầy đủ thông tin định danh y tế chuẩn, không chứa ký tự lạ hay sai lệch trước khi thực hiện các dịch vụ y tế.
- **Các bước thực hiện**:
  1. **Đăng ký tài khoản trực tuyến**: Bệnh nhân nhập Họ tên, Số điện thoại và Mật khẩu tại `/auth/register`.
  2. **Khởi tạo hồ sơ sơ bộ**: Hệ thống tạo tài khoản (`vai_tro_id = 6`, `trang_thai = 1`) và cờ `da_hoan_thien_ho_so = 0`. Tự động cấp mã bệnh nhân chuẩn `BN2609xxx`.
  3. **Đăng nhập liền trong cùng phiên**: Bệnh nhân đăng nhập bằng SĐT và Mật khẩu tại `/auth/login`.
  4. **Hàng rào chặn thông minh (Middleware Guard)**: Bộ lọc `before_request` nhận diện tài khoản có `da_hoan_thien_ho_so = 0` và tự động chuyển hướng bắt buộc đến trang `/patient/complete-profile`. Bệnh nhân bị phong tỏa quyền truy cập Dashboard và Đặt lịch khám cho đến khi hoàn tất.
  5. **Kiểm tra dữ liệu & Chống ký tự lạ**:
     - Họ tên: Chỉ cho phép chữ cái tiếng Việt và khoảng trắng, không chứa số hay ký tự đặc biệt.
     - Ngày sinh: Định dạng YYYY-MM-DD hợp lệ, không vượt quá ngày hiện tại.
     - CCCD: Bắt buộc đúng 12 chữ số.
     - BHYT: Bắt buộc đúng 10 đến 15 ký tự chữ và số.
     - SĐT người thân khẩn cấp: Đúng 10 chữ số.
     - Nhóm máu, Dị ứng, Tiền sử bệnh: Đối chiếu với danh mục chuẩn trong `data/catalogs/`.
  6. **Kích hoạt tài khoản**: Hệ thống cập nhật bảng `benh_nhan`, bật `da_hoan_thien_ho_so = 1`, mở khóa toàn bộ cổng bệnh nhân.

---

## 2. QUY TRÌNH 2: PHÂN CÔNG & DUYỆT LỊCH LÀM VIỆC CỦA NHÂN SỰ Y TẾ (STAFF SCHEDULING)
- **Tác nhân tham gia**: Bác sĩ, Nhân viên y tế, Tiếp tân, Quản trị viên (Admin).
- **Mục tiêu**: Đảm bảo phân bổ nguồn lực y tế tối ưu, tránh quá tải chuyên khoa trong từng ca trực.
- **Các bước thực hiện**:
  1. **Đăng ký ca trực**: Nhân sự đăng ký ca làm việc theo tuần (Ca 1: 07:30 - 11:30, Ca 2: 13:30 - 17:30, Ca 3: 17:30 - 20:30) tại `/admin/staff?tab=schedules`.
  2. **Ràng buộc định ngạch nghiêm ngặt**:
     - *Giới hạn vai trò*: Tối đa không quá 5 nhân sự cùng 1 vai trò trong 1 ca trực (`check_role_shift_capacity`).
     - *Giới hạn chuyên khoa bác sĩ*: Tối đa không quá 3 bác sĩ thuộc cùng 1 chuyên khoa trong 1 ca trực (`check_doctor_dept_capacity`).
  3. **Trạng thái chờ duyệt**: Ca đăng ký vào CSDL với trạng thái `CHO_DUYET`.
  4. **Duyệt đơn lẻ hoặc Phê duyệt hàng loạt (Bulk Approve)**:
     - Tiếp tân/Admin kiểm tra danh sách chờ tại bảng điều khiển.
     - Chọn duyệt từng ca hoặc duyệt nhiều ca cùng lúc qua API `/api/schedules/bulk-approve`.
     - *Gom nhóm thông báo*: Dù duyệt hàng loạt 10 ca của 1 bác sĩ, hệ thống chỉ gửi đúng 1 thông báo in-app duy nhất đến tài khoản bác sĩ đó để tránh làm phiền ("Lịch làm việc của bạn đã được phê duyệt thành công!").
  5. **Giao diện thời khóa biểu trực quan**:
     - Ô lịch kích thước lớn (155px x 145px) phân tách rõ ràng.
     - Hiển thị vị trí công tác và chuyên khoa.
     - Hover popover xem danh sách đồng nghiệp làm chung ca.
     - Click để mở modal chi tiết toàn bộ nhân sự trực ca đó.

---

## 3. QUY TRÌNH 3: ĐỒNG BỘ ĐẶT LỊCH KHÁM BỆNH TRỰC TUYẾN (APPOINTMENT BOOKING)
- **Tác nhân tham gia**: Bệnh nhân, Hệ thống.
- **Mục tiêu**: Bệnh nhân đặt lịch theo khung giờ và bác sĩ thực tế đang có ca trực đã được phê duyệt.
- **Các bước thực hiện**:
  1. **Chọn ngày khám và khung giờ**:
     - Bệnh nhân chọn ngày khám (từ hôm nay đến 30 ngày tới).
     - Quy tắc khung giờ chuẩn: Giờ khám đầu tiên cách giờ bắt đầu ca 1 tiếng, giờ khám cuối cùng cách giờ kết ca 1 tiếng, mỗi lượt cách nhau 30 phút:
       - *Ca Sáng (07:30 - 11:30)*: 08:30, 09:00, 09:30, 10:30.
       - *Ca Chiều (13:30 - 17:30)*: 14:30, 15:00, 15:30, 16:30.
       - *Ca Tối (17:30 - 20:30)*: 18:30, 19:00, 19:30.
  2. **Đồng bộ danh sách bác sĩ theo ca**: Khi người dùng chọn giờ, hệ thống chỉ hiển thị các bác sĩ có ca trực `DA_DUYET` tương ứng với ca làm việc đó.
  3. **Ghi nhận lịch hẹn**: Lịch hẹn được lưu với mã `LH2609xxx` và trạng thái ban đầu `Chờ tiếp nhận`.
  4. **Phân quyền bảo mật**: Lịch hẹn ở trạng thái `Chờ tiếp nhận` KHÔNG xuất hiện trên danh sách khám của bác sĩ để tránh bác sĩ khám nhầm người chưa làm thủ tục tiếp nhận tại quầy.
  5. **Thông báo tức thì**: Hệ thống gửi thông báo realtime kèm popup toast đến Quản trị viên và Tiếp tân ("Lịch hẹn khám mới: LH2609xxx").

---

## 4. QUY TRÌNH 4: TIẾP NHẬN & ĐIỀU PHỐI BỆNH NHÂN TẠI PHÒNG KHÁM (INTAKE & TRIAGE)
- **Tác nhân tham gia**: Nhân viên Tiếp tân, Bệnh nhân, Bác sĩ.
- **Mục tiêu**: Xác nhận bệnh nhân đã đến phòng khám, chuyển lịch vào hàng đợi của Bác sĩ chuyên khoa.
- **Các bước thực hiện**:
  1. Bệnh nhân đến quầy lễ tân trình diện mã lịch hẹn hoặc CCCD/SĐT.
  2. Tiếp tân tra cứu tại màn hình `/admin/appointments` và nhấn nút "Tiếp nhận".
  3. Trạng thái lịch hẹn chuyển sang `Đã tiếp nhận`.
  4. Hệ thống kích hoạt 2 thông báo in-app song song:
     - Gửi Bác sĩ phụ trách: "Lịch khám mới tiếp nhận: LH2609xxx - Bệnh nhân [Tên] đã vào phòng chờ."
     - Gửi Bệnh nhân: "Lịch khám của bạn đã được Tiếp tân tiếp nhận thành công. Vui lòng di chuyển đến trước cửa phòng khám chuyên khoa."

---

## 5. QUY TRÌNH 5: KHÁM LÂM SÀNG & BỆNH ÁN ĐIỆN TỬ EMR (CLINICAL CONSULTATION)
- **Tác nhân tham gia**: Bác sĩ chuyên khoa, Bệnh nhân.
- **Mục tiêu**: Bác sĩ thăm khám, ghi nhận triệu chứng, mã bệnh ICD-10 và đưa ra hướng điều trị.
- **Hai nhánh phân luồng nghiệp vụ**:
  - **Nhánh A - Khám lâm sàng bình thường (Sức khỏe tốt / Không cần CLS)**:
    - Bác sĩ bấm "Hoàn tất khám & Xuất hóa đơn" ngay từ giao diện EMR.
    - Hệ thống tự động ghi nhận bệnh án (`PK2609xxx`), cập nhật lịch hẹn sang `Đã khám`.
    - Tự động sinh hóa đơn tiền công khám ngoại trú (`HD2609xxx`: 150.000đ).
    - Cấn trừ BHYT thông minh: Nếu bệnh nhân có thẻ BHYT, tự động khấu trừ 80% (120.000đ), bệnh nhân chỉ đóng 30.000đ. Nếu không có BHYT, bệnh nhân thanh toán đủ 150.000đ.
    - Gửi thông báo hoàn tất khám và thông báo thanh toán viện phí đến bệnh nhân.
  - **Nhánh B - Chỉ định Cận lâm sàng (Xét nghiệm máu, Chụp X-quang, Siêu âm,...)**:
    - Bác sĩ chọn các kỹ thuật cận lâm sàng cần thực hiện.
    - Hệ thống tạo phiếu chỉ định `CD2609xxx` với trạng thái `Chờ thực hiện`.
    - Trạng thái phiên khám chuyển sang theo dõi cận lâm sàng.
    - Bệnh nhân nhận thông báo: "Hoàn tất khám lâm sàng & Chuyển Cận lâm sàng: CD2609xxx. Vui lòng di chuyển đến Khu Cận lâm sàng."

---

## 6. QUY TRÌNH 6: THỰC HIỆN CẬN LÂM SÀNG & CHẨN ĐOÁN HÌNH ẢNH (PARACLINICAL & IMAGING)
- **Tác nhân tham gia**: Kỹ thuật viên (KTV) xét nghiệm / CĐHA, Bác sĩ điều trị, Bệnh nhân.
- **Mục tiêu**: Thu thập mẫu, chụp chiếu, tải ảnh chẩn đoán và ghi nhận kết quả định lượng/định tính.
- **Các bước thực hiện**:
  1. KTV tiếp nhận bệnh nhân tại phân hệ `/admin/lab`.
  2. KTV thực hiện kỹ thuật và nhập kết quả phân tích.
  3. **Tải lên hình ảnh chẩn đoán (Upload Media)**:
     - Hỗ trợ ảnh chụp X-quang, siêu âm, nội soi, MRI (JPG, PNG, WebP).
     - Dịch vụ `image_service.py` tự động nén tối ưu sang WebP chất lượng cao lưu trữ tại `static/uploads/can_lam_sang/`.
  4. KTV lưu kết quả -> Phiếu chuyển sang `Chờ duyệt` (khóa sửa đổi tùy tiện).
  5. Bác sĩ điều trị kiểm tra hình ảnh trực tiếp trên bệnh án EMR và bấm "Duyệt kết quả".
  6. Toàn bộ chỉ định trong phiếu hoàn tất -> Phiếu chuyển sang `Đã duyệt`.
  7. Bệnh nhân nhận thông báo: "Đã có kết quả Cận lâm sàng. Vui lòng quay lại phòng khám ban đầu để bác sĩ hội chẩn kết luận."

---

## 7. QUY TRÌNH 7: KÊ ĐƠN THUỐC & LỰA CHỌN NƠI MUA THUỐC CỦA BỆNH NHÂN (E-PRESCRIPTION)
- **Tác nhân tham gia**: Bác sĩ, Bệnh nhân.
- **Mục tiêu**: Kê đơn an toàn, cảnh báo tồn kho và trao quyền lựa chọn nguồn mua thuốc cho người bệnh.
- **Các bước thực hiện**:
  1. Bác sĩ kê đơn gồm danh mục thuốc, liều dùng và cách dùng trong EMR.
  2. **Cảnh báo tồn kho ít & Chặn kê vượt tồn**:
     - Nếu tồn kho <= số lượng cảnh báo tối thiểu: Hiển thị tag cảnh báo màu hổ phách/đỏ.
     - Chặn tuyệt đối không cho phép bác sĩ kê đơn số lượng lớn hơn số lượng tồn thực tế trong kho.
  3. **Khởi tạo đơn thuốc**: Đơn thuốc lưu vào CSDL với trạng thái ban đầu `Chờ bệnh nhân xác nhận mua` và `hinh_thuc_mua = 'Chưa chọn'`.
  4. **Tùy chọn của bệnh nhân (Patient Decision)**:
     - *Lựa chọn 1: "Tự mua ngoài"*:
       - Bệnh nhân nhận đơn thuốc điện tử hợp thức hóa để tự mua tại hiệu thuốc tư nhân.
       - Không sinh hóa đơn thuốc của viện, không trừ kho dược bệnh viện (tránh cấn trừ sai).
     - *Lựa chọn 2: "Mua tại bệnh viện"*:
       - Đơn thuốc chuyển sang trạng thái chuẩn bị tại Nhà thuốc Bệnh viện.
       - Tự động sinh hóa đơn tiền thuốc riêng biệt (`HDT2609xxx`) liệt kê danh mục thuốc (không hiển thị đơn giá lẻ theo đúng quy định).
       - Trừ tồn kho dược viện và khóa đơn chống cấp phát lặp lại.

---

## 8. QUY TRÌNH 8: CẤP PHÁT THUỐC TẠI NHÀ THUỐC BỆNH VIỆN (PHARMACY DISPENSING)
- **Tác nhân tham gia**: Dược sĩ, Bệnh nhân.
- **Mục tiêu**: Cấp phát thuốc an toàn, trừ kho chính xác và chống xuất lặp lại (double-dispense).
- **Các bước thực hiện**:
  1. Dược sĩ kiểm tra đơn thuốc trên màn hình `/admin/pharmacy`.
  2. Kiểm tra tính hợp lệ và tiền sử dị ứng thuốc của người bệnh.
  3. Hệ thống xác nhận cấp phát:
     - Giảm số lượng tồn kho `thuoc.so_luong_ton` đúng bằng số lượng kê.
     - Ghi nhận trạng thái `Đã cấp thuốc`.
     - *Chống cấp phát lặp lại*: Nếu có bất kỳ thao tác bấm xuất thuốc lần 2 trên cùng đơn, hệ thống từ chối ngay lập tức để bảo vệ tồn kho.
  4. **Quy trình hủy/điều chỉnh đơn**: Trong trường hợp bác sĩ/dược sĩ hủy đơn thuốc đã xuất, hệ thống kích hoạt cơ chế `restore_stock` tự động hoàn trả số lượng thuốc về kho và lưu nhật ký kiểm toán `AuditLogger`.

---

## 9. QUY TRÌNH 9: QUẢN LÝ VIỆN PHÍ & CẤN TRỪ BHYT (BILLING & RECONCILIATION)
- **Tác nhân tham gia**: Thu ngân, Kế toán, Bệnh nhân.
- **Mục tiêu**: Thu viện phí minh bạch, cấn trừ đúng tỷ lệ BHYT và ghi nhận doanh thu.
- **Cấu trúc khoản thu & Cơ chế cấn trừ**:
  - `Tổng tiền` = `Tiền khám` + `Tiền Cận lâm sàng (nếu có)` + `Tiền thuốc (chỉ cộng khi mua tại viện)`.
  - `Tiền BHYT chi trả`:
    - Nếu bệnh nhân có thẻ BHYT hợp lệ: Tự động khấu trừ 80% tiền khám (120.000đ) và theo tỷ lệ % danh mục dịch vụ kỹ thuật CLS được bảo hiểm thanh toán.
    - Nếu bệnh nhân KHÔNG có thẻ BHYT: Tiền BHYT = 0đ.
  - `Thực thu (Tiền bệnh nhân trả)` = `Tổng tiền` - `Tiền BHYT chi trả` - `Giảm giá`.
- **Thanh toán**:
  - Thu ngân xác nhận thu tiền mặt, quẹt thẻ hoặc chuyển khoản tại `/admin/billing`.
  - Trạng thái hóa đơn chuyển sang `Đã thanh toán`.
  - Bệnh nhân nhận thông báo tức thì: "Thanh toán thành công: Hóa đơn [Mã] ([Số tiền] VNĐ) đã được thanh toán thành công qua [Phương thức]. Người thu: [Thu ngân]."

---

## 10. QUY TRÌNH 10: THEO DÕI HỒ SƠ 360° & NHẮC LỊCH TÁI KHÁM (PATIENT ENGAGEMENT)
- **Tác nhân tham gia**: Bệnh nhân, Hệ thống tự động.
- **Mục tiêu**: Người bệnh nắm trọn vẹn lịch sử điều trị và không bỏ lỡ lịch hẹn sắp tới.
- **Các bước thực hiện**:
  1. Bệnh nhân đăng nhập cổng `/patient/dashboard`:
     - Xem biểu đồ chỉ số sinh tồn (Huyết áp, Nhịp tim, SpO2, BMI).
     - Tra cứu toàn bộ bệnh án điện tử EMR, chi tiết toa thuốc và kết quả CLS.
  2. **Banner thông minh quét nhắc lịch hẹn (Smart Reminder Banner)**:
     - Hệ thống nền tự động quét các lịch hẹn đã tiếp nhận có ngày khám trùng hôm nay hoặc ngày mai (trong vòng 24h - 48h).
     - Tự động hiển thị thẻ nhắc nhở nổi bật màu xanh ngọc trên đỉnh Dashboard với đồng hồ đếm ngược và thông tin phòng khám/bác sĩ.
  3. Bệnh nhân có thể xem lại lịch sử các đợt thanh toán viện phí tại `/patient/invoices`.
