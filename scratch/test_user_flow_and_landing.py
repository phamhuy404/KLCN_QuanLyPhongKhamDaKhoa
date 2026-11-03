import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from models.system_setting_model import SystemSettingModel
from models.user_model import UserModel

app = create_app()
app.testing = True
app.config['DATABASE_ACCESS_ENABLED'] = True
client = app.test_client()

print("KIỂM THỬ LUỒNG ĐĂNG NHẬP TRANG HOME VÀ TRUY CẬP TÀI KHOẢN KHI BẢO TRÌ:")

# 1. Reset trạng thái bảo trì về False
SystemSettingModel.toggle_maintenance('patient', enabled=False, user_name='test')
SystemSettingModel.toggle_maintenance('staff', enabled=False, user_name='test')

# 2. Kiểm tra Đăng nhập -> Bắt đầu ở trang Home
print("\n--- 1. Kiểm tra luồng Đăng nhập -> Trang Home ---")

# 2.1 Bệnh nhân đăng nhập
res_login_bn = client.post('/login', data={'username': '0901234561', 'password': '123456'})
assert res_login_bn.status_code == 302
assert res_login_bn.headers.get('Location') in ('/', '/home', 'http://localhost/', 'http://localhost/home'), f"Bệnh nhân không về trang home: {res_login_bn.headers.get('Location')}"
print("  [OK] Bệnh nhân đăng nhập -> Chuyển hướng về trang Home (/home)")

# 2.2 Nhân viên / Bác sĩ đăng nhập
res_login_bs = client.post('/login', data={'username': '0912111001', 'password': 'Password@123'})
assert res_login_bs.status_code == 302
assert res_login_bs.headers.get('Location') in ('/', '/home', 'http://localhost/', 'http://localhost/home'), f"Bác sĩ không về trang home: {res_login_bs.headers.get('Location')}"
print("  [OK] Bác sĩ đăng nhập -> Chuyển hướng về trang Home (/home)")

# 2.3 Admin đăng nhập
res_login_admin = client.post('/login', data={'username': 'admin', 'password': 'admin123'})
assert res_login_admin.status_code == 302
assert res_login_admin.headers.get('Location') in ('/', '/home', 'http://localhost/', 'http://localhost/home'), f"Admin không về trang home: {res_login_admin.headers.get('Location')}"
print("  [OK] Admin đăng nhập -> Chuyển hướng về trang Home (/home)")

# 3. KÍCH HOẠT BẢO TRÌ VÀ KIỂM TRA TRUY CẬP TRANG HOME VÀ TÀI KHOẢN
print("\n--- 2. Kích hoạt bảo trì Bệnh nhân ---")
SystemSettingModel.toggle_maintenance('patient', enabled=True, user_name='test')

bn_identity = UserModel.get_session_user(52)  # Hoàng Bảo Nam
with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = bn_identity

# Bệnh nhân VẪN TRUY CẬP ĐƯỢC trang Home
res_bn_home = client.get('/')
assert res_bn_home.status_code == 200, f"Bệnh nhân bị chặn ở trang Home: {res_bn_home.status_code}"
print("  [OK] Bệnh nhân truy cập trang Home (/) khi bảo trì: Thành công (HTTP 200, Không bị chặn)")

res_bn_pricing = client.get('/pricing')
assert res_bn_pricing.status_code == 200
print("  [OK] Bệnh nhân truy cập trang Bảng giá (/pricing) khi bảo trì: Thành công (HTTP 200)")

# Bệnh nhân truy cập vào TÀI KHOẢN -> BỊ CHẶN VÀ ĐƯA TỚI TRANG BẢO TRÌ
res_bn_dashboard = client.get('/patient/dashboard')
assert res_bn_dashboard.status_code == 302
assert '/maintenance/patient' in res_bn_dashboard.headers.get('Location', '')
print("  [OK] Bệnh nhân truy cập /patient/dashboard: Chuyển hướng tới /maintenance/patient")

