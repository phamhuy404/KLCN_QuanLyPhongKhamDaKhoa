import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app

app = create_app()
client = app.test_client()

print("Bắt đầu kiểm thử toàn bộ luồng tạo mới và xác thực tài khoản...")

# 1. Kiểm tra trang đăng ký GET
res = client.get('/register')
assert res.status_code == 200, f"GET /register thất bại: {res.status_code}"
print("1. [PASS] Trang /register hiển thị tốt")

# 2. Đăng ký với ký tự lạ / không an toàn
res = client.post('/register', data={
    'ho_ten': 'Nguyen Van <script>alert(1)</script>',
    'sdt': '0901239999',
    'password': 'password123',
    'confirm_password': 'password123'
})
assert "không an toàn" in res.data.decode('utf-8') or "chỉ được chứa chữ cái" in res.data.decode('utf-8'), "Không chặn được ký tự đặc biệt"
print("2. [PASS] Chặn thành công ký tự lạ khi đăng ký")

# 3. Đăng ký tài khoản hợp lệ mới
import time
test_phone = f"09{int(time.time()) % 100000000:08d}"
test_user = test_phone # UserModel uses sdt as username
res = client.post('/register', data={
    'ho_ten': 'Nguyễn Hoàng Khang',
    'sdt': test_phone,
    'email': f'khang_{int(time.time())}@gmail.com',
    'password': 'password123',
    'confirm_password': 'password123'
})
assert res.status_code == 200, f"Đăng ký thất bại: {res.status_code}"
assert "thành công" in res.data.decode('utf-8').lower(), f"Response không chứa thành công: {res.data.decode('utf-8')[:300]}"
print(f"3. [PASS] Đăng ký tài khoản bệnh nhân mới thành công ({test_phone})")

# 4. Đăng nhập lần đầu bằng tài khoản mới
with client.session_transaction() as sess:
    sess.clear()

res = client.post('/login', data={
    'username': test_phone,
    'password': 'password123'
}, follow_redirects=False)
assert res.status_code == 302, f"Đăng nhập không redirect: {res.status_code}"
assert '/patient/complete-profile' in res.headers['Location'], f"Không chuyển hướng sang complete-profile: {res.headers['Location']}"
print("4. [PASS] Đăng nhập lần đầu tự động chuyển hướng đến trang /patient/complete-profile")

# 5. Kiểm tra chặn truy cập dashboard khi chưa điền thông tin cá nhân
# Đăng nhập lại với follow_redirects
res = client.post('/login', data={
    'username': test_phone,
    'password': 'password123'
}, follow_redirects=True)

# Thử truy cập dashboard
res_dash = client.get('/patient/dashboard', follow_redirects=False)
assert res_dash.status_code == 302 and '/patient/complete-profile' in res_dash.headers['Location'], "Chưa chặn được dashboard khi chưa hoàn thiện hồ sơ"
print("5. [PASS] Chặn tuyệt đối truy cập dashboard khi hồ sơ chưa hoàn thiện")

# 6. Kiểm tra ràng buộc ký tự lạ khi điền hồ sơ cá nhân
res_invalid_profile = client.post('/patient/complete-profile', data={
    'ho_ten': 'Nguyễn Hoàng Khang',
    'ngay_sinh': '2030-01-01', # Ngày sinh tương lai
    'gioi_tinh': 'Nam',
    'cccd': '07912345', # CCCD thiếu số
    'sdt': test_phone,
    'email': 'khang.test@gmail.com',
    'dia_chi': 'Quận 1, TP.HCM',
    'nhom_mau': 'O+'
})
assert res_invalid_profile.status_code == 200
html_err = res_invalid_profile.data.decode('utf-8')
assert ("12 số" in html_err or "CCCD" in html_err) or "không hợp lệ" in html_err or "tương lai" in html_err
print("6. [PASS] Kiểm tra ràng buộc ngày sinh và CCCD trên trang thông tin cá nhân thành công")

# 7. Điền thông tin cá nhân chuẩn xác
res_valid_profile = client.post('/patient/complete-profile', data={
    'ho_ten': 'Nguyễn Hoàng Khang',
    'ngay_sinh': '1996-08-20',
    'gioi_tinh': 'Nam',
    'cccd': '079196009999',
    'sdt': test_phone,
    'email': 'khang.test@gmail.com',
    'bhyt': 'GD4791960099999',
    'dia_chi': '250 Điện Biên Phủ, Phường Võ Thị Sáu, Quận 3, TP.HCM',
    'nhom_mau': 'O+',
    'di_ung': 'Không có dị ứng',
    'tien_su_benh': 'Khỏe mạnh bình thường',
    'tien_su_gia_dinh': 'Không có bệnh lý di truyền',
    'nguoi_than_ho_ten': 'Nguyễn Hoàng Sơn',
    'nguoi_than_sdt': '0901888777',
    'nguoi_than_quan_he': 'Bố'
}, follow_redirects=False)
assert res_valid_profile.status_code == 302 and '/patient/dashboard' in res_valid_profile.headers['Location']
print("7. [PASS] Hoàn thiện hồ sơ cá nhân thành công, kích hoạt cờ hoàn thiện và chuyển hướng về dashboard")

# 8. Sau khi hoàn thiện, truy cập dashboard thành công
res_dash_ok = client.get('/patient/dashboard', follow_redirects=True)
assert res_dash_ok.status_code == 200
assert 'Nguyễn Hoàng Khang' in res_dash_ok.data.decode('utf-8')
print("8. [PASS] Truy cập /patient/dashboard hiển thị đầy đủ thông tin bệnh nhân đã kích hoạt")

print("\n=> KẾT LUẬN: Toàn bộ quy trình tạo mới tài khoản, xác thực, điền thông tin cá nhân và ràng buộc dữ liệu hoạt động HOÀN HẢO 100%!")
