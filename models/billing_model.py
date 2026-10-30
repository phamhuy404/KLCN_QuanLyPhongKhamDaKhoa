from datetime import datetime
from core.database import get_db
from core.scheduling import serialized, CalendarError, integer
from core.pharmacy_safety import invoices, check_bill, APPROVED, HOSPITAL
from core.billing_policy import fetch_invoice, validate_invoice, money, CASHIER_ROLES, PAYMENT_METHODS, PAID, UNPAID
from flask import has_request_context
from core.security import refresh_session_user

class BillingModel:
    """Model quản lý hóa đơn, viện phí và thanh toán Bảo hiểm Y tế."""

    @staticmethod
    def get_invoice(identifier):
        conn = get_db()
        try:
            cursor = conn.cursor()
            bill = fetch_invoice(cursor, identifier)
            if bill:
                cursor.execute('SELECT * FROM chi_tiet_hoa_don WHERE hoa_don_id=? ORDER BY id', (bill['id'],))
                bill['chi_tiet'] = [dict(row) for row in cursor.fetchall()]
            return bill
        except CalendarError:
            return None
        finally:
            conn.close()

    @staticmethod
    def payment_instructions(identifier, patient_id=None):
        """Read-only instructions, not a transfer, receipt or persistent transaction."""
        conn = get_db()
        try:
            cursor = conn.cursor()
            bill = fetch_invoice(cursor, identifier)
            if not bill:
                return False, 'Không tìm thấy hóa đơn.'
            if patient_id is not None and bill['benh_nhan_id'] != patient_id:
                return False, 'Hóa đơn không thuộc bệnh nhân.'
            if bill['trang_thai'] != UNPAID:
                return False, 'Hóa đơn không ở trạng thái chờ thanh toán.'
            validate_invoice(cursor, bill)
            return True, {'invoice_id': bill['id'], 'ma_hoa_don': bill['ma_hoa_don'],
                          'amount': bill['thanh_tien'], 'status': bill['trang_thai'],
                          'gateway_enabled': False, 'payment_confirmed': False}
        except (CalendarError, ValueError) as exc:
            return False, str(exc)
        finally:
            conn.close()

    @staticmethod
    def get_all(patient_id=None):
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
                hd.trang_thai_nhan_thuoc,
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
            WHERE (? IS NULL OR hd.benh_nhan_id=?)
            ORDER BY hd.id DESC
        ''', (patient_id, patient_id))
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
            inv['status'] = {'Đã thanh toán':'paid', 'Chưa thanh toán':'pending', 'Đã hủy':'canceled'}.get(inv['trang_thai'], 'unknown')

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
                    inv['khoan_muc'] = 'Chi phí khám bệnh và dịch vụ ban đầu'
                else:
                    inv['khoan_muc'] = 'Chi phí khám bệnh và cận lâm sàng'

        conn.close()
        return invoices

    @staticmethod
    def get_by_patient(patient_id):
        """Lấy danh sách hóa đơn của bệnh nhân."""
        patient_id = integer(patient_id)
        if patient_id <= 0:
            raise CalendarError('Mã bệnh nhân không hợp lệ.')
        return BillingModel.get_all(patient_id=patient_id)

    @staticmethod
    @serialized
    def pay_invoice(invoice_id_or_code, payment_method='Tiền mặt', cashier_name='Thu ngân', audit_user=None, expected_amount=None):
        """Xác nhận thu viện phí và đổi trạng thái hóa đơn thành Đã thanh toán kèm thông báo in-app."""
        actor = refresh_session_user() if has_request_context() else audit_user
        if not actor or actor.get('vai_tro') not in CASHIER_ROLES or not actor.get('id'):
            return False, 'Chi nhan vien thu ngan duoc phan quyen moi duoc xac nhan thu.'
        if payment_method not in PAYMENT_METHODS:
            return False, 'Chi ho tro thu tien mat hoac chuyen khoan doi soat thu cong.'
        cashier_name = actor.get('ho_ten') or str(actor['id'])
        conn = get_db()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            hd_row = fetch_invoice(cursor, invoice_id_or_code, lock=True)
            if not hd_row:
                raise CalendarError('Khong tim thay hoa don.')
            if hd_row['trang_thai'] != UNPAID:
                raise CalendarError('Hoa don da thanh toan, da huy hoac trang thai khong hop le; khong ghi nhan thu lai.')
            if expected_amount is not None and money(expected_amount) != money(hd_row['thanh_tien']):
                raise CalendarError('So tien da thay doi; vui long tai lai va doi soat.')
            validate_invoice(cursor, hd_row)
            if str(hd_row['ma_hoa_don']).startswith('HDT'):
                from models.pharmacy_model import PharmacyModel
                cursor.execute('SELECT id FROM don_thuoc WHERE phieu_kham_id=?', (hd_row['phieu_kham_id'],))
                orders = cursor.fetchall()
                if len(orders) != 1:
                    raise CalendarError('Khong xac dinh duoc don thuoc duy nhat.')
                prescription = PharmacyModel.get_prescription_detail(orders[0]['id'])
                bills = invoices(cursor, prescription)
                if len(bills) != 1 or bills[0]['id'] != hd_row['id'] or prescription['trang_thai'] not in APPROVED or prescription['hinh_thuc_mua'] != HOSPITAL:
                    raise CalendarError('Don thuoc chua duyet hoac hoa don khong hop le.')
                check_bill(cursor, bills[0], prescription)

            cursor.execute('''UPDATE hoa_don
                SET trang_thai=?, hinh_thuc_thanh_toan=?, nhan_vien_thu=?, thoi_gian_thanh_toan=?
                OUTPUT inserted.id AS paid_invoice_id
                WHERE id=? AND trang_thai=?''',
                (PAID, payment_method, cashier_name, now_str, hd_row['id'], UNPAID))
            if not cursor.fetchone():
                raise CalendarError('Hoa don da thay doi; vui long tai lai.')

            # Nếu là hóa đơn tiền thuốc (HDT): Cập nhật trạng thái nhận thuốc trên hóa đơn và đơn thuốc
            is_drug_invoice = hd_row and str(hd_row.get('ma_hoa_don', '')).startswith('HDT')
            if is_drug_invoice and hd_row.get('phieu_kham_id'):
                cursor.execute('''
                    UPDATE hoa_don 
                    SET trang_thai_nhan_thuoc = N'Chưa nhận thuốc'
                    WHERE id = ?
                ''', (hd_row['id'],))

                cursor.execute('''
                    UPDATE don_thuoc 
                    SET trang_thai = N'Chờ nhận thuốc'
                    WHERE id = ? AND trang_thai = ?
                ''', (prescription['id'], prescription['trang_thai']))

                # Gửi thông báo cho Quản lý kho dược (Dược sĩ và Admin) để chuẩn bị phát thuốc
                cursor.execute("SELECT id FROM tai_khoan WHERE vai_tro_id IN (1, 4) AND trang_thai = 1")
                pharmacists = cursor.fetchall()
                for ph in pharmacists:
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Cấp phát thuốc', '/admin/pharmacy?tab=dispensing', 0, ?)
                    ''', (
                        ph['id'],
                        f"Đơn thuốc mới đã thanh toán ({hd_row['ma_hoa_don']})",
                        f"Hóa đơn tiền thuốc {hd_row['ma_hoa_don']} đã được thanh toán. Đơn thuốc chuyển sang 'Chờ nhận thuốc', vui lòng chuẩn bị và cấp phát cho bệnh nhân.",
                        now_str
                    ))

            # Gửi thông báo thanh toán thành công cho bệnh nhân
            if hd_row and hd_row.get('benh_nhan_id'):
                cursor.execute('SELECT tai_khoan_id FROM benh_nhan WHERE id = ?', (hd_row['benh_nhan_id'],))
                bn_row = cursor.fetchone()
                if bn_row and bn_row.get('tai_khoan_id'):
                    so_tien = int(hd_row.get('thanh_tien') or 0)
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, 'Thanh toán thành công', '/patient/invoices', 0, ?)
                    ''', (
                        bn_row['tai_khoan_id'],
                        f"Thanh toán thành công: {hd_row['ma_hoa_don']}",
                        f"Hóa đơn {hd_row['ma_hoa_don']} ({so_tien:,} VNĐ) đã được thanh toán thành công qua {payment_method}. Người thu: {cashier_name}.",
                        now_str
                    ))

            conn.commit()
            conn.close()
            return True, 'Xác nhận thu viện phí thành công!'
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
