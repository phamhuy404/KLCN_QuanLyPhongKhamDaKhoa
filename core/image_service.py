import os
import uuid
import re
import io
import base64
import urllib.request
import ssl
from PIL import Image, ImageOps

UPLOAD_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')

CATEGORY_DIRS = {
    'benh_nhan': 'benh_nhan',
    'bac_si': 'bac_si',
    'bai_viet': 'bai_viet',
    'banners': 'banners',
    'can_lam_sang': 'can_lam_sang'
}

DIMENSION_LIMITS = {
    'benh_nhan': (400, 400),
    'bac_si': (500, 500),
    'bai_viet': (1200, 800),
    'banners': (1920, 800),
    'can_lam_sang': (1600, 1200)
}

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'jpe', 'jfif',
    'webp', 'gif', 'bmp', 'tiff', 'tif',
    'ico', 'svg', 'avif', 'heic', 'heif'
}

def ensure_upload_dirs():
    """Tạo sẵn các thư mục con trong static/uploads nếu chưa tồn tại."""
    for folder in CATEGORY_DIRS.values():
        path = os.path.join(UPLOAD_BASE_DIR, folder)
        os.makedirs(path, exist_ok=True)

def is_allowed_image(filename):
    """Kiểm tra phần mở rộng tệp có hợp lệ hay không."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def save_svg(raw_bytes_or_str, category='bai_viet'):
    """Lưu tệp SVG vector an toàn vào thư mục upload."""
    folder = CATEGORY_DIRS.get(category, 'bai_viet')
    target_dir = os.path.join(UPLOAD_BASE_DIR, folder)
    os.makedirs(target_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex[:12]}.svg"
    save_path = os.path.join(target_dir, unique_name)

    if isinstance(raw_bytes_or_str, str):
        content = raw_bytes_or_str.encode('utf-8')
    else:
        content = raw_bytes_or_str

    text_content = content.decode('utf-8', errors='ignore')
    if '<script' in text_content.lower():
        return None, "Tệp SVG chứa mã lệnh không an toàn."

    with open(save_path, 'wb') as f:
        f.write(content)

    return f"/static/uploads/{folder}/{unique_name}", None

def save_and_compress_image(file_storage_or_bytes, category='bai_viet', quality=82, filename=None):
    """
    Nén và lưu hình ảnh đa định dạng (JPG, PNG, WEBP, GIF, BMP, TIFF, SVG) thành WebP siêu nhẹ.
    Hỗ trợ đối tượng FileStorage từ Flask form hoặc chuỗi raw bytes.
    """
    if file_storage_or_bytes is None:
        return None, "Không tìm thấy dữ liệu hình ảnh tải lên."

    orig_name = filename or getattr(file_storage_or_bytes, 'filename', '') or 'image.jpg'
    ext = orig_name.rsplit('.', 1)[-1].lower() if '.' in orig_name else ''

    if hasattr(file_storage_or_bytes, 'read'):
        stream_data = file_storage_or_bytes.read()
    elif isinstance(file_storage_or_bytes, (bytes, bytearray)):
        stream_data = file_storage_or_bytes
    else:
        return None, "Định dạng dữ liệu ảnh không hợp lệ."

    if not stream_data:
        return None, "Tệp hình ảnh rỗng."

    # Xử lý tệp SVG riêng biệt
    if ext == 'svg' or b'<svg' in stream_data[:500].lower():
        return save_svg(stream_data, category=category)

    folder = CATEGORY_DIRS.get(category, 'bai_viet')
    target_dir = os.path.join(UPLOAD_BASE_DIR, folder)
    os.makedirs(target_dir, exist_ok=True)

    try:
        img = Image.open(io.BytesIO(stream_data))

        # Tự động xoay ảnh đúng hướng theo thông tin EXIF của điện thoại/máy ảnh
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Giữ khung hình đầu tiên nếu là ảnh động GIF
        if getattr(img, 'is_animated', False):
            img.seek(0)

        # Xử lý hệ màu cho WebP
        if img.mode in ('RGBA', 'LA'):
            pass
        elif img.mode == 'P':
            img = img.convert('RGBA') if 'transparency' in img.info else img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize ảnh nếu vượt quá kích thước khuyến nghị
        max_w, max_h = DIMENSION_LIMITS.get(category, (1200, 800))
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        # Đặt tên tệp ngẫu nhiên chống trùng lặp
        unique_name = f"{uuid.uuid4().hex[:12]}.webp"
        save_path = os.path.join(target_dir, unique_name)

        # Lưu ảnh dưới định dạng WebP với mức nén tối ưu
        img.save(save_path, format='WEBP', quality=quality, optimize=True)

        web_path = f"/static/uploads/{folder}/{unique_name}"
        return web_path, None
    except Exception as e:
        return None, f"Lỗi xử lý hình ảnh ({orig_name}): {str(e)}"

def save_image_from_url(url, category='bai_viet', quality=82):
    """
    Tải hình ảnh từ URL về máy chủ và nén sang định dạng WebP.
    Nếu ngoại tuyến hoặc tải không thành công, trả về URL an toàn làm fallback.
    """
    if not url or not isinstance(url, str):
        return None, "Đường dẫn URL ảnh không hợp lệ."

    url = url.strip()
    if url.startswith('/static/'):
        return url, None

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) H2T-Healthcare/1.0'}
        )
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            content_type = response.headers.get('Content-Type', '')
            data = response.read()

        if not data:
            return url, None

        ext = 'jpg'
        if 'png' in content_type:
            ext = 'png'
        elif 'webp' in content_type:
            ext = 'webp'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'svg' in content_type or url.lower().endswith('.svg'):
            ext = 'svg'

        web_path, err = save_and_compress_image(data, category=category, quality=quality, filename=f"remote.{ext}")
        if web_path:
            return web_path, None
        return url, None
    except Exception:
        # Fallback an toàn về URL gốc
        return url, None

def save_image_from_base64(data_uri, category='bai_viet', quality=82):
    """
    Nhận diện và giải mã chuỗi Base64 / Data URI (data:image/...) thành ảnh WebP.
    """
    if not data_uri or not isinstance(data_uri, str):
        return None, "Chuỗi base64 không hợp lệ."

    match = re.match(r'^data:image\/([a-zA-Z0-9\+\-\.]+);base64,(.+)$', data_uri.strip())
    if match:
        image_type = match.group(1).lower()
        b64_data = match.group(2)
    else:
        b64_data = data_uri.strip()
        image_type = 'jpg'

    try:
        raw_bytes = base64.b64decode(b64_data)
        if image_type == 'svg+xml' or b'<svg' in raw_bytes[:500].lower():
            return save_svg(raw_bytes, category=category)

        return save_and_compress_image(raw_bytes, category=category, quality=quality, filename=f"image.{image_type}")
    except Exception as e:
        return None, f"Lỗi giải mã ảnh base64: {str(e)}"

def process_image_input(image_input, category='bai_viet', quality=82):
    """
    Nhận diện và xử lý mọi nguồn hình ảnh (FileStorage, URL trực tuyến, Base64 Data URI, đường dẫn tĩnh).
    """
    if not image_input:
        return None, None

    # FileStorage tải lên từ form
    if hasattr(image_input, 'filename'):
        if image_input.filename:
            return save_and_compress_image(image_input, category=category, quality=quality)
        return None, None

    # Chuỗi URL, Data URI hoặc đường dẫn
    if isinstance(image_input, str):
        val = image_input.strip()
        if not val:
            return None, None
        if val.startswith(('http://', 'https://')):
            return save_image_from_url(val, category=category, quality=quality)
        if val.startswith('data:image/'):
            return save_image_from_base64(val, category=category, quality=quality)
        if val.startswith('/static/'):
            return val, None
        return val, None

    # Dạng bytes
    if isinstance(image_input, (bytes, bytearray)):
        return save_and_compress_image(image_input, category=category, quality=quality)

    return None, "Nguồn ảnh không hợp lệ."

def delete_uploaded_image(web_path):
    """Xóa tệp ảnh vật lý trong static/uploads khi bản ghi bị xóa."""
    if not web_path or not web_path.startswith('/static/uploads/'):
        return False
    try:
        rel_path = web_path.replace('/static/uploads/', '').replace('/', os.sep)
        full_path = os.path.join(UPLOAD_BASE_DIR, rel_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception:
        pass
    return False

# Khởi tạo thư mục ngay khi nạp module
ensure_upload_dirs()
