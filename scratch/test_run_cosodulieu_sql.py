import pyodbc
import re
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=master;Trusted_Connection=yes;', autocommit=True)
cursor = conn.cursor()

with open('cosodulieu.sql', 'r', encoding='utf-8') as f:
    sql_text = f.read()

# Tách các lô lệnh theo lệnh GO (không phân biệt hoa thường, nằm riêng trên 1 dòng)
batches = re.split(r'^\s*GO\s*$', sql_text, flags=re.MULTILINE | re.IGNORECASE)

print(f"Tổng số batches cần thực thi: {len(batches)}")

errors = []
for idx, batch in enumerate(batches, 1):
    cleaned = batch.strip()
    if not cleaned:
        continue
    try:
        cursor.execute(cleaned)
        while cursor.nextset():
            pass
    except Exception as e:
        errors.append((idx, str(e), cleaned[:200]))
        print(f"[LỖI BATCH {idx}]: {e}")

conn.close()

if errors:
    print(f"\n[THẤT BẠI] Có {len(errors)} lỗi khi thực thi cosodulieu.sql:")
    for b_idx, err_msg, snippet in errors:
        print(f"--- Batch {b_idx}: {err_msg}")
        print(f"    Snippet: {snippet.strip()}\n")
else:
    print("\n[THÀNH CÔNG RỰC RỠ] Đã thực thi 100% cosodulieu.sql trong 1 run mà KHÔNG CÓ BẤT KỲ LỖI NÀO!")
