"""MSSQL invoice validation; never silently reprice an issued invoice."""
from decimal import Decimal, InvalidOperation
from core.scheduling import CalendarError, integer

CASHIER_ROLES = frozenset({'ADMIN', 'LETAN'})
PAYMENT_METHODS = frozenset({'Tiền mặt', 'Chuyển khoản'})
UNPAID, PAID, CANCELED = 'Chưa thanh toán', 'Đã thanh toán', 'Đã hủy'


def money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise CalendarError('Số tiền bị thiếu hoặc không hợp lệ.')
    if not amount.is_finite() or amount < 0 or amount > Decimal('9999999999999999.99') or amount != amount.quantize(Decimal('0.01')):
        raise CalendarError('Số tiền phải không âm và có tối đa hai chữ số thập phân.')
    return amount


def fetch_invoice(cursor, identifier, lock=False):
    if isinstance(identifier, bool) or identifier is None or not str(identifier).strip():
        raise CalendarError('Mã hóa đơn không hợp lệ.')
    value = str(identifier).strip()
    hint = ' WITH (UPDLOCK, HOLDLOCK)' if lock else ''
    # Numeric references mean identity only; never UPDATE two rows via id OR code.
    if value.isascii() and value.isdigit():
        sql, param = 'id=?', integer(value)
    else:
        if len(value) > 100:
            raise CalendarError('Mã hóa đơn không hợp lệ.')
        sql, param = 'ma_hoa_don=?', value
    cursor.execute('SELECT * FROM hoa_don'+hint+' WHERE '+sql, (param,))
    rows = cursor.fetchall()
    if len(rows) > 1:
        raise CalendarError('Mã hóa đơn không duy nhất; cần đối soát.')
    return dict(rows[0]) if rows else None


def consultation_price(cursor, doctor_id):
    cursor.execute('''SELECT bs.gia_kham, ck.gia_kham_mac_dinh
        FROM bac_si bs JOIN chuyen_khoa ck ON ck.id=bs.chuyen_khoa_id WHERE bs.id=?''', (doctor_id,))
    row = cursor.fetchone()
    if not row:
        raise CalendarError('Không tìm thấy cấu hình giá khám.')
    return money(row['gia_kham'] if row['gia_kham'] is not None else row['gia_kham_mac_dinh'])


def exam_insurance_percent():
    import config
    percent = money(config.EXAM_INSURANCE_PERCENT)
    if percent > 100:
        raise CalendarError('Tỷ lệ BHYT khám phải từ 0 đến 100.')
    return percent / Decimal(100)


def validate_invoice(cursor, bill, check_sources=True):
    """Check all amounts before manual collection/request; preserve historical paid bills."""
    cursor.execute('SELECT benh_nhan_id, bac_si_id FROM phieu_kham WHERE id=?', (bill.get('phieu_kham_id'),))
    visit = cursor.fetchone()
    if not visit or visit['benh_nhan_id'] != bill.get('benh_nhan_id'):
        raise CalendarError('Hóa đơn không khớp bệnh nhân/phiếu khám.')
    cursor.execute('SELECT * FROM chi_tiet_hoa_don WHERE hoa_don_id=? ORDER BY id', (bill['id'],))
    items = [dict(row) for row in cursor.fetchall()]
    if not items:
        raise CalendarError('Hóa đơn chưa có chi tiết; không được thu tiền.')
    total = Decimal(0)
    drug_bill = str(bill.get('ma_hoa_don', '')).startswith('HDT')
    for item in items:
        qty = integer(item.get('so_luong'))
        if qty <= 0:
            raise CalendarError('Số lượng khoản thu phải là số nguyên dương.')
        price, amount = money(item.get('don_gia')), money(item.get('thanh_tien'))
        if price * qty != amount:
            raise CalendarError('Thành tiền chi tiết khác số lượng nhân đơn giá.')
        total += amount
        if not check_sources:
            continue
        kind, reference = item.get('loai_khoan_thu'), item.get('tham_chieu_id')
        if drug_bill:
            if kind != 'Thuốc':
                raise CalendarError('Hóa đơn thuốc có khoản thu không hợp lệ.')
            cursor.execute('SELECT don_gia FROM thuoc WHERE id=?', (reference,))
            source = cursor.fetchone()
            configured = money(source['don_gia']) if source else None
        elif kind == 'Khám bệnh':
            if reference != bill['phieu_kham_id'] or qty != 1:
                raise CalendarError('Khoản khám không thuộc phiếu khám hoặc bị nhân số lượng.')
            configured = consultation_price(cursor, visit['bac_si_id'])
        else:
            cursor.execute('SELECT don_gia FROM dich_vu WHERE id=?', (reference,))
            source = cursor.fetchone()
            configured = money(source['don_gia']) if source else None
            cursor.execute('''SELECT ct.id FROM chi_tiet_chi_dinh ct
                JOIN phieu_chi_dinh cd ON cd.id=ct.phieu_chi_dinh_id
                WHERE cd.phieu_kham_id=? AND ct.dich_vu_id=?''', (bill['phieu_kham_id'], reference))
            if not cursor.fetchone():
                raise CalendarError('Dịch vụ chưa được chỉ định cho phiếu khám.')
        if configured is None or price != configured:
            raise CalendarError('Đơn giá khác nguồn giá cấu hình hiện tại; cần đối soát, không tự sửa hóa đơn.')
    gross, insurance, discount, net = (money(bill.get(name)) for name in ('tong_tien', 'tien_bhyt', 'giam_gia', 'thanh_tien'))
    if total != gross or insurance + discount > gross or net != gross-insurance-discount:
        raise CalendarError('Tổng tiền, BHYT, giảm giá hoặc thực thu không khớp chi tiết.')
    return items
