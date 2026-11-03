import sys
import os

filepath = 'models/schedule_model.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

def robust_replace(src, find_str, rep_str):
    if find_str in src:
        return src.replace(find_str, rep_str), True
    find_crlf = find_str.replace('\r\n', '\n').replace('\n', '\r\n')
    rep_crlf = rep_str.replace('\r\n', '\n').replace('\n', '\r\n')
    if find_crlf in src:
        return src.replace(find_crlf, rep_crlf), True
    return src, False

old_sig = """    def get_work_statistics_and_history(current_user, selected_month=None, scope=None, filter_staff_id=None, months_back=6):"""
new_sig = """    def get_work_statistics_and_history(current_user, selected_month=None, scope=None, filter_staff_id=None, months_back=6,
                                         filter_dept_id=None, filter_role=None, search_keyword=None):"""

content, ok1 = robust_replace(content, old_sig, new_sig)
print("Updated signature:", ok1)

old_target_setup = """                if effective_scope == 'mine':
                    target_staff_ids = {int(own_staff_id)} if own_staff_id else {-1}
                elif filter_staff_id and str(filter_staff_id).isdigit():
                    target_staff_ids = {int(filter_staff_id)}
                else:
                    target_staff_ids = None"""

new_target_setup = """                if effective_scope == 'mine':
                    target_staff_ids = {int(own_staff_id)} if own_staff_id else {-1}
                elif filter_staff_id and str(filter_staff_id).isdigit():
                    target_staff_ids = {int(filter_staff_id)}
                else:
                    target_staff_ids = None

                # Lọc bổ sung theo khoa, vị trí / vai trò và từ khóa tìm kiếm
                if filter_dept_id and str(filter_dept_id).strip():
                    f_dept = str(filter_dept_id).strip()
                    dept_staff = set()
                    for s in all_staff_rows if 'all_staff_rows' in locals() else []:
                        if str(s.get('chuyen_khoa_id')) == f_dept or f_dept.lower() in (s.get('ten_khoa') or '').lower():
                            dept_staff.add(s['nhan_vien_id'])
                    # Sẽ áp dụng sau khi nạp all_staff_rows bên dưới"""

# Wait, all_staff_rows is loaded right below in line 2757!
# Let's check where all_staff_rows is loaded.
old_staff_query = """            cursor.execute('''
                SELECT nv.id AS nhan_vien_id, nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.trang_thai,
                       t.id AS tai_khoan_id, v.ma_vai_tro, v.ten_vai_tro,
                       bs.id AS bac_si_id, bs.hoc_vi, ck.ten_khoa
                FROM nhan_vien nv
                LEFT JOIN tai_khoan t ON nv.tai_khoan_id = t.id
                LEFT JOIN vai_tro v ON t.vai_tro_id = v.id
                LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
                LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
                ORDER BY CASE WHEN v.ma_vai_tro = 'BACSI' THEN 0 ELSE 1 END, nv.id ASC
            ''')
            all_staff_rows = [dict(r) for r in cursor.fetchall()]"""

new_staff_query = """            cursor.execute('''
                SELECT nv.id AS nhan_vien_id, nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.trang_thai,
                       t.id AS tai_khoan_id, v.ma_vai_tro, v.ten_vai_tro,
                       bs.id AS bac_si_id, bs.hoc_vi, bs.chuyen_khoa_id, ck.ten_khoa
                FROM nhan_vien nv
                LEFT JOIN tai_khoan t ON nv.tai_khoan_id = t.id
                LEFT JOIN vai_tro v ON t.vai_tro_id = v.id
                LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
                LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
                ORDER BY CASE WHEN v.ma_vai_tro = 'BACSI' THEN 0 ELSE 1 END, nv.id ASC
            ''')
            all_staff_rows = [dict(r) for r in cursor.fetchall()]

            # Áp dụng bộ lọc nâng cao theo Khoa, Vị trí và Từ khóa tìm kiếm
            if can_view_all and effective_scope != 'mine':
                if filter_dept_id and str(filter_dept_id).strip():
                    f_dept = str(filter_dept_id).strip()
                    dept_ids = {
                        s['nhan_vien_id'] for s in all_staff_rows
                        if str(s.get('chuyen_khoa_id')) == f_dept or (f_dept.isdigit() and int(s.get('chuyen_khoa_id') or -1) == int(f_dept)) or f_dept.lower() in (s.get('ten_khoa') or '').lower()
                    }
                    target_staff_ids = dept_ids if target_staff_ids is None else (target_staff_ids & dept_ids)

                if filter_role and str(filter_role).strip():
                    f_role = str(filter_role).strip().upper()
                    role_ids = {
                        s['nhan_vien_id'] for s in all_staff_rows
                        if (s.get('ma_vai_tro') or '').upper() == f_role or (s.get('ten_vai_tro') or '').upper() == f_role
                    }
                    target_staff_ids = role_ids if target_staff_ids is None else (target_staff_ids & role_ids)

                if search_keyword and str(search_keyword).strip():
                    kw = str(search_keyword).strip().lower()
                    kw_ids = {
                        s['nhan_vien_id'] for s in all_staff_rows
                        if kw in (s.get('ho_ten') or '').lower() or kw in (s.get('ma_nhan_vien') or '').lower()
                    }
                    target_staff_ids = kw_ids if target_staff_ids is None else (target_staff_ids & kw_ids)"""

content, ok2 = robust_replace(content, old_staff_query, new_staff_query)
print("Updated staff query and target_staff_ids:", ok2)

# Also update the return dict in get_work_statistics_and_history
old_ret = """            'available_months': [
                {'key': mk, 'label': f"Tháng {mk[5:7]}/{mk[:4]}"}
                for mk in available_months
            ],
            'totals': totals,
            'monthly_summary': monthly_summary,
            'staff_stats': staff_stats_list,
            'shift_history': shift_history[:500]
        }"""

new_ret = """            'available_months': [
                {'key': mk, 'label': f"Tháng {mk[5:7]}/{mk[:4]}"}
                for mk in available_months
            ],
            'selected_dept_id': str(filter_dept_id or ''),
            'selected_role': str(filter_role or ''),
            'search_keyword': str(search_keyword or ''),
            'totals': totals,
            'monthly_summary': monthly_summary,
            'staff_stats': staff_stats_list,
            'shift_history': shift_history[:500]
        }"""

content, ok3 = robust_replace(content, old_ret, new_ret)
print("Updated return dict in schedule_model.py:", ok3)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated schedule_model.py successfully!")
