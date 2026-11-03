with open('templates/admin/appointments.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_doc = text.find("let doctorCell = '';")
end_actions = text.find("tbody.appendChild(tr);", start_doc)

assert start_doc != -1 and end_actions != -1, "Target region not found"

replacement = """let doctorCell = '';
            if (app.bac_si && app.bac_si.trim() !== '') {
                doctorCell = `
                    <span class="font-semibold text-slate-800 block">${app.bac_si}</span>
                    ${(currentUserRole === 'ADMIN' || currentUserRole === 'LETAN') && app.trang_thai !== 'cancelled' && app.trang_thai !== 'completed' ? `
                        <button type="button" onclick="openAssignDoctorModal(${app.id}, ${app.chuyen_khoa_id}, '${app.ngay_hen}', '${app.ma_hen}', '${app.benh_nhan.replace(/'/g, "\\\\'")}', '${app.gio_hen}', '${app.khoa.replace(/'/g, "\\\\"')}')" 
                                class="text-[10px] text-medical-600 hover:text-medical-800 hover:underline inline-flex items-center gap-1 font-semibold mt-0.5">
                            <i class="fa-solid fa-pen-to-square"></i> Đổi bác sĩ
                        </button>
                    ` : ''}
                `;
            } else {
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
                    ` : '<span class="text-[10px] text-slate-400 italic">Chờ tiếp tân phân công</span>'}
                    </div>
                `;
            }

            tr.innerHTML = `
                <td class="py-3 px-4 font-mono font-bold text-medical-700">${app.ma_hen}</td>
                <td class="py-3 px-4">
                    <span class="font-bold text-slate-900 block">${app.gio_hen}</span>
                    <span class="text-[10px] text-slate-400">${app.ngay_hen}</span>
                </td>
                <td class="py-3 px-4">
                    <a href="/admin/patients/${app.patient_id}" class="font-bold text-slate-900 hover:text-medical-700 transition-colors block">
                        ${app.benh_nhan}
                    </a>
                    <span class="text-[10px] text-slate-400 font-mono">${app.ma_bn} • ${app.sdt}</span>
                </td>
                <td class="py-3 px-4">
                    ${doctorCell}
                </td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded-lg bg-teal-50 text-teal-700 font-semibold text-[11px]">${app.khoa}</span>
                </td>
                <td class="py-3 px-4 text-slate-600 truncate max-w-[180px]" title="${app.ly_do}">
                    ${app.ly_do}
                </td>
                <td class="py-3 px-4 text-center">
                    ${statusBadge}
                </td>
                <td class="py-3 px-4 text-center">
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
                                    class="w-7 h-7 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 flex items-center justify-center transition-colors" title="Xem hồ sơ khám (EMR)">
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
                </td>
            `;
            """

text = text[:start_doc] + replacement + text[end_actions:]

with open('templates/admin/appointments.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully applied appointments UI fix!')
