"""VietQR contract checks without touching the production SQL Server."""
import hashlib
import hmac
import json
import unittest
from unittest.mock import patch

from app import create_app
from core.payment import parse_transactions, payment_details
from models.billing_model import BillingModel


class VietQRTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'isolated-test-secret-key-32bytes',
            'BANK_ID': 'MB', 'BANK_ACCOUNT_NO': '1234567890',
            'BANK_ACCOUNT_NAME': 'H2T Care', 'PAYMENT_WEBHOOK_SECRET': 'test-webhook-key'})
        self.client = self.app.test_client()

    def test_qr_contains_exact_amount_and_unique_invoice_reference(self):
        with self.app.app_context():
            payment = payment_details({'id': 105, 'ma_hoa_don': 'HD2609105', 'thanh_tien': 125000})
        self.assertEqual(payment['reference'], 'H2T105')
        self.assertEqual(payment['amount'], 125000)
        self.assertIn('amount=125000&addInfo=H2T105&accountName=H2T+Care', payment['qr_url'])

    def test_only_complete_reference_matches(self):
        payload = {'id': 7, 'accountNumber': '1234567890', 'content': 'H2T105ABC',
            'transferAmount': 125000, 'transferType': 'in'}
        self.assertIsNone(parse_transactions(payload)[0]['invoice_id'])
        payload['content'] = 'Thanh toan H2T105'
        self.assertEqual(parse_transactions(payload)[0]['invoice_id'], 105)

    def test_sepay_rejects_forged_and_wrong_account(self):
        payload = {'id': 7, 'accountNumber': '1234567890', 'content': 'H2T105',
            'transferAmount': 125000, 'transferType': 'in'}
        with patch('controllers.payment_controller.BillingModel.pay_invoice', return_value=(True, 'OK')) as pay:
            self.assertEqual(self.client.post('/api/payment/webhook', json=payload).status_code, 401)
            payload['accountNumber'] = '9999999999'
            response = self.client.post('/api/payment/webhook', json=payload,
                headers={'Authorization': 'Apikey test-webhook-key'})
            self.assertEqual(response.status_code, 409)
            pay.assert_not_called()
            payload['accountNumber'] = '1234567890'
            response = self.client.post('/api/payment/webhook', json=payload,
                headers={'Authorization': 'Apikey test-webhook-key'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['paid'], [105])
            self.assertEqual(pay.call_args.kwargs['expected_amount'], 125000)

    def test_casso_v2_signature_and_outgoing_payment(self):
        payload = {'error': 0, 'data': {'id': 8, 'accountNumber': '1234567890',
            'description': 'H2T105', 'amount': 125000}}
        timestamp = '1734924830020'
        signed = f"{timestamp}.{json.dumps(payload, sort_keys=True, separators=(',', ':'))}"
        digest = hmac.new(b'test-webhook-key', signed.encode(), hashlib.sha512).hexdigest()
        with patch('controllers.payment_controller.BillingModel.pay_invoice', return_value=(True, 'OK')) as pay:
            response = self.client.post('/api/payment/webhook', json=payload,
                headers={'X-Casso-Signature': f't={timestamp},v1={digest}'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(pay.call_args.kwargs['payment_event']['provider'], 'CASSO')
            response = self.client.post('/api/payment/webhook', json=payload,
                headers={'X-Casso-Signature': f't={timestamp},v1=' + '0'*128})
            self.assertEqual(response.status_code, 401)
            pay.reset_mock()
            outgoing = {'id': 9, 'accountNumber': '1234567890', 'content': 'H2T105',
                'transferAmount': 125000, 'transferType': 'out'}
            response = self.client.post('/api/payment/webhook', json=outgoing,
                headers={'Authorization': 'Apikey test-webhook-key'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['ignored'], ['9'])
            pay.assert_not_called()
            outgoing['transferAmount'] = -125000
            response = self.client.post('/api/payment/webhook', json=outgoing,
                headers={'Authorization': 'Apikey test-webhook-key'})
            self.assertEqual(response.status_code, 400)
            pay.assert_not_called()

    def test_mobile_status_is_scoped_to_own_invoice(self):
        class Connection:
            def cursor(self):
                return object()
            def close(self):
                pass
        identity = {'patient_id': 101, 'da_hoan_thien_ho_so': True}
        invoice = {'id': 105, 'benh_nhan_id': 202, 'trang_thai': 'Đã thanh toán'}
        with patch('controllers.payment_controller.get_db', return_value=Connection()), \
                patch('controllers.payment_controller.verify', return_value=(identity, None, None)), \
                patch('controllers.payment_controller.BillingModel.get_invoice', return_value=invoice):
            response = self.client.get('/api/payment/status/105',
                headers={'Authorization': 'Bearer valid-token'})
            self.assertEqual(response.status_code, 404)
            invoice['benh_nhan_id'] = 101
            response = self.client.get('/api/payment/status/105',
                headers={'Authorization': 'Bearer valid-token'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['status'], 'PAID')
            self.assertEqual(response.headers['Cache-Control'], 'private, no-store')

    def test_manual_transfer_cannot_bypass_bank_webhook(self):
        with self.app.test_request_context('/api/billing/pay'), \
                patch('models.billing_model.refresh_session_user', return_value={
                    'id': 1, 'vai_tro': 'LETAN', 'ho_ten': 'Thu ngân'}):
            success, _ = BillingModel.pay_invoice.__wrapped__(105,
                payment_method='Chuyển khoản VietQR', expected_amount=125000)
        self.assertFalse(success)

    def test_simulation_requires_debug_and_cashier(self):
        invoice = {'id': 105, 'thanh_tien': 125000}
        with patch('controllers.payment_controller.refresh_session_user',
                return_value={'id': 1, 'vai_tro': 'BENHNHAN'}), \
                patch('controllers.payment_controller.BillingModel.get_invoice', return_value=invoice), \
                patch('controllers.payment_controller.BillingModel.pay_invoice', return_value=(True, 'OK')) as pay:
            self.assertEqual(self.client.post('/api/payment/simulate-confirm/105').status_code, 403)
            pay.assert_not_called()
        self.app.config['DEBUG'] = False
        self.assertEqual(self.client.post('/api/payment/simulate-confirm/105').status_code, 404)


if __name__ == '__main__':
    unittest.main()
