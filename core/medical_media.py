"""Authenticated medical media, with reference-based protection for legacy files."""
import json
import os
import posixpath
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, unquote

from flask import current_app, request, session, abort, send_file
from werkzeug.exceptions import HTTPException
from PIL import Image

from core.database import get_db
from core.security import login_required, require_patient_access, positive_id
from core.clinical_data import result_is_published

PROJECT_DIR = Path(__file__).resolve().parents[1]
MEDICAL_CATEGORIES = frozenset({'kham_benh', 'can_lam_sang'})
RASTER_MIMES = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp',
                'GIF': 'image/gif', 'BMP': 'image/bmp', 'TIFF': 'image/tiff'}


def image_paths(value):
    if isinstance(value, list):
        return [path for path in value if isinstance(path, str)]
    if not isinstance(value, str) or not value.strip():
        return []
    value = value.strip()
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return [value]
    if isinstance(parsed, str):
        return [parsed]
    return [path for path in parsed if isinstance(path, str)] if isinstance(parsed, list) else []


def reference_match(value, location):
    paths = image_paths(value)
    if any(media_location(path) == location for path in paths):
        return 'exact'
    # Unknown absolute/encoded legacy paths must not make the matching local file public.
    # Quarantine them for review rather than granting ownership based on a guessed origin.
    for path in paths:
        try:
            path_only = posixpath.normpath(unquote(urlsplit(path).path).replace('\\', '/'))
            if media_location(path_only) == location:
                return 'quarantine'
            candidate = PurePosixPath(path_only).name
            if os.name == 'nt':
                candidate = candidate.casefold()
            if not media_location(path) and candidate == PurePosixPath(location[1]).name:
                return 'quarantine'
        except ValueError:
            continue
    return None


def media_location(url):
    """Canonical storage location; never accept traversal, URLs, query or fragments."""
    if not isinstance(url, str) or len(url) > 1024 or '\\' in url or '%' in url:
        return None
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        return None
    if url.startswith('/static/uploads/'):
        store, relative = 'legacy', url[len('/static/uploads/'):]
    elif url.startswith('/medical-images/legacy/'):
        store, relative = 'legacy', url[len('/medical-images/legacy/'):]
    elif url.startswith('/medical-images/'):
        store, relative = 'private', url[len('/medical-images/'):]
    else:
        return None
    segments = relative.split('/')
    if len(segments) != 2 or any(not re.fullmatch(r'[A-Za-z0-9_. -]{1,255}', s) or s in ('.', '..') or s.endswith(('.', ' ')) for s in segments):
        return None
    if store == 'private' and segments[0] not in MEDICAL_CATEGORIES:
        return None
    if PurePosixPath(relative).suffix.lower() in ('.svg', '.svgz', '.html', '.htm', '.xml'):
        return None
    return store, relative.casefold() if os.name == 'nt' else relative


def protected_image_value(value):
    converted = []
    for path in image_paths(value):
        location = media_location(path)
        if location:
            store, relative = location
            converted.append('/medical-images/' + ('legacy/' if store == 'legacy' else '') + relative)
    if not converted:
        return None
    if isinstance(value, list):
        return converted
    return json.dumps(converted, ensure_ascii=False) if len(converted) > 1 else converted[0]


def medical_references(url):
    location = media_location(url)
    if not location:
        return []
    filename = PurePosixPath(location[1]).name
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, benh_nhan_id, hinh_anh_kham FROM phieu_kham WHERE hinh_anh_kham LIKE ?', ('%' + filename + '%',))
        references = []
        for row in cursor.fetchall():
            match = reference_match(row.get('hinh_anh_kham'), location)
            if match:
                references.append({'patient_id': row['benh_nhan_id'], 'kind': 'clinical' if match == 'exact' else 'quarantine'})
        cursor.execute('''
            SELECT ct.id, ct.file_ket_qua, ct.trang_thai, pk.benh_nhan_id
            FROM chi_tiet_chi_dinh ct
            JOIN phieu_chi_dinh cd ON cd.id = ct.phieu_chi_dinh_id
            JOIN phieu_kham pk ON pk.id = cd.phieu_kham_id
            WHERE ct.file_ket_qua LIKE ?
        ''', ('%' + filename + '%',))
        for row in cursor.fetchall():
            match = reference_match(row.get('file_ket_qua'), location)
            if match:
                references.append({'patient_id': row['benh_nhan_id'], 'kind': 'lab' if match == 'exact' else 'quarantine', 'trang_thai': row.get('trang_thai')})
        return references
    finally:
        conn.close()


