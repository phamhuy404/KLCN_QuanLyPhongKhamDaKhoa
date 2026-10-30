"""Shared scheduling validation and a transaction-owned SQL Server mutex.

All cooperating calendar writers use the same lock, including across processes.
No schema changes or process-local locks are needed. Never bypass this in tests:
inject a connection implementing the SQL protocol instead.
"""
from contextvars import ContextVar
from datetime import date, datetime, time
from functools import wraps
import re

from core.database import get_db as open_db


_transaction = ContextVar('scheduling_transaction', default=None)
SHIFT_TIMES = {1: ('07:00', '11:30'), 2: ('13:30', '17:00'), 3: ('17:30', '20:30')}


class CalendarError(ValueError):
    pass


def integer(value):
    if isinstance(value, bool) or not re.fullmatch(r'[+-]?\d+', str(value).strip()):
        raise CalendarError('Giá trị phải là số nguyên.')
    return int(value)


class ConnectionLease:
    def __init__(self, connection):
        self.connection = connection
        self.failure = None

    def cursor(self):
        return TransactionCursor(self.connection.cursor(), self)

    def close(self):
        pass

    def commit(self):
        pass  # Only the outer operation may commit/release the mutex.

    def rollback(self):
        pass  # The outer operation rolls back every unsuccessful result.


class TransactionCursor:
    """A swallowed SQL error in a legacy helper must still abort this transaction."""
    def __init__(self, cursor, lease):
        self.cursor = cursor
        self.lease = lease

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def execute(self, sql, params=()):
        try:
            self.cursor.execute(sql, params)
            return self
        except Exception as exc:
            self.lease.failure = exc
            raise

    def executemany(self, sql, params):
        try:
            return self.cursor.executemany(sql, params)
        except Exception as exc:
            self.lease.failure = exc
            raise


def scheduling_db():
    return _transaction.get() or open_db()


def current_connection():
    return _transaction.get()


def serialized(function):
    @wraps(function)
    def run(*args, **kwargs):
        if _transaction.get() is not None:
            try:
                return function(*args, **kwargs)
            except CalendarError as exc:
                return False, str(exc)
        connection = None
        token = None
        try:
            connection = open_db()
            cursor = connection.cursor()
            cursor.execute("""
                SET NOCOUNT ON;
                SET XACT_ABORT ON;
                IF @@TRANCOUNT = 0 BEGIN TRANSACTION;
                DECLARE @result int;
                EXEC @result = sys.sp_getapplock
                    @Resource = 'clinic.calendar.v1', @LockMode = 'Exclusive',
                    @LockOwner = 'Transaction', @LockTimeout = 10000;
                SELECT @result AS calendar_lock_result;
            """)
            row = cursor.fetchone()
            if not row or row['calendar_lock_result'] < 0:
                raise CalendarError('Không lấy được khóa lịch. Vui lòng thử lại.')
            lease = ConnectionLease(connection)
            token = _transaction.set(lease)
            result = function(*args, **kwargs)
            if lease.failure is not None:
                raise CalendarError(f'Giao dịch gặp lỗi database: {lease.failure}')
            if result[0]:
                connection.commit()
            else:
                connection.rollback()
            return result
        except Exception as exc:
            if connection is not None:
                connection.rollback()
            failure = (False, f'Không thể cập nhật lịch: {exc}')
            if function.__name__ == 'bulk_approve_schedules':
                return (*failure, 0)
            if function.__name__ == 'import_appointments':
                return (*failure, 0, 0)
            if function.__name__ == 'register_multiple_schedules':
                return (*failure, 0, [])
            return failure
        finally:
            if token is not None:
                _transaction.reset(token)
            if connection is not None:
                connection.close()
    return run


def clock(value):
    if isinstance(value, time):
        return value
    for fmt in ('%H:%M', '%H:%M:%S', '%H:%M:%S.%f', '%I:%M %p', '%I:%M%p'):
        try:
            return datetime.strptime(str(value).strip(), fmt).time()
        except ValueError:
            pass
    raise CalendarError('Giờ không hợp lệ.')


def shift_at(value):
    try:
        value = clock(value)
    except CalendarError:
        return None
    for number, (start, end) in SHIFT_TIMES.items():
        if clock(start) <= value < clock(end):
            return number
    return None


def slot(day, value, future=True):
    try:
        day = date.fromisoformat(str(day))
        value = clock(value)
    except (ValueError, TypeError):
        raise CalendarError('Ngày hoặc giờ không hợp lệ.')
    if shift_at(value) is None:
        raise CalendarError('Giờ hẹn nằm ngoài giờ làm việc.')
    if future and datetime.combine(day, value) <= datetime.now():
        raise CalendarError('Thời gian hẹn phải ở tương lai.')
    return day.isoformat(), value.strftime('%H:%M:%S')


