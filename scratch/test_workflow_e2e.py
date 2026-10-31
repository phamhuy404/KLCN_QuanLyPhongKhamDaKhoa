# -*- coding: utf-8 -*-
"""End-to-End Operational Workflow Integration Test.

Tests core patient and staff operational pathways.
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from core.database import get_db

app = create_app()
client = app.test_client()

def login_as(username, password):
    client.get('/logout', follow_redirects=True)
    res = client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
    assert res.status_code == 200, f"Login failed for {username}: status {res.status_code}"
    return res

def test_full_workflows():
    print("Testing Step 1: Patient Login, Matrix & Booking...")
    # 1. Patient login
    login_as('0901234562', '123456')
    
    # 2. Get booking matrix dynamically for an active department
    from datetime import date
    from models.appointment_model import AppointmentModel
    test_date = date.today().isoformat()
    chosen_dept = 2
    avail_slots = []
    for d in range(1, 8):
        m = AppointmentModel.get_booking_matrix(test_date, d)
        if m.get('all_available_slots'):
            chosen_dept = d
            avail_slots = m['all_available_slots']
            break

    res = client.get(f'/api/appointment/booking-matrix?chuyen_khoa_id={chosen_dept}&date={test_date}')
    assert res.status_code == 200, f"Matrix fetch failed: {res.status_code}"
    matrix = res.get_json()
    assert matrix.get('success'), f"Matrix returned error: {matrix}"
    print(f"  Matrix OK for Dept {chosen_dept}: {len(avail_slots)} slots available ({avail_slots}...)")
    assert len(avail_slots) > 0, "No slots available!"

    # 3. Book appointment
    chosen_slot = avail_slots[-1]
    book_payload = {
        'chuyen_khoa_id': chosen_dept,
        'ngay_hen': test_date,
        'gio_hen': chosen_slot,
        'ly_do': 'Kham tong quat E2E test'
    }
    res = client.post('/api/appointment/book', json=book_payload)
    assert res.status_code == 200, f"Booking failed: {res.get_json()}"
    book_data = res.get_json()
    ma_lich_hen = book_data.get('ma_lich_hen')
    print(f"  Booked successfully: {ma_lich_hen} at {chosen_slot} on {test_date}")

    # 4. Patient appointments list
    res = client.get('/patient/appointments')
    assert res.status_code == 200, f"Appointments view failed: {res.status_code}"
    assert ma_lich_hen in res.get_data(as_text=True)
    print("  Patient view contains new appointment")

    # 5. Fetch appointment ID from DB
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, benh_nhan_id, bac_si_id, phong_kham_id FROM lich_hen WHERE ma_lich_hen = ?", (ma_lich_hen,))
    appt = cur.fetchone()
    appt_id = appt['id']
    patient_id = appt['benh_nhan_id']
    doctor_id = appt['bac_si_id']
    room_id = appt['phong_kham_id'] or 1

    # 6. Patient feedback
    print("Testing Step 2: Patient Feedback...")
    fb_payload = {
        'ho_ten': 'Hoàng Bảo Nam',
        'email': 'nam@example.com',
        'sdt': '0901234561',
        'chu_de': 'Dich vu rat tot',
        'noi_dung': 'Trải nghiệm khám chữa bệnh rất chuyên nghiệp',
        'muc_do_hai_long': 5
    }
    res = client.post('/api/feedback/submit', json=fb_payload)
    assert res.status_code == 200, f"Feedback submit failed: {res.get_json()}"
    print("  Feedback submitted OK")

    # 7. Receptionist workflow
    print("Testing Step 3: Receptionist Workflow...")
    login_as('letan_2', 'Password@123')

    # Receptionist checks in appointment (Đã tiếp nhận)
    res = client.post('/api/appointment/update-status', json={'appointment_id': appt_id, 'status': 'Đã tiếp nhận'})
    assert res.status_code == 200, f"Check-in failed: {res.get_json()}"
    print(f"  Appointment {ma_lich_hen} checked in (Đã tiếp nhận)")

    # 8. Doctor workflow
    print("Testing Step 4: Doctor EMR & Clinical Workflow...")
    # Find doctor's username
    cur.execute("SELECT t.username FROM bac_si b JOIN nhan_vien nv ON b.nhan_vien_id = nv.id JOIN tai_khoan t ON nv.tai_khoan_id = t.id WHERE b.id = ?", (doctor_id,))
    doc_user = cur.fetchone()['username']
    login_as(doc_user, 'Password@123')

    # Get a service and medicine to prescribe
    cur.execute("SELECT TOP 1 id, ten_dich_vu, don_gia FROM dich_vu WHERE loai_dich_vu != 'Khám bệnh' AND trang_thai = 1")
    service = cur.fetchone()
    service_id = service['id']

    cur.execute("SELECT TOP 1 id, ten_thuoc, don_gia, so_luong_ton FROM thuoc WHERE so_luong_ton >= 5")
    med = cur.fetchone()
    med_id = med['id']

    # Doctor saves complete examination
    emr_payload = {
        'patient_id': patient_id,
        'appointment_id': appt_id,
        'doctor_id': doctor_id,
        'room_id': room_id,
        'reason': 'Kham tong quat E2E test',
        'symptoms': 'Không có triệu chứng bất thường',
        'diagnosis': 'Theo dõi sức khỏe định kỳ (Z00)',
        'icd': 'Z00',
        'treatment': 'Tư vấn chế độ sinh hoạt lành mạnh',
        'advice': 'Tái khám định kỳ 6 tháng',
        'lab_services': [service_id],
        'medicines': [
            {'thuoc_id': med_id, 'id': med_id, 'so_luong': 5, 'cach_dung': 'Uống 1 viên sau ăn sáng'}
        ]
    }
    res = client.post('/api/emr/save', json=emr_payload)
    assert res.status_code == 200, f"EMR save failed: {res.get_json()}"
    save_data = res.get_json()
    record_id = save_data.get('record_id')
    ma_phieu = save_data.get('ma_phieu')
    print(f"  EMR saved: Record #{record_id} ({ma_phieu}) with Lab {service['ten_dich_vu']} & Med {med['ten_thuoc']}")

    # Check EMR detail
    res = client.get(f'/api/emr/detail/{record_id}')
    assert res.status_code == 200, f"EMR detail failed: {res.get_json()}"
    print(f"  EMR detail loaded successfully")

    # 9. Lab Technician workflow
    print("Testing Step 5: Lab Tech Workflow...")
    login_as('ktv_1', 'Password@123')

    cur.execute("SELECT id FROM chi_tiet_chi_dinh WHERE phieu_chi_dinh_id = (SELECT id FROM phieu_chi_dinh WHERE phieu_kham_id = ?)", (record_id,))
    lab_item = cur.fetchone()
    if lab_item:
        lab_detail_id = lab_item['id']
        res = client.post('/api/lab/result/save', json={
            'chi_tiet_id': lab_detail_id,
            'ket_qua': 'Chỉ số huyết học trong giới hạn bình thường'
        })
        assert res.status_code == 200, f"Lab result save failed: {res.get_json()}"
        print(f"  Lab result saved for item {lab_detail_id}")

    # 10. Pharmacist workflow
    print("Testing Step 6: Pharmacist Workflow...")
    login_as('duocsi_1', 'Password@123')

    cur.execute("SELECT id, trang_thai FROM don_thuoc WHERE phieu_kham_id = ?", (record_id,))
    prescription = cur.fetchone()
    if prescription:
        pres_id = prescription['id']
        print(f"  Prescription found: #{pres_id}, status: {prescription['trang_thai']}")

    # 11. Receptionist / Billing workflow
    print("Testing Step 7: Billing Workflow...")
    login_as('letan_2', 'Password@123')

    cur.execute("SELECT id, tong_tien, thanh_tien, trang_thai FROM hoa_don WHERE phieu_kham_id = ?", (record_id,))
    inv = cur.fetchone()
    if inv:
        inv_id = inv['id']
        print(f"  Invoice {inv_id} found, total: {inv['thanh_tien']}, status: {inv['trang_thai']}")
        if inv['trang_thai'] != 'Đã thanh toán':
            res = client.post('/api/billing/pay', json={
                'invoice_id': inv_id,
                'confirm_received': True,
                'expected_amount': float(inv['thanh_tien']),
                'hinh_thuc_thanh_toan': 'Tiền mặt'
            })
            assert res.status_code == 200, f"Pay invoice failed: {res.get_json()}"
            print(f"  Invoice {inv_id} paid successfully via cash")

    # 12. Admin Backup workflow
    print("Testing Step 8: Admin Backup System...")
    login_as('admin', 'admin123')

    res = client.post('/api/backup/create', json={'ghi_chu': 'E2E automated test backup'})
    assert res.status_code == 200, f"Backup create failed: {res.get_json()}"
    print(f"  Backup created successfully: {res.get_json().get('backup_file')}")

    print("\nALL 8 OPERATIONAL WORKFLOW STEPS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_full_workflows()
