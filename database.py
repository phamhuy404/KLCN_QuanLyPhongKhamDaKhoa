import os
import sqlite3
from datetime import datetime, date, time
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash

# Cấu hình hệ quản trị CSDL (Chỉ cần mở comment 1 dòng DB_ENGINE tương ứng để chuyển đổi)
# DB_ENGINE = 'sqlite'      # Cách 1: SQLite (Tự động nạp CSDL, không cần cài server)
DB_ENGINE = 'sqlserver'     # Cách 2: Microsoft SQL Server (Mặc định)
# DB_ENGINE = 'mysql'       # Cách 3: MySQL / MariaDB (XAMPP / phpMyAdmin)

# 1. Cấu hình SQLite
DB_FILE = os.path.join(os.path.dirname(__file__), 'phongkham.db')

# 2. Cấu hình Microsoft SQL Server (SSMS)
SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}', # hoặc '{SQL Server}' nếu dùng bản cũ
    'server': 'localhost',                       # hoặc '.\\SQLEXPRESS'
    'database': 'quan_ly_phong_kham',
    'trusted_connection': 'yes',                 # 'yes' cho Windows Auth, 'no' cho SQL Auth
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

class UnifiedCursor:
    def __init__(self, raw_cursor, engine):
        self._cur = raw_cursor
        self._engine = engine
        self.lastrowid = None

    def execute(self, sql, params=()):
        if self._engine == 'mysql':
            sql = sql.replace('?', '%s')
        if params:
            self._cur.execute(sql, params)
        else:
            self._cur.execute(sql)

        if self._engine == 'sqlserver' and sql.strip().upper().startswith('INSERT'):
            try:
                self._cur.execute('SELECT @@IDENTITY')
                row = self._cur.fetchone()
                self.lastrowid = int(row[0]) if row and row[0] is not None else None
            except Exception:
                self.lastrowid = None
        else:
            self.lastrowid = getattr(self._cur, 'lastrowid', None)
        return self

    def executemany(self, sql, seq_of_params):
        if self._engine == 'mysql':
            sql = sql.replace('?', '%s')
        return self._cur.executemany(sql, seq_of_params)

    def _convert_row(self, row):
        if row is None:
            return None
        if isinstance(row, dict):
            return {k: self._clean_val(v) for k, v in row.items()}
        if hasattr(row, 'keys'):
            return {k: self._clean_val(row[k]) for k in row.keys()}
        cols = [c[0] for c in self._cur.description]
        return {cols[i]: self._clean_val(row[i]) for i in range(len(cols))}

    @staticmethod
    def _clean_val(v):
        if v is None:
            return None
        if isinstance(v, (datetime, date, time)):
            return str(v)
        if isinstance(v, Decimal):
            return float(v)
        return v

    def fetchone(self):
        return self._convert_row(self._cur.fetchone())

    def fetchall(self):
        return [self._convert_row(r) for r in self._cur.fetchall()]

    def __iter__(self):
        for r in self.fetchall():
            yield r

class UnifiedConnection:
    def __init__(self, raw_conn, engine):
        self._conn = raw_conn
        self._engine = engine

    def cursor(self):
        if self._engine == 'mysql':
            import pymysql.cursors
            return UnifiedCursor(self._conn.cursor(pymysql.cursors.DictCursor), self._engine)
        return UnifiedCursor(self._conn.cursor(), self._engine)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

def get_db():
    """Tạo kết nối tới CSDL theo DB_ENGINE được chỉ định."""
    if DB_ENGINE == 'sqlite':
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return UnifiedConnection(conn, 'sqlite')
    elif DB_ENGINE == 'sqlserver':
        import pyodbc
        if SQLSERVER_CONFIG.get('trusted_connection', 'yes').lower() == 'yes':
            conn_str = (
                f"DRIVER={SQLSERVER_CONFIG['driver']};"
                f"SERVER={SQLSERVER_CONFIG['server']};"
                f"DATABASE={SQLSERVER_CONFIG['database']};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={SQLSERVER_CONFIG['driver']};"
                f"SERVER={SQLSERVER_CONFIG['server']};"
                f"DATABASE={SQLSERVER_CONFIG['database']};"
                f"UID={SQLSERVER_CONFIG['uid']};"
                f"PWD={SQLSERVER_CONFIG['pwd']};"
            )
        conn = pyodbc.connect(conn_str)
        return UnifiedConnection(conn, 'sqlserver')
    elif DB_ENGINE == 'mysql':
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG.get('port', 3306),
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            charset=MYSQL_CONFIG.get('charset', 'utf8mb4'),
            autocommit=False
        )
        return UnifiedConnection(conn, 'mysql')
    else:
        raise ValueError(f"Hệ CSDL không hợp lệ: {DB_ENGINE}")

