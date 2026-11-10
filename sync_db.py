# Cong cu tu dong kiem tra va dong bo Co so du lieu Microsoft SQL Server
# Ho tro dong bo an toan khong lam mat du lieu cu khi keo ma nguon git pull

import os
import sys
import re
import pyodbc
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import config

def detect_working_connection():
    """Tu dong do tim instance SQL Server va ODBC Driver tuong thich tren may."""
    cfg = config.SQLSERVER_CONFIG.copy()
    candidate_servers = [
        cfg.get('server', 'localhost'),
        'localhost',
        r'.\SQLEXPRESS',
        r'localhost\SQLEXPRESS',
        '(local)',
        '127.0.0.1'
    ]
    unique_servers = []
    for s in candidate_servers:
        if s and s not in unique_servers:
            unique_servers.append(s)

    candidate_drivers = [
        '{ODBC Driver 17 for SQL Server}',
        '{ODBC Driver 18 for SQL Server}',
        '{SQL Server}'
    ]

    print("[*] Dang kiem tra ket noi Microsoft SQL Server tren may...")

    for driver in candidate_drivers:
        for srv in unique_servers:
            extra_cert = ";TrustServerCertificate=yes" if "18" in driver else ""
            conn_str = f"DRIVER={driver};SERVER={srv};DATABASE=master;Trusted_Connection=yes{extra_cert};"
            try:
                conn = pyodbc.connect(conn_str, timeout=3, autocommit=True)
                conn.close()
                print(f"[OK] Phat hien SQL Server kha dung: Server='{srv}', Driver='{driver}' (Windows Auth)")
                return {
                    'driver': driver,
                    'server': srv,
                    'database': cfg.get('database', 'quan_ly_phong_kham'),
                    'trusted_connection': 'yes',
                    'uid': cfg.get('uid', 'sa'),
                    'pwd': cfg.get('pwd', 'your_password'),
                    'trust_cert': "18" in driver
                }
            except Exception:
                pass

            if cfg.get('uid') and cfg.get('pwd'):
                conn_str_sql = f"DRIVER={driver};SERVER={srv};DATABASE=master;UID={cfg['uid']};PWD={cfg['pwd']}{extra_cert};"
                try:
                    conn = pyodbc.connect(conn_str_sql, timeout=3, autocommit=True)
                    conn.close()
                    print(f"[OK] Phat hien SQL Server kha dung: Server='{srv}', Driver='{driver}' (SQL Auth)")
                    return {
                        'driver': driver,
                        'server': srv,
                        'database': cfg.get('database', 'quan_ly_phong_kham'),
                        'trusted_connection': 'no',
                        'uid': cfg['uid'],
                        'pwd': cfg['pwd'],
                        'trust_cert': "18" in driver
                    }
                except Exception:
                    pass

    return None

def build_connection_string(conn_params, database='master'):
    """Xay dung chuoi ket noi ODBC tieu chuan."""
    extra = ";TrustServerCertificate=yes" if conn_params.get('trust_cert') else ""
    if conn_params.get('trusted_connection', 'yes').lower() == 'yes':
        return f"DRIVER={conn_params['driver']};SERVER={conn_params['server']};DATABASE={database};Trusted_Connection=yes{extra};"
    return f"DRIVER={conn_params['driver']};SERVER={conn_params['server']};DATABASE={database};UID={conn_params.get('uid')};PWD={conn_params.get('pwd')}{extra};"

