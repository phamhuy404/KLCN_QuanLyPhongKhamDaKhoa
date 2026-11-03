import io
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Optimize models/schedule_model.py joins
with open('models/schedule_model.py', 'r', encoding='utf-8') as f:
    s_code = f.read()

# 1. Optimize get_all query
old_get_all_join = """            LEFT JOIN bac_si bs ON llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id


            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id


            LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id"""

new_get_all_join = """            LEFT JOIN bac_si bs ON bs.id = COALESCE(llv.bac_si_id, (SELECT TOP 1 id FROM bac_si WHERE nhan_vien_id = llv.nhan_vien_id))
            LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
            LEFT JOIN chuyen_khoa ck ON ck.id = COALESCE(bs.chuyen_khoa_id, pk.chuyen_khoa_id)"""

if old_get_all_join in s_code:
    s_code = s_code.replace(old_get_all_join, new_get_all_join, 1)
    print("Optimized get_all join in schedule_model.py")
else:
    import re
    m = re.search(r"LEFT JOIN bac_si bs ON llv\.bac_si_id = bs\.id OR bs\.nhan_vien_id = nv\.id\s+LEFT JOIN phong_kham pk ON llv\.phong_kham_id = pk\.id\s+LEFT JOIN chuyen_khoa ck ON bs\.chuyen_khoa_id = ck\.id", s_code)
    if m:
        s_code = s_code[:m.start()] + new_get_all_join + s_code[m.end():]
        print("Optimized get_all join with regex in schedule_model.py")

# 2. Optimize get_work_statistics_and_history join
old_work_join = """                LEFT JOIN bac_si bs ON llv.bac_si_id = bs.id OR bs.nhan_vien_id = nv.id
                LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id OR pk.chuyen_khoa_id = ck.id"""

new_work_join = """                LEFT JOIN bac_si bs ON bs.id = COALESCE(llv.bac_si_id, (SELECT TOP 1 id FROM bac_si WHERE nhan_vien_id = llv.nhan_vien_id))
                LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                LEFT JOIN chuyen_khoa ck ON ck.id = COALESCE(bs.chuyen_khoa_id, pk.chuyen_khoa_id)"""

if old_work_join in s_code:
    s_code = s_code.replace(old_work_join, new_work_join, 1)
    print("Optimized get_work_statistics_and_history join in schedule_model.py")
else:
    import re
    m = re.search(r"LEFT JOIN bac_si bs ON llv\.bac_si_id = bs\.id OR bs\.nhan_vien_id = nv\.id\s+LEFT JOIN phong_kham pk ON llv\.phong_kham_id = pk\.id\s+LEFT JOIN chuyen_khoa ck ON bs\.chuyen_khoa_id = ck\.id OR pk\.chuyen_khoa_id = ck\.id", s_code)
    if m:
        s_code = s_code[:m.start()] + new_work_join + s_code[m.end():]
        print("Optimized get_work_statistics_and_history join with regex in schedule_model.py")

with open('models/schedule_model.py', 'w', encoding='utf-8') as f:
    f.write(s_code)

print("ScheduleModel joins optimized successfully!")
