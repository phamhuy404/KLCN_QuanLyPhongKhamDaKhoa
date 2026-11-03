import io
import sys
import time
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from models.user_model import UserModel
from core.database import get_db

with get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tai_khoan WHERE username = 'admin'")
    row = cursor.fetchone()
    admin_id = row['id']
    admin_user = UserModel.get_session_user(admin_id)

app = create_app()
client = app.test_client()

with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = admin_user

routes_to_test = [
    ('/admin/dashboard', 'Tong quan / Dashboard'),
    ('/admin/emr', 'Kham benh EMR'),
    ('/admin/appointments', 'Lich hen kham'),
    ('/admin/staff', 'Nhan su & Lich truc'),
    ('/admin/pharmacy', 'Kho duoc & Thuoc'),
    ('/admin/billing', 'Vien phi & Thu ngan'),
    ('/admin/reports', 'Bao cao thong ke'),
]

print("BAT DAU BENCHMARK HIEU NANG CAC PHAN HE QUAN TRI (KHI DA DANG NHAP):")
for url, name in routes_to_test:
    # Warmup
    res0 = client.get(url)
    
    # Do 3 lan lay trung binh
    times = []
    size_kb = len(res0.data) / 1024
    status = res0.status_code
    for _ in range(3):
        t0 = time.perf_counter()
        res = client.get(url)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    
    avg_ms = sum(times) / len(times)
    print(f"[{status}] {url:<22} ({name:<22}): {size_kb:>8.1f} KB | {avg_ms:>7.1f} ms")

print("\nBENCHMARK API LICH SU BENH NHAN (PATIENT HISTORY):")
t0 = time.perf_counter()
res = client.get('/api/patient/1/history')
t1 = time.perf_counter()
print(f"[{res.status_code}] /api/patient/1/history: {len(res.data)/1024:.1f} KB | {(t1-t0)*1000:.1f} ms")
