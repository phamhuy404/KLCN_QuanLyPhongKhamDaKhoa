# -*- coding: utf-8 -*-
from datetime import datetime, date
from decimal import Decimal

def format_currency(value):
    """Định dạng tiền tệ theo chuẩn Việt Nam có phân tách hàng nghìn và ký hiệu đ."""
    if value is None or value == '':
        return '0 đ'
    try:
        val = int(Decimal(str(value)))
        return f"{val:,}".replace(',', '.') + ' đ'
    except (ValueError, TypeError, ArithmeticError):
        return '0 đ'

def format_currency_raw(value):
    """Định dạng tiền tệ dạng chuỗi số có dấu chấm phân tách hàng nghìn (không kèm ký hiệu đ)."""
    if value is None or value == '':
        return '0'
    try:
        val = int(Decimal(str(value)))
        return f"{val:,}".replace(',', '.')
    except (ValueError, TypeError, ArithmeticError):
        return '0'

def format_date_vn(value):
    """Định dạng ngày tháng chuẩn Việt Nam dd/mm/YYYY."""
    if not value:
        return '---'
    if isinstance(value, (datetime, date)):
        return value.strftime('%d/%m/%Y')
    s = str(value).strip()
    if not s or s.lower() in ('none', 'null'):
        return '---'
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(s[:10], fmt).strftime('%d/%m/%Y')
        except ValueError:
            pass
    return s[:10]

def format_datetime_vn(value):
    """Định dạng ngày giờ chuẩn Việt Nam HH:MM dd/mm/YYYY."""
    if not value:
        return '---'
    if isinstance(value, datetime):
        return value.strftime('%H:%M %d/%m/%Y')
    s = str(value).strip()
    if not s or s.lower() in ('none', 'null'):
        return '---'
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M'):
        try:
            return datetime.strptime(s[:19], fmt).strftime('%H:%M %d/%m/%Y')
        except ValueError:
            pass
    return format_date_vn(s)