def can_use_reference(reference, expected_patient_id=None):
    if reference['kind'] == 'quarantine':
        return False
    if expected_patient_id is not None and positive_id(reference['patient_id']) != positive_id(expected_patient_id):
        return False
    if session['user']['vai_tro'] == 'BENHNHAN' and reference['kind'] == 'lab' and not result_is_published(reference):
        return False
    try:
        require_patient_access(reference['patient_id'])
    except HTTPException as error:
        if error.code in (403, 404) or error.response is not None and error.response.status_code in (403, 404):
            return False
        raise
    return True


@login_required
def serve_medical_image(relative, legacy=False, references=None):
    url = '/medical-images/' + ('legacy/' if legacy else '') + relative
    location = media_location(url)
    if not location:
        abort(404)
    references = medical_references(url) if references is None else references
    if not references:
        abort(404)
    if session['user']['vai_tro'] == 'BENHNHAN' and any(
            ref['kind'] == 'lab' and positive_id(ref['patient_id']) == positive_id(session['user'].get('patient_id'))
            and not result_is_published(ref) for ref in references):
        # A second clinical reference must not publish the same pending lab image.
        abort(403)
    if not any(can_use_reference(reference) for reference in references):
        abort(403)
    base = Path(current_app.static_folder) / 'uploads' if legacy else Path(current_app.config['MEDICAL_UPLOAD_DIR'])
    base = base.resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        abort(404)
    if target.stat().st_size > 8 * 1024 * 1024:
        abort(413)
    try:
        with Image.open(target) as image:
            if image.width * image.height > 24_000_000:
                abort(413)
            mime = RASTER_MIMES.get(image.format)
            image.verify()
        if not mime:
            abort(415)
    except (OSError, ValueError, Image.DecompressionBombError):
        abort(415)
    response = send_file(target, mimetype=mime, conditional=False, max_age=0)
    response.headers['Cache-Control'] = 'private, no-store, max-age=0'
    response.vary.add('Cookie')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


def register_medical_media(app):
    app.config.setdefault('MEDICAL_UPLOAD_DIR', str(PROJECT_DIR / 'private_uploads'))
    if Path(app.config['MEDICAL_UPLOAD_DIR']).resolve().is_relative_to(Path(app.static_folder).resolve()):
        raise ValueError('MEDICAL_UPLOAD_DIR must be outside the public static directory')
    app.add_url_rule('/medical-images/legacy/<path:relative>', 'legacy_medical_image',
                     lambda relative: serve_medical_image(relative, legacy=True))
    app.add_url_rule('/medical-images/<path:relative>', 'medical_image', serve_medical_image)

    @app.before_request
    def protect_legacy_uploads():
        if request.endpoint != 'static':
            return None
        filename = (request.view_args or {}).get('filename', '')
        normalized = posixpath.normpath(filename.replace('\\', '/').lstrip('/'))
        if not normalized.lower().startswith('uploads/'):
            return None
        relative = normalized[len('uploads/'):]
        url = '/static/uploads/' + relative
        if filename != normalized or not media_location(url):
            abort(404)
        # The old kham_benh category fell back to bai_viet: directory alone is unsafe.
        if relative.split('/')[0] in MEDICAL_CATEGORIES:
            return serve_medical_image(relative, legacy=True)
        try:
            references = medical_references(url)
        except HTTPException:
            raise
        except Exception:
            # Do not expose a possibly clinical legacy upload if classification fails.
            abort(503)
        if references:
            return serve_medical_image(relative, legacy=True, references=references)
        return None
