import os

# Cấu hình môi trường và ứng dụng Flask
FLASK_ENV = os.environ.get('FLASK_ENV', 'development').lower()
DEBUG = os.environ.get('FLASK_DEBUG', '1' if FLASK_ENV == 'development' else '0').lower() in ('true', '1', 'yes')

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if FLASK_ENV == 'production':
        raise RuntimeError("CRITICAL SECURITY ERROR: SECRET_KEY must be set in production environment via environment variable!")
    else:
        # Khóa phát triển cục bộ tạm thời - không dùng cho production
        SECRET_KEY = 'dev_insecure_key_for_local_development_only'

# Cấu hình bảo vệ chống CSRF
CSRF_ENABLED = True
WTF_CSRF_ENABLED = True

# Cấu hình hệ quản trị CSDL (Chỉ cần đổi giá trị DB_ENGINE bên dưới)
# DB_ENGINE = 'sqlite'      # Cách 1: SQLite (Tự động nạp CSDL, không cần cài server)
DB_ENGINE = 'sqlserver'     # Cách 2: Microsoft SQL Server (Mặc định)
# DB_ENGINE = 'mysql'       # Cách 3: MySQL / MariaDB (XAMPP / phpMyAdmin)

# 1. Cấu hình SQLite
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phongkham.db')

# 2. Cấu hình Microsoft SQL Server (SSMS)
SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}', # hoặc '{SQL Server}' nếu dùng driver cũ
    'server': os.environ.get('SQL_SERVER_NAME', 'localhost'),  # Hỗ trợ tự động fallback
    'database': 'quan_ly_phong_kham',
    'trusted_connection': 'yes',                 # 'yes' cho Windows Auth, 'no' cho SQL Server Auth
    'uid': 'sa',                                 # Dùng khi trusted_connection = 'no'
    'pwd': 'your_password'
}

# 3. Cấu hình MySQL / MariaDB (XAMPP / phpMyAdmin)
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'quan_ly_phong_kham',
    'charset': 'utf8mb4'
}

# 4. Cấu hình thư mục sao lưu dữ liệu (nằm ngoài public/static)
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

# 5. Cấu hình Email SMTP (Đọc từ biến môi trường, bảo mật thông tin)
SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
SMTP_SENDER_EMAIL = os.environ.get('SMTP_SENDER_EMAIL', os.environ.get('SMTP_USERNAME', ''))
SMTP_SENDER_NAME = os.environ.get('SMTP_SENDER_NAME', 'Phòng Khám Đa Khoa H2T Care')

# 6. Múi giờ hệ thống (Việt Nam UTC+7)
TIMEZONE = 'Asia/Ho_Chi_Minh'

# 7. Cấu hình vị trí phòng khám & Google Maps
CLINIC_ADDRESS = os.environ.get('CLINIC_ADDRESS', '140 Lê Trọng Tấn, Phường Tây Thạnh, Quận Tân Phú, TP. Hồ Chí Minh')
CLINIC_LATITUDE = float(os.environ.get('CLINIC_LATITUDE', '10.806689'))
CLINIC_LONGITUDE = float(os.environ.get('CLINIC_LONGITUDE', '106.628581'))
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')


