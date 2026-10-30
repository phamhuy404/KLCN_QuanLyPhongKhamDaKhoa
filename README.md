# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare

> Toàn hệ thống và kiểm thử tích hợp dùng MSSQL/pyodbc: [cấu hình test MSSQL an toàn](docs/mssql_test_environment.md). Thiếu cấu hình xác nhận thì tích hợp SKIP; mock pass không phải bằng chứng MSSQL pass.

> Khởi tạo app, chạy Website và kiểm thử cô lập: xem [hướng dẫn startup an toàn](docs/startup_safety.md).
> Import/tạo app không còn tự cập nhật schema hoặc chạy worker; `python app.py` vẫn là lệnh chạy Website.
> Chỉ chạy test mới bằng `python -B -m unittest discover -s tests -p test_startup_safety.py -v`.
> Không chạy toàn bộ test cũ bên dưới trên database vận hành.
> Xác thực, quyền sở hữu hồ sơ, cấu hình `SECRET_KEY` và quyền nhân viên còn cần xác nhận:
> xem [hướng dẫn kiểm tra bảo mật](docs/security_access.md).
> Dữ liệu chưa đo, công bố kết quả và bảo vệ ảnh mới/cũ: [hướng dẫn dữ liệu và ảnh bệnh án](docs/clinical_media.md).
> Validation ca, đặt/đổi/hủy và kiểm thử cạnh tranh: [hướng dẫn lịch an toàn](docs/scheduling_safety.md).
> Liên kết lịch hẹn, khám trực tiếp và chống hoàn tất lặp: [hướng dẫn EMR](docs/emr_workflow.md).
> Khóa đơn/hóa đơn, nhập tồn và lịch sử dược: [quy tắc an toàn dược](docs/pharmacy_safety.md).
> Quyền thu tiền, hướng dẫn thanh toán và đối chiếu giá: [an toàn hóa đơn](docs/billing_safety.md).
> Auth Flutter/Web chung tài khoản, token và test: [hợp đồng Mobile v1](docs/mobile_auth_contract.md).

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server%20(100%25%20T--SQL)-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20Web%20Audio-teal.svg)]()
[![Dark Mode](https://img.shields.io/badge/Dark%20Mode-Midnight%20Slate-indigo.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-57%2F57%20Passing%20(100%25)-brightgreen.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo kiến trúc MVC (Model - View - Controller), vận hành chuyên biệt 100% trên nền tảng **Microsoft SQL Server**. Hệ thống số hóa hoàn chỉnh quy trình khám chữa bệnh khép kín: Tiếp đón và đặt lịch khám đa kênh, phân công ca trực thông minh đa vai trò, bệnh án điện tử EMR 5 bước liên hoàn kèm đa ảnh chuẩn hóa (tối đa 10 ảnh, lưới xem trước 2x2, phóng to Lightbox), chuyển phiên khám cận lâm sàng, cảnh báo dị ứng thuốc thời gian thực, quản lý kho dược và cấp phát thuốc 3 bước an toàn, hóa đơn viện phí tự động cấn trừ BHYT 80%, giao diện Dark Mode Midnight Slate bảo vệ thị giác, cổng thông tin bệnh nhân 360° và hồ sơ cá nhân nội bộ riêng biệt cho nhân sự y tế.

## Cấu Trúc Thư Mục Chuẩn (Project Structure)

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Điểm khởi chạy chính của máy chủ Flask
├── config.py                      # Cấu hình tập trung (Microsoft SQL Server, Google Maps, Secret Key)
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
├── README.md                      # Tài liệu tổng quan và hướng dẫn dự án
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
│   ├── home_controller.py         #   - Trang chủ (random bác sĩ, random đánh giá), bài viết cẩm nang
│   ├── patient_controller.py      #   - Cổng bệnh nhân: Hồ sơ 360°, đơn thuốc, hóa đơn, đặt lịch, phản hồi
│   ├── admin_controller.py        #   - Phân hệ quản trị: Tiếp đón, EMR, CLS, kho dược, viện phí, hồ sơ cá nhân
│   └── api_controller.py          #   - RESTful API: Đăng ký ca trực, tiếp nhận, EMR, xuất thuốc, viện phí
│
├── models/                        # [MODEL] Tương tác CSDL SQL Server và ràng buộc nghiệp vụ (13 Models)
│   ├── user_model.py              #   - Tài khoản, phân quyền RBAC, hồ sơ nhân viên, cấp lại mật khẩu
│   ├── appointment_model.py       #   - Đặt lịch, lọc theo bác sĩ, chống đặt trùng giờ, chặn đổi lịch đã xong
│   ├── medical_record_model.py    #   - EMR 5 bước liên hoàn, chỉ định CLS, kiểm tra tồn kho và kê đơn
│   ├── pharmacy_model.py          #   - Quản lý kho dược, duyệt đơn 3 bước, cấp phát thực tế trừ kho
│   ├── billing_model.py           #   - Viện phí, khấu trừ BHYT 80%, nhận diện hóa đơn thuốc HDT
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, tiền sử dị ứng, cận lâm sàng, nhóm máu
│   ├── schedule_model.py          #   - Lịch ca trực: Lễ tân tự duyệt, Admin ẩn, giới hạn 3 BS/khoa/ca
│   ├── notification_model.py      #   - Hệ thống thông báo tức thì, popups real-time, chuông Web Audio
│   ├── banner_model.py            #   - Quản lý slider quảng bá trang chủ (CRUD và sắp xếp)
│   ├── article_model.py           #   - Tin tức, cẩm nang y khoa (phân quyền chỉ Lễ tân và Admin được đăng)
│   ├── clinic_model.py            #   - Dịch vụ y tế, thống kê dashboard phòng khám
│   ├── feedback_model.py          #   - Đánh giá chất lượng và phản hồi của người bệnh (lọc >= 4 sao)
│   └── backup_model.py            #   - Sao lưu, khôi phục CSDL SQL Server (.bak)
│
├── static/                        # [STATIC] Tài nguyên tĩnh giao diện
│   ├── css/custom.css             #   - Custom styles, hệ thống Dark Mode Midnight Slate toàn diện
│   ├── js/main.js                 #   - Toast notification, Polling, Schedule interaction, Dropzone
│   ├── js/theme.js                #   - Quản lý chuyển đổi chế độ Sáng / Tối (Dark Mode) và lưu localStorage
│   ├── img/                       #   - Hình ảnh bài viết, icon thương hiệu
│   ├── images/default-avatar.png  #   - Default avatar fallback
│   └── uploads/                   #   - Tệp đính kèm người dùng: kết quả CLS, ảnh lâm sàng EMR, banner
│
├── templates/                     # [VIEW] 45 Giao diện Jinja2 HTML và TailwindCSS
│   ├── layouts/                   #   - Layout dùng chung (base.html, footer.html)
│   ├── auth/                      #   - Giao diện đăng nhập, đăng ký, cưỡng chế đổi mật khẩu (123 -> mới)
│   ├── patient/                   #   - Cổng bệnh nhân: Dashboard, đặt lịch, EMR, xét nghiệm, hóa đơn, profile
│   ├── admin/                     #   - Phân hệ quản trị: EMR 5 bước, CLS Lab, kho dược, hồ sơ của tôi, ca trực
│   └── home.html                  #   - Trang chủ hiển thị ngẫu nhiên bác sĩ và đánh giá thực tế
│
└── tests/                         # [TESTS] 7 Tệp kiểm thử tự động (57/57 Tests Passing)
    ├── test_data_constraints.py   #   - Ràng buộc regex: họ tên, BHYT 10 số, CCCD 12 số, SĐT, sinh hiệu
    ├── test_doctor_and_prescription_workflow.py # - Luồng tạo bác sĩ, ca trực và cấp phát thuốc 3 bước
    ├── test_features_6_to_10.py   #   - Nghiệp vụ lõi: đặt lịch, cấn trừ BHYT 80%, EMR, đa ảnh
    ├── test_final_comprehensive.py #  - Toàn diện EMR, cảnh báo dị ứng thời gian thực, phân quyền RBAC
    ├── test_force_change_password.py # - Cấp lại mật khẩu 123 và cưỡng chế đổi mật khẩu lần đầu
    ├── test_system_features.py    #   - Thông báo, bài viết, banner, backup CSDL
    └── test_upgraded_features.py  #   - Dark mode Midnight Slate, kiểm toán, nén ảnh WebP
```

## Hướng Dẫn Cài Đặt và Khởi Chạy Đầy Đủ

### 1. Yêu cầu môi trường
* **Hệ điều hành**: Windows 10/11 hoặc Windows Server 64-bit.
* **Python**: Phiên bản 3.9 trở lên (Khuyến nghị Python 3.10 hoặc 3.11).
* **Cơ sở dữ liệu**: Microsoft SQL Server 2017, 2019, 2022 hoặc Microsoft SQL Server Express (Bản miễn phí).
* **Driver kết nối**: Microsoft ODBC Driver 17 for SQL Server (hoặc Driver 18).

### 2. Các bước khởi chạy chi tiết

#### Bước 1: Cài đặt thư viện Python
Mở PowerShell hoặc Command Prompt tại thư mục dự án và chạy:
```bash
pip install -r requirements.txt
```

#### Bước 2: Cấu hình kết nối SQL Server
Mở tệp [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py) và xác nhận thông số:
```python
DB_ENGINE = 'sqlserver'

SQLSERVER_CONFIG = {
    'server': 'localhost',             # Hoặc: '.\SQLEXPRESS', 'localhost\SQLEXPRESS'
    'database': 'quan_ly_phong_kham',  # Tên cơ sở dữ liệu
    'driver': 'ODBC Driver 17 for SQL Server',
    'trusted_connection': 'yes',       # Dùng Windows Authentication
    'TrustServerCertificate': 'yes'    # Tránh lỗi chứng chỉ trên SQL Server 2022
}
```
*Lưu ý: Nếu dùng tài khoản sa, đổi `'trusted_connection': 'no'` và bổ sung `'uid': 'sa'`, `'pwd': 'mat_khau_cua_ban'`.*

#### Bước 3: Khởi tạo Cơ sở dữ liệu và nạp dữ liệu sạch
Chạy script nạp tự động:
```bash
python scratch/seed_database.py
```
Script sẽ tự động kết nối SQL Server, khởi tạo cơ sở dữ liệu `quan_ly_phong_kham`, tạo 27 bảng dữ liệu chuẩn và nạp sẵn 69 tài khoản mẫu đầy đủ các vai trò.

*(Hoặc mở file [database/cosodulieu.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/database/cosodulieu.sql) trong SQL Server Management Studio và nhấn Execute F5).*

#### Bước 4: Khởi chạy máy chủ Web Flask
```bash
python app.py
```
Khi màn hình hiển thị:
```text
* Running on http://127.0.0.1:5000
```
Truy cập ứng dụng tại: `http://127.0.0.1:5000`

### 3. Chạy bộ kiểm thử tự động toàn diện (57/57 Tests OK)
```bash
python -m unittest discover -s tests
```
Kết quả mong đợi: `Ran 57 tests ... OK` (100% Pass).

## Danh Sách Tài Khoản Mẫu Đăng Nhập Theo Vai Trò

Hệ thống được thiết lập sẵn 69 tài khoản đại diện cho đầy đủ 6 nhóm vai trò trong quy trình phòng khám:

| Vai trò | Tên đăng nhập | Mật khẩu mặc định | Quyền hạn và Nghiệp vụ chính |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (ADMIN)** | `admin` | `admin123` | Toàn quyền hệ thống, tạo tài khoản y tế, cấp lại mật khẩu cho nhân sự, duyệt lịch làm việc, đăng bài viết, sao lưu CSDL (.bak) |
| **Lễ tân và Thu ngân (LETAN)** | `letan_1` | `Password@123` | Tiếp đón người bệnh, phân bổ phòng khám, đặt lịch tại quầy, tự đăng ký và tự duyệt ca trực, đăng bài viết, thu viện phí |
| **Bác sĩ Nội khoa (BACSI)** | `bs_noi_1` | `Password@123` | Khám lâm sàng EMR 5 bước, tải tối đa 10 ảnh, ra chỉ định CLS, cảnh báo dị ứng, xem kết quả CLS, kê đơn, cài đặt giá khám cá nhân |
| **Bác sĩ Ngoại khoa (BACSI)** | `bs_ngoai_1` | `Password@123` | Khám ngoại khoa, chỉ định chẩn đoán hình ảnh, xử lý EMR, theo dõi lịch khám cá nhân |
| **Bác sĩ Nhi khoa (BACSI)** | `bs_nhi_1` | `Password@123` | Khám chuyên khoa nhi, theo dõi sinh hiệu trẻ em, kê đơn điện tử |
| **Kỹ thuật viên phòng Lab (KTV)**| `ktv_1` | `Password@123` | Xem chỉ định CLS, kiểm tra trạng thái viện phí CLS, nhập kết quả, tải lên tối đa 10 ảnh CĐHA/Nội soi |
| **Dược sĩ kho dược (DUOCSI)** | `duocsi_1` | `Password@123` | Quản lý kho thuốc (giá bán, tồn kho, hạn dùng), duyệt đơn thuốc, cấp phát thực tế trừ kho |
| **Bệnh nhân có BHYT (BENHNHAN)** | `0901234561` | `123456` | Có thẻ BHYT (hưởng khấu trừ 80%), dị ứng Paracetamol, xem EMR 5 bước, chọn mua thuốc viện/ngoài |
| **Bệnh nhân không BHYT (BENHNHAN)**| `0901234562` | `123456` | Không có BHYT, dị ứng Penicillin, lịch sử khám, thanh toán VietQR |

*Quy trình cấp lại mật khẩu: Khi Admin hoặc Tiếp tân bấm Cấp lại mật khẩu cho bất kỳ tài khoản nào, mật khẩu được đưa về `123`. Khi người dùng đăng nhập lần đầu với mật khẩu này, hệ thống tự động cưỡng chế chuyển đến trang `/force-change-password` để thiết lập mật khẩu mới an toàn.*

## Danh Mục Tính Năng Nghiệp Vụ Toàn Diện Đang Có

### 1. Phân hệ Bệnh nhân (Patient Portal)
- **Dashboard 360°**: Thẻ thành viên VIP điện tử, cảnh báo đợt khám gần nhất, phím tắt tiện ích sức khỏe (đơn thuốc, kết quả xét nghiệm, hóa đơn, tài khoản).
- **Đặt lịch trực tuyến**: Chọn chuyên khoa, chọn bác sĩ với thẻ cân đối trực quan, chọn ca khám và giờ hẹn, chống đặt trùng giờ.
- **Bệnh án điện tử EMR**: Hiển thị đồng bộ thanh tiến trình 5 bước khám thời gian thực, chi tiết sinh hiệu, triệu chứng, chẩn đoán ICD-10, đơn thuốc và ảnh lâm sàng.
- **Kết quả Cận lâm sàng**: Xem chi tiết kết quả xét nghiệm và chẩn đoán hình ảnh, hỗ trợ xem đa ảnh phóng to Lightbox modal chuẩn HD.
- **Hóa đơn và Viện phí**: Minh bạch chi phí khám, cận lâm sàng, tiền thuốc; hiển thị rõ số tiền cấn trừ BHYT 80% và số tiền thanh toán thực tế, tích hợp mã VietQR tự động.
- **Hồ sơ sức khỏe cá nhân**: Cập nhật thông tin định danh (CCCD 12 số, BHYT 10 số), chọn nhóm máu cơ bản và tùy chọn nhóm máu biến thể hiếm (tạm ẩn thông minh), chọn đa mục dị ứng và bệnh lý nền từ từ điển chuẩn có tìm kiếm gần đúng (fuzzy search).
- **Đóng góp ý kiến và Phản hồi**: Đánh giá 5 sao và viết nhận xét sau khám; các phản hồi tích cực (>= 4 sao) được chọn ngẫu nhiên hiển thị lên Trang chủ.
- **Hệ thống Thông báo**: Nhận thông báo nhắc lịch, tiếp nhận, có kết quả xét nghiệm, đơn thuốc đã sẵn sàng kèm âm thanh chuông báo (Web Audio API).

### 2. Phân hệ Bác sĩ và Khám chữa bệnh EMR (Doctor and Clinical Portal)
- **Quy trình Khám EMR 5 bước liên hoàn**:
  1. *Khám lâm sàng*: Ghi nhận sinh hiệu, lý do khám, triệu chứng, tiền sử.
  2. *Chỉ định Cận lâm sàng*: Chọn dịch vụ xét nghiệm, CĐHA, nội soi.
  3. *Thực hiện và Nhận kết quả CLS*: Theo dõi trạng thái hoàn thành từ phòng Lab, xem ảnh CĐHA.
  4. *Kê đơn thuốc*: Tìm kiếm kho dược, tự động cảnh báo dị ứng thuốc thời gian thực, kiểm tra tồn kho.
  5. *Kết luận và Hoàn tất ca khám*: Chốt mã bệnh ICD-10, hướng dẫn điều trị, lưu bệnh án vĩnh viễn và khóa dữ liệu.
- **Chuyển phiên khám Cận lâm sàng**: Bác sĩ khám lâm sàng có thể chuyển phiên ca khám cho Bác sĩ/KTV phụ trách cận lâm sàng. Bác sĩ tiếp nhận xem tiếp toàn bộ tiến trình và thực hiện chỉ định.
- **Quản lý đa ảnh lâm sàng**: Hỗ trợ kéo thả hoặc click chọn tải lên tối đa 10 ảnh, bố cục lưới xem trước 2x2 cuộn được, click phóng to Lightbox sắc nét.
- **Thống kê Lịch khám cá nhân hóa**: Bộ lọc "Lịch khám của tôi" ưu tiên hiển thị lịch hẹn được giao cho bác sĩ đang đăng nhập, hiển thị tên bác sĩ phụ trách trên từng thẻ lịch.
- **Đặt lịch tại quầy khóa quyền**: Khi bác sĩ thao tác đặt lịch tái khám tại quầy, hệ thống tự động khóa cứng thông tin bác sĩ và chuyên khoa của chính họ, ngăn chọn nhầm sang bác sĩ khác.
- **Hồ sơ Bác sĩ và Cài đặt giá khám**: Quản lý thông tin học vị, chuyên khoa, kinh nghiệm; nút "Cài đặt giá khám" hiển thị rõ giá gốc chưa trừ BHYT và giá áp dụng BHYT.

### 3. Phân hệ Kỹ thuật viên Cận lâm sàng (Lab / Diagnostics Portal)
- **Bàn làm việc phòng Lab**: Tiếp nhận danh sách bệnh nhân có chỉ định cận lâm sàng theo thời gian thực.
- **Kiểm soát trạng thái đóng phí**: Kiểm tra bệnh nhân đã thanh toán phí CLS trước khi tiến hành thực hiện kỹ thuật.
- **Nhập kết quả và Tải đa ảnh CĐHA**: Nhập kết luận xét nghiệm, tải lên tối đa 10 ảnh chẩn đoán hình ảnh (X-quang, Siêu âm, CT, Nội soi), tự động nén ảnh WebP.
- **Cập nhật tức thời tiến trình EMR**: Sau khi lưu kết quả CLS, trạng thái được cập nhật ngay lập tức sang màn hình Bác sĩ điều trị và Cổng bệnh nhân.

### 4. Phân hệ Dược sĩ và Quản lý Kho Dược (Pharmacy Portal)
- **Quy trình cấp phát thuốc 3 bước an toàn**:
  - *Bước 1: Bệnh nhân lựa chọn mua thuốc*: Chọn Mua tại viện (sinh đơn thuốc viện `HDT...`) hoặc Mua ngoài viện (khóa đơn, không nợ, không trừ kho).
  - *Bước 2: Lễ tân / Thu ngân duyệt đơn và thu phí*: Sau khi duyệt và thu phí, đơn chuyển trạng thái `Chờ nhận thuốc` (tuyệt đối chưa trừ kho).
  - *Bước 3: Dược sĩ cấp phát thực tế*: Dược sĩ kiểm tra đơn thuốc và bấm "Cấp phát thuốc" -> Lúc này kho dược mới bị trừ số lượng tồn thực tế.
- **Quản lý danh mục kho thuốc**: Tên biệt dược, hoạt chất, hàm lượng, đường dùng, đơn vị tính, đơn giá bán, số lượng tồn kho, cảnh báo tồn kho tối thiểu.

### 5. Phân hệ Lễ tân và Thu ngân (Reception and Billing Portal)
- **Tiếp đón và Phân buồng khám**: Tiếp nhận bệnh nhân mới, đăng ký hồ sơ, phân bổ vào các phòng khám chuyên khoa còn chỗ.
- **Quản lý Viện phí và Thu ngân**: Lập hóa đơn viện phí, tự động tính toán cấn trừ 80% BHYT đối với tiền khám và danh mục kỹ thuật thuộc phạm vi chi trả.
- **Phân công và Tự duyệt ca trực**: Lễ tân được quyền tự đăng ký ca trực và hệ thống tự động phê duyệt ngay lập tức (`DA_DUYET`).
- **Phân quyền Đăng bài cẩm nang**: Lễ tân có quyền đăng bài mới, chỉnh sửa, xóa và tải file CSV bài viết mẫu lên hệ thống.

### 6. Phân hệ Quản trị viên (Admin Portal)
- **Quản trị tài khoản và Phân quyền RBAC**: Quản lý 69+ tài khoản nhân sự và người bệnh, kích hoạt / vô hiệu hóa tài khoản.
- **Cấp lại mật khẩu an toàn**: Sinh mật khẩu mặc định `123`, gắn cờ `phai_doi_mat_khau = 1` kích hoạt luồng cưỡng chế đổi mật khẩu.
- **Quản trị Lịch trực thông minh (Staff Shifts)**:
  - Hiển thị ca trực theo dạng khối chữ nhật dọc (hình trụ thanh mảnh, hiện đại).
  - Di chuột (hover) mở rộng ngang hiển thị nhanh tên các bác sĩ cùng khoa.
  - Nhấp chuột mở rộng toàn bộ danh sách nhân sự phân chia theo từng chuyên khoa và khu vực rõ ràng.
  - Tự động nhận diện hết giờ làm việc để cập nhật trạng thái hoạt động thực tế.
  - Phê duyệt ca trực hàng loạt, kiểm soát giới hạn tối đa 3 bác sĩ/chuyên khoa/ca trực.
  - Khi duyệt hủy ca trực bác sĩ, tự động chuyển toàn bộ lịch hẹn liên quan về trạng thái `Chờ tiếp nhận` và gửi thông báo nhắc Lễ tân điều phối lại.
- **Sao lưu và Khôi phục CSDL SQL Server**: Thực thi sao lưu trọn gói tệp `.bak` và khôi phục an toàn trực tiếp từ giao diện web.
- **Nhật ký Kiểm toán (Audit Log)**: Ghi nhận vết toàn bộ các hành động thêm, sửa, xóa, duyệt, đổi mật khẩu kèm địa chỉ IP và thời gian.

### 7. Giao diện và Trải nghiệm Người dùng (UI / UX Enhancements)
- **Dark Mode Midnight Slate toàn diện**:
  - Tông màu nền tối `#0b0f19` sâu lắng, bề mặt card `#131b2e` và sub-card `#182236`, loại bỏ triệt để lỗi "hố đen" ngược phân cấp.
  - Toàn bộ huy hiệu y tế (Medical, Emerald, Amber, Rose, Blue, Purple) sử dụng nền mờ 16% và chữ dạ quang rõ nét.
  - Banner thông báo xanh ngọc, hộp Hotline khẩn cấp dark slate, nút hành động tối tinh tế.
  - Tích hợp bộ lọc ban đêm cho bản đồ Google Maps.
  - Chuyển đổi mượt mà bằng nút bấm trực quan trên header mọi trang, ghi nhớ trạng thái qua `localStorage`.
- **Âm thanh Thông báo (Notification Chime)**: Tự động phát âm thanh chuông trong trẻo qua Web Audio API khi có thông báo mới mà không cần nạp tệp âm thanh ngoài.
- **Tối ưu hóa hình ảnh WebP**: Tự động nén tất cả hình ảnh tải lên thành định dạng WebP với dung lượng dưới 80KB, đảm bảo tốc độ tải trang nhanh và tiết kiệm dung lượng lưu trữ.

## Hệ Thống Ràng Buộc Dữ Liệu Chặt Chẽ (Strict Validation Engine)

Tất cả dữ liệu nhập vào hệ thống đều đi qua bộ lọc kiểm tra nghiêm ngặt tại [core/validators.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/core/validators.py):

| Trường thông tin | Quy tắc và Ràng buộc kỹ thuật | Hàm kiểm tra |
| :--- | :--- | :--- |
| **Họ và tên** | Bắt buộc từ 2 đến 100 ký tự. Chỉ chứa chữ cái tiếng Việt có dấu, chữ cái Latin và khoảng trắng đơn. Tuyệt đối không chứa chữ số, không chứa ký tự lạ hay ký tự đặc biệt (`@#$%^&*`). | `validate_name` |
| **Mã số thẻ BHYT** | Đúng 10 chữ số (theo Quyết định 1666/QĐ-BHXH của BHXH Việt Nam). Tuyệt đối không chứa chữ cái, không chứa ký tự lạ. | `validate_bhyt` |
| **Căn cước công dân (CCCD)** | Đúng 12 chữ số theo chuẩn thẻ chip Bộ Công An. Chống nhập dãy số lặp vô lý (`111111111111`). | `validate_cccd` |
| **Số điện thoại** | Đúng 10 chữ số, bắt đầu bằng các đầu số di động chuẩn Việt Nam (`03, 05, 07, 08, 09`). | `validate_phone` |
| **Ngày sinh và Độ tuổi** | Chặn ngày sinh trong tương lai. Độ tuổi bệnh nhân từ 0 đến 130 tuổi; nhân sự y tế bắt buộc từ đủ 18 tuổi trở lên. | `validate_birth_date` |
| **Chỉ số sinh tồn lâm sàng (EMR)**| Giá trị y khoa thực tế: Mạch (30 - 250 nhịp/phút), Thân nhiệt (34.0 - 43.0 °C), Huyết áp tâm thu > Huyết áp tâm trương (50-250 / 30-150 mmHg), SpO2 (50 - 100%), Nhịp thở (8 - 60 lần/phút). | `validate_vital_signs` |
| **Kho dược và Bảng giá** | Đơn giá thuốc > 0, tồn kho >= 0, số lượng kê trong đơn >= 1. Đơn giá dịch vụ y tế >= 0, tỷ lệ BHYT từ 0% đến 100%. | `validate_medicine_data` |
| **Mật khẩu an toàn** | Tối thiểu 6 ký tự, hỗ trợ chữ cái, chữ số và ký tự đặc biệt; mã hóa scrypt chuẩn mật mã học. | `validate_password` |

## Danh Sách 27 Bảng Cơ Sở Dữ Liệu Microsoft SQL Server

Hệ thống được thiết kế chuẩn hóa 3NF trên nền tảng Microsoft SQL Server với 27 bảng dữ liệu quan hệ:

1. `tai_khoan`: Quản lý tài khoản người dùng, mã hóa mật khẩu scrypt, cờ `da_hoan_thien_ho_so`, cờ `phai_doi_mat_khau`.
2. `vai_tro`: 6 vai trò hệ thống (ADMIN, LETAN, BACSI, DUOCSI, KTV, BENHNHAN).
3. `nhan_vien`: Hồ sơ lý lịch cán bộ, nhân viên y tế (họ tên, ngày sinh, CCCD, chức vụ).
4. `bac_si`: Thông tin chuyên khoa, học vị, phòng làm việc, giá khám, kinh nghiệm.
5. `benh_nhan`: Hồ sơ bệnh nhân 360°, mã BN, số BHYT, nhóm máu, dị ứng, bệnh lý nền.
6. `chuyen_khoa`: Danh mục chuyên khoa (Nội, Ngoại, Nhi, Mắt, Tai Mũi Họng, Sản, RHM, Chẩn đoán hình ảnh).
7. `phong_kham`: Danh mục phòng khám và phòng kỹ thuật chức năng.
8. `lich_hen`: Lịch hẹn khám chữa bệnh, trạng thái xử lý, bác sĩ phụ trách.
9. `lich_lam_viec`: Ca trực nhân sự (Sáng, Chiều, Tối), trạng thái duyệt, khóa giới hạn số lượng.
10. `phieu_kham`: Bệnh án điện tử EMR, lý do khám, chẩn đoán ICD-10, ảnh lâm sàng, trạng thái 5 bước.
11. `chi_so_sinh_ton`: Chỉ số sinh tồn lâm sàng (Mạch, Huyết áp, Nhiệt độ, SpO2, Nhịp thở, BMI).
12. `dich_vu`: Bảng giá dịch vụ khám, kỹ thuật cận lâm sàng và tỷ lệ chi trả BHYT.
13. `phieu_chi_dinh`: Phiếu chỉ định cận lâm sàng do bác sĩ khởi tạo.
14. `chi_tiet_chi_dinh`: Chi tiết kỹ thuật CLS, kết quả xét nghiệm, kết luận, danh sách ảnh CĐHA.
15. `thuoc`: Kho dược, tên biệt dược, hoạt chất, hàm lượng, tồn kho, giá bán, hạn sử dụng.
16. `don_thuoc`: Đơn thuốc điện tử, hình thức mua (tại viện / ngoài viện), trạng thái duyệt và cấp phát.
17. `chi_tiet_don_thuoc`: Danh sách thuốc trong đơn, số lượng, liều dùng, cách dùng, đơn giá.
18. `hoa_don`: Hóa đơn viện phí khám bệnh, tiền CLS, tiền thuốc, số tiền khấu trừ BHYT.
19. `chi_tiet_hoa_don`: Các dòng mục chi phí chi tiết cấu thành hóa đơn.
20. `phan_hoi`: Đánh giá chất lượng dịch vụ, số sao hài lòng và nhận xét của người bệnh.
21. `hom_thu_gop_y`: Hòm thư tiếp nhận đóng góp ý kiến xây dựng phòng khám.
22. `bai_viet`: Cẩm nang y khoa, tin tức sức khỏe, quản lý bài đăng phân quyền.
23. `banner`: Quản lý hình ảnh trình chiếu quảng bá tại Trang chủ.
24. `thong_bao`: Thông báo in-app đa kênh, trạng thái đã đọc, liên kết điều hướng.
25. `lich_su_nhac_nho`: Nhật ký kiểm soát việc gửi thông báo nhắc lịch tự động.
26. `lich_su_sao_luu`: Lịch sử các phiên sao lưu và khôi phục CSDL SQL Server (.bak).
27. `audit_log`: Nhật ký kiểm toán an toàn hệ thống, theo dõi mọi tác vụ nhạy cảm.

## Bản Quyền và Tác Giả

* **Đề tài**: Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare (Khóa luận tốt nghiệp Đại học).
* **Đơn vị**: Trường Đại học Công Thương TP. Hồ Chí Minh (HUIT).
* **Nền tảng**: Python 3.10+, Flask, Microsoft SQL Server (100% T-SQL), TailwindCSS.
