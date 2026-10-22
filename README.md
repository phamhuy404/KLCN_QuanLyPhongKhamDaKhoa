# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-SQLite%20%7C%20SQL%20Server%20%7C%20MySQL-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20JS-teal.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-32%2F32%20Passing-brightgreen.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo chuẩn kiến trúc MVC (Model - View - Controller), số hóa hoàn chỉnh quy trình y tế từ tiếp đón bệnh nhân, phân công ca trực thông minh, bệnh án điện tử EMR 360°, cận lâm sàng & xét nghiệm 2 bước, quản lý kho dược và kê đơn an toàn, hóa đơn viện phí đa phương thức, bản đồ Google Maps tương tác, cho đến cổng thông tin người bệnh.

## Cấu Trúc Dự Án (Project Structure)

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Entrypoint: Khởi chạy chính ứng dụng Flask
├── config.py                      # Cấu hình tập trung (chuyển đổi 3 CSDL, Maps, Mail)
├── cosodulieu.sql                 # Kịch bản DDL & dữ liệu mẫu Microsoft SQL Server
├── cosodulieu_mysql.sql           # Kịch bản DDL & dữ liệu mẫu MySQL / MariaDB
├── phongkham.db                   # CSDL SQLite chuẩn hóa (chạy ngay, không cần cài server)
├── huongdanchay.txt               # Hướng dẫn chi tiết cài đặt, sitemap & vận hành
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
│
├── controllers/                   # [CONTROLLER] Xử lý nghiệp vụ, phân quyền & điều hướng URL
│   ├── auth_controller.py         #   - Xác thực: Đăng nhập, đăng ký, đăng xuất, phân quyền
│   ├── home_controller.py         #   - Công khai: Trang chủ (slider động), đặt lịch online, cẩm nang y tế
│   ├── patient_controller.py      #   - Cổng bệnh nhân: Hồ sơ 360°, đợt khám, đơn thuốc, kết quả xét nghiệm
│   ├── admin_controller.py        #   - Quản trị: Nhân sự, lịch trực, EMR, kho dược, viện phí, bài viết, banner
│   └── api_controller.py          #   - RESTful API: Đăng ký lịch làm việc hàng loạt, tìm kiếm, AJAX real-time
│
├── models/                        # [MODEL] Tương tác CSDL, truy vấn & ràng buộc dữ liệu
│   ├── user_model.py              #   - Tài khoản, bác sĩ, nhân viên, phân quyền vai trò (RBAC)
│   ├── schedule_model.py          #   - Quản lý ca trực, đăng ký hàng loạt, kiểm soát xung đột & hạn mức
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, nhóm máu, dị ứng, tiền sử bệnh
│   ├── appointment_model.py       #   - Quản lý lịch hẹn khám bệnh, kiểm soát lượt trống bác sĩ
│   ├── banner_model.py            #   - Quản lý slider quảng bá trang chủ (CRUD & sắp xếp)
│   ├── article_model.py           #   - Tin tức, cẩm nang y khoa & tìm kiếm gần đúng tiếng Việt
│   ├── inventory_model.py         #   - Danh mục dược phẩm, quản lý tồn kho & kê đơn tự động trừ kho
│   ├── medical_service_model.py   #   - Bảng giá dịch vụ khám và kỹ thuật cận lâm sàng
│   ├── notification_model.py      #   - Thông báo hệ thống, nhắc nhở lịch hẹn tự động
│   ├── feedback_model.py          #   - Đánh giá chất lượng và phản hồi của người bệnh
│   └── backup_model.py            #   - Sao lưu, khôi phục CSDL an toàn (chống Path Traversal)
│
├── templates/                     # [VIEW] Giao diện người dùng Jinja2 HTML & TailwindCSS
│   ├── layouts/                   #   - Layout dùng chung (base.html, header.html, footer.html)
│   ├── admin/                     #   - Phân hệ quản trị và nhân viên y tế
│   │   ├── components/            #     - Header, sidebar cố định trạng thái thu gọn/mở rộng
│   │   ├── staff.html             #     - Quản lý nhân sự, lịch làm việc tuần & đăng ký ca trực
│   │   ├── banners.html           #     - Quản lý banner slider trang chủ (CRUD & toggle bật/tắt)
│   │   ├── doctors.html           #     - Danh sách bác sĩ phòng khám
│   │   ├── doctor_detail.html     #     - Hồ sơ bác sĩ 360°, ca trực và lịch sử khám bệnh
│   │   ├── accounts.html          #     - Quản lý tài khoản, trạng thái khóa & đổi mật khẩu
│   │   ├── articles.html          #     - Danh sách bài viết cẩm nang y tế
│   │   └── article_editor.html    #     - Trình soạn thảo bài viết mới / chỉnh sửa
│   ├── patient/                   #   - Phân hệ cổng thông tin người bệnh
│   ├── articles.html              #   - Chuyên trang cẩm nang y tế công khai & fuzzy search
│   └── home.html                  #   - Trang chủ giới thiệu dịch vụ phòng khám
│
├── static/                        # Tài nguyên tĩnh Frontend
│   ├── uploads/                   #   - Thư mục lưu trữ ảnh tải lên (tự động nén WebP)
│   │   ├── benh_nhan/             #     - Ảnh chân dung đại diện bệnh nhân
│   │   ├── bac_si/                #     - Ảnh chân dung bác sĩ
│   │   ├── bai_viet/              #     - Ảnh bìa bài viết cẩm nang
│   │   └── banners/               #     - Ảnh slider trang chủ
│   ├── js/main.js                 #   - Bộ máy tìm kiếm gần đúng tiếng Việt, Tag Selector, Toast
│   ├── css/custom.css             #   - Tùy biến CSS bổ sung
│   └── img/                       #   - Ảnh mặc định, icon chuyên khoa
│
├── data/catalogs/                 # Dữ liệu danh mục y tế chuẩn hóa (text thuần)
│   ├── nhom_mau.txt               #   - 8 nhóm máu cơ bản ABO/Rh + Chưa rõ
│   ├── bien_the_nhom_mau.txt      #   - Biến thể nhóm máu & kháng thể bất thường
│   ├── di_ung.txt                 #   - Dị ứng thuốc, hóa chất, thức ăn
│   └── tien_su_benh.txt           #   - Tiền sử bệnh lý nền mạn tính
│
├── core/                          # Tầng hạ tầng & dịch vụ dùng chung
│   ├── database.py                #   - Unified Database Layer (kết nối đa CSDL & auto-migration)
│   ├── csv_service.py             #   - Nhập/xuất CSV chuẩn UTF-8-SIG (Excel) nhận biết trùng lặp
│   ├── image_service.py           #   - Tự động nén ảnh sang WebP (< 80KB), chống phình Git
│   ├── security.py                #   - Băm mật khẩu scrypt, xác thực phân quyền & decorator bảo mật
│   ├── audit.py                   #   - Ghi nhật ký kiểm toán hoạt động hệ thống (Audit Log)
│   └── notification_service.py   #   - Gửi thông báo in-app và quét nhắc nhở lịch hẹn định kỳ
│
└── tests/                         # Bộ kiểm thử tự động (Automated Unit Tests)
    ├── test_system_features.py    #   - 11 test case các phân hệ cốt lõi
    ├── test_features_6_to_10.py   #   - 9 test case quản trị EMR, bác sĩ, banner, ảnh đa định dạng
    └── test_upgraded_features.py  #   - 12 test case đăng ký ca trực tuần, CSV, hạn mức, bảo vệ admin
