"""Durable, single-use email OTP recovery for web and mobile."""
import hashlib
import hmac
import html
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app

from core.database import get_db
from core.notification_service import NotificationService
from core.security import hash_password


OTP_TTL_SECONDS = 300
RESEND_SECONDS = 60
MAX_ATTEMPTS = 5
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


class ResetError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _email(value):
    email = value.strip().lower() if isinstance(value, str) else ''
    if len(email) > 100 or not EMAIL_RE.fullmatch(email):
        raise ResetError('INVALID_EMAIL', 'Email không đúng định dạng.')
    return email


def _account(cursor, email):
    cursor.execute('''SELECT DISTINCT t.id FROM tai_khoan t
        LEFT JOIN benh_nhan bn ON bn.tai_khoan_id=t.id
        LEFT JOIN nhan_vien nv ON nv.tai_khoan_id=t.id
        WHERE t.trang_thai=1 AND
        (LOWER(t.email)=? OR LOWER(bn.email)=? OR LOWER(nv.email)=?)''',
        (email, email, email))
    rows = cursor.fetchall()
    if len(rows) != 1:
        raise ResetError('EMAIL_NOT_FOUND', 'Email không tồn tại hoặc tài khoản không khả dụng.', 404)
    return rows[0]['id']


def _digest(account_id, code):
    key = current_app.secret_key
    if isinstance(key, str):
        key = key.encode('utf-8')
    return hmac.new(key, f'password-reset:{account_id}:{code}'.encode(), hashlib.sha256).hexdigest()


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _db_time(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def _challenge(cursor, account_id):
    cursor.execute('SELECT otp_hash, expires_at, sent_at, attempts, verified '
                   'FROM password_reset_otp WHERE account_id=?', (account_id,))
    return cursor.fetchone()


def send_otp(email_value):
    email = _email(email_value)
    conn = get_db()
    try:
        cursor = conn.cursor()
        account_id = _account(cursor, email)
        previous = _challenge(cursor, account_id)
        now = _utc_now()
        if previous and (now - _db_time(previous['sent_at'])).total_seconds() < RESEND_SECONDS:
            raise ResetError('RESEND_COOLDOWN', 'Vui lòng đợi 60 giây trước khi gửi lại mã.', 429)
        code = f'{secrets.randbelow(1000000):06d}'
        safe_name = html.escape(current_app.config.get('SMTP_SENDER_NAME', 'H2T Care'))
        content = f'''<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;border:1px solid #d4f8e8;border-radius:18px;overflow:hidden;color:#1e293b">
          <div style="background:#059669;color:white;padding:26px;text-align:center"><h2 style="margin:0">{safe_name}</h2><p style="margin:8px 0 0">Xác thực đặt lại mật khẩu</p></div>
          <div style="padding:30px;text-align:center"><p>Nhập mã sau để tiếp tục đặt lại mật khẩu:</p>
          <div style="font-size:34px;font-weight:bold;letter-spacing:9px;color:#047857;padding:14px;background:#eefcf6;border-radius:12px">{code}</div>
          <p style="font-size:14px;color:#475569">Mã có hiệu lực trong 5 phút. Không chia sẻ mã này với bất kỳ ai.</p>
          <p style="font-size:13px;color:#64748b">Nếu bạn không yêu cầu, hãy bỏ qua email này.</p></div></div>'''
        # Invalidate the previous code before SMTP, so a failed resend cannot revive it.
        cursor.execute('DELETE FROM password_reset_otp WHERE account_id=?', (account_id,))
        conn.commit()
        sent, send_error = NotificationService.send_email(email, 'Mã xác thực đặt lại mật khẩu H2T Care', content)
        if not sent:
            current_app.logger.warning('Password reset email delivery failed: %s', send_error)
            raise ResetError('EMAIL_SEND_FAILED', 'Chưa gửi được email. Vui lòng thử lại sau.', 503)
        cursor.execute('''INSERT INTO password_reset_otp
            (account_id, otp_hash, expires_at, sent_at, attempts, verified)
            VALUES (?, ?, ?, ?, 0, 0)''',
            (account_id, _digest(account_id, code), now + timedelta(seconds=OTP_TTL_SECONDS), now))
        conn.commit()
        return {'success': True, 'message': 'Mã OTP đã được gửi tới email của bạn.',
                'expires_in': OTP_TTL_SECONDS, 'resend_after': RESEND_SECONDS}
    finally:
        conn.close()


def _check_otp(cursor, account_id, code):
    if not isinstance(code, str) or not re.fullmatch(r'[0-9]{6}', code):
        raise ResetError('INVALID_OTP', 'Mã OTP phải gồm đúng 6 chữ số.')
    challenge = _challenge(cursor, account_id)
    if not challenge:
        raise ResetError('OTP_NOT_FOUND', 'Vui lòng gửi mã OTP mới.')
    if _utc_now() >= _db_time(challenge['expires_at']):
        raise ResetError('OTP_EXPIRED', 'Mã OTP đã hết hạn. Vui lòng gửi lại mã.')
    if challenge['attempts'] >= MAX_ATTEMPTS:
        raise ResetError('OTP_LOCKED', 'Đã nhập sai quá nhiều lần. Vui lòng gửi mã mới.', 429)
    if not hmac.compare_digest(challenge['otp_hash'], _digest(account_id, code)):
        cursor.execute('UPDATE password_reset_otp SET attempts=attempts+1 WHERE account_id=?', (account_id,))
        raise ResetError('INVALID_OTP', 'Mã OTP không chính xác.')
    return challenge


def verify_otp(email_value, code):
    email = _email(email_value)
    conn = get_db()
    try:
        cursor = conn.cursor()
        account_id = _account(cursor, email)
        try:
            _check_otp(cursor, account_id, code)
        finally:
            conn.commit()  # Preserve failed-attempt counter.
        cursor.execute('UPDATE password_reset_otp SET verified=1 WHERE account_id=?', (account_id,))
        conn.commit()
        return {'success': True, 'message': 'Xác thực OTP thành công.'}
    finally:
        conn.close()


def reset_password(email_value, code, new_password, confirmation):
    email = _email(email_value)
    if not isinstance(new_password, str) or not 6 <= len(new_password) <= 128 or new_password != new_password.strip():
        raise ResetError('INVALID_PASSWORD', 'Mật khẩu mới cần từ 6 đến 128 ký tự, không có khoảng trắng đầu/cuối.')
    if new_password != confirmation:
        raise ResetError('PASSWORD_MISMATCH', 'Mật khẩu xác nhận không khớp.')
    conn = get_db()
    try:
        cursor = conn.cursor()
        account_id = _account(cursor, email)
        try:
            challenge = _check_otp(cursor, account_id, code)
        finally:
            conn.commit()
        if not challenge['verified']:
            raise ResetError('OTP_NOT_VERIFIED', 'Vui lòng xác thực mã OTP trước.')
        cursor.execute('UPDATE tai_khoan SET password=?, yeu_cau_doi_mat_khau=0 WHERE id=?',
                       (hash_password(new_password), account_id))
        cursor.execute('DELETE FROM password_reset_otp WHERE account_id=?', (account_id,))
        conn.commit()
        return {'success': True, 'message': 'Đặt lại mật khẩu thành công. Vui lòng đăng nhập.'}
    finally:
        conn.close()