def update_config_file_if_needed(conn_params):
    """Cap nhat lai config.py neu thong so ket noi tren may co su khac biet."""
    cfg_file = os.path.join(CURRENT_DIR, 'config.py')
    try:
        with open(cfg_file, 'r', encoding='utf-8') as f:
            text = f.read()

        current_srv = config.SQLSERVER_CONFIG.get('server')
        current_drv = config.SQLSERVER_CONFIG.get('driver')

        if current_srv != conn_params['server'] or current_drv != conn_params['driver']:
            print(f"[*] Cap nhat config.py tuong thich: server='{conn_params['server']}', driver='{conn_params['driver']}'")
            server_default = repr(conn_params['server'])
            text = re.sub(
                r"'server':\s*os\.environ\.get\([^)]+\)",
                lambda _: f"'server': os.environ.get('SQL_SERVER_NAME', {server_default})",
                text,
            )
            text = re.sub(
                r"'driver':\s*['\"][^'\"]+['\"]",
                lambda _: f"'driver': '{conn_params['driver']}'",
                text,
            )
            with open(cfg_file, 'w', encoding='utf-8') as f:
                f.write(text)
    except Exception as ex:
        print(f"[Canh bao] Khong the ghi de config.py: {ex}")

def ensure_database_exists(conn_params, create=True):
    """Dam bao co so du lieu dich ton tai trong SQL Server."""
    db_name = conn_params.get('database', 'quan_ly_phong_kham')
    master_str = build_connection_string(conn_params, 'master')
    conn = pyodbc.connect(master_str, autocommit=True)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sys.databases WHERE name = ?", (db_name,))
        exists = cursor.fetchone() is not None
        if not exists:
            if not create:
                print(f"[Loi] Co so du lieu '{db_name}' chua ton tai.")
                return False
            print(f"[*] Co so du lieu '{db_name}' chua ton tai. Dang khoi tao moi...")
            cursor.execute(f"CREATE DATABASE [{db_name.replace(']', ']]')}]")
            print(f"[OK] Da tao thanh cong co so du lieu '{db_name}' tren SQL Server!")
        else:
            print(f"[OK] Co so du lieu '{db_name}' da ton tai san sang.")
        return True
    finally:
        conn.close()

def check_existing_tables(conn_params):
    """Kiem tra so luong bang hien co trong CSDL."""
    db_name = conn_params.get('database', 'quan_ly_phong_kham')
    db_str = build_connection_string(conn_params, db_name)
    conn = pyodbc.connect(db_str, autocommit=True)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        return [r[0] for r in cursor.fetchall()]
    finally:
        conn.close()


def expected_tables(sql_path):
    """Lay ten cac bang ma script khoi tao day du phai tao."""
    with open(sql_path, 'r', encoding='utf-8') as source:
        return set(re.findall(r'^\s*CREATE\s+TABLE\s+(?:dbo\.)?(\w+)',
                              source.read(), flags=re.MULTILINE | re.IGNORECASE))

