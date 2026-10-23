# -*- coding: utf-8 -*-
import re
from datetime import datetime, date

# Danh sach ky tu nguy hiem hoac la cam tuyet doi
FORBIDDEN_CHARS_PATTERN = re.compile(r'[<>{}\[\]$%^*=~`|\\;]|--')

# Regex ho ten tieng Viet: chi chua chu cai tieng Viet co dau, chu cai Latin va khoang trang don
VIETNAMESE_NAME_PATTERN = re.compile(
    r'^[a-zA-Zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    r'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ\s]+$'
)

# Regex so dien thoai di dong Viet Nam (10 chu so, bat dau bang 03, 05, 07, 08, 09)
VN_PHONE_PATTERN = re.compile(r'^(03|05|07|08|09)\d{8}$')

# Regex Can cuoc cong dan Viet Nam (dung 12 chu so, khong chu, khong ky tu la)
CCCD_PATTERN = re.compile(r'^\d{12}$')

# Regex the BHYT chuan quoc gia moi (dung 10 chu so, khong chu, khong ky tu la)
BHYT_PATTERN = re.compile(r'^\d{10}$')

# Regex email hop le
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def sanitize_text(text):
    """Lam sach khoang trang thua va loai bo ky tu vo danh."""
    if text is None:
        return ''
    return ' '.join(str(text).strip().split())

def validate_name(name, field_label='Họ và tên'):
    """Kiem tra rang buoc ho ten: khong chua so hay ky tu la, dai 2-100 ky tu."""
    name = sanitize_text(name)
    if not name:
        return False, f"{field_label} không được để trống!"
    if len(name) < 2 or len(name) > 100:
        return False, f"{field_label} phải có độ dài từ 2 đến 100 ký tự!"
    if any(c.isdigit() for c in name):
        return False, f"{field_label} không được chứa chữ số!"
    if FORBIDDEN_CHARS_PATTERN.search(name):
        return False, f"{field_label} chứa ký tự đặc biệt lạ không hợp lệ!"
    if not VIETNAMESE_NAME_PATTERN.match(name):
        return False, f"{field_label} chỉ được chứa chữ cái tiếng Việt và khoảng trắng, không chứa số hay ký tự lạ!"
    return True, name

def validate_bhyt(bhyt, required=False):
    """Kiem tra rang buoc the BHYT: dung 10 chu so, khong chua chu cai hay ky tu la."""
    bhyt = sanitize_text(bhyt)
    if not bhyt:
        if required:
            return False, "Vui lòng nhập mã số thẻ BHYT!"
        return True, ''
    if any(c.isalpha() for c in bhyt):
        return False, "Mã số thẻ BHYT phải đúng số lượng số và không có chữ!"
    if not BHYT_PATTERN.match(bhyt):
        return False, "Mã số thẻ BHYT phải gồm đúng 10 chữ số, không chứa chữ hay ký tự lạ!"
    if len(set(bhyt)) == 1 and bhyt[0] == '0':
        return False, "Mã số thẻ BHYT không hợp lệ (không thể là chuỗi số 0)!"
    return True, bhyt

def validate_cccd(cccd, required=True):
    """Kiem tra rang buoc CCCD: dung 12 chu so, khong chua chu hay ky tu la."""
    cccd = sanitize_text(cccd)
    if not cccd:
        if required:
            return False, "Vui lòng nhập số Căn cước công dân (CCCD)!"
        return True, ''
    if any(c.isalpha() for c in cccd):
        return False, "Số CCCD phải hoàn toàn là chữ số, không chứa chữ cái!"
    if not CCCD_PATTERN.match(cccd):
        return False, "Số CCCD phải bao gồm đúng 12 chữ số, không chứa chữ hoặc ký tự lạ!"
    if len(set(cccd)) == 1:
        return False, "Số CCCD không hợp lệ (không thể là các chữ số lặp lại)!"
    return True, cccd

