with open('tests/test_upgraded_features.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace test_user in test_week_bounds_and_registration_rules
text = text.replace(
    "        test_user = {'id': 1, 'vai_tro': 'ADMIN', 'staff_id': 1}\n        ok_cur, msg_cur = ScheduleModel.register_schedule(test_user, today_str, ca_lam=1)",
    """        # Kiểm tra Admin bị chặn đăng ký ca trực
        test_admin = {'id': 1, 'vai_tro': 'ADMIN', 'staff_id': 1}
        ok_adm, msg_adm = ScheduleModel.register_schedule(test_admin, today_str, ca_lam=1)
        self.assertFalse(ok_adm)
        self.assertIn('không cần đăng ký ca trực', msg_adm)

        # Kiểm tra Bác sĩ đăng ký tuần hiện tại bị chặn
        test_user = {'id': 2, 'vai_tro': 'BACSI', 'staff_id': 2}
        ok_cur, msg_cur = ScheduleModel.register_schedule(test_user, today_str, ca_lam=1)"""
)

# Replace staff_id 1 with 2 in test_week_bounds_and_registration_rules cleanup
text = text.replace(
    "DELETE FROM lich_lam_viec WHERE nhan_vien_id = 1 AND ngay_lam = ?",
    "DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam = ?"
)

# Replace test_user in test_register_multiple_schedules
text = text.replace(
    "        test_user = {'id': 1, 'vai_tro': 'ADMIN', 'staff_id': 1}",
    "        test_user = {'id': 2, 'vai_tro': 'BACSI', 'staff_id': 2}"
)
text = text.replace(
    "DELETE FROM lich_lam_viec WHERE nhan_vien_id = 1 AND ngay_lam IN (?, ?)",
    "DELETE FROM lich_lam_viec WHERE nhan_vien_id IN (1, 2) AND ngay_lam IN (?, ?)"
)

# Replace sess['user'] in test_api_register_multiple
text = text.replace(
    """            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'ho_ten': 'Quản Trị Viên',
                'vai_tro': 'ADMIN',
                'staff_id': 1
            }""",
    """            sess['user'] = {
                'id': 2,
                'username': 'bacsi1',
                'ho_ten': 'BS. Trần Minh Quân',
                'vai_tro': 'BACSI',
                'staff_id': 2
            }"""
)

with open('tests/test_upgraded_features.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated tests/test_upgraded_features.py successfully")
