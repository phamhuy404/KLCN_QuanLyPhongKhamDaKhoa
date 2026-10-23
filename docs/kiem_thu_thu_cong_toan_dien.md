# CẨM NANG KIỂM THỬ THỦ CÔNG TOÀN DIỆN (MANUAL TESTING GUIDE)
Dành cho nhóm thực hiện nghiệm thu và kiểm tra tính năng từ khi chuyển sang Microsoft SQL Server

Tài liệu này tổng hợp toàn bộ các thay đổi kiến trúc, tính năng nâng cấp và cung cấp kịch bản kiểm thử thủ công từng bước chi tiết (tài khoản đăng nhập, các bước thao tác, dữ liệu nhập và kết quả mong đợi) để nhóm có thể tự kiểm tra thực tế 100% trên giao diện website.

---

## PHẦN I: TỔNG HỢP CÁC THAY ĐỔI và NÂNG CẤP TÍNH TỪ KHI DỰ ÁN DÙNG SQL SERVER

Từ thời điểm chuyển đổi cơ sở dữ liệu hoàn toàn sang **Microsoft SQL Server**, dự án đã được tái cấu trúc và nâng cấp toàn diện các phân hệ:

1. **Kiến trúc và CSDL**:
   - Chuyển đổi 100% sang Microsoft SQL Server (`DB_ENGINE = 'sqlserver'`).
   - Sắp xếp và phân vùng thư mục theo chuẩn MVC: `controllers/`, `models/`, `database/` (`cosodulieu.sql`), `docs/`, `static/`, `templates/`, `tests/`.
   - Bổ sung cột `hinh_anh_kham NVARCHAR(MAX)` vào bảng `phieu_kham` để lưu trữ chuỗi JSON danh sách ảnh khám lâm sàng.
   - Nâng cấp cột `file_ket_qua` trong bảng `chi_tiet_chi_dinh` sang `NVARCHAR(MAX)` để lưu trữ mảng JSON tối đa 10 ảnh cận lâm sàng.
   - Bổ sung cột `trang_thai_lam_viec` trong bảng `bac_si` (`Đang làm việc` vs `Ngoài giờ làm việc`).
   - Bổ sung cột `hinh_thuc_mua` (`Chờ bệnh nhân chọn`, `Tự mua ngoài`, `Mua tại bệnh viện`) trong bảng `don_thuoc`.
   - Bổ sung cột `trang_thai_nhan_thuoc` (`Chưa nhận thuốc`, `Đã nhận thuốc`) trong bảng `hoa_don`.

2. **Quản lý Tài khoản và Hồ sơ**:
   - **Bệnh nhân đăng ký mới**: Bắt buộc chuyển hướng đến trang hoàn thiện hồ sơ lần đầu (`/patient/complete-profile`). Kiểm tra regex tiếng Việt chuẩn, chặn ký tự đặc biệt, kiểm tra CCCD 12 số, SĐT 10 số.
   - **Admin tạo Bác sĩ mới**: Tạo nhanh bác sĩ tại trang `/admin/doctors` với mật khẩu mặc định `123`. Khi bác sĩ đăng nhập lần đầu, bắt buộc đổi mật khẩu và điền thông tin chuyên môn (chuyên khoa, phòng khám, học vị).
   - **Trang Hồ sơ cá nhân nội bộ (`/admin/profile`)**: Tạo trang hồ sơ riêng cho toàn bộ nhân sự (`ADMIN`, `BACSI`, `LETAN`, `DUOCSI`, `KTV`), chứa thông tin hành chính chuyên môn (không có thông tin bệnh án) và hỗ trợ đổi mật khẩu tài khoản trực tiếp có xác thực mật khẩu cũ.
   - **Huy hiệu trạng thái bác sĩ**: Hiển thị trạng thái hoạt động dưới tên bác sĩ (`🟢 Đang làm việc` nếu đang trong ca trực hôm nay, hoặc `⚪ Ngoài giờ làm việc`).

3. **Lịch làm việc và Phân công ca trực (`/admin/schedules`)**:
   - Ô lịch to hơn, màu sắc phân biệt trực quan, hiển thị chuyên khoa và vị trí phòng khám làm việc.
   - Mặc định điền khoa của bác sĩ/nhân viên khi đăng ký ca làm.
   - Rê chuột vào ô lịch để xem tên đồng nghiệp cùng trực.
   - Bấm mở rộng xem toàn bộ nhân viên đăng ký ca đó (Tiếp tân và Admin).
   - Tối đa 3 bác sĩ cùng khoa trên một ca trực.
   - Tiếp tân/Admin duyệt đồng loạt nhiều ca cùng lúc để giảm thiểu số lượng thông báo.
   - **Phân quyền đăng ký**:
     + `ADMIN`: Không đăng ký và không xuất hiện trên lịch làm việc.
     + `LETAN`: Tự đăng ký và **tự động duyệt ngay** (`DA_DUYET`), không cần chờ cấp trên duyệt.
     + `BACSI`, `DUOCSI`, `KTV`: Đăng ký ở trạng thái chờ duyệt `CHO_DUYET`.
   - **Điều phối khi hủy ca trực**: Khi duyệt hủy ca trực của bác sĩ, các lịch hẹn chưa khám của ca đó tự động chuyển về `Chờ tiếp nhận` (`bac_si_id = NULL`) và bắn thông báo nhắc Lễ tân điều phối bác sĩ khác.

