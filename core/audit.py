import json
from datetime import datetime
from core.database import get_db

class AuditLogger:
    """Helper ghi nhận và truy xuất audit trail cho các thao tác hệ thống quan trọng."""

    @staticmethod
    def log(table_name, row_id, action, performed_by=None, performed_by_name=None, reason=None, before_data=None, after_data=None):
        """Ghi nhận vết kiểm toán vào bảng audit_log."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            before_json = json.dumps(before_data, ensure_ascii=False, default=str) if before_data is not None else None
            after_json = json.dumps(after_data, ensure_ascii=False, default=str) if after_data is not None else None
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO audit_log (table_name, row_id, action, performed_by, performed_by_name, performed_at, reason, before_json, after_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (table_name, row_id, action, performed_by, performed_by_name, now_str, reason, before_json, after_json))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[AuditLogger Error] {e}")
            return False

    @staticmethod
    def get_logs(table_name=None, row_id=None, limit=50):
        """Truy vấn lịch sử audit log theo bảng và/hoặc ID bản ghi."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            limit_val = int(limit) if limit else 50
            
            if conn._engine == 'sqlserver':
                sql = f"SELECT TOP {limit_val} * FROM audit_log WHERE 1=1"
            else:
                sql = "SELECT * FROM audit_log WHERE 1=1"
                
            params = []
            if table_name:
                sql += " AND table_name = ?"
                params.append(table_name)
            if row_id is not None:
                sql += " AND row_id = ?"
                params.append(row_id)
                
            sql += " ORDER BY id DESC"
            if conn._engine != 'sqlserver':
                sql += f" LIMIT {limit_val}"

            cursor.execute(sql, tuple(params))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            print(f"[AuditLogger Query Error] {e}")
            return []
