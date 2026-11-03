import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from core.database import get_db

conn = get_db()
c = conn.cursor()

c.execute("""
    SELECT CONVERT(VARCHAR(7), thoi_gian_thanh_toan, 120) AS thang, trang_thai, COUNT(*) AS cnt, SUM(thanh_tien) AS tong
    FROM hoa_don
    GROUP BY CONVERT(VARCHAR(7), thoi_gian_thanh_toan, 120), trang_thai
    ORDER BY thang
""")
for r in c.fetchall():
    print(r)

print("\n--- PHẢN HỒI HIỆN TẠI ---")
c.execute("SELECT TOP 5 * FROM phan_hoi")
for r in c.fetchall():
    print(dict(r))

conn.close()