```

## Các Phân Hệ & Tính Năng Trọng Tâm

### 1. Phân Công & Đăng Ký Lịch Trực Đồng Loạt Theo Tuần
- **Giao diện ma trận tuần**: Hiển thị bảng lịch trực theo 7 ngày trong tuần với 3 ca làm việc rõ ràng:
  - **Ca Sáng**: 07:00 - 11:30.
  - **Ca Chiều**: 13:30 - 17:00.
  - **Ca Tối**: 17:30 - 20:30.
- **Phối màu trực quan**:
  - Ca đã được người dùng đăng ký: hiển thị màu **Xanh lá cây** (`emerald`).
  - Ca chưa đăng ký: hiển thị màu **Xanh dương** (`blue/slate`).
- **Tooltip thông minh**: Khi rê chuột vào từng ô ca làm việc, hệ thống hiển thị danh sách các đồng nghiệp (bác sĩ, nhân viên) cùng trực trong ca đó.
- **Đăng ký đồng loạt nhiều ca**: Cho phép chọn nhiều ca làm việc cùng lúc trên lưới và bấm một nút xác nhận đăng ký với modal kiểm tra lại thông tin.
- **Quy tắc phân công an toàn**:
  - Mỗi vai trò có hạn mức tối đa 5 người/ca.
  - Chỉ cho phép đăng ký ca trực trong 2 tuần tiếp theo, khóa đăng ký các ngày trong tuần hiện tại hoặc quá khứ.
  - Tự động phát hiện trùng ca cùng ngày/giờ đối với từng nhân sự hoặc cùng phòng khám.

### 2. Đồng Bộ Hóa CSDL Cả 3 Phương Án (Unified Multi-Database)
- Hỗ trợ chuyển đổi nhanh chỉ bằng 1 biến `DB_ENGINE` trong [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py):
  - **SQLite** (`phongkham.db`): Sẵn sàng chạy ngay lập tức, không yêu cầu cài đặt phần mềm quản trị CSDL.
  - **Microsoft SQL Server** (`cosodulieu.sql`): Phù hợp triển khai hệ thống bệnh viện lớn trên môi trường Windows Server / SSMS.
  - **MySQL / MariaDB** (`cosodulieu_mysql.sql`): Phù hợp triển khai trên môi trường Linux / Docker / XAMPP.
- Đồng nhất 27 bảng dữ liệu, chuẩn hóa tên cột, kiểu dữ liệu, khóa ngoại và chỉ mục (indexes).
- Cơ chế `UnifiedCursor` tự động tương thích cú pháp câu lệnh (như `GETDATE()` -> `CURRENT_TIMESTAMP` / `NOW()`).

### 3. Quản Lý Banner Slider Trang Chủ & Nén Ảnh WebP Tự Động
- Quản trị viên tùy biến các slide giới thiệu tại `/admin/banners`: Thứ tự ưu tiên, tiêu đề, phụ đề, nút kêu gọi hành động (CTA) và trạng thái hiển thị.
- Tự động nén ảnh thông minh qua [core/image_service.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/core/image_service.py): Chuyển đổi mọi định dạng ảnh tải lên (JPG, PNG, GIF, BMP, TIFF, WebP, SVG, Base64) sang định dạng WebP chất lượng cao với dung lượng siêu nhẹ (< 80KB), giúp trang chủ tải cực nhanh và không làm phình dung lượng kho mã nguồn Git.

### 4. Bản Đồ Google Maps Tích Hợp Tại Chân Trang (Footer)
- Hiển thị trực tiếp vị trí phòng khám tại chân trang người dùng, bố cục tinh gọn cạnh thông tin liên hệ và chuyên khoa.
- Cho phép người dùng bấm vào vị trí để mở chỉ đường trực tiếp trên ứng dụng Google Maps.
- Hỗ trợ 2 chế độ:
  - **Chế độ nhúng miễn phí**: Tự động tạo bản đồ thông qua tọa độ (vĩ độ, kinh độ) mà không bắt buộc có API Key.
  - **Chế độ Google Maps Embed API**: Sử dụng API Key chính thức khi cần tính năng chuyên sâu.

### 5. Quản Trị Nhân Sự & Tài Khoản An Toàn (RBAC)
- Phân quyền chặt chẽ 6 vai trò: `ADMIN` (Quản trị viên), `BACSI` (Bác sĩ), `LETAN` (Lễ tân / Thu ngân), `DUOCSI` (Dược sĩ), `KTV` (Kỹ thuật viên xét nghiệm), `BENHNHAN` (Bệnh nhân).
- Tài khoản quản trị viên tối cao được bảo vệ an toàn: Chặn tuyệt đối hành vi vô hiệu hóa hoặc xóa tài khoản Admin.
- Toàn bộ các vai trò nhân sự đều có thể xem tài khoản Admin ở chế độ chỉ đọc để liên hệ kỹ thuật khi cần.
- Sidebar quản trị chia nhóm khoa học và ghi nhớ trạng thái thu gọn/mở rộng qua `localStorage` (không bị co rút khi đổi trang).

### 6. Bệnh Án Điện Tử (EMR 360°) & Chuẩn Hóa Dữ Liệu Y Tế
- Quản lý hồ sơ bệnh nhân toàn diện: Tiền sử bệnh lý bản thân, tiền sử gia đình, dị ứng thuốc.
- Nhóm máu chuẩn hóa theo 8 phân nhóm ABO/Rh (`O+`, `O-`, `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `Chưa rõ`) cùng trường ghi chú biến thể nhóm máu chuyên sâu (Weak D, Bombay, kháng thể bất thường).
- Lưu vết mọi thao tác chỉnh sửa bệnh án vào bảng `audit_log` để phục vụ công tác thanh tra y tế.

