from datetime import datetime
from core.database import get_db

class BillingModel:
    """Model quản lý hóa đơn, viện phí và thanh toán Bảo hiểm Y tế."""

    @staticmethod
    def get_all():
        """Lấy toàn bộ danh sách hóa đơn viện phí."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                hd.id, hd.ma_hoa_don AS ma_hd, hd.tong_tien, hd.tien_bhyt, hd.giam_gia, hd.thanh_tien,
                hd.hinh_thuc_thanh_toan, hd.trang_thai, hd.thoi_gian_thanh_toan AS ngay_tao, hd.nhan_vien_thu,
                bn.id AS benh_nhan_id, bn.ma_benh_nhan AS ma_bn, bn.ho_ten AS benh_nhan, bn.bhyt
            FROM hoa_don hd
            JOIN benh_nhan bn ON hd.benh_nhan_id = bn.id
            ORDER BY hd.id DESC
        ''')
        invoices = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return invoices

    @staticmethod
    def get_by_patient(patient_id):
        """Lấy danh sách hóa đơn của bệnh nhân."""
        all_invoices = BillingModel.get_all()
        return [inv for inv in all_invoices if inv['benh_nhan_id'] == patient_id]

    @staticmethod
    def pay_invoice(invoice_id_or_code, payment_method='Tiền mặt', cashier_name='Thu ngân'):
        """Xác nhận thu viện phí và đổi trạng thái hóa đơn thành Đã thanh toán."""
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE hoa_don 
                SET trang_thai = 'Đã thanh toán',
                    hinh_thuc_thanh_toan = ?,
                    nhan_vien_thu = ?,
                    thoi_gian_thanh_toan = ?
                WHERE id = ? OR ma_hoa_don = ?
            ''', (payment_method, cashier_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), invoice_id_or_code, str(invoice_id_or_code)))

            conn.commit()
            conn.close()
            return True, 'Xác nhận thu viện phí thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
