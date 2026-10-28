"""Read-only MSSQL integration, no fixture/schema/seed. Skip without confirmed config."""
import unittest
import pyodbc
from core.mssql_test_database import MssqlTestSettings, MssqlTestFactory, TestDatabaseNotConfigured


class MssqlReadOnlySmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.settings = MssqlTestSettings.from_environment()
        except TestDatabaseNotConfigured as exc:
            raise unittest.SkipTest(str(exc))

    def test_real_pyodbc_connection_to_verified_test_database(self):
        conn = MssqlTestFactory(self.settings)()
        try:
            self.assertIsInstance(conn._conn,pyodbc.Connection)
            row = conn.cursor().execute('SELECT DB_NAME() AS database_name, @@TRANCOUNT AS transaction_count').fetchone()
            self.assertEqual(row['database_name'].casefold(),self.settings.database.casefold())
        finally:
            conn.rollback()
            conn.close()

    def test_app_test_factory_uses_verified_mssql_connection(self):
        from app import create_test_app
        from core.database import get_db
        app = create_test_app({'DATABASE_CONNECTION_FACTORY':MssqlTestFactory(self.settings)})
        with app.app_context():
            conn = get_db()
            try:
                self.assertIsInstance(conn._conn,pyodbc.Connection)
                self.assertEqual(conn._engine,'sqlserver')
            finally:
                conn.rollback()
                conn.close()


if __name__ == '__main__':
    unittest.main()
