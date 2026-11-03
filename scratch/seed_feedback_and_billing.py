import sys, io, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import random
from datetime import datetime, timedelta
from core.database import get_db

conn = get_db()
cur = conn.cursor()

print("--- 1. CLEANING & SEEDING PHAN_HOI ---")
# Xóa các phản hồi rác, trùng lặp hoặc lỗi font charset
cur.execute("DELETE FROM phan_hoi WHERE trang_thai LIKE '%?%' OR noi_dung LIKE '%Trải nghiệm khám chữa bệnh rất chuyên nghiệp%'")
conn.commit()

# Lấy danh sách bệnh nhân
cur.execute("SELECT id, ho_ten, ma_benh_nhan, tai_khoan_id FROM benh_nhan")
patients = cur.fetchall()
patient_ids = [p['id'] for p in patients]

# Lấy danh sách phiếu khám
cur.execute("SELECT id, benh_nhan_id, bac_si_id, thoi_gian_kham FROM phieu_kham")
encounters = cur.fetchall()
enc_by_patient = {}
for e in encounters:
    enc_by_patient.setdefault(e['benh_nhan_id'], []).append(e['id'])

feedback_templates = [
    {
        "chu_de": "Dịch vụ khám Tim Mạch",
        "diem": 5,
        "noi_dung": "Bác sĩ giải thích rất kỹ về kết quả điện tim và siêu âm tim. Dặn dò chế độ ăn giảm muối rất chu đáo.",
        "tra_loi": "Phòng khám H2T Care+ chân thành cảm ơn đánh giá của quý bệnh nhân. Chúc quý khách luôn dồi dào sức khỏe!",
        "nguoi": "Bộ phận CSKH - H2T Care+"
    },
    {
        "chu_de": "Khám Nhi và tư vấn dinh dưỡng",
        "diem": 5,
        "noi_dung": "Bác sĩ khám cho bé rất nhẹ nhàng, dỗ dành bé không khóc. Kê đơn thuốc vị ngọt dễ uống, bé đỡ sốt ngay hôm sau.",
        "tra_loi": "Cảm ơn phụ huynh đã tin tưởng đưa bé đến khám tại khoa Nhi H2T Care+. Chúc bé mau khỏe và ăn ngoan!",
        "nguoi": "Khoa Nhi - H2T Care+"
    },
    {
        "chu_de": "Chất lượng dịch vụ Nội tiêu hóa",
        "diem": 5,
        "noi_dung": "Bác sĩ Quân tư vấn tận tình, điều trị viêm loét dạ dày rất hiệu quả. Sau 2 tuần uống thuốc các triệu chứng trào ngược đã giảm hẳn.",
        "tra_loi": "H2T Care+ rất vui khi nhận được phản hồi hồi phục tích cực từ quý khách. Quý khách nhớ uống thuốc đúng giờ và tái khám theo hẹn ạ.",
        "nguoi": "Bộ phận CSKH - H2T Care+"
    },
    {
        "chu_de": "Quy trình thanh toán viện phí & BHYT",
        "diem": 4,
        "noi_dung": "Thủ tục duyệt thẻ BHYT nhanh chóng, thu ngân hướng dẫn quét mã QR thanh toán rất tiện. Phòng chờ hơi đông vào đầu giờ sáng.",
        "tra_loi": "Cảm ơn quý khách đã góp ý. Phòng khám đã mở thêm quầy tiếp nhận số 4 để giảm tải giờ cao điểm sáng.",
        "nguoi": "Phòng Kế toán - Thu ngân"
    },
    {
        "chu_de": "Khám Mắt và đo khúc xạ",
        "diem": 5,
        "noi_dung": "Máy móc đo mắt hiện đại, kỹ thuật viên đo mắt chính xác, bác sĩ cắt kính đeo vào nhìn rất êm và rõ nét.",
        "tra_loi": "Cảm ơn quý khách đã đánh giá cao trang thiết bị và dịch vụ chuyên khoa Mắt của H2T Care+!",
        "nguoi": "Bộ phận CSKH - H2T Care+"
    },
    {
        "chu_de": "Dịch vụ Da liễu",
        "diem": 5,
        "noi_dung": "Khám viêm da cơ địa rất đúng bệnh, dùng thuốc bôi 3 ngày là hết ngứa. Bác sĩ dặn dò cách dưỡng ẩm chi tiết.",
        "tra_loi": "H2T Care+ chúc quý khách mau lành thương tổn da và luôn duy trì làn da khỏe mạnh!",
        "nguoi": "Khoa Da Liễu"
    },
    {
        "chu_de": "Thái độ Dược sĩ quầy thuốc",
        "diem": 5,
        "noi_dung": "Dược sĩ đóng gói thuốc cẩn thận, ghi rõ liều uống sáng chiều trên từng vỉ thuốc. Rất chu đáo và tận tâm.",
        "tra_loi": "Cảm ơn quý khách đã khen ngợi đội ngũ Dược sĩ quầy thuốc. H2T Care+ sẽ luôn duy trì tinh thần phục vụ này.",
        "nguoi": "Kho Dược - Nhà Thuốc"
    },
    {
        "chu_de": "Khám Tai Mũi Họng",
        "diem": 4,
        "noi_dung": "Nội soi tai mũi họng không đau, hình ảnh nội soi hiển thị rõ trên màn hình lớn. Bác sĩ hút dịch xoang êm.",
        "tra_loi": "Cảm ơn quý khách. Quý khách giữ ấm cổ họng và tái khám nếu có bất kỳ khó chịu nào nhé.",
        "nguoi": "Khoa Tai Mũi Họng"
    },
    {
        "chu_de": "Khám Cơ Xương Khớp",
        "diem": 5,
        "noi_dung": "Bác sĩ nắn chỉnh khớp và tư vấn bài tập vật lý trị liệu thoái hóa cột sống lưng rất hữu ích. Đỡ đau lưng nhiều.",
        "tra_loi": "H2T Care+ rất mừng vì bài tập phát huy hiệu quả. Chúc quý khách duy trì vận động nhẹ nhàng mỗi ngày.",
        "nguoi": "Bộ phận CSKH - H2T Care+"
    },
    {
        "chu_de": "Chăm sóc khách hàng và đặt hẹn online",
        "diem": 5,
        "noi_dung": "Đặt lịch hẹn qua website rất tiện, đến phòng khám đọc mã là được tiếp nhận ngay không phải chờ lấy số.",
        "tra_loi": "Cảm ơn quý khách đã trải nghiệm tính năng đặt lịch khám thông minh của phòng khám!",
        "nguoi": "Ban Quản Trị Hệ Thống"
    },
    {
        "chu_de": "Khám sức khỏe tổng quát",
        "diem": 5,
        "noi_dung": "Gói khám tổng quát đầy đủ các hạng mục từ máu, nước tiểu, x-quang đến siêu âm. Bác sĩ tổng kết hồ sơ rất rõ ràng.",
        "tra_loi": "H2T Care+ kính chúc quý khách dồi dào sức khỏe và luôn an tâm trong công việc!",
        "nguoi": "Bộ phận CSKH - H2T Care+"
    },
    {
        "chu_de": "Thái độ nhân viên Lễ tân",
        "diem": 5,
        "noi_dung": "Các bạn tiếp tân đồng phục lịch sự, cúi chào niềm nở và dẫn tôi đến tận cửa phòng khám chuyên khoa.",
        "tra_loi": "Toàn thể nhân viên Lễ tân cảm ơn lời động viên ấm áp của quý khách!",
        "nguoi": "Tổ Lễ Tân - H2T Care+"
    }
]