### 7. Quy Trình Cận Lâm Sàng & Xét Nghiệm 2 Bước
- Phân quyền minh bạch: Kỹ thuật viên (KTV) nhập chỉ số xét nghiệm/tải file đính kèm; Bác sĩ điều trị kiểm tra và bấm duyệt kết quả.
- Khóa chỉnh sửa dữ liệu sau khi kết quả xét nghiệm đã được bác sĩ ký duyệt.

### 8. Quản Lý Dược Phẩm & Kê Đơn Tự Động Trừ Kho
- Đơn thuốc điện tử liên thông trực tiếp giữa phòng khám và quầy dược.
- Cơ chế cấp phát thuốc an toàn: Tự động trừ tồn kho chính xác, chống tình trạng cấp phát lặp lại (double-dispense) và cho phép hủy đơn thuốc kèm lý do.

### 9. Quản Lý Viện Phí & Nhập/Xuất Dữ Liệu CSV Chuẩn
- Thanh toán viện phí đa hình thức: Tiền mặt, BHYT, Chuyển khoản ngân hàng.
- Module [core/csv_service.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/core/csv_service.py) hỗ trợ tải tệp mẫu và nhập/xuất CSV chuẩn UTF-8-SIG (tương thích 100% với Microsoft Excel không bị lỗi phông tiếng Việt). Tự động nhận diện trùng lặp để cộng dồn tồn kho thuốc.

