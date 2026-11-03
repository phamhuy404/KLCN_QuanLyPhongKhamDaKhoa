import io
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('templates/admin/staff.html', 'r', encoding='utf-8') as f:
    h_code = f.read()

# 1. Update filterSchedulesTable function to render dynamically from window.schedulesData
old_filter_fn = """function filterSchedulesTable() {
    const start = document.getElementById('schedule-start-date')?.value || '';
    const end = document.getElementById('schedule-end-date')?.value || '';
    const ca = document.getElementById('schedule-ca-filter')?.value || '';
    const onlyMine = document.getElementById('schedule-mine-filter')?.checked || false;

    // Xoa cac tieu de phan ngay cu
    document.querySelectorAll('.schedule-day-group-header').forEach(el => el.remove());

    const rows = document.querySelectorAll('.schedule-row');
    let visible = 0;
    let lastDate = null;
    let dayCount = 0;
    let dayHeaderRow = null;

    rows.forEach(r => {
        const rDate = r.getAttribute('data-date') || '';
        const rCa = r.getAttribute('data-ca') || '';
        const rMine = r.getAttribute('data-mine') === '1';

        const matchStart = !start || rDate >= start;
        const matchEnd = !end || rDate <= end;
        const matchCa = !ca || rCa === ca;
        const matchMine = !onlyMine || rMine;

        if (matchStart && matchEnd && matchCa && matchMine) {
            r.classList.remove('hidden');
            visible++;

            // Chen tieu de phan chia theo tung ngay
            if (rDate !== lastDate) {
                lastDate = rDate;
                dayCount = 1;
                const dObj = new Date(rDate + 'T00:00:00');
                const dayOfWeekNames = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
                const dayOfWeek = isNaN(dObj.getDay()) ? '' : dayOfWeekNames[dObj.getDay()];
                const parts = rDate.split('-');
                const fmtDate = parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : rDate;

                dayHeaderRow = document.createElement('tr');
                dayHeaderRow.className = 'schedule-day-group-header bg-gradient-to-r from-sky-50 via-slate-50 to-indigo-50/40 border-y-2 border-sky-200 text-sky-900 font-bold';
                dayHeaderRow.innerHTML = `
                    <td colspan="6" class="px-5 py-2">
                        <div class="flex items-center justify-between">
                            <span class="flex items-center gap-2 text-xs">
                                <i class="fa-solid fa-calendar-day text-sky-600"></i>
                                <span class="font-extrabold text-slate-800">${dayOfWeek}</span> • Ngày <span class="text-sky-700 font-extrabold">${fmtDate}</span>
                            </span>
                            <span class="day-shift-badge text-[11px] font-semibold text-sky-700 bg-white px-2 py-0.5 rounded-md border border-sky-200 shadow-2xs">
                                1 ca trực
                            </span>
                        </div>
                    </td>
                `;
                r.parentNode.insertBefore(dayHeaderRow, r);
            } else {
                dayCount++;
                if (dayHeaderRow) {
                    const badge = dayHeaderRow.querySelector('.day-shift-badge');
                    if (badge) badge.innerText = `${dayCount} ca trực`;
                }
            }
        } else {
            r.classList.add('hidden');
        }
    });

    const counter = document.getElementById('schedules-visible-count');
    if (counter) counter.innerText = visible;
}"""

