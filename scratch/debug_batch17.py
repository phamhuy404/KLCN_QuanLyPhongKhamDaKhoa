import pyodbc
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Connect directly to database
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;', autocommit=True)
cursor = conn.cursor()

# Clean table first
cursor.execute("SET IDENTITY_INSERT lich_lam_viec OFF;")
cursor.execute("DELETE FROM lich_lam_viec;")

import os
sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'cosodulieu.sql')
with open(sql_path, 'r', encoding='utf-8') as f:
    text = f.read()

batches = re.split(r'^\s*GO\s*$', text, flags=re.MULTILINE|re.IGNORECASE)
batch_17 = batches[16].strip()

# Let's split batch 17 by individual SQL statements (by semicolon)
stmts = [s.strip() for s in batch_17.split(';') if s.strip()]
print(f"Batch 17 contains {len(stmts)} statements.")

for idx, stmt in enumerate(stmts, 1):
    try:
        cursor.execute(stmt)
    except Exception as e:
        print(f"Error on statement {idx}: {e}")
        print(f"Statement text: {stmt[:150]}")
        break
else:
    print("ALL statements in Batch 17 succeeded!")

conn.close()
