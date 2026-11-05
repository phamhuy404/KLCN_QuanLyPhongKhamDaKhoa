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

### Bước 2: Thiết lập Cơ sở dữ liệu Microsoft SQL Server
1. Mở SQL Server Management Studio (SSMS) và kết nối tới SQL Server instance của bạn (`localhost` hoặc `.\SQLEXPRESS`).
2. Mở file script SQL `database/cosodulieu.sql`.
3. Bấm **Execute** (hoặc nhấn phím **F5**). Script sẽ tự động tạo cơ sở dữ liệu `quan_ly_phong_kham`, tạo toàn bộ 28 bảng và nạp đầy đủ dữ liệu mẫu chuẩn y khoa.

### Bước 3: Kiểm tra cấu hình kết nối trong config.py
Mở file `config.py` tại thư mục gốc và kiểm tra cấu hình kết nối CSDL:
```python
SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': os.environ.get('SQL_SERVER_NAME', 'localhost'),
    'database': 'quan_ly_phong_kham',
    'trusted_connection': 'yes',
    'uid': 'sa',
    'pwd': 'your_password'
}
```

### Bước 4: Khởi chạy Ứng dụng Web
Tại thư mục gốc dự án, thực thi lệnh:
```bash
python app.py
```
Mở trình duyệt web bất kỳ và truy cập địa chỉ:
👉 **`http://localhost:5000`** hoặc **`http://127.0.0.1:5000`**

## III. TÀI KHOẢN MẪU HỆ THỐNG (71 TÀI KHOẢN)

Đăng nhập bằng **Tên đăng nhập** hoặc **Số điện thoại**:
- **Quản trị viên (`ADMIN`)**: `admin` / `123456` (SĐT: `0999999999`).
- **Lễ tân & Thu ngân (`LETAN`)**: `letan_1` đến `letan_5` / Mật khẩu: `123`.
- **Bác sĩ chuyên khoa (`BACSI`)**: `bs_noi_1` đến `bs_noi_5` (Khoa Nội), `bs_ngoai_1` đến `bs_ngoai_5` (Khoa Ngoại), `bs_nhi_1` đến `bs_nhi_5` (Khoa Nhi)... / Mật khẩu: `123`.
- **Dược sĩ (`DUOCSI`)**: `duocsi_1` đến `duocsi_5` / Mật khẩu: `123`.
- **Kỹ thuật viên (`KTV`)**: `ktv_1` đến `ktv_5` / Mật khẩu: `123`.
- **Bệnh nhân (`BENHNHAN`)**: `hoangbaonam` (SĐT: `0901234561`, có thẻ BHYT), `0989900112` (chưa có thẻ BHYT) / Mật khẩu: `123`.

## IV. BỘ KIỂM THỬ TỰ ĐỘNG
Chạy toàn bộ 33 unit tests hồi quy:
```bash
python -m unittest discover tests
```
Chi tiết kịch bản kiểm thử quy trình y tế khép kín vui lòng tham khảo file [`HUONGDAN.md`](../HUONGDAN.md).
