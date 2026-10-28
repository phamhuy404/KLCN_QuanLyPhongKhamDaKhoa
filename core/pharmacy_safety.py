"""Prescription policy. All writers share the existing MSSQL transaction mutex."""
from collections import Counter
from decimal import Decimal
from functools import wraps
from inspect import signature

from core.scheduling import CalendarError, integer, serialized, scheduling_db

HOSPITAL = 'Mua tại bệnh viện'
EXTERNAL = 'Tự mua ngoài'
PAID = 'Đã thanh toán'
CANCELED = 'Đã hủy'
DISPENSED = {'Đã nhận thuốc', 'Đã cấp thuốc', 'Đã cấp phát'}
APPROVED = {'Đã duyệt đơn thuốc, vui lòng thanh toán hóa đơn và nhận thuốc tại quầy',
            'Đã duyệt thành công, xuống chỗ bán thuốc để lấy', 'Chờ nhận thuốc', 'Chưa nhận thuốc'}
EDITABLE = {'Chờ bệnh nhân xác nhận mua', 'Chờ duyệt', 'Mua ngoài',
            'Bị từ chối duyệt (Hết thuốc viện, vui lòng mua ngoài)'}


def stock_import(function):
    locked = serialized(function)

    @wraps(function)
    def run(module, *args, **kwargs):
        if module != 'medicines':
            return function(module, *args, **kwargs)
        result = locked(module, *args, **kwargs)
        return result if len(result) == 4 else (*result, 0, 0)
    return run


def quantities(items):
    if not isinstance(items, list) or not items:
        raise CalendarError('Đơn thuốc phải có ít nhất một thuốc.')
    totals = Counter()
    for item in items:
        if not isinstance(item, dict):
            raise CalendarError('Dòng thuốc không hợp lệ.')
        drug, qty = integer(item.get('thuoc_id')), integer(item.get('so_luong'))
        if drug <= 0 or qty <= 0:
            raise CalendarError('ID thuốc và số lượng phải là số nguyên dương.')
        totals[drug] += qty
        if totals[drug] > 2147483647:
            raise CalendarError('Số lượng thuốc vượt giới hạn.')
    return totals


