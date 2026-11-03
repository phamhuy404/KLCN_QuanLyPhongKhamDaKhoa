with open('controllers/api_controller.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. In save_emr_examination
target1 = """    if not patient_id:
        return jsonify({'success': False, 'message': 'Thiếu ID bệnh nhân!'}), 400

    success, result = MedicalRecordModel.save_examination("""

replacement1 = """    if not patient_id:
        return jsonify({'success': False, 'message': 'Thiếu ID bệnh nhân!'}), 400

    if reexam_date and str(reexam_date).strip():
        from datetime import timedelta
        min_reexam = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        if str(reexam_date)[:10] < min_reexam:
            return jsonify(success=False, message=f'Ngày hẹn tái khám phải cách ít nhất 2 ngày so với ngày hiện tại (sớm nhất từ ngày {min_reexam})!'), 400
    else:
        reexam_date = None
        reexam_time = None

    success, result = MedicalRecordModel.save_examination("""

assert target1 in text, "target1 not found"
text = text.replace(target1, replacement1)

# 2. In finish_emr_examination
target2 = """    if not record_id:
        return jsonify({'success': False, 'message': 'Thiếu ID phiếu khám bệnh cần hoàn tất!'}), 400

    user = session.get('user')
    success, msg = MedicalRecordModel.finish_examination("""

replacement2 = """    if not record_id:
        return jsonify({'success': False, 'message': 'Thiếu ID phiếu khám bệnh cần hoàn tất!'}), 400

    if reexam_date and str(reexam_date).strip():
        from datetime import timedelta
        min_reexam = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        if str(reexam_date)[:10] < min_reexam:
            return jsonify(success=False, message=f'Ngày hẹn tái khám phải cách ít nhất 2 ngày so với ngày hiện tại (sớm nhất từ ngày {min_reexam})!'), 400
    else:
        reexam_date = None
        reexam_time = None

    user = session.get('user')
    success, msg = MedicalRecordModel.finish_examination("""

assert target2 in text, "target2 not found"
text = text.replace(target2, replacement2)

with open('controllers/api_controller.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully patched controllers/api_controller.py!')
