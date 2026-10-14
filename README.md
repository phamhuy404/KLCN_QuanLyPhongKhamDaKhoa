<<<<<<< Updated upstream
# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-SQLite%20%7C%20SQL%20Server%20%7C%20MySQL-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20JS-teal.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo chuẩn kiến trúc MVC (Model - View - Controller), số hóa quy trình y tế từ tiếp đón bệnh nhân, bệnh án điện tử EMR 360°, cận lâm sàng & xét nghiệm, quản lý kho dược đến viện phí và cổng thông tin người bệnh.

## Cấu Trúc Dự Án (Project Structure)

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                     # Entrypoint: Khởi chạy chính ứng dụng Flask
├── config.py                  # Cấu hình tập trung & chuyển đổi 3 loại CSDL
├── cosodulieu.sql             # Kịch bản tạo CSDL Microsoft SQL Server
├── cosodulieu_mysql.sql       # Kịch bản tạo CSDL MySQL / MariaDB
├── phongkham.db               # File CSDL SQLite (chạy ngay, không cần cài server)
├── huongdanchay.txt           # Cẩm nang chi tiết cài đặt, sitemap & hướng dẫn sửa code
├── requirements.txt           # Danh sách thư viện Python phụ thuộc
│
├── controllers/               # [CONTROLLER] Xử lý nghiệp vụ, phân quyền & điều hướng URL
│   ├── auth_controller.py     #   - Xác thực: Đăng nhập, đăng ký, đăng xuất, kiểm tra phiên
│   ├── home_controller.py     #   - Công khai: Trang chủ, đặt lịch online, cẩm nang bài viết
│   ├── patient_controller.py  #   - Bệnh nhân: Xem hồ sơ, đợt khám, đơn thuốc, xét nghiệm
│   ├── admin_controller.py    #   - Quản trị: EMR, tiếp nhận, viện phí, kho dược, báo cáo
│   └── api_controller.py      #   - API RESTful: Xử lý nhanh AJAX/Fetch thời gian thực
│
├── models/                    # [MODEL] Tương tác CSDL, truy vấn & ràng buộc dữ liệu
│   ├── user_model.py          #   - Tài khoản, phân quyền vai trò (Admin, Bác sĩ, Bệnh nhân)
│   ├── patient_model.py       #   - Hồ sơ bệnh nhân 360°, tiền sử, diễn biến đợt khám
│   ├── appointment_model.py   #   - Quản lý lịch hẹn khám bệnh
│   ├── article_model.py       #   - Tin tức y khoa & tìm kiếm gần đúng tiếng Việt
│   ├── inventory_model.py     #   - Danh mục dược phẩm, quản lý xuất nhập tồn
│   └── medical_service_model.py # - Bảng giá dịch vụ khám và kỹ thuật cận lâm sàng
│
├── templates/                 # [VIEW] Giao diện người dùng Jinja2 HTML
│   ├── layouts/               #   - Khung giao diện dùng chung (base.html, footer.html)
│   ├── admin/                 #   - Giao diện các phân hệ quản trị, EMR và phòng khám
│   ├── patient/               #   - Giao diện cổng thông tin người bệnh
│   ├── articles.html          #   - Chuyên trang cẩm nang y tế & live fuzzy search
│   └── home.html              #   - Trang chủ giới thiệu dịch vụ phòng khám
│
├── static/                    # Tài nguyên tĩnh Frontend
│   ├── js/main.js             #   - Bộ máy tìm kiếm gần đúng (Fuzzy Search), Tag Selector
│   ├── css/custom.css         #   - Các lớp CSS tùy biến bổ sung
│   └── img/                   #   - Hình ảnh bài viết, icon chuyên khoa, banner
│
├── data/                      # Dữ liệu danh mục y tế chuẩn hóa
│   └── catalogs/              #   - Các tệp text thuần (nhóm máu, dị ứng, bệnh lý nền)
│
└── core/                      # Tầng cốt lõi hệ thống
    ├── database.py            #   - Unified Database Layer (kết nối đa CSDL & auto-migration)
    └── catalog.py             #   - Trình nạp danh mục y tế từ file text
