import sys
import os

filepath = 'templates/admin/emr.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Stepper buttons HTML to allow clicking and show read-only banner
old_stepper = """            <!-- THANH TIẾN TRÌNH CÁC BƯỚC KHÁM TÁCH BIỆT (KHÓA CHỌN TỰ DO, ĐIỀU HƯỚNG TUẦN TỰ) -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 border-b border-slate-100 pb-3 text-xs font-semibold select-none">
                <div id="step-btn-1" class="p-2.5 rounded-xl bg-medical-50 text-medical-700 font-bold border border-medical-200 transition-all flex items-center gap-2 text-left cursor-default pointer-events-none">
                    <span class="w-6 h-6 rounded-lg bg-medical-600 text-white flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-1">1</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 1</span>
                        <span class="truncate block font-bold">Khám Lâm Sàng</span>
                    </div>
                </div>

                <div id="step-btn-2" class="p-2.5 rounded-xl bg-slate-50 text-slate-600 border border-slate-200/80 transition-all flex items-center gap-2 text-left cursor-default pointer-events-none">
                    <span class="w-6 h-6 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-2">2</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 2</span>
                        <span class="truncate block font-bold">Khám Khoa & CLS</span>
                    </div>
                </div>

                <div id="step-btn-3" class="p-2.5 rounded-xl bg-slate-50 text-slate-600 border border-slate-200/80 transition-all flex items-center gap-2 text-left cursor-default pointer-events-none">
                    <span class="w-6 h-6 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-3">3</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 3</span>
                        <span class="truncate block font-bold">Kết Quả CLS</span>
                    </div>
                </div>

                <div id="step-btn-4" class="p-2.5 rounded-xl bg-slate-50 text-slate-600 border border-slate-200/80 transition-all flex items-center gap-2 text-left cursor-default pointer-events-none">
                    <span class="w-6 h-6 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-4">4</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 4</span>
                        <span class="truncate block font-bold">Kê Đơn Thuốc</span>
                    </div>
                </div>
            </div>"""

new_stepper = """            {% if session.get('user', {}).get('vai_tro') in ['ADMIN', 'LETAN'] %}
            <!-- Dải thông báo Chế độ xem chỉ đọc cho Quản trị viên / Tiếp tân -->
            <div id="emr-readonly-banner" class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center justify-between shadow-2xs">
                <div class="flex items-center gap-2 font-semibold">
                    <i class="fa-solid fa-eye text-amber-600 text-sm"></i>
                    <span>Chế độ Xem Bệnh Án (Dành cho Quản trị viên / Tiếp tân - Xem toàn bộ các bước hồ sơ y tế, không chỉnh sửa chuyên môn)</span>
                </div>
                <span class="text-[11px] bg-amber-100 text-amber-900 px-2.5 py-0.5 rounded-full font-bold">Chế độ Chỉ đọc</span>
            </div>
            {% endif %}

            <!-- THANH TIẾN TRÌNH CÁC BƯỚC KHÁM (HỖ TRỢ CLICK CHUYỂN BƯỚC TRỰC QUAN) -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 border-b border-slate-100 pb-3 text-xs font-semibold select-none">
                <div id="step-btn-1" onclick="clickEmrStep(1)" class="p-2.5 rounded-xl bg-medical-50 text-medical-700 font-bold border border-medical-200 transition-all flex items-center gap-2 text-left cursor-pointer hover:bg-medical-100/60 shadow-2xs">
                    <span class="w-6 h-6 rounded-lg bg-medical-600 text-white flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-1">1</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 1</span>
                        <span class="truncate block font-bold">Khám Lâm Sàng</span>
                    </div>
                </div>

                <div id="step-btn-2" onclick="clickEmrStep(2)" class="p-2.5 rounded-xl bg-slate-50 text-slate-600 border border-slate-200/80 transition-all flex items-center gap-2 text-left cursor-pointer hover:bg-slate-100">
                    <span class="w-6 h-6 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-2">2</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 2</span>
                        <span class="truncate block font-bold">Khám Khoa & CLS</span>
                    </div>
                </div>

                <div id="step-btn-3" onclick="clickEmrStep(3)" class="p-2.5 rounded-xl bg-slate-50 text-slate-600 border border-slate-200/80 transition-all flex items-center gap-2 text-left cursor-pointer hover:bg-slate-100">
                    <span class="w-6 h-6 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-3">3</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 3</span>
                        <span class="truncate block font-bold">Kết Quả CLS</span>
                    </div>
                </div>

                <div id="step-btn-4" onclick="clickEmrStep(4)" class="p-2.5 rounded-xl bg-slate-50 text-slate-600 border border-slate-200/80 transition-all flex items-center gap-2 text-left cursor-pointer hover:bg-slate-100">
                    <span class="w-6 h-6 rounded-lg bg-slate-200 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0" id="step-badge-4">4</span>
                    <div class="truncate">
                        <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Bước 4</span>
                        <span class="truncate block font-bold">Kê Đơn Thuốc</span>
                    </div>
                </div>
            </div>"""

