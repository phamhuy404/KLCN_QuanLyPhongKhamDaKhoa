"""MSSQL integration only; requires separately confirmed disposable test database.
No SQLite, SQL translation or mocked application lock in integration paths.
"""
from datetime import date
from uuid import uuid4
import unittest
from unittest.mock import patch
import base64
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import threading
from http.cookiejar import CookieJar
from urllib.request import build_opener, ProxyHandler, HTTPCookieProcessor, Request, HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError

from tests import test_scheduling_safety as calendar


class EmrWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        calendar.SchedulingTests.setUpClass.__func__(cls)
        from models.medical_record_model import MedicalRecordModel
        cls.records = MedicalRecordModel

    connection = calendar.SchedulingTests.connection
    login = calendar.SchedulingTests.login
    tearDown = calendar.SchedulingTests.tearDown

    def setUp(self):
        calendar.SchedulingTests.setUp(self)
        self.keeper.executescript('''
            DROP TABLE phieu_kham;
            DROP TABLE hoa_don;
            DROP TABLE chi_tiet_hoa_don;
            CREATE TABLE phieu_kham(id INT IDENTITY(1,1) PRIMARY KEY,ma_phieu NVARCHAR(100) UNIQUE,
                benh_nhan_id INT,bac_si_id INT,phong_kham_id INT,lich_hen_id INT,
                thoi_gian_kham DATETIME2(0) DEFAULT CURRENT_TIMESTAMP,ly_do_kham NVARCHAR(MAX),trieu_chung NVARCHAR(MAX),chan_doan_so_bo NVARCHAR(MAX),
                chan_doan_icd NVARCHAR(MAX),huong_dieu_tri NVARCHAR(MAX),loi_dan NVARCHAR(MAX),ngay_tai_kham DATE,hinh_anh_kham NVARCHAR(MAX),trang_thai NVARCHAR(MAX));
            CREATE TABLE phieu_chi_dinh(id INT IDENTITY(1,1) PRIMARY KEY,ma_chi_dinh NVARCHAR(100) UNIQUE,
                phieu_kham_id INT,bac_si_id INT,trang_thai NVARCHAR(MAX));
            CREATE TABLE chi_tiet_chi_dinh(id INT IDENTITY(1,1) PRIMARY KEY,phieu_chi_dinh_id INT,
                dich_vu_id INT,ket_qua NVARCHAR(MAX),file_ket_qua NVARCHAR(MAX),trang_thai NVARCHAR(MAX));
            CREATE TABLE dich_vu(id INT PRIMARY KEY,ten_dich_vu NVARCHAR(MAX),loai_dich_vu NVARCHAR(MAX),don_gia DECIMAL(18,2),bhyt_chi_tra_pt DECIMAL(18,2));
            INSERT INTO dich_vu VALUES(1,'MSSQL test lab','Lab',20000,0);
            CREATE TABLE thuoc(id INT PRIMARY KEY,trang_thai INT DEFAULT 1,ten_thuoc NVARCHAR(MAX),so_luong_ton INT,don_vi_tinh NVARCHAR(MAX),don_gia DECIMAL(18,2));
            INSERT INTO thuoc(id,ten_thuoc,so_luong_ton,don_vi_tinh,don_gia) VALUES(1,'MSSQL test drug',10,'Unit',1000);
            CREATE TABLE don_thuoc(id INT IDENTITY(1,1) PRIMARY KEY,ma_don_thuoc NVARCHAR(100) UNIQUE,phieu_kham_id INT,
                bac_si_id INT,loi_dan NVARCHAR(MAX),trang_thai NVARCHAR(MAX),hinh_thuc_mua NVARCHAR(MAX));
            CREATE TABLE chi_tiet_don_thuoc(id INT IDENTITY(1,1) PRIMARY KEY,don_thuoc_id INT,thuoc_id INT,
                so_luong INT,lieu_dung NVARCHAR(MAX),cach_dung NVARCHAR(MAX));
            CREATE TABLE hoa_don(id INT IDENTITY(1,1) PRIMARY KEY,ma_hoa_don NVARCHAR(100) UNIQUE,benh_nhan_id INT,
                phieu_kham_id INT,tong_tien DECIMAL(18,2),tien_bhyt DECIMAL(18,2),giam_gia DECIMAL(18,2) DEFAULT 0,thanh_tien DECIMAL(18,2),trang_thai NVARCHAR(MAX));
            CREATE TABLE chi_tiet_hoa_don(id INT IDENTITY(1,1) PRIMARY KEY,hoa_don_id INT,loai_khoan_thu NVARCHAR(MAX),
                ten_khoan_thu NVARCHAR(MAX),tham_chieu_id INT,so_luong INT,don_gia DECIMAL(18,2),thanh_tien DECIMAL(18,2));
        ''')
        self.keeper.execute('ALTER TABLE chuyen_khoa ADD gia_kham_mac_dinh DECIMAL(18,2) DEFAULT 150000 WITH VALUES')
        self.day = date.today().isoformat()
        self.keeper.execute('SET IDENTITY_INSERT lich_hen ON')
        for identifier,value in ((1,'08:00'),(2,'10:00')):
            self.keeper.execute('''INSERT INTO lich_hen(id,ma_lich_hen,benh_nhan_id,bac_si_id,chuyen_khoa_id,
                phong_kham_id,ngay_hen,gio_hen,trang_thai) VALUES(?,?,101,203,10,1,?,?,N'Đã tiếp nhận')''',
                (identifier,'TEST_LH'+str(identifier),self.day,value))
        self.keeper.execute('SET IDENTITY_INSERT lich_hen OFF')
        self.keeper.commit()
        extra = {'thuoc':('ma_thuoc','hoat_chat','ham_luong','hang_san_xuat','nuoc_san_xuat','huong_dan_su_dung'),
                 'dich_vu':('chuyen_khoa_id','trang_thai'),
                 'phieu_chi_dinh':('thoi_gian_chi_dinh','ghi_chu'),
                 'chi_tiet_chi_dinh':('ktv_thuc_hien','nguoi_nhap','thoi_gian_thuc_hien','bac_si_duyet','thoi_gian_duyet','ghi_chu_duyet')}
        for table,columns in extra.items():
            for column in columns:
                self.keeper.execute('ALTER TABLE '+table+' ADD '+column+' NVARCHAR(MAX)')
        self.keeper.commit()
        self.doctor = {'id':3,'vai_tro':'BACSI','bac_si_id':203}
        self.key = str(uuid4())

    def count(self,table):
        return self.keeper.execute('SELECT count(*) FROM '+table).fetchone()[0]

    def state(self,identifier):
        return self.keeper.execute('SELECT trang_thai FROM lich_hen WHERE id=?',(identifier,)).fetchone()[0]

    def step(self,appointment=1,**kwargs):
        payload = dict(patient_id=101,appointment_id=appointment,audit_user=self.doctor)
        payload.update(kwargs)
        with self.app.app_context():
            return self.records.save_step(**payload)

    def save(self,appointment=1,**kwargs):
        payload = dict(patient_id=101,doctor_id=None,room_id=None,reason='Test',symptoms='Test',
                       diagnosis='Diagnosis',icd='TEST',treatment='Test',advice='Test',
                       appointment_id=appointment,audit_user=self.doctor)
        payload.update(kwargs)
        with self.app.app_context():
            return self.records.save_examination(**payload)

    def finish(self,identifier,**kwargs):
        payload = dict(record_id=identifier,diagnosis='Final diagnosis',icd='TEST',treatment='Test',
                       advice='Test',audit_user=self.doctor)
        payload.update(kwargs)
        with self.app.app_context():
            return self.records.finish_examination(**payload)

    def test_multiple_appointments_update_only_exact_link_and_reuse_draft(self):
        ok,draft = self.step(2)
        self.assertTrue(ok,draft)
        self.assertTrue(self.save(2,record_id=draft['record_id'])[0])
        self.assertEqual(self.count('phieu_kham'),1)
        row = self.keeper.execute('SELECT * FROM phieu_kham').fetchone()
        self.assertEqual(row['lich_hen_id'],2)
        self.assertEqual(self.state(1),'Đã tiếp nhận')
        self.assertEqual(self.state(2),'Đã khám')
        self.assertFalse(self.save(2)[0])
        self.assertEqual(self.count('hoa_don'),1)

    def test_two_distinct_visits_do_not_merge(self):
        self.assertTrue(self.save(1)[0])
        self.assertTrue(self.save(2)[0])
        self.assertEqual(self.count('phieu_kham'),2)
        self.assertEqual(self.count('hoa_don'),2)
        self.assertEqual([row[0] for row in self.keeper.execute('SELECT lich_hen_id FROM phieu_kham ORDER BY id')],[1,2])

    def test_walk_in_explicit_key_replay_and_no_appointment_changes(self):
        args = dict(walk_in=True,encounter_key=self.key,doctor_id=203,room_id=1)
        self.assertFalse(self.save(None,doctor_id=203,room_id=1)[0])
        first = self.step(None,**args)
        second = self.step(None,**args)
        self.assertTrue(first[0],first)
        self.assertEqual(first[1]['record_id'],second[1]['record_id'])
        self.assertTrue(self.save(None,**args)[0])
        self.assertFalse(self.save(None,**args)[0])
        self.assertEqual(self.count('hoa_don'),1)
        self.assertIsNone(self.keeper.execute('SELECT lich_hen_id FROM phieu_kham').fetchone()[0])
        self.assertEqual(len(self.keeper.execute('SELECT ma_phieu FROM phieu_kham').fetchone()[0]),29)
        self.assertEqual(self.state(1),'Đã tiếp nhận')
        self.assertTrue(self.save(None,**dict(args,encounter_key=str(uuid4())))[0])
        self.assertEqual(self.count('phieu_kham'),2)

    def test_wrong_patient_doctor_role_status_and_missing_profile(self):
        for changes in ({'patient_id':102},{'patient_id':999},{'doctor_id':999},{'doctor_id':204},
                        {'room_id':3},{'audit_user':{'id':1}},{'audit_user':None}):
            with self.subTest(changes=changes):
                self.assertFalse(self.save(**changes)[0])
        for status in ('Chờ tiếp nhận','Chờ xác nhận','Đã hủy','Đã khám'):
            self.keeper.execute('UPDATE lich_hen SET trang_thai=? WHERE id=1',(status,))
            self.keeper.commit()
            self.assertFalse(self.save()[0])
        self.assertEqual(self.count('phieu_kham'),0)

    def test_wait_for_cls_then_finish_after_approved_results_and_replay(self):
        result = self.save(lab_service_ids=[1])
        self.assertTrue(result[0],result)
        identifier = self.keeper.execute('SELECT id FROM phieu_kham').fetchone()[0]
        self.assertEqual(self.state(1),'Chờ kết quả CLS')
        self.assertFalse(self.finish(identifier)[0])
        self.keeper.execute("UPDATE chi_tiet_chi_dinh SET ket_qua='Observed result',trang_thai=N'Chờ duyệt'")
        self.keeper.commit()
        self.assertFalse(self.finish(identifier)[0])
        self.keeper.execute("UPDATE chi_tiet_chi_dinh SET trang_thai=N'Đã duyệt'")
        self.keeper.commit()
        medicine = [{'thuoc_id':1,'so_luong':2}]
        result = self.finish(identifier,medicines=medicine)
        self.assertTrue(result[0],result)
        self.assertFalse(self.finish(identifier,medicines=medicine)[0])
        self.assertEqual(self.count('don_thuoc'),1)
        self.assertEqual(self.count('hoa_don'),1)
        self.assertEqual(self.state(1),'Đã khám')
        self.assertEqual(self.state(2),'Đã tiếp nhận')

    def test_legacy_unlinked_record_never_auto_attached(self):
        self.keeper.execute("INSERT INTO phieu_kham(ma_phieu,benh_nhan_id,bac_si_id,phong_kham_id,trang_thai) VALUES('LEGACY',101,203,1,N'Đang khám')")
        self.keeper.commit()
        identifier = self.keeper.execute('SELECT id FROM phieu_kham').fetchone()[0]
        self.assertFalse(self.step(record_id=identifier)[0])
        self.assertTrue(self.save(2)[0])
        self.assertIsNone(self.keeper.execute('SELECT lich_hen_id FROM phieu_kham WHERE id=?',(identifier,)).fetchone()[0])
        self.assertEqual(self.count('phieu_kham'),2)

    def test_mid_invoice_failure_rolls_back_draft_appointment_orders_and_prescription(self):
        self.keeper.execute('DROP TABLE chi_tiet_hoa_don')
        self.keeper.commit()
        result = self.save(lab_service_ids=[1],medicines=[{'thuoc_id':1,'so_luong':1}])
        self.assertFalse(result[0],result)
        for table in ('phieu_kham','phieu_chi_dinh','chi_tiet_chi_dinh','don_thuoc','hoa_don','thong_bao','audit_log'):
            self.assertEqual(self.count(table),0,table)
        self.assertEqual(self.state(1),'Đã tiếp nhận')

    def test_commit_failure_is_error_without_partial_data(self):
        with patch.object(self.db_module.UnifiedConnection,'commit',side_effect=RuntimeError('test commit failure')):
            self.assertFalse(self.save()[0])
        self.assertEqual(self.count('phieu_kham'),0)
        self.assertEqual(self.count('hoa_don'),0)
        self.assertEqual(self.state(1),'Đã tiếp nhận')

    def test_api_step_save_finish_with_exact_record_and_permissions(self):
        self.login(3)
        response = self.client.post('/api/emr/save-step',json={'patient_id':101,'appointment_id':2,'step':1})
        self.assertEqual(response.status_code,200,response.json)
        identifier = response.json['record_id']
        response = self.client.post('/api/emr/save',json={'patient_id':101,'appointment_id':2,'record_id':identifier,'diagnosis':'Test'})
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(self.count('phieu_kham'),1)
        self.assertEqual(self.state(1),'Đã tiếp nhận')
        self.assertEqual(self.state(2),'Đã khám')
        response = self.client.post('/api/emr/finish',json={'record_id':identifier,'diagnosis':'Test'})
        self.assertEqual(response.status_code,400,response.json)
        self.assertEqual(self.count('hoa_don'),1)

    def test_save_step_failure_preserves_existing_draft_and_patient_history(self):
        ok, draft = self.step(symptoms='Original symptom')
        self.assertTrue(ok,draft)
        self.keeper.executescript("""CREATE TRIGGER dbo.test_fail_appointment_update ON dbo.lich_hen
            AFTER UPDATE AS BEGIN THROW 51000, 'intentional step failure', 1; END;""")
        self.keeper.commit()
        with self.app.app_context():
            result = self.records.save_step(101,record_id=draft['record_id'],symptoms='Must roll back',
                                            di_ung='Must roll back',audit_user=self.doctor)
        self.assertFalse(result[0],result)
        self.assertEqual(self.keeper.execute('SELECT trieu_chung FROM phieu_kham').fetchone()[0],'Original symptom')
        self.assertIsNone(self.keeper.execute('SELECT di_ung FROM benh_nhan WHERE id=101').fetchone()[0])
        self.assertEqual(self.count('phieu_kham'),1)

    def test_approved_but_empty_result_and_duplicate_prescription_rejected(self):
        result = self.save(lab_service_ids=[1],medicines=[{'thuoc_id':1,'so_luong':1}])
        self.assertTrue(result[0],result)
        identifier = self.keeper.execute('SELECT id FROM phieu_kham').fetchone()[0]
        self.keeper.execute("UPDATE chi_tiet_chi_dinh SET trang_thai=N'Đã duyệt'")
        self.keeper.commit()
        self.assertFalse(self.finish(identifier)[0])
        self.keeper.execute("UPDATE chi_tiet_chi_dinh SET ket_qua='Observed result'")
        self.keeper.commit()
        self.assertFalse(self.finish(identifier,medicines=[{'thuoc_id':1,'so_luong':2}])[0])
        self.assertTrue(self.finish(identifier)[0])
        self.assertEqual(self.count('don_thuoc'),1)
        self.assertEqual(self.count('hoa_don'),1)

    def test_api_rejects_anonymous_roles_locked_identity_and_conflicting_payloads(self):
        payload = {'patient_id':101,'appointment_id':1,'step':1}
        self.assertEqual(self.client.post('/api/emr/save-step',json=payload).status_code,401)
        for account in (1,5):
            self.login(account)
            self.assertEqual(self.client.post('/api/emr/save-step',json=payload).status_code,403)
        self.login(3)
        self.assertEqual(self.client.post('/api/emr/save-step',json=dict(payload,lich_hen_id=2)).status_code,400)
        self.assertEqual(self.client.post('/api/emr/save',json=dict(payload,diagnosis='Test',medicines={})).status_code,400)
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=0 WHERE id=3')
        self.keeper.commit()
        self.assertEqual(self.client.post('/api/emr/save-step',json=payload).status_code,401)
        self.assertEqual(self.count('phieu_kham'),0)

    def test_finish_failure_after_record_update_restores_pending_state(self):
        self.assertTrue(self.save(lab_service_ids=[1])[0])
        identifier = self.keeper.execute('SELECT id FROM phieu_kham').fetchone()[0]
        self.keeper.execute("UPDATE chi_tiet_chi_dinh SET trang_thai=N'Đã duyệt',ket_qua='Result'")
        self.keeper.execute('DROP TABLE chi_tiet_don_thuoc')
        self.keeper.commit()
        self.assertFalse(self.finish(identifier,medicines=[{'thuoc_id':1,'so_luong':1}])[0])
        self.assertEqual(self.keeper.execute('SELECT trang_thai FROM phieu_kham').fetchone()[0],'Chờ kết quả CLS')
        self.assertEqual(self.state(1),'Chờ kết quả CLS')
        self.assertEqual(self.count('don_thuoc'),0)
        self.assertEqual(self.count('hoa_don'),1)

    def test_other_attending_doctor_and_locked_account_rejected(self):
        self.keeper.executescript('''
            SET IDENTITY_INSERT tai_khoan ON;
            INSERT INTO tai_khoan(id,vai_tro_id,trang_thai) VALUES(99,3,1);
            SET IDENTITY_INSERT tai_khoan OFF;
            INSERT INTO nhan_vien(id,tai_khoan_id,trang_thai) VALUES(999,99,1);
            INSERT INTO bac_si(id,nhan_vien_id,chuyen_khoa_id) VALUES(299,999,10);
            UPDATE lich_hen SET bac_si_id=299,phong_kham_id=2 WHERE id=2;
        ''')
        self.keeper.commit()
        self.assertFalse(self.save(2)[0])
        self.keeper.execute('UPDATE tai_khoan SET trang_thai=0 WHERE id=3')
        self.keeper.commit()
        self.assertFalse(self.save()[0])
        self.assertEqual(self.count('phieu_kham'),0)

    def test_api_failure_cleans_only_new_images_and_rollback_commit(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            self.app.config['MEDICAL_UPLOAD_DIR'] = directory
            image = io.BytesIO()
            Image.new('RGB',(3,3)).save(image,format='PNG')
            encoded = 'data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
            existing = Path(directory)/'existing-do-not-delete.webp'
            existing.write_bytes(b'Existing unchanged test fixture')
            self.login(3)
            payload = {'patient_id':101,'appointment_id':1,'diagnosis':'Test','images':[encoded]}
            with patch.object(self.db_module.UnifiedConnection,'commit',side_effect=RuntimeError('test commit failure')):
                response = self.client.post('/api/emr/save',json=payload)
            self.assertEqual(response.status_code,400,response.json)
            self.assertEqual([p.name for p in Path(directory).rglob('*') if p.is_file()],[existing.name])
            self.assertEqual(existing.read_bytes(),b'Existing unchanged test fixture')
            self.assertEqual(self.count('phieu_kham'),0)
            self.assertEqual(self.state(1),'Đã tiếp nhận')

    def test_real_http_ui_step_cls_result_approval_finish_and_retry(self):
        from werkzeug.serving import make_server
        server = make_server('127.0.0.1',0,self.app)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        self.start_test_thread(thread)
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):
                return None
        base = 'http://127.0.0.1:'+str(server.server_port)
        def login(account):
            client = build_opener(ProxyHandler({}),HTTPCookieProcessor(CookieJar()),NoRedirect())
            with self.assertRaises(HTTPError) as redirect:
                client.open(base+'/login',data=urlencode({'username':'fixture_'+str(account),'password':'IsolatedPassword123!'}).encode(),timeout=5)
            self.assertEqual(redirect.exception.code,302)
            redirect.exception.close()
            return client
        def post(client,path,payload,expected=200):
            try:
                response = client.open(Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=5)
            except HTTPError as error:
                response = error
            with response:
                body = json.load(response)
                self.assertEqual(response.code,expected,body)
                return body
        try:
            doctor = login(3)
            with doctor.open(base+'/admin/emr?patient_id=101&appointment_id=2',timeout=5) as response:
                html = response.read().decode()
                self.assertIn('emr-encounter-select',html)
            # Actual rendered JavaScript syntax, including Jinja substitutions.
            scripts = [code for attrs,code in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S)
                       if 'application/json' not in attrs and code.strip()]
            with tempfile.TemporaryDirectory() as directory:
                file = Path(directory)/'emr-rendered.js'
                file.write_text('\n'.join(scripts),encoding='utf-8')
                with tempfile.TemporaryFile(mode='w+',encoding='utf-8') as output:
                    result = subprocess.run(['node','--check',str(file)],stdout=output,stderr=output,timeout=20)
                    output.seek(0)
                    self.assertEqual(result.returncode,0,output.read())
                data = {re.search(r'id="([^"]+)"',attrs).group(1):code
                        for attrs,code in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S)
                        if 'application/json' in attrs and 'id="' in attrs}
                main = next(code for code in scripts if 'let rawPatients =' in code)
                harness = r'''
const assert = require('node:assert/strict');
const domReady = [], nodes = new Map(), requests = [];
global.window = global;
global.location = {search:'?patient_id=101&appointment_id=2',reload(){}};
global.alert = () => {};
global.confirm = () => true;
global.Option = class { constructor(text,value){this.text=text;this.value=value;} };
class Element {
 constructor(id){this.id=id;this.value='';this.textContent=DATA[id]||'';this.style={};this.options=[];
   this.tagName='INPUT';this.classList={add(){},remove(){},toggle(){}};}
 add(option){this.options.push(option);}
 replaceChildren(...options){this.options=options;}
 appendChild(){}
}
global.document = {
 getElementById(id){if(!nodes.has(id)) nodes.set(id,new Element(id));return nodes.get(id);},
 addEventListener(event,callback){if(event==='DOMContentLoaded') domReady.push(callback);},
 querySelectorAll(){return [];},createElement(){return new Element('temporary');}
};
global.fetch = (url,options) => {
 requests.push({url,payload:JSON.parse(options.body)});
 return Promise.resolve({json:async()=>({success:true,record_id:700})});
};
'''
                checks = r'''
(async()=>{
 for(const ready of domReady) ready();
 assert.equal(currentEmrContext.appointment_id,2);
 assert.equal(currentActiveEncounterId,null);
 assert.equal(prescriptionItems.length,0,'No automatic/sample medicines');
 advanceEmrStep(1,2);
 await new Promise(setImmediate);
 assert.equal(requests.at(-1).payload.appointment_id,2);
 assert.equal(currentActiveEncounterId,700);
 selectEmrEncounter('appointment:1');
 assert.equal(currentActiveEncounterId,null,'Do not reuse another appointment draft');
 assert.equal(emrContextPayload().appointment_id,1);
 lockEmrClinicalStep();
 selectEmrEncounter('walk-in');
 document.getElementById('emr-attending-doctor').value='203';
 document.getElementById('emr-walk-in-room').value='1';
 const direct=emrContextPayload();
 assert.equal(direct.walk_in,true);
 assert.equal(isSessionTransferred,false,'A new visit must unlock the editor');
 assert.equal(emrContextPayload().encounter_key,direct.encounter_key,'Retry retains identity');
 assert.equal(direct.appointment_id,undefined);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
                file.write_text('const DATA='+json.dumps(data)+';\n'+harness+'\n'+main+'\n'+checks,encoding='utf-8')
                with tempfile.TemporaryFile(mode='w+',encoding='utf-8') as output:
                    result = subprocess.run(['node',str(file)],stdout=output,stderr=output,timeout=20)
                    output.seek(0)
                    self.assertEqual(result.returncode,0,output.read())
            draft = post(doctor,'/api/emr/save-step',{'patient_id':101,'appointment_id':2,'step':1,'symptoms':'Observed'})
            identifier = draft['record_id']
            post(doctor,'/api/emr/save',{'patient_id':101,'appointment_id':2,'record_id':identifier,'diagnosis':'Test diagnosis','lab_services':[1]})
            post(doctor,'/api/emr/finish',{'record_id':identifier,'diagnosis':'Final'},400)
            laboratory = login(5)
            item = self.keeper.execute('SELECT id FROM chi_tiet_chi_dinh').fetchone()[0]
            post(laboratory,'/api/lab/result/save',{'chi_tiet_id':item,'ket_qua':'Observed lab result'})
            post(doctor,'/api/lab/result/approve',{'chi_tiet_id':item})
            finish = {'record_id':identifier,'diagnosis':'Final diagnosis','medicines':[{'thuoc_id':1,'so_luong':2}]}
            post(doctor,'/api/emr/finish',finish)
            post(doctor,'/api/emr/finish',finish,400)
            self.assertEqual(self.count('phieu_kham'),1)
            self.assertEqual(self.count('hoa_don'),1)
            self.assertEqual(self.count('don_thuoc'),1)
            self.assertEqual(self.state(1),'Đã tiếp nhận')
            self.assertEqual(self.state(2),'Đã khám')
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == '__main__':
    unittest.main()
