import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import sync_db


class SyncDbSafetyTests(unittest.TestCase):
    def setUp(self):
        self.params = {
            'driver': '{ODBC Driver 17 for SQL Server}',
            'server': r'.\SQLEXPRESS',
            'database': 'quan_ly_phong_kham',
            'trusted_connection': 'yes',
        }

    def test_seed_stops_at_first_failed_batch(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as root:
            sql_path = os.path.join(root, 'seed.sql')
            with open(sql_path, 'w', encoding='utf-8') as source:
                source.write('CREATE TABLE example (id INT);\nGO\nINSERT INTO example VALUES (1);\n')
            cursor = Mock()
            cursor.execute.side_effect = [None, RuntimeError('insert failed')]
            cursor.nextset.return_value = False
            connection = Mock()
            connection.cursor.return_value = cursor
            with patch.object(sync_db.pyodbc, 'connect', return_value=connection), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(sync_db.execute_sql_file(self.params, sql_path))
            self.assertEqual(cursor.execute.call_count, 2)
            connection.close.assert_called_once_with()

    def test_migration_error_is_reported_as_failure(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as root:
            migration_dir = os.path.join(root, 'database', 'migrations')
            os.makedirs(migration_dir)
            with open(os.path.join(migration_dir, '001.sql'), 'w', encoding='utf-8') as source:
                source.write('SELECT 1;\n')
            cursor = Mock()
            cursor.execute.side_effect = RuntimeError('migration failed')
            connection = Mock()
            connection.cursor.return_value = cursor
            with patch.object(sync_db, 'CURRENT_DIR', root), \
                    patch.object(sync_db.pyodbc, 'connect', return_value=connection), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(sync_db.run_safe_migrations(self.params))
            connection.close.assert_called_once_with()

    def test_summary_rejects_missing_essential_seed_data(self):
        cursor = Mock()
        cursor.fetchone.side_effect = [(0,), (1,), (1,), (1,)]
        connection = Mock()
        connection.cursor.return_value = cursor
        essential = ['vai_tro', 'tai_khoan', 'chuyen_khoa', 'bac_si']
        with patch.object(sync_db, 'check_existing_tables', return_value=essential), \
                patch.object(sync_db, 'expected_tables', return_value=set(essential)), \
                patch.object(sync_db.pyodbc, 'connect', return_value=connection), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(sync_db.print_summary(self.params))

    def test_check_mode_does_not_create_database_or_rewrite_config(self):
        with patch.object(sync_db.sys, 'argv', ['sync_db.py', '--check']), \
                patch.object(sync_db, 'detect_working_connection', return_value=self.params), \
                patch.object(sync_db, 'ensure_database_exists', return_value=False) as ensure, \
                patch.object(sync_db, 'update_config_file_if_needed') as update, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_info:
                sync_db.main()
        self.assertEqual(exit_info.exception.code, 1)
        ensure.assert_called_once_with(self.params, create=False)
        update.assert_not_called()

    def test_partial_database_never_falls_back_to_destructive_seed(self):
        with patch.object(sync_db.sys, 'argv', ['sync_db.py']), \
                patch.object(sync_db, 'detect_working_connection', return_value=self.params), \
                patch.object(sync_db, 'update_config_file_if_needed'), \
                patch.object(sync_db, 'ensure_database_exists', return_value=True), \
                patch.object(sync_db, 'check_existing_tables', return_value=['vai_tro']), \
                patch.object(sync_db, 'run_safe_migrations', return_value=False), \
                patch.object(sync_db, 'execute_sql_file') as seed, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_info:
                sync_db.main()
        self.assertEqual(exit_info.exception.code, 1)
        seed.assert_not_called()

    def test_restore_failure_never_falls_back_to_seed(self):
        from models.backup_model import BackupModel

        with patch.object(sync_db.sys, 'argv', ['sync_db.py', '--restore']), \
                patch.object(sync_db, 'detect_working_connection', return_value=self.params), \
                patch.object(sync_db, 'update_config_file_if_needed'), \
                patch.object(sync_db, 'ensure_database_exists', return_value=True), \
                patch.object(sync_db, 'check_existing_tables', return_value=['vai_tro']), \
                patch.object(BackupModel, 'get_latest_backup', return_value='latest.bak'), \
                patch.object(BackupModel, 'restore_backup', return_value=(False, 'restore failed')), \
                patch.object(sync_db, 'execute_sql_file') as seed, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_info:
                sync_db.main()
        self.assertEqual(exit_info.exception.code, 1)
        seed.assert_not_called()


if __name__ == '__main__':
    unittest.main()
