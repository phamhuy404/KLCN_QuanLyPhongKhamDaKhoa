# HƯỚNG DẪN CÀI ĐẶT và KHỞI CHẠY HỆ THỐNG PHÒNG KHÁM ĐA KHOA (MVC)
Nền tảng: 100% Microsoft SQL Server và Python Flask

Tài liệu này hướng dẫn chi tiết từng bước thiết lập môi trường, cấu hình cơ sở dữ liệu Microsoft SQL Server, khởi chạy ứng dụng Web và danh sách tài khoản phục vụ vận hành, kiểm thử.

## I. YÊU CẦU MÔI TRƯỜNG VÀ PHẦN MỀM

1. **Hệ điều hành**: Windows 10/11 hoặc Windows Server 64-bit.
2. **Python**: Phiên bản 3.9 trở lên (Khuyến nghị Python 3.10 hoặc 3.11).
3. **Cơ sở dữ liệu**: Microsoft SQL Server 2017, 2019, 2022 hoặc Microsoft SQL Server Express (Bản miễn phí).
4. **Driver ODBC**: Microsoft ODBC Driver 17 for SQL Server (hoặc Driver 18).
5. **Công cụ quản trị (tùy chọn)**: SQL Server Management Studio (SSMS) hoặc Azure Data Studio.

## II. CÁC BƯỚC THIẾT LẬP VÀ KHỞI CHẠY CHI TIẾT

### Bước 1: Cài đặt thư viện Python
Mở cửa sổ dòng lệnh (PowerShell hoặc Command Prompt) tại thư mục gốc của dự án và chạy:
```bash
pip install -r requirements.txt
```

Danh sách các thư viện chính:
- `flask`: Framework kiến trúc MVC cho ứng dụng Web.
- `pyodbc`: Driver kết nối và thực thi T-SQL trực tiếp với Microsoft SQL Server.
- `pillow`: Thư viện xử lý hình ảnh và nén tự động định dạng WebP (< 80KB).

### Bước 2: Cấu hình kết nối Microsoft SQL Server trong `config.py`
Mở tệp [config.py](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/config.py) và kiểm tra khối cấu hình `SQLSERVER_CONFIG`:
```python
DB_ENGINE = 'sqlserver'

SQLSERVER_CONFIG = {
    'server': 'localhost',             # Hoặc: '.\SQLEXPRESS', 'localhost\SQLEXPRESS'
    'database': 'quan_ly_phong_kham',  # Tên cơ sở dữ liệu
    'driver': 'ODBC Driver 17 for SQL Server',
    'trusted_connection': 'yes',       # Dùng Windows Authentication
    'TrustServerCertificate': 'yes'    # Tránh lỗi chứng chỉ bảo mật trên bản 2022
}
```
*Lưu ý: Nếu sử dụng tài khoản `sa` của SQL Server Authentication, cấu hình `'trusted_connection': 'no'` và bổ sung thêm `'uid': 'sa'`, `'pwd': 'mat_khau_cua_ban'`.*

### Bước 3: Khởi tạo Cơ sở dữ liệu và nạp dữ liệu sạch (CHỈ CHẠY 1 LẦN KHI CÀI ĐẶT ĐẦU TIÊN)

> **LƯU Ý ĐẶC BIỆT**:
> - Bước 3 chỉ thực hiện duy nhất một lần khi thiết lập hệ thống lần đầu.
> - **Khi khởi động lại hệ thống ở các lần làm việc tiếp theo, BỎ QUA Bước 3 và CHỈ CẦN CHẠY Bước 4 (`python app.py`)** để bảo toàn nguyên vẹn mọi dữ liệu bạn đã chỉnh sửa (như thông tin admin, lịch hẹn, hồ sơ bệnh nhân,...).
> - Nếu chạy lại Bước 3, hệ thống sẽ xóa toàn bộ dữ liệu hiện thời và nạp lại dữ liệu mẫu gốc ban đầu.

Chọn một trong hai cách dưới đây khi cài đặt lần đầu:

**Cách 1: Khởi tạo tự động bằng Script Python (Khuyến nghị)**
Chạy lệnh sau tại thư mục gốc:
```bash
python scratch/seed_database.py
```
Script sẽ tự động kết nối SQL Server, khởi tạo cơ sở dữ liệu `quan_ly_phong_kham`, tạo toàn bộ 27 bảng dữ liệu, chỉ mục và nạp đầy đủ danh mục thuốc, dịch vụ y tế, 69 tài khoản mẫu chuẩn hóa. (Nếu CSDL đã có dữ liệu, script sẽ hiển thị cảnh báo bảo vệ).

**Cách 2: Khởi tạo thủ công bằng SQL Server Management Studio (SSMS)**
1. Mở SSMS và kết nối đến SQL Server Instance của máy tính.
2. Mở file [database/cosodulieu.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/database/cosodulieu.sql).
3. Nhấn **Execute (F5)** để thực thi toàn bộ kịch bản DDL và DML.

### Bước 4: Khởi chạy máy chủ Web Flask (Lệnh vận hành hàng ngày)
Chạy lệnh:
```bash
python app.py
```
Khi hiển thị thông báo:
```text
* Running on http://127.0.0.1:5000
* Restarting with stat
```
Hệ thống đã khởi chạy thành công!

*(Mẹo cho nhóm: Khi nhận được file `.bak` mới từ thành viên khác, bạn có thể nạp ngay bản sao lưu mới nhất bằng lệnh `python scratch/restore_backup.py` hoặc `python app.py --restore-latest`).*

