# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-SQLite%20%7C%20SQL%20Server%20%7C%20MySQL-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20JS-teal.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo chuẩn kiến trúc MVC (Model - View - Controller), số hóa quy trình y tế từ tiếp đón bệnh nhân, phân công bác sĩ, bệnh án điện tử EMR 360°, cận lâm sàng & xét nghiệm, quản lý kho dược, banner trang chủ đến viện phí và cổng thông tin người bệnh.

## Cấu Trúc Dự Án (Project Structure)

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Entrypoint: Khởi chạy chính ứng dụng Flask
├── config.py                      # Cấu hình tập trung & chuyển đổi 3 loại CSDL
├── cosodulieu.sql                 # Kịch bản tạo CSDL Microsoft SQL Server
├── cosodulieu_mysql.sql           # Kịch bản tạo CSDL MySQL / MariaDB
├── phongkham.db                   # File CSDL SQLite (chạy ngay, không cần cài server)
├── huongdanchay.txt               # Cẩm nang chi tiết cài đặt, sitemap & hướng dẫn sửa code
├── requirements.txt               # Danh sách thư viện Python phụ thuộc (Flask, PyODBC, PyMySQL, Pillow)
│
├── controllers/                   # [CONTROLLER] Xử lý nghiệp vụ, phân quyền & điều hướng URL
│   ├── auth_controller.py         #   - Xác thực: Đăng nhập, đăng ký, đăng xuất, kiểm tra phiên
│   ├── home_controller.py         #   - Công khai: Trang chủ (slider động), đặt lịch online, bài viết
│   ├── patient_controller.py      #   - Bệnh nhân: Xem hồ sơ, đợt khám, đơn thuốc, xét nghiệm
│   ├── admin_controller.py        #   - Quản trị: Banner, Bác sĩ, EMR, tài khoản, bài viết, viện phí
│   └── api_controller.py          #   - API RESTful: Xử lý nhanh AJAX/Fetch thời gian thực
│
├── models/                        # [MODEL] Tương tác CSDL, truy vấn & ràng buộc dữ liệu
│   ├── banner_model.py            #   - Quản lý các banner quảng bá slider trang chủ
│   ├── user_model.py              #   - Tài khoản, bác sĩ, nhân viên, phân quyền vai trò
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, tiền sử, diễn biến đợt khám
│   ├── appointment_model.py       #   - Quản lý lịch hẹn khám bệnh
│   ├── article_model.py           #   - Tin tức y khoa & tìm kiếm gần đúng tiếng Việt
│   ├── inventory_model.py         #   - Danh mục dược phẩm, quản lý xuất nhập tồn
│   ├── medical_service_model.py   #   - Bảng giá dịch vụ khám và kỹ thuật cận lâm sàng
│   ├── schedule_model.py          #   - Quản lý ca trực và lịch làm việc của bác sĩ
│   ├── notification_model.py      #   - Thông báo hệ thống và cảnh báo người dùng
│   ├── feedback_model.py          #   - Đánh giá và phản hồi của bệnh nhân
│   └── backup_model.py            #   - Quản lý sao lưu dữ liệu hệ thống
│
├── templates/                     # [VIEW] Giao diện người dùng Jinja2 HTML
│   ├── layouts/                   #   - Khung giao diện dùng chung (base.html, footer.html)
│   ├── admin/                     #   - Phân hệ quản trị (banner, bác sĩ, tài khoản, EMR, kho...)
│   │   ├── components/            #     - Header, sidebar, widget dùng chung
│   │   ├── banners.html           #     - Quản lý banner slider trang chủ (CRUD & toggle)
│   │   ├── doctors.html           #     - Danh sách bác sĩ phòng khám
│   │   ├── doctor_detail.html     #     - Hồ sơ bác sĩ 360°, bệnh nhân đăng ký & ca trực
│   │   ├── accounts.html          #     - Quản lý tài khoản, trạng thái & reset mật khẩu
│   │   ├── articles.html          #     - Danh sách bài viết cẩm nang y tế (CMS)
│   │   └── article_editor.html    #     - Trình soạn thảo bài viết mới / chỉnh sửa
│   ├── patient/                   #   - Giao diện cổng thông tin người bệnh
│   ├── articles.html              #   - Chuyên trang cẩm nang y tế công khai & fuzzy search
│   └── home.html                  #   - Trang chủ giới thiệu dịch vụ phòng khám
│
├── static/                        # Tài nguyên tĩnh Frontend
│   ├── uploads/                   #   - Ảnh tải lên phân tầng (tự động nén WebP, loại trừ khỏi Git)
│   │   ├── benh_nhan/             #     - Ảnh đại diện, thẻ BHYT bệnh nhân
│   │   ├── bac_si/                #     - Ảnh chân dung bác sĩ
│   │   ├── bai_viet/              #     - Ảnh bìa cẩm nang y tế
│   │   └── banners/               #     - Ảnh slider trang chủ
│   ├── js/main.js                 #   - Bộ máy tìm kiếm gần đúng (Fuzzy Search), Tag Selector, Toast
│   ├── css/custom.css             #   - Các lớp CSS tùy biến bổ sung
│   └── img/                       #   - Hình ảnh bài viết, icon chuyên khoa, banner mặc định
│
├── data/catalogs/                 # Dữ liệu danh mục y tế chuẩn hóa (text thuần)
│   ├── nhom_mau.txt               #   - 8 nhóm máu cơ bản + Chưa rõ
│   ├── bien_the_nhom_mau.txt      #   - Biến thể nhóm máu & kháng thể bất thường
│   ├── di_ung.txt                 #   - Dị ứng thuốc, thực phẩm
│   └── tien_su_benh.txt           #   - Tiền sử bệnh lý nền mạn tính
│
├── tests/                         # Bộ kiểm thử tự động (Automated Tests)
│   ├── test_system_features.py    #   - 11 test case các phân hệ lõi
│   └── test_features_6_to_10.py   #   - 8 test case quản lý bác sĩ, banner, bài viết, sao lưu
│
└── core/                          # Tầng cốt lõi hệ thống
    ├── image_service.py           #   - Tự động nén WebP (Pillow), resize, chống phình Git
    ├── database.py                #   - Unified Database Layer (kết nối đa CSDL & auto-migration)
    ├── catalog.py                 #   - Trình nạp danh mục y tế từ file text
    ├── security.py               #   - Mã hóa mật khẩu và token bảo mật
    ├── audit.py                  #   - Ghi nhật ký hoạt động hệ thống (Audit Log)
    └── notification_service.py   #   - Quản lý thông báo người dùng
