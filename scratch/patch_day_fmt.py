with open('models/schedule_model.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """            try:
                day_fmt = datetime.strptime(day_str, '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                day_fmt = day_str"""

replacement = """            day_fmt = f"{day_str[8:10]}/{day_str[5:7]}/{day_str[:4]}" if (len(day_str) == 10 and day_str[4] == '-') else day_str"""

# Also check join in get_work_statistics_and_history to remove correlated subquery
old_join = """                LEFT JOIN bac_si bs ON bs.id = COALESCE(llv.bac_si_id, (SELECT TOP 1 id FROM bac_si WHERE nhan_vien_id = llv.nhan_vien_id))
                LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                LEFT JOIN chuyen_khoa ck ON ck.id = COALESCE(bs.chuyen_khoa_id, pk.chuyen_khoa_id)"""

new_join = """                LEFT JOIN bac_si bs ON bs.id = llv.bac_si_id
                LEFT JOIN phong_kham pk ON llv.phong_kham_id = pk.id
                LEFT JOIN chuyen_khoa ck ON ck.id = pk.chuyen_khoa_id"""

changed = False
if target in text:
    text = text.replace(target, replacement, 1)
    changed = True
    print('Replaced day_fmt successfully!')

if old_join in text:
    text = text.replace(old_join, new_join, 1)
    changed = True
    print('Replaced join successfully!')

if changed:
    with open('models/schedule_model.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('models/schedule_model.py updated!')
else:
    print('No changes needed.')
