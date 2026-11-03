import io
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db

conn = get_db()
cur = conn.cursor()

# 1. Danh sách phản hồi mẫu chất lượng y tế
FEEDBACK_TEMPLATES = [
    {
        'chu_de': 'Dịch vụ khám bệnh',
        'diem': 5,
        'noi_dung': 'Bác sĩ thăm khám rất kỹ càng, lắng nghe người bệnh và giải thích phác đồ điều trị tận tình. Rất an tâm khi khám tại đây.',
        'tra_loi': 'Cảm ơn Quý khách đã tin tưởng dịch vụ khám chữa bệnh của H2T Care+. Kính chúc Quý khách nhiều sức khỏe!',
        'nguoi_tra_loi': 'Bộ phận CSKH H2T Care+'
    },
    {
        'chu_de': 'Thái độ phục vụ',
        'diem': 5,
        'noi_dung': 'Đội ngũ điều dưỡng và nhân viên tiếp tân hướng dẫn rất nhiệt tình, nhẹ nhàng từ khâu làm thủ tục đến lấy mẫu xét nghiệm.',
        'tra_loi': 'H2T Care+ rất vui khi nhận được phản hồi tích cực từ Quý khách. Đội ngũ y bác sĩ sẽ không ngừng nỗ lực nâng cao trải nghiệm người bệnh.',
        'nguoi_tra_loi': 'Ban Giám Đốc Phòng Khám'
    },
    {
        'chu_de': 'Cơ sở vật chất',
        'diem': 5,
        'noi_dung': 'Phòng khám sạch sẽ, tiện nghi, máy móc xét nghiệm và siêu âm hiện đại. Kết quả trả nhanh qua cổng bệnh nhân rất tiện lợi.',
        'tra_loi': 'Cảm ơn Quý khách đã đánh giá cao cơ sở vật chất của phòng khám!',
        'nguoi_tra_loi': 'Phòng Quản Trị Cơ Sở Vật Chất'
    },
    {
        'chu_de': 'Quy trình tiếp đón',
        'diem': 4,
        'noi_dung': 'Quy trình đặt lịch hẹn trực tuyến nhanh chóng, đến đúng giờ là được vào khám ngay mà không phải bốc số chờ đợi lâu.',
        'tra_loi': 'Dạ cảm ơn Quý khách đã sử dụng hệ thống đặt khám trực tuyến. Phòng khám sẽ tiếp tục tối ưu quy trình để phục vụ nhanh hơn nữa.',
        'nguoi_tra_loi': 'Bộ phận CSKH H2T Care+'
    },
    {
        'chu_de': 'Hiệu quả điều trị',
        'diem': 5,
        'noi_dung': 'Sau 1 tuần dùng thuốc theo đơn của bác sĩ, các triệu chứng đau rát và ho đã giảm hẳn. Bác sĩ dặn dò ăn uống kiêng cữ rất chu đáo.',
        'tra_loi': 'Phòng khám rất vui mừng khi sức khỏe của Quý khách đã hồi phục tốt. Chúc Quý khách luôn khỏe mạnh!',
        'nguoi_tra_loi': 'BS. Trưởng Khoa Khám Bệnh'
    },
    {
        'chu_de': 'Thời gian chờ khám',
        'diem': 4,
        'noi_dung': 'Vào giờ cao điểm buổi sáng quầy phát thuốc hơi đông người một chút, nhưng các dược sĩ phát thuốc đối chiếu tên tuổi rất cẩn thận.',
        'tra_loi': 'Cảm ơn ý kiến đóng góp quý báu của Quý khách. Phòng khám đang bố trí thêm nhân sự quầy phát thuốc vào các khung giờ cao điểm.',
        'nguoi_tra_loi': 'Kho Dược & CSKH'
    }
]

# Lấy toàn bộ 20 bệnh nhân
cur.execute('SELECT id, ma_benh_nhan, ho_ten FROM benh_nhan ORDER BY id ASC')
patients = [dict(r) for r in cur.fetchall()]

added_feedback_count = 0
added_unpaid_inv_count = 0