4. **Đặt lịch khám trực tuyến và Tiếp nhận**:
   - Đồng bộ giờ hẹn `gio_hen` với ca trực `ca_lam` (Sáng 08:00 - 11:30: Ca 1; Chiều 13:30 - 17:00: Ca 2).
   - **Chống đặt trùng giờ**: Bệnh nhân không thể đặt 2 lịch hẹn vào cùng một khung giờ trong cùng ngày.
   - **Chặn đổi lịch (Reschedule) bất hợp lệ**: Không cho phép đổi ngày giờ lịch hẹn khi đã ở trạng thái `Đã khám`, `Hoàn thành` hoặc `Đã hủy`.
   - Tiếp tân gán bác sĩ tiếp nhận tự động tăng quota `so_luong_da_dang_ky` của ca trực.
   - Hiển thị ngẫu nhiên bác sĩ ở trang chủ mỗi lượt tải.

5. **Khám EMR 2 giai đoạn và Quản lý hình ảnh (Tối đa 10 ảnh, Lưới 2x2, Lightbox)**:
   - **Kéo thả / Chọn tối đa 10 ảnh**: Bác sĩ (khám lâm sàng) và Kỹ thuật viên (chẩn đoán hình ảnh) có Dropzone hỗ trợ kéo thả hoặc click chọn tối đa 10 ảnh cùng lúc.
   - **Lưới xem trước 2x2**: Khung 2 cột xem trước nhỏ có thanh cuộn (`overflow-y-auto`), hiển thị số lượng ảnh và nút xóa ảnh.
   - **Lightbox phóng to**: Bấm vào bất kỳ ảnh nào để phóng to xem chi tiết chuẩn HD.
   - **Nén WebP chuẩn hóa**: Tự động nén WebP an toàn tại BackEnd (< 80KB), lưu dạng JSON mảng đường dẫn.
   - **Khám EMR 2 giai đoạn**:
     + Giai đoạn 1: Bác sĩ khám sơ bộ, tải ảnh lâm sàng và chỉ định cận lâm sàng. Phiếu khám chuyển `Chờ kết quả CLS`, bệnh nhân **chỉ nhận thông báo đi làm CLS**, chưa nhận thông báo hoàn tất khám.
     + KTV phòng Lab: Xem badge `Đã đóng phí` / `Chưa đóng phí` trên phiếu chỉ định, nhập kết quả, tải tối đa 10 ảnh CĐHA.
     + Giai đoạn 2: Bác sĩ mở Tab 4 xem kết quả CLS và ảnh chụp, bấm **"Kết Luận và Hoàn Tất Ca Khám Sau CLS"** (`/api/emr/finish`). Hệ thống chốt ICD-10, chuyển phiếu khám sang `Hoàn thành`, lịch hẹn sang `Đã khám` và gửi thông báo hoàn tất khám + đơn thuốc.
   - **Khám bình thường 1 chạm**: Nút *"Sức Khỏe Tốt (Xuất Hóa Đơn Ngay)"* kết thúc phiên khám ngay lập tức cho ca khám khỏe bình thường.
   - **Cảnh báo dị ứng thuốc thời gian thực**: So khớp tên thuốc và hoạt chất với tiền sử dị ứng bệnh nhân; hiển thị banner cảnh báo đỏ và popup xác nhận an toàn trước khi thêm thuốc vào toa.

6. **Chuẩn hóa quy trình cấp phát thuốc 3 bước**:
   - Bác sĩ kê đơn điện tử -> Ban đầu ở trạng thái `Chờ bệnh nhân xác nhận mua`.
   - Bệnh nhân chọn:
     + *Tự mua ngoài*: Trạng thái đơn thành `Mua ngoài`, không sinh công nợ, không trừ kho thuốc viện.
     + *Mua tại bệnh viện*: Trạng thái đơn thành `Chờ duyệt`, sinh hóa đơn thuốc `HDT...` tạm thời.
   - Bệnh nhân có thể đổi ý sang `Tự mua ngoài` trước khi đơn được duyệt (tự động hủy hóa đơn tạm `HDT...`).
   - Tiếp tân/Admin duyệt đơn thuốc: Trả về trạng thái `'Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy'`, **khóa chức năng đổi sang mua ngoài** của bệnh nhân. Tiếp tân/Admin **tuyệt đối KHÔNG trừ kho** ở bước này.
   - Bệnh nhân thanh toán hóa đơn thuốc -> Hóa đơn chuyển `Đã thanh toán` kèm `trang_thai_nhan_thuoc = 'Chưa nhận thuốc'`; đơn thuốc chuyển `Chờ nhận thuốc`.
   - Dược sĩ / Quản lý kho xem được đơn thuốc đã duyệt và đã thanh toán. Dược sĩ bấm **Cấp phát thuốc** -> **LÚC NÀY MỚI TRỪ TỒN KHO THUỐC**, cập nhật đơn thuốc sang `Đã nhận thuốc` và hóa đơn sang `Đã nhận thuốc`. Tiếp tân/Admin không còn quyền cấp phát trừ kho.

