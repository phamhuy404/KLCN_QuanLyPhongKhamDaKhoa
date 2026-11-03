import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db

conn = get_db()
cur = conn.cursor()

print("KIEM TRA TOAN VEN KHOA NGOAI CSDL:")

# 1. Tai khoan theo vai tro
cur.execute("""
    SELECT vt.ma_vai_tro, vt.ten_vai_tro, COUNT(tk.id) AS so_luong
    FROM vai_tro vt
    LEFT JOIN tai_khoan tk ON vt.id = tk.vai_tro_id
    GROUP BY vt.ma_vai_tro, vt.ten_vai_tro
""")
print("\n1. Phân bổ vai trò tài khoản:")
for r in cur.fetchall():
    print(f"   - {r['ma_vai_tro']:<10} ({r['ten_vai_tro']}): {r['so_luong']} tài khoản")

# 2. Mo coi lich lam viec
cur.execute("SELECT COUNT(*) AS cnt FROM lich_lam_viec WHERE nhan_vien_id IS NULL OR nhan_vien_id NOT IN (SELECT id FROM nhan_vien)")
orphan_schedules = cur.fetchone()['cnt']
print(f"\n2. Ca trực mồ côi (không có nhân viên): {orphan_schedules}")

# 3. Mo coi phieu kham
cur.execute("SELECT COUNT(*) AS cnt FROM phieu_kham WHERE benh_nhan_id NOT IN (SELECT id FROM benh_nhan)")
orphan_records_bn = cur.fetchone()['cnt']
cur.execute("SELECT COUNT(*) AS cnt FROM phieu_kham WHERE bac_si_id NOT IN (SELECT id FROM bac_si)")
orphan_records_bs = cur.fetchone()['cnt']
print(f"3. Phiếu khám mồ côi BN: {orphan_records_bn} | Mồ côi BS: {orphan_records_bs}")

# 4. Mo coi don thuoc
cur.execute("SELECT COUNT(*) AS cnt FROM don_thuoc WHERE phieu_kham_id NOT IN (SELECT id FROM phieu_kham)")
orphan_prescriptions = cur.fetchone()['cnt']
cur.execute("SELECT COUNT(*) AS cnt FROM chi_tiet_don_thuoc WHERE thuoc_id NOT IN (SELECT id FROM thuoc)")
orphan_presc_items = cur.fetchone()['cnt']
print(f"4. Đơn thuốc mồ côi Phiếu khám: {orphan_prescriptions} | Chi tiết mồ côi Thuốc: {orphan_presc_items}")

# 5. Mo coi chi dinh CLS
cur.execute("SELECT COUNT(*) AS cnt FROM phieu_chi_dinh WHERE phieu_kham_id NOT IN (SELECT id FROM phieu_kham)")
orphan_labs = cur.fetchone()['cnt']
cur.execute("SELECT COUNT(*) AS cnt FROM chi_tiet_chi_dinh WHERE dich_vu_id NOT IN (SELECT id FROM dich_vu)")
orphan_lab_items = cur.fetchone()['cnt']
print(f"5. Phiếu chỉ định mồ côi Phiếu khám: {orphan_labs} | Chi tiết mồ côi Dịch vụ: {orphan_lab_items}")

# 6. Mo coi hoa don
cur.execute("SELECT COUNT(*) AS cnt FROM hoa_don WHERE benh_nhan_id NOT IN (SELECT id FROM benh_nhan)")
orphan_invoices = cur.fetchone()['cnt']
cur.execute("SELECT COUNT(*) AS cnt FROM chi_tiet_hoa_don WHERE hoa_don_id NOT IN (SELECT id FROM hoa_don)")
orphan_invoice_items = cur.fetchone()['cnt']
print(f"6. Hóa đơn mồ côi BN: {orphan_invoices} | Chi tiết mồ côi Hóa đơn: {orphan_invoice_items}")

# 7. Thong ke doanh thu thuc te
cur.execute("SELECT trang_thai, COUNT(*) AS so_luong, SUM(tong_tien) AS tong_tien, SUM(thanh_tien) AS thanh_tien FROM hoa_don GROUP BY trang_thai")
print("\n7. Thống kê hóa đơn viện phí theo trạng thái:")
for r in cur.fetchall():
    print(f"   - {r['trang_thai']:<20}: {r['so_luong']} HĐ | Tổng giá trị: {float(r['tong_tien'] or 0):,.0f} đ | Thực thu BN: {float(r['thanh_tien'] or 0):,.0f} đ")

# 8. Thong ke lich hen
cur.execute("SELECT trang_thai, COUNT(*) AS so_luong FROM lich_hen GROUP BY trang_thai")
print("\n8. Thống kê lịch hẹn khám theo trạng thái:")
for r in cur.fetchall():
    print(f"   - {r['trang_thai']:<25}: {r['so_luong']} lượt hẹn")

# 9. Thong ke phan hoi
cur.execute("SELECT diem_danh_gia, COUNT(*) AS so_luong FROM phan_hoi GROUP BY diem_danh_gia ORDER BY diem_danh_gia DESC")
print("\n9. Thống kê đánh giá của bệnh nhân:")
for r in cur.fetchall():
    print(f"   - {r['diem_danh_gia']} sao: {r['so_luong']} lượt đánh giá")

conn.close()
