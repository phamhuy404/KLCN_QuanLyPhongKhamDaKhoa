import sys

filepath = 'templates/admin/staff.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

def robust_replace(src, find_str, rep_str):
    if find_str in src:
        return src.replace(find_str, rep_str), True
    find_crlf = find_str.replace('\r\n', '\n').replace('\n', '\r\n')
    rep_crlf = rep_str.replace('\r\n', '\n').replace('\n', '\r\n')
    if find_crlf in src:
        return src.replace(find_crlf, rep_crlf), True
    return src, False

old_form = """            <!-- Form chọn bộ lọc -->
            <form method="GET" action="{{ url_for('admin.staff') }}" class="flex flex-wrap items-center gap-2.5">
                <input type="hidden" name="tab" value="workstats">
                
                {% if work_stats and work_stats.can_view_all %}
                <!-- Chọn chế độ xem (Chỉ ADMIN & LỄ TÂN) -->
                <div class="flex items-center gap-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1.5">Phạm vi:</label>
                    <select name="stats_scope" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 outline-none focus:border-blue-500">
                        <option value="all" {% if work_stats.scope == 'all' %}selected{% endif %}>Toàn bộ nhân sự</option>
                        <option value="mine" {% if work_stats.scope == 'mine' %}selected{% endif %}>Chỉ cá nhân tôi</option>
                    </select>
                </div>

                {% if work_stats.scope == 'all' %}
                <!-- Lọc theo nhân viên cụ thể -->
                <div class="flex items-center gap-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1.5">Nhân viên:</label>
                    <select name="stats_staff_id" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 outline-none focus:border-blue-500 max-w-[180px]">
                        <option value="">Tất cả nhân viên</option>
                        {% for s in staff_list %}
                        <option value="{{ s.id }}" {% if request.args.get('stats_staff_id') == s.id|string %}selected{% endif %}>
                            {{ s.ho_ten }} ({{ s.vai_tro }})
                        </option>
                        {% endfor %}
                    </select>
                </div>
                {% endif %}
                {% endif %}

                <!-- Lọc theo tháng -->
                <div class="flex items-center gap-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1.5">Kỳ tháng:</label>
                    <select name="stats_month" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 outline-none focus:border-blue-500">
                        <option value="all" {% if work_stats and work_stats.selected_month == 'all' %}selected{% endif %}>Tất cả các tháng</option>
                        {% if work_stats and work_stats.available_months %}
                        {% for m in work_stats.available_months %}
                        <option value="{{ m.key }}" {% if work_stats.selected_month == m.key %}selected{% endif %}>{{ m.label }}</option>
                        {% endfor %}
                        {% endif %}
                    </select>
                </div>

                <a href="{{ url_for('admin.staff', tab='workstats') }}" class="px-2.5 py-1.5 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg font-semibold transition" title="Đặt lại bộ lọc">
                    <i class="fa-solid fa-arrow-rotate-left"></i>
                </a>
            </form>"""

new_form = """            <!-- Form chọn bộ lọc nâng cao -->
            <form method="GET" action="{{ url_for('admin.staff') }}" class="flex flex-wrap items-center gap-2">
                <input type="hidden" name="tab" value="workstats">
                
                {% if work_stats and work_stats.can_view_all %}
                <!-- Chọn chế độ xem (Chỉ ADMIN & LỄ TÂN) -->
                <div class="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1">Phạm vi:</label>
                    <select name="stats_scope" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 font-semibold text-slate-700 outline-none focus:border-blue-500">
                        <option value="all" {% if work_stats.scope == 'all' %}selected{% endif %}>Toàn bộ nhân sự</option>
                        <option value="mine" {% if work_stats.scope == 'mine' %}selected{% endif %}>Chỉ cá nhân tôi</option>
                    </select>
                </div>

                {% if work_stats.scope == 'all' %}
                <!-- Lọc theo Khoa / Chuyên khoa -->
                <div class="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1"><i class="fa-solid fa-hospital text-blue-600 text-[10px]"></i> Khoa:</label>
                    <select name="stats_dept_id" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 font-semibold text-slate-700 outline-none focus:border-blue-500 max-w-[150px]">
                        <option value="">Tất cả khoa</option>
                        {% for d in departments %}
                        <option value="{{ d.id }}" {% if work_stats and work_stats.selected_dept_id == d.id|string %}selected{% endif %}>{{ d.ten_khoa }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Lọc theo Vị trí / Vai trò -->
                <div class="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1"><i class="fa-solid fa-user-doctor text-indigo-600 text-[10px]"></i> Vị trí:</label>
                    <select name="stats_role" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 font-semibold text-slate-700 outline-none focus:border-blue-500">
                        <option value="">Tất cả vị trí</option>
                        <option value="BACSI" {% if work_stats and work_stats.selected_role == 'BACSI' %}selected{% endif %}>Bác sĩ</option>
                        <option value="DUOCSI" {% if work_stats and work_stats.selected_role == 'DUOCSI' %}selected{% endif %}>Dược sĩ</option>
                        <option value="KTV" {% if work_stats and work_stats.selected_role == 'KTV' %}selected{% endif %}>Kỹ thuật viên</option>
                        <option value="LETAN" {% if work_stats and work_stats.selected_role == 'LETAN' %}selected{% endif %}>Lễ tân / Thu ngân</option>
                    </select>
                </div>

                <!-- Ô tìm kiếm nhân viên -->
                <div class="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <i class="fa-solid fa-magnifying-glass text-slate-400 text-[10px] pl-1.5"></i>
                    <input type="text" name="stats_search" value="{{ work_stats.search_keyword if work_stats else '' }}" placeholder="Tìm tên, mã NV..." 
                           class="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 outline-none focus:border-blue-500 w-32">
                    <button type="submit" class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition">
                        Lọc
                    </button>
                </div>

                <!-- Lọc theo nhân viên cụ thể -->
                <div class="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1">Nhân viên:</label>
                    <select name="stats_staff_id" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 font-semibold text-slate-700 outline-none focus:border-blue-500 max-w-[150px]">
                        <option value="">Tất cả</option>
                        {% for s in staff_list %}
                        <option value="{{ s.id }}" {% if request.args.get('stats_staff_id') == s.id|string %}selected{% endif %}>
                            {{ s.ho_ten }} ({{ s.vai_tro }})
                        </option>
                        {% endfor %}
                    </select>
                </div>
                {% endif %}
                {% endif %}

                <!-- Lọc theo tháng -->
                <div class="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-200">
                    <label class="text-[11px] font-bold text-slate-500 px-1">Kỳ tháng:</label>
                    <select name="stats_month" onchange="this.form.submit()" class="text-xs bg-white border border-slate-200 rounded-lg px-2 py-1 font-semibold text-slate-700 outline-none focus:border-blue-500">
                        <option value="all" {% if work_stats and work_stats.selected_month == 'all' %}selected{% endif %}>Tất cả các tháng</option>
                        {% if work_stats and work_stats.available_months %}
                        {% for m in work_stats.available_months %}
                        <option value="{{ m.key }}" {% if work_stats.selected_month == m.key %}selected{% endif %}>{{ m.label }}</option>
                        {% endfor %}
                        {% endif %}
                    </select>
                </div>

                <a href="{{ url_for('admin.staff', tab='workstats') }}" class="px-2 py-1 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg font-semibold transition" title="Đặt lại bộ lọc">
                    <i class="fa-solid fa-arrow-rotate-left"></i>
                </a>
            </form>"""

content, ok = robust_replace(content, old_form, new_form)
print("Updated staff.html filter form:", ok)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
