import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from core.database import get_db

conn = get_db()
c = conn.cursor()
c.execute("SELECT action, COUNT(*) AS cnt FROM audit_log WHERE table_name='thuoc' GROUP BY action")
for r in c.fetchall():
    print(r['action'], ':', r['cnt'])

c.execute("SELECT TOP 5 * FROM audit_log WHERE table_name='thuoc' ORDER BY id DESC")
for r in c.fetchall():
    print(dict(r))

conn.close()