```

## Các Tính Năng Nổi Bật

1. **Hỗ trợ 3 Loại Cơ Sở Dữ Liệu Linh Hoạt**:
   - Dễ dàng chuyển đổi giữa **SQLite** (chạy ngay không cần cài đặt), **Microsoft SQL Server** (SSMS), và **MySQL / MariaDB** (XAMPP / Docker) chỉ bằng 1 biến `DB_ENGINE` trong `config.py`.
   - Cơ chế tự động kiểm tra và di trú cột dữ liệu (Auto Migration) đảm bảo tính tương thích tuyệt đối.

2. **Bộ Máy Tìm Kiếm Gần Đúng Thông Minh (Fuzzy Search Engine)**:
   - Tích hợp trên toàn bộ các ô tìm kiếm trong hệ thống (Hồ sơ bệnh nhân, Lịch hẹn, Kho dược, Viện phí, Xét nghiệm, Lịch sử bệnh án, Cẩm nang bài viết).
   - Hỗ trợ gõ tiếng Việt không dấu (`hoang nam` -> `Hoàng Bảo Nam`), gõ đảo thứ tự từ (`Nam Hoang` -> `Hoàng Bảo Nam`), gõ viết tắt chữ cái đầu (`hbn` -> `Hoàng Bảo Nam`, `ct` -> `Chụp CT Scanner`), và cho phép sai chính tả 1-2 ký tự (`paracetamon` -> `Paracetamol`, `penicilin` -> `Penicillin`).

3. **Chuẩn Hóa Dữ Liệu Y Tế (Catalog System)**:
   - Nhóm máu chuẩn hóa theo 8 nhóm ABO/Rh (`O+`, `O-`, `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `Chưa rõ`) kết hợp trường ghi chú biến thể chuyên sâu (Weak D, Bombay, Kháng thể bất thường).
   - Dị ứng thuốc và bệnh lý nền sử dụng bộ chọn thẻ tương tác cao (Tag Selector), cho phép thêm bớt danh mục dễ dàng bằng các file text thuần trong `data/catalogs/` mà không cần chỉnh sửa mã nguồn.

4. **Số Hóa Quy Trình Bệnh Án Điện Tử (EMR 360°)**:
   - Quầy tiếp nhận cấp số thứ tự 1 chạm và phân luồng phòng khám chuyên khoa.
   - Bác sĩ thăm khám lâm sàng, đo sinh hiệu (mạch, huyết áp, nhiệt độ, SpO2), chẩn đoán mã ICD-10, chỉ định cận lâm sàng và kê đơn thuốc điện tử liên thông trực tiếp với quầy phát thuốc.

## Cài Đặt & Khởi Chạy Nhanh

### Bước 1: Cài đặt thư viện phụ thuộc
Mở terminal tại thư mục dự án và chạy:
```bash
pip install -r requirements.txt
```

### Bước 2: Lựa chọn Cơ sở dữ liệu trong `config.py`
Mở file `config.py` và thiết lập biến `DB_ENGINE`:
- **Cách 1: SQLite (Mặc định - Khuyên dùng khi bắt đầu)**
  ```python
  DB_ENGINE = 'sqlite'
  ```
  Hệ thống tự động sử dụng file `phongkham.db` có sẵn. Không cần cài đặt bất kỳ server CSDL nào.

- **Cách 2: Microsoft SQL Server**
  Chạy file `cosodulieu.sql` trong SSMS, sau đó đặt `DB_ENGINE = 'sqlserver'`.

- **Cách 3: MySQL / MariaDB**
  Nhập file `cosodulieu_mysql.sql` vào MySQL (XAMPP / phpMyAdmin), sau đó đặt `DB_ENGINE = 'mysql'`.

### Bước 3: Khởi chạy ứng dụng
```bash
python app.py
```
Mở trình duyệt web truy cập: `http://127.0.0.1:5000`

## Tài Khoản Đăng Nhập Thử Nghiệm

Cơ sở dữ liệu được làm sạch 100% dữ liệu giao dịch để người dùng trải nghiệm thực tế quy trình khám bệnh:

| Vai trò | Tên đăng nhập | Mật khẩu | Phạm vi quyền hạn |
| :--- | :--- | :--- | :--- |
| **Quản trị viên & Bác sĩ** | `admin` | `admin123` | Toàn quyền quản trị phòng khám, khám bệnh EMR, xét nghiệm, kho dược, viện phí, báo cáo |
| **Bệnh nhân mẫu** | `0901234567` | `123456` | Cổng bệnh nhân, đặt lịch khám online, tra cứu hồ sơ 360°, xem toa thuốc và kết quả xét nghiệm |

## Công Nghệ Sử Dụng (Tech Stack)

- **Backend**: Python 3.10+, Flask 3.0+ (Blueprint MVC Architecture).
- **Database**: SQLite3, Microsoft SQL Server (pyodbc), MySQL/MariaDB (PyMySQL).
- **Frontend**: HTML5, Tailwind CSS, FontAwesome 6, JavaScript ES6+ (Native DOM & Fetch API).
- **Algorithms**: Levenshtein Distance, Vietnamese Tone Stripping, Multi-token Fuzzy Matcher.