### Bước 5: Truy cập các phân hệ trên trình duyệt
- **Trang chủ và Đặt lịch trực tuyến**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Đăng nhập**: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
- **Đăng ký tài khoản bệnh nhân**: [http://127.0.0.1:5000/register](http://127.0.0.1:5000/register)
- **Cổng thông tin Bệnh nhân**: [http://127.0.0.1:5000/patient](http://127.0.0.1:5000/patient)
- **Phân hệ Quản trị và Bác sĩ**: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
- **Hồ sơ cá nhân và Giá khám**: [http://127.0.0.1:5000/admin/my-profile](http://127.0.0.1:5000/admin/my-profile)

## III. CHẠY BỘ KIỂM THỬ TỰ ĐỘNG (UNIT TESTS)

Để kiểm tra toàn diện và xác nhận độ tin cậy của toàn bộ hệ thống, chạy lệnh:
```bash
python -m unittest discover -s tests
```
Hệ thống sẽ thực thi toàn bộ **57 bài kiểm thử tự động** bao phủ các nghiệp vụ:
1. Ràng buộc dữ liệu (họ tên tiếng Việt không ký tự lạ, BHYT 10 số, CCCD 12 số, SĐT, sinh hiệu EMR).
2. Quy trình cấp lại mật khẩu mặc định `123` và cưỡng chế đổi mật khẩu lần đầu tại `/force-change-password`.
3. Đặt lịch khám, chống đặt trùng giờ, cấn trừ BHYT 80%, chặn hủy lịch đã khám.
4. Bệnh án điện tử EMR 5 bước liên hoàn, tải tối đa 10 ảnh, lưới 2x2, phóng to Lightbox.
5. Cảnh báo dị ứng thuốc thời gian thực từ từ điển danh mục chuẩn.
6. Quy trình cấp phát thuốc 3 bước: bệnh nhân chọn mua, tiếp tân duyệt, dược sĩ cấp phát trừ kho.
7. Phân công ca trực: Lễ tân tự duyệt, Bác sĩ chờ duyệt, nhận diện hết giờ làm việc.
8. Giao diện Dark Mode Midnight Slate toàn diện và lưu bền vững vào `localStorage`.

Kết quả mong đợi: `Ran 57 tests ... OK` (100% Passing).

## IV. BẢNG TRA CỨU TÀI KHOẢN MẪU HỆ THỐNG

Hệ thống cung cấp sẵn 69 tài khoản mẫu phục vụ kiểm thử và nghiệm thu:

| STT | Phân hệ / Vai trò | Tên đăng nhập | Mật khẩu mặc định | Quyền hạn và Chức năng chính |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Quản trị viên (ADMIN)** | `admin` | `admin123` | Quản trị tài khoản, cấp lại mật khẩu 123, duyệt lịch trực, đăng bài viết cẩm nang, sao lưu CSDL (.bak) |
| **2** | **Lễ tân và Thu ngân (LETAN)** | `letan_1` | `Password@123` | Tiếp đón, phân buồng khám, tự đăng ký và tự duyệt ca trực, đăng bài viết cẩm nang, thu viện phí |
| **3** | **Kỹ thuật viên phòng Lab (KTV)** | `ktv_1` | `Password@123` | Xem chỉ định CLS, kiểm tra trạng thái đóng phí, nhập kết quả, tải tối đa 10 ảnh CĐHA |
| **4** | **Dược sĩ kho dược (DUOCSI)** | `duocsi_1` | `Password@123` | Quản lý kho thuốc, duyệt đơn thuốc, bấm cấp phát thuốc thực tế trừ kho |
| **5** | **Bác sĩ Nội khoa (BACSI)** | `bs_noi_1` | `Password@123` | Khám EMR 5 bước, tải tối đa 10 ảnh, ra chỉ định CLS, cảnh báo dị ứng, xem kết quả CLS, cài đặt giá khám |
| **6** | **Bác sĩ Ngoại khoa (BACSI)** | `bs_ngoai_1` | `Password@123` | Khám lâm sàng ngoại khoa, ra chỉ định chụp chiếu, lọc lịch khám cá nhân |
| **7** | **Bác sĩ Nhi khoa (BACSI)** | `bs_nhi_1` | `Password@123` | Khám bệnh nhi khoa, ghi nhận sinh hiệu trẻ em, kê đơn điện tử |
| **8** | **Bác sĩ Răng Hàm Mặt (BACSI)** | `bs_rhm_1` | `Password@123` | Khám răng hàm mặt, chỉ định X-quang răng, kê đơn điều trị |
| **9** | **Bác sĩ Sản - Phụ Khoa (BACSI)**| `bs_san_1` | `Password@123` | Khám sản phụ khoa, chỉ định siêu âm Doppler, hội chẩn |
| **10**| **Bác sĩ Tai Mũi Họng (BACSI)** | `bs_tmh_1` | `Password@123` | Khám tai mũi họng, nội soi ống mềm, chẩn đoán ICD |
| **11**| **Bác sĩ Mắt (BACSI)** | `bs_mat_1` | `Password@123` | Đo khúc xạ, khám chuyên khoa mắt, lập hồ sơ điều trị |
| **12**| **Bệnh nhân có BHYT (BENHNHAN)** | `0901234561` | `123456` | Có thẻ BHYT (khấu trừ 80%), dị ứng Paracetamol, lịch sử khám, thanh toán |
| **13**| **Bệnh nhân không BHYT (BENHNHAN)**| `0901234562` | `123456` | Không có thẻ BHYT, dị ứng Penicillin, lịch sử khám, thanh toán VietQR |

*Lưu ý cơ chế cấp lại mật khẩu: Khi Admin hoặc Lễ tân cấp lại mật khẩu cho tài khoản, mật khẩu tự động đưa về `123`. Lần đầu đăng nhập, tài khoản sẽ được yêu cầu đổi mật khẩu mới trước khi truy cập bất kỳ trang nào.*