res_bn_booking = client.get('/booking')
assert res_bn_booking.status_code == 302
assert '/maintenance/patient' in res_bn_booking.headers.get('Location', '')
print("  [OK] Bệnh nhân bấm Đặt lịch (/booking): Chuyển hướng tới /maintenance/patient")

# Kiểm tra trang /maintenance/patient: Thiết kế giống web chính
res_page_pt = client.get('/maintenance/patient')
assert res_page_pt.status_code == 200
content_pt = res_page_pt.get_data(as_text=True)
assert 'H2T Healthcare' in content_pt
assert 'Trang chủ' in content_pt
assert 'BẢN ĐỒ PHÒNG KHÁM' in content_pt or 'Bản đồ' in content_pt or 'Google Maps' in content_pt
assert 'Cổng Dịch Vụ Bệnh Nhân' in content_pt or 'Hệ Thống Đang' in content_pt
print("  [OK] Trang /maintenance/patient có đầy đủ Header, Navbar, Footer giống web chính (HTTP 200)")

print("\n--- 3. Kích hoạt bảo trì Nhân viên y tế ---")
SystemSettingModel.toggle_maintenance('staff', enabled=True, user_name='test')

bs_identity = UserModel.get_session_user(17)  # BS. Trần Minh Quân
with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = bs_identity

# Bác sĩ VẪN TRUY CẬP ĐƯỢC trang Home
res_bs_home = client.get('/')
assert res_bs_home.status_code == 200, f"Bác sĩ bị chặn ở trang Home: {res_bs_home.status_code}"
print("  [OK] Bác sĩ truy cập trang Home (/) khi bảo trì: Thành công (HTTP 200, Không bị chặn)")

# Bác sĩ truy cập vào PHÂN HỆ TÀI KHOẢN/NGHIỆP VỤ -> BỊ CHẶN VÀ ĐƯA TỚI TRANG BẢO TRÌ NHÂN VIÊN
res_bs_dashboard = client.get('/admin/dashboard')
assert res_bs_dashboard.status_code == 302
assert '/maintenance/staff' in res_bs_dashboard.headers.get('Location', '')
print("  [OK] Bác sĩ truy cập /admin/dashboard: Chuyển hướng tới /maintenance/staff")

# Kiểm tra trang /maintenance/staff: Thiết kế giống web chính
res_page_st = client.get('/maintenance/staff')
assert res_page_st.status_code == 200
content_st = res_page_st.get_data(as_text=True)
assert 'H2T HIS & EMR' in content_st or 'H2T' in content_st
assert 'Trang chủ' in content_st
assert 'Quy Trình Dự Phòng Lâm Sàng Ngoại Tuyến' in content_st or 'Offline Protocol' in content_st
print("  [OK] Trang /maintenance/staff có đầy đủ Header, Navbar, Footer giống web chính (HTTP 200)")

# 4. ADMIN KHÔNG BAO GIỜ BỊ CHẶN
admin_identity = UserModel.get_session_user(1)
with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = admin_identity

res_admin_access = client.get('/admin/backups')
assert res_admin_access.status_code == 200
print("\n--- 4. Kiểm tra Quản trị viên (ADMIN) ---")
print("  [OK] Admin truy cập /admin/backups khi bảo trì đang bật: Thành công (HTTP 200, Toàn quyền)")

# 5. Dọn dẹp: Tắt bảo trì
SystemSettingModel.toggle_maintenance('patient', enabled=False, user_name='test')
SystemSettingModel.toggle_maintenance('staff', enabled=False, user_name='test')
print("\n  [OK] Đã tắt bảo trì, đưa CSDL về trạng thái hoạt động bình thường")

print("\nTOÀN BỘ CÁC BÀI KIỂM THỬ THEO YÊU CẦU MỚI ĐÃ ĐẠT 100%!")
