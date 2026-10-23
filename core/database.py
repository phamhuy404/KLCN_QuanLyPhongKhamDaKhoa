import os
import pyodbc
from datetime import datetime, date, time
from decimal import Decimal
import config

class UnifiedCursor:
    """Cursor bọc chuẩn hóa tương thích cho Microsoft SQL Server."""
    def __init__(self, raw_cursor):
        self._cur = raw_cursor
        self.lastrowid = None

    def execute(self, sql, params=()):
        if params:
            self._cur.execute(sql, params)
        else:
            self._cur.execute(sql)

        # Trích xuất SCOPE_IDENTITY() hoặc @@IDENTITY khi chạy INSERT
        if sql.strip().upper().startswith('INSERT'):
            try:
                self._cur.execute('SELECT @@IDENTITY')
                row = self._cur.fetchone()
                self.lastrowid = int(row[0]) if row and row[0] is not None else None
            except Exception:
                self.lastrowid = None
        else:
            self.lastrowid = None
        return self

    def executemany(self, sql, seq_of_params):
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
    """Kết nối cơ sở dữ liệu Microsoft SQL Server."""
    def __init__(self, raw_conn):
        self._conn = raw_conn
        self._engine = 'sqlserver'

    def cursor(self):
        return UnifiedCursor(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

def get_db():
    """Tạo kết nối trực tiếp tới Microsoft SQL Server qua pyodbc."""
    cfg = config.SQLSERVER_CONFIG
    servers_to_try = [cfg.get('server', 'localhost'), 'localhost', r'.\SQLEXPRESS', r'localhost\SQLEXPRESS', '.']
    seen = set()
    unique_servers = [s for s in servers_to_try if s and not (s in seen or seen.add(s))]

    last_err = None
    for srv in unique_servers:
        if cfg.get('trusted_connection', 'yes').lower() == 'yes':
            conn_str = f"DRIVER={cfg['driver']};SERVER={srv};DATABASE={cfg['database']};Trusted_Connection=yes;"
        else:
            conn_str = f"DRIVER={cfg['driver']};SERVER={srv};DATABASE={cfg['database']};UID={cfg['uid']};PWD={cfg['pwd']};"
        try:
            conn = pyodbc.connect(conn_str, timeout=4)
            return UnifiedConnection(conn)
        except Exception as e:
            last_err = e
            continue
    raise last_err

def ensure_schema_updates(conn):
    """Đảm bảo các bảng, cột và chỉ mục trong Microsoft SQL Server luôn cập nhật đầy đủ."""
    try:
        cursor = conn.cursor()
        stmts = [
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tai_khoan') AND name = 'da_hoan_thien_ho_so') ALTER TABLE tai_khoan ADD da_hoan_thien_ho_so BIT DEFAULT 0;",
            "UPDATE tai_khoan SET da_hoan_thien_ho_so = 1 WHERE vai_tro_id IN (1, 2, 3, 4, 5);",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('thuoc') AND name = 'ton_kho_toi_thieu') ALTER TABLE thuoc ADD ton_kho_toi_thieu INT DEFAULT 20;",
            "UPDATE thuoc SET ton_kho_toi_thieu = 20 WHERE ton_kho_toi_thieu IS NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('benh_nhan') AND name = 'ghi_chu_nhom_mau') ALTER TABLE benh_nhan ADD ghi_chu_nhom_mau NVARCHAR(255) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('benh_nhan') AND name = 'avatar') ALTER TABLE benh_nhan ADD avatar NVARCHAR(500) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chuyen_khoa') AND name = 'trang_thai') ALTER TABLE chuyen_khoa ADD trang_thai BIT DEFAULT 1;",
            "UPDATE chuyen_khoa SET trang_thai = 1 WHERE trang_thai IS NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phong_kham') AND name = 'trang_thai') ALTER TABLE phong_kham ADD trang_thai BIT DEFAULT 1;",
            "UPDATE phong_kham SET trang_thai = 1 WHERE trang_thai IS NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dich_vu') AND name = 'trang_thai') ALTER TABLE dich_vu ADD trang_thai BIT DEFAULT 1;",
            "UPDATE dich_vu SET trang_thai = 1 WHERE trang_thai IS NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'trang_thai') ALTER TABLE lich_lam_viec ADD trang_thai BIT DEFAULT 1;",
            "UPDATE lich_lam_viec SET trang_thai = 1 WHERE trang_thai IS NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'nhan_vien_id') ALTER TABLE lich_lam_viec ADD nhan_vien_id INT NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'trang_thai_duyet') ALTER TABLE lich_lam_viec ADD trang_thai_duyet NVARCHAR(50) DEFAULT 'DA_DUYET';",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'ly_do_huy') ALTER TABLE lich_lam_viec ADD ly_do_huy NVARCHAR(MAX) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'nguoi_duyet_id') ALTER TABLE lich_lam_viec ADD nguoi_duyet_id INT NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'ngay_duyet') ALTER TABLE lich_lam_viec ADD ngay_duyet DATETIME NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('lich_lam_viec') AND name = 'ghi_chu') ALTER TABLE lich_lam_viec ADD ghi_chu NVARCHAR(MAX) NULL;",
            "UPDATE lich_lam_viec SET nhan_vien_id = (SELECT nhan_vien_id FROM bac_si WHERE bac_si.id = lich_lam_viec.bac_si_id) WHERE nhan_vien_id IS NULL AND bac_si_id IS NOT NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phan_hoi') AND name = 'chu_de') ALTER TABLE phan_hoi ADD chu_de NVARCHAR(100) DEFAULT N'Dịch vụ khám bệnh';",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phan_hoi') AND name = 'trang_thai') ALTER TABLE phan_hoi ADD trang_thai NVARCHAR(50) DEFAULT N'Chờ tiếp nhận';",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phan_hoi') AND name = 'tra_loi') ALTER TABLE phan_hoi ADD tra_loi NVARCHAR(MAX) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phan_hoi') AND name = 'ngay_tra_loi') ALTER TABLE phan_hoi ADD ngay_tra_loi DATETIME NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phan_hoi') AND name = 'nguoi_tra_loi') ALTER TABLE phan_hoi ADD nguoi_tra_loi NVARCHAR(100) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('thong_bao') AND name = 'lien_ket') ALTER TABLE thong_bao ADD lien_ket NVARCHAR(255) NULL;",
            """
            IF OBJECT_ID('lich_su_nhac_nho', 'U') IS NULL
            BEGIN
                CREATE TABLE lich_su_nhac_nho (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    lich_hen_id INT NULL,
                    phieu_kham_id INT NULL,
                    benh_nhan_id INT NULL,
                    loai_nhac NVARCHAR(50) NOT NULL,
                    ngay_nhac DATE NULL,
                    kenh_gui NVARCHAR(20) DEFAULT 'IN_APP',
                    trang_thai NVARCHAR(50) DEFAULT 'THANH_CONG',
                    loi_gui NVARCHAR(MAX) NULL,
                    thoi_gian_gui DATETIME DEFAULT GETDATE()
                );
            END
            """,
            """
            IF OBJECT_ID('lich_su_sao_luu', 'U') IS NULL
            BEGIN
                CREATE TABLE lich_su_sao_luu (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    loai_thao_tac NVARCHAR(20) NOT NULL,
                    ten_tap_tin NVARCHAR(255) NOT NULL,
                    duong_dan NVARCHAR(500) NULL,
                    loai_csdl NVARCHAR(50) NOT NULL,
                    dung_luong BIGINT DEFAULT 0,
                    nguoi_thuc_hien NVARCHAR(100) NULL,
                    trang_thai NVARCHAR(50) DEFAULT 'SUCCESS',
                    ghi_chu NVARCHAR(MAX) NULL,
                    thoi_gian DATETIME DEFAULT GETDATE()
                );
            END
            """,
            "IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_log') CREATE TABLE audit_log (id INT IDENTITY(1,1) PRIMARY KEY, table_name NVARCHAR(50) NOT NULL, row_id INT NOT NULL, action NVARCHAR(50) NOT NULL, performed_by INT NULL, performed_by_name NVARCHAR(100) NULL, performed_at DATETIME DEFAULT GETDATE(), reason NVARCHAR(MAX) NULL, before_json NVARCHAR(MAX) NULL, after_json NVARCHAR(MAX) NULL);",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'bac_si_duyet') ALTER TABLE chi_tiet_chi_dinh ADD bac_si_duyet NVARCHAR(100) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'thoi_gian_duyet') ALTER TABLE chi_tiet_chi_dinh ADD thoi_gian_duyet DATETIME NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'ghi_chu_duyet') ALTER TABLE chi_tiet_chi_dinh ADD ghi_chu_duyet NVARCHAR(MAX) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('chi_tiet_chi_dinh') AND name = 'nguoi_nhap') ALTER TABLE chi_tiet_chi_dinh ADD nguoi_nhap NVARCHAR(100) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'ly_do_huy') ALTER TABLE don_thuoc ADD ly_do_huy NVARCHAR(MAX) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'nguoi_huy') ALTER TABLE don_thuoc ADD nguoi_huy NVARCHAR(100) NULL;",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('don_thuoc') AND name = 'thoi_gian_huy') ALTER TABLE don_thuoc ADD thoi_gian_huy DATETIME NULL;",
            """
            IF OBJECT_ID('banner', 'U') IS NULL
            BEGIN
                CREATE TABLE banner (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    tieu_de NVARCHAR(255) NOT NULL,
                    phu_de NVARCHAR(255) NULL,
                    mo_ta NVARCHAR(MAX) NULL,
                    hinh_anh NVARCHAR(500) NOT NULL,
                    link_lien_ket NVARCHAR(255) DEFAULT '/booking',
                    text_nut NVARCHAR(50) DEFAULT N'Đăng ký khám ngay',
                    thu_tu INT DEFAULT 0,
                    trang_thai BIT DEFAULT 1,
                    ngay_tao DATETIME DEFAULT GETDATE()
                );
                INSERT INTO banner (tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai)
                VALUES 
                (N'Chăm sóc bằng tài năng, y đức và sự thấu cảm', N'Tiêu chuẩn chất lượng quốc tế', N'Bệnh viện Đa khoa Quốc tế H2T Healthcare mang đến trải nghiệm khám chữa bệnh chuẩn mực với các chuyên gia y tế đầu ngành và công nghệ bệnh án điện tử thông minh.', 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1600', '/booking', N'ĐĂNG KÝ KHÁM NGAY', 1, 1),
                (N'Đội ngũ chuyên gia và Bác sĩ đầu ngành', N'Chuyên môn vững vàng', N'Hội tụ đội ngũ giáo sư, tiến sĩ, bác sĩ chuyên khoa giàu kinh nghiệm, tận tâm vì sức khỏe toàn diện của bệnh nhân và gia đình.', 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=1600', '#bac-si', N'TÌM BÁC SĨ CHUYÊN KHOA', 2, 1),
                (N'Hệ thống Bệnh án điện tử EMR 360°', N'Công nghệ y tế số 4.0', 'Tra cứu lịch sử khám chữa bệnh, kết quả cận lâm sàng và toa thuốc trực tuyến mọi lúc mọi nơi nhanh chóng, bảo mật tuyệt đối.', 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1600', '/patient', N'CỔNG THÔNG TIN BỆNH NHÂN', 3, 1);
            END
            """
        ]
        for s in stmts:
            cursor.execute(s)
        conn.commit()
    except Exception as e:
        print("[Database] Luu y cap nhat schema SQL Server:", e)

ensure_patient_blood_columns = ensure_schema_updates

def init_db():
    """Kiểm tra và khởi tạo kết nối CSDL Microsoft SQL Server."""
    try:
        conn = get_db()
        ensure_schema_updates(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM tai_khoan")
        row = cursor.fetchone()
        print(f"[Database] Ket noi Microsoft SQL Server thanh cong! So tai khoan: {row['cnt']}")
        conn.close()
    except Exception as e:
        print("[Database] Canh bao ket noi Microsoft SQL Server:", e)
