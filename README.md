# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server%20(100%25%20T--SQL)-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20JS-teal.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-22%2F22%20Passing%20(100%25)-brightgreen.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo chuẩn kiến trúc MVC (Model - View - Controller), hoạt động chuyên biệt 100% trên nền tảng **Microsoft SQL Server**. Hệ thống số hóa hoàn chỉnh quy trình y tế khép kín: Tiếp đón & đặt lịch khám, phân công ca trực thông minh, bệnh án điện tử EMR 360°, cận lâm sàng 2 bước, quản lý kho dược có cảnh báo tồn kho an toàn, cấp phát thuốc tự động trừ kho, hóa đơn viện phí BHYT tổng hợp, bản đồ Google Maps tương tác và cổng thông tin người bệnh.

## Cấu Trúc Dự Án (Project Structure)

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Khởi chạy chính ứng dụng Flask
├── config.py                      # Cấu hình tập trung (Microsoft SQL Server, Google Maps)
├── cosodulieu.sql                 # Kịch bản DDL & DML trọn gói Microsoft SQL Server
├── huongdanchay.txt               # Hướng dẫn chi tiết cài đặt, sitemap & danh sách tài khoản
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
│
├── core/                          # Tầng hạ tầng & dịch vụ dùng chung
│   ├── database.py                #   - UnifiedCursor & kết nối pyodbc Microsoft SQL Server
│   ├── validators.py              #   - Bộ lọc kiểm tra dữ liệu, chống ký tự lạ & regex
│   ├── security.py                #   - Băm mật khẩu scrypt, xác thực phiên & phân quyền RBAC
│   ├── image_service.py           #   - Tự động nén ảnh sang WebP (< 80KB) chống phình Git
│   ├── csv_service.py             #   - Nhập/xuất CSV chuẩn UTF-8-SIG (Excel)
│   ├── audit.py                   #   - Ghi nhật ký kiểm toán hoạt động hệ thống (Audit Log)
│   └── notification_service.py   #   - Gửi thông báo in-app và quét nhắc nhở lịch hẹn
│
├── controllers/                   # [CONTROLLER] Xử lý nghiệp vụ & điều hướng URL
│   ├── auth_controller.py         #   - Đăng nhập, đăng ký, đăng xuất & kiểm tra hoàn thiện hồ sơ
│   ├── home_controller.py         #   - Trang chủ (random bác sĩ), đặt lịch online, cẩm nang y tế
│   ├── patient_controller.py      #   - Cổng bệnh nhân: Hồ sơ 360°, bắt buộc hoàn thiện hồ sơ, EMR
│   ├── admin_controller.py        #   - Quản trị: Tiếp nhận, EMR, CLS, kho dược, viện phí, sao lưu
│   └── api_controller.py          #   - RESTful API: Đăng ký lịch làm việc, tiếp nhận, xuất thuốc, viện phí
│
├── models/                        # [MODEL] Tương tác CSDL SQL Server & ràng buộc dữ liệu
│   ├── user_model.py              #   - Tài khoản, hoàn thiện hồ sơ, phân quyền RBAC (61 tài khoản)
│   ├── appointment_model.py       #   - Quản lý lịch hẹn khám bệnh, tiếp nhận & gửi thông báo
│   ├── medical_record_model.py    #   - Bệnh án điện tử EMR, chỉ định CLS, kiểm tra tồn kho thuốc
│   ├── pharmacy_model.py          #   - Quản lý kho dược, cảnh báo tồn kho ít & cấp phát trừ kho
│   ├── billing_model.py           #   - Quản lý viện phí, khấu trừ BHYT & thanh toán đa phương thức
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, nhóm máu, dị ứng, tiền sử bệnh
│   ├── schedule_model.py          #   - Phân công & đăng ký ca trực tuần (Sáng-Chiều-Tối)
│   ├── banner_model.py            #   - Quản lý slider quảng bá trang chủ (CRUD & sắp xếp)
│   ├── article_model.py           #   - Tin tức, cẩm nang y khoa & tìm kiếm gần đúng tiếng Việt
│   ├── medical_service_model.py   #   - Bảng giá dịch vụ khám và kỹ thuật cận lâm sàng
│   ├── notification_model.py      #   - Thông báo hệ thống, nhắc nhở lịch hẹn tự động
│   ├── feedback_model.py          #   - Đánh giá chất lượng và phản hồi của người bệnh
│   └── backup_model.py            #   - Sao lưu, khôi phục CSDL SQL Server (.bak)
│
├── templates/                     # [VIEW] Giao diện người dùng Jinja2 HTML & TailwindCSS
│   ├── layouts/                   #   - Layout dùng chung (base.html, header.html, footer.html có GG Maps)
│   ├── auth/                      #   - Giao diện đăng nhập, đăng ký tài khoản
│   ├── patient/                   #   - Giao diện cổng bệnh nhân & trang hoàn thiện hồ sơ
│   │   ├── complete_profile.html  #     - Form hoàn thiện thông tin cá nhân bắt buộc lần đầu
│   │   ├── dashboard.html         #     - Tổng quan sức khỏe & banner nhắc lịch khám
│   │   ├── booking.html           #     - Đặt lịch khám trực tuyến
│   │   ├── profile.html           #     - Hồ sơ sức khỏe cá nhân 360°
│   │   ├── records.html           #     - Lịch sử bệnh án & đơn thuốc điện tử
│   │   └── lab_results.html       #     - Kết quả cận lâm sàng
│   ├── admin/                     #   - Phân hệ quản trị và nhân viên y tế
│   │   ├── components/            #     - Header, sidebar cố định trạng thái thu gọn/mở rộng
│   │   ├── appointments.html      #     - Danh sách lịch hẹn khám & nút Tiếp nhận
│   │   ├── emr.html               #     - Phòng khám điện tử EMR, chọn CLS, kê đơn cảnh báo tồn
│   │   ├── lab.html               #     - Cận lâm sàng & chẩn đoán hình ảnh
│   │   ├── pharmacy.html          #     - Kho dược, cảnh báo tồn kho ít & xuất thuốc trừ kho
│   │   ├── billing.html           #     - Viện phí, hóa đơn tổng hợp & xác nhận thanh toán
│   │   ├── staff.html             #     - Quản lý nhân sự, lịch làm việc tuần & ca trực
│   │   ├── doctors.html           #     - Danh sách 35 bác sĩ chuyên khoa
│   │   ├── patients.html          #     - Quản lý danh sách bệnh nhân
│   │   └── backups.html           #     - Sao lưu & phục hồi CSDL SQL Server (.bak)
│   └── home.html                  #   - Trang chủ hiển thị ngẫu nhiên bác sĩ
│
└── scratch/                       # Kịch bản bảo trì & kiểm thử hệ thống
    ├── seed_database.py           #   - Nạp sạch CSDL & 61 tài khoản chuẩn vào SQL Server
    └── test_full_system.py        #   - Bộ test tự động 17/17 ca kiểm thử nghiệp vụ toàn diện
