import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
from core.database import get_db

conn = get_db()
c = conn.cursor()

# 1. Chuan hoa ky tu 'Đã khám' trong lich_hen
c.execute("UPDATE lich_hen SET trang_thai = N'Đã khám' WHERE trang_thai LIKE N'%ã khám'")

# 2. Chuan hoa hinh_thuc_mua trong don_thuoc
c.execute("UPDATE don_thuoc SET hinh_thuc_mua = N'Mua tại bệnh viện' WHERE hinh_thuc_mua = 'BENH_VIEN' OR hinh_thuc_mua = N'Mua tại bệnh viện'")
c.execute("UPDATE don_thuoc SET hinh_thuc_mua = N'Tự mua ngoài' WHERE hinh_thuc_mua = 'NGOAI' OR hinh_thuc_mua = N'Tự mua ngoài'")

conn.commit()
print('Standardized statuses successfully!')

c.execute('SELECT trang_thai, count(*) as cnt FROM lich_hen GROUP BY trang_thai')
for r in c.fetchall():
    print('lich_hen:', r['trang_thai'], r['cnt'])

c.execute('SELECT hinh_thuc_mua, trang_thai, count(*) as cnt FROM don_thuoc GROUP BY hinh_thuc_mua, trang_thai')
for r in c.fetchall():
    print('don_thuoc:', r['hinh_thuc_mua'], r['trang_thai'], r['cnt'])

conn.close()
