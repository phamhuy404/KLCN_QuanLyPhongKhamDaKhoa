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

print("Bắt đầu kiểm thử Hệ thống Bảo trì & Animation...")

# 1. Reset cài đặt về False trước khi test
SystemSettingModel.toggle_maintenance('patient', enabled=False, user_name='test_setup')
SystemSettingModel.toggle_maintenance('staff', enabled=False, user_name='test_setup')
s = SystemSettingModel.get_settings(force_reload=True)
print("1. Cài đặt ban đầu:", {k: s[k] for k in ('maintenance_patient', 'maintenance_staff', 'maintenance_eta')})

# 2. Kiểm tra API Public Status
res = client.get('/api/maintenance/status')
assert res.status_code == 200
data = res.get_json()
assert 'maintenance_patient' in data
assert 'maintenance_staff' in data
print("2. GET /api/maintenance/status thành công (HTTP 200)")

# 3. Kiểm tra trang hiển thị bảo trì
res_pt = client.get('/maintenance/patient')
assert res_pt.status_code == 200
print("3.1 GET /maintenance/patient thành công (HTTP 200)")

res_st = client.get('/maintenance/staff')
assert res_st.status_code == 200
print("3.2 GET /maintenance/staff thành công (HTTP 200)")

admin_identity = UserModel.get_session_user(1)
assert admin_identity is not None and admin_identity['vai_tro'] == 'ADMIN'

doctor_identity = UserModel.get_session_user(17)
assert doctor_identity is not None and doctor_identity['vai_tro'] == 'BACSI'

# 4. Kiểm tra Middleware khi bật bảo trì Bệnh nhân
SystemSettingModel.toggle_maintenance('patient', enabled=True, user_name='test_admin')

# 4.1 Khách truy cập /booking hoặc /register
res_blocked_booking = client.get('/booking')
assert res_blocked_booking.status_code == 302
assert '/maintenance/patient' in res_blocked_booking.headers.get('Location', '')
print("4.1 Khách truy cập /booking đã bị chặn thành công -> redirect /maintenance/patient")

res_blocked_reg = client.get('/register')
assert res_blocked_reg.status_code == 302
assert '/maintenance/patient' in res_blocked_reg.headers.get('Location', '')
print("4.2 Khách truy cập /register đã bị chặn thành công -> redirect /maintenance/patient")

# 4.3 Khách truy cập trang đăng nhập /login (Phải CHO PHÉP để Admin có thể đăng nhập!)
res_login_ok = client.get('/login')
assert res_login_ok.status_code == 200
print("4.3 Khách truy cập /login vẫn truy cập bình thường (HTTP 200)")

# 4.4 Admin truy cập /admin/backups (Admin KHÔNG BAO GIỜ bị chặn)
with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = admin_identity

res_admin_access = client.get('/admin/backups')
assert res_admin_access.status_code == 200
print("4.4 Admin truy cập /admin/backups thành công (HTTP 200, Không bao giờ bị chặn)")

# 5. Kiểm tra Middleware khi bật bảo trì Nhân viên y tế
SystemSettingModel.toggle_maintenance('staff', enabled=True, user_name='test_admin')

# 5.1 Bác sĩ truy cập /admin/dashboard
with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = doctor_identity

res_doctor_blocked = client.get('/admin/dashboard')
assert res_doctor_blocked.status_code == 302
assert '/maintenance/staff' in res_doctor_blocked.headers.get('Location', '')
print(f"5.1 Bác sĩ ({doctor_identity['ho_ten']}) truy cập /admin/dashboard đã bị chặn thành công -> redirect /maintenance/staff")

# 5.2 Bác sĩ gọi API /api/schedule
res_doctor_api_blocked = client.get('/api/schedule/week?offset=0')
assert res_doctor_api_blocked.status_code == 503
data_api = res_doctor_api_blocked.get_json()
assert data_api['maintenance'] is True
print("5.2 Bác sĩ gọi API phân hệ đã nhận phản hồi HTTP 503 Bảo trì thành công")

# 5.3 Admin vẫn truy cập bình thường khi bảo trì nhân viên bật
with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = admin_identity

res_admin_still_ok = client.get('/admin/backups')
assert res_admin_still_ok.status_code == 200
print("5.3 Admin truy cập /admin/backups trong lúc bảo trì nhân viên thành công (HTTP 200)")

# 6. Đưa hệ thống về trạng thái bình thường (Tắt cả 2 bảo trì)
SystemSettingModel.toggle_maintenance('patient', enabled=False, user_name='test_admin')
SystemSettingModel.toggle_maintenance('staff', enabled=False, user_name='test_admin')

final_settings = SystemSettingModel.get_settings(force_reload=True)
assert final_settings['maintenance_patient'] is False
assert final_settings['maintenance_staff'] is False
print("6. Đã tắt bảo trì, hệ thống trở về trạng thái mở cửa bình thường")

print("\nTOÀN BỘ CÁC BÀI KIỂM THỬ BẢO TRÌ & CHẶN TRUY CẬP ĐÃ ĐẠT 100%!")
