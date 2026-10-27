import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import get_db
from models.schedule_model import ScheduleModel

def seed_staff_shifts():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nv.id, nv.ho_ten, v.ma_vai_tro, v.ten_vai_tro 
        FROM nhan_vien nv 
        JOIN tai_khoan t ON nv.tai_khoan_id = t.id 
        JOIN vai_tro v ON t.vai_tro_id = v.id 
        WHERE v.ma_vai_tro IN ('LETAN', 'KTV', 'DUOCSI')
    """)
    staff_list = cursor.fetchall()
    if not staff_list:
        print("Không có nhân sự LETAN, KTV, DUOCSI.")
        return

    cursor.execute("SELECT id FROM phong_kham")
    rooms = [r['id'] for r in cursor.fetchall()] or [1]

    bounds = ScheduleModel.get_week_bounds()
    cur_start, cur_end = bounds['current_week']
    next1_start, next1_end = bounds['next_week_1']

    cur_days = ScheduleModel.get_week_days(cur_start)
    next_days = ScheduleModel.get_week_days(next1_start)
    all_target_days = cur_days + next_days

    inserted_count = 0
    for day in all_target_days:
        date_str = day['date_str']
        for ca_id in [1, 2, 3]:
            # Assign 1-2 staff members for each shift
            assigned_staff = staff_list[(inserted_count) % len(staff_list)]
            assigned_staff_2 = staff_list[(inserted_count + 1) % len(staff_list)]
            
            for st in [assigned_staff, assigned_staff_2]:
                cursor.execute("""
                    SELECT id FROM lich_lam_viec 
                    WHERE nhan_vien_id = ? AND ngay_lam = ? AND ca_lam = ?
                """, (st['id'], date_str, ca_id))
                if cursor.fetchone():
                    continue

                cursor.execute("""
                    INSERT INTO lich_lam_viec (
                        nhan_vien_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam,
                        gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky,
                        trang_thai, trang_thai_duyet, ghi_chu
                    ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, 1, 'DA_DUYET', ?)
                """, (
                    st['id'], rooms[0], date_str, ca_id,
                    '07:00' if ca_id == 1 else '13:30' if ca_id == 2 else '17:30',
                    '11:30' if ca_id == 1 else '17:00' if ca_id == 2 else '20:30',
                    30, 0,
                    f"Trực vị trí {st['ten_vai_tro']}"
                ))
                inserted_count += 1

    conn.commit()
    conn.close()
    print(f"Đã phân công thành công {inserted_count} ca trực cho nhân viên tiếp tân, KTV và dược sĩ.")

if __name__ == '__main__':
    seed_staff_shifts()
