import sys
import os
from datetime import date, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Dam bao duong dan root co the import core va models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import get_db
from models.schedule_model import ScheduleModel
from models.notification_model import NotificationModel
from models.appointment_model import AppointmentModel
from models.medical_record_model import MedicalRecordModel
from models.billing_model import BillingModel

def run_tests():
    print("BAT DAU KIEM THU TOAN DIEN HE THONG THONG BAO VA DUYET LICH TRUC...")

    conn = get_db()
    cursor = conn.cursor()

    # 1. Kiem tra tai khoan Admin va Bac si
    cursor.execute("""
        SELECT TOP 1 t.id, t.username, nv.ho_ten 
        FROM tai_khoan t
        LEFT JOIN nhan_vien nv ON nv.tai_khoan_id = t.id
        WHERE t.vai_tro_id = 1
    """)
    admin_acc = cursor.fetchone()
    print(f"-> Admin account: {admin_acc['ho_ten'] or admin_acc['username']} (ID: {admin_acc['id']})")

    cursor.execute("""
        SELECT TOP 1 bs.id AS bac_si_id, bs.chuyen_khoa_id, ck.ten_khoa, nv.ho_ten, nv.tai_khoan_id
        FROM bac_si bs
        JOIN nhan_vien nv ON bs.nhan_vien_id = nv.id
        JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        WHERE bs.trang_thai_lam_viec = N'Đang làm việc'
    """)
    doc = cursor.fetchone()
    print(f"-> Doctor account: {doc['ho_ten']} (BS ID: {doc['bac_si_id']}, Khoa: {doc['ten_khoa']})")

    cursor.execute("SELECT TOP 1 id, ho_ten, tai_khoan_id FROM benh_nhan WHERE tai_khoan_id IS NOT NULL")
    patient = cursor.fetchone()
    print(f"-> Patient account: {patient['ho_ten']} (BN ID: {patient['id']}, TK ID: {patient['tai_khoan_id']})")

    # 2. Test gioi han 3 bac si cung khoa trong 1 ca
    bounds = ScheduleModel.get_week_bounds()
    test_date = bounds['next_week_1'][0] + timedelta(days=2) # Thu 4 tuan toi
    ca_lam = 1
    dept_id = doc['chuyen_khoa_id']

    cnt, max_cap, is_full = ScheduleModel.check_doctor_dept_capacity(test_date, ca_lam, dept_id)
    print(f"-> [Test 1] Capacity check: Khoa {dept_id} ca {ca_lam} ngay {test_date}: {cnt}/{max_cap} (is_full={is_full})")
    assert max_cap == 3, "Hạn mức bác sĩ cùng khoa phải là 3!"

    # 3. Test gui thong bao Admin & Le tan khi Benh nhan dat lich
    initial_admin_notifs = NotificationModel.get_user_notifications(admin_acc['id'], limit=5)
    init_admin_cnt = len(initial_admin_notifs)

    success, appt_res = AppointmentModel.create(
        benh_nhan_id=patient['id'],
        chuyen_khoa_id=dept_id,
        bac_si_id=doc['bac_si_id'],
        ngay_hen=str(test_date),
        gio_hen='08:30',
        ly_do_kham='Kiem tra suc khoe tong quat test notif'
    )
    print(f"-> [Test 2] Create Appointment: {success}, Result: {appt_res}")
    assert success, f"Tao lich hen that bai: {appt_res}"

    # Kiem tra admin nhan duoc thong bao dat lich chua
    admin_notifs_after = NotificationModel.get_user_notifications(admin_acc['id'], limit=5)
    new_admin_notif = admin_notifs_after[0] if admin_notifs_after else None
    print(f"-> [Test 3] Admin received notification: {new_admin_notif['tieu_de'] if new_admin_notif else 'None'}")
    assert new_admin_notif and 'Lịch hẹn khám mới' in new_admin_notif['tieu_de'], "Admin chưa nhận được thông báo đặt lịch mới!"

    # 4. Test tiep nhan lich hen -> thong bao cho bac si va benh nhan
    cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = ?", (appt_res,))
    appt_row = cursor.fetchone()
    appt_id = appt_row['id']

    stt_ok, stt_msg = AppointmentModel.update_status(appt_id, 'Đã tiếp nhận', user_info={'id': admin_acc['id'], 'ho_ten': 'Admin Test'})
    print(f"-> [Test 4] Update status to Đã tiếp nhận: {stt_ok}, {stt_msg}")
    assert stt_ok, "Tiep nhan lich hen that bai!"

    # Kiem tra bac si nhan duoc thong bao
    doc_notifs = NotificationModel.get_user_notifications(doc['tai_khoan_id'], limit=5)
    doc_latest = doc_notifs[0] if doc_notifs else None
    print(f"-> [Test 5] Doctor notification: {doc_latest['tieu_de'] if doc_latest else 'None'}")
    assert doc_latest and 'Lịch khám mới tiếp nhận' in doc_latest['tieu_de'], "Bác sĩ chưa nhận được thông báo lịch khám tiếp nhận!"

    # 5. Test Dang ky ca lam va Duyet hang loat (Bulk approve) voi gom nhom 1 thong bao duy nhat
    import random
    bulk_test_date1 = date.today() + timedelta(days=random.randint(40, 80))
    bulk_test_date2 = bulk_test_date1 + timedelta(days=1)
    cursor.execute("""
        INSERT INTO lich_lam_viec (nhan_vien_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai, trang_thai_duyet, ghi_chu)
        VALUES ((SELECT nhan_vien_id FROM bac_si WHERE id = ?), ?, 1, ?, 3, '17:30:00', '20:30:00', 20, 0, 1, 'CHO_DUYET', N'Test duyet ca 1'),
               ((SELECT nhan_vien_id FROM bac_si WHERE id = ?), ?, 1, ?, 3, '17:30:00', '20:30:00', 20, 0, 1, 'CHO_DUYET', N'Test duyet ca 2')
    """, (doc['bac_si_id'], doc['bac_si_id'], str(bulk_test_date1), doc['bac_si_id'], doc['bac_si_id'], str(bulk_test_date2)))
    conn.commit()

    # Tim ID cac ca vua tao CHO_DUYET
    cursor.execute("""
        SELECT TOP 2 id FROM lich_lam_viec
        WHERE bac_si_id = ? AND trang_thai_duyet = 'CHO_DUYET'
        ORDER BY id DESC
    """, (doc['bac_si_id'],))
    pending_shift_ids = [r['id'] for r in cursor.fetchall()]
    print(f"-> [Test 7] Pending shift IDs to bulk approve: {pending_shift_ids}")

    assert len(pending_shift_ids) >= 2, "Phải có ít nhất 2 ca chờ duyệt để kiểm tra bulk approve!"

    prev_doc_notif_count = len(NotificationModel.get_user_notifications(doc['tai_khoan_id'], limit=50))
    bulk_ok, bulk_msg, bulk_cnt = ScheduleModel.bulk_approve_schedules(pending_shift_ids, reviewer_user={'id': admin_acc['id'], 'vai_tro': 'ADMIN'}, approved=True)
    print(f"-> [Test 8] Bulk approve result: {bulk_ok}, {bulk_msg}, count={bulk_cnt}")
    assert bulk_ok, "Duyệt hàng loạt thất bại!"

    # Kiểm tra bác sĩ chỉ nhận đúng 1 thông báo duy nhất sau khi duyệt hàng loạt 2 ca
    doc_notifs_after_bulk = NotificationModel.get_user_notifications(doc['tai_khoan_id'], limit=50)
    diff_count = len(doc_notifs_after_bulk) - prev_doc_notif_count
    latest_after_bulk = doc_notifs_after_bulk[0]
    print(f"-> [Test 9] Doctor new notifications count after bulk approve: {diff_count} (Title: {latest_after_bulk['tieu_de']}, Message: {latest_after_bulk['noi_dung']})")
    assert diff_count == 1, f"Bác sĩ phải nhận đúng 1 thông báo duy nhất sau khi duyệt hàng loạt, thực tế nhận: {diff_count}"
    assert latest_after_bulk['noi_dung'] == "Lịch làm việc của bạn đã được phê duyệt thành công!", "Nội dung thông báo duyệt lịch phải đúng yêu cầu!"

    # 6. Test Polling API
    poll_data = NotificationModel.get_poll_updates(patient['tai_khoan_id'], last_id=0)
    print(f"-> [Test 10] Polling API: unread_count={poll_data['unread_count']}, recent_count={len(poll_data['recent_list'])}")
    assert 'unread_count' in poll_data and 'recent_list' in poll_data, "Polling API thieu du lieu chuan!"

    conn.close()
    print("TAT CA CAC BAI KIEM THU DEU DA PASS 100% THANH CONG!")

if __name__ == '__main__':
    run_tests()
