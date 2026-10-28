"""Sequential model/API integration on verified SQLite RAM only.

The adapter MOCKS SQL Server applock and translates a few T-SQL constructs.
These tests do NOT establish SQL Server locking/concurrency correctness.
Run explicitly; never discover the legacy database tests.
"""
from datetime import date, timedelta
import re
import sqlite3
import unittest
from unittest.mock import patch
import json
import threading
from http.cookiejar import CookieJar
from urllib.request import build_opener, ProxyHandler, HTTPCookieProcessor, Request, HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError

from tests import test_security_access as support


class CalendarCursor(sqlite3.Cursor):
    def execute(self, sql, parameters=()):
        if 'sys.sp_getapplock' in sql:
            self.connection.lock_calls += 1
            assert "@LockOwner = 'Transaction'" in sql
            assert "@LockMode = 'Exclusive'" in sql
            sql, parameters = 'SELECT 0 AS calendar_lock_result', ()
        elif sql.strip() == 'SELECT @@IDENTITY':
            sql = 'SELECT last_insert_rowid()'
        sql = re.sub(r"\bN'", "'", sql)
        sql = re.sub(r'TRY_CAST\(\? AS INT\)', 'CAST(? AS INTEGER)', sql, flags=re.I)
        sql = sql.replace('GETDATE()', 'CURRENT_TIMESTAMP')
        sql = re.sub(r'WITH\s*\(NOLOCK\)', '', sql, flags=re.I)
        sql = sql.replace('CAST(CURRENT_TIMESTAMP AS DATE)', "date('now')")
        sql = sql.replace('CAST(CURRENT_TIMESTAMP AS TIME)', "time('now')")
        if re.match(r'\s*SELECT\s+TOP\s+1\b', sql, flags=re.I):
            sql = re.sub(r'\bSELECT\s+TOP\s+1\b', 'SELECT', sql, count=1, flags=re.I)
            sql = sql.rstrip().rstrip(';') + ' LIMIT 1'
        return super().execute(sql, parameters)


class CalendarConnection(sqlite3.Connection):
    lock_calls = 0

    def cursor(self):
        return super().cursor(factory=CalendarCursor)


class SchedulingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        support.SecurityAccessTests.setUpClass.__func__(cls)
        from models.appointment_model import AppointmentModel
        from models.schedule_model import ScheduleModel
        cls.appointments, cls.schedules = AppointmentModel, ScheduleModel

    login = support.SecurityAccessTests.login
    tearDown = support.SecurityAccessTests.tearDown

    def connection(self):
        conn = sqlite3.connect(self.uri, uri=True, factory=CalendarConnection)
        conn.row_factory = sqlite3.Row
        assert all(row[2] == '' for row in conn.execute('PRAGMA database_list'))
        conn.set_trace_callback(self.statements.append)
        self.connections.append(conn)
        return self.db_module.UnifiedConnection(conn)

    def setUp(self):
        self.connections = []
        support.SecurityAccessTests.setUp(self)
        self.keeper.executescript('''
            DROP TABLE lich_hen;
            DROP TABLE phong_kham;
            CREATE TABLE phong_kham(id INTEGER PRIMARY KEY,chuyen_khoa_id INTEGER,ten_phong TEXT,trang_thai INTEGER);
            INSERT INTO phong_kham VALUES(1,10,'Morning',1),(2,10,'Afternoon',1),(3,20,'Other department',1);
            CREATE TABLE chuyen_khoa(id INTEGER PRIMARY KEY,ten_khoa TEXT,trang_thai INTEGER);
            INSERT INTO chuyen_khoa VALUES(10,'Department',1),(20,'Other',1);
            ALTER TABLE bac_si ADD COLUMN trang_thai_lam_viec TEXT DEFAULT 'Đang làm việc';
            ALTER TABLE bac_si ADD COLUMN phong_kham_chinh_id INTEGER DEFAULT 3;
            ALTER TABLE bac_si ADD COLUMN kinh_nghiem INTEGER;
            ALTER TABLE bac_si ADD COLUMN avatar TEXT;
            ALTER TABLE bac_si ADD COLUMN gia_kham REAL;
            CREATE TABLE lich_lam_viec(id INTEGER PRIMARY KEY AUTOINCREMENT,
                nhan_vien_id INTEGER,bac_si_id INTEGER,phong_kham_id INTEGER,ngay_lam TEXT,ca_lam INTEGER,
                gio_bat_dau TEXT,gio_ket_thuc TEXT,so_luong_kham_toi_da INTEGER,so_luong_da_dang_ky INTEGER,
                trang_thai INTEGER,trang_thai_duyet TEXT,nguoi_duyet_id INTEGER,ngay_duyet TEXT,ghi_chu TEXT);
            CREATE TABLE lich_hen(id INTEGER PRIMARY KEY AUTOINCREMENT,ma_lich_hen TEXT UNIQUE,
                benh_nhan_id INTEGER,bac_si_id INTEGER,chuyen_khoa_id INTEGER,phong_kham_id INTEGER,
                ngay_hen TEXT,gio_hen TEXT,ly_do_kham TEXT,trang_thai TEXT,ngay_dat TEXT);
            CREATE TABLE thong_bao(id INTEGER PRIMARY KEY,tai_khoan_id INTEGER,tieu_de TEXT,noi_dung TEXT,
                loai_thong_bao TEXT,lien_ket TEXT,da_doc INTEGER,thoi_gian_tao TEXT);
            CREATE TABLE audit_log(id INTEGER PRIMARY KEY,table_name TEXT,row_id INTEGER,action TEXT,
                performed_by INTEGER,performed_by_name TEXT,performed_at TEXT,reason TEXT,before_json TEXT,after_json TEXT);
            CREATE TABLE hoa_don(id INTEGER,benh_nhan_id INTEGER,trang_thai TEXT,phieu_kham_id INTEGER);
            ALTER TABLE phieu_kham ADD COLUMN lich_hen_id INTEGER;
            CREATE TABLE chi_tiet_hoa_don(hoa_don_id INTEGER,loai_khoan_thu TEXT,tham_chieu_id INTEGER);
        ''')
        self.day = (date.today()+timedelta(days=14)).isoformat()
        self.staff = {'id':7,'vai_tro':'ADMIN'}
        self.patient = {'id':1,'vai_tro':'BENHNHAN','patient_id':101}
        for column in ('ma_phieu','thoi_gian_kham','ly_do_kham','trieu_chung','chan_doan_so_bo',
                       'chan_doan_icd','huong_dieu_tri','loi_dan','ngay_tai_kham','hinh_anh_kham','trang_thai'):
            self.keeper.execute('ALTER TABLE phieu_kham ADD COLUMN '+column+' TEXT')
        self.keeper.commit()

    def schedule(self, shift=1, room=1, capacity=2):
        with self.app.app_context():
            result = self.schedules.create_schedule(203,room,self.day,shift,so_luong_kham_toi_da=capacity)
        self.assertTrue(result[0],result)
        return result[1]

    def book(self, patient=101, when='08:00', doctor=203, department=10):
        with self.app.app_context():
            return self.appointments.create(patient,department,doctor,self.day,when,'Test appointment',self.patient)

    def row(self):
        return dict(self.keeper.execute('SELECT * FROM lich_hen ORDER BY id LIMIT 1').fetchone())

    def counts(self):
        return [row[0] for row in self.keeper.execute('SELECT so_luong_da_dang_ky FROM lich_lam_viec ORDER BY id')]

    def test_create_and_update_share_invalid_input_validation(self):
        identifier = self.schedule()
        cases = [(self.day,0,2),(self.day,4,2),(self.day,1,0),(self.day,1,-1),
                 (self.day,1,1.5),(self.day,True,2),('2000-01-01',1,2)]
        for day,shift,capacity in cases:
            with self.subTest(day=day,shift=shift,capacity=capacity), self.app.app_context():
                self.assertFalse(self.schedules.create_schedule(203,2,day,shift,so_luong_kham_toi_da=capacity)[0])
                self.assertFalse(self.schedules.update_schedule(identifier,203,1,day,shift,so_luong_kham_toi_da=capacity)[0])

    def test_room_department_staff_overlap_and_time_bounds(self):
        identifier = self.schedule()
        with self.app.app_context():
            self.assertFalse(self.schedules.create_schedule(203,2,self.day,1)[0])
            self.assertFalse(self.schedules.create_schedule(203,3,self.day,2)[0])
            self.assertFalse(self.schedules.update_schedule(identifier,203,3,self.day,1)[0])
            self.assertFalse(self.schedules.update_schedule(identifier,203,1,self.day,1,'06:00','12:00')[0])
            self.assertFalse(self.schedules.create_schedule(203,2,self.day,2,nhan_vien_id=306)[0])
        self.keeper.execute('INSERT INTO tai_khoan(id,vai_tro_id,trang_thai) VALUES(99,3,1)')
        self.keeper.execute('INSERT INTO nhan_vien(id,tai_khoan_id,trang_thai) VALUES(999,99,1)')
        self.keeper.execute("INSERT INTO bac_si(id,nhan_vien_id,chuyen_khoa_id) VALUES(299,999,10)")
        self.keeper.commit()
        with self.app.app_context():
            self.assertFalse(self.schedules.create_schedule(299,1,self.day,1)[0])

    def test_no_schedule_pending_inactive_wrong_department_and_outside_hours(self):
        self.assertFalse(self.book()[0])
        self.schedule()
        for value in ('06:59','11:30','12:00','13:00','17:00','21:00','bad','25:00',None):
            with self.subTest(value=value):
                self.assertFalse(self.book(when=value)[0])
                self.assertIsNone(self.appointments.get_shift_from_time(value))
        self.assertFalse(self.book(department=20)[0])
        for field,value in [('trang_thai_duyet','CHO_DUYET'),('trang_thai_duyet',None),('trang_thai',0)]:
            self.keeper.execute('UPDATE lich_lam_viec SET '+field+'=?',(value,))
            self.keeper.commit()
            self.assertFalse(self.book()[0])
            self.keeper.execute("UPDATE lich_lam_viec SET trang_thai=1,trang_thai_duyet='DA_DUYET'")
            self.keeper.commit()

    def test_duplicate_patient_doctor_capacity_and_auto_assignment(self):
        self.schedule(capacity=1)
        self.assertTrue(self.book(doctor=None)[0])
        self.assertEqual(self.row()['phong_kham_id'],1)  # not doctor's default room 3
        self.assertFalse(self.book(patient=102,when='08:00')[0])
        self.assertFalse(self.book(patient=102,when='09:00')[0])
        self.assertFalse(self.book(when='08:15')[0])
        self.assertEqual(self.counts(),[1])

    def test_same_shift_move_and_cross_shift_room_and_cancel_once(self):
        self.schedule(capacity=1)
        self.schedule(2,2,1)
        self.assertTrue(self.book()[0])
        identifier = self.row()['id']
        with self.app.app_context():
            result = self.appointments.reschedule(identifier,self.day,'09:00',user_info=self.patient)
            self.assertTrue(result[0],result)
            self.assertEqual(self.counts(),[1,0])
            result = self.appointments.reschedule(identifier,self.day,'14:00',user_info=self.patient)
            self.assertTrue(result[0],result)
            self.assertEqual(self.counts(),[0,1])
            self.assertEqual(self.row()['phong_kham_id'],2)
            self.assertTrue(self.appointments.cancel(identifier,user_info=self.patient)[0])
            self.assertFalse(self.appointments.cancel(identifier,user_info=self.patient)[0])
            self.assertEqual(self.counts(),[0,0])

    def test_reschedule_conflict_full_pending_and_capacity_reduction_rollback(self):
        first = self.schedule()
        self.schedule(2,2,1)
        self.assertTrue(self.book()[0])
        self.assertTrue(self.book(patient=102,when='14:00')[0])
        identifier = self.row()['id']
        with self.app.app_context():
            for when in ('14:00','15:00','12:00'):
                self.assertFalse(self.appointments.reschedule(identifier,self.day,when,user_info=self.patient)[0])
            self.assertFalse(self.schedules.update_schedule(first,203,1,self.day,1,so_luong_kham_toi_da=0)[0])
            self.assertFalse(self.schedules.update_schedule(first,203,2,self.day,1)[0])
            self.assertFalse(self.schedules.toggle_status(first)[0])
            self.assertFalse(self.schedules.delete_schedule(first,self.staff)[0])
            self.assertEqual(self.counts(),[1,1])
            self.assertEqual(self.row()['gio_hen'],'08:00')

    def test_commit_failure_rolls_back_booking_counter_notifications_and_audit(self):
        self.schedule()
        with patch.object(self.db_module.UnifiedConnection,'commit',side_effect=RuntimeError('test commit failure')):
            result = self.book()
        self.assertFalse(result[0],result)
        for table in ('lich_hen','thong_bao','audit_log'):
            self.assertEqual(self.keeper.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        self.assertEqual(self.counts(),[0])

    def test_swallowed_audit_sql_error_still_aborts_booking_transaction(self):
        self.schedule()
        self.keeper.execute('DROP TABLE audit_log')
        self.keeper.commit()
        self.assertFalse(self.book()[0])
        self.assertEqual(self.counts(),[0])
        self.assertEqual(self.keeper.execute('SELECT count(*) FROM lich_hen').fetchone()[0],0)

    def test_ambiguous_legacy_shift_fails_closed(self):
        self.schedule()
        self.keeper.execute('''INSERT INTO lich_lam_viec(nhan_vien_id,bac_si_id,phong_kham_id,ngay_lam,ca_lam,
            gio_bat_dau,gio_ket_thuc,so_luong_kham_toi_da,trang_thai,trang_thai_duyet)
            SELECT nhan_vien_id,bac_si_id,phong_kham_id,ngay_lam,ca_lam,gio_bat_dau,gio_ket_thuc,
            so_luong_kham_toi_da,trang_thai,trang_thai_duyet FROM lich_lam_viec''')
        self.keeper.commit()
        self.assertFalse(self.book()[0])

    def test_api_real_model_book_move_cancel_and_memory_database(self):
        self.schedule()
        self.schedule(2,2)
        self.login()
        response = self.client.post('/api/appointment/book',json={'chuyen_khoa_id':10,'bac_si_id':203,
                                  'ngay_hen':self.day,'gio_hen':'08:00'})
        self.assertEqual(response.status_code,200,response.json)
        identifier = self.row()['id']
        response = self.client.post('/api/appointment/reschedule',json={'id':identifier,'ngay_hen':self.day,'gio_hen':'14:00'})
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(self.row()['phong_kham_id'],2)
        response = self.client.post('/api/appointment/cancel',json={'id':identifier})
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(self.counts(),[0,0])
        self.assertTrue(any(connection.lock_calls for connection in self.connections))

    def test_availability_no_shift_pending_custom_hours_and_full(self):
        with self.app.app_context():
            empty = self.appointments.get_time_slots_status(self.day,10,203)
            self.assertFalse(any(item['selectable'] for shift in empty['shifts'] for item in shift['slots']))
        self.schedule(capacity=1)
        self.keeper.execute("UPDATE lich_lam_viec SET gio_bat_dau='09:00:00',gio_ket_thuc='10:00:00'")
        self.keeper.commit()
        self.assertFalse(self.book(when='08:00')[0])
        self.assertTrue(self.book(when='09:00')[0])
        with self.app.app_context():
            full = self.appointments.get_time_slots_status(self.day,10,203)
            self.assertFalse(any(item['selectable'] for shift in full['shifts'] for item in shift['slots']))

    def test_doctors_by_shift_reuses_booking_policy(self):
        self.schedule(capacity=1)
        with self.app.app_context():
            doctors,shift = self.appointments.get_doctors_by_shift(self.day,'08:00',10)
            self.assertEqual(shift,1)
            self.assertEqual([row['id'] for row in doctors],[203])
            self.assertEqual(self.appointments.get_doctors_by_shift(self.day,'12:00',10),([],None))
        self.assertTrue(self.book()[0])
        with self.app.app_context():
            self.assertEqual(self.appointments.get_doctors_by_shift(self.day,'09:00',10)[0],[])

    def test_update_conflict_employee_relinked_and_successful_capacity_change(self):
        first = self.schedule()
        second = self.schedule(2,2)
        with self.app.app_context():
            self.assertFalse(self.schedules.update_schedule(second,203,2,self.day,1)[0])
            self.assertTrue(self.schedules.update_schedule(first,203,1,self.day,1,so_luong_kham_toi_da=3)[0])
        self.assertTrue(self.book()[0])
        self.assertTrue(self.book(patient=102,when='09:00')[0])
        with self.app.app_context():
            self.assertFalse(self.schedules.update_schedule(first,203,1,self.day,1,so_luong_kham_toi_da=1)[0])
        self.assertEqual(self.counts(),[2,0])

    def test_reassign_same_doctor_and_status_cancel_do_not_double_count(self):
        self.schedule(capacity=1)
        self.assertTrue(self.book()[0])
        with self.app.app_context():
            for _ in range(2):
                result = self.appointments.assign_doctor(self.row()['id'],203,self.staff)
                self.assertTrue(result[0],result)
                self.assertEqual(self.counts(),[1])
            self.assertTrue(self.appointments.update_status(self.row()['id'],'Đã hủy',self.staff)[0])
            self.assertFalse(self.appointments.update_status(self.row()['id'],'Đã hủy',self.staff)[0])
            self.assertFalse(self.appointments.update_status(self.row()['id'],'Chờ tiếp nhận',self.staff)[0])
            self.assertEqual(self.counts(),[0])

    def test_approval_and_rejection_and_room_assignment_cannot_bypass_validation(self):
        identifier = self.schedule()
        self.keeper.execute("UPDATE lich_lam_viec SET trang_thai_duyet='CHO_DUYET'")
        self.keeper.commit()
        with self.app.app_context():
            result = self.schedules.approve_schedule(identifier,self.staff)
            self.assertTrue(result[0],result)
        self.assertTrue(self.book()[0])
        with self.app.app_context():
            self.assertFalse(self.schedules.approve_schedule(identifier,self.staff,False)[0])
            self.assertFalse(self.schedules.approve_cancellation(identifier,self.staff,True)[0])
            self.assertFalse(self.schedules.assign_doctor_room(203,2)[0])
            self.assertFalse(self.schedules.assign_doctor_room(203,3)[0])
        self.assertEqual(self.row()['phong_kham_id'],1)

    def test_quota_three_doctors_and_five_role_staff(self):
        # Artificial rows exist only in this verified RAM fixture, never application data.
        for number in range(5):
            self.keeper.execute('INSERT INTO tai_khoan(id,vai_tro_id,trang_thai) VALUES(?,?,1)',(90+number,3 if number<3 else 2))
            self.keeper.execute('INSERT INTO nhan_vien(id,tai_khoan_id,trang_thai) VALUES(?,?,1)',(900+number,90+number))
            if number<3:
                self.keeper.execute('INSERT INTO bac_si(id,nhan_vien_id,chuyen_khoa_id) VALUES(?,?,10)',(290+number,900+number))
            self.keeper.execute('''INSERT INTO lich_lam_viec(nhan_vien_id,bac_si_id,ngay_lam,ca_lam,gio_bat_dau,gio_ket_thuc,
                so_luong_kham_toi_da,trang_thai,trang_thai_duyet) VALUES(?,?,?,1,'07:00:00','11:30:00',2,1,'DA_DUYET')''',
                (900+number,290+number if number<3 else None,self.day))
        self.keeper.commit()
        with self.app.app_context():
            self.assertFalse(self.schedules.create_schedule(203,1,self.day,1)[0])
        self.keeper.execute('UPDATE tai_khoan SET vai_tro_id=3 WHERE id IN(93,94)')
        self.keeper.commit()
        with self.app.app_context():
            self.assertFalse(self.schedules.create_schedule(203,1,self.day,1)[0])

    def test_self_registration_invalid_shift_room_and_specialty_rejected(self):
        day = self.schedules.get_week_bounds()['next_week_1'][0].isoformat()
        doctor = {'id':3,'vai_tro':'BACSI'}
        with self.app.app_context():
            self.assertFalse(self.schedules.register_schedule(doctor,day,0,1)[0])
            self.assertFalse(self.schedules.register_schedule(doctor,day,'unknown',1)[0])
            self.assertFalse(self.schedules.register_schedule(doctor,day,1,3)[0])
            self.assertFalse(self.schedules.register_schedule(doctor,day,1,1,chuyen_khoa_id=20)[0])
            self.assertEqual(len(self.schedules.register_multiple_schedules(None,[])),4)

    def test_csv_uses_real_booking_validation_and_rolls_back_whole_import(self):
        from core.csv_service import CSVService
        self.schedule(capacity=1)
        self.keeper.execute("UPDATE benh_nhan SET sdt='TEST_PHONE' WHERE id=101")
        self.keeper.commit()
        rows = [['TEST_CSV','TEST_PHONE','Owner','10','203',self.day,'08:00','Test','Chờ tiếp nhận']]
        with self.app.app_context():
            result = CSVService.import_appointments(rows,self.staff)
            self.assertTrue(result[0],result)
            self.assertEqual(self.counts(),[1])
            rows[0][6] = '12:00'
            self.assertFalse(CSVService.import_appointments(rows,self.staff)[0])
            self.assertEqual(self.row()['gio_hen'],'08:00')

    def test_api_commit_failure_is_http_error_and_no_booking(self):
        self.schedule()
        self.login()
        with patch.object(self.db_module.UnifiedConnection,'commit',side_effect=RuntimeError('test commit failure')):
            response = self.client.post('/api/appointment/book',json={'chuyen_khoa_id':10,'bac_si_id':203,
                                        'ngay_hen':self.day,'gio_hen':'08:00'})
        self.assertEqual(response.status_code,400,response.json)
        self.assertFalse(response.json['success'])
        self.assertEqual(self.counts(),[0])
        self.assertEqual(self.keeper.execute('SELECT count(*) FROM lich_hen').fetchone()[0],0)

    def test_lock_failure_never_executes_business_write(self):
        from core import scheduling
        from unittest.mock import Mock
        connection = Mock()
        connection.cursor.return_value.fetchone.return_value = {'calendar_lock_result':-1}
        with patch.object(scheduling,'open_db',return_value=connection):
            self.assertFalse(self.book()[0])
        self.assertEqual(connection.cursor.return_value.execute.call_count,1)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()

    def test_pending_target_and_patient_conflict_prevent_reschedule(self):
        self.schedule()
        target = self.schedule(2,2)
        self.assertTrue(self.book()[0])
        self.assertTrue(self.book(patient=102,when='09:00')[0])
        identifier = self.row()['id']
        self.keeper.execute("UPDATE lich_lam_viec SET trang_thai_duyet='CHO_DUYET' WHERE id=?",(target,))
        self.keeper.commit()
        with self.app.app_context():
            self.assertFalse(self.appointments.reschedule(identifier,self.day,'14:00',user_info=self.patient)[0])
            self.assertFalse(self.appointments.reschedule(identifier,self.day,'09:00',user_info=self.patient)[0])
        self.assertEqual(self.counts(),[2,0])

    def test_bulk_approval_reports_zero_failure_and_invalid_boolean_rejected(self):
        identifier = self.schedule()
        self.keeper.execute("UPDATE lich_lam_viec SET trang_thai_duyet='CHO_DUYET',phong_kham_id=3")
        self.keeper.commit()
        with self.app.app_context():
            result = self.schedules.bulk_approve_schedules([identifier],self.staff)
            self.assertFalse(result[0],result)
            self.assertEqual(result[2],0)
        self.login(7)
        response = self.client.post('/api/schedule/approve-registration',json={'id':identifier,'approved':'false'})
        self.assertEqual(response.status_code,400,response.json)

    def test_doctor_assignment_to_another_shift_and_cross_day_move(self):
        self.schedule()
        self.assertTrue(self.book()[0])
        identifier = self.row()['id']
        next_day = (date.fromisoformat(self.day)+timedelta(days=1)).isoformat()
        with self.app.app_context():
            self.assertTrue(self.schedules.create_schedule(203,2,next_day,2)[0])
            result = self.appointments.reschedule(identifier,next_day,'14:00',user_info=self.patient)
            self.assertTrue(result[0],result)
            self.assertEqual(self.counts(),[0,1])
            self.assertEqual(self.row()['phong_kham_id'],2)

    def test_real_http_login_booking_page_api_move_cancel_and_ram_observation(self):
        from werkzeug.serving import make_server
        self.schedule()
        self.schedule(2,2)
        server = make_server('127.0.0.1',0,self.app)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        self.start_test_thread(thread)
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):
                return None
        http = build_opener(ProxyHandler({}),HTTPCookieProcessor(CookieJar()),NoRedirect())
        base = 'http://127.0.0.1:'+str(server.server_port)
        try:
            with http.open(base+'/login',timeout=5) as response:
                self.assertIn(b'<form',response.read())
            with self.assertRaises(HTTPError) as redirect:
                http.open(base+'/login',data=urlencode({'username':'fixture_1','password':'IsolatedPassword123!'}).encode(),timeout=5)
            self.assertEqual(redirect.exception.code,302)
            redirect.exception.close()
            with http.open(base+'/patient/booking',timeout=5) as response:
                self.assertEqual(response.status,200)
                self.assertIn(b'gio_hen',response.read())
            def post(path,payload):
                with http.open(Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=5) as response:
                    self.assertEqual(response.status,200)
                    self.assertTrue(json.load(response)['success'])
            post('/api/appointment/book',{'chuyen_khoa_id':10,'bac_si_id':203,'ngay_hen':self.day,'gio_hen':'08:00'})
            identifier = self.row()['id']
            self.assertEqual(self.counts(),[1,0])
            post('/api/appointment/reschedule',{'id':identifier,'ngay_hen':self.day,'gio_hen':'14:00'})
            self.assertEqual(self.counts(),[0,1])
            self.assertEqual(self.row()['phong_kham_id'],2)
            post('/api/appointment/cancel',{'id':identifier})
            self.assertEqual(self.counts(),[0,0])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == '__main__':
    unittest.main()