```

## Các Tính Năng Nổi Bật

1. **Hỗ Trợ 3 Loại Cơ Sở Dữ Liệu Linh Hoạt**:
   - Dễ dàng chuyển đổi giữa **SQLite** (chạy ngay không cần cài đặt), **Microsoft SQL Server** (SSMS), và **MySQL / MariaDB** (XAMPP / Docker) chỉ bằng 1 biến `DB_ENGINE` trong `config.py`.
   - Cơ chế tự động kiểm tra và di trú cột dữ liệu (Auto Migration) cùng dự phòng kết nối (Auto-fallback) đảm bảo ứng dụng luôn chạy thông suốt.

2. **Quản Lý Bác Sĩ & Hồ Sơ Chuyên Sâu 360°**:
   - Danh sách bác sĩ trực quan kèm thông tin chuyên khoa, học vị, phòng khám, số điện thoại và giá khám.
   - Hồ sơ bác sĩ 360° hiển thị 3 tab nghiệp vụ: Bệnh nhân đăng ký khám trực tuyến, Lịch làm việc 14 ngày tới và Lịch sử khám bệnh EMR.
   - Cơ chế bảo mật phân quyền: Bác sĩ chỉ truy cập được hồ sơ và danh sách bệnh nhân của chính mình.

3. **Quản Lý Banner Trang Chủ & Tự Động Nén WebP**:
   - Quản trị viên tùy chỉnh các slide quảng bá trang chủ tại `/admin/banners`: Thứ tự hiển thị, tiêu đề, mô tả, nút bấm kêu gọi hành động (CTA) và hình ảnh.
   - Module `core/image_service.py` tự động nén ảnh sang định dạng WebP siêu nhẹ (< 80KB), phân tách rõ 4 thư mục lưu trữ (`benh_nhan`, `bac_si`, `bai_viet`, `banners`) và loại trừ khỏi Git để giữ dự án luôn gọn nhẹ.

4. **Quản Trị Tài Khoản & Phân Quyền An Toàn**:
   - Quản lý toàn bộ tài khoản người dùng (Admin, Bác sĩ, Bệnh nhân).
   - Cho phép kích hoạt/khóa tài khoản tức thì và đặt lại mật khẩu an toàn theo quy chuẩn bảo mật.

5. **Bộ Máy Tìm Kiếm Gần Đúng Thông Minh (Fuzzy Search Engine)**:
   - Tích hợp trên toàn bộ các ô tìm kiếm trong hệ thống (Hồ sơ bệnh nhân, Danh sách bác sĩ, Tài khoản, Lịch hẹn, Kho dược, Viện phí, Xét nghiệm, Bài viết).
   - Hỗ trợ gõ tiếng Việt không dấu, gõ đảo thứ tự từ, gõ viết tắt chữ cái đầu, và tự sửa sai chính tả 1-2 ký tự (Levenshtein Distance).

6. **Chuẩn Hóa Dữ Liệu Y Tế (Catalog System)**:
   - Nhóm máu chuẩn hóa theo 8 nhóm ABO/Rh (`O+`, `O-`, `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `Chưa rõ`) kết hợp ghi chú biến thể chuyên sâu (Weak D, Bombay, Kháng thể bất thường).
   - Dị ứng thuốc và bệnh lý nền sử dụng bộ chọn thẻ tương tác cao (Tag Selector), cấu hình dễ dàng bằng file text thuần trong `data/catalogs/`.

