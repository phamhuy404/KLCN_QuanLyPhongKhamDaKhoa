"""HTTP contract/security tests using signed tokens and isolated model doubles; never SQL production."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import io
import time
import unittest
from unittest.mock import patch
from PIL import Image
from app import create_app
from core.mobile_auth import serializer, stamp


class Cursor:
    def execute(self, sql, params=()):
        return self
    def fetchone(self):
        return None  # No token revoked in this test repository.


class Connection:
    def cursor(self):
        return Cursor()
    def close(self):
        pass


class MobilePatientContractTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'isolated-mobile-test-secret-key-32bytes',
            'DATABASE_CONNECTION_FACTORY': Connection})
        self.client = self.app.test_client()
        self.users = {i: dict(id=i, patient_id=pid, vai_tro='BENHNHAN', ho_ten=f'Patient {i}',
            sdt='0912345678', email='', ma_benh_nhan=f'BN{pid}', da_hoan_thien_ho_so=True)
            for i, pid in [(1, 101), (2, 202)]}
        self.identity = patch('core.mobile_auth.live_identity', side_effect=lambda cursor, account: (dict(self.users[account]), 'password-hash'))
        self.identity.start()
        self.addCleanup(self.identity.stop)
        self.token_a = self.token(1)
        self.token_b = self.token(2)
        self.profile = patch('controllers.mobile_patient_controller.PatientModel.get_by_id',
            side_effect=lambda pid: dict(id=pid, ho_ten='Nguyễn Văn An', sdt='0912345678',
                ngay_sinh='1990-01-02', gioi_tinh='Nam', cccd='079123456789', bhyt='', dia_chi='Hà Nội', ma_benh_nhan=f'BN{pid}', vitals={}))
        self.profile.start()
        self.addCleanup(self.profile.stop)

    def token(self, account, expired=False):
        with self.app.app_context():
            now = int(time.time())
            return serializer().dumps(dict(sub=account, pid=self.users[account]['patient_id'],
                jti=str(account)*32, stamp=stamp('password-hash'), iat=now, exp=now-1 if expired else now+3600))

    def get(self, path, token=None):
        return self.client.get('/api/v1/mobile/patient'+path, headers={'Authorization': 'Bearer '+(token or self.token_a)})

    def post(self, path, data=None, token=None):
        return self.client.post('/api/v1/mobile/patient'+path, json=data or {}, headers={'Authorization': 'Bearer '+(token or self.token_a)})

    def test_registered_and_requires_bearer_not_cookie(self):
        with self.client.session_transaction() as session:
            session['logged_in'] = True
            session['user'] = self.users[1]
        self.assertEqual(self.client.get('/api/v1/mobile/patient/profile').status_code, 401)
        self.assertEqual(self.get('/profile', 'forged').status_code, 401)
        response = self.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['patient']['id'], 101)
        self.assertNotIn('Set-Cookie', response.headers)

    def test_expired_token(self):
        response = self.get('/profile', self.token(1, expired=True))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error_code'], 'TOKEN_EXPIRED')

    def test_profile_gate_and_completion(self):
        self.users[1]['da_hoan_thien_ho_so'] = False
        self.assertEqual(self.get('/profile').status_code, 200)
        self.assertEqual(self.get('/appointments').json['error_code'], 'PROFILE_REQUIRED')
        with patch('controllers.mobile_patient_controller.UserModel.complete_patient_profile', return_value=(True, 'OK')) as complete, patch('controllers.mobile_patient_controller.UserModel.get_session_user', return_value={**self.users[1], 'da_hoan_thien_ho_so': True}):
            invalid = self.post('/complete-profile', {'ho_ten': 'A1', 'ngay_sinh': '2999-01-01'})
            self.assertEqual(invalid.status_code, 400)
            complete.assert_not_called()
            response = self.post('/complete-profile', {'ho_ten': 'Nguyễn Văn An', 'ngay_sinh': '1990-01-02', 'gioi_tinh': 'Nam', 'patient_id': 202})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['user']['profile_complete'])
            self.assertEqual(complete.call_args.args[0], 1)

    def test_a_cannot_read_change_or_cancel_b_appointment(self):
        with patch('controllers.mobile_patient_controller.AppointmentModel.get_by_id', return_value={'id': 7, 'benh_nhan_id': 202}), patch('controllers.mobile_patient_controller.AppointmentModel.cancel') as cancel, patch('controllers.mobile_patient_controller.AppointmentModel.reschedule') as change:
            self.assertEqual(self.get('/appointments/7').status_code, 404)
            self.assertEqual(self.post('/appointments/7/cancel').status_code, 404)
            self.assertEqual(self.post('/appointments/7/reschedule').status_code, 404)
            cancel.assert_not_called()
            change.assert_not_called()
            self.assertEqual(self.get('/appointments/7', self.token_b).status_code, 200)

    def test_create_uses_verified_owner_and_real_model_conflict(self):
        with patch('controllers.mobile_patient_controller.AppointmentModel.create', return_value=(False, 'Khung giờ vừa được đặt')) as create:
            result = self.post('/appointments', {'patient_id': 202, 'chuyen_khoa_id': 3, 'ngay_hen': '2099-01-01', 'gio_hen': '09:00'})
            self.assertEqual(result.status_code, 409)
            self.assertEqual(create.call_args.args[0], 101)
            self.assertEqual(create.call_args.kwargs['audit_user']['id'], 1)

    def test_booking_catalog_and_matrix_match_web(self):
        with patch('controllers.mobile_patient_controller.ClinicModel.get_all_departments', return_value=[{'id': 3, 'ten_khoa': 'Nội'}]), patch('controllers.mobile_patient_controller.ClinicModel.get_exam_services', return_value=[{'id': 4, 'chuyen_khoa_id': 3}]), patch('controllers.mobile_patient_controller.AppointmentModel.get_booking_matrix', return_value={'success': True, 'doctors': [{'id': 9}], 'doctor_slots': {9: ['09:00']}, 'all_available_slots': ['09:00']}):
            result = self.get('/booking-meta?date=2099-01-01&chuyen_khoa_id=3&bac_si_id=9')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json['slots'], ['09:00'])
            self.assertEqual(result.json['exam_services'][0]['id'], 4)

    def test_prescription_and_invoice_ownership(self):
        with patch('controllers.mobile_patient_controller.PharmacyModel.get_prescription_detail', return_value={'benh_nhan_id': 202}), patch('controllers.mobile_patient_controller.PharmacyModel.choose_medicine_purchase_option') as choose:
            self.assertEqual(self.post('/prescriptions/1/purchase-option', {'option':'Tự mua ngoài'}).status_code, 404)
            choose.assert_not_called()
        with patch('controllers.mobile_patient_controller.BillingModel.get_invoice', return_value={'benh_nhan_id':202}), patch('controllers.mobile_patient_controller.BillingModel.payment_instructions') as pay:
            self.assertEqual(self.post('/billing/1/instructions').status_code, 404)
            pay.assert_not_called()

    def test_payment_instructions_never_confirm_transaction(self):
        with patch('controllers.mobile_patient_controller.BillingModel.get_invoice', return_value={'benh_nhan_id':101}), patch('controllers.mobile_patient_controller.BillingModel.payment_instructions', return_value=(True, {'amount':125000,'gateway_enabled':False})):
            result = self.post('/billing/1/instructions')
            self.assertFalse(result.json['payment_confirmed'])
            self.assertEqual(result.json['payment']['amount'], 125000)

    def test_feedback_uses_full_history_status_and_owner(self):
        with patch('controllers.mobile_patient_controller.FeedbackModel.get_by_patient', return_value=[{'id':n,'trang_thai':'Đã xử lý','phan_hoi_admin':'OK'} for n in range(8)]) as history:
            self.assertEqual(len(self.get('/feedbacks').json['feedbacks']), 8)
            history.assert_called_once_with(101)
        with patch('controllers.mobile_patient_controller.PatientModel.get_patient_history', return_value=[]), patch('controllers.mobile_patient_controller.FeedbackModel.create') as create:
            self.assertEqual(self.post('/feedbacks', {'chu_de':'Khám','noi_dung':'Góp ý dịch vụ','diem_danh_gia':5,'phieu_kham_id':202}).status_code, 404)
            create.assert_not_called()

    def test_notification_does_not_mark_other_accounts_id(self):
        with patch('controllers.mobile_patient_controller.NotificationModel.get_user_notifications', return_value=[{'id':1}]), patch('controllers.mobile_patient_controller.NotificationModel.mark_as_read') as mark:
            self.assertEqual(self.post('/notifications/read', {'notification_id':2}).status_code, 404)
            mark.assert_not_called()

    def test_profile_update_ignores_client_owner_and_clinical_fields(self):
        with patch('controllers.mobile_patient_controller.PatientModel.update_profile', return_value=(True, 'OK')) as update, patch('controllers.mobile_patient_controller.UserModel.get_session_user', return_value=self.users[1]):
            result=self.client.put('/api/v1/mobile/patient/profile', json={'patient_id':202,'chan_doan':'forged','ho_ten':'Nguyễn Văn An'}, headers={'Authorization':'Bearer '+self.token_a})
            self.assertEqual(result.status_code,200)
            self.assertEqual(update.call_args.args[0],101)
            self.assertNotIn('chan_doan',update.call_args.args[1])
            self.assertNotIn('patient_id',update.call_args.args[1])

    def test_records_explicitly_request_published_results(self):
        with patch('controllers.mobile_patient_controller.PatientModel.get_patient_history',return_value=[]) as history:
            self.assertEqual(self.get('/records').status_code,200)
            history.assert_called_with(101,approved_only=True)

    def test_labs_image_not_found_for_other_patient(self):
        with patch('controllers.mobile_patient_controller.PatientModel.get_all_lab_results',return_value=([],{})):
            self.assertEqual(self.get('/lab-results/202/image').status_code,404)

    def test_avatar_uses_backend_image_decoder(self):
        stream=io.BytesIO()
        Image.new('RGB',(2,2)).save(stream,format='PNG')
        stream.seek(0)
        with patch('core.image_service.process_image_input',return_value=('/static/uploads/benh_nhan/test.webp',None)) as process, patch('controllers.mobile_patient_controller.PatientModel.update_patient_avatar',return_value=(True,'OK')) as update:
            result=self.client.post('/api/v1/mobile/patient/profile/avatar',data={'avatar_file':(stream,'photo.png')}, headers={'Authorization':'Bearer '+self.token_a})
            self.assertEqual(result.status_code,200)
            self.assertEqual(process.call_args.kwargs['category'],'benh_nhan')
            update.assert_called_once_with(101,'/static/uploads/benh_nhan/test.webp')
        with patch('core.image_service.process_image_input',return_value=(None,'Invalid image')):
            result=self.client.post('/api/v1/mobile/patient/profile/avatar',data={'avatar_url':'https://not-allowed.test/x'},headers={'Authorization':'Bearer '+self.token_a})
            self.assertEqual(result.status_code,400)


if __name__=='__main__':
    unittest.main()
