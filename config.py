import secrets
import os

# Cấu hình ứng dụng Flask
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
DEBUG = True

# VietQR / bank notification. Leave unset until the clinic configures a real account.
BANK_ID = os.environ.get('BANK_ID', 'MB').strip().upper()
BANK_ACCOUNT_NO = os.environ.get('BANK_ACCOUNT_NO', '0932743258').strip()
BANK_ACCOUNT_NAME = os.environ.get('BANK_ACCOUNT_NAME', 'Phòng Khám Đa Khoa H2T Care').strip()
PAYMENT_WEBHOOK_SECRET = os.environ.get('PAYMENT_WEBHOOK_SECRET', '').strip()

MOBILE_TOKEN_TTL_SECONDS = 3600
MOBILE_TOKEN_SECRET = os.environ.get('MOBILE_TOKEN_SECRET')

# The simulated fixed VND insurance reduction is managed through Admin settings.

# Optional, exact HTTPS host allowlist for server-side image imports. Empty disables remote imports.
IMAGE_DOWNLOAD_ALLOWED_HOSTS = tuple(host.strip().lower() for host in
                                    os.environ.get('IMAGE_DOWNLOAD_ALLOWED_HOSTS', '').split(',') if host.strip())

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
AUTO_RESTORE_ON_STARTUP = os.environ.get('AUTO_RESTORE_ON_STARTUP', 'false').lower() in ('true', '1', 'yes')
AUTO_BACKUP_INTERVAL_HOURS = int(os.environ.get('AUTO_BACKUP_INTERVAL_HOURS', '2'))
AUTO_BACKUP_MAX_KEEP = int(os.environ.get('AUTO_BACKUP_MAX_KEEP', '5'))

# Cấu hình Email SMTP (Bảo mật thông tin gửi mail)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'phmhuy74@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'cbvu odyp uejx yedn')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
SMTP_SENDER_EMAIL = os.environ.get('SMTP_SENDER_EMAIL', os.environ.get('SMTP_USERNAME', 'phmhuy74@gmail.com'))
SMTP_SENDER_NAME = os.environ.get('SMTP_SENDER_NAME', 'Phòng Khám Đa Khoa H2T Care')

# Múi giờ hệ thống (Việt Nam UTC+7)
TIMEZONE = 'Asia/Ho_Chi_Minh'

# Cấu hình vị trí phòng khám và Google Maps
CLINIC_ADDRESS = os.environ.get('CLINIC_ADDRESS', '140 Lê Trọng Tấn, Phường Tây Thạnh, Quận Tân Phú, TP. Hồ Chí Minh')
CLINIC_LATITUDE = float(os.environ.get('CLINIC_LATITUDE', '10.806689'))
CLINIC_LONGITUDE = float(os.environ.get('CLINIC_LONGITUDE', '106.628581'))
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
