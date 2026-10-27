import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import get_db

def seed_reports_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, ho_ten FROM benh_nhan")
    patients = cursor.fetchall()
    if not patients:
        print("Không có bệnh nhân trong CSDL.")
        return

    cursor.execute("""
        SELECT bs.id, nv.ho_ten, bs.chuyen_khoa_id, ck.ten_khoa 
        FROM bac_si bs 
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id 
        LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
    """)
    doctors = cursor.fetchall()
    if not doctors:
        print("Không có bác sĩ trong CSDL.")
        return

    cursor.execute("SELECT id FROM phong_kham")
    rooms = cursor.fetchall()
    room_ids = [r['id'] for r in rooms] if rooms else [1]

    icd_samples = [
        ('K29 - Viêm dạ dày và tá tràng', 'K29', 'Đau thượng vị âm ỉ sau ăn', 'Điều trị nội khoa, kháng tiết acid'),
        ('I10 - Tăng huyết áp nguyên phát', 'I10', 'Hoa mắt, chóng mặt nhẹ khi thay đổi tư thế', 'Thuốc hạ áp hàng ngày, ăn nhạt'),
        ('J30 - Viêm mũi xoang dị ứng', 'J30', 'Hắt hơi, nghẹt mũi từng cơn theo thời tiết', 'Kháng histamin, xịt mũi tại chỗ'),
        ('E11 - Đái tháo đường type 2', 'E11', 'Khát nước nhiều, sụt cân nhẹ', 'Metformin, chế độ ăn kiêng tinh bột'),
        ('J45 - Hen phế quản (Suyễn)', 'J45', 'Khó thở rít về đêm, ho khan', 'Khí dung cắt cơn, dự phòng corticoid'),
        ('J00 - Viêm mũi họng cấp (Cảm thường)', 'J00', 'Đau họng, sốt nhẹ 38 độ', 'Hạ sốt, súc họng nước muối, vitamin C'),
        ('M54 - Đau lưng cơ năng', 'M54', 'Đau mỏi thắt lưng sau khi mang vác nặng', 'Giảm đau chống viêm, vật lý trị liệu'),
        ('Z00.0 - Khám sức khỏe tổng quát', 'Z00.0', 'Kiểm tra sức khỏe định kỳ', 'Sức khỏe loại 1, duy trì sinh hoạt lành mạnh')
    ]

    payment_methods = [
        ('Tiền mặt', 0.35),
        ('Chuyển khoản', 0.30),
        ('VNPAY', 0.15),
        ('Thẻ POS', 0.12),
        ('BHYT chi trả', 0.08)
    ]

    now = datetime.now()
    created_count = 0

    for i in range(30):
        days_ago = random.randint(0, 14)
        hours_ago = random.randint(8, 17)
        minutes_ago = random.randint(0, 59)
        exam_time = now - timedelta(days=days_ago, hours=(now.hour - hours_ago), minutes=minutes_ago)
        
        p = random.choice(patients)
        d = random.choice(doctors)
        room_id = random.choice(room_ids)
        icd_info = random.choice(icd_samples)
        
        ma_phieu = f"PK{exam_time.strftime('%y%m%d')}{i+100:03d}"
        
        cursor.execute("SELECT id FROM phieu_kham WHERE ma_phieu = ?", (ma_phieu,))
        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO phieu_kham (
                ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id,
                thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo,
                chan_doan_icd, huong_dieu_tri, loi_dan, trang_thai
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ma_phieu, p['id'], d['id'], room_id,
            exam_time, icd_info[2], icd_info[2], icd_info[0],
            icd_info[1], icd_info[3], 'Tái khám sau 1-2 tuần nếu có dấu hiệu bất thường',
            'Đã hoàn thành'
        ))
        
        cursor.execute("SELECT @@IDENTITY AS id")
        phieu_id = cursor.fetchone()['id']

        method_choice = random.choices(
            [pm[0] for pm in payment_methods],
            weights=[pm[1] for pm in payment_methods]
        )[0]

        tong_tien = random.choice([150000, 250000, 320000, 450000, 580000, 750000, 920000, 1200000])
        tien_bhyt = round(tong_tien * 0.8) if method_choice == 'BHYT chi trả' else 0
        giam_gia = 0
        thanh_tien = tong_tien - tien_bhyt - giam_gia

        ma_hd = f"HD{exam_time.strftime('%y%m%d')}{i+100:03d}"
        cursor.execute("""
            INSERT INTO hoa_don (
                ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt,
                giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai,
                thoi_gian_thanh_toan, nhan_vien_thu, trang_thai_nhan_thuoc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ma_hd, p['id'], phieu_id, tong_tien, tien_bhyt,
            giam_gia, thanh_tien, method_choice, 'Đã thanh toán',
            exam_time + timedelta(minutes=15), 'Thu ngân H2T Care', 'Đã nhận'
        ))

        created_count += 1

    conn.commit()
    conn.close()
    print(f"Đã tạo thành công {created_count} đơn khám và hóa đơn hoàn thành.")

if __name__ == '__main__':
    seed_reports_data()