base_date = datetime(2026, 9, 15)
for i in range(25):
    p_id = random.choice(patient_ids)
    pk_ids = enc_by_patient.get(p_id, [])
    pk_id = random.choice(pk_ids) if pk_ids else None
    tpl = random.choice(feedback_templates)
    
    delta_days = random.randint(0, 48)
    fb_time = (base_date + timedelta(days=delta_days, hours=random.randint(8, 17), minutes=random.randint(0, 59))).strftime('%Y-%m-%d %H:%M:%S')
    rep_time = (datetime.strptime(fb_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=random.randint(2, 24))).strftime('%Y-%m-%d %H:%M:%S')
    
    cur.execute('''
        INSERT INTO phan_hoi (benh_nhan_id, phieu_kham_id, chu_de, diem_danh_gia, noi_dung, trang_thai, tra_loi, ngay_tra_loi, nguoi_tra_loi, thoi_gian)
        VALUES (?, ?, ?, ?, ?, N'Đã giải quyết', ?, ?, ?, ?)
    ''', (
        p_id, pk_id, tpl['chu_de'], tpl['diem'], tpl['noi_dung'],
        tpl['tra_loi'], rep_time, tpl['nguoi'], fb_time
    ))

conn.commit()
print("-> Seeded 25 authentic phan_hoi records!")