def init_sqlite_db():
    """Khởi tạo toàn bộ cấu trúc bảng và nạp dữ liệu mẫu ban đầu cho SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Tạo các bảng cơ sở dữ liệu
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS vai_tro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_vai_tro TEXT NOT NULL UNIQUE,
        ten_vai_tro TEXT NOT NULL,
        mo_ta TEXT
    );

    CREATE TABLE IF NOT EXISTS chuyen_khoa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_khoa TEXT NOT NULL UNIQUE,
        ten_khoa TEXT NOT NULL,
        mo_ta TEXT,
        icon TEXT DEFAULT 'fa-stethoscope',
        gia_kham_mac_dinh REAL DEFAULT 150000.0
    );

    CREATE TABLE IF NOT EXISTS phong_kham (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chuyen_khoa_id INTEGER NOT NULL,
        ma_phong TEXT NOT NULL UNIQUE,
        ten_phong TEXT NOT NULL,
        vi_tri_tang TEXT DEFAULT 'Tầng 1',
        trang_thai INTEGER DEFAULT 1,
        FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
    );

    CREATE TABLE IF NOT EXISTS dich_vu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chuyen_khoa_id INTEGER,
        ma_dich_vu TEXT NOT NULL UNIQUE,
        ten_dich_vu TEXT NOT NULL,
        loai_dich_vu TEXT DEFAULT 'Khám bệnh',
        don_gia REAL NOT NULL DEFAULT 0.0,
        bhyt_chi_tra_pt INTEGER DEFAULT 0,
        mo_ta TEXT,
        FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id)
    );

    CREATE TABLE IF NOT EXISTS thuoc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_thuoc TEXT NOT NULL UNIQUE,
        ten_thuoc TEXT NOT NULL,
        hoat_chat TEXT,
        ham_luong TEXT,
        don_vi_tinh TEXT NOT NULL,
        don_gia REAL NOT NULL DEFAULT 0.0,
        so_luong_ton INTEGER DEFAULT 0,
        hang_san_xuat TEXT,
        nuoc_san_xuat TEXT,
        huong_dan_su_dung TEXT,
        trang_thai INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS tai_khoan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vai_tro_id INTEGER NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        email TEXT,
        sdt TEXT,
        trang_thai INTEGER DEFAULT 1,
        ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
        lan_dang_nhap_cuoi DATETIME,
        FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id)
    );

    CREATE TABLE IF NOT EXISTS nhan_vien (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tai_khoan_id INTEGER NOT NULL UNIQUE,
        ma_nhan_vien TEXT NOT NULL UNIQUE,
        ho_ten TEXT NOT NULL,
        gioi_tinh INTEGER DEFAULT 1,
        ngay_sinh DATE,
        sdt TEXT NOT NULL UNIQUE,
        email TEXT,
        cccd TEXT UNIQUE,
        dia_chi TEXT,
        chuc_vu TEXT NOT NULL,
        ngay_vao_lam DATE DEFAULT (CURRENT_DATE),
        trang_thai INTEGER DEFAULT 1,
        FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
    );

    CREATE TABLE IF NOT EXISTS bac_si (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nhan_vien_id INTEGER NOT NULL UNIQUE,
        chuyen_khoa_id INTEGER NOT NULL,
        phong_kham_chinh_id INTEGER,
        hoc_vi TEXT DEFAULT 'Bác sĩ',
        kinh_nghiem TEXT,
        avatar TEXT DEFAULT 'default_doctor.png',
        gia_kham REAL DEFAULT 150000.0,
        trang_thai_lam_viec TEXT DEFAULT 'Đang làm việc',
        FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
        FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
        FOREIGN KEY (phong_kham_chinh_id) REFERENCES phong_kham(id)
    );

    CREATE TABLE IF NOT EXISTS benh_nhan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tai_khoan_id INTEGER UNIQUE,
        ma_benh_nhan TEXT NOT NULL UNIQUE,
        ho_ten TEXT NOT NULL,
        ngay_sinh DATE NOT NULL,
        gioi_tinh TEXT NOT NULL DEFAULT 'Nam',
        sdt TEXT NOT NULL,
        email TEXT,
        cccd TEXT,
        bhyt TEXT,
        dia_chi TEXT,
        nhom_mau TEXT DEFAULT 'Chưa rõ',
        di_ung TEXT,
        tien_su_benh TEXT,
        tien_su_gia_dinh TEXT,
        nguoi_than_ho_ten TEXT,
        nguoi_than_sdt TEXT,
        nguoi_than_quan_he TEXT,
        co_tai_khoan INTEGER DEFAULT 0,
        ngay_tao DATE DEFAULT (CURRENT_DATE),
        FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
    );

    CREATE TABLE IF NOT EXISTS chi_so_sinh_ton (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        benh_nhan_id INTEGER NOT NULL,
        mach TEXT DEFAULT '75 lần/phút',
        nhiet_do TEXT DEFAULT '36.8 °C',
        huyet_ap TEXT DEFAULT '120/80 mmHg',
        spo2 TEXT DEFAULT '99 %',
        nhip_tho TEXT DEFAULT '18 lần/phút',
        chieu_cao TEXT DEFAULT '170 cm',
        can_nang TEXT DEFAULT '65 kg',
        bmi TEXT DEFAULT '22.5 (Bình thường)',
        thoi_gian_do DATETIME DEFAULT CURRENT_TIMESTAMP,
        ghi_chu TEXT,
        FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id)
    );

    CREATE TABLE IF NOT EXISTS lich_lam_viec (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bac_si_id INTEGER NOT NULL,
        phong_kham_id INTEGER NOT NULL,
        ngay_lam DATE NOT NULL,
        ca_lam INTEGER NOT NULL,
        gio_bat_dau TIME DEFAULT '07:00:00',
        gio_ket_thuc TIME DEFAULT '11:30:00',
        so_luong_kham_toi_da INTEGER DEFAULT 20,
        so_luong_da_dang_ky INTEGER DEFAULT 0,
        FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
        FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
    );

    CREATE TABLE IF NOT EXISTS lich_hen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_lich_hen TEXT NOT NULL UNIQUE,
        benh_nhan_id INTEGER NOT NULL,
        bac_si_id INTEGER,
        chuyen_khoa_id INTEGER NOT NULL,
        phong_kham_id INTEGER,
        ngay_hen DATE NOT NULL,
        gio_hen TIME NOT NULL,
        ly_do_kham TEXT,
        loai_lich_hen INTEGER DEFAULT 1,
        trang_thai TEXT DEFAULT 'Chờ xác nhận',
        ngay_dat DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
        FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
        FOREIGN KEY (chuyen_khoa_id) REFERENCES chuyen_khoa(id),
        FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id)
    );

    CREATE TABLE IF NOT EXISTS phieu_kham (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_phieu TEXT NOT NULL UNIQUE,
        benh_nhan_id INTEGER NOT NULL,
        bac_si_id INTEGER NOT NULL,
        phong_kham_id INTEGER NOT NULL,
        lich_hen_id INTEGER,
        thoi_gian_kham DATETIME DEFAULT CURRENT_TIMESTAMP,
        ly_do_kham TEXT,
        trieu_chung TEXT,
        chan_doan_so_bo TEXT,
        chan_doan_icd TEXT,
        huong_dieu_tri TEXT,
        loi_dan TEXT,
        ngay_tai_kham DATE,
        trang_thai TEXT DEFAULT 'Hoàn thành',
        FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
        FOREIGN KEY (bac_si_id) REFERENCES bac_si(id),
        FOREIGN KEY (phong_kham_id) REFERENCES phong_kham(id),
        FOREIGN KEY (lich_hen_id) REFERENCES lich_hen(id)
    );

    CREATE TABLE IF NOT EXISTS phieu_chi_dinh (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_chi_dinh TEXT NOT NULL UNIQUE,
        phieu_kham_id INTEGER NOT NULL,
        bac_si_id INTEGER NOT NULL,
        thoi_gian_chi_dinh DATETIME DEFAULT CURRENT_TIMESTAMP,
        ghi_chu TEXT,
        trang_thai TEXT DEFAULT 'Hoàn thành',
        FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id),
        FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
    );

    CREATE TABLE IF NOT EXISTS chi_tiet_chi_dinh (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phieu_chi_dinh_id INTEGER NOT NULL,
        dich_vu_id INTEGER NOT NULL,
        ket_qua TEXT,
        file_ket_qua TEXT,
        ktv_thuc_hien TEXT,
        thoi_gian_thuc_hien DATETIME,
        trang_thai TEXT DEFAULT 'Hoàn thành',
        FOREIGN KEY (phieu_chi_dinh_id) REFERENCES phieu_chi_dinh(id),
        FOREIGN KEY (dich_vu_id) REFERENCES dich_vu(id)
    );

    CREATE TABLE IF NOT EXISTS don_thuoc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_don_thuoc TEXT NOT NULL UNIQUE,
        phieu_kham_id INTEGER NOT NULL UNIQUE,
        bac_si_id INTEGER NOT NULL,
        thoi_gian_ke DATETIME DEFAULT CURRENT_TIMESTAMP,
        loi_dan TEXT,
        trang_thai TEXT DEFAULT 'Đã cấp thuốc',
        FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id),
        FOREIGN KEY (bac_si_id) REFERENCES bac_si(id)
    );

    CREATE TABLE IF NOT EXISTS chi_tiet_don_thuoc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        don_thuoc_id INTEGER NOT NULL,
        thuoc_id INTEGER NOT NULL,
        so_luong INTEGER NOT NULL DEFAULT 1,
        lieu_dung TEXT,
        cach_dung TEXT,
        FOREIGN KEY (don_thuoc_id) REFERENCES don_thuoc(id),
        FOREIGN KEY (thuoc_id) REFERENCES thuoc(id)
    );

    CREATE TABLE IF NOT EXISTS hoa_don (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ma_hoa_don TEXT NOT NULL UNIQUE,
        benh_nhan_id INTEGER NOT NULL,
        phieu_kham_id INTEGER,
        tong_tien REAL NOT NULL DEFAULT 0.0,
        tien_bhyt REAL DEFAULT 0.0,
        giam_gia REAL DEFAULT 0.0,
        thanh_tien REAL NOT NULL DEFAULT 0.0,
        hinh_thuc_thanh_toan TEXT DEFAULT 'Tiền mặt',
        trang_thai TEXT DEFAULT 'Đã thanh toán',
        thoi_gian_thanh_toan DATETIME,
        nhan_vien_thu TEXT DEFAULT 'Trần Thị Mai',
        FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
        FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
    );

    CREATE TABLE IF NOT EXISTS chi_tiet_hoa_don (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hoa_don_id INTEGER NOT NULL,
        loai_khoan_thu TEXT NOT NULL,
        ten_khoan_thu TEXT NOT NULL,
        tham_chieu_id INTEGER,
        so_luong INTEGER NOT NULL DEFAULT 1,
        don_gia REAL NOT NULL DEFAULT 0.0,
        thanh_tien REAL NOT NULL DEFAULT 0.0,
        FOREIGN KEY (hoa_don_id) REFERENCES hoa_don(id)
    );

    CREATE TABLE IF NOT EXISTS thong_bao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tai_khoan_id INTEGER NOT NULL,
        tieu_de TEXT NOT NULL,
        noi_dung TEXT NOT NULL,
        loai_thong_bao TEXT DEFAULT 'Hệ thống',
        da_doc INTEGER DEFAULT 0,
        thoi_gian_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tai_khoan_id) REFERENCES tai_khoan(id)
    );

    CREATE TABLE IF NOT EXISTS phan_hoi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        benh_nhan_id INTEGER NOT NULL,
        phieu_kham_id INTEGER,
        diem_danh_gia INTEGER NOT NULL,
        noi_dung TEXT,
        thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
        FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
    );

    CREATE TABLE IF NOT EXISTS hom_thu_gop_y (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ho_ten TEXT NOT NULL,
        email TEXT,
        sdt TEXT,
        chu_de TEXT,
        noi_dung TEXT NOT NULL,
        ngay_gui DATETIME DEFAULT CURRENT_TIMESTAMP,
        trang_thai TEXT DEFAULT 'Chưa xử lý'
    );

    CREATE TABLE IF NOT EXISTS bai_viet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tac_gia_id INTEGER,
        tieu_de TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        danh_muc TEXT DEFAULT 'Cẩm Nang Y Tế',
        tom_tat TEXT,
        noi_dung TEXT,
        hinh_anh TEXT,
        luot_xem INTEGER DEFAULT 0,
        ngay_dang DATETIME DEFAULT CURRENT_TIMESTAMP,
        trang_thai INTEGER DEFAULT 1,
        FOREIGN KEY (tac_gia_id) REFERENCES nhan_vien(id)
    );
    ''')

    # Kiểm tra nếu chưa có dữ liệu thì nạp seed data
    cursor.execute("SELECT COUNT(*) as cnt FROM vai_tro")
    if cursor.fetchone()['cnt'] == 0:
        _seed_initial_data(cursor)

    conn.commit()
    conn.close()

def _seed_initial_data(cursor):
    """Nạp dữ liệu mẫu ban đầu đồng bộ hoàn toàn với cosodulieu.sql."""
    # 1. Vai trò
    cursor.executemany('''
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (?, ?, ?, ?)
    ''', [
        (1, 'ADMIN', 'Quản trị viên', 'Toàn quyền cấu hình và quản trị hệ thống phòng khám'),
        (2, 'LETAN', 'Nhân viên lễ tân / Thu ngân', 'Tiếp đón bệnh nhân, sắp xếp lịch hẹn, thu ngân viện phí'),
        (3, 'BACSI', 'Bác sĩ chuyên khoa', 'Khám bệnh, chẩn đoán, kê đơn thuốc và chỉ định cận lâm sàng'),
        (4, 'DUOCSI', 'Dược sĩ / Thủ kho dược', 'Quản lý kho thuốc, cấp phát thuốc theo toa'),
        (5, 'KTV', 'Kỹ thuật viên xét nghiệm', 'Thực hiện xét nghiệm, X-quang, chẩn đoán hình ảnh'),
        (6, 'BENHNHAN', 'Bệnh nhân', 'Khách hàng sử dụng cổng thông tin y tế bệnh nhân')
    ])

    # 2. Chuyên khoa
    cursor.executemany('''
        INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh) VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'KHOA_NOI', 'Khoa Nội Tổng Quát', 'Khám, chẩn đoán và điều trị bệnh lý tim mạch, tiêu hóa, hô hấp, cơ xương khớp', 'fa-stethoscope', 150000.0),
        (2, 'KHOA_NGOAI', 'Khoa Ngoại Tổng Quát', 'Khám và điều trị ngoại khoa, tiểu phẫu, xử lý vết thương', 'fa-syringe', 150000.0),
        (3, 'KHOA_NHI', 'Khoa Nhi', 'Chăm sóc và điều trị chuyên sâu bệnh lý trẻ em, tư vấn dinh dưỡng', 'fa-baby', 120000.0),
        (4, 'KHOA_RHM', 'Khoa Răng Hàm Mặt', 'Nha khoa tổng quát, nhổ răng khôn, niềng răng, cạo vôi răng', 'fa-tooth', 150000.0),
        (5, 'KHOA_SAN', 'Khoa Sản - Phụ Khoa', 'Quản lý thai kỳ, siêu âm 4D, tầm soát và điều trị phụ khoa', 'fa-person-pregnant', 180000.0),
        (6, 'KHOA_TMH', 'Khoa Tai Mũi Họng', 'Nội soi tai mũi họng, điều trị viêm xoang, viêm họng hạt, viêm amidan', 'fa-head-side-cough', 150000.0),
        (7, 'KHOA_MAT', 'Khoa Mắt', 'Đo tật khúc xạ, khám và điều trị bệnh lý đáy mắt, giác mạc', 'fa-eye', 150000.0),
        (8, 'KHOA_CLS', 'Khoa Cận Lâm Sàng', 'Trung tâm xét nghiệm hóa sinh, huyết học và chẩn đoán hình ảnh', 'fa-vial', 100000.0)
    ])

    # 3. Phòng khám
    cursor.executemany('''
        INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 'PK101', 'Phòng Khám Nội 1', 'Tầng 1 - Khu A', 1),
        (2, 1, 'PK102', 'Phòng Khám Nội 2', 'Tầng 1 - Khu A', 1),
        (3, 2, 'PK103', 'Phòng Khám Ngoại & Tiểu Phẫu', 'Tầng 1 - Khu B', 1),
        (4, 3, 'PK201', 'Phòng Khám Nhi 1', 'Tầng 2 - Khu A', 1),
        (5, 4, 'PK202', 'Phòng Nha Khoa Kỹ Thuật Cao', 'Tầng 2 - Khu B', 1),
        (6, 5, 'PK203', 'Phòng Khám Sản Phụ Khoa', 'Tầng 2 - Khu B', 1),
        (7, 8, 'XN001', 'Phòng Xét Nghiệm Huyết Học - Hóa Sinh', 'Tầng 1 - Khu C', 1),
        (8, 8, 'CDHA01', 'Phòng Siêu Âm Màu & Chụp X-Quang', 'Tầng 1 - Khu C', 1)
    ])

    # 4. Dịch vụ y tế
    cursor.executemany('''
        INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 'DV_KHAM_NOI', 'Khám Nội Tổng Quát', 'Khám bệnh', 150000.0, 80, 'Khám và tư vấn toàn diện các bệnh lý nội khoa'),
        (2, 3, 'DV_KHAM_NHI', 'Khám Nhi Khoa', 'Khám bệnh', 120000.0, 80, 'Khám và tư vấn sức khỏe trẻ em'),
        (3, 2, 'DV_KHAM_NGOAI', 'Khám Ngoại Khoa', 'Khám bệnh', 150000.0, 80, 'Khám và tư vấn tiểu phẫu ngoại khoa'),
        (4, 4, 'DV_NHO_RANG', 'Tiểu phẫu Nhổ răng khôn', 'Thủ thuật', 1000000.0, 0, 'Nhổ răng khôn mọc lệch, không đau'),
        (5, 4, 'DV_CAO_VOI', 'Cạo vôi răng & Đánh bóng', 'Thủ thuật', 200000.0, 0, 'Làm sạch mảng bám cao răng bằng sóng siêu âm'),
        (6, 8, 'DV_SIEU_AM', 'Siêu âm Doppler màu ổ bụng tổng quát', 'Chẩn đoán hình ảnh', 250000.0, 50, 'Khảo sát gan, mật, tụy, lách, thận, bàng quang'),
        (7, 8, 'DV_XN_MAU', 'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', 'Xét nghiệm', 150000.0, 80, 'Kiểm tra hồng cầu, bạch cầu, tiểu cầu, thiếu máu'),
        (8, 8, 'DV_XN_NT', 'Tổng phân tích nước tiểu 10 thông số', 'Xét nghiệm', 100000.0, 80, 'Kiểm tra đường, đạm, tế bào vi thể nước tiểu'),
        (9, 8, 'DV_XQUANG', 'Chụp X-Quang Tim Phổi thẳng kỹ thuật số', 'Chẩn đoán hình ảnh', 200000.0, 70, 'Kiểm tra tổn thương nhu mô phổi, bóng tim'),
        (10, 8, 'DV_ECG', 'Đo điện tim đồ 12 chuyển đạo (ECG)', 'Thăm dò chức năng', 150000.0, 70, 'Khảo sát nhịp xoang, rối loạn dẫn truyền tim'),
        (11, 8, 'DV_NOISOI_DD', 'Nội soi dạ dày tá tràng ống mềm', 'Chẩn đoán hình ảnh', 600000.0, 50, 'Nội soi chẩn đoán viêm loét dạ dày kèm Test HP')
    ])

    # 5. Kho dược & Thuốc
    cursor.executemany('''
        INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'TH001', 'Paracetamol 500mg', 'Paracetamol', '500mg', 'Viên', 2000.0, 5000, 'Dược Hậu Giang', 'Việt Nam', 'Uống 1-2 viên khi sốt trên 38.5°C hoặc đau nhức, cách nhau 4-6 giờ'),
        (2, 'TH002', 'Amoxicillin 500mg', 'Amoxicillin trihydrat', '500mg', 'Viên', 3000.0, 2000, 'Imexpharm', 'Việt Nam', 'Kháng sinh: Uống 1 viên sau ăn, ngày 2 lần, dùng đủ liệu trình 5-7 ngày'),
        (3, 'TH003', 'Oresol 245', 'Glucose, Natri clorid, Kali clorid', '245 mOsm/L', 'Gói', 5000.0, 1000, 'Traphaco', 'Việt Nam', 'Pha đúng 1 gói với 200ml nước sôi để nguội, uống bù nước khi sốt hoặc tiêu chảy'),
        (4, 'TH004', 'Loratadin 10mg', 'Loratadin', '10mg', 'Viên', 4000.0, 1500, 'Pymepharco', 'Việt Nam', 'Thuốc kháng histamin: Uống 1 viên vào buổi tối trước khi đi ngủ'),
        (5, 'TH005', 'Esomeprazole 40mg', 'Esomeprazole magnesium', '40mg', 'Viên', 12000.0, 3000, 'AstraZeneca', 'Thụy Điển', 'Giảm tiết acid dạ dày: Uống 1 viên trước bữa ăn sáng 30 phút'),
        (6, 'TH006', 'Phosphalugel 20g', 'Aluminium phosphate', '20g', 'Gói', 5000.0, 2500, 'Boehringer Ingelheim', 'Pháp', 'Uống 1 gói khi có cơn đau thượng vị hoặc 2 giờ sau bữa ăn'),
        (7, 'TH007', 'Men vi sinh Enterogermina', 'Bacillus clausii', '2 tỷ bào tử/5ml', 'Ống', 9000.0, 1200, 'Sanofi', 'Ý', 'Lắc đều, uống trực tiếp 1-2 ống/ngày sau bữa ăn'),
        (8, 'TH008', 'Ibuprofen 400mg', 'Ibuprofen', '400mg', 'Viên', 3500.0, 2500, 'Stada', 'Việt Nam', 'Kháng viêm giảm đau cơ xương khớp, uống 1 viên sau ăn no'),
        (9, 'TH009', 'Siro ho thảo dược Prospan', 'Cao khô lá thường xuân', '100ml', 'Chai', 75000.0, 300, 'Engelhard', 'Đức', 'Uống 5ml/lần, ngày 3 lần sau ăn cho người lớn và trẻ em trên 6 tuổi'),
        (10, 'TH010', 'Nước muối sinh lý NaCl 0.9%', 'Natri Clorid 0.9%', '500ml', 'Chai', 10000.0, 800, 'Pharmedic', 'Việt Nam', 'Dùng súc miệng họng hoặc rửa vết thương ngoài da')
    ])

    # 6. Tài khoản
    pwd_admin = generate_password_hash('admin123')
    pwd_default = generate_password_hash('123456')

    accounts = [
        (1, 1, 'admin', pwd_admin, 'admin@phongkham.com', '0999999999'),
        (2, 2, 'letan.mai', pwd_default, 'mai.tt@phongkham.com', '0988888888'),
        (3, 2, 'letan.khang', pwd_default, 'khang.lv@phongkham.com', '0977777777'),
        (4, 3, 'dr.quan', pwd_default, 'quan.tm@phongkham.com', '0966666666'),
        (5, 3, 'dr.lan', pwd_default, 'lan.pp@phongkham.com', '0955555555'),
        (6, 3, 'dr.minh', pwd_default, 'minh.vq@phongkham.com', '0944444444'),
        (7, 3, 'dr.huong', pwd_default, 'huong.bt@phongkham.com', '0933333333'),
        (8, 6, '0901234567', pwd_default, 'baonam@gmail.com', '0901234567'),
        (9, 6, '0912345678', pwd_default, 'ngoctram@gmail.com', '0912345678'),
        (10, 6, '0923456789', pwd_default, 'vanquyet@gmail.com', '0923456789'),
        (11, 6, '0934567890', pwd_default, 'thaomy@gmail.com', '0934567890'),
        (12, 6, '0945678901', pwd_default, 'trongthang@gmail.com', '0945678901'),
        (13, 6, '0956789012', pwd_default, 'thanhtruc@gmail.com', '0956789012'),
        (14, 6, '0967890123', pwd_default, 'kienhao@gmail.com', '0967890123'),
        (15, 6, '0978901234', pwd_default, 'nhaky@gmail.com', '0978901234')
    ]
    cursor.executemany('''
        INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt) VALUES (?, ?, ?, ?, ?, ?)
    ''', accounts)

    # 7. Nhân viên
    cursor.executemany('''
        INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 'NV001', 'Admin Hệ Thống', 1, '1988-01-01', '0999999999', 'admin@phongkham.com', '079088000001', '140 Lê Trọng Tấn, Tân Phú, TP.HCM', 'Quản trị viên'),
        (2, 2, 'NV002', 'Trần Thị Mai', 0, '1996-05-15', '0988888888', 'mai.tt@phongkham.com', '079096000002', 'Quận Tân Bình, TP.HCM', 'Trưởng quầy Tiếp tân & Thu ngân'),
        (3, 3, 'NV003', 'Lê Văn Khang', 1, '1998-09-20', '0977777777', 'khang.lv@phongkham.com', '079098000003', 'Quận 12, TP.HCM', 'Nhân viên lễ tân'),
        (4, 4, 'BS001', 'BS. CKII. Trần Minh Quân', 1, '1982-03-10', '0966666666', 'quan.tm@phongkham.com', '079082000004', 'Quận 10, TP.HCM', 'Trưởng Khoa Nội'),
        (5, 5, 'BS002', 'BS. ThS. Phạm Phương Lan', 0, '1989-11-25', '0955555555', 'lan.pp@phongkham.com', '079089000005', 'Quận Tân Phú, TP.HCM', 'Bác sĩ chuyên khoa Nhi'),
        (6, 6, 'BS003', 'BS. TS. Vũ Quang Minh', 1, '1979-07-08', '0944444444', 'minh.vq@phongkham.com', '079079000006', 'Quận 3, TP.HCM', 'Trưởng Khoa Ngoại'),
        (7, 7, 'BS004', 'BS. CKI. Bùi Thu Hương', 0, '1991-04-18', '0933333333', 'huong.bt@phongkham.com', '079091000007', 'Quận Bình Thạnh, TP.HCM', 'Bác sĩ Răng Hàm Mặt')
    ])

    # 8. Bác sĩ
    cursor.executemany('''
        INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 4, 1, 1, 'BS. CKII', '15 năm kinh nghiệm chuyên sâu nội tiêu hóa, từng công tác tại BV Chợ Rẫy', 'dr_quan.jpg', 150000.0, 'Đang làm việc'),
        (2, 5, 3, 4, 'Thạc sĩ - BS Nhi', '10 năm kinh nghiệm điều trị nhi khoa tại BV Nhi Đồng 1, mát tay và ân cần', 'dr_lan.jpg', 120000.0, 'Đang làm việc'),
        (3, 6, 2, 3, 'Tiến sĩ - BS Ngoại', '18 năm kinh nghiệm phẫu thuật nội soi và chấn thương chỉnh hình', 'dr_minh.jpg', 180000.0, 'Đang làm việc'),
        (4, 7, 4, 5, 'BS. CKI', '8 năm kinh nghiệm chỉnh nha thẩm mỹ và phẫu thuật răng hàm mặt', 'dr_huong.jpg', 150000.0, 'Đang làm việc')
    ])

    # 9. Bệnh nhân
    patients = [
        (1, 8, 'BN2609001', 'Hoàng Bảo Nam', '1990-05-12', 'Nam', '0901234567', 'baonam@gmail.com', '079090000001', 'GD4797931100001', 'Quận 1, TP.HCM', 'O+', 'Không có', 'Đau dạ dày nhẹ', 'Không có tiền sử bệnh lý di truyền', 'Hoàng Tuấn Kiệt', '0909111222', 'Bố', 1, '2026-09-01'),
        (2, 9, 'BN2609002', 'Lê Ngọc Trâm', '1995-08-22', 'Nữ', '0912345678', 'ngoctram@gmail.com', '079095000002', 'GD4797931100002', 'Quận 3, TP.HCM', 'A+', 'Dị ứng hải sản, Paracetamol', 'Viêm xoang dị ứng', 'Mẹ có tiền sử hen phế quản', 'Lê Quang Liêm', '0919222333', 'Bố', 1, '2026-09-02'),
        (3, 10, 'BN2609003', 'Trần Văn Quyết', '1985-11-30', 'Nam', '0923456789', 'vanquyet@gmail.com', '079085000003', 'GD4797931100003', 'Quận Tân Bình, TP.HCM', 'B+', 'Không có', 'Tăng huyết áp vô căn độ 1', 'Bố có tiền sử tăng huyết áp', 'Trần Thị Hà', '0929333444', 'Vợ', 1, '2026-09-05'),
        (4, 11, 'BN2609004', 'Phạm Thảo My', '2015-02-14', 'Nữ', '0934567890', 'thaomy@gmail.com', '079115000004', 'TE1797931100004', 'Quận Gò Vấp, TP.HCM', 'AB+', 'Không có', 'Viêm phế quản co thắt', 'Chị gái có tiền sử viêm mũi dị ứng', 'Phạm Minh Nhật', '0939444555', 'Bố', 1, '2026-09-08'),
        (5, 12, 'BN2609005', 'Đinh Trọng Thắng', '1978-04-10', 'Nam', '0945678901', 'trongthang@gmail.com', '079078000005', 'DN4797931100005', 'Quận 10, TP.HCM', 'O-', 'Không có', 'Đái tháo đường Type 2, Rối loạn lipid máu', 'Gia đình có tiền sử đái tháo đường', 'Đinh Lan Anh', '0949555666', 'Vợ', 1, '2026-09-10'),
        (6, 13, 'BN2609006', 'Võ Thanh Trúc', '1998-09-09', 'Nữ', '0956789012', 'thanhtruc@gmail.com', '079098000006', 'SV4797931100006', 'Quận Bình Thạnh, TP.HCM', 'A+', 'Dị ứng phấn hoa', 'Đau dạ dày, viêm đại tràng co thắt', 'Không có', 'Võ Hải Đăng', '0959666777', 'Anh trai', 1, '2026-09-12'),
        (7, 14, 'BN2609007', 'Ngô Kiến Hào', '2010-12-25', 'Nam', '0967890123', 'kienhao@gmail.com', '079110000007', 'HS4797931100007', 'Quận 7, TP.HCM', 'O+', 'Không có', 'Không có', 'Không có', 'Ngô Bảo Châu', '0969777888', 'Mẹ', 1, '2026-09-14'),
        (8, 15, 'BN2609008', 'Lý Nhã Kỳ', '1982-07-19', 'Nữ', '0978901234', 'nhaky@gmail.com', '079082000008', 'DN4797931100008', 'Quận 2, TP.HCM', 'B-', 'Không có', 'Không có tiền sử bệnh lý mạn tính', 'Không có', 'Lý Đại Nghĩa', '0979888999', 'Em trai', 1, '2026-09-15'),
        (9, None, 'BN2609009', 'Châu Gia Kiệt', '1992-01-01', 'Nam', '0981234567', 'giakiet@gmail.com', '079092000009', '', 'TP. Thủ Đức, TP.HCM', 'O+', 'Không có', 'Viêm xoang mạn tính', 'Không có', 'Châu Ánh Nguyệt', '0989000111', 'Chị gái', 0, '2026-09-18'),
        (10, None, 'BN2609010', 'Bảo Thy', '1999-03-03', 'Nữ', '0991234567', 'baothy@gmail.com', '079099000010', '', 'Quận 5, TP.HCM', 'A+', 'Không có', 'Không có', 'Không có', 'Bảo Quốc', '0999111222', 'Bố', 0, '2026-09-20')
    ]
    cursor.executemany('''
        INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan, ngay_tao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients)

    # 10. Sinh hiệu
    vitals = [
        (1, 1, '76 lần/phút', '36.8 °C', '120/80 mmHg', '99 %', '18 lần/phút', '172 cm', '68 kg', '23.0 (Bình thường)'),
        (2, 2, '82 lần/phút', '37.0 °C', '115/75 mmHg', '98 %', '19 lần/phút', '160 cm', '50 kg', '19.5 (Bình thường)'),
        (3, 3, '88 lần/phút', '36.7 °C', '145/90 mmHg', '97 %', '20 lần/phút', '168 cm', '74 kg', '26.2 (Tiền béo phì)'),
        (4, 4, '96 lần/phút', '37.8 °C', '95/60 mmHg', '98 %', '24 lần/phút', '130 cm', '28 kg', '16.6 (Bình thường)'),
        (5, 5, '74 lần/phút', '36.6 °C', '135/85 mmHg', '96 %', '18 lần/phút', '170 cm', '78 kg', '27.0 (Béo phì độ 1)'),
        (6, 6, '78 lần/phút', '36.9 °C', '110/70 mmHg', '99 %', '17 lần/phút', '162 cm', '48 kg', '18.3 (Gầy nhẹ)'),
        (7, 7, '80 lần/phút', '36.5 °C', '105/65 mmHg', '99 %', '19 lần/phút', '155 cm', '45 kg', '18.7 (Bình thường)'),
        (8, 8, '72 lần/phút', '36.7 °C', '120/80 mmHg', '99 %', '16 lần/phút', '165 cm', '53 kg', '19.5 (Bình thường)'),
        (9, 9, '76 lần/phút', '36.8 °C', '125/80 mmHg', '98 %', '18 lần/phút', '174 cm', '70 kg', '23.1 (Bình thường)'),
        (10, 10, '70 lần/phút', '36.6 °C', '110/70 mmHg', '99 %', '16 lần/phút', '163 cm', '49 kg', '18.4 (Gầy nhẹ)')
    ]
    cursor.executemany('''
        INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', vitals)

    # 11. Lịch làm việc
    cursor.executemany('''
        INSERT INTO lich_lam_viec (id, bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 1, '2026-09-28', 1, '07:00:00', '11:30:00', 25, 18),
        (2, 1, 1, '2026-09-28', 2, '13:30:00', '17:00:00', 20, 12),
        (3, 2, 4, '2026-09-28', 1, '07:00:00', '11:30:00', 20, 15),
        (4, 3, 3, '2026-09-28', 2, '13:30:00', '17:00:00', 15, 9),
        (5, 4, 5, '2026-09-28', 1, '07:30:00', '11:30:00', 15, 10)
    ])

    # 12. Lịch hẹn
    cursor.executemany('''
        INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'LH2609001', 1, 1, 1, 1, '2026-09-20', '08:30:00', 'Đau âm ỉ thượng vị, ợ chua, đầy bụng khó tiêu', 1, 'Đã khám'),
        (2, 'LH2609002', 2, 1, 1, 1, '2026-09-21', '09:00:00', 'Đau rát họng, sốt nhẹ, nghẹt mũi', 1, 'Đã khám'),
        (3, 'LH2609003', 3, 1, 1, 1, '2026-09-22', '10:00:00', 'Tái khám định kỳ huyết áp, chóng mặt buổi sáng', 2, 'Đã khám'),
        (4, 'LH2609004', 4, 2, 3, 4, '2026-09-23', '08:30:00', 'Bé ho đờm nhiều, thở khò khè về đêm', 1, 'Đã khám'),
        (5, 'LH2609005', 5, 3, 2, 3, '2026-09-24', '14:00:00', 'Đau sưng cổ chân phải sau khi trượt ngã', 1, 'Đã khám'),
        (6, 'LH2609006', 6, 1, 1, 1, '2026-09-25', '14:30:00', 'Rối loạn tiêu hóa, đau quặn bụng sau ăn hải sản', 1, 'Đã khám'),
        (7, 'LH2609007', 7, 2, 3, 4, '2026-09-28', '08:30:00', 'Khám sức khỏe tổng quát đầu năm học', 1, 'Đã duyệt'),
        (8, 'LH2609008', 8, 4, 4, 5, '2026-09-28', '09:30:00', 'Đau nhức vùng hàm dưới, răng khôn mọc lệch', 1, 'Đã duyệt'),
        (9, 'LH2609009', 9, 1, 1, 1, '2026-09-28', '10:30:00', 'Mất ngủ kéo dài, suy nhược cơ thể', 1, 'Chờ xác nhận'),
        (10, 'LH2609010', 10, 3, 2, 3, '2026-09-29', '14:00:00', 'Khám nốt ruồi bất thường vùng cánh tay', 1, 'Chờ xác nhận'),
        (11, 'LH2609011', 1, 1, 1, 1, '2026-10-04', '08:30:00', 'Tái khám viêm dạ dày sau 14 ngày dùng thuốc', 2, 'Đã duyệt')
    ])

    # 13. Phiếu khám
    cursor.executemany('''
        INSERT INTO phieu_kham (id, ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'PK2609001', 1, 1, 1, 1, '2026-09-20 08:30:00', 'Đau âm ỉ vùng thượng vị, ợ chua, chướng bụng sau ăn', 'Bệnh nhân tỉnh táo, tiếp xúc tốt. Ấn đau tức nhẹ vùng thượng vị, bụng mềm, không đề kháng thành bụng.', 'Nghi ngờ viêm dạ dày HP (-)', 'K29.5 - Viêm dạ dày mạn tính, không xác định', 'Điều trị nội khoa bằng thuốc ức chế bơm proton và bao niêm mạc', 'Ăn uống đúng bữa, hạn chế đồ cay nóng và rượu bia. Tái khám sau 14 ngày.', '2026-10-04', 'Hoàn thành'),
        (2, 'PK2609002', 2, 1, 1, 2, '2026-09-21 09:15:00', 'Đau họng, sốt nhẹ, ho khan', 'Họng đỏ sung huyết, amidan không phì đại, không giả mạc. Hạch góc hàm không sưng.', 'Viêm họng cấp do virus', 'J02.9 - Viêm họng cấp, không xác định', 'Điều trị triệu chứng, hạ sốt, bù nước điện giải', 'Súc miệng nước muối sinh lý ấm ngày 3-4 lần, giữ ấm cổ họng.', '2026-09-28', 'Hoàn thành'),
        (3, 'PK2609003', 3, 1, 1, 3, '2026-09-22 10:10:00', 'Tái khám huyết áp, chóng mặt khi thức dậy', 'Huyết áp đo tại phòng khám 145/90 mmHg, tim đều, không âm thổi bệnh lý.', 'Tăng huyết áp nguyên phát độ 1', 'I10 - Tăng huyết áp vô căn (nguyên phát)', 'Điều chỉnh liều thuốc hạ áp, theo dõi huyết áp tại nhà ngày 2 lần', 'Ăn nhạt dưới 5g muối/ngày, tập thể dục nhẹ nhàng 30 phút/ngày.', '2026-10-22', 'Hoàn thành'),
        (4, 'PK2609004', 4, 2, 4, 4, '2026-09-23 08:45:00', 'Bé ho có đờm, thở khò khè', 'Họng đỏ nhẹ, nghe phổi có ít ran rít rải rác hai phế trường, không co kéo cơ hô hấp phụ.', 'Viêm phế quản cấp', 'J20.9 - Viêm phế quản cấp, không xác định', 'Kháng sinh đường uống, siro ho thảo dược, khí dung nếu khó thở', 'Uống nhiều nước ấm, theo dõi nhịp thở của bé. Tái khám ngay nếu sốt cao hoặc thở nhanh.', '2026-09-30', 'Hoàn thành'),
        (5, 'PK2609005', 5, 3, 3, 5, '2026-09-24 14:20:00', 'Đau nhức cổ chân phải sau té ngã', 'Cổ chân phải sưng nề nhẹ vùng mắt cá ngoài, ấn đau chói nhẹ, biên độ vận động hạn chế do đau.', 'Bong gân cổ chân phải độ 1', 'S93.4 - Bong gân và căng cơ khớp cổ chân', 'Nghỉ ngơi, chườm đá lạnh, băng ép thun cố định, thuốc giảm đau kháng viêm', 'Hạn chế đi lại tì đè chân đau trong 5-7 ngày đầu.', '2026-10-01', 'Hoàn thành')
    ])

    # 14. Phiếu chỉ định CLS
    cursor.executemany('''
        INSERT INTO phieu_chi_dinh (id, ma_chi_dinh, phieu_kham_id, bac_si_id, thoi_gian_chi_dinh, ghi_chu, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'CD2609001', 1, 1, '2026-09-20 08:45:00', 'Nội soi dạ dày và tổng phân tích tế bào máu', 'Hoàn thành'),
        (2, 'CD2609002', 2, 1, '2026-09-21 09:30:00', 'Xét nghiệm công thức máu', 'Hoàn thành'),
        (3, 'CD2609003', 3, 1, '2026-09-22 10:25:00', 'Đo điện tim đồ 12 chuyển đạo', 'Hoàn thành'),
        (4, 'CD2609004', 4, 2, '2026-09-23 09:00:00', 'Chụp X-quang tim phổi thẳng', 'Hoàn thành'),
        (5, 'CD2609005', 5, 3, '2026-09-24 14:35:00', 'Chụp X-quang khớp cổ chân thẳng - nghiêng', 'Hoàn thành')
    ])

    # 15. Chi tiết chỉ định CLS
    cursor.executemany('''
        INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, file_ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 11, 'Niêm mạc hang vị phù nề, sung huyết nhẹ. Test Clo HP: Âm tính (-)', 'noisoi_bn01.jpg', 'BS. CKI. Nguyễn Trọng Nghĩa', '2026-09-20 09:30:00', 'Hoàn thành'),
        (2, 1, 7, 'Hồng cầu: 4.85 T/L, Bạch cầu: 6.8 G/L, Tiểu cầu: 235 G/L. Các chỉ số trong giới hạn bình thường.', 'xn_mau_bn01.pdf', 'KTV. Lê Thị Thu', '2026-09-20 09:15:00', 'Hoàn thành'),
        (3, 2, 7, 'Bạch cầu hơi tăng 10.2 G/L (ưu thế lympho), CRP bình thường.', 'xn_mau_bn02.pdf', 'KTV. Lê Thị Thu', '2026-09-21 10:00:00', 'Hoàn thành'),
        (4, 3, 10, 'Nhịp xoang đều 78 lần/phút, trục trung gian, không thấy dấu hiệu thiếu máu cơ tim cục bộ.', 'ecg_bn03.pdf', 'KTV. Trần Văn Đức', '2026-09-22 10:45:00', 'Hoàn thành'),
        (5, 4, 9, 'Tăng đậm các nhánh phế quản rốn phổi hai bên, không thấy nốt thâm nhiễm nhu mô phổi.', 'xquang_bn04.jpg', 'KTV. Trần Văn Đức', '2026-09-23 09:20:00', 'Hoàn thành'),
        (6, 5, 9, 'Không thấy hình ảnh gãy xương hoặc trật khớp cổ chân. Khe khớp mắt cá bình thường.', 'xquang_bn05.jpg', 'KTV. Trần Văn Đức', '2026-09-24 14:55:00', 'Hoàn thành')
    ])

    # 16. Đơn thuốc
    cursor.executemany('''
        INSERT INTO don_thuoc (id, ma_don_thuoc, phieu_kham_id, bac_si_id, thoi_gian_ke, loi_dan, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'DT2609001', 1, 1, '2026-09-20 09:45:00', 'Uống thuốc đúng giờ, kiêng chua cay, rượu bia', 'Đã cấp thuốc'),
        (2, 'DT2609002', 2, 1, '2026-09-21 10:15:00', 'Uống nhiều nước ấm, súc họng nước muối', 'Đã cấp thuốc'),
        (3, 'DT2609003', 3, 1, '2026-09-22 11:00:00', 'Kiêng ăn mặn, uống thuốc hạ áp mỗi sáng', 'Đã cấp thuốc'),
        (4, 'DT2609004', 4, 2, '2026-09-23 09:45:00', 'Uống siro ho và kháng sinh đúng liều lượng', 'Đã cấp thuốc'),
        (5, 'DT2609005', 5, 3, '2026-09-24 15:15:00', 'Uống thuốc giảm đau sau ăn no, chườm lạnh', 'Đã cấp thuốc')
    ])

    # 17. Chi tiết đơn thuốc
    cursor.executemany('''
        INSERT INTO chi_tiet_don_thuoc (id, don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 5, 28, 'Ngày 1 viên', 'Uống 1 viên trước ăn sáng 30 phút'),
        (2, 1, 6, 20, 'Ngày 2 gói', 'Uống 1 gói sau ăn 2 giờ hoặc khi đau tức bụng'),
        (3, 2, 1, 15, 'Ngày 2-3 lần, lần 1 viên', 'Uống khi sốt hoặc đau rát họng, sau ăn'),
        (4, 2, 4, 10, 'Ngày 1 viên', 'Uống 1 viên trước khi đi ngủ'),
        (5, 2, 10, 2, 'Ngày 3-4 lần', 'Súc miệng họng sâu bằng nước muối sinh lý'),
        (6, 4, 2, 14, 'Ngày 2 lần, lần 1 viên', 'Uống sau bữa ăn sáng và tối'),
        (7, 4, 9, 1, 'Ngày 3 lần, lần 5ml', 'Uống sau ăn 15 phút'),
        (8, 5, 8, 14, 'Ngày 2 lần, lần 1 viên', 'Uống sau ăn no trưa và tối')
    ])

    # 18. Hóa đơn
    cursor.executemany('''
        INSERT INTO hoa_don (id, ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'HD2609001', 1, 1, 1336000.0, 300000.0, 0.0, 1036000.0, 'Momo', 'Đã thanh toán', '2026-09-20 10:00:00', 'Trần Thị Mai'),
        (2, 'HD2609002', 2, 2, 400000.0, 120000.0, 0.0, 280000.0, 'Chuyển khoản', 'Đã thanh toán', '2026-09-21 10:30:00', 'Trần Thị Mai'),
        (3, 'HD2609003', 3, 3, 300000.0, 105000.0, 0.0, 195000.0, 'Tiền mặt', 'Đã thanh toán', '2026-09-22 11:15:00', 'Lê Văn Khang'),
        (4, 'HD2609004', 4, 4, 437000.0, 140000.0, 0.0, 297000.0, 'Chuyển khoản', 'Đã thanh toán', '2026-09-23 10:00:00', 'Trần Thị Mai'),
        (5, 'HD2609005', 5, 5, 399000.0, 0.0, 50000.0, 349000.0, 'Tiền mặt', 'Đã thanh toán', '2026-09-24 15:30:00', 'Lê Văn Khang')
    ])

    # 19. Chi tiết hóa đơn
    cursor.executemany('''
        INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 'Khám bệnh', 'Khám Nội Tổng Quát', 1, 1, 150000.0, 150000.0),
        (2, 1, 'Dịch vụ CLS', 'Nội soi dạ dày tá tràng ống mềm', 11, 1, 600000.0, 600000.0),
        (3, 1, 'Dịch vụ CLS', 'Tổng phân tích tế bào máu ngoại vi', 7, 1, 150000.0, 150000.0),
        (4, 1, 'Thuốc', 'Esomeprazole 40mg (28 Viên)', 5, 28, 12000.0, 336000.0),
        (5, 1, 'Thuốc', 'Phosphalugel 20g (20 Gói)', 6, 20, 5000.0, 100000.0),
        (6, 2, 'Khám bệnh', 'Khám Nội Tổng Quát', 1, 1, 150000.0, 150000.0),
        (7, 2, 'Dịch vụ CLS', 'Tổng phân tích tế bào máu ngoại vi', 7, 1, 150000.0, 150000.0),
        (8, 2, 'Thuốc', 'Toa thuốc điều trị viêm họng cấp', None, 1, 100000.0, 100000.0),
        (9, 3, 'Khám bệnh', 'Khám Nội Tổng Quát (Tái khám)', 1, 1, 150000.0, 150000.0),
        (10, 3, 'Dịch vụ CLS', 'Đo điện tim đồ 12 chuyển đạo', 10, 1, 150000.0, 150000.0),
        (11, 4, 'Khám bệnh', 'Khám Nhi Khoa', 2, 1, 120000.0, 120000.0),
        (12, 4, 'Dịch vụ CLS', 'Chụp X-Quang Tim Phổi thẳng', 9, 1, 200000.0, 200000.0),
        (13, 4, 'Thuốc', 'Toa thuốc viêm phế quản', None, 1, 117000.0, 117000.0),
        (14, 5, 'Khám bệnh', 'Khám Ngoại Khoa', 3, 1, 150000.0, 150000.0),
        (15, 5, 'Dịch vụ CLS', 'Chụp X-Quang khớp cổ chân', 9, 1, 200000.0, 200000.0),
        (16, 5, 'Thuốc', 'Ibuprofen 400mg (14 Viên)', 8, 14, 3500.0, 49000.0)
    ])

    # 20. Bài viết
    cursor.executemany('''
        INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 4, 'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', 'benh-cam-cum-mua-giao-mua', 'Cẩm Nang Y Tế', 'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', 'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', 'cam-cum.jpg', 320, '2026-09-20 08:00:00', 1),
        (2, 5, 'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', 'cham-soc-rang-mieng-cho-tre', 'Nhi Khoa', 'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', 'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng chứa flour phù hợp lứa tuổi, hạn chế bánh kẹo ngọt trước khi đi ngủ...', 'rang-mieng-tre.jpg', 215, '2026-09-21 09:30:00', 1),
        (3, 6, 'Dấu hiệu thoái hóa khớp gối và phương pháp điều trị mới', 'dau-hieu-thoai-hoa-khop-goi', 'Cơ Xương Khớp', 'Thoái hóa khớp gối là căn bệnh phổ biến ở người trung niên và cao tuổi. Phát hiện sớm các dấu hiệu đau khớp khi leo cầu thang, lục khục khi vận động giúp bảo tồn sụn khớp tối ưu.', 'Nội dung chi tiết về các giải pháp điều trị thoái hóa khớp gối: vật lý trị liệu, tiêm chất nhờn nhân tạo, kiểm soát cân nặng và các bài tập tăng cường sức cơ đùi...', 'thoai-hoa-khop.jpg', 410, '2026-09-22 14:15:00', 1),
        (4, 4, 'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', 'kham-suc-khoe-tong-quat-dinh-ky', 'Tin Tức Phòng Khám', 'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', 'Nội dung chi tiết về gói khám tổng quát tại H2T Healthcare: bao gồm xét nghiệm máu tổng thể, siêu âm ổ bụng, chụp X-quang tim phổi và đo điện tim đồ...', 'kham-tong-quat.jpg', 580, '2026-09-23 10:00:00', 1),
        (5, 7, 'Những điều cần biết trước khi nhổ răng khôn mọc lệch', 'nhung-dieu-can-biet-khi-nho-rang-khon', 'Răng Hàm Mặt', 'Răng khôn mọc ngầm, mọc lệch gây giắt thức ăn, sâu răng bên cạnh và viêm lợi trùm. Tìm hiểu quy trình nhổ răng không đau với công nghệ máy siêu âm hiện đại.', 'Nội dung chi tiết về chỉ định nhổ răng khôn, quy trình chụp phim CT Cone Beam 3D, xét nghiệm máu trước tiểu phẫu và chế độ ăn mềm sau khi nhổ...', 'nho-rang-khon.jpg', 190, '2026-09-24 16:00:00', 1)
    ])
    conn.commit()
    conn.close()

def init_db():
    """Khởi tạo CSDL tương ứng với DB_ENGINE được cấu hình."""
    if DB_ENGINE == 'sqlite':
        init_sqlite_db()
    elif DB_ENGINE == 'sqlserver':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM benh_nhan")
            row = cursor.fetchone()
            print(f"[Database] Ket noi Microsoft SQL Server thanh cong! Tong so benh nhan: {row['cnt']}")
            conn.close()
        except Exception as e:
            print("[Database] Canh bao ket noi SQL Server:", e)
    elif DB_ENGINE == 'mysql':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM benh_nhan")
            row = cursor.fetchone()
            print(f"[Database] Ket noi MySQL thanh cong! Tong so benh nhan: {row['cnt']}")
            conn.close()
        except Exception as e:
            print("[Database] Canh bao ket noi MySQL:", e)

# CÁC HÀM TRUY VẤN DỮ LIỆU CHÍNH (REPOSITORY)

def get_all_patients():
    """Lấy toàn bộ danh sách bệnh nhân kèm sinh hiệu và số lần khám."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            b.*,
            t.username,
            t.password AS raw_hashed_pwd,
            s.mach, s.nhiet_do, s.huyet_ap, s.spo2, s.nhip_tho, s.chieu_cao, s.can_nang, s.bmi
        FROM benh_nhan b
        LEFT JOIN tai_khoan t ON b.tai_khoan_id = t.id
        LEFT JOIN chi_so_sinh_ton s ON b.id = s.benh_nhan_id
        ORDER BY b.id ASC
    ''')
    rows = cursor.fetchall()

    patients_list = []
    for r in rows:
        p = dict(r)
        # Tính tuổi
        birth_year = int(str(p['ngay_sinh'])[:4]) if p.get('ngay_sinh') else 1990
        p['tuoi'] = datetime.now().year - birth_year
        
        # Sinh hiệu
        p['vitals'] = {
            'mach': p.get('mach') or '75 lần/phút',
            'nhiet_do': p.get('nhiet_do') or '36.8 °C',
            'huyet_ap': p.get('huyet_ap') or '120/80 mmHg',
            'spo2': p.get('spo2') or '99 %',
            'nhip_tho': p.get('nhip_tho') or '18 lần/phút',
            'chieu_cao': p.get('chieu_cao') or '170 cm',
            'can_nang': p.get('can_nang') or '65 kg',
            'bmi': p.get('bmi') or '22.5 (Bình thường)'
        }
        
        # Lịch sử khám
        p['lich_su_kham'] = get_patient_history(p['id'])
        patients_list.append(p)

    conn.close()
    return patients_list

def get_patient_by_id(patient_id):
    """Lấy chi tiết hồ sơ 360 độ của một bệnh nhân theo ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            b.*,
            t.username,
            s.mach, s.nhiet_do, s.huyet_ap, s.spo2, s.nhip_tho, s.chieu_cao, s.can_nang, s.bmi
        FROM benh_nhan b
        LEFT JOIN tai_khoan t ON b.tai_khoan_id = t.id
        LEFT JOIN chi_so_sinh_ton s ON b.id = s.benh_nhan_id
        WHERE b.id = ?
    ''', (patient_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    p = dict(row)
    birth_year = int(str(p['ngay_sinh'])[:4]) if p.get('ngay_sinh') else 1990
    p['tuoi'] = datetime.now().year - birth_year
    p['vitals'] = {
        'mach': p.get('mach') or '75 lần/phút',
        'nhiet_do': p.get('nhiet_do') or '36.8 °C',
        'huyet_ap': p.get('huyet_ap') or '120/80 mmHg',
        'spo2': p.get('spo2') or '99 %',
        'nhip_tho': p.get('nhip_tho') or '18 lần/phút',
        'chieu_cao': p.get('chieu_cao') or '170 cm',
        'can_nang': p.get('can_nang') or '65 kg',
        'bmi': p.get('bmi') or '22.5 (Bình thường)'
    }
    p['lich_su_kham'] = get_patient_history(p['id'])
    return p

def get_patient_history(patient_id):
    """Lấy danh sách các phiếu khám, đơn thuốc và cận lâm sàng của bệnh nhân."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            pk.id, pk.ma_phieu, pk.thoi_gian_kham, pk.ly_do_kham, pk.trieu_chung,
            pk.chan_doan_so_bo, pk.chan_doan_icd, pk.huong_dieu_tri, pk.loi_dan, pk.ngay_tai_kham,
            nv.ho_ten AS bac_si,
            ck.ten_khoa AS khoa,
            p.ten_phong AS phong
        FROM phieu_kham pk
        JOIN bac_si bs ON pk.bac_si_id = bs.id
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        JOIN phong_kham p ON pk.phong_kham_id = p.id
        JOIN chuyen_khoa ck ON p.chuyen_khoa_id = ck.id
        WHERE pk.benh_nhan_id = ?
        ORDER BY pk.thoi_gian_kham DESC
    ''', (patient_id,))
    encounters = [dict(r) for r in cursor.fetchall()]

    for enc in encounters:
        # Lấy cận lâm sàng
        cursor.execute('''
            SELECT 
                dv.ten_dich_vu AS ten,
                dv.loai_dich_vu AS loai,
                ct.ket_qua,
                ct.ktv_thuc_hien AS bac_si_thuc_hien,
                ct.trang_thai
            FROM phieu_chi_dinh cd
            JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
            JOIN dich_vu dv ON ct.dich_vu_id = dv.id
            WHERE cd.phieu_kham_id = ?
        ''', (enc['id'],))
        enc['can_lam_sang'] = [dict(r) for r in cursor.fetchall()]

        # Lấy đơn thuốc
        cursor.execute('''
            SELECT 
                t.ten_thuoc AS ten,
                t.hoat_chat,
                ct.so_luong,
                t.don_vi_tinh,
                ct.cach_dung
            FROM don_thuoc dt
            JOIN chi_tiet_don_thuoc ct ON dt.id = ct.don_thuoc_id
            JOIN thuoc t ON ct.thuoc_id = t.id
            WHERE dt.phieu_kham_id = ?
        ''', (enc['id'],))
        dt_rows = [dict(r) for r in cursor.fetchall()]
        for dt_row in dt_rows:
            dt_row['so_luong'] = f"{dt_row['so_luong']} {dt_row['don_vi_tinh']}"
        enc['don_thuoc'] = dt_rows

        if enc.get('ngay_tai_kham'):
            enc['lich_tai_kham'] = f"{enc['ngay_tai_kham']} (Sau 14 ngày)"
        else:
            enc['lich_tai_kham'] = None

    conn.close()
    return encounters

def authenticate_user(username, password):
    """Xác thực đăng nhập tài khoản từ CSDL."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tìm kiếm theo username hoặc số điện thoại
    cursor.execute('''
        SELECT t.*, v.ma_vai_tro, v.ten_vai_tro
        FROM tai_khoan t
        JOIN vai_tro v ON t.vai_tro_id = v.id
        WHERE t.username = ? OR t.sdt = ?
    ''', (username, username))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        return None

    # Kiểm tra mật khẩu (hỗ trợ hash hoặc mật khẩu cũ/mặc định)
    stored_hash = user_row['password']
    is_valid = False
    try:
        is_valid = check_password_hash(stored_hash, password)
    except Exception:
        is_valid = (stored_hash == password)

    if not is_valid:
        conn.close()
        return None

    # Cập nhật thời gian đăng nhập cuối
    cursor.execute('''
        UPDATE tai_khoan SET lan_dang_nhap_cuoi = ? WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_row['id']))
    conn.commit()

    user_info = {
        'id': user_row['id'],
        'username': user_row['username'],
        'vai_tro': user_row['ma_vai_tro'],
        'ten_vai_tro': user_row['ten_vai_tro'],
        'sdt': user_row['sdt']
    }

    # Nếu là Bác sĩ / Nhân viên
    if user_row['ma_vai_tro'] in ['ADMIN', 'LETAN', 'BACSI', 'DUOCSI', 'KTV']:
        cursor.execute('''
            SELECT nv.ma_nhan_vien, nv.ho_ten, nv.chuc_vu, nv.email, bs.id AS bac_si_id, bs.hoc_vi
            FROM nhan_vien nv
            LEFT JOIN bac_si bs ON bs.nhan_vien_id = nv.id
            WHERE nv.tai_khoan_id = ?
        ''', (user_row['id'],))
        staff_row = cursor.fetchone()
        if staff_row:
            user_info['ho_ten'] = staff_row['ho_ten']
            user_info['chuc_vu'] = staff_row['chuc_vu']
            user_info['ma_nhan_vien'] = staff_row.get('ma_nhan_vien')
            user_info['email'] = staff_row.get('email') or user_row.get('email')
            user_info['bac_si_id'] = staff_row['bac_si_id']
            user_info['hoc_vi'] = staff_row['hoc_vi']
        else:
            user_info['ho_ten'] = user_row['username']

    # Nếu là Bệnh nhân
    elif user_row['ma_vai_tro'] == 'BENHNHAN':
        cursor.execute('''
            SELECT id, ma_benh_nhan, ho_ten, sdt, email, cccd, bhyt, nhom_mau
            FROM benh_nhan WHERE tai_khoan_id = ?
        ''', (user_row['id'],))
        patient_row = cursor.fetchone()
        if patient_row:
            user_info['ho_ten'] = patient_row['ho_ten']
            user_info['patient_id'] = patient_row['id']
            user_info['ma_benh_nhan'] = patient_row['ma_benh_nhan']
        else:
            user_info['ho_ten'] = user_row['username']

    conn.close()
    return user_info

def register_patient_account(ho_ten, sdt, ngay_sinh, gioi_tinh, cccd, email, bhyt, password):
    """Đăng ký tài khoản và tạo hồ sơ bệnh nhân mới vào CSDL."""
    conn = get_db()
    cursor = conn.cursor()

    # Kiểm tra SĐT hoặc CCCD đã tồn tại
    cursor.execute('SELECT id FROM tai_khoan WHERE username = ? OR sdt = ?', (sdt, sdt))
    if cursor.fetchone():
        conn.close()
        return False, 'Số điện thoại này đã được đăng ký tài khoản!'

    # Tạo tài khoản
    hashed_pwd = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO tai_khoan (vai_tro_id, username, password, email, sdt, trang_thai)
        VALUES (6, ?, ?, ?, ?, 1)
    ''', (sdt, hashed_pwd, email, sdt))
    tai_khoan_id = cursor.lastrowid

    # Tạo mã bệnh nhân
    cursor.execute('SELECT COUNT(*) as cnt FROM benh_nhan')
    next_id = cursor.fetchone()['cnt'] + 1
    ma_benh_nhan = f"BN2609{str(next_id).zfill(3)}"

    # Tạo hồ sơ bệnh nhân
    cursor.execute('''
        INSERT INTO benh_nhan (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, co_tai_khoan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt))
    benh_nhan_id = cursor.lastrowid

    # Khởi tạo sinh hiệu mặc định
    cursor.execute('''
        INSERT INTO chi_so_sinh_ton (benh_nhan_id) VALUES (?)
    ''', (benh_nhan_id,))

    conn.commit()
    conn.close()
    return True, 'Đăng ký tài khoản bệnh nhân thành công!'

def reset_patient_password(patient_id, new_password):
    """Cấp lại mật khẩu mới cho bệnh nhân."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT tai_khoan_id, sdt, ho_ten FROM benh_nhan WHERE id = ?', (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        conn.close()
        return False, 'Không tìm thấy bệnh nhân!'

    hashed_pwd = generate_password_hash(new_password)
    tai_khoan_id = patient['tai_khoan_id']

    if tai_khoan_id:
        cursor.execute('UPDATE tai_khoan SET password = ? WHERE id = ?', (hashed_pwd, tai_khoan_id))
    else:
        # Nếu chưa có tài khoản thì tạo tài khoản mới dựa trên SĐT
        username = patient['sdt'] or f"bn_{patient_id}"
        cursor.execute('''
            INSERT INTO tai_khoan (vai_tro_id, username, password, sdt, trang_thai)
            VALUES (6, ?, ?, ?, 1)
        ''', (username, hashed_pwd, patient['sdt']))
        new_tk_id = cursor.lastrowid
        cursor.execute('UPDATE benh_nhan SET tai_khoan_id = ?, co_tai_khoan = 1 WHERE id = ?', (new_tk_id, patient_id))

    conn.commit()
    conn.close()
    return True, f'Đã cập nhật mật khẩu mới cho {patient["ho_ten"]}'

def get_all_appointments():
    """Lấy danh sách lịch hẹn toàn hệ thống."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            lh.*,
            bn.ho_ten AS ho_ten_benh_nhan,
            bn.sdt AS sdt_benh_nhan,
            bn.ma_benh_nhan,
            nv.ho_ten AS ho_ten_bac_si,
            ck.ten_khoa,
            pk.ten_phong
        FROM lich_hen lh
        JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
        LEFT JOIN bac_si bs ON lh.bac_si_id = bs.id
        LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        JOIN chuyen_khoa ck ON lh.chuyen_khoa_id = ck.id
        LEFT JOIN phong_kham pk ON lh.phong_kham_id = pk.id
        ORDER BY lh.ngay_hen DESC, lh.gio_hen DESC
    ''')
    appointments = [dict(r) for r in cursor.fetchall()]
    for a in appointments:
        if a.get('ngay_hen'):
            a['ngay_hen'] = str(a['ngay_hen'])
        if a.get('gio_hen'):
            a['gio_hen'] = str(a['gio_hen'])
    conn.close()
    return appointments

def create_appointment(benh_nhan_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do_kham):
    """Tạo lịch hẹn khám mới."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as cnt FROM lich_hen')
    next_id = cursor.fetchone()['cnt'] + 1
    ma_lich_hen = f"LH2609{str(next_id).zfill(3)}"

    cursor.execute('''
        INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Chờ xác nhận')
    ''', (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, ngay_hen, gio_hen, ly_do_kham))
    
    conn.commit()
    conn.close()
    return True, ma_lich_hen

def get_all_medicines():
    """Lấy danh mục thuốc trong kho dược."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM thuoc ORDER BY id ASC')
    medicines = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return medicines

def get_all_services():
    """Lấy danh mục dịch vụ khám và cận lâm sàng."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dv.*, ck.ten_khoa 
        FROM dich_vu dv 
        LEFT JOIN chuyen_khoa ck ON dv.chuyen_khoa_id = ck.id 
        ORDER BY dv.id ASC
    ''')
    services = [dict(r) for r in cursor.fetchall()]
    for s in services:
        s['gia_dich_vu'] = s.get('don_gia') or 0
    conn.close()
    return services

def get_all_invoices():
    """Lấy danh sách hóa đơn viện phí."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            hd.*,
            bn.ho_ten AS ho_ten_benh_nhan,
            bn.ma_benh_nhan,
            bn.bhyt
        FROM hoa_don hd
        JOIN benh_nhan bn ON hd.benh_nhan_id = bn.id
        ORDER BY hd.id DESC
    ''')
    invoices = [dict(r) for r in cursor.fetchall()]
    for inv in invoices:
        inv['thoi_gian_tao'] = str(inv.get('thoi_gian_thanh_toan') or datetime.now().strftime('%d/%m/%Y %H:%M'))
        if inv.get('thoi_gian_thanh_toan'):
            inv['thoi_gian_thanh_toan'] = str(inv['thoi_gian_thanh_toan'])
        inv['tien_bhyt_chi_tra'] = float(inv.get('tien_bhyt') or 0)
        inv['tong_tien'] = float(inv.get('tong_tien') or 0)
        inv['thanh_tien'] = float(inv.get('thanh_tien') or 0)
        inv['giam_gia'] = float(inv.get('giam_gia') or 0)
        cursor.execute('SELECT ten_khoan_thu FROM chi_tiet_hoa_don WHERE hoa_don_id = ?', (inv['id'],))
        items = [r['ten_khoan_thu'] for r in cursor.fetchall()]
        inv['khoan_muc'] = ", ".join(items) if items else 'Chi phí khám bệnh & thuốc điều trị'
    conn.close()
    return invoices

def get_all_lab_orders():
    """Lấy danh sách phiếu chỉ định cận lâm sàng toàn hệ thống."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            cd.id,
            cd.ma_chi_dinh,
            cd.thoi_gian_chi_dinh,
            cd.ghi_chu,
            cd.trang_thai,
            pk.id AS phieu_kham_id,
            bn.id AS patient_id,
            bn.ho_ten AS benh_nhan,
            bn.ma_benh_nhan AS ma_bn,
            nv.ho_ten AS bac_si,
            ct.id AS chi_tiet_id,
            dv.ten_dich_vu AS dich_vu,
            dv.loai_dich_vu AS loai,
            ct.ket_qua,
            ct.ktv_thuc_hien,
            ct.trang_thai AS trang_thai_ct
        FROM phieu_chi_dinh cd
        JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
        JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
        JOIN bac_si bs ON cd.bac_si_id = bs.id
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        LEFT JOIN chi_tiet_chi_dinh ct ON cd.id = ct.phieu_chi_dinh_id
        LEFT JOIN dich_vu dv ON ct.dich_vu_id = dv.id
        ORDER BY cd.id DESC
    ''')
    orders = [dict(r) for r in cursor.fetchall()]
    for o in orders:
        if o.get('thoi_gian_chi_dinh'):
            o['thoi_gian_chi_dinh'] = str(o['thoi_gian_chi_dinh'])
    conn.close()
    return orders