```

## Khởi Chạy Nhanh Trong 3 Bước

### Bước 1: Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi tạo CSDL Microsoft SQL Server
Chạy script nạp tự động để tạo CSDL sạch và 61 tài khoản chuẩn:
```bash
python scratch/seed_database.py
```
*(Hoặc mở file [cosodulieu.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/cosodulieu.sql) trong SQL Server Management Studio và nhấn Execute F5).*

### Bước 3: Khởi chạy máy chủ Web
```bash
python app.py
```
Truy cập ứng dụng tại địa chỉ: `http://127.0.0.1:5000`

### Kiểm thử toàn diện (Automated Tests)
```bash
python scratch/test_full_system.py
```

## Danh Sách 61 Tài Khoản Hệ Thống Chuẩn

Toàn bộ hệ thống được khởi tạo với 61 tài khoản sạch, đầy đủ hồ sơ bệnh án và lịch trực:

| Vai trò | Số lượng | Tài khoản mẫu | Mật khẩu | Ghi chú quyền hạn |
| :--- | :--- | :--- | :--- | :--- |
| **Quản trị viên (ADMIN)** | 1 | `admin` | `admin123` | Toàn quyền quản trị, cấu hình, phân công nhân sự, sao lưu CSDL (.bak) |
| **Lễ tân & Thu ngân (LETAN)** | 5 | `letan_1` đến `letan_5` | `Password@123` | Tiếp đón, tiếp nhận lịch hẹn online, cấp số khám, thu viện phí |
| **Dược sĩ kho dược (DUOCSI)** | 5 | `duocsi_1` đến `duocsi_5` | `Password@123` | Quản lý kho dược, theo dõi hạn dùng, cảnh báo tồn kho, cấp phát thuốc trừ kho |
| **Kỹ thuật viên CLS (KTV)** | 5 | `ktv_1` đến `ktv_5` | `Password@123` | Thực hiện X-quang, xét nghiệm máu, siêu âm, nội soi, nhập kết quả |
| **Bác sĩ Chuyên khoa (BACSI)** | 35 | Xem chi tiết bên dưới (7 khoa x 5 BS) | `Password@123` | Khám EMR, ra y lệnh CLS, duyệt kết quả, kê đơn kiểm tra tồn kho |
| **Bệnh nhân chuẩn (BENHNHAN)** | 10 | `0901234561` đến `0901234570` | `123456` | Cổng bệnh nhân cá nhân, đặt lịch, hồ sơ 360°, đơn thuốc, viện phí |

