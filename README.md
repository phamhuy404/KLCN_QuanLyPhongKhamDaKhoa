# Hệ Thống Quản Lý Phòng Khám Đa Khoa H2T Healthcare

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Architecture](https://img.shields.io/badge/Architecture-MVC%20Pattern-orange.svg)]()
[![Database Support](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server%20(100%25%20T--SQL)-red.svg)]()
[![Frontend](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20HTML5%20%7C%20JS-teal.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-56%2F56%20Passing%20(100%25)-brightgreen.svg)]()

Hệ thống ứng dụng Web quản lý toàn diện phòng khám đa khoa theo chuẩn kiến trúc MVC (Model - View - Controller), hoạt động chuyên biệt 100% trên nền tảng **Microsoft SQL Server**. Hệ thống số hóa hoàn chỉnh quy trình y tế khép kín: Tiếp đón và đặt lịch khám, phân công ca trực thông minh đa vai trò, bệnh án điện tử EMR 2 giai đoạn với hỗ trợ đa ảnh chuẩn hóa (tối đa 10 ảnh, lưới xem trước 2x2, phóng to Lightbox), cận lâm sàng kiểm tra viện phí, cảnh báo dị ứng thuốc thời gian thực, quản lý kho dược và cấp phát thuốc 3 bước an toàn, hóa đơn viện phí khấu trừ BHYT, cổng thông tin người bệnh và hồ sơ cá nhân nội bộ riêng biệt cho nhân sự y tế.

## Cấu Trúc Thư Mục Chuẩn (Project Structure)

```text
KLCN_QuanLyPhongKhamDaKhoa/
├── app.py                         # Điểm khởi chạy chính của máy chủ Flask
├── config.py                      # Cấu hình tập trung (Microsoft SQL Server, Google Maps, Secret Key)
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
├── README.md                      # Tài liệu tổng quan và hướng dẫn dự án
│
├── database/                      # [DATABASE] Cơ sở dữ liệu Microsoft SQL Server
│   ├── cosodulieu.sql             #   - Toàn bộ DDL và DML trọn gói Microsoft SQL Server (100% T-SQL)
│   ├── migrations/                #   - Các script migration và cấu trúc nâng cấp CSDL
│   └── legacy_bridge.py           #   - Module hỗ trợ tương thích ngược
│
├── docs/                          # [DOCS] Tài liệu vận hành, quy trình và kiểm thử
│   ├── huong_dan_chay.md          #   - Hướng dẫn cài đặt, cấu hình SQL Server và khởi chạy chi tiết
│   ├── kiem_thu_thu_cong_toan_dien.md # - Cẩm nang kiểm thử thủ công từng bước cho nhóm
│   └── QUY_TRINH_NGHIEP_VU_HE_THONG.md # - Tài liệu nghiệp vụ y tế và cơ chế cấn trừ chuẩn
│
├── data/                          # [DATA] Từ điển danh mục và Mock data
│   ├── catalogs/                  #   - Từ điển danh mục: nhóm máu, dị ứng, tiền sử bệnh
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
│   └── notification_service.py    #   - Gửi thông báo in-app đa kênh và quét nhắc nhở lịch hẹn
│
├── controllers/                   # [CONTROLLER] Xử lý nghiệp vụ và điều hướng URL
│   ├── auth_controller.py         #   - Đăng nhập, đăng ký, đăng xuất, hoàn thiện hồ sơ lần đầu
│   ├── home_controller.py         #   - Trang chủ (random bác sĩ), đặt lịch online, cẩm nang y tế
│   ├── patient_controller.py      #   - Cổng bệnh nhân: Hồ sơ 360°, đơn thuốc, hóa đơn viện phí
│   ├── admin_controller.py        #   - Phân hệ quản trị: Tiếp đón, EMR, CLS, kho dược, viện phí, hồ sơ cá nhân
│   └── api_controller.py          #   - RESTful API: Đăng ký lịch làm, tiếp nhận, EMR, xuất thuốc, viện phí
│
├── models/                        # [MODEL] Tương tác CSDL SQL Server và ràng buộc nghiệp vụ
│   ├── user_model.py              #   - Tài khoản, phân quyền RBAC, hồ sơ nhân viên, đổi mật khẩu
│   ├── appointment_model.py       #   - Đặt lịch, chống đặt trùng giờ, chặn reschedule lịch đã xong
│   ├── medical_record_model.py    #   - EMR 2 giai đoạn, chỉ định CLS, kiểm tra tồn kho và kê đơn
│   ├── pharmacy_model.py          #   - Quản lý kho dược, duyệt đơn 3 bước, cấp phát thực tế trừ kho
│   ├── billing_model.py           #   - Viện phí, khấu trừ BHYT 80%, nhận diện hóa đơn thuốc HDT
│   ├── patient_model.py           #   - Hồ sơ bệnh nhân 360°, tiền sử dị ứng, cận lâm sàng
│   ├── schedule_model.py          #   - Lịch ca trực: Lễ tân tự duyệt, Admin ẩn, giới hạn 3 BS/khoa/ca
│   ├── notification_model.py      #   - Hệ thống thông báo tức thì, popups real-time, polling
│   ├── banner_model.py            #   - Quản lý slider quảng bá trang chủ (CRUD và sắp xếp)
│   ├── article_model.py           #   - Tin tức, cẩm nang y khoa và tìm kiếm gần đúng tiếng Việt
│   ├── clinic_model.py            #   - Dịch vụ y tế, thống kê dashboard phòng khám
│   ├── feedback_model.py          #   - Đánh giá chất lượng và phản hồi của người bệnh
│   └── backup_model.py            #   - Sao lưu, khôi phục CSDL SQL Server (.bak)
│
├── static/                        # [STATIC] Tài nguyên tĩnh giao diện
│   ├── css/                       #   - Custom styles, TailwindCSS overrides
│   ├── js/                        #   - Toast notification, Polling, Schedule interaction, Dropzone
│   ├── img/                       #   - Hình ảnh bài viết, icon thương hiệu
│   ├── images/                    #   - Default avatar fallback
│   └── uploads/                   #   - Tệp đính kèm người dùng: kết quả CLS, ảnh lâm sàng EMR, banner
│
├── templates/                     # [VIEW] Giao diện người dùng Jinja2 HTML và TailwindCSS
│   ├── layouts/                   #   - Layout dùng chung (base.html, header.html, footer.html)
│   ├── auth/                      #   - Giao diện đăng nhập, đăng ký tài khoản
│   ├── patient/                   #   - Cổng bệnh nhân và hoàn thiện hồ sơ bắt buộc
│   ├── admin/                     #   - Phân hệ quản trị, EMR, phòng Lab, kho dược, hồ sơ cá nhân
│   └── home.html                  #   - Trang chủ hiển thị ngẫu nhiên bác sĩ
│
├── tests/                         # [TESTS] Kiểm thử tự động chính thức (44 Unit Tests)
│   ├── test_features_6_to_10.py   #   - Kiểm thử nghiệp vụ lõi: đặt lịch, cấn trừ, BHYT, EMR
│   ├── test_upgraded_features.py  #   - Kiểm thử tính năng nâng cấp: ca trực, kiểm toán, nén ảnh
│   ├── test_doctor_and_prescription_workflow.py # - Kiểm thử luồng tạo bác sĩ và duyệt đơn thuốc
│   └── test_final_comprehensive.py # - Kiểm thử toàn diện EMR 2 giai đoạn, đa ảnh, dị ứng, phân quyền
│
└── scratch/                       # [SCRATCH] Kịch bản tiện ích và nạp dữ liệu ban đầu
    └── seed_database.py           #   - Nạp sạch CSDL và tài khoản chuẩn vào SQL Server
```

## Khởi Chạy Nhanh Trong 3 Bước

### Bước 1: Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi tạo CSDL Microsoft SQL Server
Chạy script nạp tự động để tạo CSDL sạch và bộ tài khoản chuẩn:
```bash
python scratch/seed_database.py
```
*(Hoặc mở file [database/cosodulieu.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/database/cosodulieu.sql) trong SQL Server Management Studio và nhấn Execute F5).*

### Bước 3: Khởi chạy máy chủ Web
```bash
python app.py
```
Truy cập ứng dụng tại địa chỉ: `http://127.0.0.1:5000`

### Chạy bộ kiểm thử tự động toàn diện (56/56 Tests OK)
```bash
python -m unittest discover -s tests
```

## Danh Sách Tài Khoản Mẫu Đăng Nhập

Hệ thống được khởi tạo sẵn các tài khoản mẫu cho từng vai trò để phục vụ kiểm thử và nghiệm thu:

| Vai trò | Tài khoản mẫu | Mật khẩu | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (ADMIN)** | `admin` | `admin123` | Toàn quyền quản trị, tạo tài khoản bác sĩ mới, duyệt lịch làm việc, sao lưu CSDL (.bak) |
| **Lễ tân và Thu ngân (LETAN)** | `letan_1` | `Password@123` | Tiếp đón, phân bổ bác sĩ, tự đăng ký và tự duyệt ca trực, duyệt đơn thuốc viện, thu viện phí |
| **Bác sĩ chuyên khoa (BACSI)** | `bs_noi_1` | `Password@123` | Khám lâm sàng EMR, tải tối đa 10 ảnh, ra chỉ định CLS, xem kết quả CLS và chốt kết luận EMR |
| **Kỹ thuật viên phòng Lab (KTV)**| `ktv_1` | `Password@123` | Xem chỉ định, kiểm tra trạng thái viện phí CLS, nhập kết quả và tải lên tối đa 10 ảnh CĐHA |
| **Dược sĩ kho dược (DUOCSI)** | `duocsi_1` | `Password@123` | Quản lý kho thuốc, kiểm tra đơn thuốc đã thanh toán, cấp phát thuốc thực tế và trừ kho |
| **Bệnh nhân (BENHNHAN)** | `0901234561` | `123456` | Đặt lịch trực tuyến, theo dõi chặng khám, chọn mua thuốc viện/ngoài, thanh toán VietQR |

*Xem danh sách đầy đủ 61+ tài khoản tại tài liệu [docs/huong_dan_chay.md](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/docs/huong_dan_chay.md).*

## Các Quy Trình Nghiệp Vụ và Nâng Cấp Nổi Bật

1. **Khám EMR 2 giai đoạn và Quản lý đa ảnh (Tối đa 10 ảnh, lưới 2x2, Lightbox)**:
   - Hỗ trợ kéo thả hoặc click chọn tối đa 10 ảnh cùng lúc cho cả Bác sĩ và Kỹ thuật viên.
   - Khung dạng 2 cột ảnh 2x2 xem trước nhỏ, cuộn được, click phóng to bằng Lightbox modal chuẩn HD.
   - Giai đoạn 1 (Chỉ định CLS) giữ phiếu khám ở trạng thái `Chờ kết quả CLS` và chỉ gửi thông báo đi làm CLS.
   - Giai đoạn 2 sau khi có kết quả CLS, bác sĩ bấm *"Kết Luận và Hoàn Tất Ca Khám Sau CLS"* mới hoàn thành bệnh án và chuyển đơn thuốc.
2. **Cảnh báo dị ứng thuốc thời gian thực**:
   - Tự động so khớp tiền sử dị ứng của bệnh nhân khi chọn thuốc. Hiển thị banner cảnh báo đỏ và hộp thoại xác nhận an toàn trước khi thêm vào toa.
3. **Phân quyền đăng ký ca làm việc**:
   - Admin không cần đăng ký và không xuất hiện trên lịch.
   - Lễ tân tự đăng ký và tự động duyệt ngay (`DA_DUYET`).
   - Bác sĩ/Dược sĩ/KTV đăng ký ở trạng thái `CHO_DUYET` để Admin/Lễ tân duyệt hàng loạt (tối đa 3 bác sĩ/khoa/ca).
   - Duyệt hủy ca trực bác sĩ tự động chuyển lịch hẹn về `Chờ tiếp nhận` và nhắc Lễ tân điều phối bác sĩ khác.
4. **Quy trình cấp phát thuốc 3 bước**:
   - Bệnh nhân chọn Mua ngoài -> Đơn `Mua ngoài`, không công nợ, không trừ kho.
   - Bệnh nhân chọn Mua tại viện -> Đơn `Chờ duyệt`, sinh hóa đơn tạm `HDT...`.
   - Tiếp tân duyệt -> Khóa chuyển mua ngoài, **tuyệt đối chưa trừ kho**.
   - Bệnh nhân thanh toán -> Đơn `Chờ nhận thuốc`.
   - Dược sĩ bấm Cấp phát thuốc -> **Lúc này mới trừ kho dược**, cập nhật đơn và hóa đơn sang `Đã nhận thuốc`.
5. **Trang hồ sơ cá nhân nội bộ (`/admin/profile`)**:
   - Cung cấp trang xem, sửa thông tin cá nhân và đổi mật khẩu an toàn cho toàn bộ nhân sự nội bộ (Admin, Bác sĩ, Lễ tân, Dược sĩ, KTV).
6. **Ràng buộc an toàn dữ liệu và Cấn trừ BHYT**:
   - Chặn đặt trùng giờ khám cho cùng một bệnh nhân.
   - Chặn reschedule lịch hẹn đã khám, hoàn thành hoặc đã hủy.
   - Tự động cấn trừ 80% tiền khám + tỷ lệ kỹ thuật CLS cho người có thẻ BHYT.
   - Tự động hủy hóa đơn tiền khám khi hủy lịch hẹn.

7. **Chế độ Giao diện Tối (Dark Mode) Toàn Diện**:
   - Cung cấp nút chuyển đổi giao diện Sáng / Tối trực quan trên thanh tiêu đề của mọi trang (Cổng công khai, Cổng bệnh nhân, Cổng quản trị y tế, Trang đăng nhập và đăng ký).
   - Tự động nhận diện theme mặc định của hệ thống máy tính và lưu trữ cấu hình bền vững vào `localStorage` giúp không bị giật nháy màn hình.
   - Bảng màu tối dịu mắt (#0b1324 / #151f32) bảo vệ thị giác cho bác sĩ và nhân viên y tế trong ca trực đêm.
8. **Phân Quyền Đăng Bài và Quản Trị Cẩm Nang Y Tế**:
   - Chỉ duy nhất Tiếp tân (`LETAN`) và Quản trị viên (`ADMIN`) có quyền soạn thảo, đăng bài mới, chỉnh sửa và xóa bài viết (cũng như nhập CSV bài viết).
   - Toàn bộ các vai trò còn lại (Bác sĩ, Dược sĩ, Kỹ thuật viên) và Bệnh nhân được phép xem danh sách bài viết và đọc chi tiết bài viết.
9. **Hệ Thống Ràng Buộc Dữ Liệu Chặt Chẽ (Strict Validation Engine)**:
   - **Họ và tên**: Bắt buộc chỉ chứa chữ cái tiếng Việt có dấu, chữ cái Latin và khoảng trắng đơn; tuyệt đối không chứa chữ số, không chứa ký tự lạ hay ký tự đặc biệt (`validate_name`).
   - **Mã số thẻ BHYT**: Chuẩn 10 chữ số (theo Quyết định 1666/QĐ-BHXH), tuyệt đối không chứa chữ cái hay ký tự lạ (`validate_bhyt`).
   - **Căn cước công dân (CCCD)**: Đúng 12 chữ số theo thẻ chip Bộ Công An, chống nhập dãy số lặp vô lý (`validate_cccd`).
   - **Số điện thoại**: Đúng 10 chữ số thuộc các đầu số di động chuẩn Việt Nam (`03, 05, 07, 08, 09`), chống ký tự lạ (`validate_phone`).
   - **Ngày sinh và độ tuổi**: Chặn ngày sinh tương lai; giới hạn tuổi bệnh nhân (0 - 130 tuổi); nhân sự y tế bắt buộc từ đủ 18 tuổi trở lên (`validate_birth_date`).
   - **Chỉ số sinh tồn lâm sàng (EMR)**: Ràng buộc giá trị y khoa chuẩn: Mạch (30-250), Thân nhiệt (34.0-43.0°C), Huyết áp tâm thu > tâm trương, SpO2 (50-100%), Nhịp thở (8-60) (`validate_vital_signs`).
   - **Kho dược và Dịch vụ**: Giá bán thuốc > 0, tồn kho >= 0, số lượng kê trong đơn >= 1; Đơn giá dịch vụ >= 0, tỷ lệ BHYT 0% - 100%.
