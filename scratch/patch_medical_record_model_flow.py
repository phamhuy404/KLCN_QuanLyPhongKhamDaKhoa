with open('models/medical_record_model.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Cập nhật approve_lab_result notification text
old_approve_notif = """                        bn_row['tai_khoan_id'],
                        f"Đã có kết quả xét nghiệm: {item['ten_dich_vu']}",
                        f"Bác sĩ {doc_str} đã duyệt kết quả xét nghiệm {item['ten_dich_vu']} của bạn. Bạn có thể xem kết quả chi tiết trong hồ sơ cá nhân.",
                        now_str"""

new_approve_notif = """                        bn_row['tai_khoan_id'],
                        f"Đã có kết quả Cận lâm sàng: {item['ten_dich_vu']}",
                        f"Bác sĩ {doc_str} đã phê duyệt kết quả {item['ten_dich_vu']}. Vui lòng quay trở lại Phòng khám ban đầu để Bác sĩ đọc kết quả, kết luận chẩn đoán và tư vấn phác đồ điều trị.",
                        now_str"""

code = code.replace(old_approve_notif, new_approve_notif).replace(old_approve_notif.replace('\n', '\r\n'), new_approve_notif.replace('\n', '\r\n'))

# 2. Cập nhật save_examination:
# Thay đổi khối tạo đơn thuốc và hóa đơn
old_save_exam_section = """            # 3. Tạo đơn thuốc nếu có (Trạng thái: 'Chưa cấp phát' để Dược sĩ duyệt và cấp phát)
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
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien, 'Chưa thanh toán'))"""

new_save_exam_section = """            # 3. Tạo đơn thuốc nếu có: Trạng thái ban đầu 'Chờ bệnh nhân xác nhận mua'
            # (Bệnh nhân có quyền chọn Mua tại bệnh viện hoặc Tự mua ngoài)
            if validated_medicines:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM don_thuoc')
                dt_next = cursor.fetchone()['next_id']
                ma_dt = f"DT2609{str(dt_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO don_thuoc (ma_don_thuoc, phieu_kham_id, bac_si_id, loi_dan, trang_thai, hinh_thuc_mua)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ma_dt, phieu_kham_id, valid_doctor_id, advice, 'Chờ bệnh nhân xác nhận mua', 'Chưa chọn'))
                don_thuoc_id = cursor.lastrowid

                for vm in validated_medicines:
                    cursor.execute('''
                        INSERT INTO chi_tiet_don_thuoc (don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (don_thuoc_id, vm['thuoc_id'], vm['so_luong'], vm['lieu_dung'], vm['cach_dung']))

            # 4. Tự động sinh hóa đơn viện phí ban đầu (Tiền khám + Tiền Cận lâm sàng nếu có)
            # Tiền thuốc sẽ sinh hóa đơn riêng khi bệnh nhân chọn 'Mua tại bệnh viện'
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM hoa_don')
            hd_next = cursor.fetchone()['next_id']
            ma_hd = f"HD2609{str(hd_next).zfill(3)}"
            thanh_tien = max(0.0, tong_tien_kham - tien_bhyt)

            cursor.execute('''
                INSERT INTO hoa_don (ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, thanh_tien, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ma_hd, patient_id, phieu_kham_id, tong_tien_kham, tien_bhyt, thanh_tien, 'Chưa thanh toán'))"""

if old_save_exam_section in code:
    code = code.replace(old_save_exam_section, new_save_exam_section)
    print("Replaced exam section LF")
elif old_save_exam_section.replace('\n', '\r\n') in code:
    code = code.replace(old_save_exam_section.replace('\n', '\r\n'), new_save_exam_section.replace('\n', '\r\n'))
    print("Replaced exam section CRLF")
else:
    print("old_save_exam_section not found")

# 3. Thêm thông báo hướng dẫn khi có chỉ định Cận lâm sàng
old_cls_block = """            # 2. Tạo chỉ định cận lâm sàng nếu có (Trạng thái: 'Chờ thực hiện' để KTV thực hiện)
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
                    ''', (chi_dinh_id, s_id, 'Chờ thực hiện'))"""

new_cls_block = """            # 2. Tạo chỉ định cận lâm sàng nếu có (Trạng thái: 'Chờ thực hiện' để KTV thực hiện)
            if lab_service_ids and len(lab_service_ids) > 0:
                cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM phieu_chi_dinh')
                cd_next = cursor.fetchone()['next_id']
                ma_cd = f"CD2609{str(cd_next).zfill(3)}"

                cursor.execute('''
                    INSERT INTO phieu_chi_dinh (ma_chi_dinh, phieu_kham_id, bac_si_id, trang_thai)
                    VALUES (?, ?, ?, ?)
                ''', (ma_cd, phieu_kham_id, valid_doctor_id, 'Chờ thực hiện'))
                chi_dinh_id = cursor.lastrowid

                assigned_lab_names = []
                for s_id in lab_service_ids:
                    cursor.execute('SELECT ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt FROM dich_vu WHERE id = ?', (s_id,))
                    dv_row = cursor.fetchone()
                    if dv_row:
                        assigned_lab_names.append(dv_row['ten_dich_vu'])
                        dg = float(dv_row['don_gia'])
                        bh_pt = float(dv_row['bhyt_chi_tra_pt']) / 100.0
                        tong_tien_kham += dg
                        tien_bhyt += dg * bh_pt
                        invoice_items.append((dv_row['loai_dich_vu'] or 'Cận lâm sàng', dv_row['ten_dich_vu'], s_id, 1, dg, dg))

                    cursor.execute('''
                        INSERT INTO chi_tiet_chi_dinh (phieu_chi_dinh_id, dich_vu_id, ket_qua, trang_thai)
                        VALUES (?, ?, NULL, ?)
                    ''', (chi_dinh_id, s_id, 'Chờ thực hiện'))

                # Gửi thông báo hướng dẫn các bước tiếp theo cho bệnh nhân
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (patient_id,))
                bn_cls_row = cursor.fetchone()
                if bn_cls_row and bn_cls_row.get('tai_khoan_id'):
                    now_cls_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Chỉ định Cận lâm sàng', '/patient/lab-results', 0, ?)
                    ''', (
                        bn_cls_row['tai_khoan_id'],
                        f"Chỉ định Cận lâm sàng: {ma_cd}",
                        f"Bác sĩ đã ra chỉ định Cận lâm sàng cho bạn (Mã: {ma_cd}) gồm: {', '.join(assigned_lab_names)}. Vui lòng di chuyển đến Khu Cận lâm sàng để Kỹ thuật viên tiến hành chụp X-Quang, siêu âm hoặc lấy mẫu xét nghiệm.",
                        now_cls_str
                    ))"""

if old_cls_block in code:
    code = code.replace(old_cls_block, new_cls_block)
    print("Replaced cls block LF")
elif old_cls_block.replace('\n', '\r\n') in code:
    code = code.replace(old_cls_block.replace('\n', '\r\n'), new_cls_block.replace('\n', '\r\n'))
    print("Replaced cls block CRLF")
else:
    print("old_cls_block not found")

with open('models/medical_record_model.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated models/medical_record_model.py successfully!")
