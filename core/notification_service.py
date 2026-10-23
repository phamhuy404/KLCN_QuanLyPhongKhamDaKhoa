import os
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config
from core.database import get_db

class NotificationService:
    """Dịch vụ gửi thông báo nhắc lịch khám, nhắc tái khám qua In-App và Email SMTP."""

    @staticmethod
    def get_smtp_status():
        """Kiểm tra tình trạng cấu hình SMTP trong hệ thống."""
        server = getattr(config, 'SMTP_SERVER', '')
        user = getattr(config, 'SMTP_USERNAME', '')
        pwd = getattr(config, 'SMTP_PASSWORD', '')

        if not server or not user or not pwd:
            return {
                'configured': False,
                'message': 'Chưa cấu hình đầy đủ biến môi trường SMTP (SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD). Hệ thống vẫn lưu thông báo In-App trong website.',
                'server': server,
                'port': getattr(config, 'SMTP_PORT', 587),
                'sender': getattr(config, 'SMTP_SENDER_EMAIL', user)
            }
        return {
            'configured': True,
            'message': 'SMTP đã được cấu hình sẵn sàng gửi email.',
            'server': server,
            'port': getattr(config, 'SMTP_PORT', 587),
            'sender': getattr(config, 'SMTP_SENDER_EMAIL', user)
        }

    @staticmethod
    def send_email(to_email, subject, html_content):
        """Gửi email HTML qua máy chủ SMTP an toàn với TLS/SSL."""
        if not to_email:
            return False, "Thiếu địa chỉ email người nhận!"

        status = NotificationService.get_smtp_status()
        if not status['configured']:
            return False, status['message']

        server_host = config.SMTP_SERVER
        port = getattr(config, 'SMTP_PORT', 587)
        username = config.SMTP_USERNAME
        password = config.SMTP_PASSWORD
        use_tls = getattr(config, 'SMTP_USE_TLS', True)
        sender_email = getattr(config, 'SMTP_SENDER_EMAIL', username)
        sender_name = getattr(config, 'SMTP_SENDER_NAME', 'Phòng Khám Đa Khoa H2T Care')

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = to_email

            part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part)

            if port == 465:
                server = smtplib.SMTP_SSL(server_host, port, timeout=15)
            else:
                server = smtplib.SMTP(server_host, port, timeout=15)
                if use_tls:
                    server.starttls()

            server.login(username, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()
            return True, "Gửi email thành công!"
        except Exception as e:
            return False, f"Lỗi gửi email SMTP: {str(e)}"

    @staticmethod
    def check_reminder_sent(loai_nhac, lich_hen_id=None, phieu_kham_id=None, ngay_nhac=None):
        """Kiểm tra xem thông báo loại này đã từng được gửi cho lịch hẹn/phiếu khám này chưa (Chống gửi trùng)."""
        conn = get_db()
        cursor = conn.cursor()
        if loai_nhac == 'LICH_HEN':
            cursor.execute('''
                SELECT id FROM lich_su_nhac_nho
                WHERE loai_nhac = 'LICH_HEN' AND lich_hen_id = ?
            ''', (lich_hen_id,))
        else:
            cursor.execute('''
                SELECT id FROM lich_su_nhac_nho
                WHERE loai_nhac = 'TAI_KHAM' AND phieu_kham_id = ?
            ''', (phieu_kham_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    @staticmethod
    def _log_reminder(benh_nhan_id, loai_nhac, lich_hen_id=None, phieu_kham_id=None, ngay_nhac=None, kenh_gui='IN_APP', trang_thai='THANH_CONG', loi_gui=''):
        """Ghi nhận lịch sử gửi nhắc lịch vào CSDL để ngăn chặn gửi trùng."""
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lich_su_nhac_nho (lich_hen_id, phieu_kham_id, benh_nhan_id, loai_nhac, ngay_nhac, kenh_gui, trang_thai, loi_gui, thoi_gian_gui)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (lich_hen_id, phieu_kham_id, benh_nhan_id, loai_nhac, str(ngay_nhac) if ngay_nhac else None, kenh_gui, trang_thai, loi_gui, now_str))
            conn.commit()
            conn.close()
        except Exception as e:
            print("[NotificationService] Loi ghi log nhac nho:", e)

    @staticmethod
    def run_all_reminders():
        """Quét và gửi nhắc lịch hẹn khám và lịch tái khám trong vòng 24 - 48 giờ tới."""
        stats = {
            'appointments_scanned': 0,
            'appointments_reminded': 0,
            'reexams_scanned': 0,
            'reexams_reminded': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'in_app_sent': 0,
            'errors': []
        }

        # Tính toán ngày hiện tại và ngày mai (Múi giờ Việt Nam)
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        today_str = str(today)
        tomorrow_str = str(tomorrow)
        day_after_str = str(day_after)

        conn = get_db()
        cursor = conn.cursor()

        # 1. QUÉT VÀ NHẮC LỊCH HẸN KHÁM (Lịch hẹn ngày mai hoặc hôm nay chưa khám)
        try:
            cursor.execute('''
                SELECT 
                    lh.id, lh.ma_lich_hen, lh.ngay_hen, lh.gio_hen, lh.ly_do_kham, lh.trang_thai,
                    bn.id AS benh_nhan_id, bn.ho_ten AS ten_benh_nhan, bn.email AS email_benh_nhan, bn.sdt AS sdt_benh_nhan, bn.tai_khoan_id,
                    ck.ten_khoa,
                    pk.ten_phong,
                    nv.ho_ten AS ten_bac_si
                FROM lich_hen lh
                JOIN benh_nhan bn ON lh.benh_nhan_id = bn.id
                JOIN chuyen_khoa ck ON lh.chuyen_khoa_id = ck.id
                LEFT JOIN phong_kham pk ON lh.phong_kham_id = pk.id
                LEFT JOIN bac_si bs ON lh.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE (lh.ngay_hen = ? OR lh.ngay_hen = ?)
                  AND lh.trang_thai NOT IN ('Đã hủy', 'Đã khám', 'Hoàn thành')
            ''', (today_str, tomorrow_str))
            appointments = [dict(r) for r in cursor.fetchall()]
            stats['appointments_scanned'] = len(appointments)

            for appt in appointments:
                appt_id = appt['id']
                # Kiểm tra chống gửi trùng
                if NotificationService.check_reminder_sent('LICH_HEN', lich_hen_id=appt_id):
                    continue

                # Tạo thông báo In-App
                title = f"Nhắc lịch khám bệnh: {appt['ma_lich_hen']}"
                content = (
                    f"Kính gửi {appt['ten_benh_nhan']}, quý khách có lịch khám tại {appt['ten_khoa']} "
                    f"vào ngày {appt['ngay_hen']} lúc {appt['gio_hen']} "
                    f"(Bác sĩ: {appt['ten_bac_si'] or 'Bác sĩ chuyên khoa'}). "
                    f"Vui lòng đến trước 15 phút để làm thủ tục tiếp đón."
                )

                if appt.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Nhắc lịch khám', '/patient/booking', 0, ?)
                    ''', (appt['tai_khoan_id'], title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    stats['in_app_sent'] += 1

                # Gửi email nếu bệnh nhân có email
                email_status = 'THANH_CONG'
                email_err = ''
                if appt.get('email_benh_nhan'):
                    email_html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                        <div style="background: linear-gradient(135deg, #0d9488, #0f766e); padding: 24px; color: white; text-align: center;">
                            <h2 style="margin: 0; font-size: 20px;">PHÒNG KHÁM ĐA KHOA H2T CARE</h2>
                            <p style="margin: 6px 0 0; opacity: 0.9; font-size: 14px;">THÔNG BÁO NHẮC LỊCH KHÁM BỆNH</p>
                        </div>
                        <div style="padding: 24px; background: #ffffff;">
                            <p>Xin chào <strong>{appt['ten_benh_nhan']}</strong>,</p>
                            <p>Hệ thống trân trọng thông báo nhắc lịch khám bệnh của quý khách trong 24 giờ tới:</p>
                            <table style="width: 100%; border-collapse: collapse; margin: 16px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                                <tr><td style="padding: 10px 14px; font-weight: bold; border-bottom: 1px solid #e2e8f0; width: 40%;">Mã lịch hẹn:</td><td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #0d9488; font-weight: bold;">{appt['ma_lich_hen']}</td></tr>
                                <tr><td style="padding: 10px 14px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Thời gian:</td><td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;"><strong>{appt['gio_hen']}</strong> - Ngày <strong>{appt['ngay_hen']}</strong></td></tr>
                                <tr><td style="padding: 10px 14px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Chuyên khoa:</td><td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">{appt['ten_khoa']}</td></tr>
                                <tr><td style="padding: 10px 14px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Bác sĩ phụ trách:</td><td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">{appt['ten_bac_si'] or 'Bác sĩ chuyên khoa'}</td></tr>
                                <tr><td style="padding: 10px 14px; font-weight: bold;">Địa điểm:</td><td style="padding: 10px 14px;">{appt['ten_phong'] or 'Khu khám bệnh ngoại trú'} - 140 Lê Trọng Tấn, Tân Phú, TP.HCM</td></tr>
                            </table>
                            <p style="color: #64748b; font-size: 13px;">* Quý khách vui lòng đến trước 15 phút để hoàn tất thủ tục tiếp đón và đo chỉ số sinh tồn. Nếu có nhu cầu đổi lịch, vui lòng liên hệ hotline 1900 8888.</p>
                        </div>
                    </div>
                    """
                    ok, msg_err = NotificationService.send_email(appt['email_benh_nhan'], f"[H2T Care] Nhắc lịch hẹn khám bệnh {appt['ma_lich_hen']}", email_html)
                    if ok:
                        stats['emails_sent'] += 1
                    else:
                        stats['emails_failed'] += 1
                        email_status = 'THAT_BAI'
                        email_err = msg_err

                # Ghi lịch sử nhắc để không gửi trùng
                NotificationService._log_reminder(
                    benh_nhan_id=appt['benh_nhan_id'],
                    loai_nhac='LICH_HEN',
                    lich_hen_id=appt_id,
                    ngay_nhac=appt['ngay_hen'],
                    kenh_gui='EMAIL+IN_APP' if appt.get('email_benh_nhan') else 'IN_APP',
                    trang_thai=email_status,
                    loi_gui=email_err
                )
                stats['appointments_reminded'] += 1

        except Exception as e:
            stats['errors'].append(f"Lỗi quét lịch hẹn: {str(e)}")

        # 2. QUÉT VÀ NHẮC LỊCH TÁI KHÁM (Phiếu khám có ngày tái khám là hôm nay hoặc ngày mai)
        try:
            cursor.execute('''
                SELECT 
                    pk.id, pk.ma_phieu, pk.ngay_tai_kham, pk.chan_doan_so_bo, pk.loi_dan,
                    bn.id AS benh_nhan_id, bn.ho_ten AS ten_benh_nhan, bn.email AS email_benh_nhan, bn.tai_khoan_id,
                    nv.ho_ten AS ten_bac_si
                FROM phieu_kham pk
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN bac_si bs ON pk.bac_si_id = bs.id
                LEFT JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
                WHERE pk.ngay_tai_kham IS NOT NULL
                  AND (pk.ngay_tai_kham = ? OR pk.ngay_tai_kham = ?)
            ''', (today_str, tomorrow_str))
            reexams = [dict(r) for r in cursor.fetchall()]
            stats['reexams_scanned'] = len(reexams)

            for rx in reexams:
                rx_id = rx['id']
                if NotificationService.check_reminder_sent('TAI_KHAM', phieu_kham_id=rx_id):
                    continue

                title = f"Nhắc lịch hẹn tái khám: {rx['ma_phieu']}"
                content = (
                    f"Kính gửi {rx['ten_benh_nhan']}, quý khách có lịch tái khám theo hẹn "
                    f"vào ngày {rx['ngay_tai_kham']} (Bác sĩ: {rx['ten_bac_si'] or 'Bác sĩ điều trị'}). "
                    f"Lời dặn: {rx['loi_dan'] or 'Đem theo đơn thuốc cũ'}. "
                    f"Vui lòng đặt lịch hẹn hoặc đến phòng khám đúng hẹn."
                )

                if rx.get('tai_khoan_id'):
                    cursor.execute('''
                        INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                        VALUES (?, ?, ?, N'Nhắc tái khám', '/patient/records', 0, ?)
                    ''', (rx['tai_khoan_id'], title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    stats['in_app_sent'] += 1

                email_status = 'THANH_CONG'
                email_err = ''
                if rx.get('email_benh_nhan'):
                    email_html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                        <div style="background: linear-gradient(135deg, #0284c7, #0369a1); padding: 24px; color: white; text-align: center;">
                            <h2 style="margin: 0; font-size: 20px;">PHÒNG KHÁM ĐA KHOA H2T CARE</h2>
                            <p style="margin: 6px 0 0; opacity: 0.9; font-size: 14px;">THÔNG BÁO NHẮC LỊCH TÁI KHÁM</p>
                        </div>
                        <div style="padding: 24px; background: #ffffff;">
                            <p>Xin chào <strong>{rx['ten_benh_nhan']}</strong>,</p>
                            <p>Theo phiếu khám bệnh <strong>{rx['ma_phieu']}</strong>, quý khách có lịch tái khám định kỳ:</p>
                            <table style="width: 100%; border-collapse: collapse; margin: 16px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                                <tr><td style="padding: 10px 14px; font-weight: bold; border-bottom: 1px solid #e2e8f0; width: 40%;">Ngày tái khám:</td><td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #0284c7; font-weight: bold;">{rx['ngay_tai_kham']}</td></tr>
                                <tr><td style="padding: 10px 14px; font-weight: bold; border-bottom: 1px solid #e2e8f0;">Bác sĩ điều trị:</td><td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">{rx['ten_bac_si'] or 'Bác sĩ điều trị'}</td></tr>
                                <tr><td style="padding: 10px 14px; font-weight: bold;">Lời dặn:</td><td style="padding: 10px 14px;">{rx['loi_dan'] or 'Mang theo đơn thuốc cũ và kết quả xét nghiệm'}</td></tr>
                            </table>
                            <p style="color: #64748b; font-size: 13px;">Tái khám đúng hẹn giúp bác sĩ đánh giá mức độ phục hồi và điều chỉnh phác đồ điều trị kịp thời.</p>
                        </div>
                    </div>
                    """
                    ok, msg_err = NotificationService.send_email(rx['email_benh_nhan'], f"[H2T Care] Nhắc lịch tái khám theo hẹn ngày {rx['ngay_tai_kham']}", email_html)
                    if ok:
                        stats['emails_sent'] += 1
                    else:
                        stats['emails_failed'] += 1
                        email_status = 'THAT_BAI'
                        email_err = msg_err

                NotificationService._log_reminder(
                    benh_nhan_id=rx['benh_nhan_id'],
                    loai_nhac='TAI_KHAM',
                    phieu_kham_id=rx_id,
                    ngay_nhac=rx['ngay_tai_kham'],
                    kenh_gui='EMAIL+IN_APP' if rx.get('email_benh_nhan') else 'IN_APP',
                    trang_thai=email_status,
                    loi_gui=email_err
                )
                stats['reexams_reminded'] += 1

        except Exception as e:
            stats['errors'].append(f"Lỗi quét lịch tái khám: {str(e)}")

        conn.close()
        return stats

    @staticmethod
    def start_background_scheduler(interval_hours=2):
        """Khởi chạy tiến trình kiểm tra định kỳ trong background thread (an toàn không chạy trùng)."""
        # Nếu đang trong môi trường Werkzeug reloader, chỉ khởi chạy ở worker chính
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and getattr(config, 'DEBUG', False):
            return

        def _worker():
            print("[NotificationService] Background Reminder Worker da khoi dong.")
            while True:
                try:
                    stats = NotificationService.run_all_reminders()
                    if stats['appointments_reminded'] > 0 or stats['reexams_reminded'] > 0:
                        print(f"[NotificationService] Da gui nhac nho: {stats['appointments_reminded']} lich hen, {stats['reexams_reminded']} tai kham.")
                except Exception as e:
                    print("[NotificationService] Loi trong tien trinh chay ngam:", e)
                # Chờ chu kỳ (mặc định 2 tiếng)
                time.sleep(interval_hours * 3600)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
