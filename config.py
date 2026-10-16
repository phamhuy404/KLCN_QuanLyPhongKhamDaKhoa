import os

# Cấu hình ứng dụng Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'h2t_healthcare_clinic_secret_key_2026')
DEBUG = True

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

