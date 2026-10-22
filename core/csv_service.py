import csv
import io
from datetime import datetime
from core.database import get_db

class CSVService:
    """Dịch vụ nhập/xuất tệp CSV với mã hóa UTF-8-SIG (tương thích hoàn hảo với Microsoft Excel)."""

    MODULE_CONFIGS = {
        'medicines': {
            'name': 'Danh sách thuốc & vật tư y tế',
            'headers': ['Mã Thuốc', 'Tên Thuốc', 'Hoạt Chất', 'Hàm Lượng', 'Đơn Vị Tính', 'Đơn Giá', 'Số Lượng', 'Hãng Sản Xuất', 'Nước Sản Xuất', 'Hướng Dẫn Sử Dụng'],
            'sample_rows': [
                ['TH011', 'Panadol Extra Đỏ', 'Paracetamol, Caffeine', '500mg/65mg', 'Viên', 2500, 500, 'GSK', 'Úc', 'Uống 1-2 viên sau ăn khi đau đầu'],
                ['TH012', 'Augmentin 1g', 'Amoxicillin, Acid Clavulanic', '1000mg', 'Viên', 18000, 200, 'GSK', 'Pháp', 'Uống 1 viên sau ăn, ngày 2 lần']
            ]
        },
        'services': {
            'name': 'Danh mục dịch vụ kỹ thuật y tế',
            'headers': ['Mã Dịch Vụ', 'Tên Dịch Vụ', 'Chuyên Khoa ID', 'Loại Dịch Vụ', 'Đơn Giá', 'BHYT Chi Trả (%)', 'Mô Tả'],
            'sample_rows': [
                ['DV_NOISOI_DD', 'Nội soi dạ dày không đau', 1, 'Thủ thuật', 950000, 50, 'Nội soi đường tiêu hóa trên có tiền mê'],
                ['DV_TEST_HP', 'Test hơi thở tìm vi khuẩn HP', 1, 'Xét nghiệm', 400000, 0, 'Xét nghiệm hơi thở C13 chẩn đoán HP']
            ]
        },
        'articles': {
            'name': 'Danh mục bài viết cẩm nang y khoa',
            'headers': ['Tiêu Đề', 'Slug', 'Danh Mục', 'Tóm Tắt', 'Nội Dung', 'Hình Ảnh', 'Lượt Xem', 'Trạng Thái'],
            'sample_rows': [
                ['Cách nhận biết sớm đột quỵ não F.A.S.T', 'cach-nhan-biet-som-dot-quy-nao-fast', 'Cẩm Nang Y Tế', 'Dấu hiệu nhận biết sớm đột quỵ giúp cứu sống người bệnh trong khung giờ vàng.', 'Nội dung chi tiết quy tắc FAST: Face, Arm, Speech, Time...', 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1600', 120, 1],
                ['Dinh dưỡng khoa học cho người đái tháo đường', 'dinh-duong-cho-nguoi-dai-thao-duong', 'Tin Tức Phòng Khám', 'Thực đơn cân bằng giúp ổn định đường huyết hàng ngày hiệu quả.', 'Nội dung thực đơn mẫu và lời khuyên từ bác sĩ chuyên khoa dinh dưỡng...', 'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=1600', 85, 1]
            ]
        },
        'accounts': {
            'name': 'Danh sách tài khoản người dùng & nhân sự',
            'headers': ['Tên Đăng Nhập', 'Mật Khẩu Mặc Định', 'Họ Và Tên', 'Mã Vai Trò (ADMIN/LETAN/BACSI/DUOCSI/KTV/BENHNHAN)', 'Số Điện Thoại', 'Email', 'CCCD', 'Chức Vụ', 'Địa Chỉ'],
            'sample_rows': [
                ['letan_thu', 'Password@123', 'Hoàng Minh Thư', 'LETAN', '0908889911', 'thu.letan@h2tcare.vn', '079198000999', 'Nhân viên tiếp đón quầy B', 'Quận 3, TP.HCM'],
                ['bs_trung', 'Password@123', 'BS. Nguyễn Văn Trung', 'BACSI', '0918776655', 'trung.bs@h2tcare.vn', '079192000888', 'Bác sĩ chuyên khoa Tim mạch', 'Quận 1, TP.HCM']
            ]
        },
        'appointments': {
            'name': 'Danh sách lịch hẹn khám bệnh',
            'headers': ['Mã Lịch Hẹn', 'Số Điện Thoại Bệnh Nhân', 'Họ Tên Bệnh Nhân', 'Chuyên Khoa ID', 'Bác Sĩ ID', 'Ngày Hẹn (YYYY-MM-DD)', 'Giờ Hẹn (HH:MM)', 'Lý Do Khám', 'Trạng Thái'],
            'sample_rows': [
                ['LH2609901', '0901234567', 'Hoàng Bảo Nam', 1, 1, '2026-10-25', '09:00', 'Tái khám dạ dày định kỳ', 'Chờ xác nhận'],
                ['LH2609902', '0908111222', 'Nguyễn Thị Lan', 3, '', '2026-10-26', '14:30', 'Khám tổng quát sức khỏe', 'Chờ xác nhận']
            ]
        }
    }

    @staticmethod
    def get_sample_csv(module):
        """Tạo nội dung CSV mẫu với BOM tiếng Việt."""
        cfg = CSVService.MODULE_CONFIGS.get(module)
        if not cfg:
            return None, "Module không tồn tại"

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(cfg['headers'])
        for r in cfg['sample_rows']:
            writer.writerow(r)

        return '\ufeff' + output.getvalue(), f"mau_nhap_{module}.csv"

    @staticmethod
    def export_csv(module):
        """Xuất dữ liệu thực tế từ CSDL ra tệp CSV chuẩn UTF-8-SIG."""
        cfg = CSVService.MODULE_CONFIGS.get(module)
        if not cfg:
            return None, "Module không tồn tại"

        conn = get_db()
        cursor = conn.cursor()
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        filename = f"xuat_{module}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        if module == 'medicines':
            writer.writerow(cfg['headers'])
            cursor.execute('''
                SELECT ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung
                FROM thuoc
                ORDER BY id ASC
            ''')
            for r in cursor.fetchall():
                writer.writerow([
                    r.get('ma_thuoc') or '',
                    r.get('ten_thuoc') or '',
                    r.get('hoat_chat') or '',
                    r.get('ham_luong') or '',
                    r.get('don_vi_tinh') or '',
                    r.get('don_gia') or 0,
                    r.get('so_luong_ton') or 0,
                    r.get('hang_san_xuat') or '',
                    r.get('nuoc_san_xuat') or '',
                    r.get('huong_dan_su_dung') or ''
                ])

        elif module == 'services':
            writer.writerow(cfg['headers'])
            cursor.execute('''
                SELECT ma_dich_vu, ten_dich_vu, chuyen_khoa_id, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta
                FROM dich_vu
                ORDER BY id ASC
            ''')
            for r in cursor.fetchall():
                writer.writerow([
                    r.get('ma_dich_vu') or '',
                    r.get('ten_dich_vu') or '',
                    r.get('chuyen_khoa_id') or 1,
                    r.get('loai_dich_vu') or 'Khám bệnh',
                    r.get('don_gia') or 0,
                    r.get('bhyt_chi_tra_pt') or 0,
                    r.get('mo_ta') or ''
                ])

        elif module == 'articles':
            writer.writerow(cfg['headers'])
            cursor.execute('''
                SELECT tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, trang_thai
                FROM bai_viet
                ORDER BY id DESC
            ''')
            for r in cursor.fetchall():
                writer.writerow([
                    r.get('tieu_de') or '',
                    r.get('slug') or '',
                    r.get('danh_muc') or '',
                    r.get('tom_tat') or '',
                    r.get('noi_dung') or '',
                    r.get('hinh_anh') or '',
                    r.get('luot_xem') or 0,
                    r.get('trang_thai') or 1
                ])

        elif module == 'accounts':
            # Bảo mật: Không xuất mật khẩu hoặc hash ra file CSV
            headers = ['Tên Đăng Nhập', 'Họ Và Tên', 'Mã Vai Trò', 'Tên Vai Trò', 'Số Điện Thoại', 'Email', 'CCCD', 'Chức Vụ', 'Trạng Thái', 'Ngày Tạo']
            writer.writerow(headers)
            cursor.execute('''
                SELECT t.username, v.ma_vai_tro, v.ten_vai_tro, t.trang_thai, t.ngay_tao,
                       COALESCE(nv.ho_ten, bn.ho_ten, t.username) AS ho_ten,
                       COALESCE(nv.sdt, bn.sdt, t.sdt) AS sdt,
                       COALESCE(nv.email, bn.email, t.email) AS email,
                       COALESCE(nv.cccd, bn.cccd, '') AS cccd,
                       COALESCE(nv.chuc_vu, 'Bệnh nhân') AS chuc_vu
                FROM tai_khoan t
                JOIN vai_tro v ON t.vai_tro_id = v.id
                LEFT JOIN nhan_vien nv ON nv.tai_khoan_id = t.id
                LEFT JOIN benh_nhan bn ON bn.tai_khoan_id = t.id
                ORDER BY t.id ASC
            ''')
            for r in cursor.fetchall():
                writer.writerow([
                    r.get('username') or '',
                    r.get('ho_ten') or '',
                    r.get('ma_vai_tro') or '',
                    r.get('ten_vai_tro') or '',
                    r.get('sdt') or '',
                    r.get('email') or '',
                    r.get('cccd') or '',
                    r.get('chuc_vu') or '',
                    'Hoạt động' if r.get('trang_thai') else 'Vô hiệu hóa',
                    str(r.get('ngay_tao') or '')[:19]
                ])

        elif module == 'appointments':
            writer.writerow(cfg['headers'])
            cursor.execute('''
                SELECT lh.ma_lich_hen, bn.sdt, bn.ho_ten, lh.chuyen_khoa_id, lh.bac_si_id, lh.ngay_hen, lh.gio_hen, lh.ly_do_kham, lh.trang_thai
                FROM lich_hen lh
                JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
                ORDER BY lh.ngay_hen DESC, lh.gio_hen DESC
            ''')
            for r in cursor.fetchall():
                writer.writerow([
                    r.get('ma_lich_hen') or '',
                    r.get('sdt') or '',
                    r.get('ho_ten') or '',
                    r.get('chuyen_khoa_id') or 1,
                    r.get('bac_si_id') or '',
                    str(r.get('ngay_hen') or '')[:10],
                    str(r.get('gio_hen') or '')[:5],
                    r.get('ly_do_kham') or '',
                    r.get('trang_thai') or 'Chờ xác nhận'
                ])

        conn.close()
        return '\ufeff' + output.getvalue(), filename

    @staticmethod
    def import_csv(module, file_stream, current_user=None):
        """
        Nhập dữ liệu từ CSV. 
        Tự động nhận biết trùng lặp: Nếu trùng thuốc -> cộng dồn số lượng;
        Nếu trùng dịch vụ/bài viết/tài khoản/lịch hẹn -> cập nhật thay vì tạo trùng lặp.
        """
        if hasattr(file_stream, 'read'):
            content = file_stream.read()
        else:
            content = file_stream
        if isinstance(content, bytes):
            # Thử giải mã utf-8-sig rồi utf-8, latin-1
            try:
                decoded = content.decode('utf-8-sig')
            except Exception:
                try:
                    decoded = content.decode('utf-8')
                except Exception:
                    decoded = content.decode('latin-1')
        else:
            decoded = str(content)

        reader = csv.reader(io.StringIO(decoded))
        rows = list(reader)
        if not rows or len(rows) < 2:
            return False, "Tệp CSV không chứa dòng dữ liệu nào!", 0, 0

        # Bỏ qua dòng tiêu đề
        data_rows = rows[1:]

        conn = get_db()
        cursor = conn.cursor()
        inserted_count = 0
        updated_count = 0

        try:
            if module == 'medicines':
                for r in data_rows:
                    if not r or not any(field.strip() for field in r):
                        continue
                    ma = r[0].strip() if len(r) > 0 else ''
                    ten = r[1].strip() if len(r) > 1 else ''
                    hoat_chat = r[2].strip() if len(r) > 2 else ''
                    ham_luong = r[3].strip() if len(r) > 3 else ''
                    dvt = r[4].strip() if len(r) > 4 else 'Hộp'
                    try:
                        don_gia = float(r[5].strip()) if len(r) > 5 and r[5].strip() else 0.0
                    except Exception:
                        don_gia = 0.0
                    try:
                        qty = int(float(r[6].strip())) if len(r) > 6 and r[6].strip() else 0
                    except Exception:
                        qty = 0
                    hang = r[7].strip() if len(r) > 7 else ''
                    nuoc = r[8].strip() if len(r) > 8 else ''
                    hdsd = r[9].strip() if len(r) > 9 else ''

                    if not ten:
                        continue

                    # Kiểm tra trùng theo mã thuốc hoặc tên thuốc (case-insensitive)
                    cursor.execute("SELECT id, so_luong_ton, don_gia FROM thuoc WHERE (ma_thuoc = ? AND ma_thuoc != '') OR LOWER(ten_thuoc) = LOWER(?)", (ma, ten))
                    existing = cursor.fetchone()

                    if existing:
                        # Cộng dồn số lượng tồn thay vì thêm bản ghi mới
                        new_ton = int(existing['so_luong_ton'] or 0) + qty
                        final_price = don_gia if don_gia > 0 else float(existing['don_gia'] or 0.0)
                        cursor.execute('''
                            UPDATE thuoc
                            SET so_luong_ton = ?, don_gia = ?, hoat_chat = COALESCE(NULLIF(?, ''), hoat_chat),
                                ham_luong = COALESCE(NULLIF(?, ''), ham_luong), don_vi_tinh = COALESCE(NULLIF(?, ''), don_vi_tinh),
                                hang_san_xuat = COALESCE(NULLIF(?, ''), hang_san_xuat), nuoc_san_xuat = COALESCE(NULLIF(?, ''), nuoc_san_xuat),
                                huong_dan_su_dung = COALESCE(NULLIF(?, ''), huong_dan_su_dung)
                            WHERE id = ?
                        ''', (new_ton, final_price, hoat_chat, ham_luong, dvt, hang, nuoc, hdsd, existing['id']))
                        updated_count += 1
                    else:
                        # Tạo mã thuốc nếu chưa có
                        if not ma:
                            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM thuoc')
                            next_id = cursor.fetchone()['next_id']
                            ma = f"TH{str(next_id).zfill(3)}"

                        cursor.execute('''
                            INSERT INTO thuoc (ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        ''', (ma, ten, hoat_chat, ham_luong, dvt, don_gia, qty, hang, nuoc, hdsd))
                        inserted_count += 1

            elif module == 'services':
                for r in data_rows:
                    if not r or not any(field.strip() for field in r):
                        continue
                    ma = r[0].strip() if len(r) > 0 else ''
                    ten = r[1].strip() if len(r) > 1 else ''
                    try:
                        chuyen_khoa_id = int(r[2].strip()) if len(r) > 2 and r[2].strip() else 1
                    except Exception:
                        chuyen_khoa_id = 1
                    loai = r[3].strip() if len(r) > 3 and r[3].strip() else 'Khám bệnh'
                    try:
                        don_gia = float(r[4].strip()) if len(r) > 4 and r[4].strip() else 0.0
                    except Exception:
                        don_gia = 0.0
                    try:
                        bhyt = int(float(r[5].strip())) if len(r) > 5 and r[5].strip() else 0
                    except Exception:
                        bhyt = 0
                    mota = r[6].strip() if len(r) > 6 else ''

                    if not ten:
                        continue

                    cursor.execute("SELECT id FROM dich_vu WHERE (ma_dich_vu = ? AND ma_dich_vu != '') OR LOWER(ten_dich_vu) = LOWER(?)", (ma, ten))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute('''
                            UPDATE dich_vu
                            SET don_gia = ?, bhyt_chi_tra_pt = ?, mo_ta = COALESCE(NULLIF(?, ''), mo_ta),
                                loai_dich_vu = COALESCE(NULLIF(?, ''), loai_dich_vu), chuyen_khoa_id = ?
                            WHERE id = ?
                        ''', (don_gia, bhyt, mota, loai, chuyen_khoa_id, existing['id']))
                        updated_count += 1
                    else:
                        if not ma:
                            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM dich_vu')
                            next_id = cursor.fetchone()['next_id']
                            ma = f"DV{str(next_id).zfill(3)}"
                        cursor.execute('''
                            INSERT INTO dich_vu (ma_dich_vu, ten_dich_vu, chuyen_khoa_id, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                        ''', (ma, ten, chuyen_khoa_id, loai, don_gia, bhyt, mota))
                        inserted_count += 1

            elif module == 'articles':
                tac_gia_id = (current_user.get('staff_id') or current_user.get('id') if current_user else 1) or 1
                for r in data_rows:
                    if not r or not any(field.strip() for field in r):
                        continue
                    tieu_de = r[0].strip() if len(r) > 0 else ''
                    slug = r[1].strip() if len(r) > 1 else ''
                    danh_muc = r[2].strip() if len(r) > 2 and r[2].strip() else 'Cẩm Nang Y Tế'
                    tom_tat = r[3].strip() if len(r) > 3 else ''
                    noi_dung = r[4].strip() if len(r) > 4 else ''
                    hinh_anh = r[5].strip() if len(r) > 5 else ''
                    try:
                        luot_xem = int(r[6].strip()) if len(r) > 6 and r[6].strip() else 0
                    except Exception:
                        luot_xem = 0
                    try:
                        trang_thai = int(r[7].strip()) if len(r) > 7 and r[7].strip() else 1
                    except Exception:
                        trang_thai = 1

                    if not tieu_de:
                        continue
                    if not slug:
                        import re
                        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', tieu_de).strip().lower()
                        slug = re.sub(r'[\s-]+', '-', slug)

                    cursor.execute('SELECT id FROM bai_viet WHERE slug = ? OR LOWER(tieu_de) = LOWER(?)', (slug, tieu_de))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute('''
                            UPDATE bai_viet
                            SET tom_tat = COALESCE(NULLIF(?, ''), tom_tat), noi_dung = COALESCE(NULLIF(?, ''), noi_dung),
                                hinh_anh = COALESCE(NULLIF(?, ''), hinh_anh), danh_muc = ?, trang_thai = ?
                            WHERE id = ?
                        ''', (tom_tat, noi_dung, hinh_anh, danh_muc, trang_thai, existing['id']))
                        updated_count += 1
                    else:
                        cursor.execute('''
                            INSERT INTO bai_viet (tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, trang_thai)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, trang_thai))
                        inserted_count += 1

            elif module == 'accounts':
                from werkzeug.security import generate_password_hash
                role_mapping = {
                    'ADMIN': 1, 'LETAN': 2, 'BACSI': 3, 'DUOCSI': 4, 'KTV': 5, 'BENHNHAN': 6
                }
                for r in data_rows:
                    if not r or not any(field.strip() for field in r):
                        continue
                    username = r[0].strip() if len(r) > 0 else ''
                    raw_pwd = r[1].strip() if len(r) > 1 and r[1].strip() else 'Password@123'
                    ho_ten = r[2].strip() if len(r) > 2 else ''
                    role_code = r[3].strip().upper() if len(r) > 3 else 'LETAN'
                    sdt = r[4].strip() if len(r) > 4 else ''
                    email = r[5].strip() if len(r) > 5 else ''
                    cccd = r[6].strip() if len(r) > 6 else ''
                    chuc_vu = r[7].strip() if len(r) > 7 else ''
                    dia_chi = r[8].strip() if len(r) > 8 else ''

                    if not username or not ho_ten:
                        continue

                    vai_tro_id = role_mapping.get(role_code, 2)

                    cursor.execute("SELECT id, vai_tro_id FROM tai_khoan WHERE username = ? OR (sdt = ? AND sdt != '')", (username, sdt))
                    existing = cursor.fetchone()

                    if existing:
                        acc_id = existing['id']
                        # Cập nhật thông tin nhân viên hoặc bệnh nhân liên kết
                        cursor.execute('SELECT id FROM nhan_vien WHERE tai_khoan_id = ?', (acc_id,))
                        nv = cursor.fetchone()
                        if nv:
                            cursor.execute('''
                                UPDATE nhan_vien
                                SET ho_ten = ?, sdt = COALESCE(NULLIF(?, ''), sdt), email = COALESCE(NULLIF(?, ''), email),
                                    cccd = COALESCE(NULLIF(?, ''), cccd), chuc_vu = COALESCE(NULLIF(?, ''), chuc_vu), dia_chi = COALESCE(NULLIF(?, ''), dia_chi)
                                WHERE id = ?
                            ''', (ho_ten, sdt, email, cccd, chuc_vu, dia_chi, nv['id']))
                        else:
                            cursor.execute('SELECT id FROM benh_nhan WHERE tai_khoan_id = ?', (acc_id,))
                            bn = cursor.fetchone()
                            if bn:
                                cursor.execute('''
                                    UPDATE benh_nhan
                                    SET ho_ten = ?, sdt = COALESCE(NULLIF(?, ''), sdt), email = COALESCE(NULLIF(?, ''), email),
                                        cccd = COALESCE(NULLIF(?, ''), cccd), dia_chi = COALESCE(NULLIF(?, ''), dia_chi)
                                    WHERE id = ?
                                ''', (ho_ten, sdt, email, cccd, dia_chi, bn['id']))
                        updated_count += 1
                    else:
                        pwd_hash = generate_password_hash(raw_pwd)
                        cursor.execute('''
                            INSERT INTO tai_khoan (vai_tro_id, username, password, email, sdt, trang_thai)
                            VALUES (?, ?, ?, ?, ?, 1)
                        ''', (vai_tro_id, username, pwd_hash, email, sdt))
                        new_acc_id = cursor.lastrowid

                        if vai_tro_id == 6: # BENHNHAN
                            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM benh_nhan')
                            next_id = cursor.fetchone()['next_id']
                            ma_bn = f"BN2609{str(next_id).zfill(3)}"
                            cursor.execute('''
                                INSERT INTO benh_nhan (tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, dia_chi, co_tai_khoan)
                                VALUES (?, ?, ?, '1995-01-01', 'Nam', ?, ?, ?, ?, 1)
                            ''', (new_acc_id, ma_bn, ho_ten, sdt, email, cccd, dia_chi))
                        else:
                            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM nhan_vien')
                            next_id = cursor.fetchone()['next_id']
                            ma_nv = f"NV{str(next_id).zfill(4)}"
                            cursor.execute('''
                                INSERT INTO nhan_vien (tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu)
                                VALUES (?, ?, ?, 1, '1992-01-01', ?, ?, ?, ?, ?)
                            ''', (new_acc_id, ma_nv, ho_ten, sdt, email, cccd, dia_chi, chuc_vu or role_code))
                            if vai_tro_id == 3: # BACSI
                                nv_id = cursor.lastrowid
                                cursor.execute('''
                                    INSERT INTO bac_si (nhan_vien_id, chuyen_khoa_id, hoc_vi, trang_thai_lam_viec)
                                    VALUES (?, 1, 'Bác sĩ', 'Đang làm việc')
                                ''', (nv_id,))
                        inserted_count += 1

            elif module == 'appointments':
                for r in data_rows:
                    if not r or not any(field.strip() for field in r):
                        continue
                    ma = r[0].strip() if len(r) > 0 else ''
                    sdt = r[1].strip() if len(r) > 1 else ''
                    ho_ten = r[2].strip() if len(r) > 2 else ''
                    try:
                        chuyen_khoa_id = int(r[3].strip()) if len(r) > 3 and r[3].strip() else 1
                    except Exception:
                        chuyen_khoa_id = 1
                    try:
                        bac_si_id = int(r[4].strip()) if len(r) > 4 and r[4].strip() else None
                    except Exception:
                        bac_si_id = None
                    ngay_hen = r[5].strip() if len(r) > 5 else ''
                    gio_hen = r[6].strip() if len(r) > 6 else '08:30'
                    ly_do = r[7].strip() if len(r) > 7 else 'Khám theo yêu cầu'
                    trang_thai = r[8].strip() if len(r) > 8 and r[8].strip() else 'Chờ xác nhận'

                    if not ngay_hen:
                        continue

                    # Tìm hoặc tạo bệnh nhân theo sdt/tên
                    cursor.execute("SELECT id FROM benh_nhan WHERE sdt = ? AND sdt != ''", (sdt,))
                    bn = cursor.fetchone()
                    if bn:
                        bn_id = bn['id']
                    else:
                        cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM benh_nhan')
                        next_id = cursor.fetchone()['next_id']
                        ma_bn = f"BN2609{str(next_id).zfill(3)}"
                        cursor.execute('''
                            INSERT INTO benh_nhan (ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, dia_chi, co_tai_khoan)
                            VALUES (?, ?, '1995-01-01', 'Nam', ?, 'TP.HCM', 0)
                        ''', (ma_bn, ho_ten or 'Bệnh nhân', sdt or '0900000000'))
                        bn_id = cursor.lastrowid

                    # Kiểm tra trùng lịch hẹn theo mã hoặc theo bệnh nhân + ngày + giờ
                    cursor.execute('''
                        SELECT id FROM lich_hen
                        WHERE (ma_lich_hen = ? AND ma_lich_hen != '') OR (benh_nhan_id = ? AND ngay_hen = ? AND gio_hen LIKE ?)
                    ''', (ma, bn_id, ngay_hen, f"{gio_hen[:5]}%"))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute('''
                            UPDATE lich_hen
                            SET chuyen_khoa_id = ?, bac_si_id = ?, ly_do_kham = ?, trang_thai = ?
                            WHERE id = ?
                        ''', (chuyen_khoa_id, bac_si_id, ly_do, trang_thai, existing['id']))
                        updated_count += 1
                    else:
                        if not ma:
                            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM lich_hen')
                            next_id = cursor.fetchone()['next_id']
                            ma = f"LH2609{str(next_id).zfill(3)}"
                        cursor.execute('''
                            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (ma, bn_id, bac_si_id, chuyen_khoa_id, ngay_hen, gio_hen, ly_do, trang_thai))
                        inserted_count += 1

            conn.commit()
            conn.close()
            return True, f"Xử lý thành công: Thêm mới {inserted_count} bản ghi, cập nhật/cộng dồn {updated_count} bản ghi!", inserted_count, updated_count

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi khi xử lý CSV: {str(e)}", 0, 0
