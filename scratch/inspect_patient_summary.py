import sys, io, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from core.database import get_db

conn = get_db()
cur = conn.cursor()

cur.execute('''
    SELECT bn.id, bn.ma_benh_nhan, bn.ho_ten, tk.username
    FROM benh_nhan bn
    JOIN tai_khoan tk ON bn.tai_khoan_id = tk.id
    ORDER BY bn.id
''')
patients = cur.fetchall()
print(f"{'Mã BN':10s} | {'Họ tên':20s} | {'Tài khoản':12s} | {'Lịch hẹn':8s} | {'Phiếu khám':10s} | {'Hóa đơn':8s} | {'Thông báo':10s}")
print("-" * 85)

for p in patients:
    cur.execute('SELECT COUNT(*) as cnt FROM lich_hen WHERE benh_nhan_id = ?', (p['id'],))
    lh = cur.fetchone()['cnt']
    cur.execute('SELECT COUNT(*) as cnt FROM phieu_kham WHERE benh_nhan_id = ?', (p['id'],))
    pk = cur.fetchone()['cnt']
    cur.execute('SELECT COUNT(*) as cnt FROM hoa_don WHERE benh_nhan_id = ?', (p['id'],))
    hd = cur.fetchone()['cnt']
    cur.execute('SELECT COUNT(*) as cnt FROM thong_bao WHERE tai_khoan_id = (SELECT tai_khoan_id FROM benh_nhan WHERE id = ?)', (p['id'],))
    tb = cur.fetchone()['cnt']
    print(f"{p['ma_benh_nhan']:10s} | {p['ho_ten']:20s} | {str(p['username']):12s} | {lh:8d} | {pk:10d} | {hd:8d} | {tb:10d}")
