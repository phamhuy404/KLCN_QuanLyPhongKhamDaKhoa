"""Billing unit/HTTP tests: no real database, notifications or payments."""
import unittest
from unittest.mock import Mock, patch
from decimal import Decimal
from core.billing_policy import validate_invoice, consultation_price, money, fetch_invoice
from core.scheduling import CalendarError
from app import create_test_app
from models.billing_model import BillingModel
from models.user_model import UserModel


class BillingAccessTests(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.client = self.app.test_client()

    def login(self, role='BENHNHAN'):
        with self.client.session_transaction() as session:
            session.update(logged_in=True, user={'id': 1})
        return patch.object(UserModel, 'get_session_user', return_value={
            'id': 1, 'vai_tro': role, 'patient_id': 101, 'ho_ten': 'Unit test'})

    def test_patient_cannot_confirm_receipt_of_money(self):
        with self.login(), patch.object(BillingModel, 'pay_invoice', return_value=(True, 'paid')) as pay:
            response = self.client.post('/api/billing/pay', json={'invoice_id': 1})
            self.assertEqual(response.status_code, 403)
            pay.assert_not_called()

    def test_anonymous_wrong_role_locked_and_deleted_cannot_collect(self):
        self.assertEqual(self.client.post('/api/billing/pay', json={}).status_code, 401)
        for role in ('BACSI', 'DUOCSI', 'KTV'):
            with self.login(role), patch.object(BillingModel, 'pay_invoice') as pay:
                self.assertEqual(self.client.post('/api/billing/pay', json={}).status_code, 403)
                pay.assert_not_called()
        for _ in range(2):
            with self.login(), patch.object(UserModel, 'get_session_user', return_value=None):
                self.assertEqual(self.client.post('/api/billing/pay', json={}).status_code, 401)

    def test_staff_must_confirm_actual_receipt_and_supply_amount(self):
        for role in ('ADMIN', 'LETAN'):
            with self.login(role), patch.object(BillingModel, 'pay_invoice', return_value=(True, 'received')) as pay:
                self.assertEqual(self.client.post('/api/billing/pay', json={'invoice_id': 1}).status_code, 400)
                self.assertEqual(self.client.post('/api/billing/pay', json={'invoice_id': 1, 'confirm_received': True}).status_code, 400)
                response = self.client.post('/api/billing/pay', json={'invoice_id': 1, 'confirm_received': True,
                    'expected_amount': 100, 'cashier_name': 'spoofed'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(pay.call_args.kwargs['audit_user']['vai_tro'], role)
                self.assertNotIn('cashier_name', pay.call_args.kwargs)

    def test_own_and_other_invoice_view_and_request_share_policy(self):
        # Exercise the real common ownership policy, mocking only its patient existence query.
        db = Mock()
        db.cursor.return_value.fetchone.return_value = {'id': 101}
        for owner, status in ((101, 200), (102, 403)):
            bill = {'id': 1, 'benh_nhan_id': owner, 'trang_thai': 'Chưa thanh toán'}
            with self.login(), patch.object(BillingModel, 'get_invoice', return_value=bill), \
                 patch('core.database.get_db', return_value=db), \
                 patch.object(BillingModel, 'payment_instructions', return_value=(True, {'amount': 100})) as instructions:
                self.assertEqual(self.client.get('/api/billing/invoice/1').status_code, status)
                response = self.client.post('/api/billing/request', json={'invoice_id': 1, 'amount': 1})
                self.assertEqual(response.status_code, status)
                if status == 200:
                    self.assertFalse(response.get_json()['payment_confirmed'])
                    self.assertEqual(instructions.call_args.kwargs['patient_id'], 101)
                else:
                    instructions.assert_not_called()

    def test_missing_invoice_view_and_request(self):
        with self.login(), patch.object(BillingModel, 'get_invoice', return_value=None):
            self.assertEqual(self.client.get('/api/billing/invoice/missing').status_code, 404)
            self.assertEqual(self.client.post('/api/billing/request', json={'invoice_id': 999}).status_code, 404)

    def test_missing_patient_id_never_loads_all_invoices(self):
        for identifier in (None, 0, -1, True):
            with patch.object(BillingModel,'get_all') as get_all, self.assertRaises(CalendarError):
                BillingModel.get_by_patient(identifier)
            get_all.assert_not_called()


class BillingAmountTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.bill = dict(id=1, ma_hoa_don='HD_TEST', phieu_kham_id=9, benh_nhan_id=101,
                         tong_tien=100, tien_bhyt=20, giam_gia=10, thanh_tien=70)
        self.line = dict(so_luong=1, don_gia=100, thanh_tien=100, loai_khoan_thu='Khám bệnh', tham_chieu_id=9)
        self.cursor.fetchone.return_value = {'benh_nhan_id': 101, 'bac_si_id': 203}
        self.cursor.fetchall.return_value = [self.line]

    def test_consistent_amount_and_invalid_totals(self):
        validate_invoice(self.cursor, self.bill, check_sources=False)
        for key, value in [('tong_tien', 101), ('tien_bhyt', 101), ('giam_gia', -1), ('thanh_tien', 71), ('thanh_tien', None)]:
            with self.subTest(key=key), self.assertRaises(CalendarError):
                validate_invoice(self.cursor, dict(self.bill, **{key:value}), check_sources=False)

    def test_empty_detail_invalid_quantity_and_line_total(self):
        for lines in ([], [dict(self.line, so_luong=0)], [dict(self.line, so_luong=1.5)],
                      [dict(self.line, thanh_tien=99)], [dict(self.line, don_gia=None)]):
            self.cursor.fetchall.return_value = lines
            with self.subTest(lines=lines), self.assertRaises(CalendarError):
                validate_invoice(self.cursor, self.bill, check_sources=False)

    def test_doctor_price_then_department_fallback_and_no_fake_default(self):
        for doctor, department, expected in ((200, 150, 200), (None, 150, 150), (0, 150, 0)):
            self.cursor.fetchone.return_value = {'gia_kham': doctor, 'gia_kham_mac_dinh': department}
            self.assertEqual(consultation_price(self.cursor, 203), Decimal(expected))
        self.cursor.fetchone.return_value = {'gia_kham': None, 'gia_kham_mac_dinh': None}
        with self.assertRaises(CalendarError):
            consultation_price(self.cursor, 203)

    def test_configured_price_mismatch_blocks_collection(self):
        self.cursor.fetchone.side_effect = [{'benh_nhan_id':101,'bac_si_id':203},
                                           {'gia_kham':200,'gia_kham_mac_dinh':150}]
        with self.assertRaises(CalendarError):
            validate_invoice(self.cursor, self.bill)

    def test_money_rejects_nonfinite_negative_and_extra_decimals(self):
        for value in (None, 'NaN', 'Infinity', -1, '0.001', True):
            with self.subTest(value=value), self.assertRaises(CalendarError):
                money(value)

    def test_numeric_reference_selects_only_identity(self):
        self.cursor.fetchall.return_value = []
        self.assertIsNone(fetch_invoice(self.cursor, '123', lock=True))
        self.assertIn('WHERE id=?', self.cursor.execute.call_args.args[0])
        self.assertNotIn(' OR ', self.cursor.execute.call_args.args[0])


class BillingTransactionTests(unittest.TestCase):
    def setUp(self):
        self.conn, self.cursor = Mock(), Mock()
        self.conn.cursor.return_value = self.cursor
        self.cursor.fetchone.return_value = {'calendar_lock_result':0}
        self.bill = dict(id=1, ma_hoa_don='HD_TEST', phieu_kham_id=9, benh_nhan_id=101,
                         trang_thai='Chưa thanh toán', thanh_tien=100)
        self.actor = dict(id=7, vai_tro='ADMIN', ho_ten='Verified cashier')
        self.db = patch('core.scheduling.open_db', return_value=self.conn)
        self.db.start()
        self.addCleanup(self.db.stop)

    def pay(self, bill, **kwargs):
        with patch('models.billing_model.fetch_invoice', return_value=bill), \
             patch('models.billing_model.validate_invoice'):
            return BillingModel.pay_invoice(1, audit_user=self.actor, **kwargs)

    def test_missing_canceled_paid_unknown_and_repeated_paid_never_write(self):
        for bill in (None, dict(self.bill,trang_thai='Đã hủy'), dict(self.bill,trang_thai='unknown'),
                     dict(self.bill,trang_thai='Đã thanh toán'), dict(self.bill,trang_thai='Đã thanh toán')):
            result = self.pay(bill)
            self.assertFalse(result[0], result)
        self.conn.commit.assert_not_called()
        self.assertTrue(all('UPDATE' not in call.args[0] and 'INSERT' not in call.args[0]
                            for call in self.cursor.execute.call_args_list))

    def test_collection_and_commit_failure_rollback(self):
        for failure in (False, True):
            self.conn.reset_mock()
            self.conn.commit.side_effect = RuntimeError('commit failure') if failure else None
            self.cursor.fetchone.side_effect = [{'calendar_lock_result':0}, {'paid_invoice_id':1}, None]
            result = self.pay(self.bill, expected_amount=100)
            self.assertEqual(result[0], not failure, result)
            sql = ' '.join(call.args[0] for call in self.cursor.execute.call_args_list)
            self.assertIn('WHERE id=? AND trang_thai=?', sql)
            if failure:
                self.conn.rollback.assert_called()

    def test_changed_amount_and_wrong_payment_method_are_rejected(self):
        self.assertFalse(self.pay(self.bill, expected_amount=99)[0])
        self.assertFalse(self.pay(self.bill, payment_method='MoMo')[0])
        self.conn.commit.assert_not_called()

    def test_drug_paid_replay_cannot_rewind_dispensing(self):
        bill = dict(self.bill,ma_hoa_don='HDT_TEST',trang_thai='Đã thanh toán',trang_thai_nhan_thuoc='Đã nhận thuốc')
        self.assertFalse(self.pay(bill)[0])
        self.assertTrue(all('UPDATE' not in call.args[0] for call in self.cursor.execute.call_args_list))

    def test_request_is_read_only_and_returns_no_payment_confirmation(self):
        for owner, valid in ((101, True), (102, False)):
            with patch('models.billing_model.get_db', return_value=self.conn), \
                 patch('models.billing_model.fetch_invoice', return_value=self.bill), \
                 patch('models.billing_model.validate_invoice'):
                result = BillingModel.payment_instructions(1, patient_id=owner)
            self.assertEqual(result[0], valid)
            if valid:
                self.assertFalse(result[1]['payment_confirmed'])
                self.assertFalse(result[1]['gateway_enabled'])
        self.conn.commit.assert_not_called()
        self.cursor.execute.assert_not_called()

    def test_canceled_paid_requests_are_rejected_without_writes(self):
        for state in ('Đã hủy','Đã thanh toán','unknown'):
            with patch('models.billing_model.get_db',return_value=self.conn), \
                 patch('models.billing_model.fetch_invoice',return_value=dict(self.bill,trang_thai=state)), \
                 patch('models.billing_model.validate_invoice') as validate:
                self.assertFalse(BillingModel.payment_instructions(1,patient_id=101)[0])
                validate.assert_not_called()
        self.cursor.execute.assert_not_called()

    def test_first_drug_collection_targets_one_order(self):
        bill = dict(self.bill,ma_hoa_don='HDT_TEST')
        order = dict(id=10,trang_thai='Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy',
                     hinh_thuc_mua='Mua tại bệnh viện')
        self.cursor.fetchall.side_effect = [[{'id':10}], []]
        self.cursor.fetchone.side_effect = [{'calendar_lock_result':0},{'paid_invoice_id':1},None]
        from models.pharmacy_model import PharmacyModel
        with patch('models.billing_model.fetch_invoice',return_value=bill), \
             patch('models.billing_model.validate_invoice'), patch('models.billing_model.check_bill'), \
             patch('models.billing_model.invoices',return_value=[bill]), \
             patch.object(PharmacyModel,'get_prescription_detail',return_value=order):
            result = BillingModel.pay_invoice(1,audit_user=self.actor)
        self.assertTrue(result[0],result)
        changes = [(call.args[0],call.args[1]) for call in self.cursor.execute.call_args_list if 'UPDATE don_thuoc' in call.args[0]]
        self.assertEqual(len(changes),1)
        self.assertIn('WHERE id = ? AND trang_thai = ?',changes[0][0])
        self.assertEqual(changes[0][1],(10,order['trang_thai']))


class BillingWebsiteTests(unittest.TestCase):
    def test_render_patient_and_staff_templates_and_javascript(self):
        import re
        import shutil
        import subprocess
        from flask import render_template
        app = create_test_app()
        bill = dict(id=1, ma_hoa_don='HD_TEST',ma_hd='HD_TEST',thoi_gian_tao=None,
                    thanh_tien=100,tong_tien=100,tien_bhyt_chi_tra=0,khoan_muc='Test',
                    trang_thai='Chưa thanh toán',trang_thai_nhan_thuoc=None)
        for template, role in [('patient/billing.html','BENHNHAN'), ('admin/billing.html','ADMIN')]:
            with app.test_request_context('/'):
                from flask import session
                session['user'] = {'id':1,'vai_tro':role}
                html = render_template(template, patient={'id':101,'ho_ten':'Test'},
                    invoices=[bill], unpaid=bill,
                    billing_stats=dict(tong_tien=100,tien_bhyt=0,da_thanh_toan=0,chua_thanh_toan=100,so_hoa_don_cho=1,tong_so_hoa_don=1),
                    stats=dict(tong_doanh_thu=0,tong_bhyt=0,thuc_thu=0,so_hoa_don_cho=1,tong_so_hoa_don=1))
            self.assertNotIn('api.qrserver.com', html)
            self.assertNotIn('1903686868', html)
            if role == 'BENHNHAN':
                self.assertNotIn('/api/billing/pay', html)
                self.assertIn('/api/billing/request', html)
            node = shutil.which('node')
            if not node:
                self.skipTest('Node unavailable for JavaScript syntax validation')
            for attributes, body in re.findall(r'<script([^>]*)>(.*?)</script>', html, re.S):
                if 'application/json' in attributes or 'src=' in attributes or not body.strip():
                    continue
                result = subprocess.run([node,'--check'],input=body,text=True,encoding='utf-8',capture_output=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
