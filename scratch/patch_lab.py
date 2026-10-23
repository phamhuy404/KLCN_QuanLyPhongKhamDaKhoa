import sys

lab_file = 'templates/admin/lab.html'

with open(lab_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update table header
old_thead = """                <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                    <tr>
                        <th class="py-3.5 px-4">Mã Chỉ Định</th>
                        <th class="py-3.5 px-4">Bệnh Nhân</th>
                        <th class="py-3.5 px-4">Kỹ Thuật / Dịch Vụ Chỉ Định</th>
                        <th class="py-3.5 px-4">Phân Loại</th>
                        <th class="py-3.5 px-4">Bác Sĩ Chỉ Định</th>
                        <th class="py-3.5 px-4">Thời Gian</th>
                        <th class="py-3.5 px-4 text-center">Ảnh Chụp CLS</th>
                        <th class="py-3.5 px-4 text-center">Trạng Thái</th>
                        <th class="py-3.5 px-4 text-center">Thao Tác</th>
                    </tr>
                </thead>"""

new_thead = """                <thead class="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                    <tr>
                        <th class="py-3.5 px-4">Mã Chỉ Định</th>
                        <th class="py-3.5 px-4">Bệnh Nhân</th>
                        <th class="py-3.5 px-4">Kỹ Thuật / Dịch Vụ Chỉ Định</th>
                        <th class="py-3.5 px-4">Phân Loại</th>
                        <th class="py-3.5 px-4">Bác Sĩ Chỉ Định</th>
                        <th class="py-3.5 px-4">Thời Gian</th>
                        <th class="py-3.5 px-4 text-center">Ảnh Chụp CLS</th>
                        <th class="py-3.5 px-4 text-center">Trạng Thái Viện Phí</th>
                        <th class="py-3.5 px-4 text-center">Trạng Thái Thực Hiện</th>
                        <th class="py-3.5 px-4 text-center">Thao Tác</th>
                    </tr>
                </thead>"""

if old_thead in content:
    content = content.replace(old_thead, new_thead)
else:
    print("Warning: old_thead not found exactly")

# 2. Update upload section in modal
old_upload = """            <!-- Upload ảnh chụp siêu âm, X-quang, nội soi -->
            <div>
                <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                    <span>Tải lên ảnh chụp Cận lâm sàng (Siêu âm, X-Quang, Nội soi...)</span>
                    <span class="text-[10px] text-slate-400">JPG, PNG, WebP</span>
                </label>
                <input type="file" id="modal-lab-image" accept="image/*" onchange="previewLabImage(this)"
                       class="block w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-medical-50 file:text-medical-700 hover:file:bg-medical-100 cursor-pointer">
                
                <div id="modal-image-preview-box" class="mt-2.5 hidden">
                    <span class="text-[11px] font-bold text-slate-500 block mb-1">Hình ảnh kết quả đính kèm:</span>
                    <div class="relative rounded-xl border border-slate-200 bg-slate-900 overflow-hidden flex items-center justify-center max-h-48">
                        <img id="modal-image-preview" src="" alt="Ảnh chụp" class="max-h-48 object-contain">
                    </div>
                </div>
            </div>"""

new_upload = """            <!-- Upload ảnh chụp siêu âm, X-quang, nội soi (Tối đa 10 ảnh) -->
            <div>
                <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                    <span class="flex items-center gap-1.5">
                        <i class="fa-solid fa-images text-medical-600"></i>
                        <span>Ảnh chụp Cận lâm sàng (Tối đa 10 ảnh)</span>
                    </span>
                    <span class="text-[11px] text-slate-400 font-mono" id="lab-image-count-badge">0 / 10 ảnh</span>
                </label>
                
                <!-- Dropzone kéo thả hoặc click chọn file -->
                <div id="lab-dropzone" onclick="document.getElementById('modal-lab-image').click()"
                     ondragover="handleLabDragOver(event)" ondragleave="handleLabDragLeave(event)" ondrop="handleLabDrop(event)"
                     class="p-3.5 border-2 border-dashed border-slate-200 hover:border-medical-500 rounded-2xl bg-slate-50 hover:bg-medical-50/30 text-center cursor-pointer transition-all">
                    <input type="file" id="modal-lab-image" multiple accept="image/*" class="hidden" onchange="handleLabFilesSelect(this.files)">
                    <div class="flex flex-col items-center justify-center space-y-1">
                        <div class="w-8 h-8 rounded-lg bg-white text-medical-600 flex items-center justify-center shadow-sm">
                            <i class="fa-solid fa-cloud-arrow-up"></i>
                        </div>
                        <p class="text-xs font-bold text-slate-700">Kéo thả ảnh vào đây hoặc bấm để chọn ảnh</p>
                        <p class="text-[10px] text-slate-400">Hỗ trợ JPG, PNG, WebP (Tối đa 10 ảnh cùng lúc)</p>
                    </div>
                </div>

                <!-- Khung dạng cột ảnh 2x2 xem trước nhỏ có thể kéo xuống -->
                <div id="lab-image-preview-box" class="mt-2.5 hidden space-y-1.5">
                    <div class="flex items-center justify-between text-[11px] text-slate-500">
                        <span class="font-bold">Ảnh kết quả đính kèm (Bấm để phóng to):</span>
                        <button type="button" onclick="clearAllLabImages()" class="text-rose-500 hover:text-rose-700 font-semibold cursor-pointer">
                            <i class="fa-solid fa-trash-can mr-1"></i> Xóa tất cả
                        </button>
                    </div>
                    <div id="lab-thumbnails-grid" class="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-xl">
                        <!-- Render dynamically -->
                    </div>
                </div>
            </div>"""

if old_upload in content:
    content = content.replace(old_upload, new_upload)
else:
    print("Warning: old_upload not found exactly")

# 3. Update the script part
script_marker_start = '<script type="application/json" id="lab-orders-data">'
script_marker_end = '<!-- Modal Phóng To Hình Ảnh Cận Lâm Sàng (Lightbox) -->'

pos1 = content.find(script_marker_start)
pos2 = content.find(script_marker_end)

new_script = """<script type="application/json" id="lab-orders-data">
    {{ lab_orders | tojson | safe }}
</script>
<script>
    let rawLabOrders = JSON.parse(document.getElementById('lab-orders-data').textContent || '[]');
    let labOrders = rawLabOrders.map(o => ({
        id: o.id,
        ma_cd: o.ma_chi_dinh,
        patient_id: o.patient_id,
        benh_nhan: o.benh_nhan,
        ma_bn: o.ma_bn,
        dich_vu: o.dich_vu || 'Chỉ định cận lâm sàng',
        loai: o.loai || 'Xét nghiệm',
        bac_si: o.bac_si,
        gio: (o.thoi_gian_chi_dinh || '').toString().slice(11, 16) || '08:30',
        status: o.trang_thai === 'Đã hoàn thành' || o.trang_thai === 'Đã duyệt' ? 'completed' : (o.trang_thai === 'Đang thực hiện' || o.trang_thai === 'Chờ duyệt' ? 'processing' : 'waiting'),
        trang_thai_raw: o.trang_thai || '',
        trang_thai_thanh_toan: o.trang_thai_thanh_toan || 'Chưa thanh toán',
        ket_qua: o.ket_qua || '',
        file_ket_qua: o.file_ket_qua || '',
        nguoi_nhap: o.nguoi_nhap || '',
        bac_si_duyet: o.bac_si_duyet || ''
    }));

    let activeLabOrderId = null;
    let modalSelectedLabImages = [];
    const userRole = "{{ session.get('user', {}).get('vai_tro', '') }}";

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

    // ==========================================
    // Quản lý kéo thả & xem trước ảnh KTV (Tối đa 10 ảnh, lưới 2x2 cuộn được)
    // ==========================================
    function handleLabDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        const dz = document.getElementById('lab-dropzone');
        if (dz) dz.classList.add('border-medical-500', 'bg-medical-50/50');
    }

    function handleLabDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        const dz = document.getElementById('lab-dropzone');
        if (dz) dz.classList.remove('border-medical-500', 'bg-medical-50/50');
    }

    function handleLabDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        const dz = document.getElementById('lab-dropzone');
        if (dz) dz.classList.remove('border-medical-500', 'bg-medical-50/50');
        if (e.dataTransfer && e.dataTransfer.files) {
            handleLabFilesSelect(e.dataTransfer.files);
        }
    }

    function handleLabFilesSelect(files) {
        if (!files || files.length === 0) return;
        const remaining = 10 - modalSelectedLabImages.length;
        if (remaining <= 0) {
            alert('Bạn đã chọn tối đa 10 ảnh cận lâm sàng!');
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
                modalSelectedLabImages.push(e.target.result);
                processedCount++;
                if (processedCount === filesToProcess.length) {
                    renderLabThumbnails();
                }
            };
            reader.readAsDataURL(file);
        });
    }

    function removeLabImage(index) {
        modalSelectedLabImages.splice(index, 1);
        renderLabThumbnails();
    }

    function clearAllLabImages() {
        modalSelectedLabImages = [];
        renderLabThumbnails();
        const input = document.getElementById('modal-lab-image');
        if (input) input.value = '';
    }

    function renderLabThumbnails() {
        const box = document.getElementById('lab-image-preview-box');
        const grid = document.getElementById('lab-thumbnails-grid');
        const badge = document.getElementById('lab-image-count-badge');
        if (!box || !grid) return;

        if (badge) badge.innerText = `${modalSelectedLabImages.length} / 10 ảnh`;

        if (modalSelectedLabImages.length === 0) {
            box.classList.add('hidden');
            grid.innerHTML = '';
            return;
        }

        box.classList.remove('hidden');
        grid.innerHTML = '';

        modalSelectedLabImages.forEach((imgSrc, idx) => {
            const card = document.createElement('div');
            card.className = "relative group rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-sm aspect-video flex items-center justify-center";
            card.innerHTML = `
                <img src="${imgSrc}" alt="Ảnh CLS #${idx+1}" 
                     onclick="openLightbox('${imgSrc}', 'Ảnh chụp Cận lâm sàng #${idx+1}')"
                     class="w-full h-full object-cover cursor-pointer hover:scale-105 transition-all duration-200">
                <span class="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-black/60 text-white text-[10px] font-mono">#${idx+1}</span>
                <button type="button" onclick="removeLabImage(${idx})" title="Xóa ảnh này"
                        class="absolute top-1 right-1 w-5 h-5 rounded-full bg-rose-600 hover:bg-rose-700 text-white flex items-center justify-center text-[10px] shadow transition-all cursor-pointer">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            `;
            grid.appendChild(card);
        });
    }

    function renderLabOrders(dataList) {
        const tbody = document.getElementById('lab-table-body');
        tbody.innerHTML = '';

        if (!dataList || dataList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400">Không tìm thấy phiếu chỉ định phù hợp</td></tr>`;
            return;
        }

        dataList.forEach(order => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-slate-50 transition-colors';

            let statusBadge = '';
            if (order.status === 'waiting') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 font-bold text-[10px]">Chờ thực hiện</span>';
            } else if (order.status === 'processing') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 font-bold text-[10px]">Chờ duyệt</span>';
            } else if (order.status === 'completed') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px]">Đã duyệt</span>';
            }

            // Trạng thái thanh toán viện phí
            let feeBadge = order.trang_thai_thanh_toan === 'Đã thanh toán' 
                ? '<span class="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px] border border-emerald-200"><i class="fa-solid fa-circle-check mr-1"></i> Đã đóng phí</span>'
                : '<span class="px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 font-bold text-[10px] border border-rose-200"><i class="fa-solid fa-circle-exclamation mr-1"></i> Chưa đóng phí</span>';

            // Ảnh chụp Cận lâm sàng
            const images = parseImageFiles(order.file_ket_qua);
            let imgCell = '<span class="text-slate-400 text-[11px]">Không có</span>';
            if (images.length > 0) {
                imgCell = `
                    <button type="button" onclick="openLightbox('${images[0]}', '${order.dich_vu}')" class="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[11px] inline-flex items-center gap-1.5 transition-all shadow-sm cursor-pointer">
                        <i class="fa-solid fa-images"></i>
                        <span>${images.length > 1 ? images.length + ' ảnh' : 'Xem ảnh'}</span>
                    </button>
                `;
            }

            // Nút thao tác
            let actionBtn = '';
            if (order.bac_si_duyet && order.status === 'completed') {
                actionBtn = `<button type="button" onclick="openResultModal(${order.id})" class="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 font-semibold text-xs"><i class="fa-solid fa-eye mr-1"></i> Xem</button>`;
            } else if (order.ket_qua && (userRole === 'ADMIN' || userRole === 'BACSI')) {
                actionBtn = `<button type="button" onclick="openResultModal(${order.id})" class="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold text-xs"><i class="fa-solid fa-circle-check mr-1"></i> Duyệt KQ</button>`;
            } else {
                actionBtn = `<button type="button" onclick="openResultModal(${order.id})" class="px-3 py-1.5 rounded-lg bg-medical-50 hover:bg-medical-100 text-medical-700 font-semibold text-xs"><i class="fa-solid fa-pen-to-square mr-1"></i> Kết Quả</button>`;
            }

            tr.innerHTML = `
                <td class="py-3.5 px-4 font-mono font-bold text-medical-700">${order.ma_cd}</td>
                <td class="py-3.5 px-4">
                    <a href="/admin/patients/${order.patient_id}" class="font-bold text-slate-900 hover:text-medical-700 transition-colors block">
                        ${order.benh_nhan}
                    </a>
                    <span class="text-[10px] text-slate-400 font-mono">${order.ma_bn}</span>
                </td>
                <td class="py-3.5 px-4 font-semibold text-slate-800">
                    ${order.dich_vu}
                    ${order.ket_qua ? `<span class="block text-[11px] text-teal-700 mt-0.5 font-normal">${order.ket_qua.split('\\n')[0]}</span>` : ''}
                </td>
                <td class="py-3.5 px-4">
                    <span class="px-2 py-0.5 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-medium">${order.loai}</span>
                </td>
                <td class="py-3.5 px-4 text-slate-600">${order.bac_si}</td>
                <td class="py-3.5 px-4 text-slate-500 font-mono">${order.gio}</td>
                <td class="py-3.5 px-4 text-center">${imgCell}</td>
                <td class="py-3.5 px-4 text-center">${feeBadge}</td>
                <td class="py-3.5 px-4 text-center">${statusBadge}</td>
                <td class="py-3.5 px-4 text-center">${actionBtn}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function filterLabOrders() {
        const query = document.getElementById('search-lab').value.toLowerCase().trim();
        const typeFilter = document.getElementById('filter-lab-type').value;
        const statusFilter = document.getElementById('filter-lab-status').value;

        const filtered = labOrders.filter(o => {
            const matchQ = !query || (window.fuzzyMatchRecord
                ? window.fuzzyMatchRecord(query, [o.ma_cd, o.benh_nhan, o.ma_bn, o.dich_vu, o.loai, o.bac_si])
                : (o.ma_cd.toLowerCase().includes(query) || o.benh_nhan.toLowerCase().includes(query) || o.dich_vu.toLowerCase().includes(query)));
            const matchT = !typeFilter || o.loai === typeFilter;
            const matchS = !statusFilter || o.status === statusFilter;
            return matchQ && matchT && matchS;
        });

        renderLabOrders(filtered);
    }

    function openResultModal(id) {
        const o = labOrders.find(x => x.id === id);
        if (!o) return;
        activeLabOrderId = id;

        document.getElementById('modal-order-id').value = id;
        document.getElementById('modal-order-status').value = o.trang_thai_raw;
        document.getElementById('modal-patient-name').innerText = o.benh_nhan;
        document.getElementById('modal-patient-code').innerText = o.ma_bn;
        document.getElementById('modal-service-name').innerText = o.dich_vu;
        document.getElementById('modal-result-detail').value = o.ket_qua || '';
        document.getElementById('modal-conclusion').value = o.ket_qua ? o.ket_qua.split('\\n')[0] : '';

        // Reset & load images
        modalSelectedLabImages = parseImageFiles(o.file_ket_qua);
        renderLabThumbnails();

        const isApproved = !!o.bac_si_duyet;
        const warningEl = document.getElementById('modal-approved-warning');
        const saveBtn = document.getElementById('btn-save-result');
        const approveBtn = document.getElementById('btn-approve-result');

        if (isApproved) {
            warningEl.classList.remove('hidden');
            saveBtn.classList.add('hidden');
            approveBtn.classList.add('hidden');
            document.getElementById('modal-result-detail').readOnly = true;
            document.getElementById('modal-conclusion').readOnly = true;
        } else {
            warningEl.classList.add('hidden');
            document.getElementById('modal-result-detail').readOnly = false;
            document.getElementById('modal-conclusion').readOnly = false;

            if (o.ket_qua && (userRole === 'ADMIN' || userRole === 'BACSI')) {
                saveBtn.classList.remove('hidden');
                approveBtn.classList.remove('hidden');
            } else {
                saveBtn.classList.remove('hidden');
                approveBtn.classList.add('hidden');
            }
        }

        document.getElementById('result-modal').classList.remove('hidden');
    }

    function closeResultModal() {
        document.getElementById('result-modal').classList.add('hidden');
    }

    function openLightbox(src, title) {
        document.getElementById('lightbox-img').src = src;
        document.getElementById('lightbox-title').innerText = title || 'Hình ảnh Cận lâm sàng';
        document.getElementById('modal-image-lightbox').classList.remove('hidden');
    }

    function closeLightbox() {
        document.getElementById('modal-image-lightbox').classList.add('hidden');
    }

    async function saveLabResult() {
        const orderId = document.getElementById('modal-order-id').value;
        const ketQua = document.getElementById('modal-conclusion').value.trim();
        const moTa = document.getElementById('modal-result-detail').value.trim();
        if (!orderId || !ketQua) {
            alert('Vui lòng nhập kết luận xét nghiệm!');
            return;
        }

        const o = labOrders.find(x => x.id === parseInt(orderId));
        if (o && o.trang_thai_thanh_toan !== 'Đã thanh toán') {
            if (!confirm('⚠️ CẢNH BÁO VIỆN PHÍ:\\nBệnh nhân này CHƯA THANH TOÁN viện phí cận lâm sàng tại Quầy Tiếp Tân!\\n\\nBạn có chắc chắn muốn tiến hành lưu và trả kết quả trước khi thu phí không?')) {
                return;
            }
        }

        try {
            const res = await fetch('/api/lab/result/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chi_tiet_id: parseInt(orderId),
                    ket_qua: ketQua + (moTa && moTa !== ketQua ? '\\n' + moTa : ''),
                    images: modalSelectedLabImages
                })
            });
            const data = await res.json();
            if (data.success) {
                if (o) {
                    o.ket_qua = ketQua;
                    if (data.file_ket_qua) o.file_ket_qua = data.file_ket_qua;
                    o.status = 'processing';
                    o.trang_thai_raw = 'Chờ duyệt';
                }
                closeResultModal();
                filterLabOrders();
                alert(data.message || 'Đã lưu kết quả và tải lên hình ảnh thành công!');
                window.location.reload();
            } else {
                alert('Lỗi: ' + data.message);
            }
        } catch (err) {
            alert('Lỗi kết nối máy chủ: ' + err.message);
        }
    }

    async function approveLabResult() {
        const orderId = document.getElementById('modal-order-id').value;
        if (!orderId) return;

        if (!confirm('Xác nhận duyệt kết quả xét nghiệm này? Sau khi duyệt sẽ không thể chỉnh sửa.')) return;

        try {
            const res = await fetch('/api/lab/result/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chi_tiet_id: parseInt(orderId), approval_note: 'Đã kiểm tra và xác nhận' })
            });
            const data = await res.json();
            if (data.success) {
                const o = labOrders.find(x => x.id === parseInt(orderId));
                if (o) {
                    o.status = 'completed';
                    o.trang_thai_raw = 'Đã duyệt';
                    o.bac_si_duyet = 'Bác sĩ';
                }
                closeResultModal();
                filterLabOrders();
                alert(data.message || 'Đã duyệt kết quả xét nghiệm thành công!');
            } else {
                alert('Lỗi: ' + data.message);
            }
        } catch (err) {
            alert('Lỗi kết nối máy chủ: ' + err.message);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        renderLabOrders(labOrders);
    });
</script>
"""

if pos1 != -1 and pos2 != -1:
    content = content[:pos1] + new_script + "\n" + content[pos2:]
else:
    print("Warning: script markers not found! pos1:", pos1, "pos2:", pos2)

with open(lab_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully patched templates/admin/lab.html")
