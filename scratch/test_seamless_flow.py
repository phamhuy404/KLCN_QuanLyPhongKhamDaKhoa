import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from core.database import get_db

app = create_app()
client = app.test_client()

print("Bắt đầu kiểm thử toàn bộ hành trình liên hoàn của người dùng trong 1 phiên chạy:")

# 1. Tạo mới tài khoản qua /register
ts = int(time.time())
sdt_user = f"09{ts % 100000000:08d}"
mk_user = "matkhau123"
ten_user = "Trần Quang Minh"

res1 = client.post('/register', data={
    'ho_ten': ten_user,
    'sdt': sdt_user,
    'email': f'minh_{ts}@gmail.com',
    'password': mk_user,
    'confirm_password': mk_user
}, follow_redirects=True)
assert res1.status_code == 200
print(f"Bước 1: [OK] Đăng ký thành công tài khoản mới: SĐT = {sdt_user}")

# 2. Đăng nhập liền
res2 = client.post('/login', data={
    'username': sdt_user,
    'password': mk_user
}, follow_redirects=False)

assert res2.status_code == 302
assert '/patient/complete-profile' in res2.headers['Location']
print("Bước 2: [OK] Đăng nhập liền thành công -> Tự động chuyển hướng đến /patient/complete-profile")

# 3. Điền thông tin cá nhân kích hoạt hồ sơ
res3 = client.post('/patient/complete-profile', data={
    'ho_ten': ten_user,
    'ngay_sinh': '1998-05-15',
    'gioi_tinh': 'Nam',
    'cccd': '079198001234',
    'sdt': sdt_user,
    'email': f'minh_{ts}@gmail.com',
    'bhyt': 'GD4791980012345',
    'dia_chi': '123 Nguyễn Thị Minh Khai, Quận 1, TP.HCM',
    'nhom_mau': 'O+',
    'di_ung': 'Không có',
    'tien_su_benh': 'Khỏe mạnh',
    'tien_su_gia_dinh': 'Không',
    'nguoi_than_ho_ten': 'Trần Văn Long',
    'nguoi_than_sdt': '0901999888',
    'nguoi_than_quan_he': 'Bố'
}, follow_redirects=False)

assert res3.status_code == 302
assert '/patient/dashboard' in res3.headers['Location']
print("Bước 3: [OK] Hoàn thiện hồ sơ cá nhân thành công -> Cờ kích hoạt = 1, chuyển về Dashboard")

# 4. Đặt lịch khám ngay lập tức qua /patient/booking
# Kiểm tra giao diện GET /patient/booking
res4_get = client.get('/patient/booking')
assert res4_get.status_code == 200

# Gửi form đặt lịch khám bệnh
ngay_kham_test = '2026-10-25'
gio_kham_test = '08:30'
ly_do_test = 'Khám tổng quát sức khỏe định kỳ cho người mới đi làm'

res4_post = client.post('/patient/booking', data={
    'chuyen_khoa_id': 1,
    'bac_si_id': 1,
    'ngay_hen': ngay_kham_test,
    'gio_hen': gio_kham_test,
    'ly_do': ly_do_test
}, follow_redirects=True)

assert res4_post.status_code == 200
print(f"Bước 4: [OK] Đặt lịch khám bệnh thành công ngay trong cùng phiên: Ngày {ngay_kham_test} lúc {gio_kham_test}")

# 5. Kiểm tra dữ liệu thực tế đã lưu trong SQL Server
conn = get_db()
cur = conn.cursor()

# Kiểm tra bảng benh_nhan
cur.execute("SELECT bn.id, bn.ma_benh_nhan, bn.ho_ten, tk.da_hoan_thien_ho_so FROM benh_nhan bn JOIN tai_khoan tk ON bn.tai_khoan_id = tk.id WHERE tk.username = ?", (sdt_user,))
bn_row = cur.fetchone()
assert bn_row is not None
print(f"Bước 5: [OK] SQL Server ghi nhận hồ sơ bệnh nhân: Mã = {bn_row['ma_benh_nhan']}, Tên = {bn_row['ho_ten']}, Cờ = {bn_row['da_hoan_thien_ho_so']}")

# Kiểm tra bảng lich_hen
cur.execute("SELECT lh.id, lh.ma_lich_hen, lh.ngay_hen, lh.gio_hen, lh.trang_thai, lh.ly_do_kham FROM lich_hen lh WHERE lh.benh_nhan_id = ? ORDER BY lh.id DESC", (bn_row['id'],))
lh_row = cur.fetchone()
assert lh_row is not None
assert lh_row['trang_thai'] == 'Chờ tiếp nhận'
print(f"Bước 6: [OK] SQL Server ghi nhận lịch hẹn: Mã = {lh_row['ma_lich_hen']}, Giờ = {str(lh_row['gio_hen'])[:5]}, Trạng thái = '{lh_row['trang_thai']}'")

conn.close()

print("\n=> XÁC NHẬN: Trong cùng 1 phiên chạy, người dùng hoàn toàn có thể TẠO MỚI TÀI KHOẢN -> ĐĂNG NHẬP LIỀN -> ĐIỀN THÔNG TIN -> ĐẶT LỊCH KHÁM NGAY LẬP TỨC 100% THÀNH CÔNG!")
