import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date, timedelta
from core.database import get_db

sys.stdout.reconfigure(encoding='utf-8')

def seed_schedules():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT bs.id AS bac_si_id, bs.nhan_vien_id, bs.phong_kham_chinh_id, bs.chuyen_khoa_id, nv.ho_ten, ck.ten_khoa
        FROM bac_si bs
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        ORDER BY bs.chuyen_khoa_id, bs.id
    ''')
    doctors = cur.fetchall()
    print(f"Tim thay {len(doctors)} bac si.")

    # Xóa lịch cũ nếu có
    cur.execute("DELETE FROM lich_lam_viec")

    shifts = {
        1: ('07:00:00', '11:30:00'),
        2: ('13:30:00', '17:00:00'),
        3: ('17:30:00', '20:30:00')
    }

    # Gom bác sĩ theo chuyên khoa (mỗi khoa 5 bác sĩ)
    dept_doctors = {}
    for d in doctors:
        ck = d['chuyen_khoa_id']
        dept_doctors.setdefault(ck, []).append(d)

    today = date.today()
    inserted_count = 0

    # Tạo lịch cho 14 ngày tới (từ hôm nay đến ngày 14)
    for day_offset in range(14):
        target_date = today + timedelta(days=day_offset)
        date_str = target_date.strftime('%Y-%m-%d')

        for ck_id, doc_list in dept_doctors.items():
            # Trong 5 bác sĩ của mỗi khoa:
            # Luân phiên ca theo ngày:
            # Bác sĩ 0, 1: Ca 1 (Sáng)
            # Bác sĩ 2, 3: Ca 2 (Chiều)
            # Bác sĩ 4: Ca 3 (Tối)
            # Xoay vòng (shift rotation) theo ngày
            n_docs = len(doc_list)
            for idx, doc in enumerate(doc_list):
                # Gán ca trực luân phiên
                shift_idx = ((idx + day_offset) % 3) + 1  # 1, 2, hoặc 3
                start_time, end_time = shifts[shift_idx]

                cur.execute('''
                    INSERT INTO lich_lam_viec (
                        bac_si_id, nhan_vien_id, phong_kham_id, ngay_lam, ca_lam,
                        gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky,
                        trang_thai, trang_thai_duyet
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 20, 0, 1, 'DA_DUYET')
                ''', (
                    doc['bac_si_id'],
                    doc['nhan_vien_id'],
                    doc['phong_kham_chinh_id'],
                    date_str,
                    shift_idx,
                    start_time,
                    end_time
                ))
                inserted_count += 1

    conn.commit()
    conn.close()
    print(f"Da tao thanh cong {inserted_count} ca truc trong 14 ngay cho 35 bac si!")

if __name__ == '__main__':
    seed_schedules()