### 10. Hệ Thống Nhắc Lịch Khám Tự Động & Sao Lưu CSDL
- Tự động quét và gửi thông báo nhắc lịch khám/tái khám qua In-app notification, có cơ chế kiểm tra chặn gửi trùng lặp.
- Module sao lưu CSDL tại `/admin/backups`: Tự động tạo bản backup CSDL an toàn, kiểm tra nghiêm ngặt đường dẫn file để ngăn ngừa tấn công Path Traversal.

## Cài Đặt & Khởi Chạy Nhanh

### Bước 1: Cài đặt thư viện Python
Mở cửa sổ dòng lệnh tại thư mục dự án và thực hiện:
```bash
pip install -r requirements.txt
```

### Bước 2: Tùy chọn Cơ sở dữ liệu trong `config.py`

Mở file [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py) và thiết lập biến `DB_ENGINE`:

- **Phương án 1: SQLite (Khuyên dùng - Chạy ngay lập tức)**
  ```python
  DB_ENGINE = 'sqlite'
  ```
  Hệ thống sử dụng file [phongkham.db](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/phongkham.db) có sẵn với 27 bảng và 10 tài khoản mẫu chuẩn.

- **Phương án 2: Microsoft SQL Server**
  Mở SQL Server Management Studio (SSMS), mở file [cosodulieu.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/cosodulieu.sql) và nhấn **Execute**. Sau đó cấu hình:
  ```python
  DB_ENGINE = 'sqlserver'
  SQLSERVER_CONFIG = {
      'driver': '{ODBC Driver 17 for SQL Server}',
      'server': 'localhost',
      'database': 'quan_ly_phong_kham',
      'trusted_connection': 'yes'
  }
  ```

- **Phương án 3: MySQL / MariaDB**
  Tạo database `quan_ly_phong_kham` trong phpMyAdmin hoặc MySQL Workbench, import file [cosodulieu_mysql.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/cosodulieu_mysql.sql), sau đó cấu hình:
  ```python
  DB_ENGINE = 'mysql'
  MYSQL_CONFIG = {
      'host': 'localhost',
      'port': 3306,
      'user': 'root',
      'password': '',
      'database': 'quan_ly_phong_kham',
      'charset': 'utf8mb4'
  }
  ```

