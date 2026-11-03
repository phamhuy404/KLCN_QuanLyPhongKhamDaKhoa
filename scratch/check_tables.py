import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db

try:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    rows = cur.fetchall()
    tables = [r['TABLE_NAME'] for r in rows]
    print("Tables:", sorted(tables))
    conn.close()
except Exception as e:
    import traceback
    traceback.print_exc()
