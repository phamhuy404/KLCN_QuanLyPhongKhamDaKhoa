"""Isolated unit tests: no database connections or payment/notification delivery."""
import json
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from core.pharmacy_safety import (quantities, validate_items, check_bill, guarded,
                                  APPROVED, HOSPITAL, PAID, DISPENSED)
from core.scheduling import CalendarError
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel


class PharmacySafetyTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.conn = Mock()
        self.conn.cursor.return_value = self.cursor
        self.cursor.fetchone.return_value = {'calendar_lock_result': 0}
        self.patch = patch('core.scheduling.open_db', return_value=self.conn)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_positive_integer_quantities_and_duplicate_totals(self):
        for qty in (None, 0, -1, 1.2, True, '1.0', ''):
            with self.subTest(qty=qty), self.assertRaises(CalendarError):
                quantities([{'thuoc_id': 1, 'so_luong': qty}])
        self.assertEqual(quantities([{'thuoc_id': 1, 'so_luong': 2}, {'thuoc_id': 1, 'so_luong': 3}]), {1: 5})

    def test_combined_shortage_and_inactive_drug(self):
        items = [{'thuoc_id': 1, 'so_luong': 3}] * 2
        for row in (None, {'trang_thai': 0, 'so_luong_ton': 20},
                    {'trang_thai': None, 'so_luong_ton': 20}, {'trang_thai': 1, 'so_luong_ton': 5}):
            self.cursor.fetchone.return_value = row
            with self.subTest(row=row), self.assertRaises(CalendarError):
                validate_items(self.cursor, items, stock=True)

    def test_invoice_quantity_and_unit_price_mismatch(self):
        prescription = {'benh_nhan_id': 7, 'items': [{'thuoc_id': 1, 'so_luong': 2}]}
        bill = {'id': 8, 'benh_nhan_id': 7, 'tong_tien': 20}
        self.cursor.fetchall.return_value = [{'tham_chieu_id': 1, 'so_luong': 2, 'don_gia': 10, 'thanh_tien': 20}]
        check_bill(self.cursor, bill, prescription)
        for field, value in [('don_gia', 0), ('so_luong', 3), ('thanh_tien', 21)]:
            self.cursor.fetchall.return_value = [{'tham_chieu_id': 1, 'so_luong': 2, 'don_gia': 10, 'thanh_tien': 20}]
            self.cursor.fetchall.return_value[0][field] = value
            with self.subTest(field=field), self.assertRaises(CalendarError):
                check_bill(self.cursor, bill, prescription)

    def guard_case(self, method, state, bills, **kwargs):
        dt = {'id': 1, 'phieu_kham_id': 9, 'bac_si_id': 2, 'benh_nhan_id': 7,
              'trang_thai': state, 'hinh_thuc_mua': HOSPITAL,
              'items': [{'thuoc_id': 1, 'so_luong': 2}]}
        with patch.object(PharmacyModel, 'get_prescription_detail', return_value=dt), \
             patch('core.pharmacy_safety.invoices', return_value=bills):
            return getattr(PharmacyModel, method)(1, **kwargs)

    def test_paid_edit_cancel_reject_and_purchase_change_are_locked(self):
        for method, kwargs in [('update_prescription', {'medicines': [{'thuoc_id': 1, 'so_luong': 2}]}),
                               ('cancel_or_adjust_prescription', {'reason': 'test'}),
                               ('reject_prescription', {}), ('choose_medicine_purchase_option', {})]:
            with self.subTest(method=method):
                result = self.guard_case(method, 'Chờ duyệt', [{'trang_thai': PAID}], **kwargs)
                self.assertFalse(result[0], result)
                self.conn.commit.assert_not_called()

    def test_repeated_dispense_cancel_and_stock_restore_never_write(self):
        for status in DISPENSED | {'Đã hủy'}:
            for method, kwargs in [('dispense_prescription', {}),
                                   ('cancel_or_adjust_prescription', {'reason': 'return', 'restore_stock': True})]:
                for _ in range(2):
                    self.assertFalse(self.guard_case(method, status, [], **kwargs)[0])
        self.conn.commit.assert_not_called()
        self.assertTrue(all('UPDATE' not in str(call) for call in self.cursor.execute.call_args_list))

    def test_invoice_blocks_edit_and_other_doctor_is_denied(self):
        self.assertFalse(self.guard_case('update_prescription', 'Chờ duyệt', [{'trang_thai': 'Chưa thanh toán'}], medicines=[{'thuoc_id': 1, 'so_luong': 2}])[0])
        self.assertFalse(self.guard_case('update_prescription', 'Chờ duyệt', [], medicines=[{'thuoc_id': 1, 'so_luong': 2}], audit_user={'vai_tro': 'BACSI', 'bac_si_id': 99})[0])

    def test_wrong_transition_approval_and_dispense_are_denied(self):
        for state in ('Mua ngoài', 'Chờ bệnh nhân xác nhận mua', 'unknown', None):
            for method in ('approve_prescription', 'dispense_prescription'):
                self.assertFalse(self.guard_case(method, state, [dict(trang_thai=PAID)])[0])

    def test_edit_unbilled_order_and_cancel_unpaid_invoice(self):
        dt = {'id': 1, 'phieu_kham_id': 9, 'ma_don_thuoc': 'DT_TEST',
              'bac_si_id': 2, 'items': [], 'trang_thai': 'Chờ bệnh nhân xác nhận mua'}
        self.cursor.fetchone.side_effect = [{'calendar_lock_result': 0},
            {'id': 1, 'ten_thuoc': 'Drug', 'so_luong_ton': 10, 'trang_thai': 1}]
        with patch.object(PharmacyModel, 'get_prescription_detail', return_value=dt), \
             patch('core.pharmacy_safety.invoices', return_value=[]), \
             patch('core.pharmacy_safety.validate_items'), patch('core.audit.AuditLogger.log', return_value=True):
            result = PharmacyModel.update_prescription(1, [{'thuoc_id': 1, 'so_luong': 2}])
        self.assertTrue(result[0], result)
        self.conn.commit.assert_called_once()
        self.conn.reset_mock()
        self.cursor.fetchone.side_effect = [{'calendar_lock_result': 0}]
        bill = {'id': 8, 'trang_thai': 'Chưa thanh toán'}
        with patch.object(PharmacyModel, 'get_prescription_detail', return_value=dt), \
             patch('core.pharmacy_safety.invoices', return_value=[bill]), \
             patch('core.audit.AuditLogger.log', return_value=True):
            result = PharmacyModel.cancel_or_adjust_prescription(1, 'test cancel')
        self.assertTrue(result[0], result)
        self.conn.commit.assert_called_once()
        sql = ' '.join(call.args[0] for call in self.cursor.execute.call_args_list)
        self.assertIn('UPDATE hoa_don', sql)
        self.assertIn('UPDATE don_thuoc', sql)

    def test_commit_failure_rolls_back_and_never_reports_success(self):
        @guarded
        def update_prescription(prescription_id, medicines):
            return True, 'saved'
        self.conn.commit.side_effect = RuntimeError('commit failed')
        with patch.object(PharmacyModel, 'get_prescription_detail', return_value={'id': 1, 'trang_thai': 'Chờ duyệt'}), \
             patch('core.pharmacy_safety.invoices', return_value=[]), \
             patch('core.pharmacy_safety.validate_items'):
            result = update_prescription(1, [{'thuoc_id': 1, 'so_luong': 2}])
        self.assertFalse(result[0])
        self.conn.rollback.assert_called()

    def test_receive_idempotency_and_conflicting_retry(self):
        receipt = str(uuid4())
        self.cursor.fetchone.side_effect = [{'calendar_lock_result': 0},
            {'row_id': 1, 'after_json': json.dumps({'delta': 3})}]
        self.assertTrue(PharmacyModel.receive_stock(1, 3, 'receipt', receipt)[0])
        self.cursor.fetchone.side_effect = [{'calendar_lock_result': 0},
            {'row_id': 1, 'after_json': json.dumps({'delta': 3})}]
        self.assertFalse(PharmacyModel.receive_stock(1, 4, 'receipt', receipt)[0])

    def test_receive_writes_stock_and_journal_in_one_transaction(self):
        self.cursor.fetchone.side_effect = [{'calendar_lock_result': 0}, None, {'old_stock': 5, 'new_stock': 8}]
        self.assertTrue(PharmacyModel.receive_stock(1, 3, 'receipt', str(uuid4()))[0])
        statements = ' '.join(call.args[0] for call in self.cursor.execute.call_args_list)
        self.assertIn('OUTPUT deleted.so_luong_ton', statements)
        self.assertIn('INSERT INTO audit_log', statements)
        self.conn.commit.assert_called_once()

    def test_missing_or_canceled_or_paid_invoice_cannot_be_paid(self):
        for row in (None, {'trang_thai': 'Đã hủy'}, {'trang_thai': PAID}):
            self.cursor.fetchone.side_effect = [{'calendar_lock_result': 0}]
            with patch('models.billing_model.fetch_invoice', return_value=row):
                self.assertFalse(BillingModel.pay_invoice(8, audit_user={'id':7,'vai_tro':'ADMIN'})[0])
        self.conn.commit.assert_not_called()

    def test_dispense_writes_conditional_stock_and_rollback_on_shortage(self):
        dt = {'id': 1, 'phieu_kham_id': 9, 'ma_don_thuoc': 'DT_TEST',
              'trang_thai': 'Chờ nhận thuốc', 'hinh_thuc_mua': HOSPITAL,
              'items': [{'thuoc_id': 1, 'so_luong': 3}]}
        bill = {'id': 8, 'ma_hoa_don': 'HDT_TEST', 'trang_thai': PAID}
        for applied in (True, False):
            self.conn.reset_mock()
            self.cursor.fetchone.side_effect = [
                {'calendar_lock_result': 0}, bill,
                {'ten_thuoc': 'Drug', 'so_luong_ton': 10, 'trang_thai': 1},
                {'old_stock': 10, 'new_stock': 7} if applied else None]
            with patch.object(PharmacyModel, 'get_prescription_detail', return_value=dt), \
                 patch('core.pharmacy_safety.invoices', return_value=[bill]), \
                 patch('core.pharmacy_safety.validate_items'), patch('core.pharmacy_safety.check_bill'), \
                 patch('core.audit.AuditLogger.log', return_value=True):
                result = PharmacyModel.dispense_prescription(1)
            self.assertEqual(result[0], applied, result)
            sql = ' '.join(call.args[0] for call in self.cursor.execute.call_args_list)
            self.assertIn('so_luong_ton>=?', sql)
            if applied:
                self.conn.commit.assert_called_once()
                self.assertIn('INSERT INTO audit_log', sql)
            else:
                self.conn.commit.assert_not_called()
                self.conn.rollback.assert_called()

    def test_stock_api_requires_identity_and_role(self):
        from app import create_test_app
        from models.user_model import UserModel
        app = create_test_app()
        client = app.test_client()
        payload = dict(medicine_id=1, quantity=3, reason='test', receipt_id=str(uuid4()))
        self.assertEqual(client.post('/api/pharmacy/receive-stock', json=payload).status_code, 401)
        for role, expected in [('BENHNHAN', 403), ('BACSI', 403), ('DUOCSI', 200), ('ADMIN', 200)]:
            with client.session_transaction() as session:
                session.update(logged_in=True, user={'id': 7})
            with patch.object(UserModel, 'get_session_user', return_value={'id': 7, 'vai_tro': role}), \
                 patch.object(PharmacyModel, 'receive_stock', return_value=(True, 'received')) as receive:
                response = client.post('/api/pharmacy/receive-stock', json=payload)
                self.assertEqual(response.status_code, expected)
                self.assertEqual(receive.call_count, int(expected == 200))

    def test_pharmacy_page_renders_and_javascript_parses_without_database(self):
        import re
        import shutil
        import subprocess
        from app import create_test_app
        from models.user_model import UserModel
        from models.medical_record_model import MedicalRecordModel
        app = create_test_app()
        client = app.test_client()
        with client.session_transaction() as session:
            session.update(logged_in=True, user={'id': 7})
        with patch.object(UserModel, 'get_session_user', return_value={'id': 7, 'vai_tro': 'ADMIN', 'ho_ten': 'Test'}), \
             patch.object(PharmacyModel, 'get_all_medicines', return_value=[]), \
             patch.object(MedicalRecordModel, 'get_all_prescriptions', return_value=[]):
            response = client.get('/admin/pharmacy')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('receiveExistingStock', html)
        self.assertIn('id: m.id', html)
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is unavailable for JavaScript syntax validation')
        for attributes, body in re.findall(r'<script([^>]*)>(.*?)</script>', html, re.S):
            if 'application/json' in attributes or 'src=' in attributes or not body.strip():
                continue
            result = subprocess.run([node, '--check'], input=body, capture_output=True, text=True, encoding='utf-8', timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
