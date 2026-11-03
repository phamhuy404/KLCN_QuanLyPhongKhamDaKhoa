import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from models.user_model import UserModel

app = create_app()
app.testing = True
app.config['DATABASE_ACCESS_ENABLED'] = True
client = app.test_client()

print("BẮT ĐẦU KIỂM THỬ TOÀN DIỆN CÁC PHÂN HỆ VÀ ROUTE:")

# 1. KIỂM THỬ CỔNG THÔNG TIN CÔNG KHAI (PUBLIC WEB)
public_routes = [
    ('/', 200, 'Trang chủ'),
    ('/articles', 200, 'Tin tức / Cẩm nang y tế'),
    ('/pricing', 200, 'Bảng giá dịch vụ'),
    ('/doctors', 200, 'Đội ngũ bác sĩ'),
    ('/departments', 200, 'Chuyên khoa'),
    ('/login', 200, 'Đăng nhập'),
    ('/register', 200, 'Đăng ký'),
    ('/maintenance/patient', 200, 'Bảo trì Bệnh nhân'),
    ('/maintenance/staff', 200, 'Bảo trì Nhân viên')
]

print("\n--- 1. Kiểm tra Route công khai ---")
for path, expected_status, name in public_routes:
    res = client.get(path)
    assert res.status_code == expected_status, f"Route {path} trả về {res.status_code}, mong đợi {expected_status}"
    print(f"  [OK] {name:<30} ({path}): HTTP {res.status_code}")

# 2. KIỂM THỬ ĐĂNG NHẬP ĐA PHƯƠNG THỨC
print("\n--- 2. Kiểm tra Đăng nhập đa phương thức ---")
# 2.1 Username Admin
admin_auth = UserModel.authenticate('admin', 'admin123')
assert admin_auth is not None, "Đăng nhập bằng username admin thất bại"
print("  [OK] Đăng nhập bằng Username 'admin': Thành công")

# 2.2 Số điện thoại Bác sĩ ('0912111001' / 'Password@123')
bs_auth = UserModel.authenticate('0912111001', 'Password@123')
assert bs_auth is not None, "Đăng nhập bằng SĐT bác sĩ thất bại"
print(f"  [OK] Đăng nhập bằng SĐT Bác sĩ '0912111001': Thành công ({bs_auth['ho_ten']})")

# 2.3 Số điện thoại Bệnh nhân ('0901234561' / '123456')
bn_sdt_auth = UserModel.authenticate('0901234561', '123456')
assert bn_sdt_auth is not None, "Đăng nhập bằng SĐT bệnh nhân thất bại"
print(f"  [OK] Đăng nhập bằng SĐT Bệnh nhân '0901234561': Thành công ({bn_sdt_auth['ho_ten']})")

# 2.4 Mã bệnh nhân ('BN0001' / '123456')
bn_auth = UserModel.authenticate('BN0001', '123456')
assert bn_auth is not None, "Đăng nhập bằng Mã BN0001 thất bại"
print(f"  [OK] Đăng nhập bằng Mã 'BN0001': Thành công ({bn_auth['ho_ten']})")

# 3. KIỂM THỬ CỔNG DỊCH VỤ BỆNH NHÂN (PATIENT PORTAL)
print("\n--- 3. Kiểm tra Cổng Dịch vụ Bệnh nhân ---")
patient_identity = UserModel.get_session_user(bn_auth['id'])

with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = patient_identity

patient_routes = [
    ('/patient/dashboard', 200, 'Tổng quan bệnh nhân'),
    ('/patient/appointments', 200, 'Lịch hẹn cá nhân'),
    ('/patient/records', 200, 'Hồ sơ bệnh án EMR'),
    ('/patient/lab-results', 200, 'Kết quả cận lâm sàng'),
    ('/patient/billing', 200, 'Hóa đơn viện phí'),
    ('/patient/profile', 200, 'Hồ sơ cá nhân'),
    ('/patient/feedbacks', 200, 'Đánh giá & Góp ý'),
    ('/patient/notifications', 200, 'Hộp thư thông báo')
]

for path, expected_status, name in patient_routes:
    res = client.get(path)
    assert res.status_code == expected_status, f"Route {path} trả về {res.status_code}, mong đợi {expected_status}"
    print(f"  [OK] {name:<30} ({path}): HTTP {res.status_code}")

# Bệnh nhân không được phép vào admin
res_patient_in_admin = client.get('/admin/dashboard')
assert res_patient_in_admin.status_code in (302, 403), f"Bệnh nhân vào admin không bị chặn: {res_patient_in_admin.status_code}"
print("  [OK] Bệnh nhân truy cập /admin/dashboard: Bị chặn thành công (RBAC)")

# 4. KIỂM THỬ PHÂN HỆ QUẢN TRỊ ADMIN (ADMIN PORTAL)
print("\n--- 4. Kiểm tra Phân hệ Quản trị Admin ---")
admin_identity = UserModel.get_session_user(1)

with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = admin_identity

admin_routes = [
    ('/admin/dashboard', 200, 'Bảng điều khiển Admin'),
    ('/admin/patients', 200, 'Quản lý Bệnh nhân'),
    ('/admin/reception', 200, 'Tiếp nhận & Lễ tân'),
    ('/admin/appointments', 200, 'Lịch hẹn khám toàn viện'),
    ('/admin/emr', 200, 'Bệnh án điện tử EMR'),
    ('/admin/lab', 200, 'Cận lâm sàng & Xét nghiệm'),
    ('/admin/pharmacy', 200, 'Kho dược & Quầy phát thuốc'),
    ('/admin/billing', 200, 'Viện phí & Thu ngân'),
    ('/admin/reports', 200, 'Báo cáo thống kê'),
    ('/admin/catalogs', 200, 'Danh mục y tế'),
    ('/admin/staff', 200, 'Nhân sự & Lịch trực'),
    ('/admin/feedbacks', 200, 'Quản lý Đánh giá'),
    ('/admin/backups', 200, 'Sao lưu & Bảo trì'),
    ('/admin/accounts', 302, 'Điều hướng Quản trị Tài khoản -> Nhân sự'),
    ('/admin/articles', 200, 'Quản lý Bài viết'),
    ('/admin/banners', 200, 'Quản lý Banner')
]

for path, expected_status, name in admin_routes:
    res = client.get(path)
    assert res.status_code == expected_status, f"Route {path} trả về {res.status_code}, mong đợi {expected_status}"
    print(f"  [OK] {name:<30} ({path}): HTTP {res.status_code}")

# 5. KIỂM THỬ CÁC API THỜI GIAN THỰC & BẢO TRÌ
print("\n--- 5. Kiểm tra API Thời gian thực & Tiện ích ---")
api_routes = [
    ('/api/maintenance/status', 200, 'Trạng thái bảo trì'),
    ('/api/schedule/week?offset=0', 200, 'Lịch trực tuần hiện tại'),
    ('/api/notifications/poll', 200, 'Polling thông báo thời gian thực')
]

for path, expected_status, name in api_routes:
    res = client.get(path)
    assert res.status_code == expected_status, f"API {path} trả về {res.status_code}, mong đợi {expected_status}"
    print(f"  [OK] {name:<30} ({path}): HTTP {res.status_code}")

print("\nTOÀN BỘ CÁC BÀI KIỂM THỬ TẤT CẢ ROUTE VÀ PHÂN QUYỀN ĐÃ ĐẠT 100%!")