def validate_phone(phone, field_label='Số điện thoại', required=True):
    """Kiem tra rang buoc so dien thoai di dong Viet Nam."""
    phone = sanitize_text(phone)
    if not phone:
        if required:
            return False, f"{field_label} không được để trống!"
        return True, ''
    if not VN_PHONE_PATTERN.match(phone):
        return False, f"{field_label} không đúng định dạng (10 số, bắt đầu bằng 03, 05, 07, 08, 09)!"
    return True, phone

def validate_birth_date(birth_date_str, is_staff=False, required=True):
    """Kiem tra rang buoc ngay sinh va do tuoi."""
    birth_date_str = sanitize_text(birth_date_str)
    if not birth_date_str:
        if required:
            return False, "Vui lòng chọn ngày sinh!"
        return True, None
    try:
        ns_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = date.today()
        if ns_date > today:
            return False, "Ngày sinh không thể lớn hơn ngày hiện tại!"
        age = today.year - ns_date.year - ((today.month, today.day) < (ns_date.month, ns_date.day))
        if age > 130:
            return False, "Ngày sinh không hợp lệ (tuổi không vượt quá 130)!"
        if is_staff:
            if age < 18:
                return False, "Nhân sự y tế và bác sĩ phải từ đủ 18 tuổi trở lên!"
            if age > 85:
                return False, "Tuổi nhân sự y tế không vượt quá 85 tuổi!"
        return True, birth_date_str
    except ValueError:
        return False, "Định dạng ngày sinh không hợp lệ (YYYY-MM-DD)!"

def validate_email(email, required=False):
    """Kiem tra rang buoc dia chi email."""
    email = sanitize_text(email)
    if not email:
        if required:
            return False, "Địa chỉ email không được để trống!"
        return True, ''
    if len(email) > 100:
        return False, "Địa chỉ email không vượt quá 100 ký tự!"
    if not EMAIL_PATTERN.match(email):
        return False, "Địa chỉ email không đúng định dạng (ví dụ: h2t@healthcare.vn)!"
    return True, email

def validate_address(address, required=True):
    """Kiem tra rang buoc dia chi cu tru."""
    address = sanitize_text(address)
    if not address:
        if required:
            return False, "Vui lòng nhập địa chỉ chi tiết!"
        return True, ''
    if len(address) < 5 or len(address) > 255:
        return False, "Địa chỉ cư trú phải có độ dài từ 5 đến 255 ký tự!"
    if FORBIDDEN_CHARS_PATTERN.search(address):
        return False, "Địa chỉ chứa ký tự đặc biệt lạ không hợp lệ!"
    return True, address

