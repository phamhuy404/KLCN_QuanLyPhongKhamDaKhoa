import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'templates', 'admin', 'backups.html')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Nâng cấp Modal Xác nhận Phục hồi với animate-modal-up
content = content.replace('animate-scale-up', 'animate-modal-up')

# 2. Khối Bảo Trì Hệ Thống & Kiểm Soát Nâng Cấp
maintenance_section = """
    <!-- Khối Quản Trị Bảo Trì Hệ Thống & Kiểm Soát Nâng Cấp -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div class="px-6 py-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <div class="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-1">
                    <i class="fa-solid fa-power-off"></i> Trung Tâm Kiểm Soát & Bảo Trì Hệ Thống
                </div>
                <h3 class="text-xl font-bold text-white flex items-center gap-2">
                    <span>Chế Độ Bảo Trì & Nâng Cấp Độc Lập</span>
                    <span class="text-xs bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 px-2.5 py-0.5 rounded-full font-semibold">
                        Nâng Cấp Dần
                    </span>
                </h3>
                <p class="text-slate-300 text-xs mt-1 max-w-2xl leading-relaxed">
                    Bật/tắt bảo trì độc lập để chặn truy cập cho từng nhóm người dùng khi cần bảo trì máy chủ hoặc nâng cấp nghiệp vụ. Quản trị viên (ADMIN) luôn có toàn quyền truy cập để nâng cấp hệ thống.
                </p>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-xs px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1.5">
                    <i class="fa-solid fa-user-shield text-emerald-400"></i> Admin Miễn Trừ 100%
                </span>
            </div>
        </div>

        <div class="p-6 space-y-6">
            <!-- 2 Thẻ Toggle Lớn: Bệnh nhân & Nhân viên -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
                
                <!-- Card 1: Bảo Trì Cổng Bệnh Nhân -->
                <div id="card-maint-patient" class="p-5 rounded-2xl border transition-all duration-300 {% if system_settings.maintenance_patient %}bg-rose-50/70 border-rose-300 shadow-md shadow-rose-500/5{% else %}bg-slate-50/70 border-slate-200{% endif %}">
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-center gap-3">
                            <div class="w-11 h-11 rounded-xl {% if system_settings.maintenance_patient %}bg-rose-600 text-white{% else %}bg-medical-100 text-medical-700{% endif %} flex items-center justify-center text-xl shrink-0 transition-colors" id="icon-maint-patient">
                                <i class="fa-solid fa-hospital-user"></i>
                            </div>
                            <div>
                                <h4 class="text-base font-bold text-slate-800">Cổng Dịch Vụ Bệnh Nhân</h4>
                                <p class="text-xs text-slate-500">Đăng ký, đặt khám trực tuyến & hồ sơ bệnh nhân</p>
                            </div>
                        </div>

                        <!-- Toggle Switch Button -->
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="toggle-maint-patient" onchange="handleToggleMaintenance('patient', this.checked)" class="sr-only peer" {% if system_settings.maintenance_patient %}checked{% endif %}>
                            <div class="w-14 h-7 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[4px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-rose-600 transition-colors shadow-inner"></div>
                        </label>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-200/80 flex items-center justify-between text-xs">
                        <div class="flex items-center gap-2" id="status-badge-patient">
                            {% if system_settings.maintenance_patient %}
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200">
                                <span class="w-2 h-2 rounded-full bg-rose-600 animate-ping"></span>
                                <span>ĐANG BẬT BẢO TRÌ (ĐÃ CHẶN)</span>
                            </span>
                            {% else %}
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 font-bold border border-emerald-200">
                                <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                                <span>Hoạt Động Bình Thường</span>
                            </span>
                            {% endif %}
                        </div>

                        <a href="/maintenance/patient?preview=1" target="_blank" class="inline-flex items-center gap-1.5 text-slate-600 hover:text-indigo-600 font-semibold transition-colors">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Xem trước trang BN
                        </a>
                    </div>
                </div>

                <!-- Card 2: Bảo Trì Phân Hệ Nhân Viên Y Tế -->
                <div id="card-maint-staff" class="p-5 rounded-2xl border transition-all duration-300 {% if system_settings.maintenance_staff %}bg-rose-50/70 border-rose-300 shadow-md shadow-rose-500/5{% else %}bg-slate-50/70 border-slate-200{% endif %}">
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-center gap-3">
                            <div class="w-11 h-11 rounded-xl {% if system_settings.maintenance_staff %}bg-rose-600 text-white{% else %}bg-indigo-100 text-indigo-700{% endif %} flex items-center justify-center text-xl shrink-0 transition-colors" id="icon-maint-staff">
                                <i class="fa-solid fa-user-doctor"></i>
                            </div>
                            <div>
                                <h4 class="text-base font-bold text-slate-800">Phân Hệ Nhân Viên Y Tế</h4>
                                <p class="text-xs text-slate-500">Bác sĩ khám EMR, Lễ tân tiếp nhận, Dược sĩ, KTV</p>
                            </div>
                        </div>

                        <!-- Toggle Switch Button -->
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="toggle-maint-staff" onchange="handleToggleMaintenance('staff', this.checked)" class="sr-only peer" {% if system_settings.maintenance_staff %}checked{% endif %}>
                            <div class="w-14 h-7 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[4px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-rose-600 transition-colors shadow-inner"></div>
                        </label>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-200/80 flex items-center justify-between text-xs">
                        <div class="flex items-center gap-2" id="status-badge-staff">
                            {% if system_settings.maintenance_staff %}
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200">
                                <span class="w-2 h-2 rounded-full bg-rose-600 animate-ping"></span>
                                <span>ĐANG BẬT BẢO TRÌ (ĐÃ CHẶN)</span>
                            </span>
                            {% else %}
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 font-bold border border-emerald-200">
                                <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                                <span>Hoạt Động Bình Thường</span>
                            </span>
                            {% endif %}
                        </div>

                        <a href="/maintenance/staff?preview=1" target="_blank" class="inline-flex items-center gap-1.5 text-slate-600 hover:text-indigo-600 font-semibold transition-colors">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Xem trước trang NV
                        </a>
                    </div>
                </div>

            </div>

            <!-- Cấu Hình Chi Tiết Thông Điệp & Thời Gian Dự Kiến Hoàn Thành -->
            <div class="bg-slate-50 rounded-2xl border border-slate-200/90 p-5">
                <div class="flex items-center justify-between mb-4">
                    <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <i class="fa-solid fa-sliders text-indigo-600"></i>
                        <span>Tùy Chỉnh Thông Điệp & Thời Gian Dự Kiến Nâng Cấp</span>
                    </h4>
                    <span class="text-xs text-slate-400">Hiển thị tức thì trên cả 2 trang bảo trì</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1.5">
                            Thời Gian Hoàn Thành Dự Kiến (ETA)
                        </label>
                        <input type="text" id="maint-input-eta" value="{{ system_settings.maintenance_eta or '23:00 Hôm nay' }}" placeholder="VD: 23:00 Hôm nay, hoặc 30 phút nữa..." class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1.5">
                            Hotline Hỗ Trợ Khẩn Cấp / Trực Ban
                        </label>
                        <input type="text" id="maint-input-hotline" value="{{ system_settings.maintenance_hotline or '1900 1234 - (028) 3810 0000' }}" placeholder="Số hotline cấp cứu hoặc trực ban IT..." class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1.5">
                            Lời Nhắn Gửi Bệnh Nhân (Cổng Bệnh nhân)
                        </label>
                        <textarea id="maint-input-msg-patient" rows="2" class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 resize-none">{{ system_settings.maintenance_message_patient or '' }}</textarea>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-700 mb-1.5">
                            Lời Nhắn Gửi Nhân Viên Y Tế (Phân hệ HIS/EMR)
                        </label>
                        <textarea id="maint-input-msg-staff" rows="2" class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 resize-none">{{ system_settings.maintenance_message_staff or '' }}</textarea>
                    </div>
                </div>

                <div class="mt-4 flex justify-end">
                    <button type="button" onclick="handleSaveMaintenanceSettings()" id="btn-save-maint" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/25 flex items-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99]">
                        <i class="fa-solid fa-floppy-disk"></i>
                        <span>Lưu Cập Nhật Cấu Hình Bảo Trì</span>
                    </button>
                </div>
            </div>

        </div>
    </div>
"""