7. **Quản lý viện phí và Phân biệt hóa đơn thuốc**:
   - Tự động cấn trừ BHYT 80% tiền khám + tỷ lệ danh mục CLS cho bệnh nhân có thẻ BHYT hợp lệ.
   - Hóa đơn thuốc chỉ hiển thị tổng tiền thuốc theo quy định (ẩn đơn giá lẻ).
   - Tích hợp cổng VietQR động trực tuyến 24/7 và tiền mặt tại quầy.
   - Tự động hủy hóa đơn tiền khám khi hủy lịch hẹn.
   - Nhận diện chính xác hóa đơn thuốc qua tiền tố `HDT...`, loại bỏ nhầm lẫn với hóa đơn khám `HDK...`.

8. **Hệ thống thông báo tức thì đa kênh (Real-time Notifications)**:
   - Thông báo cho Tiếp tân/Admin khi có bệnh nhân đặt lịch hẹn mới.
   - Thông báo cho Bác sĩ khi lịch khám được duyệt tiếp nhận.
   - Thông báo cho Tiếp tân/Admin khi nhân viên đăng ký ca làm việc.
   - Thông báo cho Bác sĩ/Nhân viên khi ca làm việc được duyệt.
   - Thông báo cho Bệnh nhân khi lịch khám được xác nhận hoặc hủy.
   - Thông báo cho Bệnh nhân theo từng chặng khám: đi làm CLS, hoàn tất khám, có đơn thuốc điện tử, thông báo thanh toán viện phí.
   - Thông báo cho Tiếp tân điều phối khi bác sĩ hủy ca trực.
   - Thông báo cho Dược sĩ khi có đơn thuốc đã thanh toán cần cấp phát.

---

## PHẦN II: KỊCH BẢN KIỂM THỬ THỦ CÔNG TỪNG BƯỚC (MANUAL TEST CASES)

### KỊCH BẢN 1: Admin tạo Bác sĩ mới và Bác sĩ đăng nhập lần đầu
- **Mục tiêu**: Kiểm tra quy trình tạo tài khoản bác sĩ mới với mật khẩu mặc định `123`, bắt buộc đổi mật khẩu và điền thông tin chuyên khoa lần đầu.
- **Các bước thực hiện**:
  1. Đăng nhập tài khoản **Admin** (`admin` / `admin123`).
  2. Truy cập menu **Bác Sĩ** (`/admin/doctors`). Bấm nút **"Thêm Bác Sĩ Mới"**.
  3. Điền thông tin:
     - Tên đăng nhập: `bs_test_01`
     - Họ và tên: `BS. Nguyễn Văn Nghiệm`
     - Chuyên khoa: `Khoa Nội Tổng Quát`
     - Số điện thoại: `0908888777`
     - Email: `bstest01@h2thealthcare.vn`
     - Bấm **"Tạo Tài Khoản"**.
  4. Đăng xuất tài khoản Admin.
  5. Đăng nhập tài khoản Bác sĩ mới: `bs_test_01` với mật khẩu mặc định `123`.
  6. **Kết quả mong đợi**:
     - Hệ thống tự động chuyển hướng đến trang hoặc modal hoàn thiện hồ sơ bác sĩ lần đầu (`/admin/doctor/complete-profile`).
     - Bác sĩ nhập mật khẩu mới (ví dụ: `Password@123`), chọn lại chuyên khoa/phòng khám, học vị `BS. CKI`, số năm kinh nghiệm `8 năm`.
     - Bấm **"Lưu Hồ Sơ và Đổi Mật Khẩu"** -> Thông báo thành công và chuyển vào phân hệ EMR.
     - Đăng xuất rồi đăng nhập lại bằng mật khẩu cũ `123` -> Bị từ chối. Đăng nhập bằng `Password@123` -> Thành công.

---

### KỊCH BẢN 2: Bệnh nhân đăng ký mới và Bắt buộc hoàn thiện hồ sơ
- **Mục tiêu**: Kiểm tra đăng ký người dùng mới và quy định bắt buộc hoàn thiện thông tin trước khi dùng dịch vụ.
- **Các bước thực hiện**:
  1. Mở trang Đăng ký: `http://127.0.0.1:5000/register`.
  2. Điền: Họ tên `Trần Văn Test`, Số điện thoại `0905555444`, Mật khẩu `123456`. Bấm **"Đăng Ký Tài Khoản"**.
  3. Hệ thống đăng nhập và tự động đưa vào `/patient/complete-profile`.
  4. Thử bấm vào menu "Đặt lịch khám" hoặc "Bệnh án" khi chưa hoàn thiện hồ sơ.
  5. Thử nhập Họ tên chứa ký tự đặc biệt `<script>` hoặc SĐT 9 số -> Bị chặn báo lỗi định dạng ngay tại BackEnd.
  6. Điền thông tin hợp lệ:
     - Ngày sinh: `15/05/1995`
     - Giới tính: `Nam`
     - Số CCCD: `079095001234` (Đúng 12 chữ số)
     - Nhóm máu: `A+`
     - Tiền sử dị ứng: `Dị ứng thuốc Paracetamol`
     - Địa chỉ: `Quận 1, TP. Hồ Chí Minh`
     - Bấm **"Hoàn Tất Hồ Sơ"**.
  7. **Kết quả mong đợi**: Hệ thống cập nhật `da_hoan_thien_ho_so = 1`, đưa vào Cổng bệnh nhân với đầy đủ tính năng.