print("--- 2. SEEDING HOM_THU_GOP_Y ---")
cur.execute("DELETE FROM hom_thu_gop_y")
conn.commit()

suggestions_data = [
    ("Trần Văn An", "0912345601", "tranvanan@gmail.com", "Đề xuất quầy lấy số thứ tự tự động", "Nên lắp thêm màn hình cảm ứng để người bệnh tự quét mã CCCD hoặc mã đặt hẹn để in phiếu số thứ tự, giảm tải cho tiếp tân vào giờ cao điểm sáng.", "2026-09-18 08:30:00"),
    ("Lê Thị Bích Hạnh", "0903124567", "bichhanh90@gmail.com", "Bãi giữ xe và lối đi người già", "Bãi giữ xe rất rộng và an ninh, các chú bảo vệ dắt xe hộ người lớn tuổi rất nhiệt tình. Tuy nhiên lối lên dốc nên thêm thanh vịn cho người đau khớp.", "2026-09-22 09:15:00"),
    ("Nguyễn Hoàng Nam", "0978112233", "namhoang.nguyen@yahoo.com", "Thêm cây nước uống nóng lạnh", "Đề nghị trang bị thêm cây nước nóng lạnh tại sảnh chờ tầng 2 khu khám Nhi để các mẹ tiện pha sữa cho các bé nhỏ.", "2026-09-27 10:20:00"),
    ("Phạm Minh Tuấn", "0934567890", "tuanminh.pham@outlook.com", "Khen ngợi bác sĩ Trần Minh Quân", "Bác sĩ Quân khám rất kỹ lưỡng và giải thích phác đồ điều trị tận tình. Tôi rất yên tâm khi đưa cả gia đình đến khám ở đây.", "2026-10-02 14:10:00"),
    ("Vũ Mai Phương", "0982345678", "phuongmai.vu@gmail.com", "Đa dạng hóa cổng thanh toán", "Nên bổ sung thêm thanh toán qua ví Apple Pay hoặc quẹt thẻ tín dụng không tiếp xúc (Contactless) tại quầy thanh toán viện phí.", "2026-10-06 11:45:00"),
    ("Đỗ Gia Bảo", "0918765432", "giabaodo@gmail.com", "Hệ thống gọi số qua loa", "Âm lượng loa gọi số tại khu vực cận lâm sàng hơi nhỏ khi phòng chờ đông người, đề xuất tăng nhẹ âm lượng hoặc hiển thị thêm bảng LED trước cửa phòng siêu âm.", "2026-10-12 15:30:00"),
    ("Hoàng Kim Oanh", "0909876543", "oanhkimhoang@gmail.com", "Khu vui chơi trẻ em", "Cảm ơn phòng khám đã bố trí góc chơi cho trẻ nhỏ với sách tranh và đồ chơi sạch sẽ. Bé nhà tôi đi khám mà không hề sợ sệt gì cả.", "2026-10-17 09:00:00"),
    ("Bùi Quốc Huy", "0945678912", "huyquoc.bui@gmail.com", "Thời gian phát thuốc quầy dược", "Dược sĩ đóng gói thuốc rất nhanh và dán nhãn hướng dẫn rất rõ ràng, tôi chỉ mất 3 phút sau khi thanh toán là đã nhận đủ thuốc.", "2026-10-21 16:20:00"),
    ("Ngô Thùy Dung", "0967891234", "thuydung.ngo@gmail.com", "Vệ sinh phòng khám", "Nhà vệ sinh sạch sẽ, thơm tho, có nước rửa tay và giấy lau đầy đủ. Rất ấn tượng với quy chuẩn vệ sinh của phòng khám.", "2026-10-25 10:05:00"),
    ("Đinh Trọng Khang", "0913456789", "khangtrong@gmail.com", "Đặt lịch tái khám online", "Rất mong phòng khám gửi tin nhắn Zalo ZNS hoặc SMS nhắc lịch tái khám trước 1 ngày để bệnh nhân không bị quên lịch.", "2026-10-29 13:40:00"),
    ("Võ Hoài Thương", "0938123456", "hoaithuong.vo@gmail.com", "Khen ngợi điều dưỡng lấy máu", "Kỹ thuật viên lấy máu xét nghiệm rất êm tay, một phát ăn ngay không đau và không bị bầm tím tay.", "2026-11-01 08:45:00"),
    ("Lý Hải Triều", "0977654321", "trieulyhai@gmail.com", "Khám sức khỏe ngoài giờ", "Phòng khám có lịch khám sáng thứ Bảy và Chủ Nhật rất tiện cho người đi làm văn phòng như tôi. Dịch vụ tuyệt vời!", "2026-11-02 11:15:00")
]