def validate_vital_signs(data):
    """Kiem tra rang buoc cac chi so sinh ton y khoa lam sang."""
    errors = {}
    try:
        mach = data.get('mach')
        if mach is not None and str(mach).strip():
            mach_val = int(mach)
            if mach_val < 30 or mach_val > 250:
                errors['mach'] = 'Nhịp mạch phải từ 30 đến 250 lần/phút!'
    except (ValueError, TypeError):
        errors['mach'] = 'Nhịp mạch phải là số nguyên hợp lệ!'

    try:
        nhiet_do = data.get('nhiet_do')
        if nhiet_do is not None and str(nhiet_do).strip():
            temp_val = float(nhiet_do)
            if temp_val < 34.0 or temp_val > 43.0:
                errors['nhiet_do'] = 'Thân nhiệt phải trong khoảng 34.0°C đến 43.0°C!'
    except (ValueError, TypeError):
        errors['nhiet_do'] = 'Thân nhiệt phải là số thực hợp lệ!'

    try:
        tam_thu = data.get('huyet_ap_tam_thu')
        tam_truong = data.get('huyet_ap_tam_truong')
        if tam_thu is not None and str(tam_thu).strip() and tam_truong is not None and str(tam_truong).strip():
            thu_val = int(tam_thu)
            truong_val = int(tam_truong)
            if thu_val < 50 or thu_val > 260:
                errors['huyet_ap_tam_thu'] = 'Huyết áp tâm thu phải từ 50 đến 260 mmHg!'
            if truong_val < 30 or truong_val > 150:
                errors['huyet_ap_tam_truong'] = 'Huyết áp tâm trương phải từ 30 đến 150 mmHg!'
            if thu_val <= truong_val:
                errors['huyet_ap'] = 'Huyết áp tâm thu phải lớn hơn huyết áp tâm trương!'
    except (ValueError, TypeError):
        errors['huyet_ap'] = 'Chỉ số huyết áp phải là số nguyên hợp lệ!'

    try:
        nhip_tho = data.get('nhip_tho')
        if nhip_tho is not None and str(nhip_tho).strip():
            nt_val = int(nhip_tho)
            if nt_val < 8 or nt_val > 60:
                errors['nhip_tho'] = 'Nhịp thở phải từ 8 đến 60 lần/phút!'
    except (ValueError, TypeError):
        errors['nhip_tho'] = 'Nhịp thở phải là số nguyên hợp lệ!'

    try:
        spo2 = data.get('spo2')
        if spo2 is not None and str(spo2).strip():
            spo2_val = int(spo2)
            if spo2_val < 50 or spo2_val > 100:
                errors['spo2'] = 'Chỉ số SpO2 phải từ 50% đến 100%!'
    except (ValueError, TypeError):
        errors['spo2'] = 'SpO2 phải là số nguyên hợp lệ!'

    try:
        can_nang = data.get('can_nang')
        if can_nang is not None and str(can_nang).strip():
            cn_val = float(can_nang)
            if cn_val < 0.5 or cn_val > 300.0:
                errors['can_nang'] = 'Cân nặng phải từ 0.5kg đến 300kg!'
    except (ValueError, TypeError):
        errors['can_nang'] = 'Cân nặng phải là số thực hợp lệ!'

    try:
        chieu_cao = data.get('chieu_cao')
        if chieu_cao is not None and str(chieu_cao).strip():
            cc_val = float(chieu_cao)
            if cc_val < 20.0 or cc_val > 250.0:
                errors['chieu_cao'] = 'Chiều cao phải từ 20cm đến 250cm!'
    except (ValueError, TypeError):
        errors['chieu_cao'] = 'Chiều cao phải là số thực hợp lệ!'

    return len(errors) == 0, errors

def validate_medicine_data(data):
    """Kiem tra rang buoc danh muc thuoc va gia ban trong kho duoc."""
    errors = {}
    ten_thuoc = sanitize_text(data.get('ten_thuoc', ''))
    if not ten_thuoc or len(ten_thuoc) < 2:
        errors['ten_thuoc'] = 'Tên thuốc không được để trống và tối thiểu 2 ký tự!'

    try:
        gia_ban = float(data.get('gia_ban', 0))
        if gia_ban <= 0:
            errors['gia_ban'] = 'Giá bán thuốc phải lớn hơn 0 VNĐ!'
    except (ValueError, TypeError):
        errors['gia_ban'] = 'Giá bán phải là số hợp lệ!'

    try:
        ton_kho = int(data.get('so_luong_ton', 0))
        if ton_kho < 0:
            errors['so_luong_ton'] = 'Số lượng tồn kho không được âm!'
    except (ValueError, TypeError):
        errors['so_luong_ton'] = 'Số lượng tồn kho phải là số nguyên!'

    return len(errors) == 0, errors

