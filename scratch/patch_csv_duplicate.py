import sys

filepath = 'core/csv_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

def robust_replace(src, find_str, rep_str):
    if find_str in src:
        return src.replace(find_str, rep_str), True
    find_crlf = find_str.replace('\r\n', '\n').replace('\n', '\r\n')
    rep_crlf = rep_str.replace('\r\n', '\n').replace('\n', '\r\n')
    if find_crlf in src:
        return src.replace(find_crlf, rep_crlf), True
    return src, False

old_block = """        try:
            if module == 'medicines':
                for r in data_rows:"""

new_block = """        try:
            if module == 'medicines':
                import hashlib
                from datetime import datetime
                today_str = datetime.now().strftime('%Y-%m-%d')
                csv_checksum = hashlib.md5(decoded.strip().encode('utf-8')).hexdigest()[:12]
                
                # Kiểm tra chống nhập trùng: nếu cùng file CSV này đã được nhập trong ngày hôm nay
                cursor.execute('''
                    SELECT TOP 1 id, performed_at FROM audit_log 
                    WHERE table_name = 'thuoc' AND action = 'STOCK_IN'
                      AND reason LIKE ? AND CAST(performed_at AS DATE) = CAST(GETDATE() AS DATE)
                ''', (f"%[{csv_checksum}]%",))
                dup_log = cursor.fetchone()
                if dup_log:
                    conn.close()
                    return False, f"⚠️ Tệp CSV này đã được nhập vào kho thuốc trong ngày hôm nay ({today_str})! Hệ thống tự động chặn nhập trùng để tránh cộng dồn sai lệch tồn kho.", 0, 0

                for r in data_rows:"""

content, ok1 = robust_replace(content, old_block, new_block)
print("Updated duplicate check in csv_service.py:", ok1)

old_journal_1 = """journal(cursor, existing['id'], qty, existing['so_luong_ton'], new_ton, current_user, 'CSV receipt')"""
new_journal_1 = """journal(cursor, existing['id'], qty, existing['so_luong_ton'], new_ton, current_user, f'CSV receipt [{csv_checksum}]')"""
content, ok2 = robust_replace(content, old_journal_1, new_journal_1)
print("Updated journal 1:", ok2)

old_journal_2 = """journal(cursor, cursor.lastrowid, qty, 0, qty, current_user, 'CSV initial stock')"""
new_journal_2 = """journal(cursor, cursor.lastrowid, qty, 0, qty, current_user, f'CSV initial stock [{csv_checksum}]')"""
content, ok3 = robust_replace(content, old_journal_2, new_journal_2)
print("Updated journal 2:", ok3)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done updating core/csv_service.py!")
