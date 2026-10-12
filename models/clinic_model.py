from core.database import get_db

class ClinicModel:
    """Model quản lý danh mục chuyên khoa, phòng khám, dịch vụ và thống kê KPI."""

    @staticmethod
    def get_all_departments():
        """Lấy toàn bộ danh sách chuyên khoa y tế."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chuyen_khoa ORDER BY id ASC')
        departments = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return departments

    @staticmethod
    def get_all_rooms():
        """Lấy danh sách các phòng khám vật lý."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pk.*, ck.ten_khoa 
            FROM phong_kham pk
            JOIN chuyen_khoa ck ON pk.chuyen_khoa_id = ck.id
            ORDER BY pk.id ASC
        ''')
        rooms = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rooms

    @staticmethod
    def get_all_services():
        """Lấy danh mục các dịch vụ kỹ thuật y tế và cận lâm sàng."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dv.*, ck.ten_khoa 
            FROM dich_vu dv
            LEFT JOIN chuyen_khoa ck ON dv.chuyen_khoa_id = ck.id
            ORDER BY dv.id ASC
        ''')
        services = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return services

    @staticmethod
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