def robust_replace(src, find_str, rep_str):
    if find_str in src:
        return src.replace(find_str, rep_str), True
    find_crlf = find_str.replace('\r\n', '\n').replace('\n', '\r\n')
    rep_crlf = rep_str.replace('\r\n', '\n').replace('\n', '\r\n')
    if find_crlf in src:
        return src.replace(find_crlf, rep_crlf), True
    return src, False

content, ok1 = robust_replace(content, old_stepper, new_stepper)
print("Updated Stepper HTML:", ok1)

# 2. Update configureEncounterChoices and selectEmrEncounter in JS
old_configure = """    function configureEncounterChoices(patient) {
        const select = document.getElementById('emr-encounter-select');
        select.replaceChildren(new Option('Chọn lần khám', ''));
        const actorDoctor = {{ session.get('user', {}).get('bac_si_id')|tojson }};
        const isAdmin = {{ (session.get('user', {}).get('vai_tro') == 'ADMIN')|tojson }};
        emrAppointments.filter(a => a.benh_nhan_id === patient.id && (isAdmin || a.bac_si_id === actorDoctor)
            && ['Đã tiếp nhận','Đang khám','Chờ kết quả CLS','Chờ kết luận'].includes(a.trang_thai))
            .forEach(a => select.add(new Option(`${a.ma_lich_hen} - ${a.ngay_hen} ${a.gio_hen} - ${a.bac_si || ''}`, 'appointment:'+a.id)));
        (patient.lich_su_kham || []).filter(r => (isAdmin || r.bac_si_id === actorDoctor)
            && ['Đang khám','Đang kê đơn','Chờ kết quả CLS','Chờ kết luận'].includes(r.trang_thai))
            .forEach(r => select.add(new Option(`Phiếu ${r.ma_phieu} - ${r.thoi_gian_kham || ''}`, 'record:'+r.id)));
        select.add(new Option('Khám trực tiếp mới', 'walk-in'));
        document.getElementById('emr-walk-in-fields').classList.add('hidden');
    }"""