---

### KỊCH BẢN 3: Hồ sơ cá nhân nội bộ (`/admin/profile`)
- **Mục tiêu**: Kiểm tra phân hệ hồ sơ riêng dành cho nhân sự (Admin, Bác sĩ, Lễ tân, Dược sĩ, KTV).
- **Các bước thực hiện**:
  1. Đăng nhập bằng tài khoản Bác sĩ `bs_noi_1` (`Password@123`).
  2. Bấm vào ảnh đại diện/tên góc trên cùng bên phải -> Chọn **"Hồ sơ cá nhân"** (hoặc truy cập `/admin/profile`).
  3. Kiểm tra thông tin hiển thị:
     - Có đầy đủ họ tên, chức danh, khoa phòng, CCCD, ngày sinh, ngày vào làm, lần đăng nhập cuối.
     - Hoàn toàn **không hiển thị** các trường bệnh án cá nhân (như triệu chứng, tiền sử bệnh tật của bệnh nhân).
  4. Nhập cập nhật số điện thoại mới, email mới.
  5. Thử đổi mật khẩu: Nhập sai mật khẩu hiện tại -> Bị báo lỗi `"Mật khẩu hiện tại không chính xác"`.
  6. Nhập đúng mật khẩu hiện tại `Password@123` và mật khẩu mới `NewPass@123` -> Bấm **"Cập Nhật Hồ Sơ"**.
  7. **Kết quả mong đợi**: Thông báo cập nhật thành công; đăng xuất và đăng nhập lại bằng `NewPass@123` thành công.

---

### KỊCH BẢN 4: Phân quyền đăng ký ca trực và Điều phối khi hủy ca
- **Mục tiêu**: Kiểm tra Admin không trực, Lễ tân tự duyệt ngay, Bác sĩ/KTV chờ duyệt; giới hạn 3 BS/khoa/ca; và cơ chế điều phối lịch hẹn khi hủy ca trực.
- **Các bước thực hiện**:
  1. **Kiểm tra Admin**:
     - Đăng nhập `admin` (`admin123`), vào `/admin/schedules`.
     - Tài khoản Admin không xuất hiện trên danh sách nhân sự trực.
  2. **Kiểm tra Lễ tân tự duyệt**:
     - Đăng nhập Lễ tân `letan_1` (`Password@123`), vào `/admin/schedules`.
     - Bấm đăng ký 1 ca trực trong tuần tới.
     - **Kết quả mong đợi**: Ca trực được duyệt ngay lập tức (`Đã duyệt` màu xanh lá), không cần người khác duyệt và không gửi thông báo xin duyệt.
  3. **Kiểm tra Bác sĩ đăng ký và Giới hạn 3 BS**:
     - Đăng nhập Bác sĩ `bs_noi_1`, đăng ký ca sáng Thứ Hai tuần tới.
     - Ca trực hiển thị trạng thái `Chờ duyệt` (màu vàng cam).
     - Rê chuột vào ô lịch: Hiển thị tên đồng nghiệp đang trực cùng ca.
     - Nếu đã có 3 bác sĩ cùng khoa Nội đăng ký ca đó, bác sĩ thứ 4 bấm đăng ký sẽ nhận thông báo: `"Đã đủ số lượng tối đa 3 bác sĩ cùng chuyên khoa trong một ca trực!"`.
  4. **Kiểm tra Tiếp tân/Admin duyệt hàng loạt**:
     - Đăng nhập `admin` hoặc `letan_1`, mở danh sách ca trực chờ duyệt.
     - Tick chọn nhiều ca trực cùng lúc -> Bấm **"Duyệt các ca đã chọn"**.
     - Toàn bộ ca được chuyển sang `Đã duyệt` chỉ với 1 thông báo tổng hợp.
  5. **Kiểm tra điều phối khi hủy ca trực**:
     - Bác sĩ `bs_noi_1` có 1 lịch hẹn khám trong ca trực sắp tới.
     - Bác sĩ gửi yêu cầu hủy ca trực.
     - Tiếp tân/Admin duyệt đồng ý hủy ca trực.
     - **Kết quả mong đợi**: Lịch hẹn chưa khám của bác sĩ đó tự động được chuyển về trạng thái `Chờ tiếp nhận` (`bac_si_id = NULL`), đồng thời một thông báo xuất hiện nhắc Lễ tân phân bổ bác sĩ khác cho lịch hẹn đó.

