import ast
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import sync_db
from models.backup_model import BackupModel


class BackupLocalConfigTests(unittest.TestCase):
    def test_sync_config_escapes_sqlexpress_instance(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as root:
            config_path = os.path.join(root, 'config.py')
            with open(config_path, 'w', encoding='utf-8') as file:
                file.write("SQLSERVER_CONFIG = {'driver': '{ODBC Driver 17 for SQL Server}', "
                           "'server': os.environ.get('SQL_SERVER_NAME', 'localhost')}\n")
            params = {'server': r'.\SQLEXPRESS', 'driver': '{ODBC Driver 17 for SQL Server}'}
            with patch.object(sync_db, 'CURRENT_DIR', root), patch.object(
                sync_db.config, 'SQLSERVER_CONFIG',
                {'server': 'localhost', 'driver': params['driver']}
            ):
                sync_db.update_config_file_if_needed(params)
            with open(config_path, encoding='utf-8') as file:
                source = file.read()
            ast.parse(source)
            self.assertIn(r"'.\\SQLEXPRESS'", source)

    def test_master_connection_uses_instance_selected_by_app(self):
        app_connection = Mock(server=r'.\SQLEXPRESS')
        master_connection = object()
        with patch('models.backup_model.get_db', return_value=app_connection), patch(
            'models.backup_model.pyodbc.connect', return_value=master_connection
        ) as connect:
            self.assertIs(BackupModel._connect_master(), master_connection)
        app_connection.close.assert_called_once_with()
        self.assertIn(r'SERVER=.\SQLEXPRESS;', connect.call_args.args[0])

    def test_restore_stops_if_safety_backup_fails(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as root:
            with open(os.path.join(root, 'existing.bak'), 'wb') as file:
                file.write(b'backup')
            cursor = Mock()
            cursor.description = [('LogicalName',), ('Type',)]
            cursor.fetchall.side_effect = [
                [('source_data', 'D'), ('source_log', 'L')],
                [(0, r'C:\SQL\target.mdf'), (1, r'C:\SQL\target_log.ldf')],
            ]
            master = Mock()
            master.cursor.return_value = cursor
            with patch.object(BackupModel, 'get_backup_dir', return_value=root), patch.object(
                BackupModel, 'create_backup', return_value=(False, 'backup error')
            ) as create, patch.object(BackupModel, '_connect_master', return_value=master):
                ok, message = BackupModel.restore_backup('existing.bak')
            self.assertFalse(ok)
            self.assertIn('backup error', message)
            create.assert_called_once_with(user_name='admin_auto_safety', cleanup=False)
            self.assertFalse(any('RESTORE DATABASE' in call.args[0]
                                 for call in cursor.execute.call_args_list))
            master.close.assert_called_once_with()

    def test_restore_moves_source_files_to_existing_destination_files(self):
        cursor = Mock()
        cursor.description = [('LogicalName',), ('Type',)]
        cursor.fetchall.side_effect = [
            [('old_data', 'D'), ('old_log', 'L')],
            [(0, r'C:\SQL17\clinic.mdf'), (1, r'C:\SQL17\clinic_log.ldf')],
        ]
        moves = BackupModel._restore_file_moves(cursor, r'D:\backup\clinic.bak', 'clinic')
        self.assertEqual(moves, [
            "MOVE N'old_data' TO N'C:\\SQL17\\clinic.mdf'",
            "MOVE N'old_log' TO N'C:\\SQL17\\clinic_log.ldf'",
        ])
        self.assertIn('RESTORE FILELISTONLY', cursor.execute.call_args_list[0].args[0])

    def test_restore_rejects_unknown_file_layout(self):
        cursor = Mock()
        cursor.description = [('LogicalName',), ('Type',)]
        cursor.fetchall.side_effect = [
            [('old_data', 'D'), ('extra_data', 'D'), ('old_log', 'L')],
            [(0, r'C:\SQL17\clinic.mdf'), (1, r'C:\SQL17\clinic_log.ldf')],
        ]
        with self.assertRaisesRegex(ValueError, 'Số lượng hoặc loại tệp'):
            BackupModel._restore_file_moves(cursor, r'D:\backup\clinic.bak', 'clinic')

    def test_restore_statement_uses_move_before_overwriting(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as root:
            with open(os.path.join(root, 'existing.bak'), 'wb') as file:
                file.write(b'backup')
            cursor = Mock()
            cursor.description = [('LogicalName',), ('Type',)]
            cursor.fetchall.side_effect = [
                [('old_data', 'D'), ('old_log', 'L')],
                [(0, r'C:\SQL17\clinic.mdf'), (1, r'C:\SQL17\clinic_log.ldf')],
            ]
            cursor.nextset.return_value = False
            master = Mock()
            master.cursor.return_value = cursor
            with patch.object(BackupModel, 'get_backup_dir', return_value=root), patch.object(
                BackupModel, 'create_backup', return_value=(True, 'saved')
            ), patch.object(BackupModel, '_connect_master', return_value=master), patch.object(
                BackupModel, '_log_history'
            ):
                ok, _ = BackupModel.restore_backup('existing.bak')
            self.assertTrue(ok)
            sql = cursor.execute.call_args_list[-1].args[0]
            self.assertIn("WITH REPLACE, MOVE N'old_data' TO N'C:\\SQL17\\clinic.mdf'", sql)
            self.assertIn("MOVE N'old_log' TO N'C:\\SQL17\\clinic_log.ldf'", sql)


if __name__ == '__main__':
    unittest.main()
