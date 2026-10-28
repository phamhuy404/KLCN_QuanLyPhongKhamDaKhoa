"""Explicit, fail-closed MSSQL test connections. Never falls back to app settings."""
from dataclasses import dataclass
import os
import re
from uuid import UUID

import pyodbc
import config
from core.database import UnifiedConnection


class TestDatabaseNotConfigured(RuntimeError):
    pass


def _odbc(value):
    if not value or any(ord(char) < 32 for char in value):
        raise ValueError('Invalid MSSQL test connection setting')
    return '{' + value.replace('}', '}}') + '}'


@dataclass(frozen=True, repr=False)
class MssqlTestSettings:
    driver: str
    server: str
    database: str
    username: str
    password: str
    expected_server: str
    marker_token: str

    @classmethod
    def from_environment(cls, environment=None):
        env = os.environ if environment is None else environment
        keys = ('DRIVER','SERVER','DATABASE','USERNAME','PASSWORD','EXPECTED_SERVER','MARKER_TOKEN')
        missing = [f'CLINIC_MSSQL_TEST_{key}' for key in keys if not env.get(f'CLINIC_MSSQL_TEST_{key}')]
        if env.get('CLINIC_MSSQL_TEST_CONFIRMED') != 'separate-disposable-mssql-test':
            missing.append('CLINIC_MSSQL_TEST_CONFIRMED')
        if missing:
            raise TestDatabaseNotConfigured('Missing confirmed MSSQL test settings: ' + ', '.join(missing))
        result = cls(*(env[f'CLINIC_MSSQL_TEST_{key}'] for key in keys))
        result.validate()
        return result

    def validate(self):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*_test', self.database, re.I):
            raise ValueError('Test database must have a dedicated name ending in _test')
        if self.database.casefold() == config.SQLSERVER_CONFIG['database'].casefold():
            raise ValueError('Main application database is forbidden')
        if self.username.casefold() == 'sa':
            raise ValueError('Use a dedicated non-sysadmin SQL login')
        if not re.fullmatch(r'ODBC Driver (17|18) for SQL Server', self.driver):
            raise ValueError('An explicit Microsoft SQL Server ODBC driver is required')
        UUID(self.marker_token)
        for value in (self.server,self.database,self.username,self.password,self.expected_server):
            _odbc(value)


class MssqlTestFactory:
    """Verifies server, database, login, no main-DB access and DBA marker per connection."""
    def __init__(self, settings):
        settings.validate()
        self.settings = settings

    def __call__(self):
        settings = self.settings
        settings.validate()
        connection_string = ';'.join(f'{key}={_odbc(value)}' for key,value in (
            ('DRIVER',settings.driver),('SERVER',settings.server),('DATABASE',settings.database),
            ('UID',settings.username),('PWD',settings.password)))
        connection_string += ';Encrypt=yes;TrustServerCertificate=no;APP=ClinicMssqlIsolatedTests;'
        raw = pyodbc.connect(connection_string,timeout=5,autocommit=False)
        try:
            cursor = raw.cursor()
            cursor.execute("""SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),
                DB_NAME(),ORIGINAL_LOGIN(),IS_SRVROLEMEMBER('sysadmin'),HAS_DBACCESS(?)""",
                (config.SQLSERVER_CONFIG['database'],))
            row = cursor.fetchone()
            if (not row or str(row[0]).casefold() != settings.expected_server.casefold()
                    or str(row[1]).casefold() != settings.database.casefold()
                    or str(row[2]).casefold() != settings.username.casefold()
                    or row[3] != 0 or row[4] not in (0,None)):
                raise RuntimeError('MSSQL test identity/isolation verification failed')
            cursor.execute("""SELECT marker_token FROM dbo.clinic_test_database_guard
                WHERE purpose = N'isolated-disposable-clinic-tests'""")
            markers = cursor.fetchall()
            if len(markers) != 1 or str(markers[0][0]).casefold() != str(UUID(settings.marker_token)):
                raise RuntimeError('MSSQL test DBA marker verification failed')
            cursor.close()
            raw.rollback()  # End verification transaction before business transaction.
            return UnifiedConnection(raw)
        except Exception:
            raw.close()
            raise
