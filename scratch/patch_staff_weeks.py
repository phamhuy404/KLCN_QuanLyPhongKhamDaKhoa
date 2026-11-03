import sys
import os

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

# 1. Update timetable-week-select options
old_select = """                        <select id="timetable-week-select" onchange="switchTimetableWeekOffset(parseInt(this.value))" class="text-xs font-semibold border border-slate-300 rounded-xl px-3 py-1.5 bg-slate-50 text-slate-700 outline-none hover:border-blue-400 focus:border-blue-500 focus:bg-white transition cursor-pointer">
                            <option value="2">Tuần +2: {{ week_bounds.next_week_2[0] }} - {{ week_bounds.next_week_2[1] }} (Kế tiếp)</option>
                            <option value="1">Tuần +1: {{ week_bounds.next_week_1[0] }} - {{ week_bounds.next_week_1[1] }} (Tuần tới)</option>
                            <option value="0" selected>Tuần 0: {{ week_bounds.current_week[0] }} - {{ week_bounds.current_week[1] }} (Hiện tại)</option>
                            <option value="-1">Tuần -1: 26/10/2026 - 01/11/2026 (Tuần trước)</option>
                            <option value="-2">Tuần -2: 19/10/2026 - 25/10/2026 (2 tuần trước)</option>
                            <option value="-3">Tuần -3: 12/10/2026 - 18/10/2026 (3 tuần trước)</option>
                            <option value="-4">Tuần -4: 05/10/2026 - 11/10/2026 (4 tuần trước)</option>
                            <option value="-5">Tuần -5: 28/09/2026 - 04/10/2026 (5 tuần trước)</option>
                            <option value="-6">Tuần -6: 21/09/2026 - 27/09/2026 (6 tuần trước)</option>
                            <option value="-7">Tuần -7: 14/09/2026 - 20/09/2026 (Giữa tháng 9)</option>
                            <option value="-8">Tuần -8: 07/09/2026 - 13/09/2026 (Đầu tháng 9)</option>
                        </select>"""

new_select = """                        <select id="timetable-week-select" onchange="switchTimetableWeekOffset(parseInt(this.value))" class="text-xs font-semibold border border-slate-300 rounded-xl px-3 py-1.5 bg-slate-50 text-slate-700 outline-none hover:border-blue-400 focus:border-blue-500 focus:bg-white transition cursor-pointer">
                            <option value="2">Tuần 47/2026 (16/11/2026 - 22/11/2026) [Kế tiếp]</option>
                            <option value="1">Tuần 46/2026 (09/11/2026 - 15/11/2026) [Tuần tới]</option>
                            <option value="0" selected>Tuần 45/2026 (02/11/2026 - 08/11/2026) [Tuần hiện tại]</option>
                            <option value="-1">Tuần 44/2026 (26/10/2026 - 01/11/2026)</option>
                            <option value="-2">Tuần 43/2026 (19/10/2026 - 25/10/2026)</option>
                            <option value="-3">Tuần 42/2026 (12/10/2026 - 18/10/2026)</option>
                            <option value="-4">Tuần 41/2026 (05/10/2026 - 11/10/2026)</option>
                            <option value="-5">Tuần 40/2026 (28/09/2026 - 04/10/2026)</option>
                            <option value="-6">Tuần 39/2026 (21/09/2026 - 27/09/2026)</option>
                            <option value="-7">Tuần 38/2026 (14/09/2026 - 20/09/2026)</option>
                            <option value="-8">Tuần 37/2026 (07/09/2026 - 13/09/2026)</option>
                        </select>"""

content, ok1 = robust_replace(content, old_select, new_select)
print("Updated timetable-week-select:", ok1)

# 2. Update schedule-quick-week in table toolbar
old_quick_week = """                        <select id="schedule-quick-week" onchange="applyWeekFilterToTable(this.value)" class="text-xs border border-blue-200 bg-blue-50/80 text-blue-800 font-semibold rounded-xl px-2.5 py-1.5 outline-none cursor-pointer">
                            <option value="">-- Chọn tuần hiển thị --</option>
                            <option value="current">Cả tuần hiện tại (02/11 - 08/11)</option>
                            <option value="prev1">Tuần trước (26/10 - 01/11)</option>
                            <option value="prev2">2 tuần trước (19/10 - 25/10)</option>
                            <option value="prev3">3 tuần trước (12/10 - 18/10)</option>
                            <option value="prev4">4 tuần trước (05/10 - 11/10)</option>
                            <option value="prev5">5 tuần trước (28/09 - 04/10)</option>
                            <option value="prev6">6 tuần trước (21/09 - 27/09)</option>
                            <option value="prev7">7 tuần trước (14/09 - 20/09)</option>
                            <option value="next1">Tuần tới (09/11 - 15/11)</option>
                            <option value="next2">Tuần +2 (16/11 - 22/11)</option>
                            <option value="all">Toàn bộ lịch sử</option>
                        </select>"""

new_quick_week = """                        <select id="schedule-quick-week" onchange="applyWeekFilterToTable(this.value)" class="text-xs border border-blue-200 bg-blue-50/80 text-blue-800 font-semibold rounded-xl px-2.5 py-1.5 outline-none cursor-pointer">
                            <option value="">-- Chọn tuần trong năm --</option>
                            <option value="current">Tuần 45/2026 (02/11 - 08/11) [Cả tuần này]</option>
                            <option value="prev1">Tuần 44/2026 (26/10 - 01/11)</option>
                            <option value="prev2">Tuần 43/2026 (19/10 - 25/10)</option>
                            <option value="prev3">Tuần 42/2026 (12/10 - 18/10)</option>
                            <option value="prev4">Tuần 41/2026 (05/10 - 11/10)</option>
                            <option value="prev5">Tuần 40/2026 (28/09 - 04/10)</option>
                            <option value="prev6">Tuần 39/2026 (21/09 - 27/09)</option>
                            <option value="prev7">Tuần 38/2026 (14/09 - 20/09)</option>
                            <option value="next1">Tuần 46/2026 (09/11 - 15/11) [Tuần tới]</option>
                            <option value="next2">Tuần 47/2026 (16/11 - 22/11) [Kế tiếp]</option>
                            <option value="all">Toàn bộ lịch sử</option>
                        </select>"""

content, ok2 = robust_replace(content, old_quick_week, new_quick_week)
print("Updated schedule-quick-week:", ok2)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated staff.html weeks successfully!")
