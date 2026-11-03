import sys

with open('templates/admin/emr.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Replace Region 1 (Vitals & Clinical Inputs in Step 1)
start_tab_kham = text.find('<div id="tab-kham" class="space-y-4">')
end_tab_kham_inputs = text.find('<!-- Upload và Xem trước ảnh khám lâm sàng', start_tab_kham)
assert start_tab_kham != -1 and end_tab_kham_inputs != -1, "Region 1 not found"

new_tab_kham_inputs = """<div id="tab-kham" class="space-y-4">
                <!-- Chỉ số sinh hiệu đo trước khi vào phòng khám -->
                <div>
                    <div class="flex items-center justify-between mb-2">
                        <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                            <i class="fa-solid fa-heart-pulse text-rose-500"></i>
                            Chỉ số sinh hiệu đo tại phòng khám
                        </label>
                        <span class="text-[11px] text-slate-400 font-medium">Định dạng chuẩn lâm sàng (Không bắt buộc)</span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 focus-within:border-medical-500 focus-within:bg-white transition-all">
                            <div class="flex items-center justify-between">
                                <span class="text-slate-500 font-semibold block text-[11px]">Huyết áp</span>
                                <span class="text-[10px] text-slate-400 font-mono">mmHg</span>
                            </div>
                            <input type="text" id="emr-ha" value="" placeholder="120/80" maxlength="8" class="w-full bg-transparent font-bold font-mono text-slate-800 mt-1 focus:outline-none text-sm placeholder:text-slate-300 placeholder:font-normal">
                            <span class="text-[9px] text-slate-400 block mt-0.5">Tâm thu/Tâm trương</span>
                        </div>
                        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 focus-within:border-medical-500 focus-within:bg-white transition-all">
                            <div class="flex items-center justify-between">
                                <span class="text-slate-500 font-semibold block text-[11px]">Mạch đập</span>
                                <span class="text-[10px] text-slate-400 font-mono">lần/phút</span>
                            </div>
                            <input type="number" id="emr-mach" value="" placeholder="75" min="40" max="220" class="w-full bg-transparent font-bold font-mono text-slate-800 mt-1 focus:outline-none text-sm placeholder:text-slate-300 placeholder:font-normal">
                            <span class="text-[9px] text-slate-400 block mt-0.5">Bình thường: 60-90</span>
                        </div>
                        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 focus-within:border-medical-500 focus-within:bg-white transition-all">
                            <div class="flex items-center justify-between">
                                <span class="text-slate-500 font-semibold block text-[11px]">Thân nhiệt</span>
                                <span class="text-[10px] text-slate-400 font-mono">°C</span>
                            </div>
                            <input type="number" step="0.1" id="emr-t" value="" placeholder="36.5" min="34" max="42" class="w-full bg-transparent font-bold font-mono text-slate-800 mt-1 focus:outline-none text-sm placeholder:text-slate-300 placeholder:font-normal">
                            <span class="text-[9px] text-slate-400 block mt-0.5">Bình thường: 36.5-37.2</span>
                        </div>
                        <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 focus-within:border-medical-500 focus-within:bg-white transition-all">
                            <div class="flex items-center justify-between">
                                <span class="text-slate-500 font-semibold block text-[11px]">SpO2</span>
                                <span class="text-[10px] text-slate-400 font-mono">%</span>
                            </div>
                            <input type="number" id="emr-spo2" value="" placeholder="98" min="50" max="100" class="w-full bg-transparent font-bold font-mono text-slate-800 mt-1 focus:outline-none text-sm placeholder:text-slate-300 placeholder:font-normal">
                            <span class="text-[9px] text-slate-400 block mt-0.5">Bình thường: 96-99%</span>
                        </div>
                    </div>
                </div>

                <div class="space-y-3 text-xs">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                            <span>Lý do khám và Triệu chứng lâm sàng <span class="text-rose-500">*</span></span>
                            <span class="text-[10px] text-slate-400 font-normal">Mô tả lý do hoặc triệu chứng người bệnh khai</span>
                        </label>
                        <textarea id="emr-symptoms" rows="2" placeholder="Ví dụ: Đau tức vùng ngực trái 2 ngày, khó thở khi gắng sức, hồi hộp trống ngực, không sốt..." class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:border-medical-500"></textarea>
                    </div>

                    <!-- BỘ CHỌN DỊ ỨNG VÀ TIỀN SỬ BỆNH CHUẨN TỪ FILE TXT (CHỌN NHIỀU) -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                        <div>
                            <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                                <span class="flex items-center gap-1.5 text-rose-700 font-bold">
                                    <i class="fa-solid fa-triangle-exclamation"></i> Dị ứng thuốc và Thực phẩm (File .txt chuẩn)
                                </span>
                                <span class="text-[10px] text-slate-400">Chọn nhiều</span>
                            </label>
                            <input type="hidden" id="emr-allergy-input" value="{{ patients[0].di_ung if patients and patients[0].di_ung else '' }}">
                            <div id="emr-allergy-tag-container" class="space-y-1.5"></div>
                        </div>

                        <div>
                            <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                                <span class="flex items-center gap-1.5 text-teal-700 font-bold">
                                    <i class="fa-solid fa-notes-medical"></i> Tiền sử bệnh lý nền (File .txt chuẩn)
                                </span>
                                <span class="text-[10px] text-slate-400">Chọn nhiều</span>
                            </label>
                            <input type="hidden" id="emr-history-input" value="{{ patients[0].tien_su_benh if patients and patients[0].tien_su_benh else '' }}">
                            <div id="emr-history-tag-container" class="space-y-1.5"></div>
                        </div>
                    </div>

                    <div>
                        <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                            <span>Chẩn đoán xác định kèm mã ICD-10 <span class="text-rose-500">*</span></span>
                            <span class="text-[10px] text-teal-600 font-normal">Gõ tên bệnh hoặc chọn nhanh từ danh mục ICD-10</span>
                        </label>
                        <input type="text" id="emr-icd" list="icd-common-datalist" value="" placeholder="Ví dụ: I10 - Tăng huyết áp vô căn, K29.0 - Viêm dạ dày cấp..." class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:bg-white focus:outline-none focus:border-medical-500">
                        <datalist id="icd-common-datalist">
                            <option value="I10 - Tăng huyết áp vô căn (nguyên phát)"></option>
                            <option value="I20 - Cơn đau thắt ngực (Bệnh tim thiếu máu cục bộ)"></option>
                            <option value="I25 - Bệnh tim thiếu máu cục bộ mạn"></option>
                            <option value="J00 - Viêm mũi họng cấp (Cảm thường)"></option>
                            <option value="J02 - Viêm họng cấp"></option>
                            <option value="J03 - Viêm amidan cấp"></option>
                            <option value="J06 - Nhiễm khuẩn hô hấp trên cấp"></option>
                            <option value="J20 - Viêm phế quản cấp"></option>
                            <option value="J45 - Hen phế quản (Suyễn)"></option>
                            <option value="K21 - Trào ngược dạ dày thực quản (GERD)"></option>
                            <option value="K29.0 - Viêm dạ dày cấp xuất huyết"></option>
                            <option value="K29.5 - Viêm dạ dày mạn tính"></option>
                            <option value="K30 - Khó tiêu chức năng (Dyspepsia)"></option>
                            <option value="E11 - Đái tháo đường típ 2"></option>
                            <option value="E78 - Rối loạn chuyển hóa lipid máu"></option>
                            <option value="M54.5 - Đau thắt lưng"></option>
                            <option value="M17 - Thoái hóa khớp gối"></option>
                            <option value="L20 - Viêm da cơ địa (Chàm/Eczema)"></option>
                            <option value="L70 - Mụn trứng cá"></option>
                            <option value="H10 - Viêm kết mạc (Đau mắt đỏ)"></option>
                            <option value="H52.1 - Cận thị"></option>
                            <option value="N39.0 - Nhiễm trùng đường tiết niệu"></option>
                            <option value="R50 - Sốt không rõ nguyên nhân"></option>
                            <option value="R51 - Nhức đầu căng thẳng"></option>
                        </datalist>
                    </div>

                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Hướng điều trị</label>
                        <input type="text" id="emr-treatment" value="" placeholder="Ví dụ: Điều trị ngoại trú theo đơn thuốc, kiểm soát huyết áp, chế độ ăn giảm muối..." class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:border-medical-500">
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block font-semibold text-slate-700 mb-1">Lời dặn của bác sĩ điều trị</label>
                            <input type="text" id="emr-advice" value="" placeholder="Ví dụ: Uống thuốc sau ăn, kiêng đồ kích thích, tái khám khi có dấu hiệu bất thường..." class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:border-medical-500">
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-700 mb-1">Ngày hẹn tái khám (Nếu có)</label>
                            <input type="date" id="emr-reexam" onchange="handleReexamDateChange(this.value, 1)" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:border-medical-500">
                            <span class="text-[10px] text-slate-400 mt-1 block">Tối thiểu cách 2 ngày so với ngày hiện tại</span>
                        </div>
                        <div id="emr-reexam-time-container-step1" class="hidden">
                            <label class="block font-semibold text-slate-700 mb-1">Khung giờ hẹn tái khám</label>
                            <select id="emr-reexam-time" onchange="syncStepReexamTime(this.value, 1)" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:border-medical-500">
                                <optgroup label="Ca Sáng">
                                    <option value="07:30">07:30</option>
                                    <option value="08:00">08:00</option>
                                    <option value="08:30" selected>08:30</option>
                                    <option value="09:00">09:00</option>
                                    <option value="09:30">09:30</option>
                                    <option value="10:00">10:00</option>
                                    <option value="10:30">10:30</option>
                                    <option value="11:00">11:00</option>
                                </optgroup>
                                <optgroup label="Ca Chiều">
                                    <option value="13:30">13:30</option>
                                    <option value="14:00">14:00</option>
                                    <option value="14:30">14:30</option>
                                    <option value="15:00">15:00</option>
                                    <option value="15:30">15:30</option>
                                    <option value="16:00">16:00</option>
                                    <option value="16:30">16:30</option>
                                </optgroup>
                                <optgroup label="Ca Tối">
                                    <option value="17:30">17:30</option>
                                    <option value="18:00">18:00</option>
                                    <option value="18:30">18:30</option>
                                    <option value="19:00">19:00</option>
                                    <option value="19:30">19:30</option>
                                    <option value="20:00">20:00</option>
                                </optgroup>
                            </select>
                        </div>
                    </div>
                </div>

                """

text = text[:start_tab_kham] + new_tab_kham_inputs + text[end_tab_kham_inputs:]

# 2. Replace Region 2 (Step 4 Re-examination booking)
start_s4 = text.find('<!-- LÊN LỊCH HẸN MỚI / TÁI KHÁM DUYỆT SẴN TRONG BƯỚC 4 -->')
end_s4 = text.find('<!-- Điều hướng cuối Bước 4: Hoàn tất ca khám -->', start_s4)
assert start_s4 != -1 and end_s4 != -1, "Region 2 not found"

new_s4 = """<!-- LÊN LỊCH HẸN MỚI / TÁI KHÁM DUYỆT SẴN TRONG BƯỚC 4 -->
                <div class="p-4 bg-teal-50/50 border border-teal-200 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="w-7 h-7 rounded-lg bg-teal-600 text-white flex items-center justify-center text-xs">
                                <i class="fa-solid fa-calendar-plus"></i>
                            </span>
                            <span class="font-bold text-teal-950 text-xs">Hẹn Lịch Khám Mới / Tái Khám Cho Bệnh Nhân (Tự Động Duyệt Sẵn)</span>
                        </div>
                        <span class="text-[11px] font-semibold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded-full">
                            <i class="fa-solid fa-check text-[10px]"></i> Đã duyệt sẵn khi tạo
                        </span>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label class="block font-semibold text-slate-700 mb-1">Ngày hẹn khám mới / Tái khám</label>
                            <input type="date" id="emr-reexam-step4" onchange="handleReexamDateChange(this.value, 4)" class="w-full p-2.5 bg-white border border-teal-200 rounded-xl text-xs focus:outline-none focus:border-teal-500">
                            <span class="text-[10px] text-teal-700 mt-1 block">Tối thiểu cách 2 ngày so với ngày hiện tại</span>
                        </div>
                        <div id="emr-reexam-time-container-step4" class="hidden">
                            <label class="block font-semibold text-slate-700 mb-1">Khung giờ hẹn</label>
                            <select id="emr-reexam-time-step4" onchange="syncStepReexamTime(this.value, 4)" class="w-full p-2.5 bg-white border border-teal-200 rounded-xl text-xs focus:outline-none focus:border-teal-500">
                                <optgroup label="Ca Sáng">
                                    <option value="07:30">07:30</option>
                                    <option value="08:00">08:00</option>
                                    <option value="08:30" selected>08:30</option>
                                    <option value="09:00">09:00</option>
                                    <option value="09:30">09:30</option>
                                    <option value="10:00">10:00</option>
                                    <option value="10:30">10:30</option>
                                    <option value="11:00">11:00</option>
                                </optgroup>
                                <optgroup label="Ca Chiều">
                                    <option value="13:30">13:30</option>
                                    <option value="14:00">14:00</option>
                                    <option value="14:30">14:30</option>
                                    <option value="15:00">15:00</option>
                                    <option value="15:30">15:30</option>
                                    <option value="16:00">16:00</option>
                                    <option value="16:30">16:30</option>
                                </optgroup>
                                <optgroup label="Ca Tối">
                                    <option value="17:30">17:30</option>
                                    <option value="18:00">18:00</option>
                                    <option value="18:30">18:30</option>
                                    <option value="19:00">19:00</option>
                                    <option value="19:30">19:30</option>
                                    <option value="20:00">20:00</option>
                                </optgroup>
                            </select>
                        </div>
                    </div>
                    <p class="text-[11px] text-slate-500 italic">
                        <i class="fa-solid fa-circle-info text-teal-600 mr-1"></i>
                        Lịch hẹn được tạo thành lịch mới riêng biệt trong danh sách của bệnh nhân, không đè lên lịch cũ, tự động duyệt sẵn và gửi thông báo.
                    </p>
                </div>

                """

text = text[:start_s4] + new_s4 + text[end_s4:]

# 3. Replace JS functions for syncStep4Reexam
old_js_sync = """    function syncStep4Reexam(val, type) {
        if (type === 'date') {
            const el1 = document.getElementById('emr-reexam');
            const el4 = document.getElementById('emr-reexam-step4');
            if (el1 && el1.value !== val) el1.value = val;
            if (el4 && el4.value !== val) el4.value = val;
        } else if (type === 'time') {
            const t1 = document.getElementById('emr-reexam-time');
            const t4 = document.getElementById('emr-reexam-time-step4');
            if (t1 && t1.value !== val) t1.value = val;
            if (t4 && t4.value !== val) t4.value = val;
        }
    }"""

new_js_sync = """    function getMinReexamDate() {
        const d = new Date();
        d.setDate(d.getDate() + 2);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    function initReexamInputs() {
        const minD = getMinReexamDate();
        const el1 = document.getElementById('emr-reexam');
        const el4 = document.getElementById('emr-reexam-step4');
        if (el1) el1.min = minD;
        if (el4) el4.min = minD;
    }

    function handleReexamDateChange(val, fromStep) {
        const minD = getMinReexamDate();
        const el1 = document.getElementById('emr-reexam');
        const el4 = document.getElementById('emr-reexam-step4');
        const c1 = document.getElementById('emr-reexam-time-container-step1');
        const c4 = document.getElementById('emr-reexam-time-container-step4');

        if (!val || val.trim() === '') {
            if (el1) el1.value = '';
            if (el4) el4.value = '';
            if (c1) c1.classList.add('hidden');
            if (c4) c4.classList.add('hidden');
            return;
        }

        if (val < minD) {
            const parts = minD.split('-');
            const minDisp = `${parts[2]}/${parts[1]}/${parts[0]}`;
            alert(`Ngày hẹn tái khám phải cách ít nhất 2 ngày so với ngày hiện tại (Sớm nhất từ ngày ${minDisp})!`);
            if (el1) el1.value = '';
            if (el4) el4.value = '';
            if (c1) c1.classList.add('hidden');
            if (c4) c4.classList.add('hidden');
            return;
        }

        if (el1 && el1.value !== val) el1.value = val;
        if (el4 && el4.value !== val) el4.value = val;

        if (c1) c1.classList.remove('hidden');
        if (c4) c4.classList.remove('hidden');
    }

    function syncStepReexamTime(val, fromStep) {
        const t1 = document.getElementById('emr-reexam-time');
        const t4 = document.getElementById('emr-reexam-time-step4');
        if (t1 && t1.value !== val) t1.value = val;
        if (t4 && t4.value !== val) t4.value = val;
    }

    function syncStep4Reexam(val, type) {
        if (type === 'date') {
            handleReexamDateChange(val, 4);
        } else if (type === 'time') {
            syncStepReexamTime(val, 4);
        }
    }"""

assert old_js_sync in text, "old_js_sync not found"
text = text.replace(old_js_sync, new_js_sync)

# 4. Update selectEmrEncounter to call handleReexamDateChange
old_load_reexam = """        const rxDate = record?.ngay_tai_kham ? String(record.ngay_tai_kham).slice(0, 10) : '';
        const rxTime = record?.gio_tai_kham || '08:30';
        ['emr-reexam', 'emr-reexam-step4'].forEach(rid => { const el = document.getElementById(rid); if (el) el.value = rxDate; });
        ['emr-reexam-time', 'emr-reexam-time-step4'].forEach(rid => { const el = document.getElementById(rid); if (el) el.value = rxTime; });"""

new_load_reexam = """        const rxDate = record?.ngay_tai_kham ? String(record.ngay_tai_kham).slice(0, 10) : '';
        const rxTime = record?.gio_tai_kham || '08:30';
        if (rxDate) {
            handleReexamDateChange(rxDate, 1);
            syncStepReexamTime(rxTime, 1);
        } else {
            handleReexamDateChange('', 1);
        }"""

assert old_load_reexam in text, "old_load_reexam not found"
text = text.replace(old_load_reexam, new_load_reexam)

# 5. In resetEncounterEditor, call handleReexamDateChange('', 1)
old_reset_reexam = """        ['emr-reexam', 'emr-reexam-step4'].forEach(rid => { const el = document.getElementById(rid); if (el) el.value = ''; });"""
new_reset_reexam = """        handleReexamDateChange('', 1);"""
assert old_reset_reexam in text, "old_reset_reexam not found"
text = text.replace(old_reset_reexam, new_reset_reexam)

# 6. Call initReexamInputs before completeNormalExamination
old_init_call = """    function completeNormalExamination() {"""
new_init_call = """    // Khởi tạo giới hạn ngày hẹn tái khám
    document.addEventListener('DOMContentLoaded', () => {
        initReexamInputs();
    });

    function completeNormalExamination() {"""
assert old_init_call in text, "old_init_call not found"
text = text.replace(old_init_call, new_init_call)

with open('templates/admin/emr.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully patched templates/admin/emr.html!')