new_configure = """    const currentUserRole = {{ session.get('user', {}).get('vai_tro')|tojson }};
    const isReadOnlyViewer = (currentUserRole === 'ADMIN' || currentUserRole === 'LETAN');

    function clickEmrStep(targetStep) {
        if (isReadOnlyViewer) {
            switchEmrStep(targetStep);
            return;
        }
        if (currentActiveEncounterId || targetStep <= currentEmrStep) {
            switchEmrStep(targetStep);
        } else {
            if (window.showAdminToast) {
                window.showAdminToast('Vui lòng lưu tiến trình bước hiện tại trước khi chuyển tiếp!', 'info');
            } else {
                alert('Vui lòng lưu tiến trình bước hiện tại trước khi chuyển tiếp!');
            }
        }
    }

    function configureEncounterChoices(patient) {
        const select = document.getElementById('emr-encounter-select');
        select.replaceChildren(new Option('Chọn lần khám', ''));
        const actorDoctor = {{ session.get('user', {}).get('bac_si_id')|tojson }};
        const isAdminOrLetan = isReadOnlyViewer;

        // Nạp lịch hẹn của bệnh nhân
        const appts = emrAppointments.filter(a => a.benh_nhan_id === patient.id && (isAdminOrLetan || a.bac_si_id === actorDoctor)
            && (isAdminOrLetan || ['Đã tiếp nhận','Đang khám','Chờ kết quả CLS','Chờ kết luận'].includes(a.trang_thai)));
        appts.forEach(a => select.add(new Option(`Lịch hẹn ${a.ma_lich_hen || a.ma_hen} - ${a.ngay_hen} ${a.gio_hen} (${a.trang_thai}) - BS: ${a.bac_si || 'Chưa phân'}`, 'appointment:'+a.id)));

        // Nạp các phiếu khám trong lịch sử
        const records = (patient.lich_su_kham || []).filter(r => (isAdminOrLetan || r.bac_si_id === actorDoctor)
            && (isAdminOrLetan || ['Đang khám','Đang kê đơn','Chờ kết quả CLS','Chờ kết luận'].includes(r.trang_thai)));
        records.forEach(r => {
            const timeStr = String(r.thoi_gian_kham || '').slice(0, 16);
            select.add(new Option(`Phiếu ${r.ma_phieu} - ${timeStr} (${r.trang_thai || 'Đã khám'}) - BS: ${r.bac_si || ''}`, 'record:'+r.id));
        });

        if (!isAdminOrLetan) {
            select.add(new Option('Khám trực tiếp mới', 'walk-in'));
        }
        document.getElementById('emr-walk-in-fields').classList.add('hidden');

        // Tự động chọn lần khám đầu tiên nếu Admin/Tiếp tân đang xem
        if (isAdminOrLetan && select.options.length > 1) {
            select.selectedIndex = 1;
            selectEmrEncounter(select.value);
        }
    }"""

content, ok2 = robust_replace(content, old_configure, new_configure)
print("Updated configureEncounterChoices:", ok2)

# 3. Update selectEmrEncounter to populate prescription items and enforce readonly mode
old_encounter_end = """        renderPatientClsResults(patient);
        if (record && record.trang_thai === 'Chờ kết quả CLS') lockEmrClinicalStep();
    }"""

new_encounter_end = """        // Tự động nạp đơn thuốc đã kê nếu có
        if (record && record.don_thuoc && Array.isArray(record.don_thuoc)) {
            prescriptionItems = record.don_thuoc.map((it, idx) => ({
                id: idx + 1,
                thuoc_id: it.thuoc_id || idx + 1,
                ten_thuoc: it.ten || it.ten_thuoc || '',
                don_vi_tinh: it.don_vi_tinh || 'Viên',
                so_luong: parseInt(it.so_luong) || 1,
                lieu_dung: it.cach_dung || it.lieu_dung || 'Ngày 2 lần',
                cach_dung: it.cach_dung || 'Uống sau ăn',
                don_gia: it.don_gia || 0,
                thanh_tien: (it.don_gia || 0) * (parseInt(it.so_luong) || 1)
            }));
            renderPrescriptionTable();
        }

        // Tự động khóa readonly cho Admin/Tiếp tân
        if (isReadOnlyViewer) {
            ['emr-ha','emr-mach','emr-t','emr-spo2','emr-symptoms','emr-icd','emr-treatment','emr-advice','emr-reexam','emr-reexam-time'].forEach(fid => {
                const el = document.getElementById(fid);
                if (el) {
                    el.readOnly = true;
                    el.classList.add('bg-slate-100', 'cursor-not-allowed');
                }
            });
            // Ẩn các nút lưu y lệnh đối với Admin/Tiếp tân
            document.querySelectorAll('#tab-kham button[onclick*=\"advanceEmrStep\"], #tab-kham button[onclick*=\"transferEmrSession\"], #tab-kham button[onclick*=\"completeExamination\"], #tab-cls button[onclick*=\"transferEmrSession\"], #tab-thuoc button[onclick*=\"finishExaminationRecord\"], #tab-thuoc button[onclick*=\"addMedicineToPrescription\"]').forEach(btn => {
                btn.style.display = 'none';
            });
        }

        renderPatientClsResults(patient);
        if (record && record.trang_thai === 'Chờ kết quả CLS') lockEmrClinicalStep();
    }"""

content, ok3 = robust_replace(content, old_encounter_end, new_encounter_end)
print("Updated selectEmrEncounter:", ok3)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated emr.html successfully!")
