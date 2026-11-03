import sys, io, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import random
from datetime import datetime, timedelta
from core.database import get_db

conn = get_db()
cur = conn.cursor()

print("--- 1. CLEANING UP DUMMY / TEST DATA ---")
# 1. Xóa thông báo test
cur.execute("DELETE FROM thong_bao WHERE LOWER(tieu_de) LIKE '%test%' OR LOWER(tieu_de) LIKE '%demo%' OR LOWER(tieu_de) LIKE '%dt_rej%' OR LOWER(tieu_de) LIKE '%dt_test%' OR LOWER(noi_dung) LIKE '%test%'")
print("Deleted test notifications.")

# 2. Chuẩn hóa bác sĩ duyệt trong chi_tiet_chi_dinh
cur.execute("UPDATE chi_tiet_chi_dinh SET bac_si_duyet = N'BS. Trần Minh Quân' WHERE bac_si_duyet LIKE '%Test%' OR bac_si_duyet IS NULL")
print("Updated chi_tiet_chi_dinh reviewer.")

# 3. Chuẩn hóa mã đơn thuốc DT_REJ
cur.execute("UPDATE don_thuoc SET ma_don_thuoc = 'DT2610006' WHERE ma_don_thuoc = 'DT_REJ_6'")
cur.execute("UPDATE don_thuoc SET ma_don_thuoc = 'DT2610009' WHERE ma_don_thuoc = 'DT_REJ_9'")
cur.execute("UPDATE don_thuoc SET ma_don_thuoc = 'DT2610017' WHERE ma_don_thuoc = 'DT_REJ_17'")
cur.execute("UPDATE don_thuoc SET ma_don_thuoc = 'DT2611020' WHERE ma_don_thuoc = 'DT_REJ_20'")
conn.commit()
print("Normalized DT_REJ codes.")

print("--- 2. RETRIEVING ALL 20 PATIENT ACCOUNTS ---")
cur.execute('''
    SELECT bn.id, bn.ma_benh_nhan, bn.ho_ten, bn.gioi_tinh, bn.ngay_sinh, bn.sdt, bn.email, bn.cccd, bn.bhyt, bn.tai_khoan_id, tk.username
    FROM benh_nhan bn
    JOIN tai_khoan tk ON bn.tai_khoan_id = tk.id
    ORDER BY bn.id
''')
patients = cur.fetchall()
print(f"Found {len(patients)} valid registered patient accounts.")

# Lấy danh sách bác sĩ thực tế kèm chuyên khoa và phòng khám
cur.execute('''
    SELECT bs.id, nv.ho_ten, bs.chuyen_khoa_id, ck.ten_khoa, bs.phong_kham_chinh_id
    FROM bac_si bs
    JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
    JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
''')
doctors = cur.fetchall()

# Lấy danh sách thuốc thực tế trong kho
cur.execute('SELECT id, ma_thuoc, ten_thuoc, don_vi_tinh, don_gia, so_luong_ton FROM thuoc WHERE so_luong_ton > 0')
medicines = cur.fetchall()

# Lấy danh sách dịch vụ kỹ thuật CLS
cur.execute('SELECT id, ten_dich_vu, loai_dich_vu, don_gia FROM dich_vu WHERE trang_thai = 1')
services = cur.fetchall()

print(f"System catalog: {len(doctors)} doctors, {len(medicines)} medicines, {len(services)} services.")

