with open('templates/admin/lab.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update the table header to include Hình ảnh
old_th = """                        <th class="py-3.5 px-4 text-center">Trạng Thái</th>
                        <th class="py-3.5 px-4 text-center">Thao Tác</th>"""

new_th = """                        <th class="py-3.5 px-4 text-center">Ảnh Chụp CLS</th>
                        <th class="py-3.5 px-4 text-center">Trạng Thái</th>
                        <th class="py-3.5 px-4 text-center">Thao Tác</th>"""

c = c.replace(old_th, new_th).replace(old_th.replace('\n', '\r\n'), new_th.replace('\n', '\r\n'))

# 2. Add image upload and preview to modal
old_modal_fields = """            <div>
                <label class="block font-semibold text-slate-700 mb-1">Kết luận chẩn đoán hình ảnh / xét nghiệm</label>
                <input type="text" id="modal-conclusion" value="" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:bg-white focus:outline-none focus:border-medical-500">
            </div>
        </div>"""

new_modal_fields = """            <div>
                <label class="block font-semibold text-slate-700 mb-1">Kết luận chẩn đoán hình ảnh / xét nghiệm</label>
                <input type="text" id="modal-conclusion" value="" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:bg-white focus:outline-none focus:border-medical-500">
            </div>

            <!-- Upload ảnh chụp siêu âm, X-quang, nội soi -->
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
            </div>
        </div>"""

c = c.replace(old_modal_fields, new_modal_fields).replace(old_modal_fields.replace('\n', '\r\n'), new_modal_fields.replace('\n', '\r\n'))

# 3. Add Image Lightbox Modal before </main> or end of content
lightbox_html = """
<!-- Modal Phóng To Hình Ảnh Cận Lâm Sàng (Lightbox) -->
<div id="modal-image-lightbox" class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 hidden flex flex-col items-center justify-center p-4">
    <div class="max-w-4xl w-full flex items-center justify-between text-white pb-3">
        <h4 id="lightbox-title" class="font-bold text-sm">Hình ảnh Cận lâm sàng</h4>
        <button type="button" onclick="closeLightbox()" class="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-lg transition-all">
            <i class="fa-solid fa-xmark"></i>
        </button>
    </div>
    <div class="max-w-4xl max-h-[80vh] w-full bg-black/50 rounded-2xl overflow-hidden flex items-center justify-center border border-white/10">
        <img id="lightbox-img" src="" alt="Ảnh Cận lâm sàng phóng to" class="max-h-[80vh] max-w-full object-contain">
    </div>
</div>
"""

c = c.replace("{% endblock %}", lightbox_html + "\n{% endblock %}")

# 4. Update JavaScript to map file_ket_qua and handle image preview/upload
old_map = """        status: o.trang_thai === 'Đã hoàn thành' ? 'completed' : (o.trang_thai === 'Đang thực hiện' ? 'processing' : 'waiting'),
        trang_thai_raw: o.trang_thai || '',
        ket_qua: o.ket_qua || '',
        nguoi_nhap: o.nguoi_nhap || '',
        bac_si_duyet: o.bac_si_duyet || ''"""

new_map = """        status: o.trang_thai === 'Đã hoàn thành' || o.trang_thai === 'Đã duyệt' ? 'completed' : (o.trang_thai === 'Đang thực hiện' || o.trang_thai === 'Chờ duyệt' ? 'processing' : 'waiting'),
        trang_thai_raw: o.trang_thai || '',
        ket_qua: o.ket_qua || '',
        file_ket_qua: o.file_ket_qua || '',
        nguoi_nhap: o.nguoi_nhap || '',
        bac_si_duyet: o.bac_si_duyet || ''"""

c = c.replace(old_map, new_map).replace(old_map.replace('\n', '\r\n'), new_map.replace('\n', '\r\n'))

# 5. In renderLabOrders: render the image column
old_render_row = """            tr.innerHTML = `
                <td class="py-3 px-4 font-mono font-bold text-slate-900">${order.ma_cd}</td>
                <td class="py-3 px-4">
                    <span class="font-bold text-slate-800 block">${order.benh_nhan}</span>
                    <span class="text-slate-400 text-[10px] font-mono">${order.ma_bn}</span>
                </td>
                <td class="py-3 px-4 font-semibold text-slate-800">${order.dich_vu}</td>
                <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-semibold">${order.loai}</span></td>
                <td class="py-3 px-4 text-slate-600">${order.bac_si}</td>
                <td class="py-3 px-4 text-slate-500 font-mono">${order.gio}</td>
                <td class="py-3 px-4 text-center">${statusBadge}</td>
                <td class="py-3 px-4 text-center">${actionBtn}</td>
            `;"""

new_render_row = """            let imageCell = '<span class="text-slate-300 text-[11px]">-</span>';
            if (order.file_ket_qua) {
                imageCell = `
                    <button type="button" onclick="openLightbox('${order.file_ket_qua}', '${order.dich_vu} - ${order.benh_nhan}')" class="px-2 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[11px] border border-teal-200 transition-all flex items-center gap-1 mx-auto" title="Xem ảnh chụp">
                        <i class="fa-solid fa-image text-teal-600"></i> Xem ảnh
                    </button>
                `;
            }

            tr.innerHTML = `
                <td class="py-3 px-4 font-mono font-bold text-slate-900">${order.ma_cd}</td>
                <td class="py-3 px-4">
                    <span class="font-bold text-slate-800 block">${order.benh_nhan}</span>
                    <span class="text-slate-400 text-[10px] font-mono">${order.ma_bn}</span>
                </td>
                <td class="py-3 px-4 font-semibold text-slate-800">${order.dich_vu}</td>
                <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-semibold">${order.loai}</span></td>
                <td class="py-3 px-4 text-slate-600">${order.bac_si}</td>
                <td class="py-3 px-4 text-slate-500 font-mono">${order.gio}</td>
                <td class="py-3 px-4 text-center">${imageCell}</td>
                <td class="py-3 px-4 text-center">${statusBadge}</td>
                <td class="py-3 px-4 text-center">${actionBtn}</td>
            `;"""

c = c.replace(old_render_row, new_render_row).replace(old_render_row.replace('\n', '\r\n'), new_render_row.replace('\n', '\r\n'))

# 6. Update openResultModal to show preview if has file_ket_qua
old_open_modal_end = """        document.getElementById('modal-patient-name').innerText = o.benh_nhan;
        document.getElementById('modal-patient-code').innerText = o.ma_bn;
        document.getElementById('modal-service-name').innerText = o.dich_vu;
        document.getElementById('modal-result-detail').value = o.ket_qua || '';
        document.getElementById('modal-conclusion').value = o.ket_qua || '';"""

new_open_modal_end = """        document.getElementById('modal-patient-name').innerText = o.benh_nhan;
        document.getElementById('modal-patient-code').innerText = o.ma_bn;
        document.getElementById('modal-service-name').innerText = o.dich_vu;
        document.getElementById('modal-result-detail').value = o.ket_qua || '';
        document.getElementById('modal-conclusion').value = o.ket_qua || '';

        // Reset file input and preview
        const fileInp = document.getElementById('modal-lab-image');
        if (fileInp) fileInp.value = '';
        const previewBox = document.getElementById('modal-image-preview-box');
        const previewImg = document.getElementById('modal-image-preview');
        if (o.file_ket_qua) {
            previewImg.src = o.file_ket_qua;
            previewBox.classList.remove('hidden');
        } else {
            previewImg.src = '';
            previewBox.classList.add('hidden');
        }"""

c = c.replace(old_open_modal_end, new_open_modal_end).replace(old_open_modal_end.replace('\n', '\r\n'), new_open_modal_end.replace('\n', '\r\n'))

# 7. Update saveLabResult to send FormData with image
old_save_func = """    async function saveLabResult() {
        const orderId = document.getElementById('modal-order-id').value;
        const ketQua = document.getElementById('modal-conclusion').value.trim();
        const moTa = document.getElementById('modal-result-detail').value.trim();
        if (!orderId || !ketQua) {
            alert('Vui lòng nhập kết luận xét nghiệm!');
            return;
        }

        try {
            const res = await fetch('/api/lab/result/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chi_tiet_id: parseInt(orderId), ket_qua: ketQua + (moTa ? '\\n' + moTa : '') })
            });
            const data = await res.json();
            if (data.success) {
                // Cập nhật local state
                const o = labOrders.find(x => x.id === parseInt(orderId));
                if (o) {
                    o.ket_qua = ketQua;
                    o.status = 'processing';
                    o.trang_thai_raw = 'Chờ duyệt';
                }
                closeResultModal();
                filterLabOrders();
                alert(data.message || 'Đã lưu kết quả xét nghiệm thành công!');
            } else {
                alert('Lỗi: ' + data.message);
            }
        } catch (err) {
            alert('Lỗi kết nối máy chủ: ' + err.message);
        }
    }"""

new_save_func = """    function previewLabImage(input) {
        const box = document.getElementById('modal-image-preview-box');
        const img = document.getElementById('modal-image-preview');
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                img.src = e.target.result;
                box.classList.remove('hidden');
            }
            reader.readAsDataURL(input.files[0]);
        }
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

        const formData = new FormData();
        formData.append('chi_tiet_id', orderId);
        formData.append('ket_qua', ketQua + (moTa ? '\\n' + moTa : ''));

        const fileInput = document.getElementById('modal-lab-image');
        if (fileInput && fileInput.files[0]) {
            formData.append('image_file', fileInput.files[0]);
        }

        try {
            const res = await fetch('/api/lab/result/save', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                // Cập nhật local state
                const o = labOrders.find(x => x.id === parseInt(orderId));
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
    }"""

c = c.replace(old_save_func, new_save_func).replace(old_save_func.replace('\n', '\r\n'), new_save_func.replace('\n', '\r\n'))

with open('templates/admin/lab.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated templates/admin/lab.html successfully!')
