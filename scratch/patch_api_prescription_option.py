with open('controllers/api_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_route = """

@api_bp.route('/prescription/choose-buying-option', methods=['POST'])
def choose_prescription_buying_option():
    \"\"\"API xử lý lựa chọn nơi mua thuốc của bệnh nhân (Tự mua ngoài hoặc Mua tại bệnh viện).\"\"\"
    data = request.get_json() or {}
    dt_id = data.get('prescription_id') or data.get('don_thuoc_id')
    option = data.get('option', 'Mua tại bệnh viện')
    user = session.get('user', {})

    if not dt_id:
        return jsonify({'success': False, 'message': 'Thiếu mã đơn thuốc!'}), 400

    success, msg = PharmacyModel.choose_medicine_purchase_option(dt_id, option, audit_user=user)
    if success:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400
"""

if "def choose_prescription_buying_option" not in c:
    c += new_route
    with open('controllers/api_controller.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Added choose_prescription_buying_option to api_controller.py")
else:
    print("choose_prescription_buying_option already exists")
