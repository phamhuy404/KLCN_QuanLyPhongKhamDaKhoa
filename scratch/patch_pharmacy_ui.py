import sys

with open('templates/admin/pharmacy.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add 3rd Tab Button
old_tab_buttons = """    <!-- 3. Chuyển đổi Tab: 1. Danh Mục Tồn Kho | 2. Quầy Phát Thuốc -->
    <div class="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl w-max text-xs font-bold">
        <button type="button" onclick="switchPharmacyTab('inventory')" id="btn-tab-inventory" class="px-5 py-2.5 rounded-xl bg-white text-medical-700 shadow-sm transition-all">
            <i class="fa-solid fa-warehouse mr-1.5"></i> Danh Mục và Tồn Kho Thuốc
        </button>
        <button type="button" onclick="switchPharmacyTab('dispensing')" id="btn-tab-dispensing" class="px-5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition-all">
            <i class="fa-solid fa-hand-holding-medical mr-1.5"></i> Quầy Phát Thuốc Theo Đơn EMR
        </button>
    </div>"""

new_tab_buttons = """    <!-- 3. Chuyển đổi Tab: 1. Danh Mục Tồn Kho | 2. Quầy Phát Thuốc | 3. Lịch Sử Tăng Giảm Thuốc -->
    <div class="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl w-max text-xs font-bold">
        <button type="button" onclick="switchPharmacyTab('inventory')" id="btn-tab-inventory" class="px-5 py-2.5 rounded-xl bg-white text-medical-700 shadow-sm transition-all">
            <i class="fa-solid fa-warehouse mr-1.5"></i> Danh Mục và Tồn Kho Thuốc
        </button>
        <button type="button" onclick="switchPharmacyTab('dispensing')" id="btn-tab-dispensing" class="px-5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition-all">
            <i class="fa-solid fa-hand-holding-medical mr-1.5"></i> Quầy Phát Thuốc Theo Đơn EMR
        </button>
        <button type="button" onclick="switchPharmacyTab('stock_history')" id="btn-tab-stock-history" class="px-5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition-all">
            <i class="fa-solid fa-clock-rotate-left mr-1.5"></i> Lịch Sử Tăng Giảm Thuốc
        </button>
    </div>"""

assert old_tab_buttons in text, "old_tab_buttons not found"
text = text.replace(old_tab_buttons, new_tab_buttons)

# 2. Add Section 3 right after section-dispensing
old_section_dispensing_end = """            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs whitespace-nowrap">
                    <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                        <tr>
                            <th class="py-3 px-4">Mã Đơn</th>
                            <th class="py-3 px-4">Bệnh Nhân</th>
                            <th class="py-3 px-4">Bác Sĩ Kê Đơn</th>
                            <th class="py-3 px-4">Các Thuốc Trong Đơn</th>
                            <th class="py-3 px-4">Giờ Kê</th>
                            <th class="py-3 px-4 text-center">Trạng Thái</th>
                            <th class="py-3 px-4 text-center">Thao Tác</th>
                        </tr>
                    </thead>
                    <tbody id="dispensing-table-body" class="divide-y divide-slate-100">
                        <!-- JS render -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>"""

new_section_stock_history = """            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs whitespace-nowrap">
                    <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                        <tr>
                            <th class="py-3 px-4">Mã Đơn</th>
                            <th class="py-3 px-4">Bệnh Nhân</th>
                            <th class="py-3 px-4">Bác Sĩ Kê Đơn</th>
                            <th class="py-3 px-4">Các Thuốc Trong Đơn</th>
                            <th class="py-3 px-4">Giờ Kê</th>
                            <th class="py-3 px-4 text-center">Trạng Thái</th>
                            <th class="py-3 px-4 text-center">Thao Tác</th>
                        </tr>
                    </thead>
                    <tbody id="dispensing-table-body" class="divide-y divide-slate-100">
                        <!-- JS render -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- NỘI DUNG PHẦN 3: LỊCH SỬ TĂNG GIẢM THUỐC THEO NGÀY/TUẦN -->
    <div id="section-stock-history" class="space-y-4 hidden">
        <!-- Thống kê nhanh biến động kho -->
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div class="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg">
                    <i class="fa-solid fa-receipt"></i>
                </div>
                <div>
                    <span class="text-[11px] text-slate-400 font-medium">Tổng giao dịch biến động</span>
                    <h4 class="text-lg font-bold text-slate-900 mt-0.5" id="stock-kpi-total">0</h4>
                </div>
            </div>
            <div class="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg">
                    <i class="fa-solid fa-arrow-down-long"></i>
                </div>
                <div>
                    <span class="text-[11px] text-slate-400 font-medium">Tổng thuốc nhập kho (+)</span>
                    <h4 class="text-lg font-bold text-emerald-600 mt-0.5" id="stock-kpi-in">+0</h4>
                </div>
            </div>
            <div class="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center text-lg">
                    <i class="fa-solid fa-arrow-up-long"></i>
                </div>
                <div>
                    <span class="text-[11px] text-slate-400 font-medium">Tổng xuất quầy theo đơn (-)</span>
                    <h4 class="text-lg font-bold text-amber-600 mt-0.5" id="stock-kpi-out">-0</h4>
                </div>
            </div>
            <div class="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center text-lg">
                    <i class="fa-solid fa-shield-halved"></i>
                </div>
                <div>
                    <span class="text-[11px] text-slate-400 font-medium">Chống trùng CSV & Ngày</span>
                    <h4 class="text-xs font-bold text-teal-700 mt-1 flex items-center gap-1">
                        <i class="fa-solid fa-circle-check"></i> Đang kích hoạt
                    </h4>
                </div>
            </div>
        </div>

        <!-- Khối Bảng Lịch Sử và Bộ Lọc -->
        <div class="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div class="p-4 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                    <h4 class="font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center gap-2">
                        <i class="fa-solid fa-clock-rotate-left text-medical-600"></i>
                        Sổ Nhật Ký Biến Động Nhập - Xuất Dược Phẩm
                    </h4>
                    <p class="text-[11px] text-slate-400 mt-0.5">
                        Kiểm soát theo ngày/tuần: Nhập kho CSV và xuất theo đơn EMR đã thanh toán thực tế tại quầy
                    </p>
                </div>
                <div class="flex items-center flex-wrap gap-2 text-xs">
                    <!-- Bộ lọc Loại biến động -->
                    <select id="filter-stock-action" onchange="filterStockMovements()" class="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-medical-500 font-medium">
                        <option value="ALL">Tất cả biến động (Nhập & Xuất)</option>
                        <option value="STOCK_IN">Chỉ Nhập kho (+)</option>
                        <option value="STOCK_OUT">Chỉ Xuất theo đơn (-)</option>
                    </select>

                    <!-- Bộ lọc Thời gian -->
                    <select id="filter-stock-time" onchange="filterStockMovements()" class="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-medical-500 font-medium">
                        <option value="ALL">Tất cả thời gian</option>
                        <option value="TODAY">Hôm nay</option>
                        <option value="WEEK">7 ngày gần nhất (Tuần)</option>
                        <option value="MONTH">30 ngày gần nhất (Tháng)</option>
                    </select>

                    <!-- Ô tìm kiếm -->
                    <div class="relative">
                        <input type="text" id="search-stock-text" oninput="filterStockMovements()" placeholder="Tìm thuốc, mã, chứng từ..." class="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-medical-500 w-52 text-xs">
                        <i class="fa-solid fa-magnifying-glass absolute left-2.5 top-2.5 text-slate-400 text-xs"></i>
                    </div>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs whitespace-nowrap">
                    <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                        <tr>
                            <th class="py-3 px-4">Thời Gian & Ngày</th>
                            <th class="py-3 px-4">Mã & Tên Dược Phẩm</th>
                            <th class="py-3 px-4 text-center">Phân Loại</th>
                            <th class="py-3 px-4 text-center">Biến Động</th>
                            <th class="py-3 px-4 text-center">Tồn Kho (Trước &rarr; Sau)</th>
                            <th class="py-3 px-4">Chứng Từ / Đơn Thuốc</th>
                            <th class="py-3 px-4">Người Thực Hiện</th>
                            <th class="py-3 px-4">Ghi Chú</th>
                        </tr>
                    </thead>
                    <tbody id="stock-movements-table-body" class="divide-y divide-slate-100">
                        <!-- JS rendered -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>"""

assert old_section_dispensing_end in text, "old_section_dispensing_end not found"
text = text.replace(old_section_dispensing_end, new_section_stock_history)

# 3. Add JSON script tag for stock_movements
old_json_tag = """<script type="application/json" id="pharmacy-prescriptions-data">
    {{ prescriptions | tojson | safe }}
</script>"""

new_json_tag = """<script type="application/json" id="pharmacy-prescriptions-data">
    {{ prescriptions | tojson | safe }}
</script>
<script type="application/json" id="pharmacy-stock-movements-data">
    {{ (stock_movements or []) | tojson | safe }}
</script>"""

assert old_json_tag in text, "old_json_tag not found"
text = text.replace(old_json_tag, new_json_tag)

# 4. Update switchPharmacyTab and add stock movements rendering JS
old_switch = """    function switchPharmacyTab(tab) {
        if (tab === 'inventory') {
            document.getElementById('section-inventory').classList.remove('hidden');
            document.getElementById('section-dispensing').classList.add('hidden');
            document.getElementById('btn-tab-inventory').className = "px-5 py-2.5 rounded-xl bg-white text-medical-700 shadow-sm transition-all";
            document.getElementById('btn-tab-dispensing').className = "px-5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition-all";
        } else {
            document.getElementById('section-inventory').classList.add('hidden');
            document.getElementById('section-dispensing').classList.remove('hidden');
            document.getElementById('btn-tab-inventory').className = "px-5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition-all";
            document.getElementById('btn-tab-dispensing').className = "px-5 py-2.5 rounded-xl bg-white text-medical-700 shadow-sm transition-all";
        }
    }"""

new_switch = """    let rawStockMovements = JSON.parse(document.getElementById('pharmacy-stock-movements-data').textContent || '[]');

    function switchPharmacyTab(tab) {
        const secInv = document.getElementById('section-inventory');
        const secDisp = document.getElementById('section-dispensing');
        const secStock = document.getElementById('section-stock-history');

        const btnInv = document.getElementById('btn-tab-inventory');
        const btnDisp = document.getElementById('btn-tab-dispensing');
        const btnStock = document.getElementById('btn-tab-stock-history');

        const activeClass = "px-5 py-2.5 rounded-xl bg-white text-medical-700 shadow-sm transition-all";
        const inactiveClass = "px-5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition-all";

        secInv.classList.add('hidden');
        secDisp.classList.add('hidden');
        secStock.classList.add('hidden');

        btnInv.className = inactiveClass;
        btnDisp.className = inactiveClass;
        btnStock.className = inactiveClass;

        if (tab === 'inventory') {
            secInv.classList.remove('hidden');
            btnInv.className = activeClass;
        } else if (tab === 'dispensing') {
            secDisp.classList.remove('hidden');
            btnDisp.className = activeClass;
        } else if (tab === 'stock_history') {
            secStock.classList.remove('hidden');
            btnStock.className = activeClass;
            filterStockMovements();
        }
    }

    function renderStockMovements(items) {
        const tbody = document.getElementById('stock-movements-table-body');
        if (!tbody) return;

        let totalIn = 0;
        let totalOut = 0;

        rawStockMovements.forEach(m => {
            const d = Math.abs(Number(m.delta) || 0);
            if (m.is_increase || m.action === 'STOCK_IN') {
                totalIn += d;
            } else {
                totalOut += d;
            }
        });

        document.getElementById('stock-kpi-total').textContent = rawStockMovements.length + ' giao dịch';
        document.getElementById('stock-kpi-in').textContent = '+' + totalIn.toLocaleString('vi-VN');
        document.getElementById('stock-kpi-out').textContent = '-' + totalOut.toLocaleString('vi-VN');

        if (!items || items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="py-12 text-center text-slate-400">
                        <i class="fa-solid fa-boxes-packing text-3xl mb-2 block"></i>
                        Không tìm thấy giao dịch tăng giảm kho nào phù hợp với bộ lọc
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = items.map(m => {
            const isInc = m.is_increase || m.action === 'STOCK_IN';
            const actionBadge = isInc 
                ? '<span class="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px] border border-emerald-200"><i class="fa-solid fa-arrow-down mr-1"></i>Nhập kho (+)</span>'
                : '<span class="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200"><i class="fa-solid fa-arrow-up mr-1"></i>Xuất theo đơn (-)</span>';
            
            const deltaDisplay = isInc
                ? `<span class="font-bold text-emerald-600 font-mono text-sm">+${Math.abs(m.delta)}</span> <span class="text-[10px] text-slate-400 font-normal">${m.don_vi_tinh || ''}</span>`
                : `<span class="font-bold text-amber-600 font-mono text-sm">-${Math.abs(m.delta)}</span> <span class="text-[10px] text-slate-400 font-normal">${m.don_vi_tinh || ''}</span>`;

            return `
                <tr class="hover:bg-slate-50/80 transition-colors">
                    <td class="py-3 px-4">
                        <span class="font-bold text-slate-900 block font-mono">${(m.thoi_gian || '').substring(11, 19) || '08:00:00'}</span>
                        <span class="text-[10px] text-slate-400 font-mono">${m.ngay || (m.thoi_gian || '').substring(0, 10)}</span>
                    </td>
                    <td class="py-3 px-4">
                        <div class="font-bold text-slate-900">${m.ten_thuoc}</div>
                        <div class="text-[10px] text-slate-400 font-mono">${m.ma_thuoc}</div>
                    </td>
                    <td class="py-3 px-4 text-center">
                        ${actionBadge}
                    </td>
                    <td class="py-3 px-4 text-center">
                        ${deltaDisplay}
                    </td>
                    <td class="py-3 px-4 text-center font-mono">
                        <span class="text-slate-500">${m.ton_truoc}</span>
                        <i class="fa-solid fa-arrow-right text-[9px] text-slate-300 mx-1"></i>
                        <span class="font-bold text-slate-900">${m.ton_sau}</span>
                    </td>
                    <td class="py-3 px-4">
                        <span class="font-semibold text-slate-800">${m.chung_tu || 'Phiếu nội bộ'}</span>
                    </td>
                    <td class="py-3 px-4 text-slate-600">
                        ${m.nguoi_thuc_hien || 'Hệ thống'}
                    </td>
                    <td class="py-3 px-4 text-slate-500 max-w-[200px] truncate" title="${m.ly_do || ''}">
                        ${m.ly_do || 'Xuất nhập tồn chuẩn GPP'}
                    </td>
                </tr>
            `;
        }).join('');
    }

    function filterStockMovements() {
        const actionFilter = document.getElementById('filter-stock-action').value;
        const timeFilter = document.getElementById('filter-stock-time').value;
        const query = (document.getElementById('search-stock-text').value || '').toLowerCase().trim();

        const todayStr = new Date().toISOString().substring(0, 10);
        const oneWeekAgo = new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString().substring(0, 10);
        const oneMonthAgo = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().substring(0, 10);

        const filtered = rawStockMovements.filter(m => {
            // Lọc loại
            if (actionFilter === 'STOCK_IN' && m.action !== 'STOCK_IN') return false;
            if (actionFilter === 'STOCK_OUT' && m.action !== 'STOCK_OUT') return false;

            // Lọc thời gian
            const itemDate = m.ngay || (m.thoi_gian || '').substring(0, 10);
            if (timeFilter === 'TODAY' && itemDate !== todayStr) return false;
            if (timeFilter === 'WEEK' && itemDate < oneWeekAgo) return false;
            if (timeFilter === 'MONTH' && itemDate < oneMonthAgo) return false;

            // Tìm kiếm
            if (query) {
                const combined = ((m.ten_thuoc || '') + ' ' + (m.ma_thuoc || '') + ' ' + (m.chung_tu || '') + ' ' + (m.nguoi_thuc_hien || '') + ' ' + (m.ly_do || '')).toLowerCase();
                if (!combined.includes(query)) return false;
            }

            return true;
        });

        renderStockMovements(filtered);
    }"""

assert old_switch in text, "old_switch not found"
text = text.replace(old_switch, new_switch)

with open('templates/admin/pharmacy.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully patched templates/admin/pharmacy.html!')
