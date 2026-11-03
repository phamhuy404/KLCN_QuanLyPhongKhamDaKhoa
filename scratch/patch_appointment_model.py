import re

with open('models/appointment_model.py', 'r', encoding='utf-8') as f:
    code = f.read()

assign_pat = r'def assign_doctor\(appointment_id, doctor_id, user_info=None, approve_now=True\):\s+"""Phân công bác sĩ cho lịch hẹn hoặc bác sĩ tự nhận lịch hẹn, duyệt đơn và tự động hủy lịch trùng."""\s+conn = get_db\(\)'

m1 = re.search(assign_pat, code)
assert m1, 'assign_doctor pattern not matched'

rep1 = """def assign_doctor(appointment_id, doctor_id, user_info=None, approve_now=True):
        \"\"\"Phân công bác sĩ cho lịch hẹn hoặc bác sĩ tự nhận lịch hẹn, duyệt đơn và tự động hủy lịch trùng.\"\"\"
        if user_info and user_info.get('vai_tro') == 'BACSI':
            return False, 'Bác sĩ không có quyền phân công hoặc duyệt lịch hẹn! Thao tác này chỉ dành cho Lễ tân hoặc Quản trị viên.'
        conn = get_db()"""

code = code[:m1.start()] + rep1 + code[m1.end():]

status_pat = r'def update_status\(appointment_id, new_status, user_info=None\):\s+"""Cập nhật trạng thái lịch hẹn khám và ghi audit trail."""'

m2 = re.search(status_pat, code)
assert m2, 'update_status pattern not matched'

rep2 = """def update_status(appointment_id, new_status, user_info=None):
        \"\"\"Cập nhật trạng thái lịch hẹn khám và ghi audit trail.\"\"\"
        if user_info and user_info.get('vai_tro') == 'BACSI':
            return False, 'Bác sĩ không có quyền đổi trạng thái hoặc duyệt lịch hẹn! Thao tác này chỉ dành cho Lễ tân hoặc Quản trị viên.'"""

code = code[:m2.start()] + rep2 + code[m2.end():]

with open('models/appointment_model.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Successfully patched appointment_model.py!')
