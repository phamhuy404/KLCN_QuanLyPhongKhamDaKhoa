# HƯỚNG DẪN CÀI ĐẶT và KHỞI CHẠY HỆ THỐNG PHÒNG KHÁM ĐA KHOA (MVC)
Nền tảng: 100% Microsoft SQL Server và Python Flask

Tài liệu này hướng dẫn chi tiết từng bước thiết lập môi trường, cấu hình cơ sở dữ liệu Microsoft SQL Server, khởi chạy ứng dụng Web và danh sách tài khoản phục vụ vận hành, kiểm thử.

## I. YÊU CẦU MÔI TRƯỜNG VÀ PHẦN MỀM

1. **Hệ điều hành**: Windows 10/11 hoặc Windows Server (Khuyến nghị 64-bit).
2. **Python**: Phiên bản 3.9 trở lên (Khuyến nghị Python 3.10 hoặc 3.11).
3. **Cơ sở dữ liệu**: Microsoft SQL Server 2017, 2019, 2022 hoặc Microsoft SQL Server Express (Bản miễn phí).
4. **Driver ODBC**: Microsoft ODBC Driver 17 for SQL Server (hoặc Driver 18).
5. **Công cụ quản trị**: SQL Server Management Studio (SSMS) hoặc Azure Data Studio.

## II. CÁC BƯỚC THIẾT LẬP CHI TIẾT

### Bước 1: Cài đặt thư viện Python
Mở cửa sổ dòng lệnh (Command Prompt hoặc PowerShell) tại thư mục gốc của dự án và chạy:
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
*Lưu ý: Nếu sử dụng tài khoản `sa` của SQL Server Authentication, cấu hình thêm `'uid': 'sa'` và `'pwd': 'mat_khau_cua_ban'`.*

### Bước 3: Khởi tạo Cơ sở dữ liệu và nạp dữ liệu sạch
Chọn một trong hai cách dưới đây:

**Cách 1: Khởi tạo tự động bằng Script Python (Khuyến nghị)**
Chạy lệnh sau tại thư mục gốc:
```bash
python scratch/seed_database.py
```
Script sẽ tự động kết nối SQL Server, khởi tạo cơ sở dữ liệu `quan_ly_phong_kham`, tạo toàn bộ các bảng, chỉ mục và nạp đầy đủ danh mục thuốc, dịch vụ, 61+ tài khoản mẫu chuẩn hóa.

