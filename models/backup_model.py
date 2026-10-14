import os
import shutil
import sqlite3
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
import config
from core.database import get_db

class BackupModel:
    """Model quản lý quy trình sao lưu và phục hồi dữ liệu cho SQLite, SQL Server và MySQL."""

    @staticmethod
    def _ensure_backup_dir():
        """Đảm bảo thư mục lưu trữ bản sao lưu tồn tại ngoài public/static."""
        backup_dir = getattr(config, 'BACKUP_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups'))
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @staticmethod
    def get_backup_dir():
        return BackupModel._ensure_backup_dir()

    @staticmethod
    def _log_history(loai_thao_tac, ten_tap_tin, duong_dan, loai_csdl, dung_luong, nguoi_thuc_hien, trang_thai, ghi_chu=''):
        """Ghi nhận lịch sử thao tác sao lưu/phục hồi vào CSDL."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lich_su_sao_luu (loai_thao_tac, ten_tap_tin, duong_dan, loai_csdl, dung_luong, nguoi_thuc_hien, trang_thai, ghi_chu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (loai_thao_tac, ten_tap_tin, duong_dan, loai_csdl, dung_luong, nguoi_thuc_hien, trang_thai, ghi_chu))
            conn.commit()
            conn.close()
        except Exception as e:
            print("[BackupModel] Khong the ghi log vao CSDL:", e)

    @staticmethod
    def list_backups():
        """Lấy danh sách các tệp sao lưu trên đĩa kèm lịch sử thao tác."""
        backup_dir = BackupModel.get_backup_dir()
        files = []
        if os.path.exists(backup_dir):
            for fname in os.listdir(backup_dir):
                fpath = os.path.join(backup_dir, fname)
                if os.path.isfile(fpath) and (fname.endswith('.db') or fname.endswith('.bak') or fname.endswith('.sql')):
                    stat = os.stat(fpath)
                    files.append({
                        'ten_tap_tin': fname,
                        'dung_luong': stat.st_size,
                        'dung_luong_hienthi': f"{stat.st_size / (1024*1024):.2f} MB" if stat.st_size >= 1024*1024 else f"{stat.st_size / 1024:.2f} KB",
                        'thoi_gian_tao': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'loai_csdl': 'sqlite' if fname.endswith('.db') else ('sqlserver' if fname.endswith('.bak') else 'mysql')
                    })

        files.sort(key=lambda x: x['thoi_gian_tao'], reverse=True)

        history = []
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM lich_su_sao_luu ORDER BY id DESC')
            history = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception:
            pass

        return {
            'files': files,
            'history': history,
            'current_engine': getattr(config, 'DB_ENGINE', 'sqlserver'),
            'backup_dir': backup_dir
        }

    @staticmethod
    def create_backup(user_name='admin'):
        """Tạo bản sao lưu tương ứng với hệ CSDL hiện tại."""
        engine = getattr(config, 'DB_ENGINE', 'sqlserver')
        backup_dir = BackupModel.get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. SAO LƯU SQLITE
        if engine == 'sqlite':
            db_file = getattr(config, 'DB_FILE', None)
            if not db_file or not os.path.exists(db_file):
                msg = f"Tệp CSDL SQLite không tồn tại: {db_file}"
                BackupModel._log_history('BACKUP', 'NONE', '', 'sqlite', 0, user_name, 'FAILED', msg)
                return False, msg

            backup_filename = f"backup_sqlite_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            try:
                # Dùng API sqlite3.backup() đảm bảo tính toàn vẹn ngay cả khi có transaction
                src_conn = sqlite3.connect(db_file)
                dst_conn = sqlite3.connect(backup_path)
                with dst_conn:
                    src_conn.backup(dst_conn)
                dst_conn.close()
                src_conn.close()

                size = os.path.getsize(backup_path)
                BackupModel._log_history('BACKUP', backup_filename, backup_path, 'sqlite', size, user_name, 'SUCCESS', 'Sao lưu SQLite thành công.')
                return True, f"Sao lưu SQLite thành công: {backup_filename}"
            except Exception as e:
                msg = f"Lỗi khi sao lưu SQLite: {str(e)}"
                BackupModel._log_history('BACKUP', backup_filename, backup_path, 'sqlite', 0, user_name, 'FAILED', msg)
                return False, msg

        # 2. SAO LƯU SQL SERVER
        elif engine == 'sqlserver':
            backup_filename = f"backup_sqlserver_{timestamp}.bak"
            backup_path = os.path.join(backup_dir, backup_filename)
            cfg = config.SQLSERVER_CONFIG
            db_name = cfg.get('database', 'quan_ly_phong_kham')

            try:
                import pyodbc
                if cfg.get('trusted_connection', 'yes').lower() == 'yes':
                    conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;Trusted_Connection=yes;"
                else:
                    conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;UID={cfg['uid']};PWD={cfg['pwd']};"

                # SQL Server yêu cầu autocommit=True (ngoài transaction) khi BACKUP
                conn = pyodbc.connect(conn_str, autocommit=True)
                cursor = conn.cursor()

                # Lấy thư mục backup mặc định của SQL Server (luôn có quyền ghi)
                default_backup_dir = None
                try:
                    cursor.execute("SELECT CAST(SERVERPROPERTY('InstanceDefaultBackupPath') AS NVARCHAR(512))")
                    row = cursor.fetchone()
                    if row and row[0]:
                        default_backup_dir = str(row[0]).rstrip('\\')
                except Exception:
                    pass

                target_sql_path = os.path.abspath(backup_path)
                backup_success = False
                err_detail = ""

                # Thử backup trực tiếp vào thư mục dự án
                try:
                    cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{target_sql_path}' WITH INIT, FORMAT")
                    while cursor.nextset():
                        pass
                    backup_success = True
                except Exception as ex1:
                    err_detail = str(ex1)
                    # Nếu lỗi quyền và có thư mục backup mặc định của SQL Server
                    if default_backup_dir:
                        alt_path = os.path.join(default_backup_dir, backup_filename)
                        try:
                            cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{alt_path}' WITH INIT, FORMAT")
                            while cursor.nextset():
                                pass
                            # Copy từ alt_path về thư mục backup của app
                            if os.path.exists(alt_path):
                                shutil.copy2(alt_path, target_sql_path)
                            backup_success = True
                            err_detail = ""
                        except Exception as ex2:
                            err_detail = f"Lỗi cả thư mục dự án ({err_detail}) và thư mục mặc định ({str(ex2)})"

                conn.close()




                if backup_success and (os.path.exists(target_sql_path) or (default_backup_dir and os.path.exists(os.path.join(default_backup_dir, backup_filename)))):
                    final_path = target_sql_path if os.path.exists(target_sql_path) else os.path.join(default_backup_dir, backup_filename)
                    size = os.path.getsize(final_path)
                    BackupModel._log_history('BACKUP', backup_filename, final_path, 'sqlserver', size, user_name, 'SUCCESS', 'Sao lưu SQL Server thành công.')
                    return True, f"Sao lưu SQL Server thành công: {backup_filename}"
                else:
                    msg = f"SQL Server không thể tạo file sao lưu: {err_detail}. Vui lòng cấp quyền ghi cho dịch vụ SQL Server (NT Service\\MSSQL$SQLEXPRESS) vào thư mục: {backup_dir}"
                    BackupModel._log_history('BACKUP', backup_filename, target_sql_path, 'sqlserver', 0, user_name, 'FAILED', msg)
                    return False, msg

            except Exception as e:
                msg = f"Lỗi kết nối hoặc thực thi T-SQL Backup: {str(e)}"
                BackupModel._log_history('BACKUP', backup_filename, backup_path, 'sqlserver', 0, user_name, 'FAILED', msg)
                return False, msg


        # 3. SAO LƯU MYSQL
        elif engine == 'mysql':
            backup_filename = f"backup_mysql_{timestamp}.sql"
            backup_path = os.path.join(backup_dir, backup_filename)
            cfg = config.MYSQL_CONFIG

            # Tìm kiếm mysqldump CLI
            mysqldump_candidates = [
                'mysqldump',
                r'C:\xampp\mysql\bin\mysqldump.exe',
                r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe',
                r'C:\Program Files\MariaDB\bin\mysqldump.exe'
            ]
            dump_bin = None
            for cand in mysqldump_candidates:
                if shutil.which(cand) or (os.path.isabs(cand) and os.path.exists(cand)):
                    dump_bin = cand
                    break

            if not dump_bin:
                msg = "Công cụ mysqldump không khả dụng trên hệ thống (không tìm thấy trong PATH hoặc XAMPP). Vui lòng thêm mysqldump vào PATH để sao lưu MySQL."
                BackupModel._log_history('BACKUP', backup_filename, backup_path, 'mysql', 0, user_name, 'FAILED', msg)
                return False, msg

            # Kiểm tra kết nối MySQL server
            try:
                conn = get_db()
                conn.close()
            except Exception as e:
                msg = f"Không thể kết nối MySQL server ({cfg.get('host')}:{cfg.get('port')}): {str(e)}. Hãy đảm bảo dịch vụ MySQL đang chạy."
                BackupModel._log_history('BACKUP', backup_filename, backup_path, 'mysql', 0, user_name, 'FAILED', msg)
                return False, msg

            # Tiến hành dump
            cmd = [
                dump_bin,
                f"--host={cfg.get('host', 'localhost')}",
                f"--port={cfg.get('port', 3306)}",
                f"--user={cfg.get('user', 'root')}",
            ]
            if cfg.get('password'):
                cmd.append(f"--password={cfg['password']}")
            cmd.append(cfg.get('database', 'quan_ly_phong_kham'))

            try:
                with open(backup_path, 'w', encoding='utf-8') as out_f:
                    res = subprocess.run(cmd, stdout=out_f, stderr=subprocess.PIPE, text=True, timeout=60)
                if res.returncode == 0 and os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                    size = os.path.getsize(backup_path)
                    BackupModel._log_history('BACKUP', backup_filename, backup_path, 'mysql', size, user_name, 'SUCCESS', 'Sao lưu MySQL thành công.')
                    return True, f"Sao lưu MySQL thành công: {backup_filename}"
                else:
                    err_msg = res.stderr or "Tệp sao lưu MySQL tạo ra rỗng."
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    BackupModel._log_history('BACKUP', backup_filename, backup_path, 'mysql', 0, user_name, 'FAILED', err_msg)
                    return False, f"Lỗi mysqldump: {err_msg}"
            except Exception as e:
                msg = f"Lỗi khi thực thi mysqldump: {str(e)}"
                BackupModel._log_history('BACKUP', backup_filename, backup_path, 'mysql', 0, user_name, 'FAILED', msg)
                return False, msg

        return False, f"Hệ CSDL '{engine}' không được hỗ trợ."

    @staticmethod
    def restore_backup(filename, user_name='admin', confirm=False):
        """Phục hồi dữ liệu từ bản sao lưu hợp lệ."""
        if not confirm:
            return False, "Yêu cầu xác nhận trước khi thực hiện phục hồi dữ liệu!"

        engine = getattr(config, 'DB_ENGINE', 'sqlserver')
        backup_dir = BackupModel.get_backup_dir()

        safe_filename = secure_filename(filename)
        backup_path = os.path.join(backup_dir, safe_filename)

        # Ngăn chặn path traversal
        if not os.path.exists(backup_path) or not os.path.abspath(backup_path).startswith(os.path.abspath(backup_dir)):
            return False, "Tệp sao lưu không tồn tại hoặc đường dẫn không hợp lệ!"

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. PHỤC HỒI SQLITE
        if engine == 'sqlite':
            if not safe_filename.endswith('.db'):
                return False, "Tệp sao lưu không đúng định dạng SQLite (.db)!"

            db_file = getattr(config, 'DB_FILE', None)
            safety_backup = f"{db_file}.safety_{timestamp}.bak"
            try:
                # Tạo bản sao lưu an toàn của dữ liệu hiện tại trước khi ghi đè
                if os.path.exists(db_file):
                    shutil.copy2(db_file, safety_backup)

                # Kiểm tra tính hợp lệ của file phục hồi
                test_conn = sqlite3.connect(backup_path)
                test_cur = test_conn.cursor()
                test_cur.execute("PRAGMA integrity_check;")
                row = test_cur.fetchone()
                test_conn.close()
                if not row or row[0] != 'ok':
                    return False, "Tệp sao lưu bị lỗi cấu trúc hoặc không nguyên vẹn!"

                # Khôi phục bằng cách copy file
                shutil.copy2(backup_path, db_file)

                # Xóa safety backup sau khi thành công
                if os.path.exists(safety_backup):
                    os.remove(safety_backup)

                size = os.path.getsize(backup_path)
                BackupModel._log_history('RESTORE', safe_filename, backup_path, 'sqlite', size, user_name, 'SUCCESS', 'Phục hồi SQLite thành công.')
                return True, "Phục hồi cơ sở dữ liệu SQLite thành công!"
            except Exception as e:
                # Rollback về safety backup nếu có lỗi
                if os.path.exists(safety_backup) and db_file:
                    shutil.copy2(safety_backup, db_file)
                msg = f"Lỗi phục hồi SQLite: {str(e)}"
                BackupModel._log_history('RESTORE', safe_filename, backup_path, 'sqlite', 0, user_name, 'FAILED', msg)
                return False, msg

        # 2. PHỤC HỒI SQL SERVER
        elif engine == 'sqlserver':
            if not safe_filename.endswith('.bak'):
                return False, "Tệp sao lưu không đúng định dạng SQL Server (.bak)!"

            cfg = config.SQLSERVER_CONFIG
            db_name = cfg.get('database', 'quan_ly_phong_kham')

            try:
                # Trước khi phục hồi, tạo bản sao lưu an toàn tự động
                BackupModel.create_backup(user_name=f"{user_name}_auto_safety")

                # Để khôi phục DB đang dùng, kết nối tới master
                import pyodbc
                if cfg.get('trusted_connection', 'yes').lower() == 'yes':
                    master_conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;Trusted_Connection=yes;"
                else:
                    master_conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;UID={cfg['uid']};PWD={cfg['pwd']};"

                master_conn = pyodbc.connect(master_conn_str, autocommit=True)
                cur = master_conn.cursor()

                target_path = os.path.abspath(backup_path)

                # Chuyển DB sang SINGLE_USER -> RESTORE -> MULTI_USER
                restore_sql = f"""
                ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                RESTORE DATABASE [{db_name}] FROM DISK = '{target_path}' WITH REPLACE;
                ALTER DATABASE [{db_name}] SET MULTI_USER;
                """
                cur.execute(restore_sql)
                while cur.nextset():
                    pass
                master_conn.close()


                size = os.path.getsize(backup_path)
                BackupModel._log_history('RESTORE', safe_filename, target_path, 'sqlserver', size, user_name, 'SUCCESS', 'Phục hồi SQL Server thành công.')
                return True, f"Phục hồi SQL Server thành công từ bản sao lưu {safe_filename}!"

            except Exception as e:
                msg = f"Lỗi khi phục hồi SQL Server: {str(e)}"
                # Cố gắng đưa DB về MULTI_USER phòng trường hợp kẹt ở SINGLE_USER
                try:
                    import pyodbc
                    m_conn = pyodbc.connect(master_conn_str, autocommit=True)
                    m_conn.cursor().execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER;")
                    m_conn.close()
                except Exception:
                    pass
                BackupModel._log_history('RESTORE', safe_filename, backup_path, 'sqlserver', 0, user_name, 'FAILED', msg)
                return False, msg

        # 3. PHỤC HỒI MYSQL
        elif engine == 'mysql':
            if not safe_filename.endswith('.sql'):
                return False, "Tệp sao lưu không đúng định dạng MySQL (.sql)!"

            cfg = config.MYSQL_CONFIG
            mysql_candidates = [
                'mysql',
                r'C:\xampp\mysql\bin\mysql.exe',
                r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe',
                r'C:\Program Files\MariaDB\bin\mysql.exe'
            ]
            mysql_bin = None
            for cand in mysql_candidates:
                if shutil.which(cand) or (os.path.isabs(cand) and os.path.exists(cand)):
                    mysql_bin = cand
                    break

            if not mysql_bin:
                msg = "Công cụ mysql client không khả dụng trong PATH. Vui lòng cấu hình môi trường."
                BackupModel._log_history('RESTORE', safe_filename, backup_path, 'mysql', 0, user_name, 'FAILED', msg)
                return False, msg

            cmd = [
                mysql_bin,
                f"--host={cfg.get('host', 'localhost')}",
                f"--port={cfg.get('port', 3306)}",
                f"--user={cfg.get('user', 'root')}",
            ]
            if cfg.get('password'):
                cmd.append(f"--password={cfg['password']}")
            cmd.append(cfg.get('database', 'quan_ly_phong_kham'))

            try:
                # Tự động tạo bản sao lưu an toàn trước
                BackupModel.create_backup(user_name=f"{user_name}_auto_safety")

                with open(backup_path, 'r', encoding='utf-8') as in_f:
                    res = subprocess.run(cmd, stdin=in_f, stderr=subprocess.PIPE, text=True, timeout=120)

                if res.returncode == 0:
                    size = os.path.getsize(backup_path)
                    BackupModel._log_history('RESTORE', safe_filename, backup_path, 'mysql', size, user_name, 'SUCCESS', 'Phục hồi MySQL thành công.')
                    return True, "Phục hồi cơ sở dữ liệu MySQL thành công!"
                else:
                    err_msg = res.stderr or "Lỗi không xác định khi nạp dữ liệu MySQL."
                    BackupModel._log_history('RESTORE', safe_filename, backup_path, 'mysql', 0, user_name, 'FAILED', err_msg)
                    return False, f"Lỗi mysql import: {err_msg}"

            except Exception as e:
                msg = f"Lỗi khi thực thi mysql restore: {str(e)}"
                BackupModel._log_history('RESTORE', safe_filename, backup_path, 'mysql', 0, user_name, 'FAILED', msg)
                return False, msg

        return False, f"Hệ CSDL '{engine}' không được hỗ trợ."
