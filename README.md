# KLCN_QuanLyPhongKhamDaKhoa
# Quản lý Phòng khám Đa khoa H2T Healthcare

**Hệ thống Quản lý Bệnh viện/Phòng khám Đa khoa trực tuyến**

Đây là một ứng dụng Web được xây dựng với Flask (Python) và sử dụng SQL Server làm hệ quản trị cơ sở dữ liệu. Hệ thống được thiết kế nhằm số hóa toàn bộ quy trình quản lý hoạt động của một phòng khám đa khoa, từ tiếp đón bệnh nhân, đặt lịch hẹn, quản lý hồ sơ bệnh án điện tử (EMR), đến quản lý dược phẩm, thanh toán và thống kê báo cáo.

## 📋 Mục lục

- [Tính năng](#--tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt & Cấu hình](#--cài-đặt--cấu-hình)
- [Cách sử dụng](#-cách-sử-dụng)
- [Cơ sở dữ liệu](#-cơ-sở-dữ-liệu)

---

## 📋 Tính năng

Hệ thống cung cấp các phân hệ và tính năng toàn diện cho các đối tượng người dùng khác nhau:

### 1. Quản lý Người dùng (RBAC)
- **Quản trị viên (Admin):** Quản lý tài khoản, phân quyền, xem báo cáo toàn hệ thống.
- **Bác sĩ (Doctor):** Quản lý lịch khám, xem hồ sơ bệnh án, chỉ định điều trị, kê đơn thuốc.
- **Nhân viên Lễ tân (Receptionist):** Tiếp đón bệnh nhân, đặt lịch hẹn, tra cứu thông tin.
- **Bệnh nhân (Patient):** Đặt lịch hẹn online, xem lịch sử khám, thông tin cá nhân, theo dõi đơn thuốc.

### 2. Quản lý Tiếp đón & Lịch hẹn
- **Đặt lịch hẹn trực tuyến:** Bệnh nhân có thể tìm kiếm bác sĩ và đặt lịch theo khung giờ trống.
- **Quản lý luồng bệnh nhân:** Cập nhật trạng thái (Chờ khám, Đang khám, Hoàn tất).
- **Check-in/Check-out:** Xác nhận bệnh nhân đến khám và kết thúc điều trị.

### 3. Hồ sơ Bệnh án Điện tử (EMR)
- **Hồ sơ y tế:** Lưu trữ thông tin cá nhân, tiền sử bệnh lý, dị ứng.
- **Phiếu khám bệnh:** Ghi nhận triệu chứng, chẩn đoán, kết quả cận lâm sàng.
- **Dấu hiệu sinh tồn:** Theo dõi huyết áp, nhịp tim, nhiệt độ, SpO2.

### 4. Quản lý Điều trị & Dược phẩm
- **Chi định cận lâm sàng:** Gửi yêu cầu xét nghiệm, chẩn đoán hình ảnh.
- **Đơn thuốc:** Kê đơn thuốc online, chỉ định liều lượng, cách dùng.
- **Quản lý kho thuốc:** Theo dõi số lượng tồn kho, cảnh báo sắp hết, nhập xuất.

### 5. Thanh toán & Hóa đơn
- **Tự động tính toán:** Tính tổng chi phí dựa trên dịch vụ và thuốc.
- **Hỗ trợ Bảo hiểm Y tế (BHYT):** Tính toán chi phí bệnh nhân chi trả và quỹ BHYT.
- **In hóa đơn:** Tạo hóa đơn PDF chi tiết.

### 6. Thông tin & Giao tiếp
- **Bài viết y tế:** Admin có thể đăng tải tin tức, bài viết sức khỏe.
- **Góp ý & Phản hồi:** Bệnh nhân gửi góp ý, admin trả lời qua hệ thống.