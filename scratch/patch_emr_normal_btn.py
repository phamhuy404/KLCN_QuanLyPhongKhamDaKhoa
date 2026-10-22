with open('templates/admin/emr.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_action_bar = """                <div class="flex items-center gap-2">
                    <button type="button" onclick="window.print()" class="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-print"></i> In Phiếu Khám
                    </button>
                    <button type="button" onclick="completeExamination()" class="px-6 py-2.5 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-md shadow-medical-600/20 flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-circle-check"></i> Hoàn Tất & Chuyển Phiên Khám
                    </button>
                </div>"""

new_action_bar = """                <div class="flex items-center gap-2">
                    <button type="button" onclick="window.print()" class="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-print"></i> In Phiếu Khám
                    </button>
                    <button type="button" onclick="completeNormalExamination()" class="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs shadow-md shadow-teal-500/20 flex items-center gap-1.5 cursor-pointer" title="Áp dụng khi khám lâm sàng bình thường, không cần cận lâm sàng và không cần kê thuốc">
                        <i class="fa-solid fa-heart-pulse"></i> Sức Khỏe Tốt (Xuất Hóa Đơn Ngay)
                    </button>
                    <button type="button" onclick="completeExamination()" class="px-6 py-2.5 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-md shadow-medical-600/20 flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-circle-check"></i> Hoàn Tất & Chuyển Phiên Khám
                    </button>
                </div>"""

c = c.replace(old_action_bar, new_action_bar).replace(old_action_bar.replace('\n', '\r\n'), new_action_bar.replace('\n', '\r\n'))

old_script_end = """        fetch('/api/emr/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(`✅ THÀNH CÔNG!\\n- Đã lưu phiếu khám: ${data.ma_phieu}\\n- Chỉ định cận lâm sàng đã chuyển sang Khoa CLS cho Kỹ thuật viên.\\n- Toa thuốc đã chuyển sang Kho Dược cho Dược sĩ.\\n- Hóa đơn viện phí tổng hợp đã được tự động sinh.`);
                window.location.reload();
            } else {
                alert('❌ KHÔNG THỂ LƯU PHIÊN KHÁM:\\n' + data.message);
            }
        })
        .catch(err => {
            alert('Lỗi kết nối khi lưu phiên khám: ' + err);
        });
    }"""

new_script_end = """        fetch('/api/emr/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(`✅ THÀNH CÔNG!\\n- Đã lưu phiếu khám: ${data.ma_phieu}\\n- Chỉ định cận lâm sàng đã chuyển sang Khoa CLS cho Kỹ thuật viên.\\n- Toa thuốc đã chuyển sang Kho Dược cho Dược sĩ.\\n- Hóa đơn viện phí ban đầu đã được tự động sinh.`);
                window.location.reload();
            } else {
                alert('❌ KHÔNG THỂ LƯU PHIÊN KHÁM:\\n' + data.message);
            }
        })
        .catch(err => {
            alert('Lỗi kết nối khi lưu phiên khám: ' + err);
        });
    }

    // Kết thúc phiên khám lâm sàng bình thường một chạm (không cần CLS, không kê thuốc)
    function completeNormalExamination() {
        if (!confirm('Xác nhận: Bệnh nhân có kết quả khám lâm sàng bình thường (sức khỏe tốt)?\\nHệ thống sẽ kết thúc phiên khám và tự động xuất hóa đơn viện phí tiền khám ngay lập tức.')) {
            return;
        }

        const payload = {
            patient_id: currentSelectedPatientId,
            reason: 'Khám sức khỏe tổng quát',
            symptoms: 'Không ghi nhận triệu chứng bất thường',
            diagnosis: 'Z00.0 - Khám sức khỏe tổng quát (Bình thường)',
            icd: 'Z00.0',
            treatment: 'Tư vấn chế độ dinh dưỡng, lối sống lành mạnh',
            advice: 'Duy trì lối sống lành mạnh, tái khám định kỳ sau 6 tháng hoặc khi có dấu hiệu bất thường',
            reexam_date: null,
            lab_services: [],
            medicines: []
        };

        fetch('/api/emr/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(`✅ KẾT THÚC PHIÊN KHÁM THÀNH CÔNG!\\n- Đã lưu phiếu khám: ${data.ma_phieu}\\n- Chẩn đoán: Khám sức khỏe bình thường\\n- Hóa đơn viện phí tiền khám đã được xuất thành công.`);
                window.location.reload();
            } else {
                alert('❌ KHÔNG THỂ LƯU PHIÊN KHÁM:\\n' + data.message);
            }
        })
        .catch(err => {
            alert('Lỗi kết nối khi lưu: ' + err);
        });
    }"""

c = c.replace(old_script_end, new_script_end).replace(old_script_end.replace('\n', '\r\n'), new_script_end.replace('\n', '\r\n'))

with open('templates/admin/emr.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated templates/admin/emr.html successfully!')