clinical_cases = [
    {
        "dept": "Khoa Nội Tổng Quát",
        "symptoms": "Đau vùng thượng vị âm ỉ kèm ợ chua, buồn nôn nhẹ sau ăn, đầy hơi khó tiêu kéo dài 1 tuần",
        "icd": "K21 - Trào ngược dạ dày thực quản (GERD)",
        "treatment": "Điều trị ngoại trú kết hợp ức chế bơm proton PPI và kháng acid, điều chỉnh chế độ ăn kiêng đồ chua cay",
        "advice": "Uống thuốc trước bữa ăn 30 phút, kiêng bia rượu, cà phê, không nằm ngay sau khi ăn",
        "cls": ["Nội soi thực quản - dạ dày - tá tràng", "Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)"],
        "cls_results": [
            "Niêm mạc thực quản đoạn dưới sung huyết nhẹ (Grade A Los Angeles), niêm mạc hang vị dạ dày viêm trợt nông, test HP âm tính.",
            "Các dòng tế bào máu trong giới hạn bình thường: RBC: 4.85 T/L, HGB: 142 g/L, WBC: 6.8 G/L, PLT: 235 G/L."
        ]
    },
    {
        "dept": "Khoa Nội Tim Mạch",
        "symptoms": "Đau đầu vùng chẩm, chóng mặt thoáng qua khi đổi tư thế, hồi hộp nhẹ, đo huyết áp tại nhà dao động 145/95 mmHg",
        "icd": "I10 - Tăng huyết áp vô căn (nguyên phát)",
        "treatment": "Khởi trị thuốc hạ áp đơn trị liệu liều thấp, theo dõi huyết áp nhật ký hàng ngày, chế độ ăn giảm muối",
        "advice": "Uống thuốc đều đặn vào buổi sáng sau ăn, hạn chế ăn mặn, tập thể dục nhẹ nhàng 30 phút mỗi ngày",
        "cls": ["Điện tim đồ (ECG 12 chuyển đạo)", "Siêu âm tim Doppler màu"],
        "cls_results": [
            "Nhịp xoang đều tần số 76 chu kỳ/phút, trục trung gian, không thấy dấu hiệu dày thất trái hoặc thiếu máu cơ tim cấp.",
            "Kích thước các buồng tim trong giới hạn bình thường, chức năng tâm thu thất trái bảo tồn EF = 64%, không rối loạn vận động vùng."
        ]
    },
    {
        "dept": "Khoa Tai Mũi Họng",
        "symptoms": "Nghẹt mũi 2 bên luân phiên, chảy nước mũi trong, ngứa mũi hắt hơi nhiều về sáng sớm, đau rát họng nhẹ",
        "icd": "J00 - Viêm mũi họng cấp (Cảm thường)",
        "treatment": "Điều trị triệu chứng, kháng dị ứng thế hệ mới kết hợp xịt rửa mũi xoang bằng nước muối ưu trương",
        "advice": "Giữ ấm cổ ngực, súc họng bằng nước muối sinh lý ấm sau ăn và trước khi ngủ, đeo khẩu trang khi ra đường",
        "cls": ["Nội soi Tai Mũi Họng ống mềm"],
        "cls_results": [
            "Cuống mũi 2 bên phù nề nhạt màu, nhiều dịch nhầy trong, vòm họng sạch, dây thanh 2 bên di động tốt khép kín khi phát âm."
        ]
    },
    {
        "dept": "Khoa Da Liễu",
        "symptoms": "Ngứa rát nhiều ở mu hai bàn tay và nếp gấp khuỷu tay, da khô đỏ, bong vảy nhẹ, ngứa tăng về đêm",
        "icd": "L20 - Viêm da cơ địa (Chàm/Eczema)",
        "treatment": "Dưỡng ẩm phục hồi hàng rào bảo vệ da kết hợp bôi corticoid tại chỗ liều thấp ngắn ngày và kháng histamin uống",
        "advice": "Thoa kem dưỡng ẩm ngay sau khi tắm, tránh tắm nước quá nóng, hạn chế tiếp xúc trực tiếp xà phòng chất tẩy rửa",
        "cls": ["Soi tươi tìm nấm da"],
        "cls_results": [
            "Soi trực tiếp mẫu vảy da dưới kính hiển vi: Không phát hiện sợi nấm hoặc bào tử nấm gây bệnh."
        ]
    },
    {
        "dept": "Khoa Cơ Xương Khớp",
        "symptoms": "Đau mỏi vùng cột sống thắt lưng lan xuống mông sau khi mang vác vật nặng, cúi ngửa khó khăn, không tê bì chân",
        "icd": "M54.5 - Đau thắt lưng cơ năng",
        "treatment": "Thuốc giảm đau chống viêm không steroid (NSAIDs) ngắn ngày, giãn cơ, vật lý trị liệu chườm ấm",
        "advice": "Tránh cúi gập người mang vác nặng, nằm đệm cứng vừa phải, tập các bài tập kéo giãn cơ lưng nhẹ nhàng",
        "cls": ["Chụp X-quang Cột sống thắt lưng thẳng - nghiêng"],
        "cls_results": [
            "Hình ảnh thoái hóa nhẹ đốt sống L4-L5, gai xương nhỏ rìa thân đốt sống, chiều cao các khe đĩa đệm tương đối đồng đều."
        ]
    },
    {
        "dept": "Khoa Mắt",
        "symptoms": "Cộm mắt, ngứa mắt, chảy nước mắt sống, mắt đỏ nhẹ sau khi đi bụi, mỏi mắt nhiều khi nhìn màn hình",
        "icd": "H10 - Viêm kết mạc dị ứng",
        "treatment": "Nhỏ mắt nước mắt nhân tạo không chất bảo quản, nhỏ thuốc kháng dị ứng tại chỗ, hạn chế dụi mắt",
        "advice": "Không dụi tay lên mắt, rửa tay thường xuyên, đeo kính râm bảo vệ mắt khi đi ra ngoài trời nắng gió",
        "cls": ["Khám mắt sinh hiển vi"],
        "cls_results": [
            "Kết mạc mi phù nề nhẹ, cương tụ rìa, giác mạc trong suốt không bắt màu Fluorescein, tiền phòng sâu sạch."
        ]
    }
]

