with open('controllers/api_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = """@api_bp.route('/lab/result/save', methods=['POST'])
@roles_required('ADMIN', 'KTV')
def save_lab_result():
    \"\"\"API kỹ thuật viên nhập/cập nhật kết quả xét nghiệm (Chặn sửa nếu đã duyệt).\"\"\"
    data = request.get_json() or {}
    chi_tiet_id = data.get('chi_tiet_id') or data.get('order_id')
    ket_qua = data.get('ket_qua')
    file_ket_qua = data.get('file_ket_qua')
    user = session.get('user')

    if not chi_tiet_id or not ket_qua:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID chỉ định và nội dung kết quả xét nghiệm!'}), 400

    ok, msg = MedicalRecordModel.update_lab_result(chi_tiet_id, ket_qua, file_ket_qua=file_ket_qua, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400"""

replacement = """@api_bp.route('/lab/result/save', methods=['POST'])
@roles_required('ADMIN', 'KTV', 'BACSI')
def save_lab_result():
    \"\"\"API kỹ thuật viên nhập/cập nhật kết quả xét nghiệm và tải lên ảnh chụp siêu âm, X-quang.\"\"\"
    from core.image_service import process_image_input

    file_ket_qua = None
    if request.is_json:
        data = request.get_json() or {}
        chi_tiet_id = data.get('chi_tiet_id') or data.get('order_id')
        ket_qua = data.get('ket_qua')
        file_ket_qua = data.get('file_ket_qua')
    else:
        chi_tiet_id = request.form.get('chi_tiet_id') or request.form.get('order_id')
        ket_qua = request.form.get('ket_qua')
        file_ket_qua = request.form.get('file_ket_qua')

        image_file = request.files.get('image_file')
        if image_file and getattr(image_file, 'filename', None):
            saved_path, err = process_image_input(image_file, 'can_lam_sang')
            if saved_path:
                file_ket_qua = saved_path

    user = session.get('user')

    if not chi_tiet_id or not ket_qua:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp ID chỉ định và nội dung kết quả xét nghiệm!'}), 400

    ok, msg = MedicalRecordModel.update_lab_result(chi_tiet_id, ket_qua, file_ket_qua=file_ket_qua, audit_user=user)
    if ok:
        return jsonify({'success': True, 'message': msg, 'file_ket_qua': file_ket_qua})
    return jsonify({'success': False, 'message': msg}), 400"""

c = c.replace(target, replacement).replace(target.replace('\n', '\r\n'), replacement.replace('\n', '\r\n'))

with open('controllers/api_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated save_lab_result in controllers/api_controller.py successfully!')