for p in patients:
    pid = p['id']
    
    # Lấy các phiếu khám của bệnh nhân
    cur.execute('SELECT id, ma_phieu, thoi_gian_kham FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY id ASC', (pid,))
    pks = [dict(r) for r in cur.fetchall()]
    
    # Kiểm tra số phản hồi hiện có
    cur.execute('SELECT COUNT(*) as cnt FROM phan_hoi WHERE benh_nhan_id = ?', (pid,))
    fb_cnt = cur.fetchone()['cnt']
    
    target_fb = 3
    if fb_cnt < target_fb:
        needed = target_fb - fb_cnt
        templates_sample = random.sample(FEEDBACK_TEMPLATES, min(needed, len(FEEDBACK_TEMPLATES)))
        for idx, tpl in enumerate(templates_sample):
            pk_id = pks[idx % len(pks)]['id'] if pks else None
            days_ago = random.randint(1, 45)
            fb_date = (datetime.now() - timedelta(days=days_ago, hours=random.randint(1, 10))).strftime('%Y-%m-%d %H:%M:%S')
            reply_date = (datetime.strptime(fb_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=random.randint(2, 24))).strftime('%Y-%m-%d %H:%M:%S')
            
            is_pending = (days_ago <= 3 and idx == 0 and pid in [2, 3, 24, 25])
            status = 'Chờ giải quyết' if is_pending else 'Đã giải quyết'
            reply_text = None if is_pending else tpl['tra_loi']
            replier = None if is_pending else tpl['nguoi_tra_loi']
            reply_dt = None if is_pending else reply_date
            
            cur.execute('''
                INSERT INTO phan_hoi (benh_nhan_id, phieu_kham_id, chu_de, diem_danh_gia, noi_dung, trang_thai, tra_loi, ngay_tra_loi, nguoi_tra_loi, thoi_gian)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pid, pk_id, tpl['chu_de'], tpl['diem'], tpl['noi_dung'], status, reply_text, reply_dt, replier, fb_date))
            added_feedback_count += 1

    # Kiểm tra số hóa đơn chưa thanh toán
    cur.execute("SELECT COUNT(*) as unpaid FROM hoa_don WHERE benh_nhan_id = ? AND trang_thai = N'Chưa thanh toán'", (pid,))
    unpaid = cur.fetchone()['unpaid']
    
    if unpaid == 0 and pks:
        recent_pk = pks[-1]
        inv_code = f"HD{datetime.now().strftime('%y%m')}{random.randint(2000, 9999)}"
        amount = random.choice([150000.0, 250000.0, 350000.0, 480000.0, 650000.0])
        inv_date = (datetime.now() - timedelta(hours=random.randint(1, 12))).strftime('%Y-%m-%d %H:%M:%S')
        
        cur.execute('''
            INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu, trang_thai_nhan_thuoc)
            VALUES (?, ?, ?, ?, 0, 0, ?, N'Chưa thanh toán', N'Chưa thanh toán', ?, N'Thu ngân phòng khám', N'Chờ phát')
        ''', (inv_code, pid, recent_pk['id'], amount, amount, inv_date))
        
        cur.execute('SELECT @@IDENTITY as new_id')
        new_hd_id = int(cur.fetchone()['new_id'])
        
        # Thêm chi tiết hóa đơn: loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien
        if amount == 150000.0:
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Khám bệnh', N'Khám Chuyên Khoa Theo Yêu Cầu', 1, 1, 150000, 150000)
            ''', (new_hd_id,))
        elif amount <= 350000.0:
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Khám bệnh', N'Khám Chuyên Khoa Theo Yêu Cầu', 1, 1, 150000, 150000)
            ''', (new_hd_id,))
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Cận lâm sàng', N'Xét Nghiệm Tổng Phân Tích Tế Bào Máu (24 thông số)', 1, 1, ?, ?)
            ''', (new_hd_id, amount - 150000, amount - 150000))
        else:
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Khám bệnh', N'Khám Chuyên Khoa Theo Yêu Cầu', 1, 1, 150000, 150000)
            ''', (new_hd_id,))
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Cận lâm sàng', N'Siêu Âm Màu Doppler Tổng Quát', 1, 1, 250000, 250000)
            ''', (new_hd_id,))
            if amount > 400000.0:
                cur.execute('''
                    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                    VALUES (?, N'Thuốc', N'Đơn thuốc điều trị ngoại trú', 1, 1, ?, ?)
                ''', (new_hd_id, amount - 400000, amount - 400000))
                
        added_unpaid_inv_count += 1

conn.commit()
conn.close()

print(f"Đã bổ sung thành công {added_feedback_count} phản hồi đánh giá và {added_unpaid_inv_count} hóa đơn chờ thanh toán!")
