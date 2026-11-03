with open('models/user_model.py', 'r', encoding='utf-8') as f:
    s = f.read()

target = """SELECT nv.id AS staff_id, nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.email, nv.trang_thai AS staff_status,

                       bs.id AS bac_si_id, bs.hoc_vi"""

replacement = """SELECT nv.id AS staff_id, nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.email, nv.trang_thai AS staff_status,

                       bs.id AS bac_si_id, bs.hoc_vi, bs.chuyen_khoa_id, bs.phong_kham_chinh_id"""

target_dict = """                    'bac_si_id': staff_row['bac_si_id'],

                    'hoc_vi': staff_row['hoc_vi']"""

replacement_dict = """                    'bac_si_id': staff_row['bac_si_id'],

                    'hoc_vi': staff_row['hoc_vi'],

                    'chuyen_khoa_id': staff_row.get('chuyen_khoa_id'),

                    'phong_kham_chinh_id': staff_row.get('phong_kham_chinh_id')"""

assert target in s, "target not found"
assert target_dict in s, "target_dict not found"

s = s.replace(target, replacement, 1)
s = s.replace(target_dict, replacement_dict, 1)

with open('models/user_model.py', 'w', encoding='utf-8') as f:
    f.write(s)
print("Successfully patched models/user_model.py")
