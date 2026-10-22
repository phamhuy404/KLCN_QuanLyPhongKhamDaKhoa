import re
from datetime import datetime, date

# Danh sách ký tự nguy hiểm hoặc lạ cấm tuyệt đối trong thông tin cá nhân
FORBIDDEN_CHARS_PATTERN = re.compile(r'[<>{}\[\]$%^*=~`|\\;]|--')

# Regex họ tên tiếng Việt (bao gồm các nguyên âm có dấu tiếng Việt và chữ đ)
VIETNAMESE_NAME_PATTERN = re.compile(
    r'^[a-zA-Zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    r'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ\s]+$'
)

# Regex số điện thoại di động Việt Nam (10 chữ số bắt đầu bằng 03, 05, 07, 08, 09)
VN_PHONE_PATTERN = re.compile(r'^(03|05|07|08|09)\d{8}$')

# Regex CCCD Việt Nam (đúng 12 chữ số)
CCCD_PATTERN = re.compile(r'^\d{12}$')

# Regex thẻ BHYT (từ 10 đến 15 ký tự chữ và số)
BHYT_PATTERN = re.compile(r'^[A-Z0-9]{10,15}$')

# Regex email hợp lệ
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def sanitize_text(text):
    """Làm sạch khoảng trắng thừa trong chuỗi."""
    if not text:
        return ''
    return ' '.join(str(text).strip().split())

def validate_patient_profile(data):
    """
    Kiểm tra tính hợp lệ toàn diện của hồ sơ bệnh nhân.
    Trả về: (is_valid, error_dict)
    """
    errors = {}

    ho_ten = sanitize_text(data.get('ho_ten', ''))
    sdt = sanitize_text(data.get('sdt', ''))
    ngay_sinh = sanitize_text(data.get('ngay_sinh', ''))
    gioi_tinh = sanitize_text(data.get('gioi_tinh', 'Nam'))
    cccd = sanitize_text(data.get('cccd', ''))
    bhyt = sanitize_text(data.get('bhyt', '')).upper()
    email = sanitize_text(data.get('email', ''))
    dia_chi = sanitize_text(data.get('dia_chi', ''))
    nhom_mau = sanitize_text(data.get('nhom_mau', 'Chưa rõ'))
    di_ung = sanitize_text(data.get('di_ung', ''))
    tien_su_benh = sanitize_text(data.get('tien_su_benh', ''))
    tien_su_gia_dinh = sanitize_text(data.get('tien_su_gia_dinh', ''))
    nguoi_than_ho_ten = sanitize_text(data.get('nguoi_than_ho_ten', ''))
    nguoi_than_sdt = sanitize_text(data.get('nguoi_than_sdt', ''))
    nguoi_than_quan_he = sanitize_text(data.get('nguoi_than_quan_he', ''))

    # 1. Kiểm tra ký tự lạ cấm
    text_fields_to_check = [
        ('ho_ten', ho_ten, 'Họ và tên'),
        ('cccd', cccd, 'Số CCCD'),
        ('bhyt', bhyt, 'Số thẻ BHYT'),
        ('dia_chi', dia_chi, 'Địa chỉ cư trú'),
        ('di_ung', di_ung, 'Dị ứng'),
        ('tien_su_benh', tien_su_benh, 'Tiền sử bệnh'),
        ('nguoi_than_ho_ten', nguoi_than_ho_ten, 'Tên người thân'),
        ('nguoi_than_quan_he', nguoi_than_quan_he, 'Mối quan hệ người thân')
    ]
    for field_key, val, field_label in text_fields_to_check:
        if val and FORBIDDEN_CHARS_PATTERN.search(val):
            errors[field_key] = f"{field_label} chứa ký tự đặc biệt lạ không hợp lệ!"

    # 2. Họ và tên
    if not ho_ten:
        errors['ho_ten'] = 'Vui lòng nhập Họ và tên đầy đủ!'
    elif len(ho_ten) < 2 or len(ho_ten) > 100:
        errors['ho_ten'] = 'Họ và tên phải có độ dài từ 2 đến 100 ký tự!'
    elif not VIETNAMESE_NAME_PATTERN.match(ho_ten):
        errors['ho_ten'] = 'Họ và tên chỉ được chứa chữ cái tiếng Việt và khoảng trắng, không chứa số hay ký tự lạ!'

    # 3. Số điện thoại
    if sdt and not VN_PHONE_PATTERN.match(sdt):
        errors['sdt'] = 'Số điện thoại không đúng định dạng di động Việt Nam (10 số, bắt đầu 03, 05, 07, 08, 09)!'

    # 4. Ngày sinh & Độ tuổi
    if not ngay_sinh:
        errors['ngay_sinh'] = 'Vui lòng chọn ngày sinh!'
    else:
        try:
            ns_date = datetime.strptime(ngay_sinh, '%Y-%m-%d').date()
            today = date.today()
            if ns_date > today:
                errors['ngay_sinh'] = 'Ngày sinh không thể lớn hơn ngày hiện tại!'
            elif today.year - ns_date.year > 130:
                errors['ngay_sinh'] = 'Ngày sinh không hợp lệ (tuổi không vượt quá 130)!'
        except ValueError:
            errors['ngay_sinh'] = 'Định dạng ngày sinh không hợp lệ (YYYY-MM-DD)!'

    # 5. Giới tính
    if gioi_tinh not in ['Nam', 'Nữ']:
        errors['gioi_tinh'] = 'Giới tính phải là Nam hoặc Nữ!'

    # 6. CCCD
    if not cccd:
        errors['cccd'] = 'Vui lòng nhập số Căn cước công dân (CCCD) 12 số!'
    elif not CCCD_PATTERN.match(cccd):
        errors['cccd'] = 'Số CCCD phải bao gồm đúng 12 chữ số, không chứa chữ hoặc ký tự lạ!'

    # 7. BHYT (nếu có)
    if bhyt and not BHYT_PATTERN.match(bhyt):
        errors['bhyt'] = 'Mã số thẻ BHYT phải có độ dài từ 10 đến 15 ký tự chữ và số!'

    # 8. Email (nếu có)
    if email and not EMAIL_PATTERN.match(email):
        errors['email'] = 'Địa chỉ email không đúng định dạng (ví dụ: nguyenvan@gmail.com)!'

    # 9. Địa chỉ
    if not dia_chi:
        errors['dia_chi'] = 'Vui lòng nhập địa chỉ cư trú chi tiết!'
    elif len(dia_chi) < 5:
        errors['dia_chi'] = 'Địa chỉ cư trú phải có ít nhất 5 ký tự!'

    # 10. SĐT người thân (nếu có)
    if nguoi_than_sdt and not VN_PHONE_PATTERN.match(nguoi_than_sdt):
        errors['nguoi_than_sdt'] = 'Số điện thoại người thân không đúng định dạng (10 số)!'

    if nguoi_than_ho_ten and not VIETNAMESE_NAME_PATTERN.match(nguoi_than_ho_ten):
        errors['nguoi_than_ho_ten'] = 'Họ tên người thân chỉ được chứa chữ cái tiếng Việt!'

    return len(errors) == 0, errors
