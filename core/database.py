import os
import sqlite3
from datetime import datetime, date, time
from decimal import Decimal
import config

class UnifiedCursor:
    """Cursor bọc chuẩn hóa tương thích giữa SQLite, SQL Server và MySQL."""
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
    """Kết nối cơ sở dữ liệu thống nhất cho toàn bộ hệ thống."""
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
    """Tạo kết nối tới CSDL theo DB_ENGINE được chỉ định trong config.py."""
    engine = getattr(config, 'DB_ENGINE', 'sqlserver')

    if engine == 'sqlite':
        conn = sqlite3.connect(config.DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return UnifiedConnection(conn, 'sqlite')

    elif engine == 'sqlserver':
        import pyodbc
        cfg = config.SQLSERVER_CONFIG
        if cfg.get('trusted_connection', 'yes').lower() == 'yes':
            conn_str = (
                f"DRIVER={cfg['driver']};"
                f"SERVER={cfg['server']};"
                f"DATABASE={cfg['database']};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={cfg['driver']};"
                f"SERVER={cfg['server']};"
                f"DATABASE={cfg['database']};"
                f"UID={cfg['uid']};"
                f"PWD={cfg['pwd']};"
            )
        conn = pyodbc.connect(conn_str)
        return UnifiedConnection(conn, 'sqlserver')

    elif engine == 'mysql':
        import pymysql
        cfg = config.MYSQL_CONFIG
        conn = pymysql.connect(
            host=cfg['host'],
            port=cfg.get('port', 3306),
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database'],
            charset=cfg.get('charset', 'utf8mb4'),
            autocommit=False
        )
        return UnifiedConnection(conn, 'mysql')

    else:
        raise ValueError(f"Hệ CSDL không hợp lệ: {engine}")

def init_sqlite_db():
    """Khởi tạo cấu trúc bảng và nạp dữ liệu tối thiểu cho SQLite."""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

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
        phieu_kham_id INTEGER NOT NULL,
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
        tong_tien REAL DEFAULT 0.0,
        tien_bhyt REAL DEFAULT 0.0,
        giam_gia REAL DEFAULT 0.0,
        thanh_tien REAL DEFAULT 0.0,
        hinh_thuc_thanh_toan TEXT DEFAULT 'Tiền mặt',
        trang_thai TEXT DEFAULT 'Đã thanh toán',
        thoi_gian_thanh_toan DATETIME DEFAULT CURRENT_TIMESTAMP,
        nhan_vien_thu TEXT,
        FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id),
        FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
    );

    CREATE TABLE IF NOT EXISTS chi_tiet_hoa_don (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hoa_don_id INTEGER NOT NULL,
        loai_khoan_thu TEXT NOT NULL,
        ten_khoan_thu TEXT NOT NULL,
        tham_chieu_id INTEGER,
        so_luong INTEGER DEFAULT 1,
        don_gia REAL DEFAULT 0.0,
        thanh_tien REAL DEFAULT 0.0,
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

    # Kiểm tra nếu chưa có tài khoản nào thì nạp seed tối thiểu (1 admin, 1 bệnh nhân)
    cursor.execute("SELECT COUNT(*) as cnt FROM tai_khoan")
    if cursor.fetchone()['cnt'] == 0:
        _seed_minimal_data(cursor)
        conn.commit()

    conn.close()

def _seed_minimal_data(cursor):
    """Nạp danh mục cơ sở và đúng 1 tài khoản admin, 1 tài khoản bệnh nhân."""
    # 1. Bảng Vai trò
    cursor.executemany('''
        INSERT OR IGNORE INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (?, ?, ?, ?)
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
        INSERT OR IGNORE INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh) VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'KHOA_NOI', 'Khoa Nội Tổng Quát', 'Khám, chẩn đoán và điều trị bệnh lý tim mạch, tiêu hóa, hô hấp', 'fa-stethoscope', 150000.0),
        (2, 'KHOA_NGOAI', 'Khoa Ngoại Tổng Quát', 'Khám và điều trị ngoại khoa, tiểu phẫu, xử lý vết thương', 'fa-syringe', 150000.0),
        (3, 'KHOA_NHI', 'Khoa Nhi', 'Chăm sóc và điều trị chuyên sâu bệnh lý trẻ em, tư vấn dinh dưỡng', 'fa-baby', 120000.0),
        (4, 'KHOA_RHM', 'Khoa Răng Hàm Mặt', 'Nha khoa tổng quát, nhổ răng khôn, niềng răng, cạo vôi răng', 'fa-tooth', 150000.0),
        (5, 'KHOA_SAN', 'Khoa Sản - Phụ Khoa', 'Quản lý thai kỳ, siêu âm 4D, tầm soát và điều trị phụ khoa', 'fa-person-pregnant', 180000.0),
        (6, 'KHOA_TMH', 'Khoa Tai Mũi Họng', 'Nội soi tai mũi họng, điều trị viêm xoang, viêm họng hạt', 'fa-head-side-cough', 150000.0),
        (7, 'KHOA_MAT', 'Khoa Mắt', 'Đo tật khúc xạ, khám và điều trị bệnh lý đáy mắt, giác mạc', 'fa-eye', 150000.0),
        (8, 'KHOA_CLS', 'Khoa Cận Lâm Sàng', 'Trung tâm xét nghiệm hóa sinh, huyết học và chẩn đoán hình ảnh', 'fa-vial', 100000.0)
    ])

    # 3. Phòng khám vật lý
    cursor.executemany('''
        INSERT OR IGNORE INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (?, ?, ?, ?, ?, ?)
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

    # 4. Dịch vụ y tế cơ bản
    cursor.executemany('''
        INSERT OR IGNORE INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 'DV_KHAM_NOI', 'Khám Nội Tổng Quát', 'Khám bệnh', 150000.0, 80, 'Khám và tư vấn toàn diện các bệnh lý nội khoa'),
        (2, 3, 'DV_KHAM_NHI', 'Khám Nhi Khoa', 'Khám bệnh', 120000.0, 80, 'Khám và tư vấn sức khỏe trẻ em'),
        (3, 2, 'DV_KHAM_NGOAI', 'Khám Ngoại Khoa', 'Khám bệnh', 150000.0, 80, 'Khám và tư vấn tiểu phẫu ngoại khoa'),
        (4, 4, 'DV_NHO_RANG', 'Tiểu phẫu Nhổ răng khôn', 'Thủ thuật', 1000000.0, 0, 'Nhổ răng khôn mọc lệch, không đau'),
        (5, 4, 'DV_CAO_VOI', 'Cạo vôi răng & Đánh bóng', 'Thủ thuật', 200000.0, 0, 'Làm sạch mảng bám cao răng bằng sóng siêu âm'),
        (6, 8, 'DV_SIEU_AM', 'Siêu âm Doppler màu ổ bụng tổng quát', 'Chẩn đoán hình ảnh', 250000.0, 50, 'Khảo sát gan, mật, tụy, lách, thận'),
        (7, 8, 'DV_XN_MAU', 'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', 'Xét nghiệm', 150000.0, 80, 'Kiểm tra hồng cầu, bạch cầu, tiểu cầu'),
        (8, 8, 'DV_XN_NT', 'Tổng phân tích nước tiểu 10 thông số', 'Xét nghiệm', 100000.0, 80, 'Kiểm tra đường, đạm nước tiểu'),
        (9, 8, 'DV_XQUANG', 'Chụp X-Quang Tim Phổi thẳng kỹ thuật số', 'Chẩn đoán hình ảnh', 200000.0, 70, 'Kiểm tra tổn thương nhu mô phổi'),
        (10, 8, 'DV_ECG', 'Đo điện tim đồ 12 chuyển đạo (ECG)', 'Thăm dò chức năng', 150000.0, 70, 'Khảo sát nhịp xoang tim')
    ])

    # 5. Danh mục thuốc ban đầu
    cursor.executemany('''
        INSERT OR IGNORE INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'TH001', 'Paracetamol 500mg', 'Paracetamol', '500mg', 'Viên', 2000.0, 5000, 'Dược Hậu Giang', 'Việt Nam', 'Uống 1-2 viên khi sốt trên 38.5°C'),
        (2, 'TH002', 'Amoxicillin 500mg', 'Amoxicillin trihydrat', '500mg', 'Viên', 3000.0, 2000, 'Imexpharm', 'Việt Nam', 'Kháng sinh: Uống 1 viên sau ăn, ngày 2 lần'),
        (3, 'TH003', 'Oresol 245', 'Glucose, Natri clorid, Kali clorid', '245 mOsm/L', 'Gói', 5000.0, 1000, 'Traphaco', 'Việt Nam', 'Pha 1 gói với 200ml nước đun sôi để nguội'),
        (4, 'TH004', 'Loratadin 10mg', 'Loratadin', '10mg', 'Viên', 4000.0, 1500, 'Pymepharco', 'Việt Nam', 'Thuốc chống dị ứng: Uống 1 viên vào buổi tối'),
        (5, 'TH005', 'Esomeprazole 40mg', 'Esomeprazole magnesium', '40mg', 'Viên', 12000.0, 3000, 'AstraZeneca', 'Thụy Điển', 'Uống 1 viên trước ăn sáng 30 phút'),
        (6, 'TH006', 'Phosphalugel 20g', 'Aluminium phosphate', '20g', 'Gói', 5000.0, 2500, 'Boehringer Ingelheim', 'Pháp', 'Uống 1 gói khi đau tức thượng vị'),
        (7, 'TH007', 'Men vi sinh Enterogermina', 'Bacillus clausii', '2 tỷ bào tử/5ml', 'Ống', 9000.0, 1200, 'Sanofi', 'Ý', 'Uống 1-2 ống/ngày sau ăn'),
        (8, 'TH008', 'Ibuprofen 400mg', 'Ibuprofen', '400mg', 'Viên', 3500.0, 2500, 'Stada', 'Việt Nam', 'Kháng viêm giảm đau, uống sau ăn no'),
        (9, 'TH009', 'Siro ho thảo dược Prospan', 'Cao khô lá thường xuân', '100ml', 'Chai', 75000.0, 300, 'Engelhard', 'Đức', 'Uống 5ml/lần, ngày 3 lần sau ăn'),
        (10, 'TH010', 'Nước muối sinh lý NaCl 0.9%', 'Natri Clorid 0.9%', '500ml', 'Chai', 10000.0, 800, 'Pharmedic', 'Việt Nam', 'Súc miệng họng hoặc rửa vết thương')
    ])

    # 6. ĐÚNG 1 TÀI KHOẢN ADMIN (admin / admin123)
    admin_pwd_hash = 'scrypt:32768:8:1$wte2IwGnBVO1lRWL$3da8cd29b71656229c22086ff7164745647f790916b2f3949a826972b6c8f4896f4fd90b2856affb5af79c1274b86fc0d20e1ee0da464623a7117faa4984e03c'
    cursor.execute('''
        INSERT OR IGNORE INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai)
        VALUES (1, 1, 'admin', ?, 'admin@phongkham.com', '0999999999', 1)
    ''', (admin_pwd_hash,))
    cursor.execute('''
        INSERT OR IGNORE INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu)
        VALUES (1, 1, 'NV001', 'Admin Hệ Thống', 1, '1988-01-01', '0999999999', 'admin@phongkham.com', '079088000001', '140 Lê Trọng Tấn, Tân Phú, TP.HCM', 'Quản trị viên')
    ''')

    # 7. ĐÚNG 1 TÀI KHOẢN BỆNH NHÂN (0901234567 / 123456)
    patient_pwd_hash = 'scrypt:32768:8:1$pj1f2Ryp5cA64fb5$f5bf70980bc4c70015007a5a00f2e5ccc0fc41168d5dbc0bf6bf6ba432babaf7f3f5f0c487e79171c2d7d31de72f4b4fc68053e117a8622d244506fd8a0dca79'
    cursor.execute('''
        INSERT OR IGNORE INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai)
        VALUES (2, 6, '0901234567', ?, 'baonam@gmail.com', '0901234567', 1)
    ''', (patient_pwd_hash,))
    cursor.execute('''
        INSERT OR IGNORE INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, di_ung, tien_su_benh, co_tai_khoan)
        VALUES (1, 2, 'BN2609001', 'Hoàng Bảo Nam', '1990-05-12', 'Nam', '0901234567', 'baonam@gmail.com', '079090000001', 'GD4797931100001', 'Quận 1, TP.HCM', 'O+', 'Không có', 'Đau dạ dày nhẹ', 1)
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi)
        VALUES (1, 1, '75 lần/phút', '36.8 °C', '120/80 mmHg', '99 %', '18 lần/phút', '170 cm', '65 kg', '22.5 (Bình thường)')
    ''')

    # 8. Bài viết y tế mẫu
    cursor.executemany('''
        INSERT OR IGNORE INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, ngay_dang, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', 'benh-cam-cum-mua-giao-mua', 'Cẩm Nang Y Tế', 'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', 'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', 'cam-cum.jpg', 320, '2026-09-20 08:00:00', 1),
        (2, 1, 'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', 'cham-soc-rang-mieng-cho-tre', 'Nhi Khoa', 'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', 'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng phù hợp lứa tuổi...', 'rang-mieng-tre.jpg', 215, '2026-09-21 09:30:00', 1),
        (3, 1, 'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', 'kham-suc-khoe-tong-quat-dinh-ky', 'Tin Tức Phòng Khám', 'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', 'Nội dung chi tiết về các gói khám tổng quát định kỳ...', 'kham-tong-quat.jpg', 580, '2026-09-23 10:00:00', 1)
    ])

def init_db():
    """Kiểm tra và khởi tạo kết nối CSDL khi ứng dụng khởi chạy."""
    engine = getattr(config, 'DB_ENGINE', 'sqlserver')
    if engine == 'sqlite':
        init_sqlite_db()
        print("[Database] Khoi tao SQLite thanh cong!")
    elif engine == 'sqlserver':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM tai_khoan")
            row = cursor.fetchone()
            print(f"[Database] Ket noi Microsoft SQL Server thanh cong! So tai khoan: {row['cnt']}")
            conn.close()
        except Exception as e:
            print("[Database] Canh bao ket noi SQL Server:", e)
    elif engine == 'mysql':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM tai_khoan")
            row = cursor.fetchone()
            print(f"[Database] Ket noi MySQL thanh cong! So tai khoan: {row['cnt']}")
            conn.close()
        except Exception as e:
            print("[Database] Canh bao ket noi MySQL:", e)
