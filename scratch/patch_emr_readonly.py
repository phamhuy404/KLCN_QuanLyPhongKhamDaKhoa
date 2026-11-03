with open('templates/admin/emr.html', 'r', encoding='utf-8') as f:
    s = f.read()

# 1. Bypass date check for isReadOnlyViewer
old_date_check = """            // Kiem tra rang buoc thoi gian hen kham
            const now = new Date();
            const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
            const appDate = String(appointment.ngay_hen || '').slice(0, 10);

            if (appDate > todayStr) {
                alert(`❌ KHÔNG THỂ KHÁM TRƯỚC NGÀY!\\n\\nLịch khám #${appointment.ma_lich_hen || appointment.ma_hen} chưa đến ngày hẹn (Ngày hẹn: ${appointment.ngay_hen}).\\nBác sĩ chỉ có thể thực hiện khám cho các lịch hẹn trong ngày hôm nay!`);
                document.getElementById('emr-encounter-select').value = '';
                resetEncounterEditor();
                return;
            }

            if (appDate === todayStr) {
                const currentHM = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                const appTime = String(appointment.gio_hen || '08:00').slice(0, 5);
                const urlParams = new URLSearchParams(window.location.search);
                const isForceOut = urlParams.get('force_out_of_turn') === '1';

                if (!isForceOut && appTime > currentHM) {
                    const confirmEarly = confirm(`⚠️ XÁC NHẬN KHÁM TRƯỚC LƯỢT / NGOÀI GIỜ:\\n\\nLịch hẹn #${appointment.ma_lich_hen || appointment.ma_hen} của bệnh nhân có giờ hẹn lúc ${appointment.gio_hen} (Hiện tại là ${currentHM}, chưa tới lượt khám).\\n\\nBác sĩ có muốn tiếp nhận khám sớm / khám ngoài giờ cho bệnh nhân không?`);
                    if (!confirmEarly) {
                        document.getElementById('emr-encounter-select').value = '';
                        resetEncounterEditor();
                        return;
                    }
                }
            }"""

new_date_check = """            // Kiem tra rang buoc thoi gian hen kham (Chi ap dung cho Bac si, Admin/Le tan chi xem giam sat)
            if (!isReadOnlyViewer) {
                const now = new Date();
                const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                const appDate = String(appointment.ngay_hen || '').slice(0, 10);

                if (appDate > todayStr) {
                    alert(`❌ KHÔNG THỂ KHÁM TRƯỚC NGÀY!\\n\\nLịch khám #${appointment.ma_lich_hen || appointment.ma_hen} chưa đến ngày hẹn (Ngày hẹn: ${appointment.ngay_hen}).\\nBác sĩ chỉ có thể thực hiện khám cho các lịch hẹn trong ngày hôm nay!`);
                    document.getElementById('emr-encounter-select').value = '';
                    resetEncounterEditor();
                    return;
                }

                if (appDate === todayStr) {
                    const currentHM = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                    const appTime = String(appointment.gio_hen || '08:00').slice(0, 5);
                    const urlParams = new URLSearchParams(window.location.search);
                    const isForceOut = urlParams.get('force_out_of_turn') === '1';

                    if (!isForceOut && appTime > currentHM) {
                        const confirmEarly = confirm(`⚠️ XÁC NHẬN KHÁM TRƯỚC LƯỢT / NGOÀI GIỜ:\\n\\nLịch hẹn #${appointment.ma_lich_hen || appointment.ma_hen} của bệnh nhân có giờ hẹn lúc ${appointment.gio_hen} (Hiện tại là ${currentHM}, chưa tới lượt khám).\\n\\nBác sĩ có muốn tiếp nhận khám sớm / khám ngoài giờ cho bệnh nhân không?`);
                        if (!confirmEarly) {
                            document.getElementById('emr-encounter-select').value = '';
                            resetEncounterEditor();
                            return;
                        }
                    }
                }
            }"""

assert old_date_check in s, "old_date_check not found"
s = s.replace(old_date_check, new_date_check, 1)

# 2. Add applyReadOnlyMode and update resetEncounterEditor
old_reset = """    function resetEncounterEditor() {
        isSessionTransferred = false;
        document.getElementById('emr-step1-lock-notice')?.classList.add('hidden');
        ['emr-ha','emr-mach','emr-t','emr-spo2','emr-symptoms','emr-dropzone'].forEach(id => {
            const element = document.getElementById(id);
            if (!element) return;
            element.readOnly = false;
            element.style.pointerEvents = '';
            element.classList.remove('bg-slate-100','cursor-not-allowed','opacity-85','opacity-50');
        });
        handleReexamDateChange('', 1);
        switchEmrStep(1);
    }"""

new_reset = """    function applyReadOnlyMode() {
        if (!isReadOnlyViewer) return;
        ['emr-ha','emr-mach','emr-t','emr-spo2','emr-symptoms','emr-icd','emr-treatment','emr-advice','emr-reexam','emr-reexam-time','emr-reexam-step4','emr-reexam-time-step4'].forEach(fid => {
            const el = document.getElementById(fid);
            if (el) {
                el.readOnly = true;
                el.classList.add('bg-slate-100', 'cursor-not-allowed');
            }
        });
        document.querySelectorAll('input[name="cls_service_id"]').forEach(cb => {
            cb.disabled = true;
        });
        document.querySelectorAll('#tab-kham button[onclick*="advanceEmrStep"], #tab-kham button[onclick*="transferEmrSession"], #tab-kham button[onclick*="completeExamination"], #tab-cls button[onclick*="transferEmrSession"], #tab-thuoc button[onclick*="finishExaminationRecord"], #tab-thuoc button[onclick*="addMedicineToPrescription"], #btn-finish-cls').forEach(btn => {
            btn.style.display = 'none';
        });
    }

    function resetEncounterEditor() {
        isSessionTransferred = false;
        document.getElementById('emr-step1-lock-notice')?.classList.add('hidden');
        ['emr-ha','emr-mach','emr-t','emr-spo2','emr-symptoms','emr-dropzone'].forEach(id => {
            const element = document.getElementById(id);
            if (!element) return;
            element.readOnly = false;
            element.style.pointerEvents = '';
            element.classList.remove('bg-slate-100','cursor-not-allowed','opacity-85','opacity-50');
        });
        handleReexamDateChange('', 1);
        switchEmrStep(1);
        if (isReadOnlyViewer) {
            applyReadOnlyMode();
        }
    }"""

assert old_reset in s, "old_reset not found"
s = s.replace(old_reset, new_reset, 1)

with open('templates/admin/emr.html', 'w', encoding='utf-8') as f:
    f.write(s)

print("Successfully patched templates/admin/emr.html!")
