import os

CATALOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'catalogs')

def load_catalog_file(filename):
    """Đọc file danh mục .txt UTF-8 và trả về danh sách các giá trị."""
    filepath = os.path.join(CATALOG_DIR, filename)
    if not os.path.exists(filepath):
        return []
    items = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            item = line.strip()
            if item and not item.startswith('#'):
                items.append(item)
    return items

def get_blood_types():
    """Lấy danh mục nhóm máu chuẩn."""
    return load_catalog_file('nhom_mau.txt')

def get_allergies():
    """Lấy danh mục dị ứng phổ biến."""
    return load_catalog_file('di_ung.txt')

def get_medical_histories():
    """Lấy danh mục tiền sử bệnh lý nền."""
    return load_catalog_file('tien_su_benh.txt')

def get_blood_variants():
    """Lấy danh mục biến thể nhóm máu và kháng thể bất thường phổ biến."""
    return load_catalog_file('bien_the_nhom_mau.txt')

def get_all_catalogs():
    """Lấy toàn bộ các danh mục y tế phục vụ giao diện."""
    return {
        'nhom_mau': get_blood_types(),
        'bien_the_nhom_mau': get_blood_variants(),
        'di_ung': get_allergies(),
        'tien_su_benh': get_medical_histories()
    }

