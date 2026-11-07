"""VietQR status polling, bank webhook, and local demonstration confirmation."""
import hmac

from flask import Blueprint, current_app, jsonify, request

from core.database import get_db
from core.mobile_auth import MobileAuthError, bearer, verify
from core.payment import bank_ready, parse_transactions, webhook_authorized
from core.scheduling import CalendarError
from core.security import refresh_session_user, require_patient_access
from models.billing_model import BillingModel


payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')


def requested_invoice(invoice_id):
    if request.headers.get('Authorization', '').lower().startswith('bearer '):
        connection = get_db()
        try:
            user, _, _ = verify(connection.cursor(), bearer())
        except MobileAuthError as error:
            return None, (jsonify(success=False, message=error.message), error.status)
        finally:
            connection.close()
        if not user.get('da_hoan_thien_ho_so'):
            return None, (jsonify(success=False, message='Vui lòng hoàn thiện hồ sơ.'), 409)
        patient_id = user['patient_id']
    else:
        user = refresh_session_user()
        if not user:
            return None, (jsonify(success=False, message='Cần đăng nhập.'), 401)
        patient_id = None
    invoice = BillingModel.get_invoice(invoice_id)
    if not invoice:
        return None, (jsonify(success=False, message='Không tìm thấy hóa đơn.'), 404)
    if patient_id is not None:
        if invoice['benh_nhan_id'] != patient_id:
            return None, (jsonify(success=False, message='Không tìm thấy hóa đơn.'), 404)
    else:
        require_patient_access(invoice['benh_nhan_id'])
    return invoice, None


@payment_bp.get('/status/<int:invoice_id>')
def status(invoice_id):
    invoice, error = requested_invoice(invoice_id)
    if error:
        return error
    state = {'Đã thanh toán': 'PAID', 'Chưa thanh toán': 'PENDING', 'Đã hủy': 'CANCELED'}.get(
        invoice['trang_thai'], 'UNKNOWN')
    invoice['clinic_name'] = 'Phòng Khám Đa Khoa H2T Care'
    invoice['clinic_address'] = current_app.config.get('CLINIC_ADDRESS', '')
    response = jsonify(success=True, status=state, invoice=invoice)
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@payment_bp.post('/webhook')
def webhook():
    if not bank_ready():
        return jsonify(success=False, message='Chưa cấu hình thanh toán.'), 503
    if not webhook_authorized():
        return jsonify(success=False, message='Webhook không hợp lệ.'), 401
    if request.content_length and request.content_length > 65536:
        return jsonify(success=False, message='Payload quá lớn.'), 413
    try:
        transactions = parse_transactions(request.get_json(silent=True))
    except (CalendarError, ValueError, TypeError) as error:
        return jsonify(success=False, message=str(error)), 400
    paid, ignored, rejected = [], [], []
    account = str(current_app.config['BANK_ACCOUNT_NO']).strip()
    for transaction in transactions:
        invoice_id = transaction['invoice_id']
        if invoice_id is None or not transaction['incoming']:
            ignored.append(transaction['event_id'])
            continue
        if not hmac.compare_digest(transaction['account'], account):
            rejected.append({'event_id': transaction['event_id'], 'reason': 'Sai tài khoản nhận.'})
            continue
        success, message = BillingModel.pay_invoice(invoice_id,
            payment_method='Chuyển khoản VietQR', expected_amount=transaction['amount'],
            payment_event=transaction)
        if success:
            paid.append(invoice_id)
        else:
            rejected.append({'event_id': transaction['event_id'], 'reason': message})
    # A failed reconciliation must remain visible to the provider for retry/review.
    return jsonify(success=not rejected, paid=paid, ignored=ignored, rejected=rejected), 409 if rejected else 200


@payment_bp.post('/simulate-confirm/<int:invoice_id>')
def simulate_confirm(invoice_id):
    if not current_app.debug or request.remote_addr not in ('127.0.0.1', '::1'):
        return jsonify(success=False, message='Chỉ dùng trên localhost ở chế độ DEBUG.'), 404
    user = refresh_session_user()
    if not user:
        return jsonify(success=False, message='Cần đăng nhập.'), 401
    if user.get('vai_tro') not in ('ADMIN', 'LETAN'):
        return jsonify(success=False, message='Chỉ thu ngân được giả lập xác nhận.'), 403
    invoice = BillingModel.get_invoice(invoice_id)
    if not invoice:
        return jsonify(success=False, message='Không tìm thấy hóa đơn.'), 404
    success, message = BillingModel.pay_invoice(invoice_id,
        payment_method='Chuyển khoản VietQR', expected_amount=invoice['thanh_tien'],
        payment_event={'provider': 'SIMULATED', 'event_id': f'DEBUG-{invoice_id}',
                       'amount': invoice['thanh_tien'], 'content': f'H2T{invoice_id} debug'})
    return jsonify(success=success, message=message), 200 if success else 409
