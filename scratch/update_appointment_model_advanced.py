import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open('models/appointment_model.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update get_for_user
target_get_for_user = """        filtered = []
        for a in all_appts:
            # 1. Lịch hẹn do chính bác sĩ phụ trách
            if doctor_id and a.get('bac_si_id') == doctor_id:
                filtered.append(a)
            # 2. Hoặc lịch hẹn chưa có người nhận nhưng cùng chuyên khoa
            elif not a.get('bac_si_id') and dept_id and a.get('chuyen_khoa_id') == dept_id:
                filtered.append(a)"""

repl_get_for_user = """        filtered = []
        for a in all_appts:
            # Bác sĩ chỉ thấy các lịch hẹn ĐÃ ĐƯỢC TIẾP NHẬN / DUYỆT bởi Admin hoặc Lễ tân
            if a.get('trang_thai') in ['Chờ tiếp nhận', 'Chờ xác nhận']:
                continue

            # 1. Lịch hẹn do chính bác sĩ phụ trách đã được tiếp nhận
            if doctor_id and a.get('bac_si_id') == doctor_id:
                filtered.append(a)
            # 2. Hoặc lịch hẹn chưa có người nhận nhưng cùng chuyên khoa đã được tiếp nhận
            elif not a.get('bac_si_id') and dept_id and a.get('chuyen_khoa_id') == dept_id:
                filtered.append(a)"""

code = code.replace(target_get_for_user, repl_get_for_user).replace(target_get_for_user.replace('\n', '\r\n'), repl_get_for_user.replace('\n', '\r\n'))

# 2. Add get_doctors_by_shift method before assign_doctor
target_method_anchor = "    @staticmethod\n    def assign_doctor(appointment_id, doctor_id, user_info=None):"
target_method_anchor_crlf = "    @staticmethod\r\n    def assign_doctor(appointment_id, doctor_id, user_info=None):"

new_method = """    @staticmethod
    def get_doctors_by_shift(ngay_kham, gio_kham, chuyen_khoa_id=None):
        \"\"\"Lấy danh sách các bác sĩ có ca trực tương ứng với ngày và giờ khám được chọn.\"\"\"
        t = str(gio_kham).strip()
        if 'AM' in t or 'PM' in t:
            try:
                t = datetime.strptime(t, '%I:%M %p').strftime('%H:%M')
            except Exception:
                pass
        h_m = t[:5]
        if h_m in ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30']:
            shift = 1
        elif h_m in ['14:30', '15:00', '15:30', '16:00']:
            shift = 2
        elif h_m in ['18:30', '19:00', '19:30']:
            shift = 3
        else:
            try:
                hour = int(h_m.split(':')[0])
                if hour < 12:
                    shift = 1
                elif hour < 17:
                    shift = 2
                else:
                    shift = 3
            except Exception:
                shift = 1

        work_date_str = str(ngay_kham)[:10]

        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT 
                bs.id, bs.hoc_vi, bs.avatar, bs.kinh_nghiem, bs.gia_kham,
                nv.ho_ten, nv.sdt,
                ck.id AS chuyen_khoa_id, ck.ten_khoa,
                pk.id AS phong_kham_id, pk.ten_phong,
                llv.ca_lam, llv.gio_bat_dau, llv.gio_ket_thuc,
                llv.so_luong_kham_toi_da, llv.so_luong_da_dang_ky
            FROM lich_lam_viec llv
            JOIN bac_si bs ON llv.bac_si_id = bs.id
            JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            WHERE llv.ngay_lam = ? 
              AND llv.ca_lam = ?
              AND (llv.trang_thai_duyet = 'DA_DUYET' OR llv.trang_thai_duyet IS NULL)
              AND (llv.trang_thai = 1 OR llv.trang_thai IS NULL)
        '''
        params = [work_date_str, shift]
        if chuyen_khoa_id:
            sql += ' AND bs.chuyen_khoa_id = ?'
            params.append(int(chuyen_khoa_id))

        sql += ' ORDER BY bs.id'
        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows, shift

"""

if target_method_anchor in code:
    code = code.replace(target_method_anchor, new_method + target_method_anchor)
    print("Added get_doctors_by_shift LF")
elif target_method_anchor_crlf in code:
    code = code.replace(target_method_anchor_crlf, new_method.replace('\n', '\r\n') + target_method_anchor_crlf)
    print("Added get_doctors_by_shift CRLF")
else:
    print("Anchor for get_doctors_by_shift not found!")

# 3. In create: Change default status to 'Chờ tiếp nhận'
code = code.replace("'Chờ xác nhận')", "'Chờ tiếp nhận')")
code = code.replace("Trạng thái: Chờ xác nhận.", "Trạng thái: Chờ tiếp nhận.")

with open('models/appointment_model.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated models/appointment_model.py successfully!")
