from datetime import datetime
from core.database import get_db

class BillingModel:
    """Model quản lý hóa đơn, viện phí và thanh toán Bảo hiểm Y tế."""

    @staticmethod
    def get_all():
        """Lấy toàn bộ danh sách hóa đơn viện phí cùng chi tiết các khoản thu."""
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                hd.id, 
                hd.ma_hoa_don,
                hd.ma_hoa_don AS ma_hd, 
                hd.tong_tien, 
                hd.tien_bhyt,
                hd.tien_bhyt AS tien_bhyt_chi_tra,
                hd.giam_gia, 
                hd.thanh_tien,
                hd.hinh_thuc_thanh_toan, 
                hd.trang_thai, 
                hd.thoi_gian_thanh_toan,
                hd.thoi_gian_thanh_toan AS ngay_tao, 
                hd.nhan_vien_thu,
                hd.phieu_kham_id,
                bn.id AS benh_nhan_id, 
                bn.ma_benh_nhan,
                bn.ma_benh_nhan AS ma_bn, 
                bn.ho_ten AS ho_ten_benh_nhan,
                bn.ho_ten AS benh_nhan, 
                bn.bhyt,
                bn.sdt
            FROM hoa_don hd
            JOIN benh_nhan bn ON hd.benh_nhan_id = bn.id
            ORDER BY hd.id DESC
        ''')
        invoices = [dict(r) for r in cursor.fetchall()]

        for inv in invoices:
            inv['tong_tien'] = float(inv['tong_tien'] or 0)
            inv['tien_bhyt'] = float(inv['tien_bhyt'] or 0)
            inv['tien_bhyt_chi_tra'] = inv['tien_bhyt']
            inv['thanh_tien'] = float(inv['thanh_tien'] or 0)
            inv['giam_gia'] = float(inv['giam_gia'] or 0)
            
            # Gán sẵn các biến số phục vụ hiển thị trực tiếp mà không cần FrontEnd tính toán lại
            inv['tong'] = inv['tong_tien']
            inv['bhyt'] = inv['tien_bhyt']
            inv['thuc_thu'] = inv['thanh_tien']
            inv['patient_id'] = inv['benh_nhan_id']
            inv['phuong_thuc'] = inv.get('hinh_thuc_thanh_toan') or 'Tiền mặt'
            inv['status'] = 'paid' if inv['trang_thai'] == 'Đã thanh toán' else 'pending'

            # Lấy chi tiết các khoản thu
            cursor.execute('''
                SELECT id, loai_khoan_thu, ten_khoan_thu, so_luong, don_gia, thanh_tien
                FROM chi_tiet_hoa_don
                WHERE hoa_don_id = ?
            ''', (inv['id'],))
            cts = [dict(ct) for ct in cursor.fetchall()]
            for item in cts:
                item['don_gia'] = float(item['don_gia'] or 0)
                item['thanh_tien'] = float(item['thanh_tien'] or 0)
            inv['chi_tiet'] = cts

            if cts:
                items_str = []
                for ct in cts:
                    loai = ct.get('loai_khoan_thu') or ''
                    ten = ct.get('ten_khoan_thu') or ''
                    if loai:
                        items_str.append(f"[{loai}] {ten}")
                    else:
                        items_str.append(ten)
                inv['khoan_muc'] = ", ".join(items_str)
            else:
                if str(inv.get('ma_hoa_don', '')).startswith('HDT'):
                    inv['khoan_muc'] = 'Hóa đơn thuốc điều trị tại bệnh viện'
                elif str(inv.get('ma_hoa_don', '')).startswith('HDK'):
                    inv['khoan_muc'] = 'Chi phí khám bệnh & dịch vụ ban đầu'
                else:
                    inv['khoan_muc'] = 'Chi phí khám bệnh & cận lâm sàng'

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
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            is_num = str(invoice_id_or_code).isdigit()
            if is_num:
                cursor.execute('''
                    UPDATE hoa_don 
                    SET trang_thai = ?,
                        hinh_thuc_thanh_toan = ?,
                        nhan_vien_thu = ?,
                        thoi_gian_thanh_toan = ?
                    WHERE id = ? OR ma_hoa_don = ?
                ''', ('Đã thanh toán', payment_method, cashier_name, now_str, int(invoice_id_or_code), str(invoice_id_or_code)))
            else:
                cursor.execute('''
                    UPDATE hoa_don 
                    SET trang_thai = ?,
                        hinh_thuc_thanh_toan = ?,
                        nhan_vien_thu = ?,
                        thoi_gian_thanh_toan = ?
                    WHERE ma_hoa_don = ?
                ''', ('Đã thanh toán', payment_method, cashier_name, now_str, str(invoice_id_or_code)))

            conn.commit()
            conn.close()
            return True, 'Xác nhận thu viện phí thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