new_filter_fn = """function filterSchedulesTable() {
    const start = document.getElementById('schedule-start-date')?.value || '';
    const end = document.getElementById('schedule-end-date')?.value || '';
    const ca = document.getElementById('schedule-ca-filter')?.value || '';
    const onlyMine = document.getElementById('schedule-mine-filter')?.checked || false;
    const tbody = document.getElementById('schedules-tbody');
    if (!tbody || !window.schedulesData) return;

    const allData = window.schedulesData || [];
    const filtered = allData.filter(s => {
        const rDate = s.ngay_lam || '';
        const rCa = String(s.ca_lam || '');
        const rMine = Boolean(s.is_my_shift);

        if (start && rDate < start) return false;
        if (end && rDate > end) return false;
        if (ca && rCa !== ca) return false;
        if (onlyMine && !rMine) return false;
        return true;
    });

    const counter = document.getElementById('schedules-visible-count');
    if (counter) counter.innerText = filtered.length;

    const displayList = filtered.slice(0, 100);
    const dayOfWeekNames = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];

    let html = '';
    let lastDate = null;

    displayList.forEach(sc => {
        const rDate = sc.ngay_lam || '';
        if (rDate !== lastDate) {
            lastDate = rDate;
            const dObj = new Date(rDate + 'T00:00:00');
            const dayOfWeek = isNaN(dObj.getDay()) ? '' : dayOfWeekNames[dObj.getDay()];
            const parts = rDate.split('-');
            const fmtDate = parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : rDate;
            const countForDay = filtered.filter(x => x.ngay_lam === rDate).length;

            html += `
            <tr class="schedule-day-group-header bg-gradient-to-r from-sky-50 via-slate-50 to-indigo-50/40 border-y-2 border-sky-200 text-sky-900 font-bold">
                <td colspan="6" class="px-5 py-2">
                    <div class="flex items-center justify-between">
                        <span class="flex items-center gap-2 text-xs">
                            <i class="fa-solid fa-calendar-day text-sky-600"></i>
                            <span class="font-extrabold text-slate-800">${dayOfWeek}</span> • Ngày <span class="text-sky-700 font-extrabold">${fmtDate}</span>
                        </span>
                        <span class="day-shift-badge text-[11px] font-semibold text-sky-700 bg-white px-2 py-0.5 rounded-md border border-sky-200 shadow-2xs">
                            ${countForDay} ca trực
                        </span>
                    </div>
                </td>
            </tr>`;
        }

        const caBadge = sc.ca_lam == 1
            ? 'bg-amber-50 text-amber-700 border border-amber-200'
            : (sc.ca_lam == 2 ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-purple-50 text-purple-700 border border-purple-200');

        let statusBadge = '';
        const stt = sc.trang_thai_duyet || 'DA_DUYET';
        if (stt === 'DA_DUYET') {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200"><i class="fa-solid fa-circle-check mr-0.5"></i> Đã duyệt</span>';
        } else if (stt === 'CHO_DUYET') {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200"><i class="fa-solid fa-hourglass-half mr-0.5"></i> Chờ duyệt</span>';
        } else if (stt === 'CHO_HUY') {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-orange-50 text-orange-700 border border-orange-200"><i class="fa-solid fa-circle-exclamation mr-0.5"></i> Đang xin hủy ca</span>';
        } else if (stt === 'DA_HUY') {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-slate-100 text-slate-500 border border-slate-200"><i class="fa-solid fa-ban mr-0.5"></i> Đã hủy ca</span>';
        } else {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-rose-50 text-rose-700 border border-rose-200"><i class="fa-solid fa-xmark mr-0.5"></i> Từ chối</span>';
        }

        const canManage = (window.currentUser && window.currentUser.vai_tro === 'ADMIN');
        let actionBtns = '';
        if (sc.can_request_cancel) {
            actionBtns += `<button onclick="openCancelRequestModal('${sc.id}', '${sc.ngay_lam}', '${sc.ten_ca}')" class="px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[11px] font-semibold transition flex items-center gap-1 shadow-sm"><i class="fa-solid fa-paper-plane text-[10px]"></i> Xin hủy ca</button>`;
        }
        if (sc.is_my_shift && sc.is_next_2_weeks) {
            actionBtns += `<button onclick="deleteSchedule('${sc.id}')" class="px-2 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-[11px] font-semibold transition flex items-center gap-1 border border-rose-200"><i class="fa-solid fa-trash-can text-[10px]"></i> Hủy lịch</button>`;
        }
        if (canManage && !sc.is_past) {
            actionBtns += `<button type="button" onclick="openAssignRoomModal(${sc.nhan_vien_id || sc.staff_id}, '${(sc.ten_bac_si || '').replace(/'/g, "\\\\'")}', ${sc.phong_kham_id || 'null'}, '${sc.ngay_lam}', ${sc.ca_lam})" class="px-2 py-1 bg-sky-50 hover:bg-sky-100 text-sky-700 rounded-lg text-[11px] font-semibold transition flex items-center gap-1 border border-sky-200" title="Phân phòng khám"><i class="fa-solid fa-door-open text-[10px]"></i> Phân phòng</button>`;
            actionBtns += `<button onclick="editScheduleById('${sc.id}')" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition" title="Sửa ca"><i class="fa-solid fa-pen text-xs"></i></button>`;
            actionBtns += `<button onclick="deleteSchedule('${sc.id}')" class="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition" title="Xóa ca"><i class="fa-solid fa-trash-can text-xs"></i></button>`;
        }

        html += `
        <tr class="hover:bg-slate-50/70 transition schedule-row ${sc.is_my_shift ? 'bg-blue-50/40 border-l-4 border-l-blue-500' : ''}" data-date="${sc.ngay_lam}" data-ca="${sc.ca_lam}" data-mine="${sc.is_my_shift ? '1' : '0'}">
            <td class="px-5 py-3.5">
                <div class="font-bold text-slate-800">${sc.ngay_lam}</div>
                <div class="text-[11px] text-slate-400">
                    ${sc.is_current_week ? '<span class="text-amber-600 font-semibold"><i class="fa-solid fa-lock text-[10px] mr-0.5"></i> Tuần hiện tại</span>' : (sc.is_next_2_weeks ? '<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-calendar-check text-[10px] mr-0.5"></i> 2 tuần tới (Mở)</span>' : '<span class="text-slate-400">Đã qua</span>')}
                </div>
            </td>
            <td class="px-5 py-3.5">
                <div class="font-semibold text-slate-800 flex items-center gap-1.5">
                    <span>${sc.ten_bac_si || sc.ten_nhan_vien}</span>
                    ${sc.is_my_shift ? '<span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-bold rounded-full">Lịch của bạn</span>' : ''}
                </div>
                <div class="text-[11px] text-slate-500">${sc.ten_vai_tro || 'Nhân viên y tế'} • ${sc.ten_khoa || 'Toàn viện'}</div>
            </td>
            <td class="px-5 py-3.5">
                <span class="px-2 py-1 text-[11px] font-semibold rounded-lg ${caBadge}">${sc.ten_ca || ('Ca ' + sc.ca_lam)}</span>
            </td>
            <td class="px-5 py-3.5">
                <div class="font-medium text-slate-700">${sc.ten_phong || 'Khu vực tiếp đón / Khoa'}</div>
                ${sc.vi_tri_tang ? `<div class="text-[11px] text-slate-400">${sc.vi_tri_tang}</div>` : ''}
            </td>
            <td class="px-5 py-3.5">${statusBadge}</td>
            <td class="px-5 py-3.5 text-right"><div class="flex items-center justify-end gap-1.5">${actionBtns}</div></td>
        </tr>`;
    });

    if (filtered.length > 100) {
        html += `
        <tr>
            <td colspan="6" class="px-5 py-3 text-center text-xs text-slate-500 bg-slate-50 border-t border-slate-200 font-medium">
                <i class="fa-solid fa-circle-info text-blue-500 mr-1.5"></i>
                Đang hiển thị 100 ca trực đầu tiên (Tổng tìm thấy: <strong>${filtered.length}</strong> ca). Vui lòng chọn lọc theo ngày hoặc ca cụ thể để xem chi tiết.
            </td>
        </tr>`;
    }

    if (filtered.length === 0) {
        html = `
        <tr>
            <td colspan="6" class="px-5 py-10 text-center text-slate-400">
                <i class="fa-solid fa-calendar-xmark text-2xl block mb-2"></i>
                Không tìm thấy ca làm việc nào phù hợp với bộ lọc
            </td>
        </tr>`;
    }

    tbody.innerHTML = html;
}"""

assert old_filter_fn in h_code, "old_filter_fn not found"
h_code = h_code.replace(old_filter_fn, new_filter_fn, 1)

with open('templates/admin/staff.html', 'w', encoding='utf-8') as f:
    f.write(h_code)

print("Updated filterSchedulesTable successfully!")
