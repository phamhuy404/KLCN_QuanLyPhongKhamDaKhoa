with open('controllers/api_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = "docs = AppointmentModel.get_doctors_with_availability(dept_id, date_str)\n    return jsonify({'success': True, 'doctors': docs})"
target_crlf = "docs = AppointmentModel.get_doctors_with_availability(dept_id, date_str)\r\n    return jsonify({'success': True, 'doctors': docs})"

addition = """

@api_bp.route('/doctors/available-by-shift', methods=['GET'])
def doctors_available_by_shift():
    \"\"\"API lấy danh sách bác sĩ có ca trực tương ứng theo ngày và khung giờ khám đã chọn.\"\"\"
    from datetime import datetime
    ngay_kham = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')
    gio_kham = request.args.get('time') or '08:00'
    dept_id = request.args.get('department_id', type=int)

    doctors, shift = AppointmentModel.get_doctors_by_shift(ngay_kham, gio_kham, dept_id)
    shift_names = {1: 'Ca Sáng (07:00 - 11:30)', 2: 'Ca Chiều (13:30 - 17:00)', 3: 'Ca Tối (17:30 - 20:30)'}
    return jsonify({
        'success': True,
        'shift': shift,
        'shift_name': shift_names.get(shift, 'Ca khám'),
        'doctors': doctors,
        'total': len(doctors)
    })"""

if target in c:
    c = c.replace(target, target + addition)
    print('Inserted LF')
elif target_crlf in c:
    c = c.replace(target_crlf, target_crlf + addition.replace('\n', '\r\n'))
    print('Inserted CRLF')
else:
    print('Target not found')

with open('controllers/api_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done!')