for item in suggestions_data:
    cur.execute('''
        INSERT INTO hom_thu_gop_y (ho_ten, sdt, email, chu_de, noi_dung, ngay_gui, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, N'Đã tiếp nhận')
    ''', item)

conn.commit()
print("-> Seeded 12 hom_thu_gop_y records!")

print("--- 3. BACKFILLING CHI_TIET_HOA_DON FOR MISSING INVOICES ---")
cur.execute('''
    SELECT hd.id, hd.ma_hoa_don, hd.tong_tien, hd.thanh_tien, hd.phieu_kham_id, COUNT(ct.id) as ct_count
    FROM hoa_don hd
    LEFT JOIN chi_tiet_hoa_don ct ON ct.hoa_don_id = hd.id
    GROUP BY hd.id, hd.ma_hoa_don, hd.tong_tien, hd.thanh_tien, hd.phieu_kham_id
    HAVING COUNT(ct.id) = 0
''')
missing_invoices = cur.fetchall()
print(f"Found {len(missing_invoices)} invoices missing chi_tiet_hoa_don.")

for inv in missing_invoices:
    inv_id = inv['id']
    tot = float(inv['tong_tien'] or 150000)
    
    # Tạo khoản khám bệnh cơ bản
    kham_price = min(tot, 150000.0)
    cur.execute('''
        INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
        VALUES (?, N'Khám bệnh', N'Công khám chuyên khoa theo yêu cầu', 1, 1, ?, ?)
    ''', (inv_id, kham_price, kham_price))
    
    rem = tot - kham_price
    if rem > 0:
        if rem >= 100000:
            cls_price = min(rem, 150000.0)
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Cận lâm sàng', N'Tổng phân tích tế bào máu ngoại vi (CBC)', 8, 1, ?, ?)
            ''', (inv_id, cls_price, cls_price))
            rem -= cls_price
            
        if rem > 0:
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Thuốc', N'Thuốc và vật tư y tế theo đơn ngoại trú', 1, 1, ?, ?)
            ''', (inv_id, rem, rem))

conn.commit()
print("-> Backfilled chi_tiet_hoa_don for all missing invoices!")

print("--- 4. SEEDING ADDITIONAL INVOICES (PAID & UNPAID) SPANNING MID-SEPT TO NOV ---")
payment_methods = ['Tiền mặt', 'Chuyển khoản QR Code', 'VNPAY', 'Thẻ POS']
cashiers = ['Lê Phương Thảo', 'Nguyễn Thị Minh Châu', 'Trần Bảo Ngọc', 'Hoàng Thu Trang']

# Tạo thêm 15 hóa đơn đa dạng ngày tháng để biểu đồ doanh thu đầy đủ
start_date = datetime(2026, 9, 16)
cur.execute("SELECT MAX(id) as max_id FROM hoa_don")
curr_max = cur.fetchone()['max_id'] or 200

