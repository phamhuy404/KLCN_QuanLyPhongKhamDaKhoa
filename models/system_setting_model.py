import os
import json
from datetime import datetime
from core.database import get_db

class SystemSettingModel:
    """Model quản lý cấu hình và trạng thái bảo trì toàn hệ thống."""

    _cache = None
    _CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'system_settings.json')

    DEFAULT_SETTINGS = {
        'maintenance_patient': False,
        'maintenance_staff': False,
        'maintenance_message_patient': 'Cổng Dịch vụ Bệnh nhân H2T Care+ đang được nâng cấp tính năng và bảo trì định kỳ. Quý khách vui lòng quay lại sau.',
        'maintenance_message_staff': 'Phân hệ Quản lý Y tế Nội bộ đang tạm dừng để bảo trì nâng cấp máy chủ và đồng bộ cơ sở dữ liệu. Vui lòng thực hiện quy trình giấy khẩn cấp.',
        'maintenance_eta': '23:00 Hôm nay',
        'maintenance_hotline': '1900 1234 - (028) 3810 0000',
        'updated_at': None,
        'updated_by': 'system'
    }

    @classmethod
    def _ensure_table(cls):
        """Khởi tạo bảng cai_dat_he_thong trong SQL Server nếu chưa tồn tại."""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'cai_dat_he_thong')
                BEGIN
                    CREATE TABLE cai_dat_he_thong (
                        khoa NVARCHAR(100) PRIMARY KEY,
                        gia_tri NVARCHAR(MAX),
                        mo_ta NVARCHAR(255),
                        cap_nhat_luc DATETIME DEFAULT GETDATE(),
                        nguoi_cap_nhat NVARCHAR(100) DEFAULT 'admin'
                    );
                END
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            # Ghi nhận ngoại lệ nhẹ nếu không kết nối được CSDL
            pass

    @classmethod
    def _read_file_cache(cls):
        """Đọc cài đặt từ tệp JSON dự phòng."""
        try:
            if os.path.exists(cls._CACHE_FILE):
                with open(cls._CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    res = cls.DEFAULT_SETTINGS.copy()
                    res.update(data)
                    return res
        except Exception:
            pass
        return cls.DEFAULT_SETTINGS.copy()

    @classmethod
    def _write_file_cache(cls, data):
        """Ghi cài đặt ra tệp JSON dự phòng để đọc tức thì không nghẽn CSDL."""
        try:
            os.makedirs(os.path.dirname(cls._CACHE_FILE), exist_ok=True)
            with open(cls._CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def get_settings(cls, force_reload=False):
        """Lấy toàn bộ cấu hình hệ thống từ bộ nhớ đệm hoặc CSDL."""
        if cls._cache and not force_reload:
            return cls._cache.copy()

        settings = cls.DEFAULT_SETTINGS.copy()
        file_data = cls._read_file_cache()
        settings.update(file_data)

        try:
            cls._ensure_table()
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT khoa, gia_tri FROM cai_dat_he_thong")
            rows = cur.fetchall()
            conn.close()

            for row in rows:
                k = row.get('khoa')
                v = row.get('gia_tri')
                if k in ('maintenance_patient', 'maintenance_staff'):
                    settings[k] = (v == '1' or v.lower() == 'true')
                elif k:
                    settings[k] = v
        except Exception:
            # Khi CSDL bận, dùng giá trị từ file cache
            pass

        cls._cache = settings.copy()
        return settings

    @classmethod
    def update_settings(cls, new_settings, user_name='admin'):
        """Cập nhật cài đặt hệ thống vào cả CSDL và bộ nhớ đệm."""
        cls._ensure_table()
        current = cls.get_settings()
        current.update(new_settings)
        current['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current['updated_by'] = user_name

        try:
            conn = get_db()
            cur = conn.cursor()
            now_str = current['updated_at']

            for k, v in current.items():
                if k in ('updated_at', 'updated_by'):
                    continue
                str_val = '1' if v is True else ('0' if v is False else str(v or ''))
                cur.execute("""
                    IF EXISTS (SELECT 1 FROM cai_dat_he_thong WHERE khoa = ?)
                        UPDATE cai_dat_he_thong 
                        SET gia_tri = ?, cap_nhat_luc = ?, nguoi_cap_nhat = ? 
                        WHERE khoa = ?
                    ELSE
                        INSERT INTO cai_dat_he_thong (khoa, gia_tri, cap_nhat_luc, nguoi_cap_nhat) 
                        VALUES (?, ?, ?, ?)
                """, (k, str_val, now_str, user_name, k, k, str_val, now_str, user_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print("[SystemSettingModel] Cảnh báo lỗi lưu CSDL:", e)

        cls._write_file_cache(current)
        cls._cache = current.copy()
        return True, "Cập nhật cấu hình hệ thống thành công!"

    @classmethod
    def toggle_maintenance(cls, target='patient', enabled=None, user_name='admin'):
        """Bật hoặc tắt trạng thái bảo trì cho phân hệ tương ứng."""
        settings = cls.get_settings()
        key = 'maintenance_patient' if target == 'patient' else 'maintenance_staff'
        
        if enabled is None:
            settings[key] = not settings.get(key, False)
        else:
            settings[key] = bool(enabled)

        ok, msg = cls.update_settings(settings, user_name=user_name)
        status_text = "ĐÃ BẬT" if settings[key] else "ĐÃ TẮT"
        target_text = "Cổng Bệnh nhân" if target == 'patient' else "Phân hệ Nhân viên"
        return ok, f"{status_text} chế độ bảo trì cho {target_text} thành công!"
