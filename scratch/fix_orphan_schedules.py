import io
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db

with get_db() as conn:
    cur = conn.cursor()
    cur.execute('''
        UPDATE llv
        SET llv.nhan_vien_id = bs.nhan_vien_id
        FROM lich_lam_viec llv
        JOIN bac_si bs ON llv.bac_si_id = bs.id
        WHERE llv.nhan_vien_id IS NULL AND llv.bac_si_id IS NOT NULL
    ''')
    conn.commit()
    print("Đã cập nhật nhan_vien_id cho các ca trực!")