### Chi tiết 35 Bác sĩ chuyên khoa (7 khoa x 5 bác sĩ):
- **Khoa Nội tổng quát**: `bs_noi_1` đến `bs_noi_5` (Phòng 101 - 105).
- **Khoa Ngoại tổng quát**: `bs_ngoai_1` đến `bs_ngoai_5` (Phòng 106 - 110).
- **Khoa Nhi khoa**: `bs_nhi_1` đến `bs_nhi_5` (Phòng 201 - 205).
- **Khoa Răng Hàm Mặt**: `bs_rhm_1` đến `bs_rhm_5` (Phòng 301 - 305).
- **Khoa Sản - Phụ Khoa**: `bs_san_1` đến `bs_san_5` (Phòng 401 - 405).
- **Khoa Tai Mũi Họng**: `bs_tmh_1` đến `bs_tmh_5` (Phòng 501 - 505).
- **Khoa Mắt**: `bs_mat_1` đến `bs_mat_5` (Phòng 601 - 605).

## Các Tính Năng Nâng Cấp Nổi Bật

### 1. Luồng Đăng Ký Mới & Bắt Buộc Hoàn Thiện Hồ Sơ Lần Đầu
- Người dùng đăng ký nhanh qua `/register` với Họ tên, SĐT và Mật khẩu. Tài khoản được gắn cờ `da_hoan_thien_ho_so = 0`.
- Khi đăng nhập lần đầu vào Cổng bệnh nhân, hệ thống tự động nhận diện và chuyển hướng bắt buộc đến trang [/patient/complete-profile](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/templates/patient/complete_profile.html).
- **Bộ lọc kiểm tra dữ liệu nghiêm ngặt** ([core/validators.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/core/validators.py)):
  - Cấm tuyệt đối các ký tự lạ và nguy hại: `<, >, {, }, [, ], $, %, ^, &, *, =, +, ~, `, |, \, ;, --`.
  - Họ tên: Chuẩn tiếng Việt có dấu, không chứa số hay ký tự đặc biệt.
  - SĐT: Đúng 10 chữ số đầu số Việt Nam.
  - CCCD: Đúng 12 chữ số định danh cá nhân.
  - Ngày sinh: Không vượt quá ngày hiện tại, tuổi từ 0 đến 130.

### 2. Quy Trình Khám Chữa Bệnh Khép Kín (End-to-End Clinic Workflow)
Hệ thống kết nối liên thông chặt chẽ 6 bước:
1. **Đồng bộ đặt lịch khám & Ca trực Bác sĩ**:
   - Bệnh nhân chọn Chuyên khoa, chọn Ngày khám và Giờ khám trước (13 khung giờ chuẩn cách đầu và cuối ca 1 tiếng, mỗi nấc 30 phút: Ca Sáng 08:00 - 10:30; Ca Chiều 14:30 - 16:00; Ca Tối 18:30 - 19:30).
   - Hệ thống tự động lọc danh sách Bác sĩ trực ca tương ứng trong ngày theo thời gian thực.
   - Lịch hẹn lưu ở trạng thái `Chờ tiếp nhận` và ẩn khỏi danh sách của Bác sĩ cho đến khi được Tiếp tân/Admin duyệt qua.
2. **Tiếp nhận & Thông báo 2 chiều**:
   - Lễ tân/Admin duyệt lịch hẹn (`Đã tiếp nhận` / `Đã xác nhận`) -> Lịch hẹn lập tức xuất hiện tại phòng khám của Bác sĩ trực ca đó.
   - Bệnh nhân nhận thông báo in-app xác nhận thành công và banner nhắc nhở trước ngày khám.
3. **Khám lâm sàng bình thường (Sức khỏe tốt)**:
   - Nếu bệnh nhân không có bệnh lý, bác sĩ chỉ cần bấm nút **"Sức Khỏe Tốt (Xuất Hóa Đơn Ngay)"** một chạm. Hệ thống kết thúc phiên khám và tự động xuất hóa đơn viện phí tiền khám ngay lập tức.
4. **Khám chuyên sâu, Cận lâm sàng & Upload ảnh chẩn đoán**:
   - Bác sĩ ra y lệnh CLS -> Bệnh nhân nhận thông báo in-app hướng dẫn di chuyển đến phòng Cận lâm sàng.
   - Kỹ thuật viên (KTV) thực hiện kỹ thuật và **upload ảnh chụp chẩn đoán hình ảnh** (siêu âm, X-quang, nội soi...).
   - Bác sĩ mở Tab 4 **"Xem Kết Quả CLS & Ảnh Chụp"** trên EMR để phóng to ảnh chụp chuẩn HD, hội chẩn và bấm duyệt kết quả -> Bệnh nhân nhận thông báo quay lại phòng khám ban đầu để tư vấn kết luận.
5. **Kê đơn thuốc & Tùy chọn nơi mua thuốc**:
   - Bác sĩ kê đơn thuốc (có cảnh báo tồn ít và chặn kê vượt tồn). Đơn thuốc ban đầu ở trạng thái `Chờ bệnh nhân xác nhận mua`.
   - Bệnh nhân nhận thông tin đơn thuốc trên Cổng cá nhân với 2 lựa chọn:
     + *Tự mua ngoài*: Không tính tiền vào viện phí, không trừ kho thuốc bệnh viện.
     + *Mua tại bệnh viện*: Sinh hóa đơn thuốc riêng biệt `HDT...` (không hiển thị đơn giá lẻ từng loại theo quy định), tự động trừ số lượng tồn kho bệnh viện và chuyển sang kho Dược.
6. **Quản lý viện phí & Cổng thanh toán VietQR**:
   - Quản lý minh bạch từng khoản thu (Tiền khám, Tiền CLS, Tiền thuốc mua tại viện).
   - Tích hợp mã VietQR động trực tuyến 24/7 chứa sẵn thông tin giao dịch chính xác. Thu ngân hoặc bệnh nhân xác nhận thanh toán trực tuyến cập nhật trạng thái `Đã thanh toán` tức thì.

### 3. Hiển Thị Bác Sĩ Ngẫu Nhiên Ở Trang Chủ
Mỗi lần tải trang chủ (`/`), hệ thống tự động xáo trộn ngẫu nhiên danh sách 35 bác sĩ chuyên khoa giúp người bệnh tiếp cận đa dạng đội ngũ y bác sĩ, đồng thời tạo giao diện động trực quan.

### 4. Sao Lưu & Phục Hồi Microsoft SQL Server (.bak)
- Phân hệ quản trị [/admin/backups](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/templates/admin/backups.html) hỗ trợ sao lưu trực tiếp bằng câu lệnh T-SQL `BACKUP DATABASE` sinh file `.bak`.
- Phục hồi an toàn: Hệ thống tự động tạo bản sao lưu dự phòng trước khi phục hồi, đưa cơ sở dữ liệu về chế độ `SINGLE_USER` và mở lại `MULTI_USER` tự động.