def get_all_prescriptions():
    """Lấy danh sách đơn thuốc chờ và đã phát."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            dt.id,
            dt.ma_don_thuoc AS ma_don,
            dt.thoi_gian_ke AS gio,
            dt.trang_thai,
            dt.loi_dan,
            bn.id AS patient_id,
            bn.ho_ten AS benh_nhan,
            bn.ma_benh_nhan AS ma_bn,
            nv.ho_ten AS bac_si
        FROM don_thuoc dt
        JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
        JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
        JOIN bac_si bs ON dt.bac_si_id = bs.id
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        ORDER BY dt.id DESC
    ''')
    prescriptions = [dict(r) for r in cursor.fetchall()]
    for p in prescriptions:
        if p.get('gio'):
            p['gio'] = str(p['gio'])
        cursor.execute('''
            SELECT ct.*, t.ten_thuoc, t.hoat_chat, t.don_vi_tinh
            FROM chi_tiet_don_thuoc ct
            JOIN thuoc t ON ct.thuoc_id = t.id
            WHERE ct.don_thuoc_id = ?
        ''', (p['id'],))
        med_rows = [dict(r) for r in cursor.fetchall()]
        if med_rows:
            p['thuoc'] = ", ".join([f"{m['ten_thuoc']} x {m['so_luong']} {m['don_vi_tinh']}" for m in med_rows])
        else:
            p['thuoc'] = 'Theo đơn bác sĩ điều trị'
    conn.close()
    return prescriptions

def get_articles(limit=10):
    """Lấy danh sách bài viết truyền thông y tế."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bv.*, nv.ho_ten AS tac_gia
        FROM bai_viet bv
        LEFT JOIN nhan_vien nv ON bv.tac_gia_id = nv.id
        WHERE bv.trang_thai = 1
        ORDER BY bv.ngay_dang DESC
    ''')
    articles = [dict(r) for r in cursor.fetchall()][:limit]
    conn.close()
    return articles

def get_dashboard_stats():
    """Lấy số liệu thống kê thời gian thực cho trang Dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total_patients FROM benh_nhan')
    total_patients = cursor.fetchone()['total_patients']

    cursor.execute("SELECT COUNT(*) as waiting_appointments FROM lich_hen WHERE trang_thai = 'Chờ xác nhận'")
    waiting_appointments = cursor.fetchone()['waiting_appointments']

    cursor.execute("SELECT COUNT(*) as completed_today FROM phieu_kham")
    completed_today = cursor.fetchone()['completed_today']

    cursor.execute("SELECT COALESCE(SUM(thanh_tien), 0) as total_revenue FROM hoa_don WHERE trang_thai = 'Đã thanh toán'")
    total_revenue = cursor.fetchone()['total_revenue']

    conn.close()
    return {
        'total_patients': total_patients,
        'waiting_appointments': waiting_appointments,
        'completed_today': completed_today,
        'total_revenue': total_revenue
    }

# Tự động khởi tạo database khi import
init_db()
