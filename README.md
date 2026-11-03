# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare (HIS & EMR)

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server%20(100%25%20T--SQL)-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20Web%20Audio-teal.svg)]()
[![Dark Mode](https://img.shields.io/badge/Dark%20Mode-Midnight%20Slate-indigo.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo kiến trúc MVC (Model - View - Controller), vận hành 100% trên nền tảng **Microsoft SQL Server**. Hệ thống số hóa hoàn chỉnh quy trình y tế khép kín: Tiếp đón, tiếp nhận nhanh sảnh chờ bằng giọng nói Web Speech API, phân bổ bác sĩ chống xung đột giờ khám, bệnh án điện tử EMR 5 bước liên hoàn kèm đa ảnh chuẩn hóa (WebP, lightbox), điều phối cận lâm sàng, cảnh báo dị ứng thời gian thực, quản lý kho dược và cấp phát thuốc 3 bước trừ kho tự động, viện phí cấn trừ BHYT 80%, thanh toán tự động VietQR, tự động sao lưu định kỳ 2 giờ và tự động nạp bản sao lưu gần nhất khi khởi động, cùng giao diện Dark Mode Midnight Slate toàn diện.

---

## Mục Lục
1. [Cấu Trúc Thư Mục Dự Án](#cấu-trúc-thư-mục-dự-án)
2. [Hướng Dẫn Cài Đặt và Khởi Chạy](#hướng-dẫn-cài-đặt-và-khởi-chạy)
3. [Cơ Chế Sao Lưu và Phục Hồi CSDL Tự Động](#cơ-chế-sao-lưu-và-phục-hồi-csdl-tự-động)
4. [Ma Trận Phân Quyền Hệ Thống (RBAC)](#ma-trận-phân-quyền-hệ-thống-rbac)
5. [Toàn Bộ Danh Sách Tài Khoản Hệ Thống (71 Tài Khoản)](#toàn-bộ-danh-sách-tài-khoản-hệ-thống-71-tài-khoản)
   - [5.1 Quản Trị Viên (ADMIN)](#51-quản-trị-viên-admin---1-tài-khoản)
   - [5.2 Nhân Viên Lễ Tân & Thu Ngân (LETAN)](#52-nhân-viên-lễ-tân--thu-ngân-letan---5-tài-khoản)
   - [5.3 Bác Sĩ Chuyên Khoa (BACSI)](#53-bác-sĩ-chuyên-khoa-bacsi---35-tài-khoản)
   - [5.4 Dược Sĩ & Quản Lý Kho Dược (DUOCSI)](#54-dược-sĩ--quản-lý-kho-dược-duocsi---5-tài-khoản)
   - [5.5 Kỹ Thuật Viên Cận Lâm Sàng (KTV)](#55-kỹ-thuật-viên-cận-lâm-sàng-ktv---5-tài-khoản)
   - [5.6 Bệnh Nhân (BENHNHAN)](#56-khách-hàng--bệnh-nhân-benhnhan---20-tài-khoản)
6. [Danh Mục Tính Năng Nghiệp Vụ Toàn Diện](#danh-mục-tính-năng-nghiệp-vụ-toàn-diện)
7. [Hệ Thống Ràng Buộc Dữ Liệu & Điền Thông Tin Linh Hoạt](#hệ-thống-ràng-buộc-dữ-liệu--điền-thông-tin-linh-hoạt)
8. [Cơ Sở Dữ Liệu 27 Bảng Microsoft SQL Server](#cơ-sở-dữ-liệu-27-bảng-microsoft-sql-server)
9. [Bản Quyền và Thông Tin Đồ Án](#bản-quyền-và-thông-tin-đồ-án)

---

## Cấu Trúc Thư Mục Dự Án

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Khởi chạy Flask Server (nạp bản .bak gần nhất & chạy scheduler)
├── config.py                      # Cấu hình SQL Server, SMTP, Auto-backup, Google Maps
├── requirements.txt               # Thư viện Python phụ thuộc
├── README.md                      # Tài liệu tổng quan và cẩm nang vận hành
│
├── database/                      # Cơ sở dữ liệu Microsoft SQL Server
│   ├── cosodulieu.sql             #   - Kịch bản DDL và DML trọn gói Microsoft SQL Server (100% T-SQL)
│   ├── migrations/                #   - Các bản script nâng cấp CSDL
│   └── legacy_bridge.py           #   - Module tương thích ngược
│
├── docs/                          # Tài liệu vận hành, quy trình và kiểm thử
│   ├── huong_dan_chay.md          #   - Hướng dẫn cài đặt, cấu hình SQL Server và khởi chạy chi tiết
│   ├── kiem_thu_thu_cong_toan_dien.md # - Cẩm nang kiểm thử thủ công từng bước cho nhóm
│   └── QUY_TRINH_NGHIEP_VU_HE_THONG.md # - Tài liệu nghiệp vụ y tế và cơ chế cấn trừ chuẩn
│
├── data/                          # Từ điển danh mục chuẩn và Mock data
│   ├── catalogs/                  #   - Từ điển danh mục: nhóm máu, biến thể, dị ứng, tiền sử bệnh
│   │   ├── nhom_mau.txt           #     - 8 nhóm máu cơ bản ABO và Rh (+/-)
│   │   ├── bien_the_nhom_mau.txt  #     - 12 biến thể nhóm máu hiếm (Weak D, Partial D, Bombay, ...)
│   │   ├── di_ung.txt             #     - 19 nhóm dị ứng thuốc và thực phẩm phổ biến
│   │   └── tien_su_benh.txt       #     - 21 bệnh lý nền mạn tính (Tim mạch, Huyết áp, Đái tháo đường, ...)
│   └── articles_data.py           #   - Dữ liệu cẩm nang y khoa mẫu
│
├── backups/                       # Chứa các bản sao lưu .bak tự động và thủ công của SQL Server
│
├── core/                          # Tầng hạ tầng và dịch vụ nghiệp vụ dùng chung
│   ├── database.py                #   - UnifiedCursor và kết nối pyodbc Microsoft SQL Server
│   ├── validators.py              #   - Bộ lọc kiểm tra dữ liệu, chống ký tự lạ, regex tiếng Việt
│   ├── security.py                #   - Quản trị phiên đăng nhập, hashing scrypt, kiểm tra phân quyền RBAC
│   ├── scheduling.py              #   - Ma trận giờ khám, phát hiện xung đột và tự động hủy lịch trùng
│   ├── billing_policy.py          #   - Thuật toán cấn trừ viện phí BHYT 80% và nhận diện hóa đơn HDT
│   ├── emr_workflow.py            #   - Quy trình khám 5 bước, phiên khám chuyển tiếp và chỉ định CLS
│   └── catalog.py                 #   - Bộ nạp từ điển danh mục chuẩn y khoa
│
├── controllers/                   # Tầng điều khiển (Controllers / Blueprints)
│   ├── auth_controller.py         #   - Đăng nhập, đăng ký, đăng xuất, cưỡng chế đổi mật khẩu
│   ├── home_controller.py         #   - Trang chủ, bảng giá, danh sách bác sĩ, chuyên khoa mở rộng
│   ├── patient_controller.py      #   - Cổng bệnh nhân: Hồ sơ 360°, đơn thuốc, hóa đơn, đặt lịch, phản hồi
│   ├── admin_controller.py        #   - Phân hệ quản trị: Tiếp đón, EMR, CLS, kho dược, viện phí, nhân sự
│   ├── api_controller.py          #   - RESTful API: Đặt lịch, ma trận giờ, chấm công, xuất thuốc, sao lưu
│   └── mobile_auth_controller.py  #   - API xác thực dành cho ứng dụng di động Flutter
│
├── models/                        # Tầng mô hình dữ liệu (13 Models kết nối SQL Server)
│   ├── user_model.py              #   - Tài khoản, phân quyền RBAC, hồ sơ nhân viên, cấp lại mật khẩu
│   ├── appointment_model.py       #   - Đặt lịch, ma trận giờ khám, phân công bác sĩ, hủy tự động lịch trùng
│   ├── medical_record_model.py    #   - EMR 5 bước liên hoàn, chỉ định CLS, kiểm tra tồn kho và kê đơn
│   ├── pharmacy_model.py          #   - Quản lý kho dược, duyệt đơn 3 bước, cấp phát thực tế trừ kho
│   ├── billing_model.py           #   - Viện phí, khấu trừ BHYT 80%, nhận diện hóa đơn thuốc HDT
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, tiền sử dị ứng, cận lâm sàng, nhóm máu
│   ├── schedule_model.py          #   - Ca trực, thống kê giờ công, chấm công theo tháng, lịch sử 10 tuần
│   ├── notification_model.py      #   - Thông báo tức thì, popups real-time, chuông Web Audio
│   ├── banner_model.py            #   - Quản lý slider quảng bá trang chủ
│   ├── article_model.py           #   - Tin tức, cẩm nang y khoa
│   ├── clinic_model.py            #   - Dịch vụ y tế, thống kê dashboard phòng khám
│   ├── feedback_model.py          #   - Đánh giá chất lượng và phản hồi của người bệnh
│   └── backup_model.py            #   - Sao lưu, tự động phục hồi CSDL SQL Server (.bak), scheduler 2 giờ
│
├── static/                        # Tài nguyên tĩnh giao diện
│   ├── css/custom.css             #   - Custom styles, Dark Mode Midnight Slate, hoạt ảnh slideInRight
│   ├── js/main.js                 #   - Toast notification, Polling, Web Speech Audio, Dropzone
│   ├── js/theme.js                #   - Quản lý chuyển đổi chế độ Sáng / Tối và lưu localStorage
│   ├── img/                       #   - Hình ảnh bài viết, icon thương hiệu
│   └── uploads/                   #   - Kết quả xét nghiệm CLS, ảnh lâm sàng EMR, banner
│
└── templates/                     # Giao diện Jinja2 HTML và TailwindCSS
    ├── layouts/                   #   - Layout dùng chung (base.html, header, footer Google Maps tự nhiên)
    ├── auth/                      #   - Giao diện đăng nhập, đăng ký, hoàn thiện hồ sơ lần đầu
    ├── patient/                   #   - Cổng bệnh nhân: Dashboard, đặt lịch 4 màu, bệnh án, hóa đơn
    └── admin/                     #   - Phân hệ quản trị: Tiếp đón, EMR 5 bước, CLS, kho dược, chấm công
```

---

## Hướng Dẫn Cài Đặt và Khởi Chạy

### 1. Yêu cầu môi trường
* **Hệ điều hành**: Windows 10/11 hoặc Windows Server 64-bit.
* **Python**: Phiên bản 3.9 trở lên (Khuyến nghị Python 3.10 hoặc 3.11).
* **Cơ sở dữ liệu**: Microsoft SQL Server 2017, 2019, 2022 hoặc Microsoft SQL Server Express (Bản miễn phí).
* **Driver ODBC**: Microsoft ODBC Driver 17 for SQL Server (hoặc Driver 18).

### 2. Các bước cài đặt chi tiết

**Bước 1: Mở Terminal tại thư mục gốc dự án**
```bash
cd "d:\baitap\Khoa Luan\KLCN_QuanLyPhongKhamDaKhoa"
```

**Bước 2: Cài đặt các thư viện phụ thuộc**
```bash
pip install -r requirements.txt
```

**Bước 3: Cấu hình kết nối CSDL trong [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py)**
Kiểm tra cấu hình chuỗi kết nối SQL Server:
```python
DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost',             # Hoặc localhost\SQLEXPRESS
    'database': 'QL_PHONGKHAM_DAKHOA',
    'trusted_connection': 'yes',       # Sử dụng Windows Authentication
}
```

**Bước 4: Khởi chạy máy chủ**
```bash
python app.py
```
> Khi khởi chạy, hệ thống sẽ:
> 1. Tự động kiểm tra thư mục `backups/`, tự động nạp bản sao lưu `.bak` gần nhất vào SQL Server nếu cần đồng bộ.
> 2. Kích hoạt bộ lập lịch sao lưu tự động chạy ngầm mỗi 2 tiếng.
> 3. Khởi động Web Server tại: **http://127.0.0.1:5000**

---

## Cơ Chế Sao Lưu và Phục Hồi CSDL Tự Động

1. **Tự động sao lưu định kỳ mỗi 2 tiếng**:
   - Chạy trên một luồng nền độc lập (`threading.Thread`), định kỳ gọi lệnh T-SQL `BACKUP DATABASE` nguyên bản của Microsoft SQL Server.
   - Bản sao lưu được lưu trữ tại thư mục `backups/` theo định dạng chuẩn: `backup_sqlserver_YYYYMMDD_HHMMSS.bak`.
2. **Tự động nạp bản sao lưu mới nhất khi khởi động**:
   - Khi chạy `python app.py`, hàm `BackupModel.get_latest_backup()` sẽ quét thư mục `backups/`.
   - Nếu phát hiện bản sao lưu mới nhất, hệ thống tự động đưa các phiên kết nối về `SINGLE_USER WITH ROLLBACK IMMEDIATE` và tiến hành `RESTORE DATABASE`, sau đó trả lại chế độ `MULTI_USER`.
3. **Sao lưu thủ công & Quản lý bản sao lưu**:
   - Quản trị viên có thể truy cập giao diện `/admin/backups` để tạo bản sao lưu tức thì, tải file `.bak` về máy hoặc phục hồi lại bất kỳ thời điểm nào chỉ với 1 cú click chuột.

---

## Ma Trận Phân Quyền Hệ Thống (RBAC)

Hệ thống thiết lập 6 vai trò người dùng với quyền hạn độc lập và kiểm soát truy cập nghiêm ngặt:

| Mã Vai Trò | Tên Vai Trò | Mô Tả & Quyền Hạn Nghiệp Vụ |
|:---|:---|:---|
| **ADMIN** | Quản Trị Viên | Toàn quyền quản trị hệ thống: Quản lý tài khoản, phân vai trò, xem audit log, sao lưu/phục hồi CSDL, thống kê tổng quan doanh thu, quản lý danh mục khoa/phòng/dịch vụ, quản lý ca trực và chấm công toàn viện. |
| **LETAN** | Lễ Tân / Thu Ngân | Tiếp đón bệnh nhân tại sảnh, phân phòng khám, điều phối & duyệt lịch hẹn, giải quyết xung đột lịch trùng, thu ngân viện phí (tiền mặt/VietQR), quản lý bài viết y khoa, xem bảng chấm công toàn nhân viên. |
| **BACSI** | Bác Sĩ Chuyên Khoa | Khám bệnh EMR 5 bước liên hoàn, ra chỉ định cận lâm sàng, kê đơn thuốc điện tử kèm cảnh báo tương tác/dị ứng, hẹn lịch tái khám mới (tự động duyệt), đăng ký ca trực và theo dõi giờ công cá nhân. |
| **DUOCSI** | Dược Sĩ / Quản Lý Kho | Quản lý kho dược phẩm, duyệt đơn thuốc mua tại viện, cấp phát thuốc thực tế trừ tồn kho tự động, nhập kho, kiểm kê thẻ kho và lịch sử xuất nhập thuốc. |
| **KTV** | Kỹ Thuật Viên CLS | Tiếp nhận chỉ định xét nghiệm & CĐHA, nhập kết quả chỉ số xét nghiệm, tải lên ảnh chẩn đoán hình ảnh (X-Quang, Siêu âm, Nội soi), duyệt kết quả gửi về cho Bác sĩ điều trị. |
| **BENHNHAN** | Khách Hàng / Bệnh Nhân | Cổng thông tin bệnh nhân: Tra cứu lịch sử khám bệnh EMR, xem kết quả xét nghiệm, theo dõi đơn thuốc (chọn mua tại viện hoặc tự mua ngoài), tra cứu hóa đơn viện phí, đặt lịch hẹn trực tuyến 4 trạng thái màu. |

---

## Toàn Bộ Danh Sách Tài Khoản Hệ Thống (71 Tài Khoản)

Dưới đây là danh sách chi tiết toàn bộ **71 tài khoản** thực tế đang hoạt động trong hệ thống, được phân loại rõ ràng theo từng vai trò nghiệp vụ (100% dữ liệu sạch, đã dọn bỏ hoàn toàn các tài khoản test):

### 5.1 Quản Trị Viên (ADMIN) - 1 tài khoản
* **Mật khẩu mặc định**: `admin123`

| ID | Username | Họ và Tên | Mã Nhân Viên | Số Điện Thoại | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|
| 1 | `admin` | Quản Trị Viên Hệ Thống | NV001 | 0999999999 | `admin123` |

---

### 5.2 Nhân Viên Lễ Tân & Thu Ngân (LETAN) - 5 tài khoản
* **Mật khẩu mặc định**: `Password@123`

| ID | Username | Họ và Tên | Mã Nhân Viên | Số Điện Thoại | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|
| 2 | `letan_1` | Nguyễn Thị Lan | NV_LT01 | 0908111221 | `Password@123` |
| 3 | `letan_2` | Trần Thu Huyền | NV_LT02 | 0908111222 | `Password@123` |
| 4 | `letan_3` | Lê Phương Thảo | NV_LT03 | 0908111223 | `Password@123` |
| 5 | `letan_4` | Phạm Ngọc Bích | NV_LT04 | 0908111224 | `Password@123` |
| 6 | `letan_5` | Đỗ Thu Hà | NV_LT05 | 0908111225 | `Password@123` |

---

### 5.3 Bác Sĩ Chuyên Khoa (BACSI) - 35 tài khoản
* **Mật khẩu mặc định**: `Password@123`
* **Phân bổ**: 35 Bác sĩ lâm sàng phụ trách 7 chuyên khoa mũi nhọn (mỗi khoa 5 bác sĩ, 100% có ca trực và lịch sử khám bệnh EMR):

| ID | Username | Họ và Tên | Chuyên Khoa | Phòng Khám Chính | Số Điện Thoại | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|:---|
| 17 | `bs_noi_1` | BS. Trần Minh Quân | Khoa Nội Tổng Quát | Phòng Khám Nội 1 | 0912111001 | `Password@123` |
| 18 | `bs_noi_2` | BS. Phạm Anh Tuấn | Khoa Nội Tổng Quát | Phòng Khám Nội 2 | 0912111002 | `Password@123` |
| 19 | `bs_noi_3` | BS. Nguyễn Thu Trang | Khoa Nội Tổng Quát | Phòng Khám Nội 3 | 0912111003 | `Password@123` |
| 20 | `bs_noi_4` | BS. Vũ Quốc Hưng | Khoa Nội Tổng Quát | Phòng Khám Nội 4 | 0912111004 | `Password@123` |
| 21 | `bs_noi_5` | BS. Lê Hoài An | Khoa Nội Tổng Quát | Phòng Khám Nội 5 | 0912111005 | `Password@123` |
| 22 | `bs_ngoai_1` | BS. Nguyễn Hoàng Nam | Khoa Ngoại Tổng Quát | Phòng Khám Ngoại 1 | 0912222001 | `Password@123` |
| 23 | `bs_ngoai_2` | BS. Phan Thanh Phong | Khoa Ngoại Tổng Quát | Phòng Khám Ngoại 2 | 0912222002 | `Password@123` |
| 24 | `bs_ngoai_3` | BS. Đinh Văn Hùng | Khoa Ngoại Tổng Quát | Phòng Khám Ngoại 3 | 0912222003 | `Password@123` |
| 25 | `bs_ngoai_4` | BS. Hoàng Đức Lâm | Khoa Ngoại Tổng Quát | Phòng Khám Ngoại 4 | 0912222004 | `Password@123` |
| 26 | `bs_ngoai_5` | BS. Trịnh Văn Long | Khoa Ngoại Tổng Quát | Phòng Khám Ngoại 5 | 0912222005 | `Password@123` |
| 27 | `bs_nhi_1` | BS. Lê Thị Mai | Khoa Nhi | Phòng Khám Nhi 1 | 0912333001 | `Password@123` |
| 28 | `bs_nhi_2` | BS. Dương Diệu Linh | Khoa Nhi | Phòng Khám Nhi 2 | 0912333002 | `Password@123` |
| 29 | `bs_nhi_3` | BS. Ngô Đình Quân | Khoa Nhi | Phòng Khám Nhi 3 | 0912333003 | `Password@123` |
| 30 | `bs_nhi_4` | BS. Phạm Thúy Hằng | Khoa Nhi | Phòng Khám Nhi 4 | 0912333004 | `Password@123` |
| 31 | `bs_nhi_5` | BS. Đỗ Tuấn Nghĩa | Khoa Nhi | Phòng Khám Nhi 5 | 0912333005 | `Password@123` |
| 32 | `bs_rhm_1` | BS. Hoàng Đức Duy | Khoa Răng Hàm Mặt | Phòng Khám RHM 1 | 0912444001 | `Password@123` |
| 33 | `bs_rhm_2` | BS. Đoàn Minh Khang | Khoa Răng Hàm Mặt | Phòng Khám RHM 2 | 0912444002 | `Password@123` |
| 34 | `bs_rhm_3` | BS. Vũ Hồng Loan | Khoa Răng Hàm Mặt | Phòng Khám RHM 3 | 0912444003 | `Password@123` |
| 35 | `bs_rhm_4` | BS. Mai Văn Trọng | Khoa Răng Hàm Mặt | Phòng Khám RHM 4 | 0912444004 | `Password@123` |
| 36 | `bs_rhm_5` | BS. Nguyễn Bích Thủy | Khoa Răng Hàm Mặt | Phòng Khám RHM 5 | 0912444005 | `Password@123` |
| 37 | `bs_san_1` | BS. Đặng Thu Hương | Khoa Sản - Phụ Khoa | Phòng Khám Sản Phụ 1 | 0912555001 | `Password@123` |
| 38 | `bs_san_2` | BS. Trần Kiều Nga | Khoa Sản - Phụ Khoa | Phòng Khám Sản Phụ 2 | 0912555002 | `Password@123` |
| 39 | `bs_san_3` | BS. Nguyễn Thanh Huyền | Khoa Sản - Phụ Khoa | Phòng Khám Sản Phụ 3 | 0912555003 | `Password@123` |
| 40 | `bs_san_4` | BS. Bùi Thị Minh Tâm | Khoa Sản - Phụ Khoa | Phòng Khám Sản Phụ 4 | 0912555004 | `Password@123` |
| 41 | `bs_san_5` | BS. Lê Tuyết Lan | Khoa Sản - Phụ Khoa | Phòng Khám Sản Phụ 5 | 0912555005 | `Password@123` |
| 42 | `bs_tmh_1` | BS. Võ Thanh Bình | Khoa Tai Mũi Họng | Phòng Khám TMH 1 | 0912666001 | `Password@123` |
| 43 | `bs_tmh_2` | BS. Hoàng Quốc Tuấn | Khoa Tai Mũi Họng | Phòng Khám TMH 2 | 0912666002 | `Password@123` |
| 44 | `bs_tmh_3` | BS. Nguyễn Thị Thục Anh | Khoa Tai Mũi Họng | Phòng Khám TMH 3 | 0912666003 | `Password@123` |
| 45 | `bs_tmh_4` | BS. Trương Hoài Nam | Khoa Tai Mũi Họng | Phòng Khám TMH 4 | 0912666004 | `Password@123` |
| 46 | `bs_tmh_5` | BS. Chu Đức Cảnh | Khoa Tai Mũi Họng | Phòng Khám TMH 5 | 0912666005 | `Password@123` |
| 47 | `bs_mat_1` | BS. Đỗ Viết Thắng | Khoa Mắt | Phòng Khám Mắt 1 | 0912777001 | `Password@123` |
| 48 | `bs_mat_2` | BS. Lê Khánh Linh | Khoa Mắt | Phòng Khám Mắt 2 | 0912777002 | `Password@123` |
| 49 | `bs_mat_3` | BS. Nguyễn Hữu Đạt | Khoa Mắt | Phòng Khám Mắt 3 | 0912777003 | `Password@123` |
| 50 | `bs_mat_4` | BS. Phạm Hồng Nhung | Khoa Mắt | Phòng Khám Mắt 4 | 0912777004 | `Password@123` |
| 51 | `bs_mat_5` | BS. Vũ Văn Hải | Khoa Mắt | Phòng Khám Mắt 5 | 0912777005 | `Password@123` |

---

### 5.4 Dược Sĩ & Quản Lý Kho Dược (DUOCSI) - 5 tài khoản
* **Mật khẩu mặc định**: `Password@123`

| ID | Username | Họ và Tên | Mã Nhân Viên | Số Điện Thoại | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|
| 7 | `duocsi_1` | Dược sĩ Phạm Hoàng Minh | NV_DS01 | 0908222331 | `Password@123` |
| 8 | `duocsi_2` | Dược sĩ Nguyễn Thị Kim Oanh | NV_DS02 | 0908222332 | `Password@123` |
| 9 | `duocsi_3` | Dược sĩ Vũ Đình Trọng | NV_DS03 | 0908222333 | `Password@123` |
| 10 | `duocsi_4` | Dược sĩ Hoàng Thanh Trúc | NV_DS04 | 0908222334 | `Password@123` |
| 11 | `duocsi_5` | Dược sĩ Trần Văn Phúc | NV_DS05 | 0908222335 | `Password@123` |

---

### 5.5 Kỹ Thuật Viên Cận Lâm Sàng (KTV) - 5 tài khoản
* **Mật khẩu mặc định**: `Password@123`

| ID | Username | Họ và Tên | Mã Nhân Viên | Số Điện Thoại | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|
| 12 | `ktv_1` | KTV. Võ Anh Đức | NV_KTV01 | 0908333441 | `Password@123` |
| 13 | `ktv_2` | KTV. Hoàng Văn Cường | NV_KTV02 | 0908333442 | `Password@123` |
| 14 | `ktv_3` | KTV. Đặng Mỹ Linh | NV_KTV03 | 0908333443 | `Password@123` |
| 15 | `ktv_4` | KTV. Bùi Quốc Tuấn | NV_KTV04 | 0908333444 | `Password@123` |
| 16 | `ktv_5` | KTV. Lê Thùy Trang | NV_KTV05 | 0908333445 | `Password@123` |

---

### 5.6 Khách Hàng / Bệnh Nhân (BENHNHAN) - 20 tài khoản

#### Nhóm 10 Bệnh Nhân Tiêu Biểu & Đã Có Lịch Sử Khám Bệnh Đầy Đủ
* **Mật khẩu**: `123456`

| ID | Username / SĐT | Họ và Tên Bệnh Nhân | Mã BN | Ghi Chú Hồ Sơ | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|
| 52 | `hoangbaonam` / `0901234561` | Hoàng Bảo Nam | BN0001 | Đầy đủ BHYT, nhóm máu O+, dị ứng | `123456` |
| 53 | `0901234562` | Trần Thị Thu Hà | BN0002 | Đầy đủ BHYT, nhóm máu A+ | `123456` |
| 54 | `0901234563` | Nguyễn Văn Hùng | BN0003 | Tiền sử bệnh Tăng huyết áp | `123456` |
| 55 | `0901234564` | Lê Minh Anh | BN0004 | Nhóm máu B+, có người thân | `123456` |
| 56 | `0901234565` | Phạm Đức Trọng | BN0005 | Đầy đủ thông tin cá nhân | `123456` |
| 57 | `0901234566` | Đỗ Thị Bích Ngân | BN0006 | Có BHYT đúng tuyến | `123456` |
| 58 | `0901234567` | Vũ Đình Khang | BN0007 | Có người thân liên hệ | `123456` |
| 59 | `0901234568` | Bùi Tuyết Mai | BN0008 | Tiền sử dị ứng thức ăn | `123456` |
| 60 | `0901234569` | Đặng Quốc Bảo | BN0009 | Nhóm máu AB+ | `123456` |
| 61 | `0901234570` | Phan Mỹ Duyên | BN0010 | Đầy đủ thông tin | `123456` |

#### Nhóm 10 Bệnh Nhân Mở Rộng (Thông Tin Khuyết Thiếu Ngẫu Nhiên Hợp Lệ)
* **Mật khẩu**: `BenhNhan@123`

| ID | Username / SĐT | Họ và Tên Bệnh Nhân | Mã BN | Đặc Điểm Thông Tin Hồ Sơ | Mật Khẩu |
|:--:|:---|:---|:---|:---|:---|
| 154 | `0981122334` | Lê Hoàng Long | BN2609024 | Khuyết BHYT, Nhóm máu, Người thân (Lịch chờ tiếp nhận #LH2609101) | `BenhNhan@123` |
| 155 | `0972233445` | Vũ Thị Bích Ngọc | BN2609025 | Có BHYT, khuyết Nhóm máu, Người thân (Lịch chờ tiếp nhận #LH2609102) | `BenhNhan@123` |
| 156 | `0963344556` | Đặng Quốc Bảo | BN2609026 | Có Nhóm máu O+, khuyết CCCD, BHYT, Người thân (Lịch hẹn #LH2609103 Đã duyệt) | `BenhNhan@123` |
| 157 | `0944455667` | Phạm Thanh Thảo | BN2609027 | Khuyết BHYT, Nhóm máu, Người thân (Lịch hẹn #LH2609104 Đã hủy do trùng giờ) | `BenhNhan@123` |
| 158 | `0935566778` | Trịnh Đình Trọng | BN2609028 | Có Người thân (Vợ), khuyết BHYT, Nhóm máu | `BenhNhan@123` |
| 159 | `0926677889` | Hoàng Mỹ Duyên | BN2609029 | Có BHYT, khuyết CCCD, Nhóm máu, Người thân | `BenhNhan@123` |
| 160 | `0917788990` | Bùi Hải Đăng | BN2609030 | Có Tên người thân (Bố), khuyết SĐT người thân, BHYT, Nhóm máu | `BenhNhan@123` |
| 161 | `0908899001` | Nguyễn Khánh Vy | BN2609031 | Khuyết CCCD, BHYT, Nhóm máu, Người thân | `BenhNhan@123` |
| 162 | `0989900112` | Mai Văn Khiêm | BN2609032 | Có CCCD, khuyết BHYT, Nhóm máu, Người thân | `BenhNhan@123` |
| 163 | `0970011223` | Đỗ Thị Kim Chi | BN2609033 | Có Nhóm máu A+, khuyết CCCD, BHYT, Người thân | `BenhNhan@123` |

---

## Danh Mục Tính Năng Nghiệp Vụ Toàn Diện

### 1. Phân Hệ Đặt Lịch Khám & Phát Hiện Xung Đột Thông Minh
* **Ma trận khung giờ 4 màu sắc trực quan**:
  - **Màu Xanh Lá (Available)**: Khung giờ còn trống, bác sĩ đang trong ca trực.
  - **Màu Vàng (Pending)**: Khung giờ đang có bệnh nhân khác đặt chờ duyệt. Bệnh nhân vẫn được phép gửi yêu cầu nhưng hệ thống hiển thị banner cảnh báo khả năng bị hủy nếu lịch kia được duyệt trước.
  - **Màu Đỏ (Booked)**: Khung giờ đã được duyệt chính thức hoặc đã đủ số lượng, khóa không cho đặt.
  - **Màu Xám (Off Duty)**: Bác sĩ ngoài ca trực.
* **Cơ chế tự động hủy lịch trùng (Conflict Auto-Cancellation)**:
  - Khi Tiếp tân hoặc Admin duyệt hoặc phân bác sĩ cho 1 lịch hẹn, hệ thống tự động tìm và chuyển trạng thái toàn bộ các lịch hẹn khác bị trùng ngày giờ của bác sĩ đó sang `Đã hủy`.
  - Tự động gửi thông báo in-app giải thích rõ ràng lý do hủy kèm đường link dẫn bệnh nhân quay lại chọn giờ khám khác.
* **Tự động gán phòng khám theo ca trực**:
  - Nếu bệnh nhân chọn "Để bệnh viện tự phân bác sĩ", Tiếp tân/Admin dễ dàng chọn bác sĩ chuyên khoa và duyệt ngay trong modal điều phối. Phòng khám tự động liên kết với phòng trực của bác sĩ trong ca đó.

### 2. Trang Xem Chuyên Khoa Mở Rộng Kèm Giá Từng Loại Khám
* Truy cập tại: `/chuyen-khoa` (hoặc `/departments`).
* Dưới mỗi chuyên khoa, ngoài danh sách phòng khám và đội ngũ bác sĩ, hiển thị phân khu riêng biệt **"Các Loại Khám & Dịch Vụ Kỹ Thuật Chuyên Sâu"**:
  - Tên dịch vụ hiển thị rõ ràng, không bị rút ngắn.
  - Thẻ badge phân loại nghiệp vụ: Khám chuyên khoa, Khám bệnh, Thủ thuật, Thăm dò chức năng, Xét nghiệm, CĐHA.
  - Đơn giá niêm yết công khai (VD: `200.000 đ`, `250.000 đ`).
  - Tỷ lệ chi trả BHYT (Hỗ trợ 80% BHYT hoặc Tự nguyện).

### 3. Phân Hệ Quản Lý Nhân Sự, Lịch Trực & Thống Kê Giờ Công
* Truy cập tại: `/admin/staff`.
* **Điều hướng lịch trực trong quá khứ & tương lai linh hoạt**:
  - Giao diện thời khóa biểu lưới (Timetable Grid) tích hợp thanh điều hướng với dropdown chọn tuần nhanh lùi từ tuần -8 (giữa tháng 09/2026) đến tuần +2 trong tương lai, kết hợp nút điều hướng `< Tuần trước` / `Tuần sau >`.
  - Nút bấm `Chi tiết ngày` trên từng cột ngày của Grid giúp chuyển ngay sang bảng chi tiết được lọc đúng ngày đó.
* **Bảng danh sách ca trực phân chia nhóm theo từng ngày**:
  - Chế độ bảng chi tiết tự động nhóm các ca trực theo từng ngày với dải tiêu đề nổi bật: `Thứ 2, Thứ 3, ..., Chủ nhật • Ngày DD/MM/YYYY` kèm huy hiệu đếm số ca trực trong ngày (VD: `3 ca trực`).
  - Hỗ trợ nút bấm nhanh `Cả tuần này` và dropdown chọn tuần trực tiếp ngay trên thanh công cụ của bảng.
* **Thống kê chuyên sâu**:
  - Số giờ công thực tế đã làm trong kỳ (`gio_cong_da_lam_ky`).
  - Số giờ công được duyệt trong kỳ (`tong_gio_duyet_ky`).
  - Tổng số giờ công tích lũy (`tong_gio_cong_tich_luy`).
  - Số ca khám bệnh đã hoàn thành trong kỳ (`so_ca_kham_hoan_thanh_ky`).
  - Tổng số ca khám tích lũy (`tong_ca_kham_hoan_thanh`).
* **Dữ liệu lịch trực thực tế dày dặn**: Hơn 5.500 ca trực được duyệt (`DA_DUYET`), 30 ca chờ duyệt (`CHO_DUYET`), 15 ca xin hủy (`CHO_HUY`) có lý do thực tế và 25 ca đã duyệt hủy (`DA_HUY`) phân bổ liên tục từ 15/09/2026 đến nay.
* **Phân quyền xem**:
  - Nhân viên chỉ xem được của chính mình.
  - Tiếp tân và Admin có quyền xem của mình và xem toàn bộ 50 cán bộ nhân viên y tế của phòng khám.

### 4. Bệnh Án Điện Tử EMR 5 Bước Liên Hoàn & Ràng Buộc Thời Gian Khám
* Khám bệnh chuyên khoa 5 bước: (1) Khám lâm sàng & Dấu hiệu sinh tồn -> (2) Chỉ định cận lâm sàng -> (3) Kết quả CLS & Chẩn đoán hình ảnh -> (4) Chẩn đoán ICD-10 & Kê đơn thuốc -> (5) Hướng điều trị & Hẹn tái khám.
* **Ràng buộc thời gian khám bệnh chặt chẽ**:
  - **Chặn khám trước ngày**: Nếu lịch hẹn có ngày khám trong tương lai, hệ thống chặn mở giao diện EMR từ cả trang Danh sách lịch hẹn và trang Bệnh án điện tử, đồng thời hiển thị thông báo lỗi rõ ràng.
  - **Xác nhận khám trước lượt / ngoài giờ trong ngày**: Nếu lịch hẹn diễn ra trong ngày hiện tại nhưng chưa đến giờ hẹn, hệ thống bật hộp thoại thông báo hỏi ý kiến Bác sĩ có muốn tiếp nhận khám sớm / khám ngoài giờ cho bệnh nhân không trước khi mở ca khám.
* Hẹn tái khám mới: Tự động sinh lịch hẹn mới hoàn toàn, trạng thái `Đã duyệt` sẵn, không đè lên lịch cũ, đồng thời gửi thông báo tức thì cho bệnh nhân.

### 5. Quản Lý Dược Phẩm & Cấp Phát Thuốc Khép Kín
* Cấp phát 3 bước: (1) Bác sĩ kê đơn -> (2) Tiếp tân duyệt & Thu ngân thanh toán hóa đơn thuốc HDT -> (3) Dược sĩ kiểm tra tồn kho và xác nhận cấp phát, tự động trừ kho nguyên tử.
* **Đầy đủ 2 luồng xử lý đơn thuốc linh hoạt**:
  - **Mua tại bệnh viện**: Tự động sinh hóa đơn thuốc `HDT`, cấn trừ theo quy chế, chuyển đến Dược sĩ duyệt và cấp thuốc tại quầy thuốc bệnh viện.
  - **Tự mua ngoài**: Chuyển trạng thái sang `Mua ngoài`, lưu trữ toàn bộ thông tin kê đơn trên Cổng thông tin hồ sơ sức khỏe bệnh nhân (`/patient/records`) để người bệnh chủ động mua tại các nhà thuốc bên ngoài.

---

## Hệ Thống Ràng Buộc Dữ Liệu & Điền Thông Tin Linh Hoạt

* **Hồ sơ bệnh nhân không ép buộc**:
  - Khi đăng ký tài khoản hoặc đăng nhập lần đầu, chỉ bắt buộc: Họ và tên, Ngày sinh, Giới tính.
  - Các trường: BHYT, CCCD, Nhóm máu, Người thân, Dị ứng, Tiền sử bệnh **cho phép để trống hoàn toàn**, có thể bổ sung sau khi đến khám.
* **Tránh tải lại trang (No-Scroll Jump)**: Các thao tác chuyển bước, lọc dữ liệu, chọn ca trực được tối ưu bằng AJAX/Fetch API, không làm cuộn nhảy vị trí trang.
* **Google Maps trong Dark Mode**: Khóa cố định màu sắc tự nhiên cho iframe bản đồ trong chế độ Dark Mode (`filter: none !important`), tránh bị đảo màu âm bản gây khó nhìn.
* **Hoạt ảnh chuyển trang**: Tích hợp animation `h2tSlideInRight` tạo hiệu ứng trượt ngang hiện đại khi chuyển giữa các màn hình.

---

## Cơ Sở Dữ Liệu 27 Bảng Microsoft SQL Server

Hệ thống được thiết kế theo chuẩn cơ sở dữ liệu y tế với 27 bảng liên kết chặt chẽ:
1. `tai_khoan`: Quản lý tài khoản đăng nhập (hashing scrypt, RBAC).
2. `vai_tro`: Danh mục vai trò (ADMIN, LETAN, BACSI, DUOCSI, KTV, BENHNHAN).
3. `nhan_vien`: Hồ sơ nhân sự y tế toàn phòng khám.
4. `bac_si`: Hồ sơ chuyên môn bác sĩ, chuyên khoa và phòng khám chính.
5. `chuyen_khoa`: 8 chuyên khoa mũi nhọn kèm giá khám mặc định.
6. `phong_kham`: Danh mục phòng khám bệnh và cận lâm sàng.
7. `dich_vu`: Danh mục dịch vụ y tế, khám chuyên sâu, xét nghiệm, CĐHA kèm đơn giá & BHYT.
8. `benh_nhan`: Hồ sơ bệnh nhân 360°, thông tin liên hệ, tiền sử bệnh, nhóm máu.
9. `lich_hen`: Quản lý lịch hẹn khám bệnh, phát hiện xung đột và lịch sử đặt khám.
10. `lich_lam_viec`: Ca trực (Sáng, Chiều, Tối), duyệt ca, chấm công và giờ làm việc.
11. `phieu_kham`: Bệnh án điện tử EMR, chẩn đoán ICD-10, hướng điều trị, hẹn tái khám.
12. `chi_so_sinh_ton`: Chỉ số sinh tồn (Huyết áp, Mạch, Nhiệt độ, SpO2).
13. `phieu_chi_dinh`: Phiếu chỉ định cận lâm sàng của bác sĩ.
14. `chi_tiet_chi_dinh`: Chi tiết xét nghiệm / CĐHA, kết quả và ảnh đính kèm.
15. `thuoc`: Kho dược phẩm, đơn giá, hoạt chất, số lượng tồn kho.
16. `don_thuoc`: Đơn thuốc điện tử, hình thức mua (Bệnh viện / Mua ngoài), trạng thái cấp phát.
17. `chi_tiet_don_thuoc`: Danh sách thuốc trong đơn, liều dùng, số lượng, cách dùng.
18. `hoa_don`: Hóa đơn viện phí khám bệnh, hóa đơn thuốc HDT, cấn trừ BHYT 80%.
19. `chi_tiet_hoa_don`: Chi tiết từng dòng dịch vụ tính tiền trong hóa đơn.
20. `thong_bao`: Thông báo in-app thời gian thực, nhắc nhở lịch hẹn và kết quả.
21. `lich_su_nhac_nho`: Ghi nhận lịch sử gửi nhắc nhở lịch hẹn và tái khám.
22. `phan_hoi`: Đánh giá sao (1-5 sao) và nhận xét dịch vụ của bệnh nhân.
23. `hom_thu_gop_y`: Hòm thư phản ánh chất lượng khám chữa bệnh.
24. `bai_viet`: Tin tức y tế, cẩm nang sức khỏe.
25. `banner`: Slider quảng bá và khuyến mãi trên trang chủ.
26. `audit_log`: Nhật ký ghi vết kiểm toán bảo mật mọi thao tác nhạy cảm.
27. `lich_su_sao_luu`: Lịch sử các phiên sao lưu và phục hồi CSDL SQL Server.

---

## Bản Quyền và Thông Tin Đồ Án

* **Đồ Án**: Khóa Luận Chuyên Ngành - Hệ Thống Quản Lý Phòng Khám Đa Khoa (HIS & EMR).
* **Nền tảng**: Python 3.10+ / Flask / Microsoft SQL Server / TailwindCSS / Web Audio.
* **Thời gian thực hiện**: Năm học 2026.
