"""VietQR presentation and authenticated bank notification parsing."""
import hmac
import hashlib
import json
import re
from decimal import Decimal
from urllib.parse import quote, urlencode

from flask import current_app, request

from core.billing_policy import money


REFERENCE = re.compile(r'(?<![A-Z0-9])H2T([1-9][0-9]*)(?![A-Z0-9])', re.I)


def bank_ready():
    settings = current_app.config
    if not all(str(settings.get(key) or '').strip() for key in
               ('BANK_ID', 'BANK_ACCOUNT_NO', 'BANK_ACCOUNT_NAME', 'PAYMENT_WEBHOOK_SECRET')):
        return False
    return (re.fullmatch(r'[A-Z0-9]{2,12}', str(settings['BANK_ID']).strip().upper()) is not None
            and re.fullmatch(r'[0-9]{6,25}', str(settings['BANK_ACCOUNT_NO']).strip()) is not None)


def payment_details(bill):
    if not bank_ready():
        raise ValueError('Chưa cấu hình tài khoản ngân hàng và khóa webhook.')
    amount = money(bill['thanh_tien'])
    if amount <= 0 or amount != amount.to_integral_value():
        raise ValueError('VietQR chỉ hỗ trợ hóa đơn có số tiền VND nguyên dương.')
    settings = current_app.config
    bank_id = str(settings['BANK_ID']).strip().upper()
    account = str(settings['BANK_ACCOUNT_NO']).strip()
    name = str(settings['BANK_ACCOUNT_NAME']).strip()
    reference = f"H2T{bill['id']}"
    query = urlencode({'amount': int(amount), 'addInfo': reference, 'accountName': name})
    return {'invoice_id': bill['id'], 'ma_hoa_don': bill['ma_hoa_don'],
            'amount': int(amount), 'status': 'PENDING', 'reference': reference,
            'bank_id': bank_id, 'bank_account_no': account, 'bank_account_name': name,
            'qr_url': f'https://img.vietqr.io/image/{quote(bank_id)}-{quote(account)}-compact2.png?{query}',
            'expires_in_seconds': 600}


def webhook_authorized():
    secret = str(current_app.config.get('PAYMENT_WEBHOOK_SECRET') or '')
    if not secret:
        return False
    signature = request.headers.get('X-Casso-Signature', '')
    if signature:
        try:
            parts = dict(part.split('=', 1) for part in signature.split(','))
            timestamp = parts['t']
            provided = parts['v1']
            if not timestamp.isdigit() or len(provided) != 128:
                return False
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                return False
            signed = f"{timestamp}.{json.dumps(payload, sort_keys=True, separators=(',', ':'))}"
            expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha512).hexdigest()
            return hmac.compare_digest(provided, expected)
        except (KeyError, ValueError, TypeError):
            return False
    # SePay API Key, Casso legacy secure-token, or an explicitly configured shared key.
    candidates = (request.headers.get('Authorization', ''),
                  request.headers.get('secure-token', ''),
                  request.headers.get('X-Payment-Webhook-Secret', ''))
    return any(hmac.compare_digest(value, expected) for value in candidates for expected in
               (secret, f'Apikey {secret}', f'Bearer {secret}'))


def parse_transactions(payload):
    """Normalize SePay JSON and Casso legacy/V2 JSON; reject ambiguous entries."""
    if not isinstance(payload, dict):
        raise ValueError('Webhook phải là JSON object.')
    if 'data' in payload and payload.get('error') not in (None, 0):
        raise ValueError('Webhook Casso báo lỗi.')
    data = payload.get('data', payload)
    provider = 'CASSO' if 'data' in payload else 'SEPAY'
    entries = data if isinstance(data, list) else [data]
    if not entries or len(entries) > 100:
        raise ValueError('Danh sách giao dịch không hợp lệ.')
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Giao dịch không hợp lệ.')
        event_id = entry.get('id')
        content = str(entry.get('content') or entry.get('description') or '')
        match = REFERENCE.search(content.upper())
        if not match and entry.get('code'):
            match = REFERENCE.fullmatch(str(entry['code']).upper())
        amount = money(entry.get('transferAmount') if provider == 'SEPAY' else entry.get('amount'))
        transfer_type = str(entry.get('transferType') or '').lower()
        account = str(entry.get('accountNumber') or entry.get('bank_sub_acc_id') or
                      entry.get('subAccId') or '').strip()
        if event_id is None or not str(event_id).strip() or len(str(event_id)) > 100:
            raise ValueError('Giao dịch thiếu ID để chống xử lý lặp.')
        if not account:
            raise ValueError('Giao dịch thiếu tài khoản nhận.')
        result.append({'provider': provider, 'event_id': str(event_id),
                       'invoice_id': int(match.group(1)) if match else None,
                       'amount': amount, 'account': account,
                       'incoming': transfer_type in ('', 'in') and amount > Decimal(0),
                       'content': content[:1000]})
    return result
