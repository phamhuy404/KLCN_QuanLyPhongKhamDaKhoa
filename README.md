# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare (Kiến Trúc MVC)

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa, số hóa toàn bộ quy trình từ tiếp đón, khám bệnh điện tử (EMR), cận lâm sàng, dược phẩm, thu ngân viện phí đến cổng thông tin người bệnh.

## 1. Kiến Trúc Dự Án (Model - View - Controller)

Dự án được tái cấu trúc hoàn toàn theo mô hình MVC tiêu chuẩn:
- **Model (`models/`):** Xử lý nghiệp vụ và truy vấn CSDL độc lập với Controller.
  - `user_model.py`: Xác thực, phân quyền RBAC, quản lý tài khoản và nhân sự.
  - `patient_model.py`: Hồ sơ bệnh nhân 360, sinh hiệu, lịch sử khám bệnh.
  - `appointment_model.py`: Đặt lịch khám, phân luồng tiếp nhận, cập nhật trạng thái.
  - `medical_record_model.py`: Bệnh án điện tử EMR, chỉ định cận lâm sàng, kê toa thuốc.
  - `pharmacy_model.py`: Kho dược phẩm, xuất nhập tồn, phát thuốc tự động trừ kho.
  - `billing_model.py`: Hóa đơn viện phí, khấu trừ BHYT, thanh toán VietQR / tiền mặt.
  - `clinic_model.py`: Danh mục chuyên khoa, phòng khám, dịch vụ kỹ thuật.
  - `article_model.py`: Tin tức y khoa, bài viết sức khỏe.
- **View (`templates/` & `static/`):** Giao diện người dùng HTML5, Tailwind CSS, FontAwesome, JavaScript tương tác cao.
- **Controller (`controllers/`):** Điều phối luồng request, xử lý nghiệp vụ thông qua Flask Blueprints:
  - `home_controller.py`: Trang chủ và tin tức y khoa.
  - `auth_controller.py`: Đăng nhập, đăng ký, đăng xuất.
  - `patient_controller.py`: Cổng thông tin cá nhân bệnh nhân.
  - `admin_controller.py`: Bảng điều khiển quản trị y tế và các phân hệ lâm sàng.
  - `api_controller.py`: RESTful API phục vụ các tác vụ AJAX/Fetch thời gian thực.
- **Core & Config (`core/`, `config.py`):**
  - `config.py`: Cấu hình tập trung (môi trường, Secret Key, kết nối 3 loại CSDL).
  - `core/database.py`: Unified Database Layer tự động chuẩn hóa cursor và cú pháp giữa SQLite, SQL Server và MySQL.
  - `core/security.py`: Mã hóa mật khẩu bảo mật, Decorator kiểm tra quyền đăng nhập `@login_required` và phân quyền `@roles_required`.

## 2. Cài Đặt Môi Trường

Yêu cầu: Python 3.10 trở lên.
Cài đặt các gói phụ thuộc:
```bash
pip install -r requirements.txt
```

## 3. Cấu Hình Cơ Sở Dữ Liệu

Tùy chỉnh biến `DB_ENGINE` trong file `config.py` để lựa chọn 1 trong 3 cơ chế CSDL:

### Cách 1: SQLite (Mặc định - Chạy ngay)
- Trong `config.py`: `DB_ENGINE = 'sqlite'`
- Sử dụng trực tiếp file CSDL `phongkham.db` đã được khởi tạo sẵn với schema và dữ liệu sạch.

### Cách 2: Microsoft SQL Server
- Mở SQL Server Management Studio (SSMS).
- Mở file `cosodulieu.sql` và nhấn Execute (F5) để khởi tạo CSDL `quan_ly_phong_kham`.
- Trong `config.py`: `DB_ENGINE = 'sqlserver'`

### Cách 3: MySQL / MariaDB
- Khởi động MySQL (XAMPP / Docker).
- Nhập file `cosodulieu_mysql.sql` vào MySQL:
```bash
mysql -u root < cosodulieu_mysql.sql
```
- Trong `config.py`: `DB_ENGINE = 'mysql'`

## 4. Khởi Chạy Ứng Dụng

Chạy lệnh:
```bash
python app.py
```
Truy cập website tại: `http://127.0.0.1:5000`

## 5. Tài Khoản Thử Nghiệm

Cơ sở dữ liệu được làm sạch 100% các bảng giao dịch (khám bệnh, đơn thuốc, lịch hẹn, viện phí) để người dùng tự do tạo mới:
- **Quản trị viên (Admin):** `admin` / `admin123`
- **Bệnh nhân mẫu:** `0901234567` / `123456`