def validate_service_data(data):
    """Kiem tra rang buoc dich vu kham benh va ty le BHYT."""
    errors = {}
    ten_dv = sanitize_text(data.get('ten_dich_vu', ''))
    if not ten_dv or len(ten_dv) < 3:
        errors['ten_dich_vu'] = 'Tên dịch vụ khám tối thiểu 3 ký tự!'

    try:
        don_gia = float(data.get('don_gia', 0))
        if don_gia < 0:
            errors['don_gia'] = 'Đơn giá dịch vụ không được âm!'
    except (ValueError, TypeError):
        errors['don_gia'] = 'Đơn giá phải là số hợp lệ!'

    try:
        bhyt_pt = float(data.get('bhyt_chi_tra_pt', 0))
        if bhyt_pt < 0 or bhyt_pt > 100:
            errors['bhyt_chi_tra_pt'] = 'Tỷ lệ BHYT chi trả phải từ 0% đến 100%!'
    except (ValueError, TypeError):
        errors['bhyt_chi_tra_pt'] = 'Tỷ lệ BHYT phải là số hợp lệ!'

    return len(errors) == 0, errors

def validate_patient_profile(data):
    """Kiem tra tinh hop le toan dien cua ho so benh nhan."""
    errors = {}

    # 1. Ho va ten
    ok, res = validate_name(data.get('ho_ten', ''), 'Họ và tên')
    if not ok:
        errors['ho_ten'] = res

    # 2. So dien thoai
    sdt = data.get('sdt')
    if sdt:
        ok, res = validate_phone(sdt, 'Số điện thoại', required=False)
        if not ok:
            errors['sdt'] = res

    # 3. Ngay sinh
    ok, res = validate_birth_date(data.get('ngay_sinh', ''), is_staff=False, required=True)
    if not ok:
        errors['ngay_sinh'] = res

    # 4. Gioi tinh
    gioi_tinh = sanitize_text(data.get('gioi_tinh', 'Nam'))
    if gioi_tinh not in ['Nam', 'Nữ']:
        errors['gioi_tinh'] = 'Giới tính phải là Nam hoặc Nữ!'

    # 5. CCCD
    ok, res = validate_cccd(data.get('cccd', ''), required=True)
    if not ok:
        errors['cccd'] = res

    # 6. BHYT (Neu co phai dung 10 so va khong co chu)
    bhyt = data.get('bhyt', '')
    if bhyt and sanitize_text(bhyt):
        ok, res = validate_bhyt(bhyt, required=False)
        if not ok:
            errors['bhyt'] = res

    # 7. Email
    email = data.get('email', '')
    if email and sanitize_text(email):
        ok, res = validate_email(email, required=False)
        if not ok:
            errors['email'] = res

    # 8. Dia chi
    ok, res = validate_address(data.get('dia_chi', ''), required=True)
    if not ok:
        errors['dia_chi'] = res

    # 9. Nguoi than (neu co)
    nguoi_than_ho_ten = data.get('nguoi_than_ho_ten', '')
    if nguoi_than_ho_ten and sanitize_text(nguoi_than_ho_ten):
        ok, res = validate_name(nguoi_than_ho_ten, 'Họ tên người thân')
        if not ok:
            errors['nguoi_than_ho_ten'] = res

    nguoi_than_sdt = data.get('nguoi_than_sdt', '')
    if nguoi_than_sdt and sanitize_text(nguoi_than_sdt):
        ok, res = validate_phone(nguoi_than_sdt, 'Số điện thoại người thân', required=False)
        if not ok:
            errors['nguoi_than_sdt'] = res

    # 10. Kiem tra ky tu doc hai trong cac truong y te tu do
    free_fields = [
        ('di_ung', data.get('di_ung', ''), 'Tiền sử dị ứng'),
        ('tien_su_benh', data.get('tien_su_benh', ''), 'Tiền sử bệnh lý'),
        ('tien_su_gia_dinh', data.get('tien_su_gia_dinh', ''), 'Tiền sử gia đình')
    ]
    for key, val, label in free_fields:
        if val and FORBIDDEN_CHARS_PATTERN.search(str(val)):
            errors[key] = f"{label} chứa ký tự đặc biệt lạ không hợp lệ!"

    return len(errors) == 0, errors
