"""MSSQL integration only; requires separately confirmed disposable test database.
No SQLite, SQL translation or mocked application lock in integration paths.
"""
import io
import json
import re
import shutil
import subprocess
from pathlib import Path
import socket
import ssl
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from PIL import Image
import test_security_access as security_support


class ClinicalMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        security_support.SecurityAccessTests.setUpClass.__func__(cls)
        from core import image_service, medical_media, clinical_data
        cls.images, cls.media, cls.data = image_service, medical_media, clinical_data

    connection = security_support.SecurityAccessTests.connection
    login = security_support.SecurityAccessTests.login
    assert_no_writes = security_support.SecurityAccessTests.assert_no_writes
    tearDown = security_support.SecurityAccessTests.tearDown

    def setUp(self):
        security_support.SecurityAccessTests.setUp(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app.static_folder = str(Path(self.temp.name) / 'static')
        self.app.config['MEDICAL_UPLOAD_DIR'] = str(Path(self.temp.name) / 'private')
        self.app.config['IMAGE_DOWNLOAD_ALLOWED_HOSTS'] = ('images.example.invalid',)
        columns = {'lich_hen_id': 'INT', 'ma_phieu': 'NVARCHAR(MAX)', 'thoi_gian_kham': 'DATETIME2(0)', 'ly_do_kham': 'NVARCHAR(MAX)',
                   'trieu_chung': 'NVARCHAR(MAX)', 'chan_doan_so_bo': 'NVARCHAR(MAX)', 'chan_doan_icd': 'NVARCHAR(MAX)',
                   'huong_dieu_tri': 'NVARCHAR(MAX)', 'loi_dan': 'NVARCHAR(MAX)', 'ngay_tai_kham': 'DATE',
                   'hinh_anh_kham': 'NVARCHAR(MAX)', 'trang_thai': 'NVARCHAR(MAX)'}
        for column, kind in columns.items():
            self.keeper.execute('ALTER TABLE phieu_kham ADD ' + column + ' ' + kind)
        self.keeper.executescript('''
            ALTER TABLE phong_kham ADD ten_phong NVARCHAR(MAX);
            CREATE TABLE chuyen_khoa(id INT, ten_khoa NVARCHAR(MAX));
            CREATE TABLE phieu_chi_dinh(id INT, phieu_kham_id INT, bac_si_id INT, ma_chi_dinh NVARCHAR(MAX));
            CREATE TABLE dich_vu(id INT, ten_dich_vu NVARCHAR(MAX), loai_dich_vu NVARCHAR(MAX));
            CREATE TABLE chi_tiet_chi_dinh(id INT, phieu_chi_dinh_id INT,
                dich_vu_id INT, ket_qua NVARCHAR(MAX), file_ket_qua NVARCHAR(MAX), ktv_thuc_hien NVARCHAR(MAX), trang_thai NVARCHAR(MAX));
            CREATE TABLE don_thuoc(id INT, phieu_kham_id INT, ma_don_thuoc NVARCHAR(MAX),
                trang_thai NVARCHAR(MAX), hinh_thuc_mua NVARCHAR(MAX));
            CREATE TABLE chi_tiet_don_thuoc(don_thuoc_id INT, thuoc_id INT,
                so_luong INT, cach_dung NVARCHAR(MAX));
            CREATE TABLE thuoc(id INT, ten_thuoc NVARCHAR(MAX), hoat_chat NVARCHAR(MAX), don_vi_tinh NVARCHAR(MAX));
            INSERT INTO chuyen_khoa VALUES(10,'Test department');
            INSERT INTO phong_kham VALUES(1,10,'Test room');
            INSERT INTO dich_vu VALUES(1,'Approved blank fixture','Test');
            INSERT INTO dich_vu VALUES(2,'PENDING_SECRET','Test');
            INSERT INTO dich_vu VALUES(3,'OTHER_OWNER_SECRET','Test');
        ''')
        self.legacy = '/static/uploads/bai_viet/clinical.webp'
        self.new = '/medical-images/kham_benh/new.webp'
        self.lab = '/static/uploads/can_lam_sang/approved.webp'
        self.pending = '/static/uploads/can_lam_sang/pending.webp'
        self.keeper.execute('''INSERT INTO phieu_kham(id,benh_nhan_id,bac_si_id,phong_kham_id,
            ma_phieu,thoi_gian_kham,hinh_anh_kham,trang_thai) VALUES(201,101,203,1,?,?,?,?)''',
            ('TEST201', '2030-01-01 09:00', json.dumps([self.legacy, self.new]), 'Chờ kết quả CLS'))
        self.keeper.execute('INSERT INTO phieu_kham(id,benh_nhan_id) VALUES(202,102)')
        self.keeper.executemany('INSERT INTO phieu_chi_dinh VALUES(?,?,?,?)',
                                [(401, 201, 203, 'T401'), (402, 202, 203, 'T402')])
        self.keeper.executemany('INSERT INTO chi_tiet_chi_dinh VALUES(?,?,?,?,?,?,?)', [
            (301, 401, 1, None, self.lab, None, 'Đã duyệt'),
            (302, 401, 2, 'PENDING_SECRET', self.pending, None, 'Chờ duyệt'),
            (303, 402, 3, 'OTHER_OWNER_SECRET', None, None, 'Đã duyệt')])
        self.keeper.commit()
        self.image_bytes = self.raster()
        for path in (self.legacy, self.new, self.lab, self.pending):
            store, relative = self.media.media_location(path)
            base = Path(self.app.static_folder) / 'uploads' if store == 'legacy' else Path(self.app.config['MEDICAL_UPLOAD_DIR'])
            target = base / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.image_bytes)

    @staticmethod
    def raster(size=(8, 8)):
        stream = io.BytesIO()
        Image.new('RGB', size, 'white').save(stream, format='PNG')
        return stream.getvalue()

    def test_null_vitals_remain_null_and_zero_is_preserved(self):
        self.keeper.execute('INSERT INTO chi_so_sinh_ton(benh_nhan_id,mach) VALUES(101,?)', ('0',))
        self.keeper.commit()
        with self.app.app_context():
            for records in (self.patients.get_all(), self.patients.get_by_department(10),
                            [self.patients.get_by_id(101)]):
                patient = next(row for row in records if row['id'] == 101)
                self.assertEqual(patient['vitals']['mach'], '0')
                self.assertIsNone(patient['vitals']['nhiet_do'])
                self.assertIsNone(patient['vitals']['bmi'])
                self.assertIsNone(patient['tuoi'])
        self.assertEqual(self.data.display_clinical(0), 0)
        self.assertEqual(self.data.display_clinical('  '), 'Chưa có dữ liệu')

    def test_website_and_api_publish_only_approved_result(self):
        self.login(1)
        for path in ('/patient/lab-results', '/patient/records'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertNotIn('PENDING_SECRET', html)
            self.assertNotIn('OTHER_OWNER_SECRET', html)
            self.assertNotIn('Bình thường trong giới hạn tham chiếu', html)
        html = self.client.get('/patient/lab-results').get_data(as_text=True)
        self.assertIn('Chưa có dữ liệu', html)
        self.assertIn('/medical-images/legacy/can_lam_sang/approved.webp', html)
        self.assertEqual(self.client.get('/api/lab/result/view/302').status_code, 403)
        response = self.client.get('/api/lab/result/view/301')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json['item']['ket_qua'])
        self.assertTrue(response.json['item']['file_ket_qua'].startswith('/medical-images/'))
        self.assertEqual(self.client.get('/api/lab/result/view/303').status_code, 403)
        self.assert_no_writes()

    def test_patient_history_filters_unapproved_but_staff_can_review(self):
        with self.app.test_request_context():
            from flask import session
            session['user'] = {'vai_tro': 'BENHNHAN'}
            history = self.patients.get_patient_history(101)
            self.assertEqual([r['chi_tiet_id'] for r in history[0]['can_lam_sang']], [301])
        with self.app.app_context():
            history = self.patients.get_patient_history(101, approved_only=False)
            self.assertEqual({r['chi_tiet_id'] for r in history[0]['can_lam_sang']}, {301, 302})
            rows, stats = self.patients.get_all_lab_results(101)
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0]['ket_qua'])
            self.assertEqual(stats['da_co_ket_qua'], 0)

    def test_admin_profile_does_not_claim_normal_or_fabricate_timestamp(self):
        self.login(7)
        response = self.client.get('/admin/patients/101')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Chưa đo', html)
        self.assertNotIn('20/09/2026 08:15', html)
        self.assertNotIn('>Bình thường</span>', html)
        self.assertNotIn('>Ổn định</span>', html)

    def test_anonymous_cannot_read_new_or_legacy_medical_images(self):
        for path in (self.new, self.legacy, self.lab, self.pending,
                     '/medical-images/legacy/bai_viet/clinical.webp'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertNotEqual(response.data, self.image_bytes)
        self.assert_no_writes()

    def test_image_owner_other_and_unapproved_result(self):
        self.login(1)
        for path in (self.new, self.legacy, self.lab, '/medical-images/legacy/bai_viet/clinical.webp'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, self.image_bytes)
                self.assertIn('no-store', response.headers['Cache-Control'])
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                response.close()
        self.assertEqual(self.client.get(self.pending).status_code, 403)
        self.login(2)
        self.assertEqual(self.client.get(self.new).status_code, 403)
        self.assertEqual(self.client.get(self.legacy).status_code, 403)
        self.login(7)
        response = self.client.get(self.pending)
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_public_image_unchanged_and_legacy_files_not_moved(self):
        public = Path(self.app.static_folder) / 'uploads' / 'bai_viet' / 'public.webp'
        public.write_bytes(self.image_bytes)
        response = self.client.get('/static/uploads/bai_viet/public.webp')
        self.assertEqual(response.status_code, 200)
        response.close()
        self.login(1)
        self.client.get(self.legacy).close()
        self.assertEqual((Path(self.app.static_folder) / 'uploads/bai_viet/clinical.webp').read_bytes(), self.image_bytes)

    def test_static_aliases_traversal_and_svg_are_not_bypasses(self):
        for path in ('/static/a/../uploads/bai_viet/clinical.webp',
                     '/static/uploads/bai_viet/clinical.webp.',
                     '/static/uploads/BAI_V~1/clinic~1.webp',
                     '/medical-images/kham_benh/../new.webp',
                     '/medical-images/legacy/bai_viet/unsafe.svg'):
            with self.subTest(path=path):
                self.assertNotEqual(self.client.get(path).status_code, 200)
        if self.media.os.name == 'nt':
            self.assertEqual(self.client.get('/static/UPLOADS/BAI_VIET/CLINICAL.WEBP').status_code, 302)

    def test_missing_reference_is_not_a_public_private_file(self):
        target = Path(self.app.config['MEDICAL_UPLOAD_DIR']) / 'kham_benh' / 'orphan.webp'
        target.write_bytes(self.image_bytes)
        self.login(1)
        self.assertEqual(self.client.get('/medical-images/kham_benh/orphan.webp').status_code, 404)

    def test_absolute_legacy_reference_is_quarantined_instead_of_public(self):
        self.keeper.execute('UPDATE phieu_kham SET hinh_anh_kham=? WHERE id=201',
                            ('https://old.example.invalid' + self.legacy + '?old=1',))
        self.keeper.commit()
        self.assertEqual(self.client.get(self.legacy).status_code, 302)
        self.login(1)
        self.assertEqual(self.client.get(self.legacy).status_code, 403)

    def test_pending_lab_image_cannot_be_published_by_second_clinical_reference(self):
        self.keeper.execute('UPDATE phieu_kham SET hinh_anh_kham=? WHERE id=201', (self.pending,))
        self.keeper.commit()
        self.login(1)
        self.assertEqual(self.client.get(self.pending).status_code, 403)

    def test_clinical_upload_private_and_existing_reference_bound_to_patient(self):
        with self.app.app_context():
            path, error = self.images.save_and_compress_image(self.image_bytes, 'kham_benh')
        self.assertIsNone(error)
        self.assertTrue(path.startswith('/medical-images/kham_benh/'))
        self.assertTrue((Path(self.app.config['MEDICAL_UPLOAD_DIR']) / path[len('/medical-images/'):]).is_file())
        with self.app.test_request_context():
            from flask import session
            session['logged_in'] = True
            session['user'] = {'id': 7}
            path, error = self.images.process_image_input(self.legacy, 'kham_benh', patient_id=102)
            self.assertIsNone(path)
            self.assertTrue(error)

    def test_image_limits_svg_and_arbitrary_strings_are_rejected(self):
        with self.app.app_context(), patch.object(self.images, 'UPLOAD_BASE_DIR', self.temp.name):
            for data in (b'<svg onload="alert(1)"></svg>', b'not an image', b''):
                self.assertIsNone(self.images.save_and_compress_image(data)[0])
            self.assertIsNone(self.images.save_svg('<svg/>')[0])
            with patch.object(self.images, 'MAX_IMAGE_BYTES', 10):
                self.assertIsNone(self.images.save_and_compress_image(self.image_bytes)[0])
                self.assertIsNone(self.images.save_image_from_base64('data:image/png;base64,' + 'A' * 500)[0])
            with patch.object(self.images, 'MAX_IMAGE_PIXELS', 1):
                self.assertIsNone(self.images.save_and_compress_image(self.image_bytes)[0])
            for value in ('javascript:alert(1)', 'file:///etc/passwd', '//localhost/test', '/static/../../secret.png'):
                self.assertIsNone(self.images.process_image_input(value)[0])

    def test_remote_import_blocks_private_dns_redirects_size_and_no_url_fallback(self):
        public_dns = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]
        with self.app.app_context(), patch.object(socket, 'create_connection', side_effect=AssertionError('Network forbidden')) as connect:
            for url in ('http://images.example.invalid/x', 'https://localhost/x', 'file:///x',
                        'https://user:password@images.example.invalid/x', 'https://images.example.invalid:8443/x'):
                self.assertIsNone(self.images.save_image_from_url(url)[0])
            for ip in ('127.0.0.1', '10.0.0.1', '169.254.169.254', '::1'):
                with patch.object(socket, 'getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 443))]):
                    self.assertIsNone(self.images.save_image_from_url('https://images.example.invalid/x')[0])
            connect.assert_not_called()
            for status, headers in ((302, {}), (200, {'Content-Type': 'image/svg+xml'}),
                                    (200, {'Content-Type': 'image/png', 'Content-Length': '999999999'})):
                response = Mock(status=status)
                response.getheader.side_effect = lambda key, default=None: headers.get(key, default)
                with patch.object(socket, 'getaddrinfo', return_value=public_dns), patch.object(self.images, 'PinnedHTTPSConnection') as connection:
                    connection.return_value.getresponse.return_value = response
                    self.assertIsNone(self.images.save_image_from_url('https://images.example.invalid/x')[0])
                    response.read.assert_not_called()

    def test_pinned_https_uses_verified_tls_and_original_hostname(self):
        context = ssl.create_default_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        fake_context = Mock()
        with patch.object(socket, 'create_connection') as connect:
            connection = self.images.PinnedHTTPSConnection('images.example.invalid', '8.8.8.8', fake_context)
            connection.connect()
            connect.assert_called_once_with(('8.8.8.8', 443), timeout=5)
            fake_context.wrap_socket.assert_called_once_with(connect.return_value, server_hostname='images.example.invalid')

    def test_valid_remote_download_bounded_and_certificate_error_has_no_fallback(self):
        dns = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]
        response = Mock(status=200)
        response.getheader.side_effect = lambda key, default=None: {'Content-Type': 'image/png'}.get(key, default)
        response.read.return_value = self.image_bytes
        with self.app.app_context(), patch.object(socket, 'getaddrinfo', return_value=dns), patch.object(
                self.images, 'PinnedHTTPSConnection') as connection:
            connection.return_value.getresponse.return_value = response
            self.assertEqual(self.images.download_image('https://images.example.invalid/image'), self.image_bytes)
            response.read.assert_called_once_with(self.images.MAX_IMAGE_BYTES + 1)
            context = connection.call_args.args[2]
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            connection.return_value.close.assert_called_once()
        with self.app.app_context(), patch.object(socket, 'getaddrinfo', return_value=dns), patch.object(
                self.images, 'PinnedHTTPSConnection', side_effect=ssl.SSLCertVerificationError('bad certificate')):
            self.assertIsNone(self.images.save_image_from_url('https://images.example.invalid/image')[0])

    def test_real_http_lab_page_api_image_and_revocation(self):
        from urllib.request import build_opener, ProxyHandler, HTTPCookieProcessor, HTTPRedirectHandler
        from urllib.parse import urlencode
        from urllib.error import HTTPError
        from http.cookiejar import CookieJar
        from werkzeug.serving import make_server
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        server = make_server('127.0.0.1', 0, self.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        self.start_test_thread(thread)
        try:
            http = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()), NoRedirect())
            base = 'http://127.0.0.1:' + str(server.server_port)
            with self.assertRaises(HTTPError) as blocked:
                http.open(base + self.legacy, timeout=5)
            self.assertEqual(blocked.exception.code, 302)
            blocked.exception.close()
            credentials = urlencode({'username': 'fixture_1', 'password': 'IsolatedPassword123!'}).encode()
            with self.assertRaises(HTTPError) as logged_in:
                http.open(base + '/login', data=credentials, timeout=5)
            self.assertEqual(logged_in.exception.code, 302)
            logged_in.exception.close()
            with http.open(base + '/patient/lab-results', timeout=5) as response:
                html = response.read().decode()
                self.assertNotIn('PENDING_SECRET', html)
                self.assertIn('Chưa có dữ liệu', html)
            with http.open(base + '/api/lab/result/view/301', timeout=5) as response:
                item = json.load(response)['item']
                self.assertIsNone(item['ket_qua'])
            with http.open(base + item['file_ket_qua'], timeout=5) as response:
                self.assertEqual(response.read(), self.image_bytes)
                self.assertIn('no-store', response.headers['Cache-Control'])
            # Revoke publication in this test DB; cached prior authorization must not survive.
            self.keeper.execute('UPDATE chi_tiet_chi_dinh SET trang_thai=? WHERE id=301', ('Chờ duyệt',))
            self.keeper.commit()
            with self.assertRaises(HTTPError) as revoked:
                http.open(base + item['file_ket_qua'], timeout=5)
            self.assertEqual(revoked.exception.code, 403)
            revoked.exception.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_invalid_image_or_blank_diagnosis_never_reaches_medical_write(self):
        from models.medical_record_model import MedicalRecordModel
        self.login(7)
        with patch.object(MedicalRecordModel, 'update_lab_result') as update:
            response = self.client.post('/api/lab/result/save', json={
                'chi_tiet_id': 302, 'ket_qua': 'Test result', 'images': ['file:///private/image']})
            self.assertEqual(response.status_code, 400)
            update.assert_not_called()
        with patch.object(MedicalRecordModel, 'save_examination') as save:
            response = self.client.post('/api/emr/save', json={'patient_id': 101})
            self.assertEqual(response.status_code, 400)
            save.assert_not_called()
        self.assert_no_writes()

    def test_rendered_template_scripts_have_valid_syntax(self):
        node = shutil.which('node')
        if node is None:
            self.skipTest('Node is unavailable for frontend syntax checking')
        from flask import render_template, session
        with self.app.test_request_context():
            session['user'] = {'id': 7, 'vai_tro': 'ADMIN'}
            patient = self.patients.get_by_id(101)
            pages = [
                render_template('admin/emr.html', patients=[patient], medicines=[], services=[], doctors=[], catalogs={}),
                render_template('admin/patient_detail.html', patient=patient),
                render_template('patient/lab_results.html', patient=patient, all_cls=[], cls_stats={}),
            ]
        for page_index, html in enumerate(pages):
            for script_index, (attrs, source) in enumerate(re.findall(r'<script\b([^>]*)>(.*?)</script>', html, flags=re.S)):
                if 'src=' in attrs or 'application/json' in attrs or not source.strip():
                    continue
                target = Path(self.temp.name) / f'page_{page_index}_{script_index}.js'
                target.write_text(source, encoding='utf-8')
                with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as output:
                    result = subprocess.run([node, '--check', str(target)], stdout=output, stderr=output, timeout=10)
                    output.seek(0)
                    self.assertEqual(result.returncode, 0, output.read())


if __name__ == '__main__':
    unittest.main()
