from datetime import datetime
from core.database import get_db

class FeedbackModel:
    """Model quản lý ý kiến đóng góp và phản hồi chất lượng dịch vụ của bệnh nhân."""

    @staticmethod
    def create(benh_nhan_id, phieu_kham_id=None, chu_de='Dịch vụ khám bệnh', diem_danh_gia=5, noi_dung=''):
        """Bệnh nhân gửi ý kiến phản hồi mới."""
        if not benh_nhan_id:
            return False, "Yêu cầu thông tin bệnh nhân!"

        if not noi_dung or len(noi_dung.strip()) < 5:
            return False, "Nội dung phản hồi phải có ít nhất 5 ký tự!"

        try:
            diem_danh_gia = int(diem_danh_gia)
            if diem_danh_gia < 1 or diem_danh_gia > 5:
                diem_danh_gia = 5
        except (ValueError, TypeError):
            diem_danh_gia = 5

        chu_de = (chu_de or 'Dịch vụ khám bệnh').strip()

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO phan_hoi (benh_nhan_id, phieu_kham_id, chu_de, diem_danh_gia, noi_dung, trang_thai, thoi_gian)
                VALUES (?, ?, ?, ?, ?, 'Chờ tiếp nhận', ?)
            ''', (benh_nhan_id, phieu_kham_id if phieu_kham_id else None, chu_de, diem_danh_gia, noi_dung.strip(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return True, "Gửi phản hồi thành công! Cảm ơn ý kiến quý báu của bạn."
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi khi gửi phản hồi: {str(e)}"

    @staticmethod
    def get_by_patient(benh_nhan_id):
        """Lấy danh sách các phản hồi của duy nhất bệnh nhân đang đăng nhập."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ph.*, pk.ma_phieu
            FROM phan_hoi ph
            LEFT JOIN phieu_kham pk ON ph.phieu_kham_id = pk.id
            WHERE ph.benh_nhan_id = ?
            ORDER BY ph.id DESC
        ''', (benh_nhan_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_all(filter_status=None, filter_topic=None):
        """Lấy toàn bộ phản hồi phục vụ quản trị và tiếp nhận chăm sóc khách hàng."""
        conn = get_db()
        cursor = conn.cursor()

        sql = '''
            SELECT ph.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan, pk.ma_phieu
            FROM phan_hoi ph
            JOIN benh_nhan bn ON ph.benh_nhan_id = bn.id
            LEFT JOIN phieu_kham pk ON ph.phieu_kham_id = pk.id
            WHERE 1=1
        '''
        params = []
        if filter_status and filter_status != 'ALL':
            sql += ' AND ph.trang_thai = ?'
            params.append(filter_status)
        if filter_topic and filter_topic != 'ALL':
            sql += ' AND ph.chu_de = ?'
            params.append(filter_topic)

        sql += ' ORDER BY ph.id DESC'

        cursor.execute(sql, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(feedback_id):
        """Lấy thông tin chi tiết một bản ghi phản hồi."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ph.*, bn.ma_benh_nhan, bn.ho_ten AS ten_benh_nhan, bn.sdt AS sdt_benh_nhan, bn.email AS email_benh_nhan, bn.tai_khoan_id, pk.ma_phieu
            FROM phan_hoi ph
            JOIN benh_nhan bn ON ph.benh_nhan_id = bn.id
            LEFT JOIN phieu_kham pk ON ph.phieu_kham_id = pk.id
            WHERE ph.id = ?
        ''', (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def reply(feedback_id, tra_loi, trang_thai='Đã giải quyết', nguoi_tra_loi='Bộ phận CSKH'):
        """Nhân viên/Quản trị viên trả lời và cập nhật trạng thái xử lý phản hồi."""
        if not tra_loi or len(tra_loi.strip()) == 0:
            return False, "Nội dung trả lời không được để trống!"

        valid_statuses = ['Chờ tiếp nhận', 'Đang xử lý', 'Đã giải quyết', 'Đóng']
        if trang_thai not in valid_statuses:
            trang_thai = 'Đã giải quyết'

        fb = FeedbackModel.get_by_id(feedback_id)
        if not fb:
            return False, "Không tìm thấy phản hồi cần xử lý!"

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE phan_hoi
                SET tra_loi = ?, trang_thai = ?, ngay_tra_loi = ?, nguoi_tra_loi = ?
                WHERE id = ?
            ''', (tra_loi.strip(), trang_thai, now_str, nguoi_tra_loi, feedback_id))

            # Tự động gửi thông báo in-app cho tài khoản bệnh nhân nếu có
            if fb.get('tai_khoan_id'):
                cursor.execute('''
                    INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                    VALUES (?, ?, ?, 'Phản hồi', '/patient/feedbacks', 0, ?)
                ''', (
                    fb['tai_khoan_id'],
                    f"Phản hồi về ý kiến: {fb.get('chu_de')}",
                    f"Phòng khám đã trả lời góp ý của bạn: '{tra_loi.strip()[:100]}...'",
                    now_str
                ))

            conn.commit()
            conn.close()
            return True, "Đã gửi câu trả lời và cập nhật trạng thái thành công!"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi cập nhật phản hồi: {str(e)}"
