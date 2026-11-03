import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'templates', 'admin', 'backups.html')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

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

if "async function handleToggleMaintenance" not in content:
    idx = content.rfind('</script>')
    if idx != -1:
        content = content[:idx] + js_handlers + "\n" + content[idx:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully added handleToggleMaintenance to backups.html")
    else:
        print("</script> not found")
else:
    print("Function already present")