---

### KỊCH BẢN 5: Đặt lịch trực tuyến, Chặn trùng giờ và Chặn đổi lịch đã xong
- **Mục tiêu**: Kiểm tra đồng bộ ca trực, kiểm tra trạng thái hoạt động bác sĩ, chống đặt trùng giờ và chặn đổi lịch hẹn không hợp lệ.
- **Các bước thực hiện**:
  1. Đăng nhập tài khoản Bệnh nhân `0901234561` (`123456`).
  2. Vào trang **"Đặt lịch khám"** (`/booking`).
  3. Chọn Chuyên khoa `Khoa Nội Tổng Quát`.
  4. Xem danh sách bác sĩ: Dưới tên bác sĩ có hàng trạng thái biểu hiện `🟢 Đang làm việc` hoặc `⚪ Ngoài giờ làm việc`.
  5. Chọn Ngày hẹn: Ngày mai, Khung giờ `08:30`. Chọn Bác sĩ và bấm **"Xác Nhận Đặt Lịch"** -> Đặt thành công (mã `LH...`).
  6. **Kiểm tra chống đặt trùng giờ**:
     - Vẫn là bệnh nhân đó, chọn tiếp một chuyên khoa khác (ví dụ: `Khoa Mắt`), chọn cùng Ngày mai và **cùng khung giờ `08:30`**.
     - Bấm xác nhận đặt lịch.
     - **Kết quả mong đợi**: Hệ thống từ chối và hiện thông báo: `"Bạn đã có lịch hẹn (...) vào lúc 08:30 ngày mai. Vui lòng chọn khung giờ khác!"`.
  7. **Kiểm tra chặn đổi lịch đã xong**:
     - Mở Cổng bệnh nhân -> Danh sách lịch khám.
     - Với lịch hẹn đã ở trạng thái `Đã khám` hoặc `Đã hủy`: Hệ thống ẩn nút "Đổi ngày hẹn" hoặc nếu cố tình gọi lệnh, hệ thống trả về lỗi `"Không thể đổi lịch hẹn đã ở trạng thái Đã khám / Đã hủy!"`.

---