def appointments(cursor, day):
    cursor.execute("SELECT * FROM lich_hen WHERE ngay_hen = ? AND (trang_thai IS NULL OR trang_thai != ?)", (str(day), 'Đã hủy'))
    return [dict(row) for row in cursor.fetchall()]


def schedule_for(cursor, doctor, day, value, approved=True):
    cursor.execute('SELECT * FROM lich_lam_viec WHERE bac_si_id = ? AND ngay_lam = ? AND ca_lam = ?',
                   (doctor, str(day)[:10], shift_at(value)))
    rows = [dict(row) for row in cursor.fetchall()
            if clock(row['gio_bat_dau']) <= clock(value) < clock(row['gio_ket_thuc'])]
    if len(rows) != 1:
        raise CalendarError('Không xác định được duy nhất ca trực của lịch hẹn.')
    row = rows[0]
    if approved and (row.get('trang_thai') != 1 or row.get('trang_thai_duyet') != 'DA_DUYET'):
        raise CalendarError('Ca trực chưa được duyệt hoặc không hoạt động.')
    return row


def in_schedule(appointment, schedule):
    return (appointment.get('bac_si_id') == schedule.get('bac_si_id')
            and str(appointment['ngay_hen'])[:10] == str(schedule['ngay_lam'])[:10]
            and shift_at(appointment['gio_hen']) == schedule['ca_lam']
            and clock(schedule['gio_bat_dau']) <= clock(appointment['gio_hen']) < clock(schedule['gio_ket_thuc']))


def sync_count(cursor, schedule):
    count = sum(in_schedule(row, schedule) for row in appointments(cursor, str(schedule['ngay_lam'])[:10]))
    cursor.execute('UPDATE lich_lam_viec SET so_luong_da_dang_ky = ? WHERE id = ?', (count, schedule['id']))


def booking_target(cursor, patient, department, doctor, day, value, exclude=None, availability=False):
    day, value = slot(day, value)
    cursor.execute('SELECT id, trang_thai FROM chuyen_khoa WHERE id = ?', (department,))
    dept = cursor.fetchone()
    if not dept or dept['trang_thai'] != 1:
        raise CalendarError('Chuyên khoa không hoạt động.')
    if not availability:
        cursor.execute('SELECT id FROM benh_nhan WHERE id = ?', (patient,))
        patient_row = cursor.fetchone()
        if not patient_row:
            raise CalendarError('Không có hồ sơ bệnh nhân.')
        patient = patient_row['id']
    existing = [row for row in appointments(cursor, day) if row['id'] != exclude]
    minutes = lambda v: clock(v).hour * 60 + clock(v).minute
    if any(row['benh_nhan_id'] == patient and abs(minutes(row['gio_hen']) - minutes(value)) < 30 for row in existing):
        raise CalendarError('Bệnh nhân đã có lịch hẹn trong vòng 30 phút.')
    cursor.execute('''SELECT bs.*, nv.trang_thai AS staff_active, tk.trang_thai AS account_active
                      FROM bac_si bs JOIN nhan_vien nv ON nv.id = bs.nhan_vien_id
                      JOIN tai_khoan tk ON tk.id = nv.tai_khoan_id
                      WHERE bs.chuyen_khoa_id = ? ORDER BY bs.id''', (department,))
    candidates = cursor.fetchall()
    for candidate in candidates:
        if doctor and str(candidate['id']) != str(doctor):
            continue
        if candidate['staff_active'] != 1 or candidate['account_active'] != 1 or candidate['trang_thai_lam_viec'] != 'Đang làm việc':
            continue
        try:
            schedule = schedule_for(cursor, candidate['id'], day, value)
        except CalendarError:
            continue
        if minutes(value) + 30 > minutes(schedule['gio_ket_thuc']):
            continue
        cursor.execute('SELECT chuyen_khoa_id, trang_thai FROM phong_kham WHERE id = ?', (schedule['phong_kham_id'],))
        room = cursor.fetchone()
        if not room or room['trang_thai'] != 1 or room['chuyen_khoa_id'] != candidate['chuyen_khoa_id']:
            continue
        occupancy = sum(in_schedule(row, schedule) for row in existing)
        if occupancy >= int(schedule.get('so_luong_kham_toi_da') or 0):
            continue
        if any((row['bac_si_id'] == candidate['id'] or row.get('phong_kham_id') == schedule['phong_kham_id'])
               and abs(minutes(row['gio_hen']) - minutes(value)) < 30 for row in existing):
            continue
        return schedule
    raise CalendarError('Không có ca được duyệt phù hợp chuyên khoa, phòng và sức chứa tại giờ hẹn.')