# Chèn khối bảo trì ngay trước <!-- Main Section: Danh Sách File Sao Lưu Khả Dụng -->
target_section = '    <!-- Main Section: Danh Sách File Sao Lưu Khả Dụng -->'
if target_section in content:
    content = content.replace(target_section, maintenance_section + '\n' + target_section)
    print("Inserted maintenance section into backups.html")
else:
    print("Target section not found")

# 3. Bổ sung các hàm JS xử lý Toggle và Update cấu hình bảo trì vào cuối script
js_handlers = """
async function handleToggleMaintenance(target, enabled) {
    try {
        const res = await fetch('/api/maintenance/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ target, enabled })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            // Cập nhật giao diện thẻ tương ứng
            const card = document.getElementById(target === 'patient' ? 'card-maint-patient' : 'card-maint-staff');
            const icon = document.getElementById(target === 'patient' ? 'icon-maint-patient' : 'icon-maint-staff');
            const badge = document.getElementById(target === 'patient' ? 'status-badge-patient' : 'status-badge-staff');
            
            if (enabled) {
                card.className = 'p-5 rounded-2xl border transition-all duration-300 bg-rose-50/70 border-rose-300 shadow-md shadow-rose-500/5';
                icon.className = 'w-11 h-11 rounded-xl bg-rose-600 text-white flex items-center justify-center text-xl shrink-0 transition-colors';
                badge.innerHTML = `
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-100 text-rose-700 font-bold border border-rose-200">
                        <span class="w-2 h-2 rounded-full bg-rose-600 animate-ping"></span>
                        <span>ĐANG BẬT BẢO TRÌ (ĐÃ CHẶN)</span>
                    </span>`;
            } else {
                card.className = 'p-5 rounded-2xl border transition-all duration-300 bg-slate-50/70 border-slate-200';
                icon.className = target === 'patient' 
                    ? 'w-11 h-11 rounded-xl bg-medical-100 text-medical-700 flex items-center justify-center text-xl shrink-0 transition-colors'
                    : 'w-11 h-11 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center text-xl shrink-0 transition-colors';
                badge.innerHTML = `
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 font-bold border border-emerald-200">
                        <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                        <span>Hoạt Động Bình Thường</span>
                    </span>`;
            }
        } else {
            showToast(data.message || 'Lỗi khi cập nhật trạng thái bảo trì!', 'error');
            // Rollback checkbox
            document.getElementById(target === 'patient' ? 'toggle-maint-patient' : 'toggle-maint-staff').checked = !enabled;
        }
    } catch (err) {
        showToast('Lỗi mạng: ' + err.message, 'error');
        document.getElementById(target === 'patient' ? 'toggle-maint-patient' : 'toggle-maint-staff').checked = !enabled;
    }
}

async function handleSaveMaintenanceSettings() {
    const btn = document.getElementById('btn-save-maint');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang lưu...';

    const payload = {
        maintenance_eta: document.getElementById('maint-input-eta').value,
        maintenance_hotline: document.getElementById('maint-input-hotline').value,
        maintenance_message_patient: document.getElementById('maint-input-msg-patient').value,
        maintenance_message_staff: document.getElementById('maint-input-msg-staff').value
    };

    try {
        const res = await fetch('/api/maintenance/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast('Đã lưu cấu hình bảo trì thành công!', 'success');
        } else {
            showToast(data.message || 'Lỗi khi lưu cấu hình bảo trì!', 'error');
        }
    } catch (err) {
        showToast('Lỗi mạng: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
"""

if "handleToggleMaintenance" not in content:
    content = content.replace("</script>\n{% endblock %}", js_handlers + "\n</script>\n{% endblock %}")
    print("Added JavaScript handlers to backups.html")
else:
    print("JS handlers already in backups.html")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("backups.html updated successfully!")
