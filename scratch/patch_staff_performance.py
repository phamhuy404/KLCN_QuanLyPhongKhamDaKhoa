import io
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. Patch models/schedule_model.py
with open('models/schedule_model.py', 'r', encoding='utf-8') as f:
    s_code = f.read()

# Replace slow strptime loop in get_all
old_loop = """            w_date = r['ngay_lam']


            if isinstance(w_date, str):


                w_date = datetime.strptime(w_date[:10], '%Y-%m-%d').date()





            r['is_current_week'] = bool(w_date <= end_current_week)


            r['is_next_2_weeks'] = bool(start_w1 <= w_date <= end_w2)"""

new_loop = """            w_date_str = str(r['ngay_lam'])[:10]
            end_cw_str = end_current_week.strftime('%Y-%m-%d')
            start_w1_str = start_w1.strftime('%Y-%m-%d')
            end_w2_str = end_w2.strftime('%Y-%m-%d')

            r['is_current_week'] = bool(w_date_str <= end_cw_str)
            r['is_next_2_weeks'] = bool(start_w1_str <= w_date_str <= end_w2_str)"""

if old_loop in s_code:
    s_code = s_code.replace(old_loop, new_loop, 1)
    print("Replaced slow strptime in schedule_model.get_all")
else:
    print("Note: old_loop not found in exact whitespace, searching normalized...")
    import re
    m = re.search(r"w_date\s*=\s*r\['ngay_lam'\].*?r\['is_next_2_weeks'\]\s*=\s*bool\(start_w1\s*<=\s*w_date\s*<=\s*end_w2\)", s_code, re.DOTALL)
    if m:
        s_code = s_code[:m.start()] + new_loop + s_code[m.end():]
        print("Replaced slow strptime using regex in schedule_model.get_all")

with open('models/schedule_model.py', 'w', encoding='utf-8') as f:
    f.write(s_code)

# 2. Patch controllers/admin_controller.py to generate lean_schedules
with open('controllers/admin_controller.py', 'r', encoding='utf-8') as f:
    c_code = f.read()

old_render = """        schedules=schedules,
        roles=roles,"""

new_render = """        schedules=schedules,
        lean_schedules=[{
            'id': s['id'],
            'ngay_lam': str(s['ngay_lam'])[:10],
            'ca_lam': s['ca_lam'],
            'ten_ca': s.get('ten_ca') or f"Ca {s['ca_lam']}",
            'staff_id': s.get('staff_id'),
            'nhan_vien_id': s.get('nhan_vien_id'),
            'bac_si_id': s.get('bac_si_id'),
            'ten_bac_si': s.get('ten_bac_si') or s.get('ten_nhan_vien') or '',
            'ten_nhan_vien': s.get('ten_nhan_vien') or s.get('ten_bac_si') or '',
            'ten_vai_tro': s.get('ten_vai_tro') or '',
            'ten_khoa': s.get('ten_khoa') or '',
            'ten_phong': s.get('ten_phong') or '',
            'vi_tri_tang': s.get('vi_tri_tang') or '',
            'phong_kham_id': s.get('phong_kham_id'),
            'trang_thai_duyet': s.get('trang_thai_duyet') or 'DA_DUYET',
            'is_my_shift': bool(s.get('is_my_shift')),
            'can_request_cancel': bool(s.get('can_request_cancel')),
            'is_next_2_weeks': bool(s.get('is_next_2_weeks')),
            'is_current_week': bool(s.get('is_current_week')),
            'is_past': bool(s.get('is_past')),
        } for s in schedules],
        roles=roles,"""

if old_render in c_code:
    c_code = c_code.replace(old_render, new_render, 1)
    with open('controllers/admin_controller.py', 'w', encoding='utf-8') as f:
        f.write(c_code)
    print("Added lean_schedules in admin_controller.py")
else:
    print("old_render not found in admin_controller.py")

# 3. Patch templates/admin/staff.html
with open('templates/admin/staff.html', 'r', encoding='utf-8') as f:
    h_code = f.read()

# Replace full JSON dump with lean_schedules
old_json_tag = '<script id="schedules-data-json" type="application/json">{{ schedules|tojson|safe }}</script>'
new_json_tag = '<script id="schedules-data-json" type="application/json">{{ (lean_schedules or schedules)|tojson|safe }}</script>'
if old_json_tag in h_code:
    h_code = h_code.replace(old_json_tag, new_json_tag, 1)
    print("Replaced schedules-data-json with lean_schedules in staff.html")

# Limit initial server rendering of schedules table to top 100
old_loop_html = '{% for sc in schedules %}'
new_loop_html = '{% for sc in schedules[:100] %}'
if old_loop_html in h_code:
    h_code = h_code.replace(old_loop_html, new_loop_html, 1)
    print("Limited initial schedules table rendering to top 100 rows in staff.html")

with open('templates/admin/staff.html', 'w', encoding='utf-8') as f:
    f.write(h_code)

print("Patching completed!")
