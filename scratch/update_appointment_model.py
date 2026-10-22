import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'appointment_model.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """        try:
            cursor.execute('UPDATE lich_hen SET trang_thai = ? WHERE id = ?', (new_status, appointment_id))
            conn.commit()
            conn.close()"""

new_block = """        try:
            cursor.execute('UPDATE lich_hen SET trang_thai = ? WHERE id = ?', (new_status, appointment_id))

            # Nếu tiếp nhận hoặc xác nhận lịch hẹn, tự động gửi thông báo in-app cho bệnh nhân
            if new_status in ['Đã tiếp nhận', 'Đã xác nhận']:
                cursor.execute('SELECT tai_khoan_id, ho_ten FROM benh_nhan WHERE id = ?', (appt['benh_nhan_id'],))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    khoa_name = appt.get('ten_khoa') or 'Chuyên khoa'
                    bs_name = appt.get('ten_bac_si') or 'Bác sĩ phụ trách'
                    tieu_de = f"Tiếp nhận thành công lịch khám: {appt['ma_lich_hen']}"
                    noi_dung = (
                        f"Kính gửi {bn_row['ho_ten']}, lịch hẹn khám bệnh mã {appt['ma_lich_hen']} của bạn "
                        f"vào ngày {appt['ngay_hen']} lúc {str(appt['gio_hen'])[:5]} tại {khoa_name} ({bs_name}) "
                        f"đã được nhân viên Lễ tân tiếp nhận thành công. Xin vui lòng có mặt trước giờ khám 15 phút tại Quầy tiếp đón."
                    )
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Lịch hẹn', '/patient/booking', 0, ?)
                    ''', (bn_row['tai_khoan_id'], tieu_de, noi_dung, now_str))

            conn.commit()
            conn.close()"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated update_status in appointment_model.py successfully!")
else:
    print("old_block not found in appointment_model.py!")
