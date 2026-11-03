import sys, io, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from core.database import get_db

conn = get_db()
cur = conn.cursor()

tables_to_check = ['benh_nhan', 'lich_hen', 'phieu_kham', 'don_thuoc', 'chi_tiet_don_thuoc', 'chi_tiet_chi_dinh', 'hoa_don', 'phan_hoi', 'thong_bao']

for t in tables_to_check:
    cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' AND DATA_TYPE IN ('varchar', 'nvarchar', 'text', 'ntext')")
    cols = [r['COLUMN_NAME'] for r in cur.fetchall()]
    
    where_clauses = " OR ".join([f"LOWER({c}) LIKE '%test%' OR LOWER({c}) LIKE '%demo%' OR LOWER({c}) LIKE '%abc%'" for c in cols])
    if where_clauses:
        sql = f"SELECT COUNT(*) as cnt FROM {t} WHERE {where_clauses}"
        cur.execute(sql)
        cnt = cur.fetchone()['cnt']
        print(f"Table {t}: {cnt} rows matching 'test'/'demo'/'abc'")
        if cnt > 0:
            cur.execute(f"SELECT TOP 5 * FROM {t} WHERE {where_clauses}")
            for row in cur.fetchall():
                print("   Sample:", {k: row[k] for k in cols if row[k] and any(w in str(row[k]).lower() for w in ['test', 'demo', 'abc'])})
