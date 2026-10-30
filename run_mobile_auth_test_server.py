"""Explicit verified MSSQL test server. No fixture DDL, worker, seed or SMTP."""
import os
from core.mssql_test_database import MssqlTestSettings, MssqlTestFactory, TestDatabaseNotConfigured


def main():
    try:
        settings = MssqlTestSettings.from_environment()
    except TestDatabaseNotConfigured as exc:
        raise SystemExit(str(exc))
    secret = os.environ.get('MOBILE_TOKEN_SECRET', '')
    if len(secret.encode()) < 32:
        raise SystemExit('Set a dedicated MOBILE_TOKEN_SECRET of at least 32 bytes for this test environment')
    factory = MssqlTestFactory(settings)
    connection = factory()  # Read-only identity/marker verification before listening.
    connection.close()
    from app import create_test_app
    app = create_test_app({'DATABASE_CONNECTION_FACTORY':factory,
                           'SECRET_KEY':secret,'MOBILE_TOKEN_SECRET':secret,'DEBUG':False})
    app.run(host='127.0.0.1',port=5001,debug=False,use_reloader=False)


if __name__ == '__main__':
    main()
