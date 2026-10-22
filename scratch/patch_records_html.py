with open('templates/patient/records.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update prescription header & buying option box
old_prescription_block = """                    <!-- Đơn thuốc điện tử -->
                    {% if enc.don_thuoc %}
                    <div>
                        <h4 class="font-bold text-sm text-slate-800 mb-3 flex items-center gap-2">
                            <i class="fa-solid fa-pills text-medical-600"></i> Toa thuốc điều trị ({{ enc.don_thuoc|length }} loại thuốc)
                        </h4>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse text-xs">
                                <thead>
                                    <tr class="bg-slate-50 text-slate-400 font-semibold uppercase tracking-wider border-y border-slate-100">
                                        <th class="py-2.5 px-4">#</th>
                                        <th class="py-2.5 px-4">Tên thuốc & Hoạt chất</th>
                                        <th class="py-2.5 px-4">Số lượng</th>
                                        <th class="py-2.5 px-4">Liều dùng & Hướng dẫn sử dụng</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100 text-slate-700">
                                    {% for dt in enc.don_thuoc %}
                                    <tr>
                                        <td class="py-3 px-4 font-bold text-medical-600">{{ loop.index }}</td>
                                        <td class="py-3 px-4">
                                            <div class="font-bold text-slate-900">{{ dt.ten }}</div>
                                            <span class="text-[11px] text-slate-400">{{ dt.hoat_chat or '' }}</span>
                                        </td>
                                        <td class="py-3 px-4 font-semibold">{{ dt.so_luong }}</td>
                                        <td class="py-3 px-4">{{ dt.cach_dung or 'Theo chỉ dẫn của bác sĩ' }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    {% endif %}"""

new_prescription_block = """                    <!-- Đơn thuốc điện tử & Tùy chọn mua thuốc -->
                    {% if enc.don_thuoc %}
                    <div>
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                            <h4 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-pills text-medical-600"></i> Toa thuốc điều trị ({{ enc.don_thuoc|length }} loại thuốc)
                            </h4>
                            <div>
                                {% if enc.hinh_thuc_mua == 'Mua tại bệnh viện' %}
                                    <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                                        <i class="fa-solid fa-hospital mr-1"></i> Mua tại nhà thuốc bệnh viện (Đã trừ kho)
                                    </span>
                                {% elif enc.hinh_thuc_mua == 'Tự mua ngoài' %}
                                    <span class="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200">
                                        <i class="fa-solid fa-store mr-1"></i> Bệnh nhân tự mua ngoài
                                    </span>
                                {% else %}
                                    <span class="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-bold border border-amber-200">
                                        <i class="fa-solid fa-clock mr-1"></i> Chờ chọn nơi mua thuốc
                                    </span>
                                {% endif %}
                            </div>
                        </div>

                        <div class="overflow-x-auto border border-slate-100 rounded-xl">
                            <table class="w-full text-left border-collapse text-xs">
                                <thead>
                                    <tr class="bg-slate-50 text-slate-400 font-semibold uppercase tracking-wider border-y border-slate-100">
                                        <th class="py-2.5 px-4">#</th>
                                        <th class="py-2.5 px-4">Tên thuốc & Hoạt chất</th>
                                        <th class="py-2.5 px-4">Số lượng</th>
                                        <th class="py-2.5 px-4">Liều dùng & Hướng dẫn sử dụng</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100 text-slate-700">
                                    {% for dt in enc.don_thuoc %}
                                    <tr>
                                        <td class="py-3 px-4 font-bold text-medical-600">{{ loop.index }}</td>
                                        <td class="py-3 px-4">
                                            <div class="font-bold text-slate-900">{{ dt.ten }}</div>
                                            <span class="text-[11px] text-slate-400">{{ dt.hoat_chat or '' }}</span>
                                        </td>
                                        <td class="py-3 px-4 font-semibold">{{ dt.so_luong }}</td>
                                        <td class="py-3 px-4">{{ dt.cach_dung or 'Theo chỉ dẫn của bác sĩ' }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>

                        <!-- Khối lựa chọn mua thuốc nếu chưa chọn -->
                        {% if enc.don_thuoc_id and (enc.hinh_thuc_mua == 'Chưa chọn' or not enc.hinh_thuc_mua) %}
                        <div class="mt-3.5 p-4 rounded-2xl bg-gradient-to-r from-teal-50/80 to-emerald-50/80 border border-teal-200/80">
                            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <div>
                                    <h5 class="text-xs font-bold text-teal-900 flex items-center gap-1.5">
                                        <i class="fa-solid fa-bag-shopping text-medical-600"></i> Lựa chọn nhận thuốc
                                    </h5>
                                    <p class="text-[11px] text-teal-700 mt-0.5">
                                        Bạn có thể chọn nhận mua thuốc tại Nhà thuốc Bệnh viện hoặc tự mua tại các hiệu thuốc bên ngoài:
                                    </p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button type="button" onclick="chooseMedicineOption({{ enc.don_thuoc_id }}, 'Tự mua ngoài')"
                                            class="px-3.5 py-2 rounded-xl bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 font-bold text-xs transition-all shadow-sm">
                                        <i class="fa-solid fa-store mr-1 text-slate-500"></i> Tự mua ngoài
                                    </button>
                                    <button type="button" onclick="chooseMedicineOption({{ enc.don_thuoc_id }}, 'Mua tại bệnh viện')"
                                            class="px-4 py-2 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-md shadow-medical-600/20 transition-all flex items-center gap-1.5">
                                        <i class="fa-solid fa-hospital mr-1"></i> Mua tại bệnh viện
                                    </button>
                                </div>
                            </div>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}"""

c = c.replace(old_prescription_block, new_prescription_block).replace(old_prescription_block.replace('\n', '\r\n'), new_prescription_block.replace('\n', '\r\n'))

# 2. Add chooseMedicineOption function in script
old_script_anchor = "    function filterPatientRecords() {"
new_script_func = """    function chooseMedicineOption(dtId, option) {
        if (!dtId) return;
        const confirmMsg = option === 'Tự mua ngoài'
            ? 'Bạn muốn tự mua thuốc tại các nhà thuốc bên ngoài theo toa này?\\n(Không tính tiền thuốc vào viện phí bệnh viện).'
            : 'Bạn muốn mua thuốc tại Nhà thuốc Bệnh viện?\\n(Hệ thống sẽ thêm hóa đơn thuốc, trừ số lượng tồn kho bệnh viện và chuyển sang Quầy Dược).';
        
        if (!confirm(confirmMsg)) return;

        fetch('/api/prescription/choose-buying-option', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prescription_id: dtId, option: option })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert('✅ ' + data.message);
                window.location.reload();
            } else {
                alert('❌ ' + data.message);
            }
        })
        .catch(err => {
            alert('Lỗi kết nối máy chủ: ' + err);
        });
    }

    function filterPatientRecords() {"""

c = c.replace(old_script_anchor, new_script_func).replace(old_script_anchor.replace('\n', '\r\n'), new_script_func.replace('\n', '\r\n'))

with open('templates/patient/records.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated templates/patient/records.html successfully!')
