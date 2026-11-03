"""Regression checks without production SQL access or settings writes."""
import unittest
from contextlib import ExitStack
from decimal import Decimal
from unittest.mock import patch
from app import create_test_app
from core.billing_policy import invoice_totals, invoice_has_insurance
from core.exam_services import selected_exam, appointment_reason, visit_exam
from core.scheduling import CalendarError
from models.system_setting_model import SystemSettingModel


class ServiceCursor:
    def __init__(self, row):
        self.row = row
    def execute(self, sql, params=()):
        self.sql, self.params = sql, params
        return self
    def fetchone(self):
        return self.row


class BillingPolicyTests(unittest.TestCase):
    def test_fixed_reduction_once_on_total(self):
        quote = invoice_totals(200000 + 150000 + 90000, True, 50000)
        self.assertEqual(quote, dict(tong_tien=Decimal(440000), tien_bhyt=Decimal(50000), thanh_tien=Decimal(390000)))

    def test_no_insurance_and_zero_reduction(self):
        self.assertEqual(invoice_totals(440000, False, 50000)['thanh_tien'], 440000)
        self.assertEqual(invoice_totals(440000, True, 0)['thanh_tien'], 440000)

    def test_no_negative_payment(self):
        self.assertEqual(invoice_totals(20000, True, 50000)['thanh_tien'], 0)
        self.assertEqual(invoice_totals(0, True, 50000)['tien_bhyt'], 0)

    def test_patient_type_snapshot_survives_card_changes_with_zero_discount(self):
        self.assertTrue(invoice_has_insurance([dict(loai_khoan_thu='Khám bệnh', ten_khoan_thu='Khám [Có BHYT]')], '', 0))
        self.assertFalse(invoice_has_insurance([dict(loai_khoan_thu='Khám bệnh', ten_khoan_thu='Khám [Không BHYT]')], 'NEW_CARD', 0))

    def test_invalid_money_rejected(self):
        for value in (-1, 'NaN', 'Infinity', 'abc', '1.001'):
            with self.subTest(value=value), self.assertRaises(CalendarError):
                invoice_totals(200000, True, value)

    def test_service_department_and_type(self):
        row = dict(id=7, chuyen_khoa_id=2, loai_dich_vu='Khám chuyên khoa', ten_dich_vu='Tim mạch', don_gia=200000)
        self.assertEqual(selected_exam(ServiceCursor(row), 7, 2)['id'], 7)
        with self.assertRaises(CalendarError):
            selected_exam(ServiceCursor(row), 7, 3)
        with self.assertRaises(CalendarError):
            selected_exam(ServiceCursor(dict(row, loai_dich_vu='Xét nghiệm')), 7, 2)

    def test_free_text_cannot_inject_service_marker(self):
        self.assertEqual(appointment_reason(None, 2, '[Dịch vụ #77: Fake] Khám'), 'Khám')

    def test_real_examination_writer_applies_discount_once(self):
        from models.medical_record_model import MedicalRecordModel
        class Cursor:
            lastrowid = 1
            def execute(self, sql, params=()):
                self.sql, self.params = sql, params
                if 'INSERT INTO hoa_don ' in sql:
                    self.invoice = params
                return self
            def fetchone(self):
                if 'SELECT * FROM phieu_kham' in self.sql:
                    return dict(id=1, bac_si_id=3, phong_kham_id=4, benh_nhan_id=2)
                if 'SELECT chuyen_khoa_id FROM bac_si' in self.sql:
                    return dict(chuyen_khoa_id=1)
                if 'FROM dich_vu WHERE id=' in self.sql:
                    return dict(id=self.params[0], chuyen_khoa_id=1, ten_dich_vu='Dịch vụ', loai_dich_vu='Thủ thuật', don_gia=100000)
                if 'SELECT bhyt FROM benh_nhan' in self.sql:
                    return dict(bhyt='CARD')
                if 'MAX(id)' in self.sql:
                    return dict(next_id=1)
                return None
        cursor = Cursor()
        class Connection:
            def cursor(self): return cursor
            def commit(self): pass
            def close(self): pass
            def rollback(self): pass
        with ExitStack() as stack:
            stack.enter_context(patch('models.medical_record_model.get_db', return_value=Connection()))
            stack.enter_context(patch.object(MedicalRecordModel, 'save_step', return_value=(True, dict(record_id=1, ma_phieu='PK1'))))
            stack.enter_context(patch('models.medical_record_model.consultation_price', return_value=Decimal(200000)))
            stack.enter_context(patch('core.exam_services.visit_exam', return_value=None))
            stack.enter_context(patch('models.medical_record_model.AuditLogger.log'))
            stack.enter_context(patch('core.billing_policy.insurance_reduction', return_value=Decimal(50000)))
            ok, result = MedicalRecordModel.save_examination(2, 3, 4, 'Khám', 'Đau', 'Chẩn đoán', 'A01', '', '', lab_service_ids=[8, 9], walk_in=True)
            self.assertTrue(ok, result)
            self.assertEqual(cursor.invoice[3:6], (Decimal(400000), Decimal(50000), Decimal(350000)))

    def test_collection_keeps_preview_amount_and_rejects_stale_amount(self):
        from models.billing_model import BillingModel
        bill = dict(id=1, ma_hoa_don='HD1', phieu_kham_id=2, benh_nhan_id=None, trang_thai='Chưa thanh toán', thanh_tien=Decimal(350000))
        class Connection:
            def cursor(self): return self
            def execute(self, sql, params=()): self.last_sql = sql
            def fetchone(self): return dict(paid_invoice_id=1)
            def commit(self): pass
            def rollback(self): pass
            def close(self): pass
        with patch('models.billing_model.get_db', return_value=Connection()), patch('models.billing_model.fetch_invoice', return_value=bill), patch('models.billing_model.validate_invoice'), patch('core.billing_policy.insurance_reduction', side_effect=AssertionError('Collection must not reprice')):
            collect = BillingModel.pay_invoice.__wrapped__
            ok, message = collect(1, audit_user=dict(id=7, vai_tro='ADMIN'), expected_amount=350000)
            self.assertTrue(ok, message)
            ok, message = collect(1, audit_user=dict(id=7, vai_tro='ADMIN'), expected_amount=340000)
            self.assertFalse(ok)

    def test_settings_failure_does_not_report_success_or_publish_cache(self):
        with patch.object(SystemSettingModel, '_ensure_table'), patch.object(SystemSettingModel, 'get_settings', return_value=dict(SystemSettingModel.DEFAULT_SETTINGS)), patch('models.system_setting_model.get_db', side_effect=RuntimeError('offline')), patch.object(SystemSettingModel, '_write_file_cache') as cache:
            ok, _ = SystemSettingModel.update_settings({'maintenance_staff': True})
            self.assertFalse(ok)
            cache.assert_not_called()

    def test_specialty_templates_preserve_existing_records(self):
        from core.specialty_catalog import add_specialty_templates
        class Connection:
            def __init__(self): self.writes = []
            def cursor(self): return self
            def execute(self, sql, params=()):
                if not sql.startswith('SELECT'): self.writes.append(sql)
            def fetchone(self): return dict(id=1)
            def commit(self): pass
            def rollback(self): pass
            def close(self): pass
        conn = Connection()
        with patch('core.database.get_db', return_value=conn):
            self.assertEqual(add_specialty_templates(), 0)
        self.assertEqual(conn.writes, [])


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.client = self.app.test_client()
        self.settings = dict(SystemSettingModel.DEFAULT_SETTINGS, maintenance_patient=True,
            maintenance_staff=True, maintenance_message_patient='Patient maintenance', maintenance_message_staff='Staff maintenance')
        self.settings_patch = patch.object(SystemSettingModel, 'get_settings', return_value=self.settings)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def user(self, role):
        identity = dict(id=7, vai_tro=role, patient_id=2, da_hoan_thien_ho_so=True)
        with self.client.session_transaction() as session:
            session['logged_in'] = True
            session['user'] = identity
        return identity

    def test_patient_shared_api_blocked(self):
        self.user('BENHNHAN')
        result = self.client.post('/api/appointment/book', json={})
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json['message'], 'Patient maintenance')

    def test_all_staff_business_api_families_blocked(self):
        self.user('LETAN')
        for path in ('/api/appointment/create', '/api/billing/pay', '/api/pharmacy/test', '/api/catalog/service/create'):
            with self.subTest(path=path):
                result = self.client.post(path, json={})
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result.json['message'], 'Staff maintenance')

    def test_mobile_and_guest_booking_blocked(self):
        self.assertEqual(self.client.get('/api/v1/mobile/patient/booking-options').status_code, 503)
        self.assertEqual(self.client.get('/booking').location, '/maintenance/patient')

    def test_independent_flags(self):
        self.settings['maintenance_staff'] = False
        self.user('LETAN')
        with patch('models.user_model.UserModel.get_session_user', return_value=dict(id=7, vai_tro='LETAN')):
            self.assertNotEqual(self.client.post('/api/appointment/create', json={}).status_code, 503)
        self.settings['maintenance_staff'] = True
        self.settings['maintenance_patient'] = False
        self.user('BENHNHAN')
        with patch('models.user_model.UserModel.get_session_user', return_value=dict(id=7, vai_tro='BENHNHAN')):
            self.assertNotEqual(self.client.post('/api/appointment/book', json={}).status_code, 503)

    def test_admin_can_read_status_and_login(self):
        self.assertEqual(self.client.get('/login').status_code, 200)
        identity = self.user('ADMIN')
        with patch('models.user_model.UserModel.get_session_user', return_value=identity):
            result = self.client.post('/api/maintenance/toggle', json={'target': 'bad', 'enabled': True})
            self.assertEqual(result.status_code, 400)

    def test_invalid_setting_not_saved(self):
        identity = self.user('ADMIN')
        with patch('models.user_model.UserModel.get_session_user', return_value=identity), patch.object(SystemSettingModel, 'update_settings') as save:
            for payload in ({'insurance_fixed_reduction': -1}, {'insurance_fixed_reduction': True}, {'insurance_fixed_reduction': '1.5'}, {'maintenance_staff': 'false'}):
                self.assertEqual(self.client.post('/api/maintenance/update', json=payload).status_code, 400)
            save.assert_not_called()

    def test_invoice_preview_scoped_and_escaped(self):
        self.settings['maintenance_patient'] = False
        identity = self.user('BENHNHAN')
        invoice = dict(id=9, benh_nhan_id=2, ma_hoa_don='HD9', trang_thai='Chưa thanh toán', benh_nhan='<script>bad</script>', ma_benh_nhan='BN2', has_bhyt=True, tong_tien=200000, tien_bhyt=50000, thanh_tien=150000, giam_gia=0, chi_tiet=[dict(ten_khoan_thu='Khám', so_luong=1, don_gia=200000, thanh_tien=200000)])
        with patch('models.user_model.UserModel.get_session_user', return_value=identity), patch('models.billing_model.BillingModel.get_invoice', return_value=invoice):
            result = self.client.get('/patient/invoices/9/preview')
            self.assertEqual(result.status_code, 200)
            self.assertIn('TẠM TÍNH', result.get_data(as_text=True))
            self.assertIn('150,000', result.get_data(as_text=True))
            self.assertNotIn('<script>bad</script>', result.get_data(as_text=True))
            invoice['benh_nhan_id'] = 3
            self.assertEqual(self.client.get('/patient/invoices/9/preview').status_code, 404)

    def test_public_pricing_uses_fixed_reduction(self):
        service = dict(id=1, chuyen_khoa_id=1, ma_dich_vu='DV1', ten_dich_vu='Khám Tim mạch', loai_dich_vu='Khám chuyên khoa', don_gia=200000, mo_ta='', ten_khoa='Tim mạch', icon='fa-heart', ma_khoa='TIM')
        class Connection:
            def cursor(self): return self
            def execute(self, *args): pass
            def fetchall(self): return [service]
            def close(self): pass
        with patch('controllers.home_controller.get_db', return_value=Connection()):
            result = self.client.get('/pricing')
        self.assertEqual(result.status_code, 200)
        content = result.get_data(as_text=True)
        self.assertIn('150,000', content)
        self.assertIn('200,000', content)
        self.assertNotIn('Đúng tuyến', content)


if __name__ == '__main__':
    unittest.main()