def validate_items(cursor, items, stock=False):
    totals = quantities(items)
    for drug, qty in totals.items():
        cursor.execute('SELECT id, trang_thai, so_luong_ton FROM thuoc WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (drug,))
        row = cursor.fetchone()
        if not row or row['trang_thai'] != 1:
            raise CalendarError('Thuốc không tồn tại hoặc đã ngừng hoạt động.')
        if stock and (row['so_luong_ton'] is None or row['so_luong_ton'] < qty):
            raise CalendarError('Không đủ tồn kho cho tổng số lượng thuốc trong đơn.')
    return totals


def invoices(cursor, prescription):
    visit = prescription.get('phieu_kham_id')
    if not visit:
        raise CalendarError('Đơn thiếu liên kết phiếu khám.')
    cursor.execute('SELECT id FROM don_thuoc WITH (UPDLOCK, HOLDLOCK) WHERE phieu_kham_id=?', (visit,))
    siblings = cursor.fetchall()
    if len(siblings) != 1 or siblings[0]['id'] != prescription['id']:
        raise CalendarError('Phiếu có nhiều đơn hoặc liên kết không rõ; cần đối soát hóa đơn thủ công.')
    cursor.execute("SELECT * FROM hoa_don WITH (UPDLOCK, HOLDLOCK) WHERE phieu_kham_id=? AND ma_hoa_don LIKE 'HDT%' AND (trang_thai IS NULL OR trang_thai != ?)", (visit, CANCELED))
    bills = [dict(row) for row in cursor.fetchall()]
    if len(bills) > 1:
        raise CalendarError('Nhiều hóa đơn thuốc còn hiệu lực; cần đối soát thủ công.')
    return bills


def check_bill(cursor, bill, prescription):
    if bill.get('benh_nhan_id') != prescription.get('benh_nhan_id'):
        raise CalendarError('Hóa đơn không thuộc bệnh nhân của đơn.')
    cursor.execute('SELECT tham_chieu_id, so_luong, don_gia, thanh_tien FROM chi_tiet_hoa_don WHERE hoa_don_id=?', (bill['id'],))
    rows = [dict(row) for row in cursor.fetchall()]
    actual = quantities([{'thuoc_id': r['tham_chieu_id'], 'so_luong': r['so_luong']} for r in rows])
    if actual != quantities(prescription['items']):
        raise CalendarError('Chi tiết hóa đơn khác đơn thuốc; cần đối soát.')
    total = Decimal(0)
    for row in rows:
        price = Decimal(str(row['don_gia']))
        amount = Decimal(str(row['thanh_tien']))
        if not price.is_finite() or not amount.is_finite() or price < 0 or amount != price * row['so_luong']:
            raise CalendarError('Đơn giá/thành tiền hóa đơn không nhất quán; cần đối soát.')
        total += amount
    if total != Decimal(str(bill['tong_tien'])):
        raise CalendarError('Tổng hóa đơn không khớp chi tiết.')


def guarded(function):
    """Validation runs inside the mutex, before any legacy mutation or notification."""
    sig = signature(function)

    @wraps(function)
    def run(*args, **kwargs):
        from models.pharmacy_model import PharmacyModel
        values = sig.bind(*args, **kwargs).arguments
        identifier = values.get('prescription_id', values.get('prescription_id_or_code'))
        dt = PharmacyModel.get_prescription_detail(identifier)
        if not dt:
            raise CalendarError('Không tìm thấy đơn thuốc.')
        actor = values.get('audit_user') or values.get('reviewer_user')
        if actor and actor.get('vai_tro') == 'BACSI' and actor.get('bac_si_id') != dt.get('bac_si_id'):
            raise CalendarError('Chỉ bác sĩ kê đơn được sửa hoặc hủy đơn.')
        cursor = scheduling_db().cursor()
        bills = invoices(cursor, dt)
        if any(b.get('trang_thai') not in {PAID, 'Chưa thanh toán'} for b in bills):
            raise CalendarError('Trạng thái hóa đơn không xác định; cần đối soát trước khi xử lý đơn.')
        state = dt.get('trang_thai')
        name = function.__name__
        if state in DISPENSED or state == CANCELED:
            raise CalendarError('Đơn đã hủy/cấp phát bị khóa; không tự hoàn kho hoặc điều chỉnh tiền đã thu.')
        if any(b.get('trang_thai') == PAID for b in bills) and name != 'dispense_prescription':
            raise CalendarError('Đơn đã thanh toán bị khóa; cần quy trình điều chỉnh riêng.')
        if name == 'update_prescription':
            if state not in EDITABLE or bills:
                raise CalendarError('Chỉ sửa đơn chưa có hóa đơn còn hiệu lực và chưa duyệt.')
            validate_items(cursor, values['medicines'])
        elif name == 'cancel_or_adjust_prescription':
            if state not in EDITABLE | APPROVED:
                raise CalendarError('Trạng thái đơn không cho phép hủy.')
            if not isinstance(values.get('restore_stock', True), bool):
                raise CalendarError('restore_stock phải là boolean.')
            for bill in bills:
                if bill['trang_thai'] != 'Chưa thanh toán':
                    raise CalendarError('Không được hủy hóa đơn ở trạng thái này.')
                cursor.execute('UPDATE hoa_don SET trang_thai=? WHERE id=?', (CANCELED, bill['id']))
        elif name == 'choose_medicine_purchase_option':
            if state not in EDITABLE or values.get('option', HOSPITAL) not in {HOSPITAL, EXTERNAL}:
                raise CalendarError('Không được thay nơi mua ở trạng thái này.')
            validate_items(cursor, dt['items'])
            for item in dt['items']:
                price = Decimal(str(item.get('don_gia')))
                if not price.is_finite() or price < 0:
                    raise CalendarError('Đơn giá thuốc không hợp lệ.')
            if bills:
                check_bill(cursor, bills[0], dt)
        elif name == 'approve_prescription':
            if state != 'Chờ duyệt' or dt.get('hinh_thuc_mua') != HOSPITAL or len(bills) != 1:
                raise CalendarError('Chỉ duyệt đơn mua tại viện đang chờ duyệt, có hóa đơn duy nhất.')
            validate_items(cursor, dt['items'], stock=True)
            check_bill(cursor, bills[0], dt)
        elif name == 'reject_prescription':
            if state != 'Chờ duyệt' or dt.get('hinh_thuc_mua') != HOSPITAL:
                raise CalendarError('Chỉ từ chối đơn mua tại viện đang chờ duyệt.')
        elif name == 'dispense_prescription':
            if state not in APPROVED or dt.get('hinh_thuc_mua') != HOSPITAL or len(bills) != 1 or bills[0]['trang_thai'] != PAID:
                raise CalendarError('Chỉ cấp đơn đã duyệt, mua tại viện và đã thanh toán.')
            validate_items(cursor, dt['items'], stock=True)
            check_bill(cursor, bills[0], dt)
        return function(*args, **kwargs)
    return serialized(run)


def journal(cursor, drug, delta, before, after, actor=None, reason=None, receipt=None):
    import json
    cursor.execute('''INSERT INTO audit_log
        (table_name,row_id,action,performed_by,performed_by_name,performed_at,reason,before_json,after_json)
        VALUES (?,?,?,?,?,GETDATE(),?,?,?)''',
        ('thuoc', drug, 'STOCK_IN' if delta > 0 else 'STOCK_OUT',
         (actor or {}).get('id'), (actor or {}).get('ho_ten'), reason,
         json.dumps({'stock': before}), json.dumps({'stock': after, 'delta': delta, 'receipt': receipt})))