### Bước 3: Khởi chạy máy chủ Web
```bash
python app.py
```
Mở trình duyệt web và truy cập địa chỉ: `http://127.0.0.1:5000`

### Bước 4: Chạy bộ kiểm thử tự động
Để kiểm tra tính toàn vẹn của toàn bộ 32 chức năng:
```bash
python -m unittest discover tests
```

### Bước 5: Cấu hình vị trí Google Maps (Tùy chọn)
Tại [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py):
```python
CLINIC_NAME = 'Phòng Khám Đa Khoa H2T Healthcare'
CLINIC_ADDRESS = '140 Lê Trọng Tấn, Phường Tây Thạnh, Quận Tân Phú, TP. Hồ Chí Minh'
CLINIC_LATITUDE = 10.806689
CLINIC_LONGITUDE = 106.628581
GOOGLE_MAPS_API_KEY = '' # Để trống để dùng chế độ nhúng trực tiếp miễn phí
```

## Bảng Tài Khoản Thử Nghiệm

Hệ thống đã nạp sẵn 10 tài khoản đại diện cho toàn bộ các nhóm chức năng trong phòng khám:

| Vai trò | Tên đăng nhập | Mật khẩu | Họ và tên | Chức danh / Phạm vi nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| **Quản trị viên** | `admin` | `admin123` | Quản trị viên hệ thống | Toàn quyền quản trị, banner, tài khoản, nhân sự, phân ca, sao lưu |
| **Bác sĩ Nội khoa** | `bs_quan` | `Password@123` | ThS.BS Trần Minh Quân | Trưởng khoa Nội - Phụ trách Phòng khám 101 |
| **Bác sĩ Sản phụ khoa** | `bs_mai` | `Password@123` | BSCKI Lê Thị Mai | Bác sĩ Chuyên khoa Sản - Phòng khám 201 |
| **Bác sĩ Ngoại khoa** | `bs_nam` | `Password@123` | BSCKII Nguyễn Hoàng Nam | Bác sĩ Chuyên khoa Ngoại - Phòng khám 103 |
| **Lễ tân trưởng** | `letan_lan` | `Password@123` | Nguyễn Thị Lan | Tiếp đón bệnh nhân, phân luồng khám, quản lý lịch hẹn |
| **Điều dưỡng tiếp đón** | `letan_huyen` | `Password@123` | Trần Thu Huyền | Điều dưỡng trưởng quầy tiếp nhận và hướng dẫn khám |
| **Thu ngân viện phí** | `letan_thao` | `Password@123` | Lê Phương Thảo | Thu ngân viện phí, đối soát BHYT, in hóa đơn tài chính |
| **Dược sĩ kho dược** | `duocsi_minh` | `Password@123` | DS. Phạm Hoàng Minh | Quản lý kho dược phẩm, duyệt đơn thuốc và cấp phát thuốc |
| **Kỹ thuật viên xét nghiệm** | `ktv_duc` | `Password@123` | KTV. Võ Anh Đức | Thực hiện xét nghiệm cận lâm sàng và chẩn đoán hình ảnh |
| **Bệnh nhân mẫu** | `0901234567` | `123456` | Hoàng Bảo Nam | Cổng bệnh nhân: Đặt lịch trực tuyến, theo dõi EMR, tra cứu đơn thuốc |

## Công Nghệ Sử Dụng (Tech Stack)

- **Ngôn ngữ & Nền tảng**: Python 3.10+, Flask 3.0+ (Kiến trúc Blueprint MVC).
- **Hệ quản trị CSDL**: SQLite3 (WAL mode), Microsoft SQL Server (pyodbc), MySQL 8.0+ (PyMySQL).
- **Xử lý đồ họa & Đa phương tiện**: Pillow (Chuyển đổi và nén tối ưu WebP).
- **Giao diện Frontend**: HTML5 semantic, Tailwind CSS, FontAwesome 6, JavaScript ES6+ (Native Fetch, LocalStorage).
- **Thuật toán & Bảo mật**: Password hashing với `scrypt`, Levenshtein Distance (Fuzzy Search tiếng Việt), Role-Based Access Control (RBAC).
