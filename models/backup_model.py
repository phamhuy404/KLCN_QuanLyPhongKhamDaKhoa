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
    def _sql_literal(value):
        return "N'" + str(value).replace("'", "''") + "'"

    @staticmethod
    def _restore_file_moves(cursor, backup_path, db_name):
        """Map each file in the backup onto this database's existing file path."""
        cursor.execute(f"RESTORE FILELISTONLY FROM DISK = {BackupModel._sql_literal(backup_path)}")
        columns = {column[0]: index for index, column in enumerate(cursor.description)}
        backup_files = [(row[columns['LogicalName']], row[columns['Type']])
                        for row in cursor.fetchall()]

        cursor.execute(
            "SELECT type, physical_name FROM sys.master_files "
            "WHERE database_id = DB_ID(?) ORDER BY file_id", (db_name,)
        )
        destination_files = list(cursor.fetchall())
        if not destination_files:
            raise ValueError(f"Không tìm thấy tệp dữ liệu hiện tại của {db_name} trên SQL Server này.")

        # A different file layout needs an explicit DBA decision; never guess a new path.
        locations = {'D': [], 'L': []}
        for file_type, physical_name in destination_files:
            if file_type not in (0, 1):
                raise ValueError('CSDL đích có loại tệp đặc biệt; cần khôi phục thủ công bằng SSMS.')
            locations['D' if file_type == 0 else 'L'].append(physical_name)

        moves = []
        for logical_name, file_type in backup_files:
            if file_type not in locations or not locations[file_type]:
                raise ValueError('Số lượng hoặc loại tệp trong bản sao lưu khác CSDL đích; cần khôi phục thủ công bằng SSMS.')
            destination = locations[file_type].pop(0)
            moves.append(f"MOVE {BackupModel._sql_literal(logical_name)} TO {BackupModel._sql_literal(destination)}")
        if not moves or any(locations.values()):
            raise ValueError('Số lượng tệp trong bản sao lưu khác CSDL đích; cần khôi phục thủ công bằng SSMS.')
        return moves

    @staticmethod
    def _connect_master():
        """Use the SQL Server instance already selected by the application."""
        cfg = config.SQLSERVER_CONFIG
        server = cfg['server']
        try:
            db_conn = get_db()
            try:
                server = getattr(db_conn, 'server', None) or server
            finally:
                db_conn.close()
        except Exception:
            # Restoring a missing database still needs access to master.
            pass

        if cfg.get('trusted_connection', 'yes').lower() == 'yes':
            conn_str = f"DRIVER={cfg['driver']};SERVER={server};DATABASE=master;Trusted_Connection=yes;"
        else:
            conn_str = f"DRIVER={cfg['driver']};SERVER={server};DATABASE=master;UID={cfg['uid']};PWD={cfg['pwd']};"
        return pyodbc.connect(conn_str, autocommit=True, timeout=5)

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
                if os.path.isfile(fpath) and (fname.endswith('.bak') or fname.endswith('.zip')):
                    stat = os.stat(fpath)
                    is_zip = fname.endswith('.zip')
                    files.append({
                        'ten_tap_tin': fname,
                        'dung_luong': stat.st_size,
                        'dung_luong_hienthi': f"{stat.st_size / (1024*1024):.2f} MB" if stat.st_size >= 1024*1024 else f"{stat.st_size / 1024:.2f} KB",
                        'thoi_gian_tao': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'loai_csdl': 'Toàn hệ thống (CSDL + Ảnh y tế)' if is_zip else 'sqlserver'
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
    def create_backup(user_name='admin', cleanup=True):
        """Tạo bản sao lưu cho Microsoft SQL Server (.bak)."""
        backup_dir = BackupModel.get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_filename = f"backup_sqlserver_{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)
        cfg = config.SQLSERVER_CONFIG
        db_name = cfg.get('database', 'quan_ly_phong_kham')

        try:
            conn = BackupModel._connect_master()
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
                try:
                    cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{target_sql_path}' WITH INIT, FORMAT, COMPRESSION")
                except Exception:
                    cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{target_sql_path}' WITH INIT, FORMAT")
                while cursor.nextset():
                    pass
                backup_success = True
            except Exception as ex1:
                err_detail = str(ex1)
                if default_backup_dir:
                    alt_path = os.path.join(default_backup_dir, backup_filename)
                    try:
                        try:
                            cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{alt_path}' WITH INIT, FORMAT, COMPRESSION")
                        except Exception:
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
                
                # Nén cả file .bak và thư mục private_uploads/ thành tệp .zip hoàn chỉnh
                import zipfile
                zip_filename = f"backup_full_system_{timestamp}.zip"
                zip_path = os.path.join(backup_dir, zip_filename)
                saved_file_name = backup_filename
                saved_path = final_path
                size = os.path.getsize(final_path)
                try:
                    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                        zf.write(final_path, arcname=os.path.basename(final_path))
                        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        upload_dir = os.path.join(proj_root, 'private_uploads')
                        if os.path.exists(upload_dir):
                            for root, _, files_in_dir in os.walk(upload_dir):
                                for f_item in files_in_dir:
                                    abs_file = os.path.join(root, f_item)
                                    rel_file = os.path.relpath(abs_file, proj_root)
                                    zf.write(abs_file, arcname=rel_file)
                    saved_file_name = zip_filename
                    saved_path = zip_path
                    size = os.path.getsize(zip_path)
                except Exception as z_err:
                    print("[BackupModel] Zip creation warning, fallback to .bak:", z_err)

                BackupModel._log_history('BACKUP', saved_file_name, saved_path, 'sqlserver', size, user_name, 'SUCCESS', 'Sao lưu toàn bộ hệ thống (CSDL và Ảnh y tế) thành công.')
                max_keep = getattr(config, 'AUTO_BACKUP_MAX_KEEP', 5)
                if cleanup:
                    BackupModel.cleanup_old_backups(keep=max_keep)
                return True, f"Sao lưu toàn bộ hệ thống thành công: {saved_file_name}"
            else:
                msg = f"SQL Server không thể tạo file sao lưu: {err_detail}. Vui lòng cấp quyền ghi cho dịch vụ SQL Server vào thư mục: {backup_dir}"
                BackupModel._log_history('BACKUP', backup_filename, target_sql_path, 'sqlserver', 0, user_name, 'FAILED', msg)
                return False, msg

        except Exception as e:
            msg = f"Lỗi kết nối hoặc thực thi T-SQL Backup: {str(e)}"
            BackupModel._log_history('BACKUP', backup_filename, backup_path, 'sqlserver', 0, user_name, 'FAILED', msg)
            return False, msg

    @staticmethod
    def get_latest_backup():
        """Lấy tên tệp sao lưu .bak mới nhất trong thư mục backups."""
        backup_dir = BackupModel.get_backup_dir()
        if not os.path.exists(backup_dir):
            return None
        bak_files = [
            f for f in os.listdir(backup_dir)
            if (f.endswith('.bak') or f.endswith('.zip')) and os.path.isfile(os.path.join(backup_dir, f))
        ]
        if not bak_files:
            return None
        bak_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        return bak_files[0]

    @staticmethod
    def cleanup_old_backups(keep=5):
        """Giữ lại tối đa N bản sao lưu gần nhất để tiết kiệm dung lượng đĩa."""
        backup_dir = BackupModel.get_backup_dir()
        if not os.path.exists(backup_dir):
            return 0
        bak_files = [
            f for f in os.listdir(backup_dir)
            if f.endswith('.bak') and os.path.isfile(os.path.join(backup_dir, f))
        ]
        if len(bak_files) <= keep:
            return 0
        bak_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        to_delete = bak_files[keep:]
        deleted_count = 0
        for f in to_delete:
            try:
                os.remove(os.path.join(backup_dir, f))
                deleted_count += 1
            except Exception:
                pass
        return deleted_count

    @staticmethod
    def restore_backup(filename, user_name='admin', create_safety_copy=True, **kwargs):
        """Phục hồi CSDL Microsoft SQL Server từ tệp .bak."""
        backup_dir = BackupModel.get_backup_dir()
        safe_filename = secure_filename(filename)
        backup_path = os.path.join(backup_dir, safe_filename)

        if not os.path.exists(backup_path):
            return False, f"Tệp sao lưu không tồn tại: {safe_filename}"

        is_zip = safe_filename.endswith('.zip')
        if not safe_filename.endswith('.bak') and not is_zip:
            return False, "Tệp sao lưu không đúng định dạng SQL Server (.bak hoặc .zip)!"

        actual_bak_path = backup_path
        temp_extracted_bak = None
        if is_zip:
            import zipfile
            try:
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    bak_names = [n for n in zf.namelist() if n.endswith('.bak')]
                    if not bak_names:
                        return False, "Tệp zip không chứa tệp sao lưu CSDL (.bak)!"
                    temp_extracted_bak = zf.extract(bak_names[0], path=backup_dir)
                    actual_bak_path = temp_extracted_bak

                    # Khôi phục toàn bộ thư mục ảnh y tế private_uploads
                    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    for member in zf.namelist():
                        if member.startswith('private_uploads/') or member.startswith('private_uploads\\'):
                            zf.extract(member, path=proj_root)
            except Exception as ze:
                return False, f"Không thể giải nén tệp sao lưu zip: {str(ze)}"

        cfg = config.SQLSERVER_CONFIG
        db_name = cfg.get('database', 'quan_ly_phong_kham')

        master_conn = None
        restore_started = False
        try:
            master_conn = BackupModel._connect_master()
            cur = master_conn.cursor()

            target_path = os.path.abspath(actual_bak_path)
            moves = BackupModel._restore_file_moves(cur, target_path, db_name)

            if create_safety_copy:
                safety_ok, safety_msg = BackupModel.create_backup(user_name=f"{user_name}_auto_safety", cleanup=False)
                if not safety_ok:
                    return False, f"Không thể phục hồi vì bản sao lưu dự phòng thất bại: {safety_msg}"

            restore_sql = f"""
            ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            RESTORE DATABASE [{db_name}] FROM DISK = {BackupModel._sql_literal(target_path)}
            WITH REPLACE, {', '.join(moves)};
            ALTER DATABASE [{db_name}] SET MULTI_USER;
            """
            restore_started = True
            cur.execute(restore_sql)
            while cur.nextset():
                pass

            size = os.path.getsize(backup_path)
            BackupModel._log_history('RESTORE', safe_filename, target_path, 'sqlserver', size, user_name, 'SUCCESS', 'Phục hồi SQL Server thành công.')
            return True, f"Phục hồi SQL Server thành công từ bản sao lưu {safe_filename}!"

        except Exception as e:
            msg = f"Lỗi khi phục hồi SQL Server: {str(e)}"
            if restore_started:
                try:
                    recovery_conn = master_conn or BackupModel._connect_master()
                    recovery_conn.cursor().execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER;")
                    if recovery_conn is not master_conn:
                        recovery_conn.close()
                except Exception:
                    pass
            BackupModel._log_history('RESTORE', safe_filename, backup_path, 'sqlserver', 0, user_name, 'FAILED', msg)
            return False, msg
        finally:
            if master_conn is not None:
                master_conn.close()

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

    @staticmethod
    def start_auto_backup_scheduler(interval_hours=2):
        """Khởi chạy tiến trình tự động sao lưu CSDL định kỳ trong background thread."""
        import threading
        import time
        from flask import current_app, has_app_context

        if has_app_context() and (current_app.testing or not current_app.config.get('DATABASE_ACCESS_ENABLED', True)):
            return None

        debug = current_app.debug if has_app_context() else getattr(config, 'DEBUG', False)
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and debug:
            return None

        if interval_hours <= 0:
            return None

        def _worker():
            def _safe_log(msg):
                try:
                    print(msg)
                except Exception:
                    try:
                        print(msg.encode('ascii', 'replace').decode('ascii'))
                    except Exception:
                        pass
            _safe_log(f"[BackupScheduler] Tien trinh tu dong sao luu da kich hoat (chu ky {interval_hours} tieng).")
            while True:
                time.sleep(interval_hours * 3600)
                try:
                    ok, msg = BackupModel.create_backup(user_name='auto_scheduler_2h')
                    if ok:
                        _safe_log(f"[BackupScheduler] Da tu dong tao ban sao luu: {msg}")
                        max_keep = getattr(config, 'AUTO_BACKUP_MAX_KEEP', 20)
                        del_cnt = BackupModel.cleanup_old_backups(keep=max_keep)
                        if del_cnt > 0:
                            _safe_log(f"[BackupScheduler] Da don dep {del_cnt} ban sao luu cu.")
                    else:
                        _safe_log(f"[BackupScheduler] Tu dong sao luu that bai: {msg}")
                except Exception as e:
                    _safe_log(f"[BackupScheduler] Loi trong tien trinh sao luu ngam: {e}")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t
