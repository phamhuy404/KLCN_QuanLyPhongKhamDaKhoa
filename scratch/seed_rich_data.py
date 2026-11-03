import sys, os, random
from datetime import datetime, date, timedelta
sys.path.insert(0, os.path.abspath('.'))
from core.database import get_db

def seed_rich_data():
    conn = get_db()
    c = conn.cursor()

    # 1. Thu thap thong tin he thong
    c.execute('SELECT id, ma_benh_nhan, ho_ten, sdt, bhyt FROM benh_nhan')
    patients = [dict(r) for r in c.fetchall()]

    c.execute('''
        SELECT bs.id, bs.nhan_vien_id, nv.ho_ten, bs.chuyen_khoa_id, ck.ten_khoa, nv.tai_khoan_id
        FROM bac_si bs
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        ORDER BY bs.id
    ''')
    doctors = [dict(r) for r in c.fetchall()]

    c.execute('''
        SELECT nv.id, nv.ho_ten, v.ma_vai_tro, nv.tai_khoan_id
        FROM nhan_vien nv
        JOIN tai_khoan t ON nv.tai_khoan_id = t.id
        JOIN vai_tro v ON t.vai_tro_id = v.id
        WHERE v.ma_vai_tro IN ('LETAN', 'DUOCSI', 'KTV')
    ''')
    staff_rows = [dict(r) for r in c.fetchall()]
    letans = [s for s in staff_rows if s['ma_vai_tro'] == 'LETAN']
    duocsis = [s for s in staff_rows if s['ma_vai_tro'] == 'DUOCSI']
    ktvs = [s for s in staff_rows if s['ma_vai_tro'] == 'KTV']

    c.execute('SELECT id, ma_phong, ten_phong, chuyen_khoa_id FROM phong_kham WHERE trang_thai = 1')
    rooms = [dict(r) for r in c.fetchall()]
    rooms_by_dept = {}
    for r in rooms:
        rooms_by_dept.setdefault(r['chuyen_khoa_id'], []).append(r)

    c.execute('SELECT id, ten_thuoc, don_gia, so_luong_ton FROM thuoc WHERE trang_thai = 1')
    medicines = [dict(r) for r in c.fetchall()]

    c.execute('SELECT id, ten_dich_vu, loai_dich_vu, don_gia, chuyen_khoa_id FROM dich_vu WHERE trang_thai = 1')
    services = [dict(r) for r in c.fetchall()]

    print(f'Patients: {len(patients)}, Doctors: {len(doctors)}, Letan: {len(letans)}, Duocsi: {len(duocsis)}, KTV: {len(ktvs)}')

    # 2. Dieu chinh trang thai ca truc (lich_lam_viec) da dang tu giua thang 9 den thang 11
    c.execute('''
        SELECT id, ngay_lam, nhan_vien_id, bac_si_id 
        FROM lich_lam_viec 
        WHERE ngay_lam >= '2026-09-15' AND ngay_lam <= '2026-11-03' AND trang_thai_duyet = 'DA_DUYET'
    ''')
    past_shifts = [dict(r) for r in c.fetchall()]
    random.shuffle(past_shifts)

    cancel_reasons = [
        'Bận tham dự Hội nghị Khoa học Y tế Toàn quốc',
        'Có việc gia đình đột xuất cần giải quyết',
        'Con nhỏ bị ốm sốt cần người chăm sóc',
        'Bận tham gia khóa đào tạo chuyên khoa nâng cao',
        'Sức khỏe không đảm bảo (cảm cúm, khản tiếng)',
        'Đã thỏa thuận đổi ca trực với đồng nghiệp cùng khoa',
        'Công tác chỉ đạo tuyến theo yêu cầu của Sở Y tế'
    ]

    for s in past_shifts[:15]:
        reason = random.choice(cancel_reasons)
        c.execute('UPDATE lich_lam_viec SET trang_thai_duyet = ?, ly_do_huy = ? WHERE id = ?',
                  ('CHO_HUY', reason, s['id']))

    approver = letans[0]['tai_khoan_id'] if letans else 1
    for s in past_shifts[15:40]:
        reason = random.choice(cancel_reasons)
        app_date = str(s['ngay_lam'])[:10] + ' 10:00:00'
        c.execute('''
            UPDATE lich_lam_viec 
            SET trang_thai_duyet = 'DA_HUY', trang_thai = 0, ly_do_huy = ?, nguoi_duyet_id = ?, ngay_duyet = ?
            WHERE id = ?
        ''', (reason, approver, app_date, s['id']))

    c.execute('''
        SELECT id FROM lich_lam_viec 
        WHERE ngay_lam >= '2026-11-09' AND trang_thai_duyet = 'DA_DUYET'
    ''')
    future_shifts = [dict(r) for r in c.fetchall()]
    random.shuffle(future_shifts)
    for s in future_shifts[:30]:
        c.execute('UPDATE lich_lam_viec SET trang_thai_duyet = \'CHO_DUYET\' WHERE id = ?', (s['id'],))

    print('Updated lich_lam_viec statuses successfully.')

    # 3. Kiem tra va tao lien ket lich_hen cho cac phieu_kham da co
    c.execute('SELECT id, ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, thoi_gian_kham, ly_do_kham, lich_hen_id, trang_thai FROM phieu_kham WHERE lich_hen_id IS NULL')
    unlinked_pks = [dict(r) for r in c.fetchall()]
    print(f'Unlinked phieu_kham to link with lich_hen: {len(unlinked_pks)}')

    for pk in unlinked_pks:
        doc = next((d for d in doctors if d['id'] == pk['bac_si_id']), doctors[0])
        pk_time_str = str(pk.get('thoi_gian_kham') or '2026-10-15 08:30:00')[:19]
        ngay_hen = pk_time_str[:10]
        gio_hen = pk_time_str[11:19] if len(pk_time_str) >= 19 else '08:30:00'
        ly_do = pk.get('ly_do_kham') or 'Khám chuyên khoa định kỳ'
        stt = 'Đã khám' if pk.get('trang_thai') in ('Hoàn thành', 'Đã khám') else 'Đang khám'
        pk_room_id = int(pk['phong_kham_id']) if pk.get('phong_kham_id') else 1

        c.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
            VALUES ('TMP', ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (pk['benh_nhan_id'], pk['bac_si_id'], doc['chuyen_khoa_id'], pk_room_id, ngay_hen, gio_hen, ly_do, stt, pk_time_str))

        new_lh_id = c.lastrowid
        ma_lh = f"LH2609{str(new_lh_id).zfill(4)}"
        c.execute('UPDATE lich_hen SET ma_lich_hen = ? WHERE id = ?', (ma_lh, new_lh_id))
        c.execute('UPDATE phieu_kham SET lich_hen_id = ? WHERE id = ?', (new_lh_id, pk['id']))

    # 4. Kiem tra cac bac si chua co phieu_kham, tao ca kham cho ho
    c.execute('SELECT bs.id FROM bac_si bs WHERE bs.id NOT IN (SELECT distinct bac_si_id FROM phieu_kham)')
    zero_docs_ids = [r['id'] for r in c.fetchall()]
    print(f'Doctors with 0 phieu_kham: {zero_docs_ids}')

    clinical_scenarios = [
        {
            'ly_do': 'Tái khám tăng huyết áp, kiểm tra huyết áp định kỳ',
            'trieu_chung': 'Hơi chóng mặt nhẹ khi thay đổi tư thế buổi sáng, không đau ngực',
            'chan_doan_so_bo': 'Tăng huyết áp vô căn (nguyên phát)',
            'icd': 'I10 - Bệnh tăng huyết áp vô căn (nguyên phát)',
            'huong_dieu_tri': 'Duy trì thuốc hạ áp hàng ngày, ăn nhạt, hạn chế mỡ động vật',
            'loi_dan': 'Uống thuốc đúng giờ mỗi sáng, tái khám sau 2 tuần hoặc khi có dấu hiệu bất thường',
            'thuoc_ids': [1, 6],
            'cls_ids': [8, 9]
        },
        {
            'ly_do': 'Khám họng đau rát, sốt nhẹ 2 ngày nay',
            'trieu_chung': 'Cổ họng đỏ, đau khi nuốt, có ít đờm trắng, sốt 38 độ C',
            'chan_doan_so_bo': 'Viêm họng cấp tính do vi khuẩn',
            'icd': 'J02.9 - Viêm họng cấp tính, không xác định',
            'huong_dieu_tri': 'Kháng sinh, hạ sốt giảm đau, súc họng nước muối sinh lý',
            'loi_dan': 'Uống nhiều nước ấm, nghỉ ngơi, giữ ấm cổ họng',
            'thuoc_ids': [7, 6],
            'cls_ids': [8]
        },
        {
            'ly_do': 'Đau thượng vị âm ỉ, ợ chua nhiều sau ăn',
            'trieu_chung': 'Đau tức vùng thượng vị, ợ hơi, cồn cào lúc đói, buồn nôn nhẹ',
            'chan_doan_so_bo': 'Viêm dạ dày - tá tràng cấp',
            'icd': 'K29.7 - Viêm dạ dày không xác định',
            'huong_dieu_tri': 'Ức chế tiết acid dạ dày, bảo vệ niêm mạc, ăn đúng bữa',
            'loi_dan': 'Kiêng thức ăn cay nóng, chua, cà phê, rượu bia; ăn đúng bữa',
            'thuoc_ids': [4, 6],
            'cls_ids': [8, 9, 10]
        },
        {
            'ly_do': 'Đau nhức khớp gối hai bên khi đi lại nhiều',
            'trieu_chung': 'Khớp gối lục cục khi co duỗi, hơi sưng nhẹ, cứng khớp buổi sáng 10 phút',
            'chan_doan_so_bo': 'Thoái hóa khớp gối nguyên phát hai bên',
            'icd': 'M17.0 - Thoái hóa khớp gối nguyên phát, hai bên',
            'huong_dieu_tri': 'Giảm đau chống viêm không steroid, bổ sung dưỡng chất sụn khớp, tập vật lý trị liệu',
            'loi_dan': 'Tránh ngồi xổm, leo cầu thang nhiều, kiểm soát cân nặng',
            'thuoc_ids': [9, 6],
            'cls_ids': [8]
        },
        {
            'ly_do': 'Mắt cộm rát, đỏ và chảy nước mắt',
            'trieu_chung': 'Kết mạc mắt cương tụ đỏ, có ít tiết tố dính mi buổi sáng, thị lực bình thường',
            'chan_doan_so_bo': 'Viêm kết mạc cấp tính',
            'icd': 'H10.9 - Viêm kết mạc, không xác định',
            'huong_dieu_tri': 'Nhỏ mắt kháng khuẩn, rửa mắt bằng nước muối sinh lý 0.9%',
            'loi_dan': 'Tránh dụi mắt, đeo kính bảo hộ khi ra đường, không dùng chung khăn mặt',
            'thuoc_ids': [10, 6],
            'cls_ids': []
        },
        {
            'ly_do': 'Đau răng hàm dưới bên phải, ê buốt khi ăn đồ lạnh',
            'trieu_chung': 'Răng số 46 có lỗ sâu mặt nhai, kích thích đau nhẹ với nước đá',
            'chan_doan_so_bo': 'Sâu ngà sâu răng 46',
            'icd': 'K02.1 - Sâu ngà răng',
            'huong_dieu_tri': 'Làm sạch xoang trám và hàn phục hồi răng sâu bằng Composite',
            'loi_dan': 'Chải răng đúng cách ngày 2 lần, dùng chỉ nha khoa, súc miệng nước muối',
            'thuoc_ids': [6],
            'cls_ids': []
        }
    ]

    for doc_id in zero_docs_ids:
        doc = next(d for d in doctors if d['id'] == doc_id)
        dept_rooms = rooms_by_dept.get(doc['chuyen_khoa_id'], rooms[:1])
        room = random.choice(dept_rooms)

        for enc_i in range(2):
            pat = random.choice(patients)
            days_ago = random.randint(10, 45)
            exam_dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(1, 4))
            exam_dt_str = exam_dt.strftime('%Y-%m-%d %H:%M:%S')
            exam_date = exam_dt.strftime('%Y-%m-%d')
            exam_time = exam_dt.strftime('%H:%M:%S')

            scen = random.choice(clinical_scenarios)

            # 1. lich_hen
            c.execute('''
                INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
                VALUES ('TMP', ?, ?, ?, ?, ?, ?, ?, 1, 'Đã khám', ?)
            ''', (pat['id'], doc['id'], doc['chuyen_khoa_id'], room['id'], exam_date, exam_time, scen['ly_do'], exam_dt_str))

            new_lh_id = c.lastrowid
            ma_lh = f"LH2609{str(new_lh_id).zfill(4)}"
            c.execute('UPDATE lich_hen SET ma_lich_hen = ? WHERE id = ?', (ma_lh, new_lh_id))

            # 2. phieu_kham
            reexam_date = (exam_dt + timedelta(days=14)).strftime('%Y-%m-%d')
            c.execute('''
                INSERT INTO phieu_kham (ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
                VALUES ('TMP', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Hoàn thành')
            ''', (pat['id'], doc['id'], room['id'], new_lh_id, exam_dt_str, scen['ly_do'], scen['trieu_chung'], scen['chan_doan_so_bo'], scen['icd'], scen['huong_dieu_tri'], scen['loi_dan'], reexam_date))

            new_pk_id = c.lastrowid
            ma_pk = f"PK2609{str(new_pk_id).zfill(4)}"
            c.execute('UPDATE phieu_kham SET ma_phieu = ? WHERE id = ?', (ma_pk, new_pk_id))

            # 3. chi_so_sinh_ton
            mach = random.randint(72, 86)
            t = round(random.uniform(36.5, 37.2), 1)
            ha = f"{random.randint(110, 135)}/{random.randint(70, 85)}"
            spo2 = random.randint(97, 99)
            c.execute('''
                INSERT INTO chi_so_sinh_ton (benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi, thoi_gian_do, ghi_chu)
                VALUES (?, ?, ?, ?, ?, 18, 165, 62, 22.8, ?, N'Chỉ số ổn định')
            ''', (pat['id'], mach, t, ha, spo2, exam_dt_str))

            # 4. don_thuoc
            hinh_thuc = 'BENH_VIEN' if (enc_i % 2 == 0) else 'NGOAI'
            stt_don = 'Đã nhận thuốc' if hinh_thuc == 'BENH_VIEN' else 'Mua ngoài'
            approver_ds = random.choice(duocsis)['tai_khoan_id'] if duocsis else 7
            c.execute('''
                INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, thoi_gian_ke, loi_dan, trang_thai, hinh_thuc_mua, nguoi_duyet, ngay_duyet)
                VALUES ('TMP', ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (new_pk_id, doc['id'], exam_dt_str, scen['loi_dan'], stt_don, hinh_thuc, approver_ds, exam_dt_str))

            new_dt_id = c.lastrowid
            ma_dt = f"DT2609{str(new_dt_id).zfill(4)}"
            c.execute('UPDATE don_thuoc SET ma_don_thuoc = ? WHERE id = ?', (ma_dt, new_dt_id))

            tong_tien_thuoc = 0
            for t_id in scen['thuoc_ids']:
                med = next((m for m in medicines if m['id'] == t_id), medicines[0])
                qty = 10
                c.execute('''
                    INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                    VALUES (?, ?, ?, N'Uống 1 viên x 2 lần/ngày sau bữa ăn', N'Uống với nước sôi để nguội')
                ''', (new_dt_id, med['id'], qty))
                tong_tien_thuoc += float(med.get('don_gia', 2000)) * qty

            # 5. phieu_chi_dinh
            tong_tien_cls = 0
            if scen['cls_ids']:
                c.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, thoi_gian_chi_dinh, ghi_chu, trang_thai)
                    VALUES ('TMP', ?, ?, ?, N'Thực hiện theo chỉ định lâm sàng', 'Đã thực hiện')
                ''', (new_pk_id, doc['id'], exam_dt_str))

                new_cd_id = c.lastrowid
                ma_cd = f"CD2609{str(new_cd_id).zfill(4)}"
                c.execute('UPDATE phieu_chi_dinh SET ma_chi_dinh = ? WHERE id = ?', (ma_cd, new_cd_id))

                for s_id in scen['cls_ids']:
                    srv = next((s for s in services if s['id'] == s_id), None)
                    if not srv: continue
                    ktv = random.choice(ktvs)['ho_ten'] if ktvs else 'KTV. Võ Anh Đức'
                    ket_qua_str = 'Kết quả trong giới hạn sinh lý bình thường' if 'Máu' in srv['ten_dich_vu'] else 'Không phát hiện bất thường'
                    c.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai, bac_si_duyet, thoi_gian_duyet)
                        VALUES (?, ?, ?, ?, ?, 'DA_DUYET', ?, ?)
                    ''', (new_cd_id, srv['id'], ket_qua_str, ktv, exam_dt_str, doc['ho_ten'], exam_dt_str))
                    tong_tien_cls += float(srv.get('don_gia', 100000))

            # 6. hoa_don HDK
            tien_kham = 150000.0
            tong_hd = tien_kham + tong_tien_cls
            tien_bhyt = tong_hd * 0.8 if pat.get('bhyt') else 0.0
            thanh_tien = tong_hd - tien_bhyt
            thu_ngan = random.choice(letans)['ho_ten'] if letans else 'Nguyễn Thị Lan'

            c.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu, trang_thai_nhan_thuoc)
                VALUES ('TMP', ?, ?, ?, ?, 0, ?, N'Tiền mặt', N'Đã thanh toán', ?, ?, 'Không có thuốc')
            ''', (pat['id'], new_pk_id, tong_hd, tien_bhyt, thanh_tien, exam_dt_str, thu_ngan))

            new_hd_id = c.lastrowid
            ma_hd = f"HD2609{str(new_hd_id).zfill(4)}"
            c.execute('UPDATE hoa_don SET ma_hoa_don = ? WHERE id = ?', (ma_hd, new_hd_id))

            c.execute('''
                INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                VALUES (?, N'KhamBenh', N'Khám chuyên khoa', ?, 1, ?, ?)
            ''', (new_hd_id, doc['chuyen_khoa_id'], tien_kham, tien_kham))

            # 7. Neu mua tai vien: Tao them hoa_don HDT
            if hinh_thuc == 'BENH_VIEN' and tong_tien_thuoc > 0:
                c.execute('''
                    INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu, trang_thai_nhan_thuoc)
                    VALUES ('TMP', ?, ?, ?, 0, 0, ?, N'Chuyển khoản', N'Đã thanh toán', ?, ?, N'Đã nhận')
                ''', (pat['id'], new_pk_id, tong_tien_thuoc, tong_tien_thuoc, exam_dt_str, thu_ngan))

                new_hdt_id = c.lastrowid
                ma_hdt = f"HDT2609{str(new_hdt_id).zfill(4)}"
                c.execute('UPDATE hoa_don SET ma_hoa_don = ? WHERE id = ?', (ma_hdt, new_hdt_id))

                c.execute('''
                    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                    VALUES (?, N'Thuoc', N'Đơn thuốc điều trị ngoại trú', ?, 1, ?, ?)
                ''', (new_hdt_id, new_dt_id, tong_tien_thuoc, tong_tien_thuoc))

    print('Added rich clinical encounters for remaining doctors successfully.')

    # 5. Bo sung cac lich hen hien tai (Hom nay 03/11/2026 va Tuong lai)
    today_str = date.today().isoformat()
    today_dt_str = today_str + ' 07:45:00'
    today_appts = [
        {'bn': patients[0], 'bs': doctors[0], 'time': '08:30:00', 'stt': 'Đang khám', 'ly_do': 'Khám định kỳ huyết áp tháng 11'},
        {'bn': patients[1], 'bs': doctors[5], 'time': '09:00:00', 'stt': 'Đang khám', 'ly_do': 'Kiểm tra vết sưng cổ tay sau chấn thương'},
        {'bn': patients[2], 'bs': doctors[10], 'time': '10:00:00', 'stt': 'Đã tiếp nhận', 'ly_do': 'Tái khám viêm phế quản cho bé'},
        {'bn': patients[3], 'bs': doctors[15], 'time': '14:00:00', 'stt': 'Đã tiếp nhận', 'ly_do': 'Lấy cao răng và kiểm tra răng sâu'},
        {'bn': patients[4], 'bs': doctors[25], 'time': '15:30:00', 'stt': 'Chờ tiếp nhận', 'ly_do': 'Ù tai và đau nhức vùng xoang mũi'},
    ]

    for item in today_appts:
        c.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
            VALUES ('TMP', ?, ?, ?, 1, ?, ?, ?, 1, ?, ?)
        ''', (item['bn']['id'], item['bs']['id'], item['bs']['chuyen_khoa_id'], today_str, item['time'], item['ly_do'], item['stt'], today_dt_str))

        new_lh_id = c.lastrowid
        ma_lh = f"LH2609{str(new_lh_id).zfill(4)}"
        c.execute('UPDATE lich_hen SET ma_lich_hen = ? WHERE id = ?', (ma_lh, new_lh_id))

    future_appts = [
        {'bn': patients[5], 'bs': doctors[1], 'day_offset': 2, 'time': '08:30:00', 'stt': 'Đã duyệt', 'ly_do': 'Tái khám đái tháo đường'},
        {'bn': patients[6], 'bs': doctors[6], 'day_offset': 3, 'time': '09:30:00', 'stt': 'Đã duyệt', 'ly_do': 'Kiểm tra thoái hóa khớp gối'},
        {'bn': patients[7], 'bs': doctors[11], 'day_offset': 4, 'time': '10:00:00', 'stt': 'Đã duyệt', 'ly_do': 'Khám sức khỏe tổng quát trẻ em'},
        {'bn': patients[8], 'bs': doctors[16], 'day_offset': 5, 'time': '14:30:00', 'stt': 'Đã duyệt', 'ly_do': 'Hàn răng thẩm mỹ răng cửa'},
        {'bn': patients[9], 'bs': doctors[21], 'day_offset': 6, 'time': '09:00:00', 'stt': 'Đã duyệt', 'ly_do': 'Khám phụ khoa định kỳ'},
        {'bn': patients[10], 'bs': doctors[26], 'day_offset': 7, 'time': '15:00:00', 'stt': 'Đã duyệt', 'ly_do': 'Nội soi thanh quản kiểm tra khản tiếng'},
        {'bn': patients[11], 'bs': doctors[31], 'day_offset': 3, 'time': '08:45:00', 'stt': 'Chờ xét duyệt', 'ly_do': 'Đo khúc xạ kiểm tra độ cận thị'},
        {'bn': patients[12], 'bs': doctors[2], 'day_offset': 5, 'time': '09:15:00', 'stt': 'Chờ xét duyệt', 'ly_do': 'Tư vấn dinh dưỡng và xét nghiệm máu'},
        {'bn': patients[13], 'bs': doctors[7], 'day_offset': 6, 'time': '10:30:00', 'stt': 'Chờ xét duyệt', 'ly_do': 'Khám đau lưng và thoát vị đĩa đệm'},
        {'bn': patients[14], 'bs': doctors[12], 'day_offset': 8, 'time': '14:00:00', 'stt': 'Chờ xét duyệt', 'ly_do': 'Khám ho kéo dài ở trẻ nhỏ'},
        {'bn': patients[15], 'bs': doctors[3], 'day_offset': 4, 'time': '09:00:00', 'stt': 'Đã hủy', 'ly_do': 'Bệnh nhân bận công tác đột xuất'},
        {'bn': patients[16], 'bs': doctors[8], 'day_offset': 7, 'time': '10:00:00', 'stt': 'Đã hủy', 'ly_do': 'Bệnh nhân xin dời lịch do có việc riêng'}
    ]

    for item in future_appts:
        f_date = (date.today() + timedelta(days=item['day_offset'])).isoformat()
        c.execute('''
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
            VALUES ('TMP', ?, ?, ?, 1, ?, ?, ?, 1, ?, ?)
        ''', (item['bn']['id'], item['bs']['id'], item['bs']['chuyen_khoa_id'], f_date, item['time'], item['ly_do'], item['stt'], today_dt_str))

        new_lh_id = c.lastrowid
        ma_lh = f"LH2609{str(new_lh_id).zfill(4)}"
        c.execute('UPDATE lich_hen SET ma_lich_hen = ? WHERE id = ?', (ma_lh, new_lh_id))

    # 6. Cap nhat trang thai don thuoc hien co cho day du 2 luong (Mua tai vien va Mua ngoai)
    c.execute('SELECT id, hinh_thuc_mua, trang_thai FROM don_thuoc')
    all_dts = [dict(r) for r in c.fetchall()]
    for i, dt in enumerate(all_dts):
        if not dt.get('hinh_thuc_mua') or dt.get('hinh_thuc_mua') == 'None':
            h_thuc = 'BENH_VIEN' if (i % 2 == 0) else 'NGOAI'
            t_thai = 'Đã nhận thuốc' if h_thuc == 'BENH_VIEN' else 'Mua ngoài'
            c.execute('UPDATE don_thuoc SET hinh_thuc_mua = ?, trang_thai = ? WHERE id = ?', (h_thuc, t_thai, dt['id']))

    conn.commit()
    print('All rich clinical data seeded successfully with realistic distribution!')
    conn.close()

if __name__ == '__main__':
    seed_rich_data()
