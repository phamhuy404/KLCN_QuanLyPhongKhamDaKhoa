import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'medical_record_model.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block tu doan # 1. Tao phieu kham benh den het save_examination
old_block = """            # 1. Tạo phiếu khám bệnh
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_kham')
            pk_id = cursor.fetchone()['next_id']
            ma_phieu = f"PK2609{str(pk_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO phieu_kham (ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Hoàn thành')
            ''', (ma_phieu, patient_id, valid_doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date))
            phieu_kham_id = cursor.lastrowid

            tong_tien_kham = 150000.0
            tien_bhyt = 120000.0

            # 2. Tạo chỉ định cận lâm sàng nếu có (Trạng thái khởi tạo: 'Chờ thực hiện')
            if lab_service_ids and len(lab_service_ids) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, ?)
                ''', (ma_cd, phieu_kham_id, valid_doctor_id, 'Chờ thực hiện'))
                chi_dinh_id = cursor.lastrowid

                for s_id in lab_service_ids:
                    cursor.execute('SELECT don_gia, bhyt_chi_tra_pt FROM dich_vu WHERE id = ?', (s_id,))
                    dv_row = cursor.fetchone()
                    if dv_row:
                        tong_tien_kham += float(dv_row['don_gia'])
                        tien_bhyt += float(dv_row['don_gia']) * (float(dv_row['bhyt_chi_tra_pt']) / 100.0)

                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, NULL, ?)
                    ''', (chi_dinh_id, s_id, 'Chờ thực hiện'))

            # 3. Tạo đơn thuốc nếu có (Trạng thái khởi tạo: 'Chưa cấp phát')
            if medicines and len(medicines) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ma_dt, phieu_kham_id, valid_doctor_id, advice, 'Chưa cấp phát'))
                don_thuoc_id = cursor.lastrowid


                for m in medicines:
                    thuoc_id = m.get('thuoc_id')
                    so_luong = int(m.get('so_luong', 1))
                    lieu_dung = m.get('lieu_dung', 'Ngày 2 lần, lần 1 viên')
                    cach_dung = m.get('cach_dung', 'Uống sau ăn')

                    cursor.execute('SELECT don_gia FROM thuoc WHERE id = ?', (thuoc_id,))
                    th_row = cursor.fetchone()
                    if th_row:
                        tong_tien_kham += float(th_row['don_gia']) * so_luong

                    cursor.execute('''
                        INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung))

            # 4. Tự động sinh hóa đơn viện phí
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
            hd_next = cursor.fetchone()['next_id']
            ma_hd = f"HD2609{str(hd_next).zfill(3)}"
            thanh_tien = max(0.0, tong_tien_kham - tien_bhyt)

            cursor.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, 'Chưa thanh toán')
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien))

            conn.commit()
            conn.close()"""