7. **Bệnh Án Điện Tử (EMR 360°) & Quy Trình Khám Khép Kín**:
   - Tiếp nhận cấp số một chạm, phân luồng phòng khám.
   - Bác sĩ thăm khám lâm sàng, đo sinh hiệu, chẩn đoán ICD-10, chỉ định cận lâm sàng và kê đơn thuốc điện tử liên thông quầy dược và viện phí.

## Cài Đặt & Khởi Chạy Nhanh

### Bước 1: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 2: Lựa chọn Cơ sở dữ liệu trong `config.py`
- **Cách 1: SQLite (Mặc định - Khuyên dùng khi bắt đầu)**
  ```python
  DB_ENGINE = 'sqlite'
  ```
  Hệ thống tự động sử dụng file `phongkham.db` có sẵn. Không cần cài đặt bất kỳ server CSDL nào.

- **Cách 2: Microsoft SQL Server**
  Chạy file `cosodulieu.sql` trong SSMS, sau đó đặt:
  ```python
  DB_ENGINE = 'sqlserver'
  ```

- **Cách 3: MySQL / MariaDB**
  Nhập file `cosodulieu_mysql.sql` vào MySQL (XAMPP / phpMyAdmin), sau đó đặt:
  ```python
  DB_ENGINE = 'mysql'
  ```

### Bước 3: Khởi chạy ứng dụng
```bash
python app.py
```
Mở trình duyệt web truy cập: `http://127.0.0.1:5000`

### Bước 4: Chạy bộ kiểm thử tự động
```bash
python -m unittest discover tests
```

## Tài Khoản Đăng Nhập Thử Nghiệm

| Vai trò | Tên đăng nhập | Mật khẩu | Thông tin & Phạm vi quyền hạn |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin` | `admin123` | Toàn quyền quản trị hệ thống, banner, bác sĩ, tài khoản, bài viết, báo cáo |
| **Bác sĩ Nội khoa** | `bs_quan` | `Password@123` | ThS.BS Trần Minh Quân - Trưởng khoa Nội, PK101 |
| **Bác sĩ Nhi khoa** | `bs_mai` | `Password@123` | BSCKI Lê Thị Mai - Bác sĩ Nhi khoa, PK201 |
| **Bác sĩ Ngoại khoa** | `bs_nam` | `Password@123` | BSCKII Nguyễn Hoàng Nam - Bác sĩ Ngoại khoa, PK103 |
| **Lễ tân trưởng** | `letan_lan` | `Password@123` | Nguyễn Thị Lan - Quầy tiếp đón Tầng 1 |
| **Tiếp đón & Điều phối** | `letan_huyen` | `Password@123` | Trần Thu Huyền - Quầy A, tiếp nhận và điều phối |
| **Thu ngân viện phí** | `letan_thao` | `Password@123` | Lê Phương Thảo - Thu ngân viện phí & BHYT |
| **Dược sĩ kho thuốc** | `duocsi_minh` | `Password@123` | Dược sĩ Phạm Hoàng Minh - Cấp phát thuốc theo đơn |
| **Kỹ thuật viên xét nghiệm** | `ktv_duc` | `Password@123` | KTV. Võ Anh Đức - Thực hiện xét nghiệm CLS & Chẩn đoán hình ảnh |
| **Bệnh nhân mẫu** | `0901234567` | `123456` | Hoàng Bảo Nam - Cổng bệnh nhân, đặt lịch khám online, tra cứu hồ sơ 360° |

## Công Nghệ Sử Dụng (Tech Stack)

- **Backend**: Python 3.10+, Flask 3.0+ (Blueprint MVC Architecture).
- **Image Processing**: Pillow (Auto-compression to WebP, quality 80-85, aspect ratio preserving).
- **Database**: SQLite3, Microsoft SQL Server (pyodbc), MySQL/MariaDB (PyMySQL).
- **Frontend**: HTML5, Tailwind CSS, FontAwesome 6, JavaScript ES6+ (Native DOM & Fetch API).
- **Algorithms**: Levenshtein Distance, Vietnamese Tone Stripping, Multi-token Fuzzy Matcher.