### KỊCH BẢN 6: Khám EMR 2 giai đoạn, Đa ảnh 2x2 Lightbox và Cảnh báo dị ứng
- **Mục tiêu**: Kiểm tra trải nghiệm tải tối đa 10 ảnh, lưới 2x2 cuộn được, Lightbox phóng to, cảnh báo dị ứng thời gian thực và quy trình EMR 2 giai đoạn (chỉ định CLS -> KTV nhập kết quả -> Bác sĩ kết luận sau CLS).
- **Các bước thực hiện**:
  1. **Tiếp nhận bệnh nhân**:
     - Đăng nhập Lễ tân `letan_1` -> Danh sách chờ khám -> Bấm **"Tiếp nhận"** bệnh nhân `0901234561` (Trần Văn An, dị ứng Paracetamol) và phân bổ cho BS `bs_noi_1`.
  2. **Bác sĩ khám lâm sàng và Tải ảnh**:
     - Đăng nhập Bác sĩ `bs_noi_1` (`Password@123`) -> Vào `/admin/emr`.
     - Bệnh nhân vừa tiếp nhận xuất hiện ngay ở đầu danh sách chờ. Bấm chọn bệnh nhân.
     - Thẻ dị ứng ở đầu bệnh án đổi màu đỏ cảnh báo: `"Tiền sử dị ứng: Dị ứng thuốc Paracetamol"`.
     - **Kiểm tra tải ảnh lâm sàng**:
       + Tại Tab 1 (Khám lâm sàng), khu vực Dropzone: Kéo thả 3 file ảnh vết thương/lâm sàng vào khung (hoặc click chọn).
       + Khung dạng 2 cột ảnh 2x2 xem trước nhỏ xuất hiện, hiển thị `3 / 10 ảnh`, có thể cuộn chuột lên xuống.
       + Bấm vào ảnh bất kỳ -> Lightbox modal phóng to ảnh chuẩn HD. Bấm dấu X đóng modal.
       + Bấm nút X trên 1 ảnh -> Ảnh đó bị xóa khỏi danh sách xem trước (`còn 2 / 10 ảnh`).
     - **Kiểm tra cảnh báo dị ứng thời gian thực**:
       + Chuyển sang Tab 3 (Kê đơn thuốc).
       + Tại ô chọn thuốc: Chọn `Paracetamol 500mg`.
       + **Kết quả mong đợi**: Banner đỏ xuất hiện ngay lập tức: `"⚠️ CẢNH BÁO DỊ ỨNG THUỐC THỜI GIAN THỰC: Bệnh nhân có tiền sử dị ứng: Dị ứng thuốc Paracetamol. Thuốc Paracetamol có nguy cơ gây dị ứng phản vệ!"`.
       + Bấm **"Thêm Thuốc Này Vào Toa"** -> Trình duyệt bật hộp thoại xác nhận cảnh báo nguy cơ dị ứng. Bác sĩ bấm Cancel -> Thuốc không được thêm vào toa.
     - **Ra chỉ định Cận lâm sàng (Giai đoạn 1)**:
       + Chuyển sang Tab 2 (Chỉ định CLS) -> Tick chọn `Nội soi dạ dày tá tràng` và `Tổng phân tích tế bào máu`.
       + Bấm nút **"Hoàn Tất và Chuyển Phiên Khám"**.
       + **Kết quả mong đợi**: Phiếu khám được lưu ở trạng thái `Chờ kết quả CLS`. Bệnh nhân chỉ nhận thông báo in-app hướng dẫn đi làm CLS, **chưa nhận** thông báo hoàn tất khám.
  3. **KTV phòng Lab kiểm tra viện phí và trả kết quả**:
     - Đăng nhập KTV `ktv_1` (`Password@123`) -> Vào `/admin/lab`.
     - Phiếu chỉ định của bệnh nhân xuất hiện.
     - Cột Viện phí hiển thị badge: `Chưa đóng phí` (màu đỏ) hoặc `Đã đóng phí` (màu xanh).
     - Bấm nút **"Kết Quả"**:
       + Điền kết luận: `Niêm mạc dạ dày xung huyết nhẹ, không có vết loét`.
       + Kéo thả 2 ảnh nội soi vào Dropzone của KTV.
       + Ảnh hiển thị trên lưới 2x2 xem trước nhỏ, bấm vào để mở Lightbox kiểm tra ảnh.
       + Bấm **"Lưu Kết Quả"**.
  4. **Bác sĩ xem kết quả CLS và Chốt kết luận (Giai đoạn 2)**:
     - Quay lại tài khoản Bác sĩ `bs_noi_1` trên EMR.
     - Chọn bệnh nhân đang khám. Phía trên xuất hiện banner vàng: `"Phiếu khám PK... đang ở trạng thái Chờ kết quả CLS"`.
     - Bác sĩ bấm Tab 4 **"Xem Kết Quả CLS và Ảnh Chụp"**: Thấy kết luận của KTV và nút xem ảnh chụp chẩn đoán.
     - Bác sĩ bổ sung đơn thuốc an toàn (ví dụ: `Esomeprazole 20mg`), dặn dò tái khám.
     - Bác sĩ bấm nút **"Kết Luận và Hoàn Tất Ca Khám Sau CLS"**.
     - **Kết quả mong đợi**: Phiếu khám chuyển sang `Hoàn thành`, lịch hẹn chuyển sang `Đã khám`. Bệnh nhân nhận đồng thời thông báo hoàn tất khám và thông báo có đơn thuốc điện tử.
  5. **Kiểm tra ca khám bình thường 1 chạm**:
     - Chọn bệnh nhân khác không có bệnh lý -> Bác sĩ chỉ cần bấm nút **"Sức Khỏe Tốt (Xuất Hóa Đơn Ngay)"**.
     - Hệ thống hoàn tất khám và xuất hóa đơn viện phí tiền khám ngay lập tức.

---

### KỊCH BẢN 7: Chuẩn hóa quy trình cấp phát thuốc 3 bước
- **Mục tiêu**: Kiểm tra duyệt đơn không trừ kho, bệnh nhân thanh toán, Dược sĩ cấp phát thực tế mới trừ kho, và quyền hạn phân chia đúng chuẩn.
- **Các bước thực hiện**:
  1. **Bước 1: Bệnh nhân chọn nơi mua thuốc**:
     - Đăng nhập Bệnh nhân vừa được kê đơn thuốc.
     - Vào menu **"Đơn thuốc"** (`/patient/prescriptions`).
     - Đơn thuốc hiển thị với trạng thái `Chờ bệnh nhân xác nhận mua` và 2 nút lựa chọn:
       + Bấm thử nút **"Tự Mua Ngoài"**: Trạng thái chuyển thành `Mua ngoài`, không sinh hóa đơn và kết thúc luồng.
       + Bấm nút **"Mua Tại Bệnh Viện"**: Trạng thái chuyển thành `Chờ duyệt`, hệ thống sinh 1 hóa đơn tiền thuốc tạm thời mã `HDT...`.
       + Khi đang `Chờ duyệt`, bệnh nhân vẫn có quyền đổi ý bấm lại "Tự mua ngoài" (hệ thống sẽ tự hủy hóa đơn tạm `HDT...`).
  2. **Bước 2: Lễ tân / Admin duyệt đơn thuốc**:
     - Đăng nhập Lễ tân `letan_1` hoặc Admin `admin`.
     - Vào phân hệ duyệt đơn thuốc. Bấm **"Duyệt đơn thuốc"**.
     - **Kết quả mong đợi**:
       + Thông báo trả về: `"Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy"`.
       + Quay lại Cổng bệnh nhân: Nút chuyển sang "Mua ngoài" đã bị khóa/ẩn (không cho đổi nữa).
       + **Kiểm tra kho thuốc**: Mở kho dược kiểm tra số lượng tồn kho -> **Số lượng tồn kho hoàn toàn CHƯA BỊ TRỪ** (vì chưa cấp phát).
  3. **Bước 3: Bệnh nhân thanh toán hóa đơn thuốc**:
     - Bệnh nhân mở menu **"Hóa đơn và Viện phí"** (`/patient/invoices`).
     - Chọn hóa đơn thuốc `HDT...` -> Bấm thanh toán (chọn quét VietQR hoặc thanh toán tại quầy).
     - Hóa đơn chuyển trạng thái `Đã thanh toán`, cột trạng thái nhận thuốc ghi: `Chưa nhận thuốc`.
     - Đơn thuốc tự động chuyển sang trạng thái: `Chờ nhận thuốc`.
  4. **Bước 4: Dược sĩ cấp phát thuốc thực tế và Trừ kho**:
     - Đăng nhập Dược sĩ `duocsi_1` (`Password@123`) -> Vào `/admin/pharmacy`.
     - Dược sĩ thấy đơn thuốc của bệnh nhân đã được duyệt và đã thanh toán tiền.
     - Dược sĩ chuẩn bị thuốc thực tế, sau đó bấm nút **"Cấp Phát Thuốc"**.
     - **Kết quả mong đợi**:
       + **Lúc này hệ thống MỚI THỰC HIỆN TRỪ TỒN KHO** trong bảng `thuoc`.
       + Trạng thái đơn thuốc cập nhật thành: `Đã nhận thuốc`.
       + Hóa đơn viện phí của bệnh nhân cập nhật: `Đã nhận thuốc`.
       + Bệnh nhân nhận thông báo in-app: *"Bạn đã hoàn tất nhận thuốc tại quầy dược bệnh viện"*.
       + Thử bấm lại nút cấp phát lần nữa -> Bị từ chối vì đơn đã được cấp phát.
       + Tài khoản Tiếp tân/Admin không còn hiển thị nút cấp phát thuốc này nữa.

