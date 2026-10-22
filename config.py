import os

# Cấu hình ứng dụng Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'h2t_healthcare_clinic_secret_key_2026')
DEBUG = True

# Cấu hình hệ quản trị CSDL duy nhất: Microsoft SQL Server
DB_ENGINE = 'sqlserver'

# Cấu hình kết nối Microsoft SQL Server
SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': os.environ.get('SQL_SERVER_NAME', 'localhost'),
    'database': 'quan_ly_phong_kham',
    'trusted_connection': 'yes',
    'uid': 'sa',
    'pwd': 'your_password'
}

# Cấu hình thư mục sao lưu dữ liệu
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

# Cấu hình Email SMTP (Bảo mật thông tin gửi mail)
SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
SMTP_SENDER_EMAIL = os.environ.get('SMTP_SENDER_EMAIL', os.environ.get('SMTP_USERNAME', ''))
SMTP_SENDER_NAME = os.environ.get('SMTP_SENDER_NAME', 'Phòng Khám Đa Khoa H2T Care')

# Múi giờ hệ thống (Việt Nam UTC+7)
TIMEZONE = 'Asia/Ho_Chi_Minh'

# Cấu hình vị trí phòng khám & Google Maps
CLINIC_ADDRESS = os.environ.get('CLINIC_ADDRESS', '140 Lê Trọng Tấn, Phường Tây Thạnh, Quận Tân Phú, TP. Hồ Chí Minh')
CLINIC_LATITUDE = float(os.environ.get('CLINIC_LATITUDE', '10.806689'))
CLINIC_LONGITUDE = float(os.environ.get('CLINIC_LONGITUDE', '106.628581'))
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
