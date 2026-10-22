import os
import shutil
import pyodbc
from datetime import datetime
from werkzeug.utils import secure_filename
import config
from core.database import get_db

class BackupModel:
    """Model quản lý quy trình sao lưu và phục hồi dữ liệu chuyên biệt cho Microsoft SQL Server."""

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
                if os.path.isfile(fpath) and fname.endswith('.bak'):
                    stat = os.stat(fpath)
                    files.append({
                        'ten_tap_tin': fname,
                        'dung_luong': stat.st_size,
                        'dung_luong_hienthi': f"{stat.st_size / (1024*1024):.2f} MB" if stat.st_size >= 1024*1024 else f"{stat.st_size / 1024:.2f} KB",
                        'thoi_gian_tao': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'loai_csdl': 'sqlserver'
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
            'current_engine': 'sqlserver',
            'backup_dir': backup_dir
        }

    @staticmethod
    def create_backup(user_name='admin'):
        """Tạo bản sao lưu cho Microsoft SQL Server (.bak)."""
        backup_dir = BackupModel.get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_sqlserver_{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)
        cfg = config.SQLSERVER_CONFIG
        db_name = cfg.get('database', 'quan_ly_phong_kham')

        try:
            if cfg.get('trusted_connection', 'yes').lower() == 'yes':
                conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;Trusted_Connection=yes;"
            else:
                conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;UID={cfg['uid']};PWD={cfg['pwd']};"

            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()

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

            try:
                cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{target_sql_path}' WITH INIT, FORMAT")
                while cursor.nextset():
                    pass
                backup_success = True
            except Exception as ex1:
                err_detail = str(ex1)
                if default_backup_dir:
                    alt_path = os.path.join(default_backup_dir, backup_filename)
                    try:
                        cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{alt_path}' WITH INIT, FORMAT")
                        while cursor.nextset():
                            pass
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
                msg = f"SQL Server không thể tạo file sao lưu: {err_detail}. Vui lòng cấp quyền ghi cho dịch vụ SQL Server vào thư mục: {backup_dir}"
                BackupModel._log_history('BACKUP', backup_filename, target_sql_path, 'sqlserver', 0, user_name, 'FAILED', msg)
                return False, msg

        except Exception as e:
            msg = f"Lỗi kết nối hoặc thực thi T-SQL Backup: {str(e)}"
            BackupModel._log_history('BACKUP', backup_filename, backup_path, 'sqlserver', 0, user_name, 'FAILED', msg)
            return False, msg

    @staticmethod
    def restore_backup(filename, user_name='admin'):
        """Phục hồi CSDL Microsoft SQL Server từ tệp .bak."""
        backup_dir = BackupModel.get_backup_dir()
        safe_filename = secure_filename(filename)
        backup_path = os.path.join(backup_dir, safe_filename)

        if not os.path.exists(backup_path):
            return False, f"Tệp sao lưu không tồn tại: {safe_filename}"

        if not safe_filename.endswith('.bak'):
            return False, "Tệp sao lưu không đúng định dạng SQL Server (.bak)!"

        cfg = config.SQLSERVER_CONFIG
        db_name = cfg.get('database', 'quan_ly_phong_kham')

        try:
            BackupModel.create_backup(user_name=f"{user_name}_auto_safety")

            if cfg.get('trusted_connection', 'yes').lower() == 'yes':
                master_conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;Trusted_Connection=yes;"
            else:
                master_conn_str = f"DRIVER={cfg['driver']};SERVER={cfg['server']};DATABASE=master;UID={cfg['uid']};PWD={cfg['pwd']};"

            master_conn = pyodbc.connect(master_conn_str, autocommit=True)
            cur = master_conn.cursor()

            target_path = os.path.abspath(backup_path)

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
            try:
                m_conn = pyodbc.connect(master_conn_str, autocommit=True)
                m_conn.cursor().execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER;")
                m_conn.close()
            except Exception:
                pass
            BackupModel._log_history('RESTORE', safe_filename, backup_path, 'sqlserver', 0, user_name, 'FAILED', msg)
            return False, msg

    @staticmethod
    def delete_backup(filename, user_name='admin'):
        """Xóa một bản sao lưu an toàn khỏi đĩa cứng."""
        backup_dir = BackupModel.get_backup_dir()
        safe_filename = secure_filename(filename)
        backup_path = os.path.join(backup_dir, safe_filename)

        if not os.path.exists(backup_path):
            return False, "Tệp sao lưu không tồn tại!"

        try:
            size = os.path.getsize(backup_path)
            os.remove(backup_path)
            BackupModel._log_history('DELETE', safe_filename, backup_path, 'sqlserver', size, user_name, 'SUCCESS', 'Đã xóa tệp sao lưu.')
            return True, f"Đã xóa thành công tệp sao lưu {safe_filename}!"
        except Exception as e:
            return False, f"Lỗi khi xóa tệp: {str(e)}"
