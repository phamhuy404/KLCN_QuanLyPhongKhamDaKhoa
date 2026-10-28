"""Unit/contract checks only: mock pyodbc; no database connection is made."""
from dataclasses import replace
from pathlib import Path
import ast
import unittest
from unittest.mock import Mock, patch

from core.mssql_test_database import MssqlTestSettings, MssqlTestFactory, TestDatabaseNotConfigured
from core.database import UnifiedCursor


class MssqlTestDatabaseUnitTests(unittest.TestCase):
    def setUp(self):
        self.settings = MssqlTestSettings('ODBC Driver 18 for SQL Server','test-host',
            'clinic_integration_test','clinic_test_login','unit-only-placeholder','test-host',
            '755899d2-93e1-45d5-af04-d6e2c7f4f900')

    def test_missing_confirmation_never_connects(self):
        with patch('pyodbc.connect') as connect:
            with self.assertRaises(TestDatabaseNotConfigured):
                MssqlTestSettings.from_environment({})
            connect.assert_not_called()

    def test_main_database_invalid_driver_and_admin_rejected_before_connect(self):
        import config
        for changes in ({'database':config.SQLSERVER_CONFIG['database']},
                        {'database':'master'},{'driver':'SQLite3'},{'username':'sa'},
                        {'server':'test\nhost'},{'marker_token':'not-a-uuid'}):
            with self.subTest(changes=changes), patch('pyodbc.connect') as connect:
                with self.assertRaises(ValueError):
                    MssqlTestFactory(replace(self.settings,**changes))
                connect.assert_not_called()

    def raw(self,identity=None,markers=None):
        raw = Mock()
        raw.cursor.return_value.fetchone.return_value = identity or (
            'test-host','clinic_integration_test','clinic_test_login',0,0)
        raw.cursor.return_value.fetchall.return_value = markers if markers is not None else [(self.settings.marker_token,)]
        return raw

    def test_identity_and_marker_checked_each_connection_without_any_writes(self):
        raw = self.raw()
        with patch('pyodbc.connect',return_value=raw) as connect:
            factory = MssqlTestFactory(self.settings)
            self.assertEqual(factory()._engine,'sqlserver')
            factory()
        self.assertEqual(connect.call_count,2)
        self.assertIn('Encrypt=yes;TrustServerCertificate=no',connect.call_args.args[0])
        self.assertFalse(connect.call_args.kwargs['autocommit'])
        for call in raw.cursor.return_value.execute.call_args_list:
            self.assertTrue(call.args[0].lstrip().upper().startswith('SELECT'))

    def test_wrong_server_database_login_sysadmin_and_main_access_fail_closed(self):
        valid = ['test-host','clinic_integration_test','clinic_test_login',0,0]
        for index,value in ((0,'other-server'),(1,'quan_ly_phong_kham'),(2,'other-login'),(3,1),(4,1)):
            identity = list(valid)
            identity[index] = value
            raw = self.raw(identity)
            with self.subTest(index=index), patch('pyodbc.connect',return_value=raw):
                with self.assertRaisesRegex(RuntimeError,'verification failed'):
                    MssqlTestFactory(self.settings)()
                raw.close.assert_called_once()
                raw.commit.assert_not_called()

    def test_missing_or_wrong_marker_closes_connection(self):
        for markers in ([],[('755899d2-93e1-45d5-af04-d6e2c7f4f901',)],[(self.settings.marker_token,)]*2):
            raw = self.raw(markers=markers)
            with self.subTest(markers=markers), patch('pyodbc.connect',return_value=raw):
                with self.assertRaisesRegex(RuntimeError,'marker verification failed'):
                    MssqlTestFactory(self.settings)()
                raw.close.assert_called_once()

    def test_verification_sql_failure_never_returns_connection(self):
        raw = self.raw()
        raw.cursor.return_value.execute.side_effect = RuntimeError('unit verification error')
        with patch('pyodbc.connect',return_value=raw), self.assertRaises(RuntimeError):
            MssqlTestFactory(self.settings)()
        raw.close.assert_called_once()

    def test_insert_identity_in_same_batch_ignores_trigger_resultsets(self):
        raw = Mock()
        descriptions = [None,[('trigger_value',)],[('__clinic_insert_id',)]]
        type(raw).description = property(lambda obj: descriptions[0])
        raw.nextset.side_effect = lambda: bool(descriptions.pop(0)) or True
        raw.fetchone.return_value = (42,)
        cursor = UnifiedCursor(raw)
        cursor.execute('INSERT INTO phieu_kham(ma_phieu) VALUES (?)',('UNIT',))
        self.assertEqual(cursor.lastrowid,42)
        self.assertEqual(raw.execute.call_count,1)
        self.assertIn('SCOPE_IDENTITY()',raw.execute.call_args.args[0])
        self.assertNotIn('@@IDENTITY',raw.execute.call_args.args[0])

    def test_missing_insert_identity_result_is_not_swallowed(self):
        raw = Mock(description=None)
        raw.nextset.return_value = False
        with self.assertRaises(RuntimeError):
            UnifiedCursor(raw).execute('INSERT INTO phieu_kham(ma_phieu) VALUES (?)',('UNIT',))

    def test_integration_sources_have_no_sqlite_engine_or_tsql_translation(self):
        root = Path(__file__).parent
        for name in ('test_security_access.py','test_scheduling_safety.py','test_clinical_media.py','test_emr_workflow.py'):
            source = (root/name).read_text(encoding='utf-8')
            ast.parse(source)
            for forbidden in ('import sqlite3','sqlite3.connect','PRAGMA database_list',
                              'AUTOINCREMENT','last_insert_rowid','RAISE(ABORT','BEFORE UPDATE ON'):
                self.assertNotIn(forbidden,source,name)


if __name__ == '__main__':
    unittest.main()