def run_safe_migrations(conn_params):
    """Ap dung migrations tren CSDL da co bang, dung ngay neu co loi."""
    db_name = conn_params.get('database', 'quan_ly_phong_kham')
    db_str = build_connection_string(conn_params, db_name)
    migrations_dir = os.path.join(CURRENT_DIR, 'database', 'migrations')

    if not os.path.exists(migrations_dir):
        return True

    print("[*] Dang chay cac kich ban migration tren CSDL hien co...")
    migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])

    conn = pyodbc.connect(db_str, autocommit=True)
    cursor = conn.cursor()

    try:
        for m_file in migration_files:
            m_path = os.path.join(migrations_dir, m_file)
            try:
                with open(m_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Bo qua file chi de review
                if 'REVIEW ONLY' in content:
                    continue

                # Chay cac batch
                batches = re.split(r'^\s*GO\s*$', content, flags=re.MULTILINE | re.IGNORECASE)
                for batch in batches:
                    b_str = batch.strip()
                    if not b_str:
                        continue
                    # Bo qua switch use
                    if b_str.upper().startswith('USE '):
                        b_str = re.sub(r'^\s*USE\s+[^\n;]+;?', '', b_str, flags=re.IGNORECASE).strip()
                    if b_str:
                        cursor.execute(b_str)
                        while cursor.nextset():
                            pass
                print(f"  [OK] Da ap dung ban cap nhat an toan: {m_file}")
            except Exception as e:
                print(f"  [Loi khi chay {m_file}]: {e}")
                return False
    finally:
        conn.close()
    return True

def execute_sql_file(conn_params, sql_path):
    """Thuc thi tep script T-SQL chia tach theo cac khoi lenh GO."""
    if not os.path.exists(sql_path):
        print(f"[Loi] Khong tim thay tep SQL tai: {sql_path}")
        return False

    db_name = conn_params.get('database', 'quan_ly_phong_kham')
    db_str = build_connection_string(conn_params, db_name)

    print(f"[*] Dang nap toan bo cau truc va du lieu tu '{os.path.basename(sql_path)}' vao '{db_name}'...")

    with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
        full_sql = f.read()

    batches = re.split(r'^\s*GO\s*$', full_sql, flags=re.MULTILINE | re.IGNORECASE)
    valid_batches = [b.strip() for b in batches if b.strip()]

    conn = pyodbc.connect(db_str, autocommit=True)
    cursor = conn.cursor()

    total = len(valid_batches)
    success_count = 0

    try:
        for idx, batch in enumerate(valid_batches, 1):
            lines = [l.strip() for l in batch.splitlines() if l.strip() and not l.strip().startswith('--')]
            if not lines:
                continue
            first = lines[0].upper()
            if first.startswith('CREATE DATABASE') or first.startswith('IF NOT EXISTS (SELECT * FROM SYS.DATABASES'):
                continue
            if first.startswith('USE '):
                continue

            try:
                cursor.execute(batch)
                while cursor.nextset():
                    pass
                success_count += 1
                if idx % 5 == 0 or idx == total:
                    print(f"  -> Tien do: [{idx}/{total}] khoi lenh T-SQL da xu ly xong...")
            except Exception as e:
                print(f"[Loi o khoi {idx}/{total}]: {e}")
                print("[Loi] Qua trinh nap SQL da dung. Co so du lieu co the dang o trang thai chua day du.")
                return False
    finally:
        conn.close()

    print(f"[OK] Da thuc thi thanh cong {success_count}/{total} khoi lenh T-SQL!")
    return True

def print_summary(conn_params):
    """In bang tong hop trang thai du lieu sau khi dong bo."""
    tables = check_existing_tables(conn_params)
    db_name = conn_params.get('database', 'quan_ly_phong_kham')
    db_str = build_connection_string(conn_params, db_name)
    sql_file = os.path.join(CURRENT_DIR, 'database', 'cosodulieu.sql')
    required_tables = expected_tables(sql_file)
    missing = {name.lower() for name in required_tables} - {name.lower() for name in tables}
    counts = {}
    count_errors = []

    print("\nKet qua dong bo Co so du lieu Microsoft SQL Server:")
    print(f"  Server instance: {conn_params['server']}")
    print(f"  Driver ODBC:     {conn_params['driver']}")
    print(f"  Database:        {db_name}")
    print(f"  Tong so bang:    {len(tables)} bang (script mau tao {len(required_tables)} bang)")
    if missing:
        print(f"  [Loi] Thieu bang: {', '.join(sorted(missing))}")

    try:
        conn = pyodbc.connect(db_str, autocommit=True)
        try:
            cur = conn.cursor()
            for tbl in sorted(tables):
                try:
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM [{tbl}]")
                    cnt = cur.fetchone()[0]
                    counts[tbl.lower()] = cnt
                    print(f"    + Bang {tbl:22}: {cnt:5d} ban ghi")
                except Exception as error:
                    count_errors.append(f"{tbl}: {error}")
        finally:
            conn.close()
    except Exception as error:
        count_errors.append(str(error))

    empty_essentials = [name for name in ('vai_tro', 'tai_khoan', 'chuyen_khoa', 'bac_si')
                        if name in required_tables and counts.get(name) == 0]
    if count_errors:
        print(f"  [Loi] Khong doc duoc du lieu: {'; '.join(count_errors)}")
    if empty_essentials:
        print(f"  [Loi] Thieu du lieu mau can thiet: {', '.join(empty_essentials)}")
    if missing or count_errors or empty_essentials:
        print("\nCo so du lieu chua day du. Khong khoi chay web cho den khi xu ly xong loi SQL.\n")
        return False
    print("\nHe thong da san sang! Ban co the khoi chay ung dung ngay:")
    print("  python app.py\n")
    return True

def main():
    print("H2T Care+: Cong cu dong bo Co so du lieu tu dong")

    force_fresh = '--fresh' in sys.argv or '--reset' in sys.argv
    check_only = '--check' in sys.argv
    restore_bak = '--restore' in sys.argv
    if sum((force_fresh, check_only, restore_bak)) > 1:
        print("[Loi] Chi chon mot trong cac che do --fresh, --check, --restore.")
        sys.exit(1)

    conn_params = detect_working_connection()
    if not conn_params:
        print("\n[Loi ket noi] Khong the ket noi toi Microsoft SQL Server tren may nay!")
        print("Huong dan khac phuc nhanh:")
        print("  1. Mo Services tren Windows, kiem tra dich vu 'SQL Server (MSSQLSERVER)' hoac 'SQL Server (SQLEXPRESS)' da o trang thai Running.")
        print("  2. Kiem tra may da cai dat Microsoft ODBC Driver 17 hoac 18 for SQL Server chua.")
        print("  3. Mo SQL Server Configuration Manager va bat TCP/IP sang Enabled.")
        sys.exit(1)

    if not check_only:
        update_config_file_if_needed(conn_params)
    if not ensure_database_exists(conn_params, create=not check_only):
        sys.exit(1)

    tables = check_existing_tables(conn_params)
    print(f"[*] Hien co trong CSDL: {len(tables)} bang du lieu.")

    if check_only:
        if not print_summary(conn_params):
            sys.exit(1)
        return

    sql_file = os.path.join(CURRENT_DIR, 'database', 'cosodulieu.sql')

    if restore_bak:
        from models.backup_model import BackupModel
        latest = BackupModel.get_latest_backup()
        if not latest:
            print("[Loi] Khong tim thay tep .bak de phuc hoi. Khong nap de du lieu mau.")
            sys.exit(1)
        print(f"[*] Dang phuc hoi tu ban sao luu moi nhat: {latest}...")
        ok, msg = BackupModel.restore_backup(latest, user_name='sync_tool', create_safety_copy=False)
        if not ok:
            print(f"[Loi] Phuc hoi that bai: {msg}. Co so du lieu hien tai duoc giu nguyen.")
            sys.exit(1)
        print(f"[OK] {msg}")
        if not print_summary(conn_params):
            sys.exit(1)
        return

    if force_fresh:
        if tables:
            print("[*] Che do '--fresh': Dang tao ban sao luu truoc khi xoa du lieu...")
            from models.backup_model import BackupModel
            try:
                ok, msg = BackupModel.create_backup(user_name='before_fresh_sync', cleanup=False)
                if not ok:
                    print(f"[Canh bao] Khong the sao luu: {msg}. Tiep tuc vi da chon --fresh.")
            except Exception as error:
                print(f"[Canh bao] Khong the sao luu: {error}. Tiep tuc vi da chon --fresh.")
        print("[*] Dang lam sach va tao moi toan bo CSDL tu dau theo cosodulieu.sql...")
        if not execute_sql_file(conn_params, sql_file):
            sys.exit(1)
    elif not tables:
        print("[*] CSDL trong. Dang khoi tao day du tu cosodulieu.sql...")
        if not execute_sql_file(conn_params, sql_file):
            sys.exit(1)
    else:
        print("[*] CSDL da co bang. Chi ap dung migrations, khong nap lai du lieu mau.")
        if not run_safe_migrations(conn_params):
            print("[Loi] Dong bo dung lai. Khong chay --fresh neu con du lieu can giu.")
            sys.exit(1)

    if not print_summary(conn_params):
        sys.exit(1)

if __name__ == '__main__':
    main()