---

### KỊCH BẢN 8: Cấn trừ BHYT và Nhận diện hóa đơn thuốc `HDT`
- **Mục tiêu**: Kiểm tra khấu trừ BHYT 80% tiền khám + CLS, và nhận diện chính xác hóa đơn thuốc.
- **Các bước thực hiện**:
  1. Kiểm tra 2 bệnh nhân khám cùng 1 dịch vụ khám 150.000đ:
     - Bệnh nhân có thẻ BHYT (`0901234561`): Tiền khám được cấn trừ 80% (120.000đ), bệnh nhân chỉ cần thanh toán **30.000đ**.
     - Bệnh nhân không có thẻ BHYT (`0901234562`): BHYT chi trả 0đ, bệnh nhân thanh toán đủ **150.000đ**.
  2. Khi hủy 1 lịch hẹn khám chưa thanh toán: Hóa đơn tiền khám `HDK...` liên quan tự động chuyển sang `Đã hủy`, không để lại nợ ảo.
  3. Kiểm tra hóa đơn thuốc: Mã luôn bắt đầu bằng `HDT...`, chỉ hiển thị tổng tiền thuốc cần đóng, không để lộ giá lẻ từng viên.

---

### KỊCH BẢN 9: Kiểm tra hệ thống thông báo tức thì (In-app Notification Dropdown)
- **Mục tiêu**: Kiểm tra chuông thông báo hiển thị đúng các mốc sự kiện quan trọng.
- **Các bước thực hiện**:
  1. Bấm vào biểu tượng quả chuông thông báo ở góc trên bên phải thanh Header.
  2. Kiểm tra danh sách thả xuống (Notification Dropdown):
     - Thông báo mới có chấm đỏ và hiển thị nội dung tóm tắt.
     - Lễ tân/Admin: Nhận thông báo khi bệnh nhân đặt lịch, nhân viên đăng ký ca trực, bác sĩ xin hủy ca.
     - Bác sĩ: Nhận thông báo khi lịch hẹn được tiếp nhận, ca trực được duyệt.
     - Bệnh nhân: Nhận thông báo lịch hẹn xác nhận/hủy, thông báo đi làm CLS, thông báo kết thúc khám, thông báo hóa đơn viện phí.
  3. Bấm vào một thông báo: Tự động đánh dấu đã đọc và chuyển hướng đến trang chi tiết tương ứng.

---

### KỊCH BẢN 10: Sao lưu và Khôi phục Microsoft SQL Server (.bak)
- **Mục tiêu**: Kiểm tra an toàn dữ liệu cơ sở dữ liệu.
- **Các bước thực hiện**:
  1. Đăng nhập Admin (`admin` / `admin123`).
  2. Vào menu **"Sao lưu CSDL"** (`/admin/backups`).
  3. Bấm **"Tạo Bản Sao Lưu Mới"**: Hệ thống thực thi lệnh T-SQL `BACKUP DATABASE` và sinh file `.bak` trong thư mục `backups/`.
  4. Bảng danh sách hiển thị tên file, dung lượng và thời gian tạo chính xác.
  5. Bấm tải về file `.bak` hoặc bấm **"Khôi phục"**: Hệ thống tự động chuyển database về `SINGLE_USER`, khôi phục bản ghi và mở lại `MULTI_USER` an toàn.