**Cách 2: Khởi tạo thủ công bằng SQL Server Management Studio (SSMS)**
1. Mở SSMS và kết nối đến SQL Server Instance của máy tính.
2. Mở file [database/cosodulieu.sql](file:///d:/baitap/Khoa%20Luan/KLCN_QuanLyPhongKhamDaKhoa/database/cosodulieu.sql).
3. Nhấn **Execute (F5)** để thực thi toàn bộ kịch bản DDL và DML.

### Bước 4: Khởi chạy máy chủ Web Flask
Chạy lệnh:
```bash
python app.py
```
Khi hiển thị thông báo:
```text
* Running on http://127.0.0.1:5000
* Restarting with stat
```
Bạn đã khởi chạy thành công!

### Bước 5: Truy cập các phân hệ trên trình duyệt
- **Trang chủ và Đặt lịch trực tuyến**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Đăng nhập**: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
- **Đăng ký tài khoản bệnh nhân**: [http://127.0.0.1:5000/register](http://127.0.0.1:5000/register)
- **Cổng thông tin Bệnh nhân**: [http://127.0.0.1:5000/patient](http://127.0.0.1:5000/patient)
- **Phân hệ Quản trị và Nhân viên y tế**: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
- **Hồ sơ cá nhân nội bộ**: [http://127.0.0.1:5000/admin/profile](http://127.0.0.1:5000/admin/profile)

## III. CHẠY BỘ KIỂM THỬ TỰ ĐỘNG (UNIT TESTS)

Để xác nhận tính toàn vẹn của logic nghiệp vụ, chạy lệnh:
```bash
python -m unittest discover -s tests
```
Hệ thống sẽ thực thi 44 bài kiểm thử liên hoàn kiểm tra:
1. Đặt lịch, chặn trùng giờ, chặn đổi lịch đã khám/hoàn thành.
2. Cấn trừ BHYT 80% và tự động hủy hóa đơn khám khi hủy lịch.
3. Khám EMR 2 giai đoạn, ra chỉ định CLS, kiểm tra phí CLS, chốt kết luận EMR sau CLS.
4. Kéo thả tối đa 10 ảnh, lưới 2x2, phóng to Lightbox.
5. Cảnh báo dị ứng thuốc thời gian thực.
6. Quy trình cấp phát thuốc 3 bước: duyệt đơn, thanh toán, Dược sĩ cấp phát trừ kho.
7. Phân quyền ca trực: Admin không trực, Lễ tân tự duyệt, Bác sĩ chờ duyệt.
8. Điều phối lịch hẹn khi hủy ca trực bác sĩ.
9. Hồ sơ cá nhân nội bộ và đổi mật khẩu an toàn.

Kết quả mong đợi: `Ran 44 tests ... OK`.

## IV. BẢNG TRA CỨU TÀI KHOẢN MẪU HỆ THỐNG

| STT | Phân hệ / Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn và Chức năng |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Quản trị viên (ADMIN)** | `admin` | `admin123` | Quản trị tài khoản, tạo bác sĩ mới, duyệt lịch làm việc, quản lý kho thuốc, sao lưu CSDL (.bak) |
| **2** | **Lễ tân và Thu ngân (LETAN)** | `letan_1` | `Password@123` | Tiếp đón, phân bổ bác sĩ, tự đăng ký và tự duyệt ca trực, duyệt đơn thuốc viện, thu viện phí |
| **3** | **Kỹ thuật viên phòng Lab (KTV)** | `ktv_1` | `Password@123` | Xem chỉ định CLS, kiểm tra trạng thái đóng phí, nhập kết quả, kéo thả tối đa 10 ảnh CĐHA |
| **4** | **Dược sĩ kho dược (DUOCSI)** | `duocsi_1` | `Password@123` | Quản lý kho thuốc, kiểm tra đơn thuốc đã thanh toán, cấp phát thuốc thực tế trừ kho |
| **5** | **Bác sĩ Nội khoa (BACSI)** | `bs_noi_1` | `Password@123` | Khám EMR, kéo thả tối đa 10 ảnh, chỉ định CLS, cảnh báo dị ứng, chốt kết luận EMR sau CLS |
| **6** | **Bác sĩ Ngoại khoa (BACSI)** | `bs_ngoai_1` | `Password@123` | Khám lâm sàng ngoại khoa, ra chỉ định chụp chiếu, kê đơn thuốc |
| **7** | **Bác sĩ Nhi khoa (BACSI)** | `bs_nhi_1` | `Password@123` | Khám bệnh nhi khoa, ghi nhận sinh hiệu trẻ em, kê đơn điện tử |
| **8** | **Bác sĩ Răng Hàm Mặt (BACSI)** | `bs_rhm_1` | `Password@123` | Khám răng hàm mặt, chỉ định X-quang răng, kê đơn điều trị |
| **9** | **Bác sĩ Sản - Phụ Khoa (BACSI)**| `bs_san_1` | `Password@123` | Khám sản phụ khoa, chỉ định siêu âm Doppler, hội chẩn |
| **10**| **Bác sĩ Tai Mũi Họng (BACSI)** | `bs_tmh_1` | `Password@123` | Khám tai mũi họng, nội soi ống mềm, chẩn đoán ICD |
| **11**| **Bác sĩ Mắt (BACSI)** | `bs_mat_1` | `Password@123` | Đo khúc xạ, khám chuyên khoa mắt, lập hồ sơ điều trị |
| **12**| **Bệnh nhân mẫu 1 (BENHNHAN)** | `0901234561` | `123456` | Có thẻ BHYT, tiền sử dị ứng Paracetamol, lịch sử khám đầy đủ |
| **13**| **Bệnh nhân mẫu 2 (BENHNHAN)** | `0901234562` | `123456` | Không có thẻ BHYT, tiền sử dị ứng Penicillin |
