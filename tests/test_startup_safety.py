"""Isolated tests: run this file only; never discover the legacy DB tests."""
import importlib
from pathlib import Path
import smtplib
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import pyodbc


def run_isolated_process(code):
    # Windows subprocess capture_output starts reader threads, which our guard forbids.
    with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as output:
        result = subprocess.run([sys.executable, '-B', '-c', code],
                                cwd=Path(__file__).resolve().parents[1],
                                stdout=output, stderr=output, timeout=30)
        output.seek(0)
        return result.returncode, output.read()


class StartupSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Guard before importing *any* application modules, including blueprints.
        cls.guards = [
            patch.object(pyodbc, 'connect', side_effect=AssertionError('Real DB forbidden')),
            patch.object(threading.Thread, 'start', side_effect=AssertionError('Worker forbidden')),
            patch.object(smtplib, 'SMTP', side_effect=AssertionError('SMTP forbidden')),
            patch.object(smtplib, 'SMTP_SSL', side_effect=AssertionError('SMTP forbidden')),
        ]
        cls.mocks = [guard.start() for guard in cls.guards]
        for guard in cls.guards:
            cls.addClassCleanup(guard.stop)
        cls.module = importlib.import_module('app')
        cls.db = importlib.import_module('core.database')
        cls.service = importlib.import_module('core.notification_service').NotificationService

    def setUp(self):
        for mock in self.mocks:
            mock.reset_mock()
        self.app = self.module.create_app({'TESTING': True, 'SECRET_KEY': 'isolated-test'})

    def test_fresh_process_import_has_no_external_side_effects(self):
        code = '''
from unittest.mock import patch
import pyodbc, threading, smtplib
with patch.object(pyodbc, 'connect') as db, patch.object(threading.Thread, 'start') as worker, patch.object(smtplib, 'SMTP') as smtp, patch.object(smtplib, 'SMTP_SSL') as ssl:
    with patch('pathlib.Path.mkdir') as mkdir, patch('os.makedirs') as makedirs:
        import core.image_service
        import app
        test_app = app.create_test_app()
        mkdir.assert_not_called()
        makedirs.assert_not_called()
    assert {'home', 'auth', 'patient', 'admin', 'api'} == set(test_app.blueprints)
    db.assert_not_called()
    worker.assert_not_called()
    smtp.assert_not_called()
    ssl.assert_not_called()
'''
        returncode, output = run_isolated_process(code)
        self.assertEqual(returncode, 0, output)

    def test_real_http_server_in_test_mode(self):
        code = '''
from unittest.mock import patch
import pyodbc, smtplib, threading
from urllib.request import build_opener, ProxyHandler
from urllib.error import HTTPError
from werkzeug.serving import make_server
with patch.object(pyodbc, 'connect', side_effect=AssertionError('Real DB forbidden')) as db, patch.object(smtplib, 'SMTP', side_effect=AssertionError('SMTP forbidden')) as smtp, patch.object(smtplib, 'SMTP_SSL', side_effect=AssertionError('SMTP forbidden')) as ssl:
    import app
    test_app = app.create_app({'TESTING': True})
    server = make_server('127.0.0.1', 0, test_app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = build_opener(ProxyHandler({}))
        base = 'http://127.0.0.1:' + str(server.server_port)
        with client.open(base + '/login', timeout=5) as response:
            assert response.status == 200
            assert b'<form' in response.read()
        try:
            client.open(base + '/api/feedback/submit', data=b'{}', timeout=5)
            raise AssertionError('Unauthenticated request succeeded')
        except HTTPError as error:
            assert error.code == 401
        db.assert_not_called()
        smtp.assert_not_called()
        ssl.assert_not_called()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
'''
        returncode, output = run_isolated_process(code)
        self.assertEqual(returncode, 0, output)

    def test_api_commit_failure_and_success_keep_authentication(self):
        for fails in (True, False):
            with self.subTest(commit_fails=fails):
                auth = Mock()
                auth.cursor.return_value.fetchone.return_value = {
                    'id': 123, 'trang_thai': 1, 'vai_tro': 'BENHNHAN',
                    'patient_id': 123, 'da_hoan_thien_ho_so': 1,
                    'yeu_cau_doi_mat_khau': 0,
                }
                raw = Mock()
                raw.cursor.return_value.fetchone.return_value = (123,)
                if fails:
                    raw.commit.side_effect = RuntimeError('commit failed')
                self.app.config['DATABASE_CONNECTION_FACTORY'] = Mock(side_effect=[
                    self.db.UnifiedConnection(auth), self.db.UnifiedConnection(raw)])
                client = self.app.test_client()
                with client.session_transaction() as session:
                    session['logged_in'] = True
                    session['user'] = {'id': 123, 'patient_id': 123, 'vai_tro': 'BENHNHAN'}
                response = client.post('/api/feedback/submit', json={
                    'noi_dung': 'Isolated API transaction test', 'diem_danh_gia': 5})
                self.assertEqual(response.status_code, 400 if fails else 200)
                self.assertEqual(response.json['success'], not fails)
                auth.cursor.return_value.execute.assert_called_once()
                sql, params = auth.cursor.return_value.execute.call_args.args
                self.assertIn('LEFT JOIN benh_nhan', sql)
                self.assertEqual(params, (123,))
                raw.commit.assert_called_once_with()
                raw.close.assert_called_once_with()
                if fails:
                    self.assertIn('commit failed', response.json['message'])
                    self.assertGreaterEqual(raw.rollback.call_count, 1)
                else:
                    raw.rollback.assert_not_called()

    def test_all_routes_and_aliases_registered_without_runtime(self):
        self.assertEqual(set(self.app.blueprints), {'home', 'auth', 'patient', 'admin', 'api'})
        self.assertEqual(
            {(r.rule, r.endpoint, frozenset(r.methods)) for r in self.module.app.url_map.iter_rules()},
            {(r.rule, r.endpoint, frozenset(r.methods)) for r in self.app.url_map.iter_rules()})
        self.assertIn('admin_dashboard', self.app.view_functions)
        for mock in self.mocks:
            mock.assert_not_called()

    def test_test_configuration_cannot_enable_real_io(self):
        app = self.module.create_app({'TESTING': True, 'DATABASE_ACCESS_ENABLED': True,
                                      'NOTIFICATIONS_ENABLED': True})
        with app.app_context():
            with self.assertRaisesRegex(RuntimeError, 'Database access disabled'):
                self.db.get_db()
            self.assertFalse(self.service.send_email('test@example.invalid', 'test', 'test')[0])
            self.assertIsNone(self.service.start_background_scheduler())
            with self.assertRaisesRegex(RuntimeError, 'Notifications disabled'):
                self.service.run_all_reminders()
        self.module.start_runtime_services(app)
        for mock in self.mocks:
            mock.assert_not_called()

    def test_injected_connection_does_not_initialize_schema(self):
        factory = Mock()
        self.app.config['DATABASE_CONNECTION_FACTORY'] = factory
        with self.app.app_context(), patch.object(self.db, 'ensure_schema_updates') as schema:
            self.assertIs(self.db.get_db(), factory.return_value)
            factory.assert_called_once_with()
            schema.assert_not_called()
        self.mocks[0].assert_not_called()

    def test_schema_updates_rejected_in_test_context(self):
        conn = Mock()
        with self.app.app_context(), self.assertRaisesRegex(RuntimeError, 'Schema updates disabled'):
            self.db.ensure_schema_updates(conn)
        conn.cursor.assert_not_called()

    def test_normal_connection_does_not_execute_schema_or_queries(self):
        raw = Mock()
        with patch.object(pyodbc, 'connect', return_value=raw), patch.object(self.db, 'ensure_schema_updates') as schema:
            conn = self.db.get_db()
            self.assertIs(conn._conn, raw)
            schema.assert_not_called()
            raw.cursor.assert_not_called()

    def test_explicit_startup_is_idempotent_and_does_not_initialize_database(self):
        app = self.module.create_app({'TESTING': False})
        with patch.object(self.service, 'start_background_scheduler', return_value=Mock()) as start:
            self.module.start_runtime_services(app)
            self.module.start_runtime_services(app)
            start.assert_called_once_with(interval_hours=2)
        self.mocks[0].assert_not_called()

    def test_scheduler_reloader_parent_skips_child_starts(self):
        app = self.module.create_app({'DEBUG': True})
        with patch.dict('os.environ', {'WERKZEUG_RUN_MAIN': 'false'}), patch(
                'core.notification_service.threading.Thread') as thread:
            self.module.start_runtime_services(app)
            thread.assert_not_called()
            self.assertNotIn('reminder_scheduler_started', app.extensions)
        with patch.dict('os.environ', {'WERKZEUG_RUN_MAIN': 'true'}), patch(
                'core.notification_service.threading.Thread') as thread:
            self.module.start_runtime_services(app)
            thread.return_value.start.assert_called_once_with()
            self.assertTrue(app.extensions['reminder_scheduler_started'])

    def test_login_page_and_legacy_booking(self):
        client = self.app.test_client()
        response = client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<form', response.data)
        response = client.get('/booking')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
        self.mocks[0].assert_not_called()

    def test_api_requires_authentication(self):
        response = self.app.test_client().post('/api/feedback/submit', json={'noi_dung': 'test'})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json['success'])
        self.mocks[0].assert_not_called()

    def test_commit_error_propagates_and_rolls_back(self):
        raw = Mock()
        error = RuntimeError('commit failed')
        raw.commit.side_effect = error
        conn = self.db.UnifiedConnection(raw)
        with self.assertRaises(RuntimeError) as result:
            conn.commit()
        self.assertIs(result.exception, error)
        raw.rollback.assert_called_once_with()

    def test_rollback_failure_preserves_commit_error_and_closes(self):
        raw = Mock()
        error = RuntimeError('commit failed')
        raw.commit.side_effect = error
        raw.rollback.side_effect = RuntimeError('rollback failed')
        with self.assertRaises(RuntimeError) as result:
            self.db.UnifiedConnection(raw).commit()
        self.assertIs(result.exception, error)
        raw.close.assert_called_once_with()

    def test_context_manager_closes_on_commit_failure(self):
        raw = Mock()
        raw.commit.side_effect = RuntimeError('commit failed')
        with self.assertRaisesRegex(RuntimeError, 'commit failed'):
            with self.db.UnifiedConnection(raw):
                pass
        raw.rollback.assert_called_once_with()
        raw.close.assert_called_once_with()

    def test_context_manager_success_and_body_error(self):
        raw = Mock()
        with self.db.UnifiedConnection(raw):
            pass
        raw.commit.assert_called_once_with()
        raw.rollback.assert_not_called()
        raw.close.assert_called_once_with()
        raw.reset_mock()
        with self.assertRaisesRegex(ValueError, 'body failed'):
            with self.db.UnifiedConnection(raw):
                raise ValueError('body failed')
        raw.commit.assert_not_called()
        raw.rollback.assert_called_once_with()
        raw.close.assert_called_once_with()

    def test_closed_connection_cannot_report_commit_success(self):
        conn = self.db.UnifiedConnection(Mock())
        conn.close()
        with self.assertRaisesRegex(RuntimeError, 'closed connection'):
            conn.commit()

    def test_business_cannot_report_success_after_failed_commit(self):
        from models.feedback_model import FeedbackModel
        raw = Mock()
        raw.cursor.return_value.fetchone.return_value = (1,)
        raw.commit.side_effect = RuntimeError('commit failed')
        self.app.config['DATABASE_CONNECTION_FACTORY'] = lambda: self.db.UnifiedConnection(raw)
        with self.app.app_context():
            ok, message = FeedbackModel.create(123, noi_dung='Isolated transaction failure test')
        self.assertFalse(ok)
        self.assertIn('commit failed', message)
        self.assertGreaterEqual(raw.rollback.call_count, 1)
        raw.close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
