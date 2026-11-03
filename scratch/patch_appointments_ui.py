with open('templates/admin/appointments.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Normalize CRLF to LF
crlf = '\r\n' in text
text = text.replace('\r\n', '\n')

old_doc_else = """            } else {
                doctorCell = `
                    <span class="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200 inline-block mb-1">
                        Chưa phân công
                    </span>
                    <div>
                    ${(currentUserRole === 'ADMIN' || currentUserRole === 'LETAN') ? `
                        <button type="button" onclick="openAssignDoctorModal(${app.id}, ${app.chuyen_khoa_id}, '${app.ngay_hen}', '${app.ma_hen}', '${app.benh_nhan.replace(/'/g, "\\\\'")}', '${app.gio_hen}', '${app.khoa.replace(/'/g, "\\\\"')}')" 
                                class="px-2 py-1 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 font-bold text-[10px] inline-flex items-center gap-1 border border-medical-200 transition-colors">
                            <i class="fa-solid fa-user-plus text-[9px]"></i> Phân công
                        </button>
                    ` : ''}
                    ${currentUserRole === 'BACSI' ? `
                        <button type="button" onclick="claimAppointment(${app.id}, '${app.ma_hen}')" 
                                class="px-2 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-[10px] inline-flex items-center gap-1 border border-emerald-200 transition-colors">
                            <i class="fa-solid fa-hand-holding-medical text-[9px]"></i> Nhận khám
                        </button>
                    ` : ''}
                    </div>
                `;
            }"""

new_doc_else = """            } else {
                doctorCell = `
                    <span class="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200 inline-block mb-1">
                        Chưa phân công
                    </span>
                    <div>
                    ${(currentUserRole === 'ADMIN' || currentUserRole === 'LETAN') ? `
                        <button type="button" onclick="openAssignDoctorModal(${app.id}, ${app.chuyen_khoa_id}, '${app.ngay_hen}', '${app.ma_hen}', '${app.benh_nhan.replace(/'/g, "\\\\'")}', '${app.gio_hen}', '${app.khoa.replace(/'/g, "\\\\"')}')" 
                                class="px-2 py-1 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 font-bold text-[10px] inline-flex items-center gap-1 border border-medical-200 transition-colors">
                            <i class="fa-solid fa-user-plus text-[9px]"></i> Phân công
                        </button>
                    ` : '<span class="text-[10px] text-slate-400 italic">Chờ điều phối</span>'}
                    </div>
                `;
            }"""

if old_doc_else in text:
    text = text.replace(old_doc_else, new_doc_else)
    print('Replaced doc_else')
else:
    print('WARNING: old_doc_else not found!')

old_actions = """                <td class="py-3 px-4 text-center">
                    <div class="flex items-center justify-center gap-1.5">
                        ${(!app.bac_si_id && currentUserRole === 'BACSI') ? `
                        <button type="button" onclick="claimAppointment(${app.id}, '${app.ma_hen}')" 
                                class="px-2 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm" title="Nhận ca khám này">
                            <i class="fa-solid fa-hand-holding-medical text-xs"></i>
                            <span>Nhận</span>
                        </button>
                        ` : ''}
                        ${(!app.bac_si_id && (currentUserRole === 'ADMIN' || currentUserRole === 'LETAN')) ? `
                        <button type="button" onclick="openAssignDoctorModal(${app.id}, ${app.chuyen_khoa_id}, '${app.ngay_hen}', '${app.ma_hen}', '${app.benh_nhan.replace(/'/g, "\\\\'")}', '${app.gio_hen}', '${app.khoa.replace(/'/g, "\\\\"')}')" 
                                class="px-2 py-1 rounded-lg bg-medical-600 hover:bg-medical-700 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm" title="Phân công bác sĩ">
                            <i class="fa-solid fa-user-plus text-xs"></i>
                            <span>Phân công</span>
                        </button>
                        ` : ''}
                        ${app.trang_thai === 'waiting' ? `
                        <button type="button" onclick="acceptAppointment(${app.id}, '${app.ma_hen}')" 
                                class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm transition-all" title="Lễ tân/Admin xác nhận tiếp nhận lịch">
                            <i class="fa-solid fa-check"></i>
                            <span>Tiếp nhận</span>
                        </button>
                        ` : ''}
                        <button type="button" onclick="startEmrExamination(${app.id}, '${app.ma_hen}', ${app.patient_id}, '${app.ngay_hen}', '${app.gio_hen}', '${(app.benh_nhan || '').replace(/'/g, "\\\\'")}')"
                                class="w-7 h-7 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 flex items-center justify-center transition-colors" title="Bắt đầu khám (EMR)">
                            <i class="fa-solid fa-stethoscope text-xs"></i>
                        </button>
                        ${app.trang_thai !== 'cancelled' ? `
                        <button type="button" onclick="cycleAppointmentStatus(${app.id}, '${app.trang_thai}')" 
                                class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition-colors" title="Chuyển trạng thái kế tiếp">
                            <i class="fa-solid fa-rotate text-xs"></i>
                        </button>
                        <button type="button" onclick="cancelAppointment(${app.id}, '${app.ma_hen}')" 
                                class="w-7 h-7 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 flex items-center justify-center transition-colors" title="Hủy lịch hẹn">
                            <i class="fa-solid fa-ban text-xs"></i>
                        </button>
                        ` : ''}
                    </div>
                </td>"""

new_actions = """                <td class="py-3 px-4 text-center">
                    <div class="flex items-center justify-center gap-1.5">
                        ${(currentUserRole === 'ADMIN' || currentUserRole === 'LETAN') ? `
                            ${(!app.bac_si_id) ? `
                            <button type="button" onclick="openAssignDoctorModal(${app.id}, ${app.chuyen_khoa_id}, '${app.ngay_hen}', '${app.ma_hen}', '${app.benh_nhan.replace(/'/g, "\\\\'")}', '${app.gio_hen}', '${app.khoa.replace(/'/g, "\\\\"')}')" 
                                    class="px-2 py-1 rounded-lg bg-medical-600 hover:bg-medical-700 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm" title="Phân công bác sĩ">
                                <i class="fa-solid fa-user-plus text-xs"></i>
                                <span>Phân công</span>
                            </button>
                            ` : ''}
                            ${app.trang_thai === 'waiting' ? `
                            <button type="button" onclick="acceptAppointment(${app.id}, '${app.ma_hen}')" 
                                    class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm transition-all" title="Lễ tân/Admin xác nhận tiếp nhận lịch">
                                <i class="fa-solid fa-check"></i>
                                <span>Tiếp nhận</span>
                            </button>
                            ` : ''}
                            <button type="button" onclick="startEmrExamination(${app.id}, '${app.ma_hen}', ${app.patient_id}, '${app.ngay_hen}', '${app.gio_hen}', '${(app.benh_nhan || '').replace(/'/g, "\\\\'")}')"
                                    class="w-7 h-7 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 flex items-center justify-center transition-colors" title="Xem buồng khám (EMR)">
                                <i class="fa-solid fa-stethoscope text-xs"></i>
                            </button>
                            ${app.trang_thai !== 'cancelled' ? `
                            <button type="button" onclick="cycleAppointmentStatus(${app.id}, '${app.trang_thai}')" 
                                    class="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition-colors" title="Chuyển trạng thái kế tiếp">
                                <i class="fa-solid fa-rotate text-xs"></i>
                            </button>
                            <button type="button" onclick="cancelAppointment(${app.id}, '${app.ma_hen}')" 
                                    class="w-7 h-7 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 flex items-center justify-center transition-colors" title="Hủy lịch hẹn">
                                <i class="fa-solid fa-ban text-xs"></i>
                            </button>
                            ` : ''}
                        ` : `
                            ${app.trang_thai === 'waiting' ? `
                            <span class="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 font-semibold text-[10px] border border-amber-200 inline-flex items-center gap-1">
                                <i class="fa-solid fa-hourglass-half text-[9px]"></i> Chờ tiếp tân duyệt
                            </span>
                            ` : (app.trang_thai === 'cancelled' ? `
                            <span class="text-[10px] text-slate-400 italic">Đã hủy</span>
                            ` : `
                            <button type="button" onclick="startEmrExamination(${app.id}, '${app.ma_hen}', ${app.patient_id}, '${app.ngay_hen}', '${app.gio_hen}', '${(app.benh_nhan || '').replace(/'/g, "\\\\'")}')"
                                    class="px-2.5 py-1 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 font-bold text-[10px] flex items-center gap-1.5 shadow-sm transition-all" title="Bắt đầu khám bệnh EMR">
                                <i class="fa-solid fa-stethoscope text-xs"></i>
                                <span>Khám EMR</span>
                            </button>
                            `)}
                        `}
                    </div>
                </td>"""

if old_actions in text:
    text = text.replace(old_actions, new_actions)
    print('Replaced actions')
else:
    print('WARNING: old_actions not found!')

old_accept = """    // Lễ tân hoặc Admin xác nhận tiếp nhận lịch khám
    async function acceptAppointment(id, maHen) {"""

new_accept = """    // Lễ tân hoặc Admin xác nhận tiếp nhận lịch khám
    async function acceptAppointment(id, maHen) {
        if (currentUserRole === 'BACSI') {
            alert('Bác sĩ không có quyền duyệt hoặc tiếp nhận lịch hẹn! Thao tác này chỉ dành cho Lễ tân hoặc Quản trị viên.');
            return;
        }"""

if old_accept in text:
    text = text.replace(old_accept, new_accept)
    print('Replaced accept')
else:
    print('WARNING: old_accept not found!')

old_cycle = """    // Chuyển đổi trạng thái hẹn qua API
    async function cycleAppointmentStatus(id, currentStatus) {"""

new_cycle = """    // Chuyển đổi trạng thái hẹn qua API
    async function cycleAppointmentStatus(id, currentStatus) {
        if (currentUserRole === 'BACSI') {
            alert('Bác sĩ không có quyền đổi trạng thái lịch hẹn! Thao tác này chỉ dành cho Lễ tân hoặc Quản trị viên.');
            return;
        }"""

if old_cycle in text:
    text = text.replace(old_cycle, new_cycle)
    print('Replaced cycle')
else:
    print('WARNING: old_cycle not found!')

old_cancel = """    // Hủy lịch hẹn qua API
    async function cancelAppointment(id, maHen) {"""

new_cancel = """    // Hủy lịch hẹn qua API
    async function cancelAppointment(id, maHen) {
        if (currentUserRole === 'BACSI') {
            alert('Bác sĩ không có quyền hủy lịch hẹn! Thao tác này chỉ dành cho Lễ tân hoặc Quản trị viên.');
            return;
        }"""

if old_cancel in text:
    text = text.replace(old_cancel, new_cancel)
    print('Replaced cancel')
else:
    print('WARNING: old_cancel not found!')

if crlf:
    text = text.replace('\n', '\r\n')

with open('templates/admin/appointments.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated appointments.html!')
