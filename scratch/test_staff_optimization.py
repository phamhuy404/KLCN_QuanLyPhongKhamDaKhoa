import io
import sys
import os
import time

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models.schedule_model import ScheduleModel

curr_user = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN', 'staff_id': 1}

t0 = time.time()
schedules = ScheduleModel.get_all(current_user=curr_user)
t_fetch = (time.time() - t0) * 1000

t0 = time.time()
lean_schedules = [{
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
} for s in schedules]
t_lean = (time.time() - t0) * 1000

import json
json_full = json.dumps(schedules)
json_lean = json.dumps(lean_schedules)

print(f"Fetch {len(schedules)} schedules: {t_fetch:.2f} ms")
print(f"Lean transformation: {t_lean:.2f} ms")
print(f"Full JSON size: {len(json_full)//1024} KB")
print(f"Lean JSON size: {len(json_lean)//1024} KB (Reduction: {(1 - len(json_lean)/len(json_full))*100:.1f}%)")
