from datetime import datetime
from core.database import get_db

class AppointmentModel:
    """Model quản lý lịch hẹn khám và tiếp nhận bệnh nhân."""

    @staticmethod
    def get_all():
        """Lấy toàn bộ danh sách lịch hẹn khám kèm thông tin bệnh nhân, bác sĩ và chuyên khoa."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                lh.id, lh.ma_lich_hen, lh.ngay_hen, lh.gio_hen, lh.ly_do_kham, lh.trang_thai, lh.ngay_dat,
                lh.benh_nhan_id,
                bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                ck.id AS chuyen_khoa_id, ck.ten_khoa,
                pk.id AS phong_kham_id, pk.ten_phong,
                bs.id AS bac_si_id,
                nv.ho_ten AS ten_bac_si
            FROM lich_hen lh
            JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
            JOIN chuyen_khoa ck ON lh.chuyen_khoa_id = ck.id
            LEFT JOIN phong_kham pk ON lh.phong_kham_id = pk.id
            LEFT JOIN bac_si bs ON lh.bac_si_id = bs.id
            LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
            ORDER BY lh.ngay_hen DESC, lh.gio_hen DESC
        ''')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_patient(patient_id):
        """Lấy danh sách lịch hẹn của một bệnh nhân cụ thể."""
        all_appts = AppointmentModel.get_all()
        return [a for a in all_appts if a['benh_nhan_id'] == patient_id]

    @staticmethod
    def create(benh_nhan_id, chuyen_khoa_id, bac_si_id, ngay_hen, gio_hen, ly_do_kham):
        """Tạo lịch hẹn khám mới."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM lich_hen')
            next_id = cursor.fetchone()['next_id']
            ma_lich_hen = f"LH2609{str(next_id).zfill(3)}"

            cursor.execute('''
                INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, ngay_hen, gio_hen, ly_do_kham, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Chờ xác nhận')
            ''', (ma_lich_hen, benh_nhan_id, bac_si_id if bac_si_id else None, chuyen_khoa_id, ngay_hen, gio_hen, ly_do_kham))

            conn.commit()
            conn.close()
            return True, ma_lich_hen
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)

    @staticmethod
    def update_status(appointment_id, new_status):
        """Cập nhật trạng thái lịch hẹn khám."""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE lich_hen SET trang_thai = ? WHERE id = ?', (new_status, appointment_id))
            conn.commit()
            conn.close()
            return True, 'Cập nhật trạng thái thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