for i in range(16):
    curr_max += 1
    p_id = random.choice(patient_ids)
    days_offset = random.randint(0, 48)
    inv_date = (start_date + timedelta(days=days_offset, hours=random.randint(8, 16), minutes=random.randint(0, 59))).strftime('%Y-%m-%d %H:%M:%S')
    
    # 75% Đã thanh toán, 25% Chưa thanh toán
    is_paid = (random.random() < 0.75)
    trang_thai = 'Đã thanh toán' if is_paid else 'Chưa thanh toán'
    pay_method = random.choice(payment_methods) if is_paid else 'Tiền mặt'
    cashier = random.choice(cashiers) if is_paid else None
    
    kham_val = random.choice([150000, 200000, 250000, 300000])
    cls_val = random.choice([0, 120000, 180000, 250000, 400000])
    med_val = random.choice([0, 85000, 145000, 220000, 360000])
    
    tong_tien = kham_val + cls_val + med_val
    bhyt_coverage = random.choice([0.0, 0.2, 0.5, 0.8]) if random.random() < 0.6 else 0.0
    tien_bhyt = round(tong_tien * bhyt_coverage)
    thanh_tien = tong_tien - tien_bhyt
    ma_hd = f"HD26{days_offset+10:02d}{curr_max:03d}"
    
    cur.execute('''
        INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu, trang_thai_nhan_thuoc)
        VALUES (?, ?, NULL, ?, ?, 0.0, ?, ?, ?, ?, ?, ?)
    ''', (
        ma_hd, p_id, tong_tien, tien_bhyt, thanh_tien, pay_method, trang_thai,
        inv_date, cashier, 'Đã nhận' if is_paid and med_val > 0 else 'Chưa nhận'
    ))
    
    cur.execute("SELECT @@IDENTITY as new_id")
    new_hd_id = int(cur.fetchone()['new_id'])
    
    # Chi tiết
    cur.execute('''
        INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
        VALUES (?, N'Khám bệnh', N'Khám Chuyên Khoa Theo Yêu Cầu', 1, 1, ?, ?)
    ''', (new_hd_id, kham_val, kham_val))
    
    if cls_val > 0:
        cur.execute('''
            INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
            VALUES (?, N'Cận lâm sàng', N'Siêu âm hoặc Xét nghiệm sinh hóa', 8, 1, ?, ?)
        ''', (new_hd_id, cls_val, cls_val))
        
    if med_val > 0:
        cur.execute('''
            INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
            VALUES (?, N'Thuốc', N'Thuốc kê đơn ngoại trú theo phác đồ', 1, 1, ?, ?)
        ''', (new_hd_id, med_val, med_val))

conn.commit()
print("-> Seeded 16 additional diverse invoices with line items!")

print("--- 5. SEEDING STOCK MOVEMENTS IN AUDIT_LOG ---")
cur.execute("SELECT id, ten_thuoc, so_luong_ton FROM thuoc")
meds = cur.fetchall()

for i in range(20):
    m = random.choice(meds)
    m_id = m['id']
    m_name = m['ten_thuoc']
    
    days_offset = random.randint(2, 45)
    mov_date = (start_date + timedelta(days=days_offset, hours=random.randint(8, 16), minutes=random.randint(0, 59))).strftime('%Y-%m-%d %H:%M:%S')
    
    # 50% nhập CSV, 50% xuất phát thuốc
    is_in = (random.random() < 0.5)
    action = 'STOCK_IN' if is_in else 'STOCK_OUT'
    delta = random.choice([50, 100, 150, 200]) if is_in else -random.choice([2, 5, 10, 14, 20])
    
    stock_before = random.randint(50, 300)
    stock_after = stock_before + delta
    
    reason = "Nhập kho định kỳ từ file CSV" if is_in else "Cấp phát thuốc theo đơn khám EMR"
    receipt = f"CSV_NHAP_{mov_date[:10].replace('-', '')}" if is_in else f"DT26{random.randint(100, 999)}"
    
    cur.execute('''
        INSERT INTO audit_log (table_name, row_id, action, performed_by, performed_by_name, performed_at, reason, before_json, after_json)
        VALUES ('thuoc', ?, ?, 4, N'Phạm Thị Dung (Dược sĩ)', ?, ?, ?, ?)
    ''', (
        m_id, action, mov_date, reason,
        f'{{"stock": {stock_before}}}',
        f'{{"stock": {stock_after}, "delta": {delta}, "receipt": "{receipt}"}}'
    ))

conn.commit()
print("-> Seeded 20 realistic stock movement audit logs!")

conn.close()
print("=== ALL SEEDING TASKS COMPLETED SUCCESSFULLY! ===")