new_block = """            # 0. Kiểm tra tồn kho trước khi kê đơn thuốc
            validated_medicines = []
            if medicines and len(medicines) > 0:
                for m in medicines:
                    thuoc_id = m.get('thuoc_id')
                    so_luong = int(m.get('so_luong', 1))
                    cursor.execute('SELECT id, ten_thuoc, so_luong_ton, don_vi_tinh, don_gia, ton_kho_toi_thieu FROM thuoc WHERE id = ?', (thuoc_id,))
                    th_row = cursor.fetchone()
                    if not th_row:
                        conn.close()
                        return False, f"Thuốc ID {thuoc_id} không tồn tại trong kho dược!"
                    if so_luong > th_row['so_luong_ton']:
                        conn.close()
                        return False, f"Thuốc '{th_row['ten_thuoc']}' chỉ còn tồn {th_row['so_luong_ton']} {th_row['don_vi_tinh']}, không đủ số lượng kê ({so_luong})!"
                    validated_medicines.append({
                        'thuoc_id': thuoc_id,
                        'ten_thuoc': th_row['ten_thuoc'],
                        'so_luong': so_luong,
                        'don_gia': float(th_row['don_gia']),
                        'don_vi_tinh': th_row['don_vi_tinh'],
                        'lieu_dung': m.get('lieu_dung', 'Uống 1 viên/lần, ngày 2 lần'),
                        'cach_dung': m.get('cach_dung', 'Uống sau bữa ăn no 30 phút')
                    })

            # 1. Tạo phiếu khám bệnh
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_kham')
            pk_id = cursor.fetchone()['next_id']
            ma_phieu = f"PK2609{str(pk_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO phieu_kham (ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Hoàn thành')
            ''', (ma_phieu, patient_id, valid_doctor_id, room_id, reason, symptoms, diagnosis, icd, treatment, advice, reexam_date))
            phieu_kham_id = cursor.lastrowid

            # Khoản thu ban đầu: Tiền khám bệnh chuyên khoa
            tong_tien_kham = 150000.0
            tien_bhyt = 120000.0
            invoice_items = [
                ('Khám bệnh', 'Khám Chuyên Khoa Ngoại Trú', phieu_kham_id, 1, 150000.0, 150000.0)
            ]

            # 2. Tạo chỉ định cận lâm sàng nếu có (Trạng thái: 'Chờ thực hiện' để KTV thực hiện)
            if lab_service_ids and len(lab_service_ids) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, ?)
                ''', (ma_cd, phieu_kham_id, valid_doctor_id, 'Chờ thực hiện'))
                chi_dinh_id = cursor.lastrowid

                for s_id in lab_service_ids:
                    cursor.execute('SELECT ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt FROM dich_vu WHERE id = ?', (s_id,))
                    dv_row = cursor.fetchone()
                    if dv_row:
                        dg = float(dv_row['don_gia'])
                        bh_pt = float(dv_row['bhyt_chi_tra_pt']) / 100.0
                        tong_tien_kham += dg
                        tien_bhyt += dg * bh_pt
                        invoice_items.append((dv_row['loai_dich_vu'] or 'Cận lâm sàng', dv_row['ten_dich_vu'], s_id, 1, dg, dg))

                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, NULL, ?)
                    ''', (chi_dinh_id, s_id, 'Chờ thực hiện'))

            # 3. Tạo đơn thuốc nếu có (Trạng thái: 'Chưa cấp phát' để Dược sĩ duyệt và cấp phát)
            if validated_medicines:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ma_dt, phieu_kham_id, valid_doctor_id, advice, 'Chưa cấp phát'))
                don_thuoc_id = cursor.lastrowid

                for vm in validated_medicines:
                    cursor.execute('''
                        INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (don_thuoc_id, vm['thuoc_id'], vm['so_luong'], vm['lieu_dung'], vm['cach_dung']))

                    thanh_tien_thuoc = vm['don_gia'] * vm['so_luong']
                    tong_tien_kham += thanh_tien_thuoc
                    invoice_items.append(('Thuốc', vm['ten_thuoc'], vm['thuoc_id'], vm['so_luong'], vm['don_gia'], thanh_tien_thuoc))

            # 4. Tự động sinh hóa đơn viện phí tổng hợp
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
            hd_next = cursor.fetchone()['next_id']
            ma_hd = f"HD2609{str(hd_next).zfill(3)}"
            thanh_tien = max(0.0, tong_tien_kham - tien_bhyt)

            cursor.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, 'Chưa thanh toán')
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien))
            hoa_don_id = cursor.lastrowid

            # Lưu từng dòng chi tiết hóa đơn
            for l_khoan, ten_khoan, tham_chieu, sl, dg, tt in invoice_items:
                cursor.execute('''
                    INSERT INTO chi_tiet_hoa_don (hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (hoa_don_id, l_khoan, ten_khoan, tham_chieu, sl, dg, tt))

            # 5. Gửi thông báo in-app cho tài khoản bệnh nhân
            cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
            bn_row = cursor.fetchone()
            if bn_row and bn_row.get('tai_khoan_id'):
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, 'Khám bệnh', '/patient/records', 0, ?)
                ''', (
                    bn_row['tai_khoan_id'],
                    f"Hoàn thành khám bệnh: {ma_phieu}",
                    f"Bác sĩ đã hoàn tất phiên khám cho bạn (Chẩn đoán: {icd}). Toa thuốc và hóa đơn viện phí {ma_hd} đã được cập nhật.",
                    now_str
                ))

            conn.commit()
            conn.close()"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated save_examination in medical_record_model.py successfully!")
else:
    print("old_block not found in medical_record_model.py!")
