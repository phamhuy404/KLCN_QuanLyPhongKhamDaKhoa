"""MSSQL integration only; requires separately confirmed disposable test database.
No SQLite, SQL translation or mocked application lock in integration paths.
"""
import importlib
import json
import os
import re
import smtplib
import threading
import unittest
import uuid
from unittest.mock import patch
from urllib.request import build_opener, ProxyHandler, HTTPCookieProcessor, Request
from urllib.parse import urlencode
from http.cookiejar import CookieJar

import pyodbc


from core.mssql_test_database import MssqlTestSettings, TestDatabaseNotConfigured
from tests.mssql_support import fixture_connection, reset_fixture_tables, traced_connection


class SecurityAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.mssql_settings = MssqlTestSettings.from_environment()
        except TestDatabaseNotConfigured as exc:
            raise unittest.SkipTest(str(exc))
        if os.environ.get('CLINIC_MSSQL_TEST_ALLOW_FIXTURES') != 'rebuild-only-disposable-fixtures':
            raise unittest.SkipTest('MSSQL fixture DDL/DML has not been explicitly authorized')
        cls.start_test_thread = staticmethod(threading.Thread.start)
        cls.guards = [
            patch.object(smtplib, 'SMTP', side_effect=AssertionError('SMTP forbidden')),
            patch.object(smtplib, 'SMTP_SSL', side_effect=AssertionError('SMTP forbidden')),
            patch.object(threading.Thread, 'start', side_effect=AssertionError('Worker forbidden')),
        ]
        cls.io_mocks = [guard.start() for guard in cls.guards]
        for guard in cls.guards:
            cls.addClassCleanup(guard.stop)
        cls.module = importlib.import_module('app')
        cls.db_module = importlib.import_module('core.database')
        cls.security = importlib.import_module('core.security')
        cls.users = importlib.import_module('models.user_model').UserModel
        cls.patients = importlib.import_module('models.patient_model').PatientModel
        cls.password_hash = cls.security.hash_password('IsolatedPassword123!')

    def setUp(self):
        for mock in self.io_mocks:
            mock.reset_mock()
        self.keeper = fixture_connection(self.mssql_settings)
        self.addCleanup(self.keeper.close)
        reset_fixture_tables(self.keeper)
        self.keeper.executescript('''
            CREATE TABLE vai_tro(id INT PRIMARY KEY, ma_vai_tro NVARCHAR(MAX), ten_vai_tro NVARCHAR(MAX));
            CREATE TABLE tai_khoan(id INT IDENTITY(1,1) PRIMARY KEY, username NVARCHAR(MAX), password NVARCHAR(MAX),
                sdt NVARCHAR(MAX), email NVARCHAR(MAX), vai_tro_id INT, trang_thai INT DEFAULT 1,
                da_hoan_thien_ho_so INT DEFAULT 1, yeu_cau_doi_mat_khau INT DEFAULT 0,
                lan_dang_nhap_cuoi DATETIME2(0), ngay_tao DATETIME2(0));
            CREATE TABLE benh_nhan(id INT IDENTITY(1,1) PRIMARY KEY, tai_khoan_id INT,
                ma_benh_nhan NVARCHAR(MAX), ho_ten NVARCHAR(MAX), ngay_sinh DATE, gioi_tinh NVARCHAR(MAX), sdt NVARCHAR(MAX),
                email NVARCHAR(MAX), cccd NVARCHAR(MAX), bhyt NVARCHAR(MAX), dia_chi NVARCHAR(MAX), nhom_mau NVARCHAR(MAX),
                ghi_chu_nhom_mau NVARCHAR(MAX), di_ung NVARCHAR(MAX), tien_su_benh NVARCHAR(MAX),
                nguoi_than_ho_ten NVARCHAR(MAX), nguoi_than_sdt NVARCHAR(MAX), nguoi_than_quan_he NVARCHAR(MAX));
            CREATE TABLE nhan_vien(id INT PRIMARY KEY, tai_khoan_id INT,
                ho_ten NVARCHAR(MAX), trang_thai INT DEFAULT 1, chuc_vu NVARCHAR(MAX),
                ma_nhan_vien NVARCHAR(MAX), sdt NVARCHAR(MAX), email NVARCHAR(MAX));
            CREATE TABLE bac_si(id INT PRIMARY KEY, nhan_vien_id INT,
                chuyen_khoa_id INT, hoc_vi NVARCHAR(MAX));
            CREATE TABLE chi_so_sinh_ton(benh_nhan_id INT, mach NVARCHAR(MAX), nhiet_do NVARCHAR(MAX),
                huyet_ap NVARCHAR(MAX), spo2 NVARCHAR(MAX), nhip_tho NVARCHAR(MAX), chieu_cao NVARCHAR(MAX), can_nang NVARCHAR(MAX), bmi NVARCHAR(MAX));
            CREATE TABLE lich_hen(id INT, benh_nhan_id INT, chuyen_khoa_id INT);
            CREATE TABLE phieu_kham(id INT, benh_nhan_id INT,
                bac_si_id INT, phong_kham_id INT);
            CREATE TABLE phong_kham(id INT, chuyen_khoa_id INT);
        ''')
        roles = ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV', 'BENHNHAN', 'UNKNOWN']
        self.keeper.executemany('INSERT INTO vai_tro VALUES (?, ?, ?)',
                                [(i, role, role) for i, role in enumerate(roles, 1)])
        account_roles = {1: 6, 2: 6, 3: 3, 4: 4, 5: 5, 6: 2, 7: 1,
                         8: 6, 9: 6, 10: 3, 11: 4, 12: 7, 13: 5, 14: 6}
        self.keeper.execute('SET IDENTITY_INSERT tai_khoan ON')
        self.keeper.executemany(
            'INSERT INTO tai_khoan(id,username,vai_tro_id) VALUES (?,?,?)',
            [(key, 'fixture_' + str(key), role) for key, role in account_roles.items()])
        self.keeper.execute('SET IDENTITY_INSERT tai_khoan OFF')
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=0 WHERE id=8')
        self.keeper.execute('UPDATE tai_khoan SET password=?', (self.password_hash,))
        self.keeper.execute('UPDATE tai_khoan SET yeu_cau_doi_mat_khau=1 WHERE id=14')
        self.keeper.execute('SET IDENTITY_INSERT benh_nhan ON')
        self.keeper.executemany(
            'INSERT INTO benh_nhan(id,tai_khoan_id,ma_benh_nhan,ho_ten) VALUES (?,?,?,?)',
            [(101, 1, 'TEST101', 'Owner'), (102, 2, 'TEST102', 'Other'),
             (108, 8, 'TEST108', 'Locked'), (114, 14, 'TEST114', 'Reset')])
        self.keeper.execute('SET IDENTITY_INSERT benh_nhan OFF')
        self.keeper.executemany(
            'INSERT INTO nhan_vien(id,tai_khoan_id,ho_ten) VALUES (?,?,?)',
            [(303, 3, 'Doctor'), (304, 4, 'Pharmacy'), (305, 5, 'Lab'),
             (306, 6, 'Reception'), (307, 7, 'Admin'), (310, 10, 'No doctor'),
             (311, 11, 'Inactive staff')])
        self.keeper.execute('UPDATE nhan_vien SET trang_thai=0 WHERE id=311')
        self.keeper.execute('INSERT INTO bac_si VALUES (203,303,10,NULL)')
        self.keeper.executemany('INSERT INTO lich_hen VALUES (?,?,?)', [(1, 101, 10), (2, 102, 20)])
        self.keeper.commit()
        self.statements = []
        self.app = self.module.create_test_app({'SECRET_KEY': 'isolated-security-session-key',
                                               'DATABASE_CONNECTION_FACTORY': self.connection})
        self.client = self.app.test_client()

    def connection(self):
        return traced_connection(self.mssql_settings,self.statements)

    def login(self, account_id=1, **stale):
        with self.client.session_transaction() as session:
            session.clear()
            session['logged_in'] = True
            session['user'] = {'id': account_id, 'vai_tro': 'ADMIN', 'patient_id': 102, **stale}

    def assert_no_writes(self):
        self.assertFalse([sql for sql in self.statements if sql.lstrip().upper().startswith(
            ('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP'))])

    def tearDown(self):
        for mock in self.io_mocks:
            mock.assert_not_called()

    def test_anonymous_all_sensitive_paths(self):
        paths = ['/api/appointment/book', '/api/patient/update-profile',
                 '/api/prescription/choose-buying-option', '/api/patient/update']
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.post(path, json={}).status_code, 401)
        for path in ['/api/emr/detail/1', '/api/prescription/detail/1',
                     '/api/appointment/1', '/api/lab/result/view/1',
                     '/api/patient/prescriptions', '/api/lab/orders']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get('/patient/profile').status_code, 302)
        self.assertEqual(self.client.get('/admin/patients').status_code, 302)
        self.assert_no_writes()

    def test_locked_deleted_missing_profile_or_unknown_role_denied(self):
        for account_id in (8, 9, 10, 11, 12, 13, 999):
            for path in ('/api/appointment/book', '/api/patient/update-profile',
                         '/api/prescription/choose-buying-option'):
                with self.subTest(account=account_id, path=path):
                    self.login(account_id)
                    response = self.client.post(path, json={})
                    self.assertEqual(response.status_code, 401)
                    with self.client.session_transaction() as session:
                        self.assertNotIn('user', session)
        self.assert_no_writes()

    def test_missing_account_identifier_denied(self):
        for value in (None, '', True, -1, 'bad'):
            self.login(value)
            self.assertEqual(self.client.post('/api/patient/update-profile', json={}).status_code, 401)

    def test_booking_owner_uses_live_identity_and_rejects_other_patient(self):
        from models.appointment_model import AppointmentModel
        self.login(1, patient_id=102, vai_tro='ADMIN')
        data = {'ngay_hen': '2030-01-01', 'gio_hen': '09:00', 'chuyen_khoa_id': 10}
        with patch.object(AppointmentModel, 'create', return_value=(True, 'isolated')) as create:
            self.assertEqual(self.client.post('/api/appointment/book', json=data).status_code, 200)
            self.assertEqual(create.call_args.args[0], 101)
            create.reset_mock()
            for alias in ('patient_id', 'benh_nhan_id'):
                self.assertEqual(self.client.post('/api/appointment/book', json={**data, alias: 102}).status_code, 403)
            create.assert_not_called()
        self.assert_no_writes()

    def test_booking_wrong_staff_role_denied(self):
        from models.appointment_model import AppointmentModel
        for account_id in (4, 5):
            self.login(account_id)
            with patch.object(AppointmentModel, 'create') as create:
                self.assertEqual(self.client.post('/api/appointment/book', json={'patient_id': 101}).status_code, 403)
                create.assert_not_called()

    def test_reception_booking_explicit_existing_patient_required(self):
        from models.appointment_model import AppointmentModel
        self.login(6)
        with patch.object(AppointmentModel, 'create', return_value=(True, 'isolated')) as create:
            payload = {'ngay_hen': '2030-01-01', 'gio_hen': '09:00'}
            self.assertEqual(self.client.post('/api/appointment/book', json=payload).status_code, 400)
            self.assertEqual(self.client.post('/api/appointment/book', json={**payload, 'patient_id': 999}).status_code, 404)
            create.assert_not_called()
            self.assertEqual(self.client.post('/api/appointment/book', json={**payload, 'patient_id': 101}).status_code, 200)
            self.assertEqual(create.call_args.args[0], 101)

    def test_profile_update_real_sql_changes_only_owner(self):
        self.login(1, patient_id=102)
        response = self.client.post('/api/patient/update-profile', json={'email': 'owner@example.invalid'})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=101').fetchone()[0], 'owner@example.invalid')
        self.assertIsNone(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=102').fetchone()[0])
        self.assertEqual(self.keeper.execute('SELECT email FROM tai_khoan WHERE id=1').fetchone()[0], 'owner@example.invalid')

    def test_real_http_login_profile_update_and_database_observation(self):
        from werkzeug.serving import make_server
        server = make_server('127.0.0.1', 0, self.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        # Start only this test-owned HTTP thread; application thread guard stays active.
        self.start_test_thread(thread)
        try:
            http = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
            base = 'http://127.0.0.1:' + str(server.server_port)
            with http.open(base + '/login', timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b'<form', response.read())
            # Prevent following the successful login redirect into unrelated dashboard work.
            from urllib.request import HTTPRedirectHandler
            from urllib.error import HTTPError
            class NoRedirect(HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None
            cookies = CookieJar()
            http = build_opener(ProxyHandler({}), HTTPCookieProcessor(cookies), NoRedirect())
            body = urlencode({'username': 'fixture_1', 'password': 'IsolatedPassword123!'}).encode()
            with self.assertRaises(HTTPError) as redirect:
                http.open(base + '/login', data=body, timeout=5)
            self.assertEqual(redirect.exception.code, 302)
            self.assertEqual(redirect.exception.headers['Location'], '/patient/dashboard')
            redirect.exception.close()
            payload = json.dumps({'email': 'http-owner@example.invalid'}).encode()
            request = Request(base + '/api/patient/update-profile', data=payload,
                              headers={'Content-Type': 'application/json'})
            with http.open(request, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(json.load(response)['success'])
            self.assertEqual(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=101').fetchone()[0], 'http-owner@example.invalid')
            self.assertIsNone(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=102').fetchone()[0])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_real_login_rejects_missing_locked_or_unlinked_account(self):
        for account_id in (8, 9, 10, 11, 12, 13, 999):
            with self.subTest(account=account_id), self.app.app_context():
                self.assertIsNone(self.users.authenticate('fixture_' + str(account_id), 'IsolatedPassword123!'))
        with self.app.app_context():
            self.assertIsNone(self.users.authenticate('fixture_1', 'wrong-password'))
        self.assert_no_writes()

    def test_profile_other_owner_invalid_data_and_wrong_role_denied(self):
        self.login(1)
        self.assertEqual(self.client.post('/api/patient/update-profile', json={'patient_id': 102}).status_code, 403)
        self.assertEqual(self.client.post('/api/patient/update-profile', json={'email': 'not-an-email'}).status_code, 400)
        for account_id in (3, 4, 5, 6, 7):
            self.login(account_id)
            self.assertEqual(self.client.post('/api/patient/update-profile', json={}).status_code, 403)
            self.assertEqual(self.client.post('/patient/profile', data={}).status_code, 403)
        self.assert_no_writes()

    def test_purchase_owner_other_and_wrong_role(self):
        from models.pharmacy_model import PharmacyModel
        with patch.object(PharmacyModel, 'get_prescription_detail', return_value={'id': 51, 'benh_nhan_id': 101}), patch.object(
                PharmacyModel, 'choose_medicine_purchase_option', return_value=(True, 'isolated')) as choose:
            self.login(1)
            self.assertEqual(self.client.post('/api/prescription/choose-buying-option', json={'prescription_id': 51}).status_code, 200)
            choose.assert_called_once()
            choose.reset_mock()
            for account_id in (2, 3, 4, 5, 6, 7):
                self.login(account_id)
                self.assertEqual(self.client.post('/api/prescription/choose-buying-option', json={'prescription_id': 51}).status_code, 403)
            choose.assert_not_called()
        self.assert_no_writes()

    def test_detail_owner_other_and_deleted_account(self):
        from models.medical_record_model import MedicalRecordModel
        from models.pharmacy_model import PharmacyModel
        from models.appointment_model import AppointmentModel
        cases = [('/api/emr/detail/1', MedicalRecordModel, 'get_examination_by_id', {'benh_nhan_id': 101}),
                 ('/api/prescription/detail/1', PharmacyModel, 'get_prescription_detail', {'benh_nhan_id': 101}),
                 ('/api/appointment/1', AppointmentModel, 'get_by_id', {'benh_nhan_id': 101}),
                 ('/api/lab/result/view/1', MedicalRecordModel, 'get_lab_item_by_id', {'patient_id': 101, 'trang_thai': 'Đã duyệt'})]
        for path, model, method, row in cases:
            with self.subTest(path=path), patch.object(model, method, return_value=row):
                for account_id, status in ((1, 200), (2, 403), (8, 401), (999, 401)):
                    self.login(account_id)
                    self.assertEqual(self.client.get(path).status_code, status)
        self.assert_no_writes()

    def test_doctor_list_detail_and_update_use_same_department_policy(self):
        self.login(3)
        with patch('controllers.admin_controller.render_template', side_effect=lambda name, **data: json.dumps(data)), patch.object(
                self.patients, 'get_patient_history', return_value=[]):
            response = self.client.get('/admin/patients')
            self.assertEqual(response.status_code, 200)
            self.assertEqual([row['id'] for row in json.loads(response.data)['patients']], [101])
            self.assertEqual(self.client.get('/admin/patients/101').status_code, 200)
            for path in ('/admin/patients/102', '/admin/patient_details/102', '/admin/patient-details?id=102'):
                self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post('/api/patient/update', json={'patient_id': 102}).status_code, 403)
        self.assertEqual(self.client.post('/api/patient/update', json={'patient_id': 101, 'email': 'doctor@example.invalid'}).status_code, 200)
        self.assertEqual(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=101').fetchone()[0], 'doctor@example.invalid')

    def test_doctor_missing_department_has_no_global_fallback(self):
        self.keeper.execute('UPDATE bac_si SET chuyen_khoa_id=NULL WHERE id=203')
        self.keeper.commit()
        self.login(3)
        with patch('controllers.admin_controller.render_template', side_effect=lambda name, **data: json.dumps(data)):
            response = self.client.get('/admin/patients')
            self.assertEqual(json.loads(response.data)['patients'], [])
        self.assertEqual(self.client.get('/admin/patients/101').status_code, 403)

    def test_patient_cannot_access_staff_list_detail_or_update(self):
        self.login(1)
        for path in ('/admin/patients', '/admin/patients/101', '/admin/patient-details?id=101'):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post('/api/patient/update', json={'patient_id': 101}).status_code, 403)
        self.assert_no_writes()

    def test_role_lock_profile_and_password_reset_changes_apply_next_request(self):
        self.login(1)
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=0 WHERE id=1')
        self.keeper.commit()
        self.assertEqual(self.client.post('/api/patient/update-profile', json={}).status_code, 401)
        self.login(14)
        self.assertEqual(self.client.post('/api/patient/update-profile', json={}).status_code, 403)
        self.login(1)
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=1 WHERE id=1')
        self.keeper.execute('DELETE FROM benh_nhan WHERE tai_khoan_id=1')
        self.keeper.commit()
        self.assertEqual(self.client.post('/api/patient/update-profile', json={}).status_code, 401)

    def test_live_role_change_overrides_session_role(self):
        self.login(6, vai_tro='LETAN')
        self.keeper.execute('UPDATE tai_khoan SET vai_tro_id=4 WHERE id=6')
        self.keeper.commit()
        self.assertEqual(self.client.post('/api/appointment/book', json={'patient_id': 101}).status_code, 403)
        self.assert_no_writes()

    def test_form_profile_update_ignores_foreign_target_and_uses_owner(self):
        self.login(1, patient_id=102)
        with patch.object(self.patients, 'get_patient_history', return_value=[]):
            response = self.client.post('/patient/profile', data={
                'patient_id': 102, 'email': 'form-owner@example.invalid'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=101').fetchone()[0], 'form-owner@example.invalid')
        self.assertIsNone(self.keeper.execute('SELECT email FROM benh_nhan WHERE id=102').fetchone()[0])

    def test_account_list_pagination_and_linked_patient_detail_respect_policy(self):
        self.login(3)
        response = self.client.get('/api/admin/accounts/list?role=BENHNHAN&per_page=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['total'], 1)
        self.assertEqual([row['patient_id'] for row in response.json['accounts']], [101])
        with patch.object(self.users, 'get_account_detail', return_value={
                'id': 2, 'benh_nhan': {'id': 102}}):
            self.assertEqual(self.client.get('/api/admin/account/2').status_code, 403)
        with patch.object(self.users, 'get_account_detail', return_value={
                'id': 1, 'benh_nhan': {'id': 101}}):
            self.assertEqual(self.client.get('/api/admin/account/1').status_code, 200)
        self.assert_no_writes()

    def test_nonexistent_account_is_not_active(self):
        with self.app.app_context():
            self.assertFalse(self.users.check_account_active(None))
            self.assertFalse(self.users.check_account_active(999))
            self.assertFalse(self.users.check_account_active(8))
            self.assertTrue(self.users.check_account_active(1))

    def test_safe_next_url_matrix(self):
        for value in ('https://evil.invalid', '//evil.invalid', '/\\evil.invalid',
                      '/%2fevil.invalid', '/%252fevil.invalid', '/%5cevil.invalid',
                      '/%0d%0aLocation:evil', 'javascript:alert(1)', 'relative', ' //evil.invalid'):
            with self.subTest(value=value):
                self.assertIsNone(self.security.safe_next_url(value))
        self.assertEqual(self.security.safe_next_url('/patient/profile?tab=info'), '/patient/profile?tab=info')

    def test_login_redirect_rejects_external_next_and_clears_old_session(self):
        with self.client.session_transaction() as session:
            session['obsolete_flag'] = 'must be cleared'
        response = self.client.post('/login?next=//evil.invalid', data={
            'username': 'fixture_1', 'password': 'IsolatedPassword123!'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/patient/dashboard')
        with self.client.session_transaction() as session:
            self.assertEqual(session['user']['patient_id'], 101)
            self.assertNotIn('obsolete_flag', session)

    def test_old_public_key_cannot_sign_an_accepted_session(self):
        from flask import Flask
        public_app = Flask('obsolete-key')
        public_app.secret_key = 'h2t_healthcare_clinic_secret_key_2026'
        forged = public_app.session_interface.get_signing_serializer(public_app).dumps({
            'logged_in': True, 'user': {'id': 7, 'vai_tro': 'ADMIN'}})
        self.client.set_cookie('session', forged)
        self.assertEqual(self.client.post('/api/patient/update-profile', json={}).status_code, 401)
        self.assert_no_writes()

    def test_patient_prescription_list_uses_live_owner(self):
        from models.pharmacy_model import PharmacyModel
        self.login(1, patient_id=102)
        with patch.object(PharmacyModel, 'get_prescriptions_by_patient', return_value=[]) as fetch:
            self.assertEqual(self.client.get('/api/patient/prescriptions').status_code, 200)
            fetch.assert_called_once_with(101)
            fetch.reset_mock()
            self.assertEqual(self.client.get('/api/patient/prescriptions?patient_id=102').status_code, 403)
            fetch.assert_not_called()

    def test_appointment_cancel_and_reschedule_enforce_owner_and_role(self):
        from models.appointment_model import AppointmentModel
        for path, method in (('/api/appointment/cancel', 'cancel'),
                             ('/api/appointment/reschedule', 'reschedule')):
            with self.subTest(path=path), patch.object(AppointmentModel, 'get_by_id', return_value={
                    'id': 51, 'benh_nhan_id': 101}), patch.object(AppointmentModel, method, return_value=(True, 'isolated')) as mutate:
                payload = {'appointment_id': 51, 'ngay_hen': '2030-01-01', 'gio_hen': '09:00'}
                for account_id, expected in ((2, 403), (4, 403), (8, 401), (999, 401)):
                    self.login(account_id)
                    self.assertEqual(self.client.post(path, json=payload).status_code, expected)
                mutate.assert_not_called()
                self.login(1)
                self.assertEqual(self.client.post(path, json=payload).status_code, 200)
                mutate.assert_called_once()
        self.assert_no_writes()

    def test_doctor_lab_list_and_detail_agree(self):
        from models.medical_record_model import MedicalRecordModel
        self.login(3)
        with patch.object(MedicalRecordModel, 'get_all_lab_orders', return_value=[
                {'patient_id': 101}, {'patient_id': 102}]):
            response = self.client.get('/api/lab/orders')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['orders'], [{'patient_id': 101}])
        with patch.object(MedicalRecordModel, 'get_lab_item_by_id', return_value={'patient_id': 102}):
            self.assertEqual(self.client.get('/api/lab/result/view/1').status_code, 403)
        self.assert_no_writes()

    def test_secret_key_configuration(self):
        with self.assertRaisesRegex(RuntimeError, 'SECRET_KEY is required'):
            self.module.create_app({'DEBUG': False, 'TESTING': False, 'SECRET_KEY': None})
        with self.assertRaisesRegex(RuntimeError, 'public default'):
            self.module.create_test_app({'SECRET_KEY': 'h2t_healthcare_clinic_secret_key_2026'})
        development = self.module.create_app({'DEBUG': True, 'SECRET_KEY': None})
        self.assertGreaterEqual(len(development.secret_key), 64)
        with self.assertRaisesRegex(RuntimeError, 'at least 32'):
            self.module.create_app({'DEBUG': False, 'SECRET_KEY': 'short'})


if __name__ == '__main__':
    unittest.main()
