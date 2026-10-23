import pyodbc
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;', autocommit=True)
cursor = conn.cursor()

import os
sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'cosodulieu.sql')
with open(sql_path, 'r', encoding='utf-8') as f:
    text = f.read()

batches = re.split(r'^\s*GO\s*$', text, flags=re.MULTILINE|re.IGNORECASE)
batch_17 = batches[16].strip()

try:
    cursor.execute(batch_17)
    print("Batch 17 executed successfully!")
except Exception as e:
    print("Batch 17 error:", e)

conn.close()
