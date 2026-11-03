"""Validated service selection, stored in the existing appointment reason field."""
import re
from core.scheduling import CalendarError, integer

SERVICE_MARKER = re.compile(r'\[Dịch vụ #(\d+):[^\]]*\]')
EXAM_TYPES = ('Khám bệnh', 'Khám chuyên khoa')


def selected_exam(cursor, service_id, department_id):
    service_id, department_id = integer(service_id), integer(department_id)
    cursor.execute('''SELECT dv.* FROM dich_vu dv JOIN chuyen_khoa ck ON ck.id=dv.chuyen_khoa_id
        WHERE dv.id=? AND dv.trang_thai=1 AND ck.trang_thai=1''', (service_id,))
    row = cursor.fetchone()
    if not row or row['chuyen_khoa_id'] != department_id or row['loai_dich_vu'] not in EXAM_TYPES:
        raise CalendarError('Dịch vụ khám không phù hợp với khoa hoặc đã ngừng hoạt động.')
    return dict(row)


def appointment_reason(service_id, department_id, reason):
    """Only server-resolved IDs/names may create the billing marker."""
    from core.database import get_db
    clean = SERVICE_MARKER.sub('', str(reason or '')).strip()
    if not service_id:
        return clean
    conn = get_db()
    try:
        service = selected_exam(conn.cursor(), service_id, department_id)
        name = service['ten_dich_vu'].replace(']', '')
        return f"[Dịch vụ #{service['id']}: {name}] {clean}"
    finally:
        conn.close()


def visit_exam(cursor, record_id, doctor_id):
    cursor.execute('''SELECT lh.ly_do_kham, bs.chuyen_khoa_id FROM phieu_kham pk
        JOIN bac_si bs ON bs.id=pk.bac_si_id
        LEFT JOIN lich_hen lh ON lh.id=pk.lich_hen_id WHERE pk.id=? AND pk.bac_si_id=?''', (record_id, doctor_id))
    row = cursor.fetchone()
    marker = SERVICE_MARKER.search(str(row.get('ly_do_kham') or '')) if row else None
    return selected_exam(cursor, marker.group(1), row['chuyen_khoa_id']) if marker else None