time_slots = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '14:00', '14:30', '15:00', '15:30', '16:00']
cashiers = ['Lê Phương Thảo', 'Nguyễn Thị Minh Châu', 'Trần Bảo Ngọc', 'Hoàng Thu Trang']
payment_methods = ['Chuyển khoản QR Code', 'Tiền mặt', 'VNPAY', 'Thẻ POS']

base_start = datetime(2026, 9, 16)

for p in patients:
    p_id = p['id']
    cur.execute('SELECT COUNT(*) as cnt FROM phieu_kham WHERE benh_nhan_id = ?', (p_id,))
    existing_pk = cur.fetchone()['cnt']
    
    needed_encounters = max(0, 4 - existing_pk)
    print(f"Patient {p['ma_benh_nhan']} ({p['ho_ten']}): current encounters = {existing_pk}, adding = {needed_encounters}")
    
    for k in range(needed_encounters):
        c_case = random.choice(clinical_cases)
        dept_docs = [d for d in doctors if d['ten_khoa'] == c_case['dept']]
        if not dept_docs:
            dept_docs = doctors
        doc = random.choice(dept_docs)
        
        days_offset = random.randint(1, 46)
        enc_dt = base_start + timedelta(days=days_offset, hours=random.randint(8, 16), minutes=random.choice([0, 15, 30, 45]))
        enc_str = enc_dt.strftime('%Y-%m-%d %H:%M:%S')
        date_str = enc_dt.strftime('%Y-%m-%d')
        time_str = random.choice(time_slots)
        
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM lich_hen")
        next_lh_num = cur.fetchone()['next_id']
        ma_lh = f"LH26{days_offset+10:02d}{next_lh_num:03d}"
        
        # 1. Tạo lịch hẹn hoàn tất
        cur.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai, ngay_dat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
        ''', (ma_lh, p_id, doc['id'], doc['chuyen_khoa_id'], doc['phong_kham_chinh_id'] or 1, date_str, time_str, c_case['symptoms'][:100], enc_str))
        cur.execute("SELECT @@IDENTITY as new_id")
        lh_id = int(cur.fetchone()['new_id'])
        
        # 2. Tạo phiếu khám hoàn tất
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM phieu_kham")
        next_pk_num = cur.fetchone()['next_id']
        ma_pk = f"PK26{days_offset+10:02d}{next_pk_num:03d}"
        
        reexam_dt = enc_dt + timedelta(days=14)
        reexam_date_str = reexam_dt.strftime('%Y-%m-%d')
        
        cur.execute('''
            INSERT INTO phieu_kham (ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, N'Hoàn tất')
        ''', (
            ma_pk, p_id, doc['id'], doc['phong_kham_chinh_id'] or 1, lh_id,
            enc_str, c_case['symptoms'][:100], c_case['symptoms'], c_case['icd'], c_case['icd'],
            c_case['treatment'], c_case['advice'], reexam_date_str
        ))
        cur.execute("SELECT @@IDENTITY as new_id")
        pk_id = int(cur.fetchone()['new_id'])
        
        # 3. Tạo phiếu chỉ định CLS và kết quả
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM phieu_chi_dinh")
        next_cd_num = cur.fetchone()['next_id']
        ma_cd = f"CD26{days_offset+10:02d}{next_cd_num:03d}"
        
        cur.execute('''
            INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, thoi_gian_chi_dinh, ghi_chu, trang_thai)
            VALUES (?, ?, ?, ?, ?, N'Đã hoàn thành')
        ''', (ma_cd, pk_id, doc['id'], enc_str, c_case['icd']))
        cur.execute("SELECT @@IDENTITY as new_id")
        cd_id = int(cur.fetchone()['new_id'])
        
        cls_total = 0
        for idx, cls_name in enumerate(c_case['cls']):
            match_srv = next((s for s in services if cls_name.lower() in s['ten_dich_vu'].lower()), None)
            srv_id = match_srv['id'] if match_srv else services[0]['id']
            srv_price = float(match_srv['don_gia'] if match_srv else 150000)
            cls_total += srv_price
            result_text = c_case['cls_results'][idx] if idx < len(c_case['cls_results']) else "Kết quả trong giới hạn bình thường."
            
            cur.execute('''
                INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai, bac_si_duyet, thoi_gian_duyet)
                VALUES (?, ?, ?, N'KTV. Nguyễn Văn Toàn', ?, N'Đã có kết quả', ?, ?)
            ''', (cd_id, srv_id, result_text, enc_str, doc['ho_ten'], enc_str))
            
        # 4. Tạo đơn thuốc hoàn tất
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM don_thuoc")
        next_dt_num = cur.fetchone()['next_id']
        ma_dt = f"DT26{days_offset+10:02d}{next_dt_num:03d}"
        
        cur.execute('''
            INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, thoi_gian_ke, loi_dan, trang_thai, hinh_thuc_mua)
            VALUES (?, ?, ?, ?, ?, N'Đã phát', N'Mua tại quầy')
        ''', (ma_dt, pk_id, doc['id'], enc_str, c_case['advice']))
        cur.execute("SELECT @@IDENTITY as new_id")
        dt_id = int(cur.fetchone()['new_id'])
        
        med_total = 0
        selected_meds = random.sample(medicines, min(2, len(medicines)))
        for med in selected_meds:
            qty = random.randint(10, 28)
            price = float(med['don_gia'] or 15000)
            m_sub = qty * price
            med_total += m_sub
            cur.execute('''
                INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, cach_dung)
                VALUES (?, ?, ?, N'Ngày uống 2 lần, mỗi lần 1 viên sau ăn sáng - chiều')
            ''', (dt_id, med['id'], qty))
            
        # 5. Tạo hóa đơn thanh toán
        kham_fee = 150000.0
        tot_invoice = kham_fee + cls_total + med_total
        has_bhyt = bool(p.get('bhyt') and str(p.get('bhyt')).strip())
        bhyt_ratio = 0.8 if has_bhyt else 0.0
        tien_bhyt = round(tot_invoice * bhyt_ratio)
        thanh_tien = tot_invoice - tien_bhyt
        
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM hoa_don")
        next_hd_num = cur.fetchone()['next_id']
        ma_hd = f"HD26{days_offset+10:02d}{next_hd_num:03d}"
        
        cur.execute('''
            INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu, trang_thai_nhan_thuoc)
            VALUES (?, ?, ?, ?, ?, 0.0, ?, ?, N'Đã thanh toán', ?, ?, N'Đã nhận')
        ''', (
            ma_hd, p_id, pk_id, tot_invoice, tien_bhyt, thanh_tien,
            random.choice(payment_methods), enc_str, random.choice(cashiers)
        ))
        cur.execute("SELECT @@IDENTITY as new_id")
        hd_id = int(cur.fetchone()['new_id'])
        
        # Chi tiết hóa đơn
        cur.execute('''
            INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
            VALUES (?, N'Khám bệnh', N'Khám chuyên khoa ' + ?, 1, 1, ?, ?)
        ''', (hd_id, doc['ten_khoa'], kham_fee, kham_fee))
        
        if cls_total > 0:
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Cận lâm sàng', N'Xét nghiệm và Chẩn đoán hình ảnh', 8, 1, ?, ?)
            ''', (hd_id, cls_total, cls_total))
            
        if med_total > 0:
            cur.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'Thuốc', N'Thuốc kê đơn ngoại trú điều trị', 1, 1, ?, ?)
            ''', (hd_id, med_total, med_total))

    conn.commit()

print("-> Successfully populated realistic medical records for all 20 patients!")

print("--- 3. POPULATING CLEAN IN-APP NOTIFICATIONS FOR ALL 20 PATIENTS ---")
for p in patients:
    tk_id = p['tai_khoan_id']
    if not tk_id:
        continue
    
    cur.execute('SELECT COUNT(*) as cnt FROM thong_bao WHERE tai_khoan_id = ?', (tk_id,))
    cnt_tb = cur.fetchone()['cnt']
    if cnt_tb < 4:
        user_notifications = [
            ("Lịch hẹn khám đã được tiếp nhận", f"Lịch khám của bạn tại khoa Nội Tổng Quát đã được tiếp nhận thành công. Vui lòng đến trước 15 phút.", "/patient/appointments", "2026-10-15 08:30:00"),
            ("Kết quả Cận lâm sàng mới", "Bác sĩ đã hoàn tất duyệt kết quả xét nghiệm và chụp X-quang của bạn. Bấm để xem chi tiết.", "/patient/records", "2026-10-15 10:15:00"),
            ("Đơn thuốc điện tử sẵn sàng", "Đơn thuốc điều trị ngoại trú của bạn đã được xuất và sẵn sàng nhận tại Nhà thuốc H2T Care+.", "/patient/records", "2026-10-15 10:45:00"),
            ("Hóa đơn viện phí điện tử", "Hóa đơn viện phí khám chữa bệnh đã được thanh toán thành công qua chuyển khoản QR Code.", "/patient/billing", "2026-10-15 11:00:00"),
            ("Nhắc nhở tái khám định kỳ", f"Bác sĩ hẹn bạn tái khám định kỳ sau 14 ngày. Hãy chú ý giữ gìn sức khỏe và uống thuốc đúng liều.", "/patient/appointments", "2026-10-22 09:00:00")
        ]
        for t_de, n_dung, l_ket, t_gian in user_notifications:
            cur.execute('''
                INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                VALUES (?, ?, ?, N'Hệ thống', ?, 1, ?)
            ''', (tk_id, t_de, n_dung, l_ket, t_gian))

conn.commit()
print("-> Cleaned and seeded authentic in-app notifications for all patient accounts!")

conn.close()
print("=== ALL STANDARDIZATION & ENRICHMENT TASKS COMPLETED SUCCESSFULLY! ===")
