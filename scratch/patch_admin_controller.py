import sys
import os

filepath = 'controllers/admin_controller.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    # Ưu tiên đưa bệnh nhân trong hàng đợi tiếp nhận hôm nay của bác sĩ lên đầu
    if user_role == 'BACSI' and doc_id:
        from core.database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT benh_nhan_id
            FROM lich_hen
            WHERE (bac_si_id = ? OR phong_kham_id IN (SELECT phong_kham_chinh_id FROM bac_si WHERE id = ?))
              AND CAST(ngay_hen AS DATE) = CAST(GETDATE() AS DATE)
              AND trang_thai IN (N'Đã tiếp nhận', N'Đã duyệt', N'Đã xác nhận', N'Đang khám', N'Chờ kết quả CLS')
        ''', (doc_id, doc_id))
        queue_ids = {r['benh_nhan_id'] for r in cursor.fetchall()}
        conn.close()
        queue_patients = [p for p in all_patients if p['id'] in queue_ids]
        other_patients = [p for p in all_patients if p['id'] not in queue_ids]
        patients_list = queue_patients + other_patients
    else:
        patients_list = all_patients"""

replacement = """    # Bác sĩ chỉ xem bệnh nhân thuộc phụ trách (có lịch hẹn hoặc từng khám)
    if user_role == 'BACSI' and doc_id:
        from core.database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT benh_nhan_id
            FROM lich_hen
            WHERE (bac_si_id = ? OR phong_kham_id IN (SELECT phong_kham_chinh_id FROM bac_si WHERE id = ?))
              AND CAST(ngay_hen AS DATE) = CAST(GETDATE() AS DATE)
              AND trang_thai IN (N'Đã tiếp nhận', N'Đã duyệt', N'Đã xác nhận', N'Đang khám', N'Chờ kết quả CLS')
        ''', (doc_id, doc_id))
        queue_ids = {r['benh_nhan_id'] for r in cursor.fetchall()}

        cursor.execute('''
            SELECT DISTINCT benh_nhan_id FROM lich_hen WHERE bac_si_id = ?
            UNION
            SELECT DISTINCT benh_nhan_id FROM phieu_kham WHERE bac_si_id = ?
        ''', (doc_id, doc_id))
        all_doc_patient_ids = {r['benh_nhan_id'] for r in cursor.fetchall()}
        conn.close()

        queue_patients = [p for p in all_patients if p['id'] in queue_ids]
        doc_other_patients = [p for p in all_patients if p['id'] in (all_doc_patient_ids - queue_ids)]
        patients_list = queue_patients + doc_other_patients
    else:
        patients_list = all_patients"""

target_crlf = target.replace('\r\n', '\n').replace('\n', '\r\n')
replacement_crlf = replacement.replace('\r\n', '\n').replace('\r\n', '\n') if '\r\n' not in content else replacement.replace('\r\n', '\n').replace('\n', '\r\n')

if target in content:
    content = content.replace(target, replacement)
    print("Replaced LF version")
elif target_crlf in content:
    content = content.replace(target_crlf, replacement_crlf)
    print("Replaced CRLF version")
else:
    print("Target not found!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin_controller.py successfully!")
