import sys, io, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from core.database import get_db

conn = get_db()
cur = conn.cursor()

for t, col in [('don_thuoc', 'ma_don'), ('hoa_don', 'ma_hoa_don'), ('lich_hen', 'ma_lich_hen'), ('phieu_kham', 'ma_phieu'), ('phieu_chi_dinh', 'ma_phieu')]:
    cur.execute(f"SELECT {col} FROM {t} WHERE {col} LIKE '%TEST%' OR {col} LIKE '%REJ%' OR {col} LIKE '%DEMO%'")
    rows = cur.fetchall()
    print(f"{t}.{col}: {len(rows)} matching")
    for r in rows[:5]:
        print("  ", r)
