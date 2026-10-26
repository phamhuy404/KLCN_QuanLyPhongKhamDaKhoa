from core.database import get_db

class ClinicModel:
    """Model quản lý danh mục chuyên khoa, phòng khám, dịch vụ và thống kê KPI."""

    # 1. QUẢN LÝ CHUYÊN KHOA
    @staticmethod
    def get_all_departments(active_only=False):
        """Lấy toàn bộ danh sách chuyên khoa y tế (hỗ trợ lọc chỉ lấy khoa đang hoạt động)."""
        conn = get_db()
        cursor = conn.cursor()
        if active_only:
            cursor.execute('SELECT * FROM chuyen_khoa WHERE trang_thai = 1 ORDER BY id ASC')
        else:
            cursor.execute('SELECT * FROM chuyen_khoa ORDER BY id ASC')
        departments = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return departments

    @staticmethod
    def get_department_by_id(dep_id):
        """Lấy thông tin một chuyên khoa theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chuyen_khoa WHERE id = ?', (dep_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create_department(ma_khoa, ten_khoa, mo_ta='', icon='fa-stethoscope', gia_kham=150000.0):
        """Thêm chuyên khoa mới vào hệ thống."""
        ma_khoa = (ma_khoa or '').strip().upper()
        ten_khoa = (ten_khoa or '').strip()
        if not ma_khoa or not ten_khoa:
            return False, "Mã khoa và tên chuyên khoa là bắt buộc!"

        try:
            gia_kham = float(gia_kham)
            if gia_kham < 0:
                gia_kham = 0.0
        except (ValueError, TypeError):
            gia_kham = 150000.0

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM chuyen_khoa WHERE ma_khoa = ?', (ma_khoa,))
            if cursor.fetchone():
                conn.close()
                return False, f"Mã chuyên khoa '{ma_khoa}' đã tồn tại!"

            cursor.execute('''
                INSERT INTO chuyen_khoa (ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (ma_khoa, ten_khoa, mo_ta.strip(), icon or 'fa-stethoscope', gia_kham))
            conn.commit()
            dep_id = cursor.lastrowid
            conn.close()
            return True, dep_id
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi tạo chuyên khoa: {str(e)}"

    @staticmethod
    def update_department(dep_id, ma_khoa, ten_khoa, mo_ta='', icon='fa-stethoscope', gia_kham=150000.0, trang_thai=1):
        """Cập nhật thông tin chuyên khoa."""
        ma_khoa = (ma_khoa or '').strip().upper()
        ten_khoa = (ten_khoa or '').strip()
        if not ma_khoa or not ten_khoa:
            return False, "Mã khoa và tên chuyên khoa là bắt buộc!"

        try:
            gia_kham = float(gia_kham)
            trang_thai = int(trang_thai)
        except (ValueError, TypeError):
            pass

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM chuyen_khoa WHERE ma_khoa = ? AND id != ?', (ma_khoa, dep_id))
            if cursor.fetchone():
                conn.close()
                return False, f"Mã chuyên khoa '{ma_khoa}' đã thuộc về chuyên khoa khác!"

            cursor.execute('''
                UPDATE chuyen_khoa
                SET ma_khoa = ?, ten_khoa = ?, mo_ta = ?, icon = ?, gia_kham_mac_dinh = ?, trang_thai = ?
                WHERE id = ?
            ''', (ma_khoa, ten_khoa, mo_ta.strip(), icon, gia_kham, trang_thai, dep_id))
            conn.commit()
            conn.close()
            return True, "Cập nhật chuyên khoa thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cập nhật: {str(e)}"

    @staticmethod
    def toggle_department_status(dep_id):
        """Bật/tắt trạng thái hoạt động của chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT trang_thai FROM chuyen_khoa WHERE id = ?', (dep_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Không tìm thấy chuyên khoa!"
            new_status = 0 if row['trang_thai'] else 1
            cursor.execute('UPDATE chuyen_khoa SET trang_thai = ? WHERE id = ?', (new_status, dep_id))
            conn.commit()
            conn.close()
            return True, new_status
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def delete_department(dep_id):
        """Xóa chuyên khoa (chỉ cho phép khi chưa có dữ liệu tham chiếu lịch sử)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            # Kiểm tra ràng buộc
            cursor.execute('SELECT COUNT(*) as cnt FROM phong_kham WHERE chuyen_khoa_id = ?', (dep_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Không thể xóa cứng vì chuyên khoa đang liên kết với các phòng khám vật lý! Hãy chuyển sang Vô hiệu hóa."

            cursor.execute('SELECT COUNT(*) as cnt FROM bac_si WHERE chuyen_khoa_id = ?', (dep_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Không thể xóa cứng vì đang có bác sĩ thuộc chuyên khoa này! Hãy chuyển sang Vô hiệu hóa."

            cursor.execute('SELECT COUNT(*) as cnt FROM lich_hen WHERE chuyen_khoa_id = ?', (dep_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Không thể xóa cứng vì đã có lịch hẹn khám đăng ký chuyên khoa này! Hãy chuyển sang Vô hiệu hóa."

            cursor.execute('DELETE FROM chuyen_khoa WHERE id = ?', (dep_id,))
            conn.commit()
            conn.close()
            return True, "Đã xóa chuyên khoa thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi xóa chuyên khoa: {str(e)}"

    # 2. QUẢN LÝ PHÒNG KHÁM
    @staticmethod
    def get_all_rooms(active_only=False):
        """Lấy danh sách các phòng khám vật lý."""
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT pk.*, ck.ten_khoa 
            FROM phong_kham pk
            JOIN chuyen_khoa ck ON pk.chuyen_khoa_id = ck.id
        '''
        if active_only:
            sql += ' WHERE pk.trang_thai = 1'
        sql += ' ORDER BY pk.id ASC'
        cursor.execute(sql)
        rooms = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rooms

    @staticmethod
    def get_room_by_id(room_id):
        """Lấy thông tin phòng khám theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pk.*, ck.ten_khoa 
            FROM phong_kham pk
            JOIN chuyen_khoa ck ON pk.chuyen_khoa_id = ck.id
            WHERE pk.id = ?
        ''', (room_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create_room(chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang='Tầng 1'):
        """Tạo phòng khám mới."""
        ma_phong = (ma_phong or '').strip().upper()
        ten_phong = (ten_phong or '').strip()
        if not chuyen_khoa_id or not ma_phong or not ten_phong:
            return False, "Vui lòng nhập đầy đủ chuyên khoa, mã phòng và tên phòng!"

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM chuyen_khoa WHERE id = ?', (chuyen_khoa_id,))
            if not cursor.fetchone():
                conn.close()
                return False, "Chuyên khoa được chọn không tồn tại!"

            cursor.execute('SELECT id FROM phong_kham WHERE ma_phong = ?', (ma_phong,))
            if cursor.fetchone():
                conn.close()
                return False, f"Mã phòng '{ma_phong}' đã tồn tại!"

            cursor.execute('''
                INSERT INTO phong_kham (chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai)
                VALUES (?, ?, ?, ?, 1)
            ''', (chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang or 'Tầng 1'))
            conn.commit()
            r_id = cursor.lastrowid
            conn.close()
            return True, r_id
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi tạo phòng khám: {str(e)}"

    @staticmethod
    def update_room(room_id, chuyen_khoa_id=None, ma_phong=None, ten_phong=None, vi_tri_tang=None, trang_thai=None):
        """Cập nhật thông tin phòng khám."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai FROM phong_kham WHERE id = ?', (room_id,))
            cur_room = cursor.fetchone()
            if not cur_room:
                conn.close()
                return False, "Không tìm thấy phòng khám!"

            chuyen_khoa_id = chuyen_khoa_id or cur_room['chuyen_khoa_id']
            ma_phong = (ma_phong or cur_room['ma_phong'] or '').strip().upper()
            ten_phong = (ten_phong or cur_room['ten_phong'] or '').strip()
            vi_tri_tang = vi_tri_tang or cur_room.get('vi_tri_tang') or 'Tầng 1'
            trang_thai = int(trang_thai) if trang_thai is not None else cur_room.get('trang_thai', 1)

            if not chuyen_khoa_id or not ma_phong or not ten_phong:
                conn.close()
                return False, "Thông tin phòng khám không được để trống!"

            cursor.execute('SELECT id FROM phong_kham WHERE ma_phong = ? AND id != ?', (ma_phong, room_id))
            if cursor.fetchone():
                conn.close()
                return False, f"Mã phòng '{ma_phong}' đã được sử dụng bởi phòng khác!"

            cursor.execute('''
                UPDATE phong_kham
                SET chuyen_khoa_id = ?, ma_phong = ?, ten_phong = ?, vi_tri_tang = ?, trang_thai = ?
                WHERE id = ?
            ''', (chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, int(trang_thai), room_id))
            conn.commit()
            conn.close()
            return True, "Cập nhật phòng khám thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cập nhật: {str(e)}"

    @staticmethod
    def toggle_room_status(room_id):
        """Bật/tắt trạng thái hoạt động của phòng khám."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT trang_thai FROM phong_kham WHERE id = ?', (room_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Không tìm thấy phòng khám!"
            new_status = 0 if row['trang_thai'] else 1
            cursor.execute('UPDATE phong_kham SET trang_thai = ? WHERE id = ?', (new_status, room_id))
            conn.commit()
            conn.close()
            return True, new_status
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def delete_room(room_id):
        """Xóa phòng khám (chỉ cho phép khi chưa có dữ liệu tham chiếu)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) as cnt FROM bac_si WHERE phong_kham_chinh_id = ?', (room_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Phòng khám đang được bác sĩ chọn làm phòng khám chính! Hãy chuyển sang Vô hiệu hóa."

            cursor.execute('SELECT COUNT(*) as cnt FROM lich_lam_viec WHERE phong_kham_id = ?', (room_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Phòng khám đã có lịch trực được phân bổ! Hãy chuyển sang Vô hiệu hóa."

            cursor.execute('SELECT COUNT(*) as cnt FROM phieu_kham WHERE phong_kham_id = ?', (room_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Phòng khám đã có bệnh nhân khám và phát sinh phiếu khám! Hãy chuyển sang Vô hiệu hóa."

            cursor.execute('DELETE FROM phong_kham WHERE id = ?', (room_id,))
            conn.commit()
            conn.close()
            return True, "Đã xóa phòng khám thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi xóa phòng khám: {str(e)}"

    # 3. QUẢN LÝ DỊCH VỤ Y TẾ
    @staticmethod
    def get_all_services(active_only=False, category=None):
        """Lấy danh mục các dịch vụ kỹ thuật y tế và cận lâm sàng."""
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
            SELECT dv.*, ck.ten_khoa 
            FROM dich_vu dv
            LEFT JOIN chuyen_khoa ck ON dv.chuyen_khoa_id = ck.id
            WHERE 1=1
        '''
        params = []
        if active_only:
            sql += ' AND dv.trang_thai = 1'
        if category and category != 'ALL':
            sql += ' AND dv.loai_dich_vu = ?'
            params.append(category)

        sql += ' ORDER BY dv.id ASC'
        cursor.execute(sql, tuple(params))
        services = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return services

    @staticmethod
    def get_service_by_id(service_id):
        """Lấy thông tin dịch vụ theo ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dv.*, ck.ten_khoa 
            FROM dich_vu dv
            LEFT JOIN chuyen_khoa ck ON dv.chuyen_khoa_id = ck.id
            WHERE dv.id = ?
        ''', (service_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create_service(chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu='Khám bệnh', don_gia=0.0, bhyt_chi_tra_pt=0, mo_ta=''):
        """Thêm dịch vụ kỹ thuật y tế mới với kiểm tra ràng buộc chặt chẽ."""
        ma_dich_vu = (ma_dich_vu or '').strip().upper()
        ten_dich_vu = (ten_dich_vu or '').strip()
        if not ma_dich_vu or not ten_dich_vu:
            return False, "Mã dịch vụ và tên dịch vụ là bắt buộc!"

        from core.validators import validate_service_data
        ok_srv, err_srv = validate_service_data({
            'ten_dich_vu': ten_dich_vu,
            'don_gia': don_gia,
            'bhyt_chi_tra_pt': bhyt_chi_tra_pt
        })
        if not ok_srv:
            return False, list(err_srv.values())[0]

        try:
            don_gia = float(don_gia)
            bhyt_chi_tra_pt = int(bhyt_chi_tra_pt)
        except (ValueError, TypeError):
            don_gia = 0.0
            bhyt_chi_tra_pt = 0

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM dich_vu WHERE ma_dich_vu = ?', (ma_dich_vu,))
            if cursor.fetchone():
                conn.close()
                return False, f"Mã dịch vụ '{ma_dich_vu}' đã tồn tại!"

            cursor.execute('''
                INSERT INTO dich_vu (chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (chuyen_khoa_id if chuyen_khoa_id else None, ma_dich_vu, ten_dich_vu, loai_dich_vu or 'Khám bệnh', don_gia, bhyt_chi_tra_pt, mo_ta.strip()))
            conn.commit()
            srv_id = cursor.lastrowid
            conn.close()
            return True, srv_id
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi tạo dịch vụ: {str(e)}"

    @staticmethod
    def update_service(service_id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu='Khám bệnh', don_gia=0.0, bhyt_chi_tra_pt=0, mo_ta='', trang_thai=1):
        """Cập nhật thông tin dịch vụ kỹ thuật."""
        ma_dich_vu = (ma_dich_vu or '').strip().upper()
        ten_dich_vu = (ten_dich_vu or '').strip()
        if not ma_dich_vu or not ten_dich_vu:
            return False, "Mã dịch vụ và tên dịch vụ là bắt buộc!"

        try:
            don_gia = float(don_gia)
            bhyt_chi_tra_pt = int(bhyt_chi_tra_pt)
            trang_thai = int(trang_thai)
        except (ValueError, TypeError):
            pass

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM dich_vu WHERE ma_dich_vu = ? AND id != ?', (ma_dich_vu, service_id))
            if cursor.fetchone():
                conn.close()
                return False, f"Mã dịch vụ '{ma_dich_vu}' đã được sử dụng cho dịch vụ khác!"

            cursor.execute('''
                UPDATE dich_vu
                SET chuyen_khoa_id = ?, ma_dich_vu = ?, ten_dich_vu = ?, loai_dich_vu = ?, don_gia = ?, bhyt_chi_tra_pt = ?, mo_ta = ?, trang_thai = ?
                WHERE id = ?
            ''', (chuyen_khoa_id if chuyen_khoa_id else None, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta.strip(), trang_thai, service_id))
            conn.commit()
            conn.close()
            return True, "Cập nhật dịch vụ thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cập nhật dịch vụ: {str(e)}"

    @staticmethod
    def toggle_service_status(service_id):
        """Bật/tắt trạng thái hoạt động của dịch vụ kỹ thuật."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT trang_thai FROM dich_vu WHERE id = ?', (service_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Không tìm thấy dịch vụ!"
            new_status = 0 if row['trang_thai'] else 1
            cursor.execute('UPDATE dich_vu SET trang_thai = ? WHERE id = ?', (new_status, service_id))
            conn.commit()
            conn.close()
            return True, new_status
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def delete_service(service_id):
        """Xóa dịch vụ (chỉ cho phép khi chưa từng được chỉ định trong hồ sơ y tế)."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) as cnt FROM chi_tiet_chi_dinh WHERE dich_vu_id = ?', (service_id,))
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return False, "Dịch vụ đã từng được bác sĩ chỉ định trong phiếu khám! Hãy chuyển sang Vô hiệu hóa để bảo toàn lịch sử y bạ."

            cursor.execute('DELETE FROM dich_vu WHERE id = ?', (service_id,))
            conn.commit()
            conn.close()
            return True, "Đã xóa dịch vụ thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi xóa dịch vụ: {str(e)}"

    # 4. THỐNG KÊ DASHBOARD
    @staticmethod
    def get_dashboard_stats():
        """Lấy số liệu thống kê thời gian thực cho trang Dashboard."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total_patients FROM benh_nhan')
        total_patients = cursor.fetchone()['total_patients']

        cursor.execute("SELECT COUNT(*) as waiting_appointments FROM lich_hen WHERE trang_thai IN ('Chờ tiếp nhận', 'Chờ xác nhận')")
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

    @staticmethod
    def get_report_stats():
        """Lấy số liệu thống kê chi tiết cho trang báo cáo."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total_visits FROM phieu_kham')
        total_visits = cursor.fetchone()['total_visits']

        cursor.execute("SELECT COALESCE(SUM(thanh_tien), 0) as total_revenue FROM hoa_don WHERE trang_thai = 'Đã thanh toán'")
        total_revenue = cursor.fetchone()['total_revenue']

        cursor.execute('SELECT COUNT(*) as total_patients FROM benh_nhan')
        total_patients = cursor.fetchone()['total_patients']

        cursor.execute("SELECT COUNT(*) as bhyt_patients FROM benh_nhan WHERE bhyt IS NOT NULL AND bhyt != ''")
        bhyt_patients = cursor.fetchone()['bhyt_patients']
        bhyt_ratio = round((bhyt_patients / total_patients * 100), 1) if total_patients > 0 else 0

        cursor.execute('''
            SELECT hinh_thuc_thanh_toan, COUNT(*) as so_luong, COALESCE(SUM(thanh_tien), 0) as doanh_thu
            FROM hoa_don
            WHERE trang_thai = 'Đã thanh toán'
            GROUP BY hinh_thuc_thanh_toan
        ''')
        payment_stats = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT ck.ten_khoa, COUNT(pk.id) as so_luot_kham
            FROM chuyen_khoa ck
            LEFT JOIN bac_si bs ON bs.chuyen_khoa_id = ck.id
            LEFT JOIN phieu_kham pk ON pk.bac_si_id = bs.id
            GROUP BY ck.id, ck.ten_khoa
            ORDER BY so_luot_kham DESC
        ''')
        department_visits = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return {
            'total_visits': total_visits,
            'total_revenue': total_revenue,
            'total_patients': total_patients,
            'bhyt_patients': bhyt_patients,
            'bhyt_ratio': bhyt_ratio,
            'payment_stats': payment_stats,
            'department_visits': department_visits
        }
