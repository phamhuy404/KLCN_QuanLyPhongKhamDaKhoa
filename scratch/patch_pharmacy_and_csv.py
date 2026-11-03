import sys
import os

# 1. Update models/pharmacy_model.py
with open('models/pharmacy_model.py', 'r', encoding='utf-8') as f:
    pm_code = f.read()

get_stock_func = '''    @staticmethod
    def get_stock_movements(limit=300):
        """Lấy danh sách chi tiết các biến động tăng/giảm kho thuốc (Nhập CSV hoặc Cấp phát đơn thanh toán)."""
        import json
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT a.id, a.row_id AS thuoc_id, a.action, a.performed_by, a.performed_by_name,
                       a.performed_at, a.reason, a.before_json, a.after_json,
                       t.ma_thuoc, t.ten_thuoc, t.don_vi_tinh, t.hoat_chat
                FROM audit_log a
                JOIN thuoc t ON a.row_id = t.id
                WHERE a.table_name = 'thuoc' AND a.action IN ('STOCK_IN', 'STOCK_OUT')
                ORDER BY a.id DESC
            """)
            rows = [dict(r) for r in cursor.fetchall()]
        except Exception:
            rows = []

        movements = []
        for r in rows[:limit]:
            try:
                after = json.loads(r.get('after_json') or '{}')
                before = json.loads(r.get('before_json') or '{}')
            except Exception:
                after, before = {}, {}

            delta = int(after.get('delta') or 0)
            receipt = after.get('receipt')
            action = r.get('action')
            reason = r.get('reason') or ''
            perf_at = str(r.get('performed_at') or '')

            # Xác định loại chứng từ đối chiếu
            doc_info = 'Nhập kho từ tệp CSV'
            if action == 'STOCK_OUT' and receipt:
                try:
                    pid = int(receipt)
                    cursor.execute("""
                        SELECT dt.ma_don_thuoc, bn.ho_ten AS ten_benh_nhan, hd.ma_hoa_don
                        FROM don_thuoc dt
                        JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                        JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                        LEFT JOIN hoa_don hd ON hd.phieu_kham_id = pk.id AND hd.ma_hoa_don LIKE 'HDT%'
                        WHERE dt.id = ?
                    """, (pid,))
                    p_row = cursor.fetchone()
                    if p_row:
                        doc_info = f"Đơn thuốc {p_row['ma_don_thuoc']} (HĐ: {p_row['ma_hoa_don'] or 'N/A'} - BN: {p_row['ten_benh_nhan']})"
                    else:
                        doc_info = f"Đơn thuốc #{pid}"
                except Exception:
                    doc_info = f"Đơn thuốc #{receipt}"
            elif 'initial' in reason.lower():
                doc_info = 'Khởi tạo ban đầu'
            elif 'csv' in reason.lower():
                doc_info = 'Nhập kho từ file CSV'

            movements.append({
                'id': r['id'],
                'thuoc_id': r['thuoc_id'],
                'ma_thuoc': r['ma_thuoc'],
                'ten_thuoc': r['ten_thuoc'],
                'don_vi_tinh': r['don_vi_tinh'] or 'Viên',
                'action': action,
                'delta': delta,
                'is_increase': delta > 0,
                'ton_truoc': before.get('stock', 0),
                'ton_sau': after.get('stock', 0),
                'thoi_gian': perf_at[:19],
                'ngay': perf_at[:10],
                'nguoi_thuc_hien': r.get('performed_by_name') or 'Dược sĩ quản lý kho',
                'chung_tu': doc_info,
                'ly_do': reason
            })

        conn.close()
        return movements
'''

if 'def get_stock_movements' not in pm_code:
    # Insert right before class end or after stock_history
    idx = pm_code.find('class PharmacyModel:')
    if idx != -1:
        # Find def stock_history
        hist_idx = pm_code.find('def stock_history')
        if hist_idx != -1:
            end_hist = pm_code.find('\n    @staticmethod', hist_idx)
            if end_hist != -1:
                pm_code = pm_code[:end_hist] + '\n' + get_stock_func + '\n' + pm_code[end_hist:]
            else:
                pm_code += '\n' + get_stock_func
        else:
            pm_code += '\n' + get_stock_func
    with open('models/pharmacy_model.py', 'w', encoding='utf-8') as f:
        f.write(pm_code)
    print("Added get_stock_movements to models/pharmacy_model.py")
else:
    print("get_stock_movements already exists in models/pharmacy_model.py")

# 2. Update controllers/admin_controller.py
with open('controllers/admin_controller.py', 'r', encoding='utf-8') as f:
    ac_code = f.read()

target_pharmacy = """    return render_template('admin/pharmacy.html', active_page='admin_pharmacy', medicines=medicines, prescriptions=prescriptions, stats=stats)"""
new_pharmacy = """    stock_movements = PharmacyModel.get_stock_movements()
    return render_template('admin/pharmacy.html', active_page='admin_pharmacy', medicines=medicines, prescriptions=prescriptions, stats=stats, stock_movements=stock_movements)"""

if target_pharmacy in ac_code:
    ac_code = ac_code.replace(target_pharmacy, new_pharmacy)
    with open('controllers/admin_controller.py', 'w', encoding='utf-8') as f:
        f.write(ac_code)
    print("Updated controllers/admin_controller.py pharmacy route")
elif new_pharmacy in ac_code:
    print("controllers/admin_controller.py already updated")
else:
    print("Target pharmacy not found in controllers/admin_controller.py")

print("Done step 1 and 2 of patch!")