---

---

### KỊCH BẢN 11: Kiểm tra Giao diện Dark Mode (Chế độ Tối)
- **Mục tiêu**: Kiểm tra tính năng chuyển đổi chế độ Sáng / Tối trên toàn bộ các cổng hệ thống.
- **Các bước thực hiện**:
  1. Mở bất kỳ trang nào (Trang chủ `/`, Cổng bệnh nhân `/patient/dashboard`, Cổng quản trị `/admin/dashboard`, Trang đăng nhập `/login`).
  2. Quan sát nút biểu tượng Mặt trăng / Mặt trời trên thanh Header (hoặc góc trên bên phải trang đăng nhập).
  3. Bấm vào nút: Hệ thống chuyển sang giao diện tối dịu mắt ngay lập tức, biểu tượng đổi thành Mặt trời.
  4. Tải lại trang (F5): Giao diện vẫn duy trì màu tối mượt mà (không bị chớp trắng) nhờ lưu trạng thái vào `localStorage`.
  5. Bấm lại lần nữa: Hệ thống chuyển lại về giao diện sáng.

---

### KỊCH BẢN 12: Kiểm tra Phân quyền Quản lý Bài viết và Cẩm nang Y tế
- **Mục tiêu**: Đảm bảo chỉ có Tiếp tân và Admin được quyền tạo, sửa, xóa bài viết; toàn bộ vai trò còn lại chỉ được xem.
- **Các bước thực hiện**:
  1. **Kiểm tra vai trò Quản lý (Admin / Tiếp tân)**:
     - Đăng nhập bằng `admin` (`admin123`) hoặc `letan_1` (`Password@123`).
     - Vào menu **"Quản lý Bài viết"** (`/admin/articles`).
     - Thấy nút **"Viết và Đăng Bài Mới"**, các nút **"File Mẫu"**, **"Nhập CSV"**.
     - Cột thao tác của từng bài viết có đủ các nút: **"Xem"**, **"Sửa"**, **"Xóa"**.
     - Bấm thử sửa / tạo bài viết mới -> Thao tác thành công.
  2. **Kiểm tra các vai trò chỉ đọc (Bác sĩ, Dược sĩ, Kỹ thuật viên)**:
     - Đăng nhập bằng `bs_noi_1` hoặc `duocsi_1` hoặc `ktv_1` (`Password@123`).
     - Vào menu **"Quản lý Bài viết"** (`/admin/articles`).
     - Danh sách bài viết vẫn hiển thị đầy đủ, tìm kiếm và lọc danh mục hoạt động bình thường.
     - **Hoàn toàn KHÔNG hiển thị** nút *"Viết và Đăng Bài Mới"*, *"File Mẫu"*, *"Nhập CSV"*.
     - Cột thao tác chỉ có nút **"Xem"** (mở xem chi tiết bài viết), không có nút *"Sửa"* và *"Xóa"*.
     - Thử nhập trực tiếp đường dẫn `/admin/articles/create` hoặc `/admin/articles/edit/1` trên thanh địa chỉ -> Bị hệ thống chặn và chuyển hướng kèm thông báo cảnh báo quyền hạn.
  3. **Kiểm tra Cổng bệnh nhân và Khách vãng lai**:
     - Truy cập `/articles` và click vào bài viết `/articles/<slug>`.
     - Toàn bộ nội dung bài viết hiển thị chuẩn xác, đẹp mắt.

---

## PHẦN III: DANH SÁCH TÀI KHOẢN PHỤC VỤ TEST THỦ CÔNG

| Vai trò | Username | Password | Chuyên khoa / Ghi chú |
| :--- | :--- | :--- | :--- |
| **Quản trị viên** | `admin` | `admin123` | Toàn quyền cấu hình, tạo bác sĩ mới, duyệt ca trực |
| **Lễ tân** | `letan_1` | `Password@123` | Tiếp đón, phân bổ bác sĩ, tự duyệt ca trực, duyệt đơn thuốc |
| **Bác sĩ Nội** | `bs_noi_1` | `Password@123` | Khám EMR 2 giai đoạn, tải tối đa 10 ảnh, cảnh báo dị ứng |
| **Bác sĩ Ngoại** | `bs_ngoai_1` | `Password@123` | Khám ngoại khoa tổng quát |
| **Bác sĩ Nhi** | `bs_nhi_1` | `Password@123` | Khám nhi khoa |
| **Kỹ thuật viên** | `ktv_1` | `Password@123` | Kiểm tra phí CLS, trả kết quả và tải tối đa 10 ảnh |
| **Dược sĩ** | `duocsi_1` | `Password@123` | Kiểm tra đơn đã thanh toán, cấp phát thực tế trừ kho |
| **Bệnh nhân 1** | `0901234561` | `123456` | Có BHYT, dị ứng Paracetamol |
| **Bệnh nhân 2** | `0901234562` | `123456` | Không BHYT, dị ứng Penicillin |
