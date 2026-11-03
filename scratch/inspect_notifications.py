import sys, io, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from core.database import get_db

conn = get_db()
cur = conn.cursor()

cur.execute('SELECT COUNT(*) as cnt FROM thong_bao')
print('Total thong_bao:', cur.fetchone()['cnt'])

cur.execute('SELECT tieu_de, COUNT(*) as cnt FROM thong_bao GROUP BY tieu_de ORDER BY cnt DESC')
for r in cur.fetchall()[:15]:
    print(f"  {r['cnt']}x: {r['tieu_de']}")
