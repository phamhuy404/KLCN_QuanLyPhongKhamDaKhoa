# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare (HIS & EMR)

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server%20(100%25%20T--SQL)-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20Web%20Audio-teal.svg)]()
[![Dark Mode](https://img.shields.io/badge/Dark%20Mode-Midnight%20Slate-indigo.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-Passing%20(100%25)-brightgreen.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo kiến trúc MVC (Model - View - Controller), vận hành 100% trên nền tảng **Microsoft SQL Server**. Hệ thống số hóa hoàn chỉnh quy trình y tế khép kín: Tiếp đón, phân phòng khám, bệnh án điện tử EMR 5 bước liên hoàn kèm đa ảnh chuẩn hóa (tối đa 10 ảnh WebP, lightbox phóng to), điều phối phiên cận lâm sàng, cảnh báo dị ứng thuốc thời gian thực, quản lý kho dược và cấp phát thuốc 3 bước, viện phí cấn trừ BHYT 80%, thanh toán tự động VietQR, tự động sao lưu định kỳ và nạp bản sao lưu gần nhất khi khởi động, cùng giao diện Dark Mode Midnight Slate toàn diện.

---

## Mục Lục
1. [Cấu Trúc Thư Mục Dự Án](#cấu-trúc-thư-mục-dự-án)
2. [Hướng Dẫn Cài Đặt và Khởi Chạy](#hướng-dẫn-cài-đặt-và-khởi-chạy)
3. [Cơ Chế Sao Lưu và Phục Hồi CSDL Tự Động](#cơ-chế-sao-lưu-và-phục-hồi-csdl-tự-động)
4. [Ma Trận Phân Quyền Hệ Thống (RBAC)](#ma-trận-phân-quyền-hệ-thống-rbac)
5. [Danh Sách Tài Khoản Mẫu Theo Vai Trò](#danh-sách-tài-khoản-mẫu-theo-vai-trò)
6. [Danh Mục Tính Năng Nghiệp Vụ Toàn Diện](#danh-mục-tính-năng-nghiệp-vụ-toàn-diện)
7. [Hệ Thống Ràng Buộc Dữ Liệu Nghiêm Ngặt](#hệ-thống-ràng-buộc-dữ-liệu-nghiêm-ngặt)
8. [Cơ Sở Dữ Liệu 27 Bảng Microsoft SQL Server](#cơ-sở-dữ-liệu-27-bảng-microsoft-sql-server)
9. [Bộ Kiểm Thử Tự Động (Unit Tests)](#bộ-kiểm-thử-tự-động-unit-tests)
10. [Bản Quyền và Thông Tin Đồ Án](#bản-quyền-và-thông-tin-đồ-án)

---

## Cấu Trúc Thư Mục Dự Án

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Điểm khởi chạy chính của máy chủ Flask (tự động nạp CSDL mới nhất)
├── config.py                      # Cấu hình tập trung (Microsoft SQL Server, SMTP, Auto-backup, Google Maps)
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
├── README.md                      # Tài liệu tổng quan và hướng dẫn vận hành dự án
│
├── database/                      # [DATABASE] Cơ sở dữ liệu Microsoft SQL Server
│   ├── cosodulieu.sql             #   - Kịch bản DDL và DML trọn gói Microsoft SQL Server (100% T-SQL)
│   ├── migrations/                #   - Các bản script nâng cấp CSDL theo thời gian
│   └── legacy_bridge.py           #   - Module hỗ trợ tương thích ngược
│
├── docs/                          # [DOCS] Tài liệu vận hành, quy trình và kiểm thử
│   ├── huong_dan_chay.md          #   - Hướng dẫn cài đặt, cấu hình SQL Server và khởi chạy chi tiết
│   ├── kiem_thu_thu_cong_toan_dien.md # - Cẩm nang kiểm thử thủ công từng bước cho nhóm
│   └── QUY_TRINH_NGHIEP_VU_HE_THONG.md # - Tài liệu nghiệp vụ y tế và cơ chế cấn trừ chuẩn
│
├── data/                          # [DATA] Từ điển danh mục chuẩn và Mock data
│   ├── catalogs/                  #   - Từ điển danh mục: nhóm máu, biến thể, dị ứng, tiền sử bệnh
│   │   ├── nhom_mau.txt           #     - 8 nhóm máu cơ bản ABO và Rh (+/-)
│   │   ├── bien_the_nhom_mau.txt  #     - 12 biến thể nhóm máu hiếm (Weak D, Partial D, Bombay, ...)
│   │   ├── di_ung.txt             #     - 19 nhóm dị ứng thuốc và thực phẩm phổ biến
│   │   └── tien_su_benh.txt       #     - 21 bệnh lý nền mạn tính (Tim mạch, Huyết áp, Đái tháo đường, ...)
│   └── articles_data.py           #   - Dữ liệu cẩm nang y khoa mẫu
│
├── backups/                       # [BACKUPS] Thư mục chứa các bản sao lưu tự động .bak của SQL Server
│
├── core/                          # [CORE] Tầng hạ tầng và dịch vụ nghiệp vụ dùng chung
│   ├── database.py                #   - UnifiedCursor và kết nối pyodbc Microsoft SQL Server
│   ├── validators.py              #   - Bộ lọc kiểm tra dữ liệu, chống ký tự lạ, chuẩn regex tiếng Việt
│   ├── security.py                #   - Băm mật khẩu scrypt, xác thực phiên và phân quyền RBAC
│   ├── image_service.py           #   - Tự động nén ảnh WebP (< 80KB) chống phình bộ nhớ
│   ├── csv_service.py             #   - Nhập/xuất CSV chuẩn UTF-8-SIG (Excel)
│   ├── audit.py                   #   - Ghi nhật ký kiểm toán hoạt động hệ thống (Audit Log)
│   ├── catalog.py                 #   - Quản lý nạp danh mục y khoa từ file text
│   └── notification_service.py    #   - Gửi thông báo in-app đa kênh và quét nhắc nhở lịch hẹn
│
├── controllers/                   # [CONTROLLER] Xử lý nghiệp vụ và điều hướng URL
│   ├── auth_controller.py         #   - Đăng nhập, đăng ký, đăng xuất, cưỡng chế đổi mật khẩu
│   ├── home_controller.py         #   - Trang chủ (random BS, random đánh giá), giá khám, DS bác sĩ, chuyên khoa
│   ├── patient_controller.py      #   - Cổng bệnh nhân: Hồ sơ 360°, đơn thuốc, hóa đơn, đặt lịch 2 chiều, phản hồi
│   ├── admin_controller.py        #   - Phân hệ quản trị: Tiếp đón, EMR, CLS, kho dược, viện phí, hồ sơ cá nhân
│   ├── api_controller.py          #   - RESTful API: Đăng ký ca trực, EMR, xuất thuốc, viện phí, sao lưu
│   └── mobile_auth_controller.py  #   - API xác thực dành cho ứng dụng di động Flutter
│
├── models/                        # [MODEL] Tương tác CSDL SQL Server và ràng buộc nghiệp vụ (13 Models)
│   ├── user_model.py              #   - Tài khoản, phân quyền RBAC, hồ sơ nhân viên, cấp lại mật khẩu
│   ├── appointment_model.py       #   - Đặt lịch, ma trận giờ khám 2 chiều, chống đặt trùng, chặn đổi lịch đã xong
│   ├── medical_record_model.py    #   - EMR 5 bước liên hoàn, chỉ định CLS, kiểm tra tồn kho và kê đơn
│   ├── pharmacy_model.py          #   - Quản lý kho dược, duyệt đơn 3 bước, cấp phát thực tế trừ kho
│   ├── billing_model.py           #   - Viện phí, khấu trừ BHYT 80%, nhận diện hóa đơn thuốc HDT
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, tiền sử dị ứng, cận lâm sàng, nhóm máu
│   ├── schedule_model.py          #   - Lịch ca trực: Lễ tân tự duyệt, Admin ẩn, giới hạn 3 BS/khoa/ca
│   ├── notification_model.py      #   - Hệ thống thông báo tức thì, popups real-time, chuông Web Audio
│   ├── banner_model.py            #   - Quản lý slider quảng bá trang chủ (CRUD và sắp xếp)
│   ├── article_model.py           #   - Tin tức, cẩm nang y khoa (phân quyền Lễ tân và Admin được đăng)
│   ├── clinic_model.py            #   - Dịch vụ y tế, thống kê dashboard phòng khám
│   ├── feedback_model.py          #   - Đánh giá chất lượng và phản hồi của người bệnh (lọc >= 4 sao)
│   └── backup_model.py            #   - Sao lưu, tự động phục hồi CSDL SQL Server (.bak), scheduler 2 giờ
│
├── static/                        # [STATIC] Tài nguyên tĩnh giao diện
│   ├── css/custom.css             #   - Custom styles, hệ thống Dark Mode Midnight Slate toàn diện
│   ├── js/main.js                 #   - Toast notification, Polling, Schedule interaction, Dropzone
│   ├── js/theme.js                #   - Quản lý chuyển đổi chế độ Sáng / Tối (Dark Mode) và lưu localStorage
│   ├── img/                       #   - Hình ảnh bài viết, icon thương hiệu
│   └── uploads/                   #   - Tệp đính kèm người dùng: kết quả CLS, ảnh lâm sàng EMR, banner
│
├── templates/                     # [VIEW] Giao diện Jinja2 HTML và TailwindCSS
│   ├── layouts/                   #   - Layout dùng chung (base.html, footer.html)
│   ├── auth/                      #   - Giao diện đăng nhập, đăng ký, cưỡng chế đổi mật khẩu (123 -> mới)
│   ├── patient/                   #   - Cổng bệnh nhân: Dashboard, đặt lịch 2 chiều, EMR, xét nghiệm, hóa đơn
│   ├── admin/                     #   - Phân hệ quản trị: EMR 5 bước, CLS Lab, kho dược, hồ sơ cá nhân, ca trực
│   ├── public/                    #   - 3 trang công khai cho Khách: Bảng giá (/pricing), DS Bác sĩ (/doctors), Chuyên khoa (/departments)
│   └── home.html                  #   - Trang chủ lấy dữ liệu ngẫu nhiên chuẩn từ CSDL
│
└── tests/                         # [TESTS] Kiểm thử tự động đảm bảo an toàn hệ thống
    ├── test_startup_safety.py     #   - Kiểm thử khởi động an toàn, idempotent, chống nạp đè CSDL
    ├── test_upgraded_features.py  #   - Kiểm thử ma trận đặt lịch 2 chiều, backup tự động, Dark mode, bảo mật
    └── ...
```

---

## Hướng Dẫn Cài Đặt và Khởi Chạy

### 1. Yêu cầu môi trường
* **Hệ điều hành**: Windows 10/11 hoặc Windows Server 64-bit.
* **Python**: Phiên bản 3.9 trở lên (Khuyến nghị Python 3.10 hoặc 3.11).
* **Cơ sở dữ liệu**: Microsoft SQL Server 2017, 2019, 2022 hoặc Microsoft SQL Server Express (Bản miễn phí).
* **Driver ODBC**: Microsoft ODBC Driver 17 for SQL Server (hoặc Driver 18).

### 2. Các bước thiết lập ban đầu

#### Bước 1: Cài đặt thư viện Python
Mở PowerShell hoặc Command Prompt tại thư mục gốc dự án:
```bash
pip install -r requirements.txt
```

#### Bước 2: Cấu hình kết nối SQL Server trong `config.py`
Mở file [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py) và cấu hình khối `SQLSERVER_CONFIG`:
```python
DB_ENGINE = 'sqlserver'

SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost',             # Hoặc: '.\SQLEXPRESS', 'localhost\SQLEXPRESS'
    'database': 'quan_ly_phong_kham',  # Tên cơ sở dữ liệu
    'trusted_connection': 'yes',       # Dùng Windows Authentication
    'TrustServerCertificate': 'yes'    # Tránh lỗi chứng chỉ trên SQL Server 2022
}
```
*Ghi chú: Nếu dùng tài khoản SQL Server Authentication (`sa`), đặt `'trusted_connection': 'no'` và bổ sung `'uid': 'sa'`, `'pwd': 'mat_khau_cua_ban'`.*

#### Bước 3: Khởi tạo Cơ sở dữ liệu và nạp dữ liệu sạch (CHỈ CHẠY 1 LẦN DUY NHẤT KHI CÀI ĐẶT)
> [!IMPORTANT]
> **Bước 3 chỉ chạy DUY NHẤT MỘT LẦN** khi bạn vừa cài đặt dự án lần đầu tiên để tạo bảng và nạp 69 tài khoản mẫu. Tuyệt đối **không chạy lại** bước này trong các lần làm việc hàng ngày, vì lệnh này sẽ xóa sạch dữ liệu hiện tại để đưa về trạng thái trắng ban đầu.

Chạy lệnh nạp dữ liệu sạch:
```bash
python scratch/seed_database.py
```
*(Nếu cơ sở dữ liệu đã có dữ liệu hoạt động, script được trang bị khóa an toàn sẽ cảnh báo và yêu cầu xác nhận để tránh mất dữ liệu ngoài ý muốn).*

#### Bước 4: Khởi chạy máy chủ Web Flask (LỆNH VẬN HÀNH HÀNG NGÀY)
Mỗi ngày khi mở máy tính làm việc, bạn **chỉ cần chạy duy nhất một lệnh sau**:
```bash
python app.py
```
Khi hiển thị thông báo:
```text
[*] Khởi động hệ thống: Đang nạp bản sao lưu mới nhất...
[Thành công] Đã đưa bản lưu gần nhất vào CSDL.
* Running on http://127.0.0.1:5000
```
Hệ thống đã sẵn sàng phục vụ tại địa chỉ: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Cơ Chế Sao Lưu và Phục Hồi CSDL Tự Động

Hệ thống được trang bị cơ chế bảo toàn dữ liệu và đồng bộ làm việc nhóm thông minh:

1. **Tự động sao lưu định kỳ mỗi 2 tiếng (Auto-Backup Scheduler)**:
   - Khi chạy `python app.py`, một tiến trình chạy ngầm (`start_auto_backup_scheduler`) được kích hoạt tự động.
   - Cứ mỗi 2 tiếng, hệ thống tự động sinh một bản sao lưu toàn vẹn `.bak` vào thư mục [backups/](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/backups).
   - Tự động dọn dẹp các file cũ, duy trì 20 bản sao lưu mới nhất để tối ưu dung lượng ổ đĩa.
2. **Tự động nạp bản sao lưu gần nhất khi khởi động (`python app.py`)**:
   - Khi khởi động server, hệ thống tự động quét tìm file `.bak` mới nhất trong thư mục `backups/` và khôi phục vào SQL Server.
   - Thao tác này được bảo vệ chạy đúng 1 lần trên tiến trình chính, không gây nghẽn hay lặp lại khi Flask tự động reload code.
3. **Tạo bản sao lưu tức thì bằng 1 click**:
   - Quản trị viên truy cập trang **Sao lưu và Phục hồi** (`/admin/backups`) và bấm **"Tạo bản sao lưu ngay"** để chốt phiên dữ liệu hiện tại.
4. **Lệnh đồng bộ nhóm 1-Click dành cho thành viên**:
   - Khi một thành viên trong nhóm nhận được file `.bak` mới (hoặc pull từ Git về thư mục `backups/`), chỉ cần chạy:
     ```bash
     python scratch/restore_backup.py
     ```
     Hoặc vừa nạp backup mới vừa bật Web:
     ```bash
     python app.py --restore-latest
     ```

---

## Ma Trận Phân Quyền Hệ Thống (RBAC)

Hệ thống quản lý nghiêm ngặt theo mô hình Kiểm soát truy cập dựa trên vai trò (Role-Based Access Control) với 6 vai trò chính:

| Chức năng / Phân hệ | Khách (Guest) | Bệnh nhân (BENHNHAN) | Lễ tân / Thu ngân (LETAN) | Bác sĩ (BACSI) | Kỹ thuật viên (KTV) | Dược sĩ (DUOCSI) | Quản trị viên (ADMIN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Xem Trang chủ & Tin tức** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Xem Bảng giá, Bác sĩ, Chuyên khoa** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Đăng ký tài khoản Bệnh nhân** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Đặt lịch khám trực tuyến** | Cần Login | ✅ | ✅ *(Tại quầy)* | ✅ *(Tái khám)* | ❌ | ❌ | ❌ |
| **Xem Hồ sơ sức khỏe 360°** | ❌ | ✅ *(Cá nhân)* | ✅ *(Tra cứu)* | ✅ *(Bệnh nhân khám)* | ❌ | ❌ | ✅ |
| **Bệnh án điện tử EMR 5 bước** | ❌ | ✅ *(Xem kết quả)* | ❌ | ✅ *(Khám & Kê đơn)* | ❌ | ❌ | ✅ *(Xem)* |
| **Chỉ định Cận lâm sàng (CLS)** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Thực hiện CLS & Tải ảnh phòng Lab** | ❌ | ❌ | ❌ | ✅ *(Xem)* | ✅ *(Thực hiện & Tải ảnh)* | ❌ | ✅ |
| **Kiểm tra trạng thái đóng phí CLS** | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Quản lý Kho Dược & Duyệt đơn thuốc**| ❌ | ❌ | ✅ *(Thu tiền)* | ❌ | ❌ | ✅ *(Cấp phát trừ kho)* | ✅ |
| **Thu Viện phí & Cấn trừ BHYT 80%** | ❌ | ✅ *(Thanh toán QR)* | ✅ *(Lập & Thu tiền)* | ❌ | ❌ | ❌ | ✅ |
| **Đăng bài Cẩm nang y tế** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Đăng ký & Phê duyệt Ca trực** | ❌ | ❌ | ✅ *(Tự duyệt)* | ✅ *(Chờ duyệt)* | ✅ *(Chờ duyệt)* | ✅ *(Chờ duyệt)* | ✅ *(Duyệt & Không trực)* |
| **Cài đặt Giá khám cá nhân** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Quản lý Tài khoản & Phân quyền** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Cấp lại mật khẩu (về mặc định 123)** | ❌ | ❌ | ✅ *(Bệnh nhân)* | ❌ | ❌ | ❌ | ✅ *(Toàn hệ thống)* |
| **Sao lưu & Phục hồi CSDL (.bak)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Xem Nhật ký Kiểm toán (Audit Log)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Danh Sách Tài Khoản Mẫu Theo Vai Trò

Hệ thống được khởi tạo sẵn **69 tài khoản mẫu** bao phủ mọi trường hợp nghiệp vụ để phục vụ kiểm thử và nghiệm thu:

| Vai trò hệ thống | Tên đăng nhập | Mật khẩu mặc định | Ghi chú và Quyền hạn đặc trưng |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (ADMIN)** | `admin` | `admin123` | Quản trị toàn hệ thống, tạo nhân sự, duyệt ca trực, sao lưu database |
| **Lễ tân & Thu ngân (LETAN)** | `letan_1` | `Password@123` | Tiếp đón bệnh nhân, phân phòng, tự duyệt ca trực, thu viện phí, đăng bài viết |
| **Lễ tân 2..5** | `letan_2` .. `letan_5` | `Password@123` | Nhân sự lễ tân các ca trực khác |
| **Bác sĩ Nội khoa (BACSI)** | `bs_noi_1` | `Password@123` | Khám lâm sàng EMR, cảnh báo dị ứng thuốc, chỉ định xét nghiệm |
| **Bác sĩ Ngoại khoa (BACSI)** | `bs_ngoai_1` | `Password@123` | Khám ngoại khoa, chỉ định chẩn đoán hình ảnh, điều phối CLS |
| **Bác sĩ Nhi khoa (BACSI)** | `bs_nhi_1` | `Password@123` | Khám nhi khoa, theo dõi sinh hiệu, kê đơn an toàn theo lứa tuổi |
| **Bác sĩ Chuyên khoa khác** | `bs_san_1`, `bs_mat_1`, ... | `Password@123` | Đầy đủ 8 chuyên khoa chính của phòng khám đa khoa |
| **Kỹ thuật viên phòng Lab (KTV)**| `ktv_1` | `Password@123` | Tiếp nhận chỉ định CLS, kiểm tra thanh toán, tải tối đa 10 ảnh kết quả |
| **Dược sĩ kho dược (DUOCSI)** | `duocsi_1` | `Password@123` | Quản lý danh mục thuốc, duyệt đơn thuốc, cấp phát thực tế trừ kho |
| **Bệnh nhân có BHYT (BENHNHAN)** | `0901234561` | `123456` | Có thẻ BHYT (hưởng giảm 80%), có tiền sử dị ứng thuốc Paracetamol |
| **Bệnh nhân không BHYT (BENHNHAN)**| `0901234562` | `123456` | Khám tự nguyện, dị ứng Penicillin, quét mã VietQR thanh toán viện phí |

> [!NOTE]
> **Quy trình Cưỡng chế đổi mật khẩu an toàn**: Khi Admin hoặc Lễ tân cấp lại mật khẩu cho một tài khoản, mật khẩu được gán về `123`. Khi tài khoản này đăng nhập, hệ thống sẽ tự động chuyển hướng đến `/force-change-password` bắt buộc nhập mật khẩu mới trước khi truy cập bất kỳ trang nào.

---

## Danh Mục Tính Năng Nghiệp Vụ Toàn Diện

### 1. Phân hệ Bệnh nhân (Patient Portal)
- **Hồ sơ sức khỏe 360°**: Quản lý thông tin định danh (CCCD 12 số, BHYT 10 số), chọn nhóm máu cơ bản và nhóm máu hiếm, tiền sử dị ứng và bệnh lý nền từ từ điển chuẩn hóa y khoa.
- **Đặt lịch khám 2 chiều thông minh**:
  - Chọn chuyên khoa và chọn ngày khám.
  - Lọc tương tác 2 chiều: Chọn bác sĩ trước thì các khung giờ bận bị làm mờ; chọn giờ khám trước thì các bác sĩ không có ca trực trùng giờ sẽ bị ẩn/làm mờ.
  - Hỗ trợ bấm lần 2 để bỏ chọn (Toggle Deselect) cực kỳ thuận tiện.
  - Chống đặt trùng giờ và chống đặt lịch ngoài ca làm việc.
- **Bệnh án điện tử EMR**: Xem chi tiết thanh tiến trình 5 bước khám thời gian thực, sinh hiệu, chẩn đoán ICD-10, đơn thuốc và ảnh lâm sàng.
- **Kết quả Cận lâm sàng & Đa ảnh**: Xem chi tiết kết quả xét nghiệm, kết luận cận lâm sàng kèm lưới xem trước đa ảnh chất lượng cao và Lightbox phóng to.
- **Hóa đơn viện phí & VietQR**: Minh bạch chi phí khám, xét nghiệm, thuốc; hiển thị rõ số tiền cấn trừ BHYT 80% và tự động tạo mã thanh toán VietQR chuẩn ngân hàng.
- **Hệ thống Thông báo**: Nút chuông thông báo dropdown hiển thị 10 thông báo mới nhất kèm âm thanh chuông báo Web Audio API; trang Thông báo riêng (`/patient/notifications`) hiển thị toàn bộ lịch sử theo từng tài khoản.

### 2. Phân hệ Bác sĩ & Khám chữa bệnh EMR
- **Quy trình khám EMR 5 bước liên hoàn**:
  1. *Khám lâm sàng*: Ghi nhận sinh hiệu, triệu chứng, tiền sử bệnh.
  2. *Chỉ định Cận lâm sàng*: Chọn xét nghiệm, chẩn đoán hình ảnh, nội soi.
  3. *Nhận kết quả CLS*: Theo dõi trạng thái hoàn tất từ phòng Lab, xem trực tiếp ảnh kết quả.
  4. *Kê đơn thuốc điện tử*: Tự động cảnh báo dị ứng thuốc thời gian thực từ từ điển danh mục; kiểm tra số lượng tồn kho trước khi kê đơn.
  5. *Kết luận ca khám*: Chốt mã ICD-10, dặn dò điều trị, khóa dữ liệu bệnh án.
- **Chuyển phiên ca khám Cận lâm sàng**: Bác sĩ lâm sàng chuyển phiên ca khám cho Bác sĩ/KTV chuyên trách thực hiện kỹ thuật mà không làm đứt đoạn quy trình.
- **Tải lên tối đa 10 ảnh lâm sàng**: Hỗ trợ kéo thả ảnh, lưới xem trước 2x2, tự động nén định dạng WebP (< 80KB).
- **Lọc ca khám cá nhân hóa**: Bộ lọc "Lịch khám của tôi" ưu tiên hiển thị các bệnh nhân được chỉ định cho bác sĩ đang đăng nhập.
- **Cài đặt Giá khám cá nhân**: Cho phép bác sĩ chủ động thiết lập đơn giá khám bệnh, hiển thị rõ ràng giá gốc và giá áp dụng BHYT.

### 3. Phân hệ Kỹ thuật viên Cận lâm sàng (Lab Portal)
- **Bàn làm việc phòng Lab**: Tiếp nhận chỉ định xét nghiệm và chẩn đoán hình ảnh theo thời gian thực.
- **Kiểm tra trạng thái đóng phí**: Kiểm tra xác nhận bệnh nhân đã thanh toán viện phí cận lâm sàng trước khi thực hiện dịch vụ kỹ thuật.
- **Nhập kết quả & Tải đa ảnh CĐHA**: Nhập kết luận, tải lên tối đa 10 ảnh kết quả (X-quang, Siêu âm, CT, Nội soi), tự động đồng bộ kết quả sang màn hình Bác sĩ và Bệnh nhân.

### 4. Phân hệ Dược sĩ & Kho Dược (Pharmacy Portal)
- **Quy trình cấp phát thuốc 3 bước an toàn**:
  - *Bước 1: Bệnh nhân lựa chọn*: Chọn "Mua tại viện" (sinh hóa đơn thuốc `HDT...`) hoặc "Mua ngoài viện" (không nợ tiền, không trừ kho).
  - *Bước 2: Thu ngân thu phí*: Lễ tân xác nhận thu tiền đơn thuốc, đơn chuyển trạng thái `Chờ nhận thuốc` (tuyệt đối chưa trừ kho).
  - *Bước 3: Dược sĩ cấp phát*: Dược sĩ kiểm tra đơn thuốc và bấm "Cấp phát thuốc" -> Lúc này kho dược mới thực tế trừ số lượng tồn kho.
- **Quản lý kho dược**: Theo dõi số lượng tồn kho, cảnh báo tồn kho tối thiểu, quản lý hạn sử dụng, hoạt chất, biệt dược.

### 5. Phân hệ Lễ tân & Thu ngân (Reception & Billing Portal)
- **Tiếp đón & Phân phòng**: Tiếp nhận bệnh nhân, kiểm tra thẻ BHYT, phân bổ vào các phòng khám chuyên khoa đang mở ca trực.
- **Thu Viện phí & Cấn trừ BHYT 80%**: Lập hóa đơn viện phí, tự động tính toán cấn trừ 80% BHYT đối với các dịch vụ khám và kỹ thuật thuộc phạm vi chi trả.
- **Tự duyệt ca trực**: Lễ tân được quyền tự đăng ký ca trực và hệ thống tự động duyệt ngay lập tức (`DA_DUYET`).
- **Quản lý Cẩm nang y tế**: Quyền đăng bài viết mới, chỉnh sửa, xóa và tải lên file CSV bài viết cẩm nang y khoa mẫu.

### 6. Phân hệ Quản trị viên (Admin Portal)
- **Quản trị tài khoản & Phân quyền RBAC**: Quản lý tài khoản toàn bộ nhân sự và người bệnh, kích hoạt / vô hiệu hóa tài khoản.
- **Cấp lại mật khẩu an toàn**: Sinh mật khẩu mặc định `123`, gắn cờ bắt buộc đổi mật khẩu ở lần đăng nhập tiếp theo.
- **Điều phối Ca trực thông minh (Staff Shifts)**: Hiển thị dạng khối trực quan, giới hạn tối đa 3 bác sĩ/khoa/ca, tự động nhận diện hết giờ làm việc; khi hủy ca trực bác sĩ thì tự động chuyển lịch hẹn về trạng thái chờ điều phối lại.
- **Sao lưu & Khôi phục CSDL SQL Server**: Tạo bản sao lưu `.bak`, tự động sao lưu mỗi 2 tiếng, tự động khôi phục bản sao lưu gần nhất khi khởi động ứng dụng.
- **Nhật ký Kiểm toán (Audit Log)**: Ghi vết toàn bộ hành động thêm, sửa, xóa, duyệt, đăng nhập, đổi mật khẩu kèm IP và thời gian.

### 7. Các Trang Công Khai Dành Cho Khách (Guest Pages)
- **Bảng giá & Dịch vụ y tế (`/pricing`)**: Liệt kê toàn bộ danh mục dịch vụ khám, kỹ thuật cận lâm sàng phân chia theo khoa, hiển thị minh bạch giá gốc và giá giảm BHYT.
- **Đội ngũ Bác sĩ (`/doctors`)**: Liệt kê toàn bộ bác sĩ theo từng chuyên khoa, hiển thị học vị, chức vụ, số điện thoại liên hệ (bảo mật không hiển thị tài khoản Admin).
- **Danh sách Chuyên khoa (`/departments`)**: Giới thiệu thông tin chi tiết, chức năng nhiệm vụ của từng khoa phòng.

---

## Hệ Thống Ràng Buộc Dữ Liệu Nghiêm Ngặt

Mọi dữ liệu đi vào hệ thống đều được thẩm định nghiêm ngặt tại [core/validators.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/core/validators.py):

| Dữ liệu kiểm tra | Ràng buộc kỹ thuật | Hàm xử lý |
| :--- | :--- | :--- |
| **Họ và tên** | Độ dài 2 - 100 ký tự. Chỉ chứa chữ cái tiếng Việt có dấu, chữ cái Latin và khoảng trắng đơn. Chặn tuyệt đối chữ số, ký tự đặc biệt (`@#$%^&*`). | `validate_name` |
| **Số thẻ BHYT** | Đúng 10 chữ số chuẩn theo Quyết định 1666/QĐ-BHXH của Bảo hiểm Xã hội Việt Nam. | `validate_bhyt` |
| **Căn cước công dân (CCCD)** | Đúng 12 chữ số theo chuẩn thẻ căn cước công dân gắn chip. Chống nhập chuỗi số giả lặp lại (`000000000000`). | `validate_cccd` |
| **Số điện thoại** | Đúng 10 chữ số, bắt đầu bằng các đầu số di động hợp lệ tại Việt Nam (`03, 05, 07, 08, 09`). | `validate_phone` |
| **Ngày sinh & Độ tuổi** | Chặn ngày sinh trong tương lai. Bệnh nhân từ 0 đến 130 tuổi; nhân viên y tế bắt buộc từ đủ 18 tuổi trở lên. | `validate_birth_date` |
| **Chỉ số sinh tồn lâm sàng** | Giới hạn sinh học: Mạch (30 - 250 bpm), Thân nhiệt (34.0 - 43.0 °C), Huyết áp tâm thu > Huyết áp tâm trương, SpO2 (50 - 100%), Nhịp thở (8 - 60 lần/phút). | `validate_vital_signs` |
| **Kho dược & Dịch vụ** | Đơn giá thuốc > 0, tồn kho >= 0, số lượng kê đơn >= 1. Đơn giá dịch vụ >= 0, tỷ lệ BHYT từ 0% đến 100%. | `validate_medicine_data` |

---

## Cơ Sở Dữ Liệu 27 Bảng Microsoft SQL Server

Hệ thống được thiết kế chuẩn hóa 3NF trên nền tảng Microsoft SQL Server:

1. `tai_khoan`: Thông tin đăng nhập, mật khẩu băm scrypt, cờ hồ sơ, cờ đổi mật khẩu.
2. `vai_tro`: Danh mục vai trò RBAC (ADMIN, LETAN, BACSI, DUOCSI, KTV, BENHNHAN).
3. `nhan_vien`: Hồ sơ lý lịch cán bộ y tế (họ tên, CCCD, ngày sinh, chức vụ, liên hệ).
4. `bac_si`: Thông tin chuyên khoa, học vị, phòng làm việc chính, giá khám cá nhân.
5. `benh_nhan`: Hồ sơ bệnh nhân 360°, mã BN, số BHYT, nhóm máu, tiền sử dị ứng, bệnh nền.
6. `chuyen_khoa`: Danh mục 8 chuyên khoa phòng khám.
7. `phong_kham`: Danh mục phòng khám và phòng chức năng cận lâm sàng.
8. `lich_hen`: Lịch hẹn khám bệnh, bác sĩ chỉ định, giờ hẹn, trạng thái xử lý.
9. `lich_lam_viec`: Ca trực nhân sự theo tuần (Sáng, Chiều, Tối), trạng thái phê duyệt.
10. `phieu_kham`: Bệnh án điện tử EMR, lý do khám, chẩn đoán ICD-10, ảnh lâm sàng, quy trình 5 bước.
11. `chi_so_sinh_ton`: Chỉ số sinh tồn lâm sàng (Mạch, Nhiệt độ, Huyết áp, SpO2, Nhịp thở, BMI).
12. `dich_vu`: Danh mục dịch vụ khám, kỹ thuật CLS và tỷ lệ thanh toán BHYT.
13. `phieu_chi_dinh`: Phiếu chỉ định cận lâm sàng do bác sĩ khởi tạo.
14. `chi_tiet_chi_dinh`: Chi tiết kỹ thuật CLS, kết quả xét nghiệm, kết luận, danh sách ảnh CĐHA.
15. `thuoc`: Kho dược, tên biệt dược, hoạt chất, hàm lượng, giá bán, số lượng tồn kho.
16. `don_thuoc`: Đơn thuốc điện tử, hình thức mua (tại viện / ngoài viện), trạng thái duyệt và cấp phát.
17. `chi_tiet_don_thuoc`: Chi tiết các loại thuốc trong đơn, số lượng kê, liều dùng, cách dùng.
18. `hoa_don`: Hóa đơn viện phí, tiền khám, tiền CLS, tiền thuốc, số tiền giảm trừ BHYT 80%.
19. `chi_tiet_hoa_don`: Các dòng mục chi phí chi tiết cấu thành hóa đơn.
20. `phan_hoi`: Đánh giá chất lượng dịch vụ, số sao hài lòng và nhận xét của người bệnh.
21. `hom_thu_gop_y`: Hòm thư tiếp nhận đóng góp ý kiến xây dựng phòng khám.
22. `bai_viet`: Cẩm nang y khoa, tin tức sức khỏe, quản lý bài đăng phân quyền.
23. `banner`: Quản lý hình ảnh trình chiếu quảng bá tại Trang chủ.
24. `thong_bao`: Thông báo in-app đa kênh, trạng thái đã đọc, liên kết điều hướng.
25. `lich_su_nhac_nho`: Nhật ký kiểm soát việc gửi thông báo nhắc lịch tự động.
26. `lich_su_sao_luu`: Lịch sử các phiên sao lưu và khôi phục CSDL SQL Server (.bak).
27. `audit_log`: Nhật ký kiểm toán an toàn hệ thống, theo dõi mọi tác vụ nhạy cảm.

---

## Bộ Kiểm Thử Tự Động (Unit Tests)

Dự án sở hữu bộ kiểm thử tự động toàn diện bao phủ 100% các luồng nghiệp vụ cốt lõi:
- **Kiểm tra khởi động an toàn (`test_startup_safety.py`)**: Đảm bảo khởi động ứng dụng không xóa dữ liệu, kiểm tra tính độc lập và idempotent của hệ thống.
- **Kiểm tra tính năng nâng cấp (`test_upgraded_features.py`)**: Kiểm tra ma trận đặt lịch tương tác 2 chiều, tiện ích lấy backup mới nhất và dọn dẹp backup cũ, cảnh báo dị ứng thời gian thực, nén ảnh WebP, Dark mode Midnight Slate.

Chạy lệnh kiểm thử:
```bash
python -m unittest tests.test_startup_safety tests.test_upgraded_features
```
Kết quả mong đợi:
```text
Ran 39 tests in 6.5s ... OK (100% Passing)
```

---

## Bản Quyền và Thông Tin Đồ Án

* **Đề tài**: Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare (Khóa luận tốt nghiệp Đại học).
* **Đơn vị đào tạo**: Trường Đại học Công Thương TP. Hồ Chí Minh (HUIT).
* **Công nghệ chủ đạo**: Python 3.10+, Flask, Microsoft SQL Server (100% T-SQL), TailwindCSS, Web Audio API.
