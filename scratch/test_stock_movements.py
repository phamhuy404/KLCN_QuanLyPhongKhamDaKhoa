import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from core.database import get_db

conn = get_db()
c = conn.cursor()

c.execute("""
    SELECT a.id, a.row_id AS thuoc_id, a.action, a.performed_by, a.performed_by_name,
           a.performed_at, a.reason, a.before_json, a.after_json,
           t.ma_thuoc, t.ten_thuoc, t.don_vi_tinh, t.hoat_chat
    FROM audit_log a
    JOIN thuoc t ON a.row_id = t.id
    WHERE a.table_name = 'thuoc' AND a.action IN ('STOCK_IN', 'STOCK_OUT')
    ORDER BY a.id DESC
""")
rows = [dict(r) for r in c.fetchall()]
print(f"Found {len(rows)} stock audit entries.")
for r in rows[:5]:
    after = json.loads(r.get('after_json') or '{}')
    before = json.loads(r.get('before_json') or '{}')
    delta = after.get('delta', 0)
    receipt = after.get('receipt')
    print(f"ID {r['id']} | {r['performed_at']} | {r['ten_thuoc']} ({r['ma_thuoc']}) | Delta: {delta} | Stock: {before.get('stock')} -> {after.get('stock')} | Receipt: {receipt} | Reason: {r['reason']}")

conn.close()
