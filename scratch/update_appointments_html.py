import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'admin', 'appointments.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Cap nhat status mapping de nhan ca 'Chờ tiếp nhận' va 'Đã tiếp nhận'
old_status_mapping = """        let status = 'waiting';
        if (a.trang_thai === 'Đã khám' || a.trang_thai === 'Hoàn thành') status = 'completed';
        else if (a.trang_thai === 'Đã duyệt' || a.trang_thai === 'Đã xác nhận') status = 'confirmed';
        else if (a.trang_thai === 'Đã hủy') status = 'cancelled';"""

new_status_mapping = """        let status = 'waiting';
        if (a.trang_thai === 'Đã khám' || a.trang_thai === 'Hoàn thành') status = 'completed';
        else if (a.trang_thai === 'Đã tiếp nhận' || a.trang_thai === 'Đã duyệt' || a.trang_thai === 'Đã xác nhận') status = 'confirmed';
        else if (a.trang_thai === 'Đã hủy') status = 'cancelled';"""

if old_status_mapping in content:
    content = content.replace(old_status_mapping, new_status_mapping)

# 2. Them nut Tiep Nhan vao bang
old_action_block = """                        <a href="/admin/emr?patient_id=${app.patient_id}" 
                           class="w-7 h-7 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 flex items-center justify-center transition-colors" title="Bắt đầu khám (EMR)">
                            <i class="fa-solid fa-stethoscope text-xs"></i>
                        </a>"""

new_action_block = """                        ${app.trang_thai === 'waiting' ? `
                        <button type="button" onclick="acceptAppointment(${app.id}, '${app.ma_hen}')" 
                                class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm transition-all" title="Lễ tân/Admin xác nhận tiếp nhận lịch">
                            <i class="fa-solid fa-check"></i>
                            <span>Tiếp nhận</span>
                        </button>
                        ` : ''}
                        <a href="/admin/emr?patient_id=${app.patient_id}" 
                           class="w-7 h-7 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 flex items-center justify-center transition-colors" title="Bắt đầu khám (EMR)">
                            <i class="fa-solid fa-stethoscope text-xs"></i>
                        </a>"""

if old_action_block in content:
    content = content.replace(old_action_block, new_action_block)

# 3. Them ham acceptAppointment vao script
func_marker = "    // Chuyển đổi trạng thái hẹn qua API"
accept_func_code = """    // Lễ tân hoặc Admin xác nhận tiếp nhận lịch khám
    async function acceptAppointment(id, maHen) {
        if (!confirm(`Xác nhận tiếp nhận lịch hẹn #${maHen}? Hệ thống sẽ tự động gửi thông báo đến tài khoản bệnh nhân.`)) return;
        try {
            const res = await fetch('/api/appointment/status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, status: 'Đã tiếp nhận' })
            });
            const data = await res.json();
            if (data.success) {
                alert(`✅ Đã tiếp nhận thành công lịch khám #${maHen}! Thông báo tiếp nhận đã được gửi cho bệnh nhân.`);
                const app = appointments.find(a => a.id === id);
                if (app) app.trang_thai = 'confirmed';
                filterAppointments();
            } else {
                alert('Lỗi tiếp nhận lịch hẹn: ' + data.message);
            }
        } catch (err) {
            alert('Lỗi kết nối máy chủ: ' + err.message);
        }
    }

"""

if func_marker in content:
    content = content.replace(func_marker, accept_func_code + func_marker)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated templates/admin/appointments.html successfully!")
