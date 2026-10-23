import sys

emr_script_content = """<script type="application/json" id="emr-patients-data">
    {{ patients | tojson | safe }}
</script>

<script>
    let rawPatients = JSON.parse(document.getElementById('emr-patients-data').textContent || '[]');
    let currentSelectedPatientId = rawPatients.length > 0 ? rawPatients[0].id : 1;
    let currentActiveEncounterId = null;
    let prescriptionItems = [];
    let emrSelectedImages = [];

    // Helper: phân tích mảng ảnh từ chuỗi JSON hoặc URL đơn
    function parseImageFiles(str) {
        if (!str) return [];
        if (Array.isArray(str)) return str;
        if (typeof str === 'string' && str.trim().startsWith('[') && str.trim().endsWith(']')) {
            try {
                return JSON.parse(str);
            } catch (e) {
                return [str];
            }
        }
        return [str];
    }

    // Khởi tạo một số thuốc mẫu ban đầu để bác sĩ tiện chỉnh sửa
    prescriptionItems.push({
        thuoc_id: 6,
        ten_thuoc: 'Paracetamol 500mg Hậu Giang',
        so_luong: 20,
        don_vi_tinh: 'Viên',
        so_luong_ton: 5000,
        don_gia: 2000,
        lieu_dung: 'Uống 1-2 viên khi sốt trên 38.5°C',
        cach_dung: 'Uống sau ăn no, cách 4-6h/lần'
    });
    prescriptionItems.push({
        thuoc_id: 11,
        ten_thuoc: 'Esomeprazole 20mg Stada',
        so_luong: 28,
        don_vi_tinh: 'Viên',
        so_luong_ton: 2800,
        don_gia: 8000,
        lieu_dung: 'Uống 1 viên/lần, ngày 2 lần',
        cach_dung: 'Uống trước ăn sáng và ăn tối 30 phút'
    });
    renderPrescriptionTable();

    // ==========================================
    // Quản lý kéo thả và xem trước nhiều ảnh EMR (Tối đa 10 ảnh, lưới 2x2 cuộn được)
    // ==========================================
    function handleEmrDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        const dz = document.getElementById('emr-dropzone');
        if (dz) dz.classList.add('border-medical-500', 'bg-medical-50/50');
    }

    function handleEmrDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        const dz = document.getElementById('emr-dropzone');
        if (dz) dz.classList.remove('border-medical-500', 'bg-medical-50/50');
    }

    function handleEmrDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        const dz = document.getElementById('emr-dropzone');
        if (dz) dz.classList.remove('border-medical-500', 'bg-medical-50/50');
        if (e.dataTransfer && e.dataTransfer.files) {
            handleEmrFilesSelect(e.dataTransfer.files);
        }
    }

    function handleEmrFilesSelect(files) {
        if (!files || files.length === 0) return;
        const remaining = 10 - emrSelectedImages.length;
        if (remaining <= 0) {
            alert('Bạn đã chọn tối đa 10 ảnh khám lâm sàng!');
            return;
        }

        const filesToProcess = Array.from(files).slice(0, remaining);
        let processedCount = 0;

        filesToProcess.forEach(file => {
            if (!file.type.startsWith('image/')) {
                processedCount++;
                return;
            }
            const reader = new FileReader();
            reader.onload = function(e) {
                emrSelectedImages.push(e.target.result);
                processedCount++;
                if (processedCount === filesToProcess.length) {
                    renderEmrThumbnails();
                }
            };
            reader.readAsDataURL(file);
        });
    }

    function removeEmrImage(index) {
        emrSelectedImages.splice(index, 1);
        renderEmrThumbnails();
    }

    function clearAllEmrImages() {
        emrSelectedImages = [];
        renderEmrThumbnails();
        const input = document.getElementById('emr-image-input');
        if (input) input.value = '';
    }

    function renderEmrThumbnails() {
        const container = document.getElementById('emr-preview-container');
        const grid = document.getElementById('emr-thumbnails-grid');
        const badge = document.getElementById('emr-image-count-badge');
        if (!container || !grid) return;

        badge.innerText = `${emrSelectedImages.length} / 10 ảnh`;

        if (emrSelectedImages.length === 0) {
            container.classList.add('hidden');
            grid.innerHTML = '';
            return;
        }

        container.classList.remove('hidden');
        grid.innerHTML = '';

        emrSelectedImages.forEach((imgSrc, idx) => {
            const card = document.createElement('div');
            card.className = "relative group rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-sm aspect-video sm:aspect-square flex items-center justify-center";
            card.innerHTML = `
                <img src="${imgSrc}" alt="Ảnh lâm sàng #${idx+1}" 
                     onclick="openEmrImageModal('${imgSrc}', 'Ảnh khám lâm sàng #${idx+1}', 'Tư liệu khám và hội chẩn')"
                     class="w-full h-full object-cover cursor-pointer hover:scale-105 transition-all duration-200">
                <span class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/60 text-white text-[10px] font-mono">#${idx+1}</span>
                <button type="button" onclick="removeEmrImage(${idx})" title="Xóa ảnh này"
                        class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-rose-600/90 hover:bg-rose-700 text-white flex items-center justify-center text-xs shadow-md transition-all cursor-pointer">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            `;
            grid.appendChild(card);
        });
    }

    // ==========================================
    // Chọn bệnh nhân & đồng bộ trạng thái EMR
    // ==========================================
    function selectEmrPatient(id) {
        currentSelectedPatientId = parseInt(id);
        const p = rawPatients.find(x => x.id === currentSelectedPatientId);
        if (!p) return;

        document.getElementById('current-patient-name').innerText = p.ho_ten;
        document.getElementById('current-patient-avatar').innerText = p.ho_ten.charAt(0);
        document.getElementById('current-patient-code').innerText = p.ma_benh_nhan;
        document.getElementById('current-patient-meta').innerText = `${p.gioi_tinh || 'Nam'} • ${p.ngay_sinh || ''}`;
        document.getElementById('current-patient-blood').innerText = p.nhom_mau || 'Chưa rõ';
        
        const variantEl = document.getElementById('current-patient-blood-variant');
        if (variantEl) {
            variantEl.innerText = p.ghi_chu_nhom_mau || '';
            variantEl.style.display = p.ghi_chu_nhom_mau ? 'inline-block' : 'none';
        }

        document.getElementById('current-patient-bhyt').innerText = p.bhyt || 'Không áp dụng';
        
        // Cảnh báo dị ứng nổi bật
        const allergyBox = document.getElementById('allergy-warning-box');
        const allergyEl = document.getElementById('current-patient-allergy');
        const allergyVal = p.di_ung || '';
        const hasAllergy = allergyVal && allergyVal !== 'Không có' && allergyVal !== 'Không ghi nhận dị ứng thuốc' && allergyVal !== 'Không ghi nhận dị ứng';
        
        if (allergyEl) allergyEl.innerText = allergyVal || 'Không ghi nhận dị ứng thuốc';
        if (allergyBox) {
            if (hasAllergy) {
                allergyBox.className = "p-3 bg-rose-50 border border-rose-300 rounded-xl text-xs flex items-center justify-between text-rose-800 animate-pulse";
            } else {
                allergyBox.className = "p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs flex items-center justify-between text-emerald-800";
            }
        }

        document.getElementById('current-patient-dossier-btn').href = `/admin/patients/${id}`;

        // Kiểm tra phiên khám đang chờ kết quả CLS (để kích hoạt nút Kết Luận & Hoàn Tất sau CLS)
        let activeEncounter = null;
        if (p && p.lich_su_kham && Array.isArray(p.lich_su_kham)) {
            activeEncounter = p.lich_su_kham.find(e => e.trang_thai === 'Chờ kết quả CLS' || e.trang_thai === 'Đang khám');
        }
        const btnFinishCls = document.getElementById('btn-finish-cls');
        const bannerPending = document.getElementById('emr-pending-finish-banner');
        if (activeEncounter) {
            currentActiveEncounterId = activeEncounter.id;
            if (btnFinishCls) btnFinishCls.classList.remove('hidden');
            if (bannerPending) {
                bannerPending.classList.remove('hidden');
                document.getElementById('pending-finish-code').innerText = activeEncounter.ma_phieu;
            }
            if (activeEncounter.chan_doan_icd) document.getElementById('emr-icd').value = activeEncounter.chan_doan_icd;
            if (activeEncounter.huong_dieu_tri) document.getElementById('emr-treatment').value = activeEncounter.huong_dieu_tri;
            if (activeEncounter.loi_dan) document.getElementById('emr-advice').value = activeEncounter.loi_dan;
        } else {
            currentActiveEncounterId = null;
            if (btnFinishCls) btnFinishCls.classList.add('hidden');
            if (bannerPending) bannerPending.classList.add('hidden');
        }

        // Render danh sách kết quả cận lâm sàng của bệnh nhân
        renderPatientClsResults(p);

        // Reset highlight card
        rawPatients.forEach(item => {
            const card = document.getElementById(`patient-card-${item.id}`);
            if (card) {
                if (item.id === currentSelectedPatientId) {
                    card.className = "p-3.5 rounded-xl border border-medical-500 bg-medical-50/50 cursor-pointer transition-all space-y-2 hover:shadow-sm";
                } else {
                    card.className = "p-3.5 rounded-xl border border-slate-100 hover:border-medical-200 bg-white hover:bg-slate-50/50 cursor-pointer transition-all space-y-2";
                }
            }
        });
    }

    if (rawPatients.length > 0) {
        selectEmrPatient(rawPatients[0].id);
    }

    function switchEmrTab(tabId) {
        ['tab-kham', 'tab-cls', 'tab-thuoc', 'tab-view-cls'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('hidden');
        });
        ['btn-tab-kham', 'btn-tab-cls', 'btn-tab-thuoc', 'btn-tab-view-cls'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.className = "px-4 py-2 rounded-xl text-slate-500 hover:text-slate-800 transition-all";
        });

        const target = document.getElementById(tabId);
        if (target) target.classList.remove('hidden');
        const activeBtn = document.getElementById(`btn-${tabId}`);
        if (activeBtn) activeBtn.className = "px-4 py-2 rounded-xl bg-medical-50 text-medical-700 font-bold transition-all";
    }

    function renderPatientClsResults(p) {
        const container = document.getElementById('emr-patient-cls-container');
        const badge = document.getElementById('emr-patient-cls-badge');
        if (!container || !badge) return;

        let allCls = [];
        if (p && p.lich_su_kham && Array.isArray(p.lich_su_kham)) {
            p.lich_su_kham.forEach(enc => {
                if (enc.can_lam_sang && Array.isArray(enc.can_lam_sang)) {
                    enc.can_lam_sang.forEach(item => {
                        allCls.push({
                            ...item,
                            ma_phieu: enc.ma_phieu,
                            thoi_gian_kham: enc.thoi_gian_kham
                        });
                    });
                }
            });
        }

        badge.innerText = `${allCls.length} kết quả`;

        if (allCls.length === 0) {
            container.innerHTML = `
                <div class="py-10 text-center text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200 space-y-2">
                    <div class="w-10 h-10 rounded-xl bg-white text-slate-400 flex items-center justify-center mx-auto shadow-sm">
                        <i class="fa-solid fa-flask-vial"></i>
                    </div>
                    <p class="font-bold text-slate-700 text-xs">Chưa có kết quả cận lâm sàng nào</p>
                    <p class="text-[11px] text-slate-400">Bệnh nhân chưa thực hiện xét nghiệm hoặc chẩn đoán hình ảnh nào trong hệ thống.</p>
                </div>
            `;
            return;
        }

        let html = `
            <div class="overflow-x-auto border border-slate-100 rounded-xl">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                        <tr>
                            <th class="py-2.5 px-3">Tên xét nghiệm / Kỹ thuật</th>
                            <th class="py-2.5 px-3">Phân loại</th>
                            <th class="py-2.5 px-3">Đợt khám</th>
                            <th class="py-2.5 px-3">KTV Thực hiện</th>
                            <th class="py-2.5 px-3">Kết quả / Nhận xét</th>
                            <th class="py-2.5 px-3 text-center">Ảnh chụp / Tư liệu</th>
                            <th class="py-2.5 px-3 text-center">Trạng thái</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
        `;

        allCls.forEach(c => {
            const images = parseImageFiles(c.file_ket_qua);
            let imgBtnHtml = '<span class="text-slate-400 text-[11px]">Không có ảnh</span>';
            if (images.length > 0) {
                imgBtnHtml = `
                    <button type="button" onclick="openEmrImageModal('${images[0]}', '${c.ten}', '${c.ket_qua || ''}')" class="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[11px] inline-flex items-center gap-1.5 transition-all shadow-sm cursor-pointer">
                        <i class="fa-solid fa-images"></i>
                        <span>${images.length > 1 ? images.length + ' ảnh' : 'Xem ảnh'}</span>
                    </button>
                `;
            }
            html += `
                <tr class="hover:bg-slate-50/50">
                    <td class="py-2.5 px-3 font-bold text-slate-800">${c.ten || 'Chỉ định CLS'}</td>
                    <td class="py-2.5 px-3 text-slate-500">${c.loai || 'CĐHA'}</td>
                    <td class="py-2.5 px-3 text-slate-500 font-mono text-[11px]">${c.ma_phieu || 'EMR'}</td>
                    <td class="py-2.5 px-3 text-slate-600">${c.bac_si_thuc_hien || 'KTV'}</td>
                    <td class="py-2.5 px-3 text-teal-800 font-medium">${c.ket_qua || 'Chưa có kết luận'}</td>
                    <td class="py-2.5 px-3 text-center">${imgBtnHtml}</td>
                    <td class="py-2.5 px-3 text-center">
                        <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold">
                            ${c.trang_thai || 'Hoàn tất'}
                        </span>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table></div>`;
        container.innerHTML = html;
    }

    function openEmrImageModal(imageUrl, title, desc) {
        const modal = document.getElementById('emr-image-modal');
        const img = document.getElementById('emr-image-modal-img');
        const titleEl = document.getElementById('emr-image-modal-title');
        const descEl = document.getElementById('emr-image-modal-desc');
        if (!modal || !img) return;

        img.src = imageUrl;
        if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-image text-medical-600"></i> ${title || 'Ảnh chụp Cận lâm sàng'}`;
        if (descEl) descEl.innerText = desc ? `Kết luận: ${desc}` : 'Hình ảnh chẩn đoán kỹ thuật số chuẩn HD';
        modal.classList.remove('hidden');
    }

    function closeEmrImageModal() {
        const modal = document.getElementById('emr-image-modal');
        if (modal) modal.classList.add('hidden');
    }

    function updateClsCount() {
        const checked = document.querySelectorAll('input[name="cls_service_id"]:checked');
        document.getElementById('cls-selected-count').innerText = `${checked.length} kỹ thuật được chọn`;
    }

    // Xử lý khi chọn thuốc từ dropdown: Cảnh báo tồn kho ít & Cảnh báo dị ứng thời gian thực
    function onMedicineSelected() {
        const sel = document.getElementById('select-medicine');
        const opt = sel.options[sel.selectedIndex];
        const warningBanner = document.getElementById('stock-warning-banner');
        const errorBanner = document.getElementById('stock-error-banner');
        errorBanner.classList.add('hidden');

        if (!opt || !opt.value) {
            warningBanner.classList.add('hidden');
            const allergyBanner = document.getElementById('allergy-danger-banner');
            if (allergyBanner) allergyBanner.classList.add('hidden');
            return;
        }

        const ton = parseInt(opt.getAttribute('data-ton') || 0);
        const minStock = parseInt(opt.getAttribute('data-min') || 20);
        const name = opt.getAttribute('data-name');
        const dvt = opt.getAttribute('data-dvt');
        const defaultUsage = opt.getAttribute('data-usage');

        document.getElementById('input-medicine-usage').value = defaultUsage || 'Uống sau ăn 30 phút';

        // 1. CẢNH BÁO TỒN KHO ÍT
        if (ton <= minStock) {
            document.getElementById('warning-med-name').innerText = name;
            document.getElementById('warning-stock-qty').innerText = `${ton} ${dvt}`;
            warningBanner.classList.remove('hidden');
        } else {
            warningBanner.classList.add('hidden');
        }

        // 2. CẢNH BÁO DỊ ỨNG THUỐC THỜI GIAN THỰC
        const p = rawPatients.find(x => x.id === currentSelectedPatientId);
        const allergyBanner = document.getElementById('allergy-danger-banner');
        const allergyText = document.getElementById('allergy-danger-text');
        const allergyVal = (p && p.di_ung) ? p.di_ung.toLowerCase().trim() : '';
        const hasAllergy = allergyVal && allergyVal !== 'không có' && allergyVal !== 'không ghi nhận dị ứng' && allergyVal !== 'không ghi nhận dị ứng thuốc';

        if (hasAllergy && name && allergyBanner) {
            const medLower = name.toLowerCase();
            const keywords = allergyVal.split(/[,;\\s]+/).filter(k => k.length > 2);
            const isSuspected = keywords.some(k => medLower.includes(k)) || medLower.includes(allergyVal);
            if (isSuspected) {
                allergyText.innerHTML = `Bệnh nhân có tiền sử dị ứng: <strong class="text-rose-700">${p.di_ung}</strong>. Thuốc <strong class="text-slate-900">${name}</strong> có nguy cơ gây dị ứng phản vệ! Bác sĩ hãy kiểm tra kỹ trước khi thêm vào đơn.`;
                allergyBanner.classList.remove('hidden');
            } else {
                allergyBanner.classList.add('hidden');
            }
        } else if (allergyBanner) {
            allergyBanner.classList.add('hidden');
        }
    }

    // Thêm thuốc vào đơn khám
    function addMedicineToPrescription() {
        const sel = document.getElementById('select-medicine');
        const opt = sel.options[sel.selectedIndex];
        if (!opt || !opt.value) {
            alert('Vui lòng chọn thuốc từ danh mục trước khi thêm!');
            return;
        }

        const thuocId = parseInt(opt.value);
        const name = opt.getAttribute('data-name');
        const ton = parseInt(opt.getAttribute('data-ton') || 0);
        const dvt = opt.getAttribute('data-dvt') || 'Viên';
        const price = parseFloat(opt.getAttribute('data-price') || 0);
        const qty = parseInt(document.getElementById('input-medicine-qty').value || 1);
        const usage = document.getElementById('input-medicine-usage').value.trim();

        // Kiểm tra số lượng tồn kho
        const errBanner = document.getElementById('stock-error-banner');
        if (qty > ton) {
            document.getElementById('err-requested-qty').innerText = `${qty} ${dvt}`;
            document.getElementById('err-avail-qty').innerText = `${ton} ${dvt}`;
            errBanner.classList.remove('hidden');
            alert(`Lỗi tồn kho: Thuốc "${name}" chỉ còn tồn ${ton} ${dvt}, không thể kê vượt quá số lượng tồn!`);
            return;
        }
        errBanner.classList.add('hidden');

        // Kiểm tra cảnh báo dị ứng trước khi cho phép thêm
        const p = rawPatients.find(x => x.id === currentSelectedPatientId);
        const allergyVal = (p && p.di_ung) ? p.di_ung.toLowerCase().trim() : '';
        const hasAllergy = allergyVal && allergyVal !== 'không có' && allergyVal !== 'không ghi nhận dị ứng' && allergyVal !== 'không ghi nhận dị ứng thuốc';
        if (hasAllergy && name) {
            const medLower = name.toLowerCase();
            const keywords = allergyVal.split(/[,;\\s]+/).filter(k => k.length > 2);
            const isSuspected = keywords.some(k => medLower.includes(k)) || medLower.includes(allergyVal);
            if (isSuspected) {
                if (!confirm(`⚠️ CẢNH BÁO NGUY HIỂM VỀ DỊ ỨNG THUỐC:\nBệnh nhân có tiền sử: "${p.di_ung}"\nThuốc bạn đang kê: "${name}"\n\nBạn có CHẮC CHẮN muốn tiếp tục kê loại thuốc này vào đơn?`)) {
                    return;
                }
            }
        }

        // Nếu đã có thuốc trong đơn thì tăng số lượng
        const existing = prescriptionItems.find(x => x.thuoc_id === thuocId);
        if (existing) {
            if (existing.so_luong + qty > ton) {
                alert(`Tổng số lượng thuốc "${name}" kê (${existing.so_luong + qty}) vượt quá tồn kho (${ton} ${dvt})!`);
                return;
            }
            existing.so_luong += qty;
            existing.cach_dung = usage;
        } else {
            prescriptionItems.push({
                thuoc_id: thuocId,
                ten_thuoc: name,
                so_luong: qty,
                don_vi_tinh: dvt,
                so_luong_ton: ton,
                don_gia: price,
                lieu_dung: usage,
                cach_dung: usage
            });
        }

        renderPrescriptionTable();
        alert(`Đã thêm thuốc "${name}" (${qty} ${dvt}) vào toa!`);
    }

    function removePrescriptionItem(index) {
        prescriptionItems.splice(index, 1);
        renderPrescriptionTable();
    }

    function renderPrescriptionTable() {
        const tbody = document.getElementById('prescription-body');
        tbody.innerHTML = '';
        let totalAmount = 0;

        if (prescriptionItems.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">Chưa có thuốc nào trong đơn. Chọn thuốc từ kho và bấm "Thêm Thuốc Này Vào Toa" ở trên.</td></tr>`;
            document.getElementById('total-med-types').innerText = '0';
            document.getElementById('total-med-amount').innerText = '0 đ';
            return;
        }

        prescriptionItems.forEach((item, idx) => {
            const itemTotal = item.don_gia * item.so_luong;
            totalAmount += itemTotal;
            const isLowStock = item.so_luong_ton <= 20;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="py-2.5 px-3">
                    <strong class="text-slate-800">${item.ten_thuoc}</strong>
                    ${isLowStock ? '<span class="inline-block ml-1.5 px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800 font-bold">Tồn ít</span>' : ''}
                </td>
                <td class="py-2.5 px-3 font-mono ${isLowStock ? 'text-amber-600 font-bold' : 'text-slate-500'}">${item.so_luong_ton} ${item.don_vi_tinh}</td>
                <td class="py-2.5 px-3 font-mono font-bold text-teal-800">${item.so_luong} ${item.don_vi_tinh}</td>
                <td class="py-2.5 px-3 text-slate-600">${item.cach_dung}</td>
                <td class="py-2.5 px-3 text-right font-mono text-slate-600">${item.don_gia.toLocaleString('vi-VN')} đ</td>
                <td class="py-2.5 px-3 text-right font-mono font-bold text-slate-800">${itemTotal.toLocaleString('vi-VN')} đ</td>
                <td class="py-2.5 px-3 text-center text-rose-500 hover:text-rose-700 cursor-pointer" onclick="removePrescriptionItem(${idx})">
                    <i class="fa-solid fa-trash"></i>
                </td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById('total-med-types').innerText = prescriptionItems.length;
        document.getElementById('total-med-amount').innerText = totalAmount.toLocaleString('vi-VN') + ' đ';
    }

    // Hoàn tất phiên khám
    function completeExamination() {
        const diagnosis = document.getElementById('emr-icd')?.value || 'K29.5 - Viêm dạ dày mạn tính';
        const symptoms = document.getElementById('emr-symptoms')?.value || 'Đau thượng vị';
        const treatment = document.getElementById('emr-treatment')?.value || 'Chỉ định CLS và kê đơn điều trị nội khoa';
        const advice = document.getElementById('emr-advice')?.value || 'Uống thuốc đúng giờ, tái khám đúng hẹn';
        const reexam = document.getElementById('emr-reexam')?.value || null;

        // Lấy danh sách ID các kỹ thuật CLS đã chọn
        const checkedCls = Array.from(document.querySelectorAll('input[name="cls_service_id"]:checked')).map(el => parseInt(el.value));

        if (prescriptionItems.length === 0 && checkedCls.length === 0) {
            if (!confirm('Bạn chưa chọn kỹ thuật cận lâm sàng và chưa kê đơn thuốc nào. Bạn có chắc chắn muốn lưu phiếu khám chỉ có kết luận lâm sàng không?')) {
                return;
            }
        }

        const payload = {
            patient_id: currentSelectedPatientId,
            reason: 'Khám chuyên khoa',
            symptoms: symptoms,
            diagnosis: diagnosis,
            icd: diagnosis,
            treatment: treatment,
            advice: advice,
            reexam_date: reexam,
            lab_services: checkedCls,
            medicines: prescriptionItems.map(x => ({
                thuoc_id: x.thuoc_id,
                so_luong: x.so_luong,
                lieu_dung: x.lieu_dung,
                cach_dung: x.cach_dung
            })),
            images: emrSelectedImages
        };

        fetch('/api/emr/save', {
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

    // Bác sĩ chốt kết luận và hoàn tất ca khám sau khi có kết quả CLS
    function finishExaminationRecord() {
        if (!currentActiveEncounterId) {
            alert('Không tìm thấy phiếu khám đang chờ kết quả CLS cho bệnh nhân này!');
            return;
        }

        const diagnosis = document.getElementById('emr-icd')?.value || 'K29.5 - Viêm dạ dày mạn tính';
        const treatment = document.getElementById('emr-treatment')?.value || 'Điều trị nội khoa sau khi có kết quả cận lâm sàng';
        const advice = document.getElementById('emr-advice')?.value || 'Uống thuốc đúng giờ, tái khám đúng hẹn';
        const reexam = document.getElementById('emr-reexam')?.value || null;

        if (!confirm('Xác nhận hoàn tất phiên khám EMR sau khi đã xem xét đầy đủ kết quả cận lâm sàng?\\nHệ thống sẽ chốt bệnh án, chuyển đơn thuốc sang Dược sĩ và cập nhật trạng thái đã khám.')) {
            return;
        }

        const payload = {
            record_id: currentActiveEncounterId,
            diagnosis: diagnosis,
            icd: diagnosis,
            treatment: treatment,
            advice: advice,
            reexam_date: reexam,
            medicines: prescriptionItems.map(x => ({
                thuoc_id: x.thuoc_id,
                so_luong: x.so_luong,
                lieu_dung: x.lieu_dung,
                cach_dung: x.cach_dung
            })),
            images: emrSelectedImages
        };

        fetch('/api/emr/finish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(`✅ KẾT THÚC PHIÊN KHÁM THÀNH CÔNG!\\n${data.message || 'Đã chốt kết luận và hoàn tất ca khám.'}`);
                window.location.reload();
            } else {
                alert('❌ LỖI:\\n' + data.message);
            }
        })
        .catch(err => {
            alert('Lỗi kết nối máy chủ: ' + err);
        });
    }

    // Kết thúc phiên khám lâm sàng bình thường một chạm (Xử lý toàn bộ biến số nghiệp vụ tại BackEnd)
    function completeNormalExamination() {
        if (!confirm('Xác nhận: Bệnh nhân có kết quả khám lâm sàng bình thường (sức khỏe tốt)?\\nHệ thống sẽ kết thúc phiên khám và tự động xuất hóa đơn viện phí tiền khám ngay lập tức.')) {
            return;
        }

        fetch('/api/emr/save-normal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: currentSelectedPatientId })
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
    }
</script>
"""

with open('templates/admin/emr.html', 'r', encoding='utf-8') as f:
    orig = f.read()

start_marker = '<script type="application/json" id="emr-patients-data">'
end_marker = '<!-- Modal phóng to xem ảnh Cận Lâm Sàng cho Bác sĩ -->'

start_pos = orig.find(start_marker)
end_pos = orig.find(end_marker)

if start_pos == -1 or end_pos == -1:
    print("Markers not found! start:", start_pos, "end:", end_pos)
    sys.exit(1)

new_content = orig[:start_pos] + emr_script_content + "\n" + orig[end_pos:]

with open('templates/admin/emr.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully patched templates/admin/emr.html")
