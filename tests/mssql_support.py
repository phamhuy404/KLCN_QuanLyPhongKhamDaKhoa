"""Real MSSQL fixture helpers. No SQL translation and no emulated application lock."""
from core.mssql_test_database import MssqlTestFactory
from core.database import UnifiedConnection, UnifiedCursor


TABLES = ('chi_tiet_hoa_don','hoa_don','chi_tiet_don_thuoc','don_thuoc',
          'chi_tiet_chi_dinh','phieu_chi_dinh','phieu_kham','lich_hen','lich_lam_viec',
          'thong_bao','audit_log','chi_so_sinh_ton','thuoc','dich_vu','phong_kham',
          'bac_si','nhan_vien','benh_nhan','tai_khoan','vai_tro','chuyen_khoa')


class FixtureRow(dict):
    def __getitem__(self,key):
        if isinstance(key,int):
            return list(self.values())[key]
        return super().__getitem__(key)


class FixtureCursor:
    def __init__(self,cursor):
        self.cursor = cursor

    def fetchone(self):
        row = self.cursor.fetchone()
        return FixtureRow(row) if row is not None else None

    def fetchall(self):
        return [FixtureRow(row) for row in self.cursor.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class FixtureConnection:
    def __init__(self,connection):
        self.connection = connection

    def execute(self,sql,params=()):
        return FixtureCursor(self.connection.cursor().execute(sql,params))

    def executemany(self,sql,params):
        return self.connection.cursor().executemany(sql,params)

    def executescript(self,sql):
        # Send the original T-SQL batch. Drain SELECT/row-count results, never rewrite SQL.
        cursor = self.connection._conn.cursor()
        try:
            cursor.execute(sql)
            while cursor.nextset():
                pass
        finally:
            cursor.close()

    def commit(self):
        return self.connection.commit()

    def close(self):
        try:
            self.connection.rollback()
            self.connection.cursor().execute("EXEC sys.sp_releaseapplock @Resource='clinic.integration.fixture', @LockOwner='Session'")
            self.connection.rollback()
        finally:
            self.connection.close()


def fixture_connection(settings):
    connection = MssqlTestFactory(settings)()
    try:
        cursor = connection.cursor()
        cursor.execute("""SET NOCOUNT ON;
            DECLARE @result int;
            EXEC @result=sys.sp_getapplock @Resource='clinic.integration.fixture',
                @LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0;
            SELECT @result AS fixture_lock;""")
        if cursor.fetchone()['fixture_lock'] < 0:
            raise RuntimeError('Another integration fixture owns this test database')
        cursor.close()
        connection.rollback()
        return FixtureConnection(connection)
    except Exception:
        connection.close()
        raise


class TracedCursor(UnifiedCursor):
    def __init__(self,raw,statements):
        super().__init__(raw)
        self.statements = statements

    def execute(self,sql,params=()):
        self.statements.append(sql)
        return super().execute(sql,params)


class TracedConnection(UnifiedConnection):
    def __init__(self,raw,statements):
        super().__init__(raw)
        self.statements = statements

    def cursor(self):
        return TracedCursor(self._conn.cursor(),self.statements)


def traced_connection(settings,statements):
    verified = MssqlTestFactory(settings)()
    return TracedConnection(verified._conn,statements)


def reset_fixture_tables(keeper):
    # This is fixture DDL, only on the separately confirmed disposable DB.
    # The DBA marker table is never modified or removed.
    keeper.executescript('\n'.join(f'DROP TABLE IF EXISTS dbo.[{table}];' for table in TABLES))
    keeper.commit()
