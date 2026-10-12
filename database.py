# database.py - Cầu nối tương thích ngược (Backward Compatibility Layer) sang cấu trúc MVC
from core.database import get_db, init_db, init_sqlite_db, UnifiedConnection, UnifiedCursor
from models.user_model import UserModel
from models.patient_model import PatientModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.pharmacy_model import PharmacyModel
from models.billing_model import BillingModel
from models.article_model import ArticleModel
from models.clinic_model import ClinicModel

# Ánh xạ các hàm DAO cũ sang các Model trong cấu trúc MVC
authenticate_user = UserModel.authenticate
register_patient_account = UserModel.register_patient
reset_patient_password = UserModel.reset_patient_password
get_all_patients = PatientModel.get_all
get_patient_by_id = PatientModel.get_by_id
get_patient_history = PatientModel.get_patient_history
get_all_appointments = AppointmentModel.get_all
create_appointment = AppointmentModel.create
get_all_medicines = PharmacyModel.get_all_medicines
get_all_services = ClinicModel.get_all_services
get_all_invoices = BillingModel.get_all
get_all_lab_orders = MedicalRecordModel.get_all_lab_orders
get_all_prescriptions = MedicalRecordModel.get_all_prescriptions
get_articles = ArticleModel.get_all
get_dashboard_stats = ClinicModel.get_dashboard_stats

if __name__ == '__main__':
    init_db()
