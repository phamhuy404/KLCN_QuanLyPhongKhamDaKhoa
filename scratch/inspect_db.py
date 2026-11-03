import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from core.database import get_db

conn = get_db()
c = conn.cursor()

c.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")
tables = [list(r.values())[0] if isinstance(r, dict) else r[0] for r in c.fetchall()]
print("Tables in DB:", len(tables))
for t in tables:
    print("-", t)

print("\n--- SCHEMA CỦA phan_hoi VÀ hom_thu_gop_y ---")
for tbl in ['phan_hoi', 'hom_thu_gop_y', 'hoa_don', 'chi_tiet_hoa_don', 'lich_su_kho']:
    if tbl in tables:
        c.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tbl}'")
        cols = [f"{list(r.values())[0]} ({list(r.values())[1]})" for r in c.fetchall()]
        print(f"Table {tbl}: {', '.join(cols)}")
    else:
        print(f"Table {tbl}: NOT FOUND")

conn.close()
