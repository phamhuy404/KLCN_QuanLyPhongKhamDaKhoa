"""Bounded raster uploads; medical files never enter the public static tree."""
import base64
import http.client
import io
import ipaddress
import os
from pathlib import Path
import re
import socket
import ssl
import uuid
import warnings
from urllib.parse import urlsplit

from flask import current_app, has_app_context, has_request_context
from PIL import Image, ImageOps

UPLOAD_BASE_DIR = str(Path(__file__).resolve().parents[1] / 'static' / 'uploads')
PRIVATE_UPLOAD_BASE_DIR = str(Path(__file__).resolve().parents[1] / 'private_uploads')
CATEGORY_DIRS = {name: name for name in
                 ('benh_nhan', 'bac_si', 'bai_viet', 'banners', 'can_lam_sang', 'kham_benh')}
MEDICAL_CATEGORIES = frozenset({'kham_benh', 'can_lam_sang'})
DIMENSION_LIMITS = {'benh_nhan': (400, 400), 'bac_si': (500, 500),
                    'bai_viet': (1200, 800), 'banners': (1920, 800),
                    'can_lam_sang': (1600, 1200), 'kham_benh': (1600, 1200)}
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jpe', 'jfif', 'webp', 'gif',
                      'bmp', 'tiff', 'tif', 'ico', 'avif', 'heic', 'heif'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000


def ensure_upload_dirs():
    # Kept for explicit callers; importing this module creates no directories.
    for category in CATEGORY_DIRS:
        base = PRIVATE_UPLOAD_BASE_DIR if category in MEDICAL_CATEGORIES else UPLOAD_BASE_DIR
        Path(base, category).mkdir(parents=True, exist_ok=True)


