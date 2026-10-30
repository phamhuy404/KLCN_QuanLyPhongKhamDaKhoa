"""Clinical values stay unknown until recorded; lab results require approval."""
from flask import has_request_context, session
from jinja2 import Undefined


def clinical_value(value):
    return None if value is None or isinstance(value, str) and not value.strip() else value


def result_is_published(result):
    return result.get('trang_thai') == 'Đã duyệt'


def patient_request():
    return has_request_context() and session.get('user', {}).get('vai_tro') == 'BENHNHAN'


def published_results(results):
    return [result for result in results if result_is_published(result)]


def display_clinical(value, placeholder='Chưa có dữ liệu'):
    return placeholder if isinstance(value, Undefined) or clinical_value(value) is None else value