def validate_schedule(cursor, staff, doctor, room, day, shift, start=None, end=None, capacity=20, exclude=None):
    try:
        shift = integer(shift)
        capacity = integer(capacity)
        day = date.fromisoformat(str(day)[:10])
        default_start, default_end = SHIFT_TIMES[shift]
        start, end = clock(start or default_start), clock(end or default_end)
    except (ValueError, TypeError, KeyError):
        raise CalendarError('Ngày, ca hoặc sức chứa không hợp lệ.')
    if day < date.today() or datetime.combine(day, start) <= datetime.now():
        raise CalendarError('Không được tạo hoặc sửa ca trong quá khứ.')
    duration = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
    if capacity <= 0 or duration < 30 or not (clock(default_start) <= start < end <= clock(default_end)):
        raise CalendarError('Giờ làm hoặc sức chứa không hợp lệ.')
    if doctor:
        cursor.execute('SELECT nhan_vien_id, chuyen_khoa_id FROM bac_si WHERE id = ?', (doctor,))
        row = cursor.fetchone()
        if not row or (staff and str(staff) != str(row['nhan_vien_id'])):
            raise CalendarError('Bác sĩ và nhân viên không khớp.')
        staff, department = row['nhan_vien_id'], row['chuyen_khoa_id']
        cursor.execute('SELECT trang_thai FROM chuyen_khoa WHERE id = ?', (department,))
        dept = cursor.fetchone()
        if not dept or dept['trang_thai'] != 1:
            raise CalendarError('Chuyên khoa không hoạt động.')
    else:
        department = None
    cursor.execute('''SELECT nv.id, tk.vai_tro_id, tk.trang_thai AS account_active, nv.trang_thai
                      FROM nhan_vien nv JOIN tai_khoan tk ON tk.id = nv.tai_khoan_id WHERE nv.id = ?''', (staff,))
    employee = cursor.fetchone()
    if not employee or employee['account_active'] != 1 or employee['trang_thai'] != 1:
        raise CalendarError('Nhân viên không tồn tại hoặc không hoạt động.')
    if doctor and not room:
        raise CalendarError('Ca bác sĩ phải có phòng khám.')
    if room:
        cursor.execute('SELECT chuyen_khoa_id, trang_thai FROM phong_kham WHERE id = ?', (room,))
        row = cursor.fetchone()
        if not row or row['trang_thai'] != 1 or (department and row['chuyen_khoa_id'] != department):
            raise CalendarError('Phòng không hoạt động hoặc không đúng chuyên khoa.')
    cursor.execute('''SELECT llv.*, tk.vai_tro_id, bs.chuyen_khoa_id
                      FROM lich_lam_viec llv
                      LEFT JOIN nhan_vien nv ON nv.id = llv.nhan_vien_id
                      LEFT JOIN tai_khoan tk ON tk.id = nv.tai_khoan_id
                      LEFT JOIN bac_si bs ON bs.id = llv.bac_si_id
                      WHERE llv.ngay_lam = ?''', (day.isoformat(),))
    rows = [row for row in cursor.fetchall() if row['id'] != exclude
            and row.get('trang_thai_duyet') not in ('DA_HUY', 'TU_CHOI')]
    for row in rows:
        overlaps = clock(row['gio_bat_dau']) < end and start < clock(row['gio_ket_thuc'])
        if overlaps and (row['nhan_vien_id'] == staff or (doctor and str(row.get('bac_si_id')) == str(doctor)) or (room and str(row.get('phong_kham_id')) == str(room))):
            raise CalendarError('Nhân viên hoặc phòng đã có ca trùng giờ.')
    same_shift = [row for row in rows if row['ca_lam'] == shift and row.get('trang_thai') == 1]
    if sum(row['vai_tro_id'] == employee['vai_tro_id'] for row in same_shift) >= 5:
        raise CalendarError('Ca đã đủ 5 nhân viên cùng vai trò.')
    if doctor and sum(row.get('chuyen_khoa_id') == department for row in same_shift) >= 3:
        raise CalendarError('Ca đã đủ 3 bác sĩ cùng chuyên khoa.')
    return staff, day.isoformat(), shift, start.strftime('%H:%M:%S'), end.strftime('%H:%M:%S'), capacity