def is_allowed_image(filename):
    return bool(filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


def save_svg(raw_bytes_or_str, category='bai_viet'):
    return None, 'SVG uploads are not supported; use a raster image.'


def save_and_compress_image(file_storage_or_bytes, category='bai_viet', quality=82, filename=None):
    if category not in CATEGORY_DIRS:
        return None, 'Unknown image category.'
    original_name = filename or getattr(file_storage_or_bytes, 'filename', '') or 'image.jpg'
    if original_name.lower().endswith(('.svg', '.svgz')):
        return save_svg(None)
    if hasattr(file_storage_or_bytes, 'read'):
        data = file_storage_or_bytes.read(MAX_IMAGE_BYTES + 1)
    elif isinstance(file_storage_or_bytes, (bytes, bytearray)):
        data = file_storage_or_bytes
    else:
        return None, 'Invalid image input.'
    if not data or len(data) > MAX_IMAGE_BYTES:
        return None, 'Image is empty or exceeds the 8 MiB limit.'
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    return None, 'Image exceeds the pixel limit.'
                source.seek(0)
                source.load()
                image = ImageOps.exif_transpose(source)
                image = image.convert('RGBA' if image.mode in ('RGBA', 'LA', 'P') else 'RGB')
                image.thumbnail(DIMENSION_LIMITS[category], Image.Resampling.LANCZOS)
                if category in MEDICAL_CATEGORIES:
                    base = current_app.config['MEDICAL_UPLOAD_DIR'] if has_app_context() else PRIVATE_UPLOAD_BASE_DIR
                    prefix = '/medical-images/'
                else:
                    base, prefix = UPLOAD_BASE_DIR, '/static/uploads/'
                target_dir = Path(base) / category
                target_dir.mkdir(parents=True, exist_ok=True)
                name = uuid.uuid4().hex + '.webp'
                # Exclusive creation never overwrites an existing medical/public file.
                with (target_dir / name).open('xb') as output:
                    from core.emr_workflow import track_new_image
                    track_new_image(target_dir / name)
                    image.save(output, format='WEBP', quality=quality, optimize=True)
        return prefix + category + '/' + name, None
    except (OSError, ValueError, TypeError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        return None, 'Invalid or unsafe raster image.'


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a validated address while retaining hostname/SNI certificate checks."""
    def __init__(self, host, address, context):
        super().__init__(host, port=443, timeout=5, context=context)
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def download_image(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or not parts.hostname or parts.username is not None or parts.password is not None
            or parts.fragment or parts.port not in (None, 443)):
        raise ValueError('Only allowlisted HTTPS image sources on port 443 are accepted.')
    host = parts.hostname.encode('idna').decode('ascii').lower()
    allowed = current_app.config.get('IMAGE_DOWNLOAD_ALLOWED_HOSTS', ()) if has_app_context() else ()
    if isinstance(allowed, str):
        allowed = [item.strip() for item in allowed.split(',') if item.strip()]
    if host not in {item.lower() for item in allowed}:
        raise ValueError('Image source host is not allowlisted.')
    answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addresses = {answer[4][0] for answer in answers}
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError('Private, loopback, reserved and mixed DNS destinations are forbidden.')
    # No proxy or second DNS lookup, and no automatic redirect following.
    context = ssl.create_default_context()
    connection = PinnedHTTPSConnection(host, sorted(addresses)[0], context)
    try:
        target = parts.path or '/'
        if parts.query:
            target += '?' + parts.query
        connection.request('GET', target, headers={'Accept': 'image/*', 'User-Agent': 'ClinicImageImport/1.0'})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError('Image source did not return 200; redirects are not followed.')
        mime = response.getheader('Content-Type', '').split(';')[0].lower().strip()
        if mime not in {'image/jpeg', 'image/png', 'image/webp', 'image/gif',
                        'image/bmp', 'image/tiff', 'image/avif', 'image/x-icon'}:
            raise ValueError('Unsupported image content type.')
        length = response.getheader('Content-Length')
        if length is not None and (int(length) < 0 or int(length) > MAX_IMAGE_BYTES):
            raise ValueError('Image source exceeds the size limit.')
        if response.getheader('Content-Encoding', 'identity').lower() not in ('', 'identity'):
            raise ValueError('Encoded image response is not supported.')
        data = response.read(MAX_IMAGE_BYTES + 1)
        if not data or len(data) > MAX_IMAGE_BYTES:
            raise ValueError('Image source is empty or too large.')
        return data
    finally:
        connection.close()


def save_image_from_url(url, category='bai_viet', quality=82):
    if not isinstance(url, str) or len(url) > 4096 or any(ord(c) < 32 for c in url):
        return None, 'Invalid image URL.'
    try:
        data = download_image(url.strip())
        return save_and_compress_image(data, category, quality)
    except (OSError, ValueError, http.client.HTTPException):
        # Never persist or echo an unvalidated external URL as a fallback.
        return None, 'Unable to import image from the permitted HTTPS source.'


def save_image_from_base64(data_uri, category='bai_viet', quality=82):
    if not isinstance(data_uri, str) or len(data_uri) > ((MAX_IMAGE_BYTES + 2) // 3) * 4 + 128:
        return None, 'Image exceeds the encoded size limit.'
    match = re.fullmatch(r'data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)', data_uri.strip())
    if not match or match.group(1).lower() in ('svg+xml', 'svg'):
        return None, 'Invalid or unsupported image data URI.'
    try:
        data = base64.b64decode(match.group(2), validate=True)
    except ValueError:
        return None, 'Invalid base64 image.'
    return save_and_compress_image(data, category, quality)


def process_image_input(image_input, category='bai_viet', quality=82, patient_id=None):
    if image_input is None or image_input == '':
        return None, None
    if category in MEDICAL_CATEGORIES:
        if not has_request_context() or patient_id is None:
            return None, 'A verified patient context is required for medical images.'
        from core.security import require_patient_access
        require_patient_access(patient_id)
    if hasattr(image_input, 'filename'):
        return save_and_compress_image(image_input, category, quality)
    if isinstance(image_input, (bytes, bytearray)):
        return save_and_compress_image(image_input, category, quality)
    if not isinstance(image_input, str):
        return None, 'Invalid image input.'
    value = image_input.strip()
    if value.startswith(('http://', 'https://')):
        return save_image_from_url(value, category, quality)
    if value.startswith('data:image/'):
        return save_image_from_base64(value, category, quality)
    if category in MEDICAL_CATEGORIES:
        from core.medical_media import media_location, medical_references, can_use_reference, protected_image_value
        if media_location(value) and any(can_use_reference(ref, patient_id) for ref in medical_references(value)):
            return protected_image_value(value), None
        return None, 'The existing medical image does not belong to this patient.'
    # Local public image paths only; arbitrary strings and schemes are never image URLs.
    if value.startswith('/static/') and '%' not in value and chr(92) not in value:
        relative = value[len('/static/'):]
        base = Path(current_app.static_folder) if has_app_context() else Path(UPLOAD_BASE_DIR).parent
        target = (base / relative).resolve()
        if target.is_relative_to(base.resolve()) and target.is_file() and is_allowed_image(target.name):
            return value, None
    return None, 'Invalid or untrusted image source.'


def delete_uploaded_image(web_path):
    # No deletion occurs unless an existing caller explicitly requests it.
    if not isinstance(web_path, str) or not web_path.startswith('/static/uploads/'):
        return False
    try:
        base = Path(UPLOAD_BASE_DIR).resolve()
        target = (base / web_path[len('/static/uploads/'):]).resolve()
        if target.is_relative_to(base) and target.is_file():
            target.unlink()
            return True
    except OSError:
        pass
    return False
