// Bộ công cụ tìm kiếm gần đúng thông minh toàn cục (Universal Smart Search Engine)

window.removeVietnameseTones = function(str) {

    if (!str) return '';

    str = String(str);

    str = str.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, "a");

    str = str.replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, "a");

    str = str.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, "e");

    str = str.replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, "e");

    str = str.replace(/ì|í|ị|ỉ|ĩ/g, "i");

    str = str.replace(/Ì|Í|Ị|Ỉ|Ĩ/g, "i");

    str = str.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, "o");

    str = str.replace(/Ò|Ó|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, "o");

    str = str.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, "u");

    str = str.replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, "u");

    str = str.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, "y");

    str = str.replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, "y");

    str = str.replace(/đ/g, "d");

    str = str.replace(/Đ/g, "d");

    return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

};



window.levenshteinDistance = function(s1, s2) {

    if (s1 === s2) return 0;

    if (!s1) return s2.length;

    if (!s2) return s1.length;

    const m = s1.length;

    const n = s2.length;

    let prev = new Array(n + 1);

    let curr = new Array(n + 1);

    for (let j = 0; j <= n; j++) prev[j] = j;

    for (let i = 1; i <= m; i++) {

        curr[0] = i;

        const c1 = s1.charCodeAt(i - 1);

        for (let j = 1; j <= n; j++) {

            const cost = (c1 === s2.charCodeAt(j - 1)) ? 0 : 1;

            curr[j] = Math.min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost);

        }

        for (let j = 0; j <= n; j++) prev[j] = curr[j];

    }

    return prev[n];

};



// Từ điển từ viết tắt và đồng nghĩa ngành y tế / phòng khám

window.CLINIC_ABBREVIATIONS = {

    'bs': ['bac si', 'bac sy', 'doctor', 'bs'],

    'bacsi': ['bs', 'bac si', 'bac sy'],

    'bacsy': ['bs', 'bac si', 'bac sy'],

    'nv': ['nhan vien', 'staff', 'nv'],

    'nhanvien': ['nv', 'nhan vien'],

    'ktv': ['ky thuat vien', 'ki thuat vien', 'technician', 'ktv'],

    'cls': ['can lam sang', 'canlamsang', 'xet nghiem', 'cls'],

    'tmh': ['tai mui hong', 'tmh'],

    'rhm': ['rang ham mat', 'rhm'],

    'yhct': ['y hoc co truyen', 'yhct', 'dong y'],

    'pkn': ['phong kham noi', 'khoa noi', 'pkn'],

    'pk': ['phong kham', 'pk'],

    'bn': ['benh nhan', 'patient', 'bn'],

    'ds': ['duoc si', 'pharmacist', 'nha thuoc', 'ds'],

    'dd': ['dieu duong', 'nurse', 'dd'],

    'lt': ['le tan', 'tiep tan', 'receptionist', 'lt'],

    'tt': ['tiep tan', 'thanh toan', 'tt'],

    'ck': ['chuyen khoa', 'ck'],

    'xq': ['x quang', 'xquang', 'xq'],

    'sa': ['sieu am', 'sa'],

    'ct': ['chup cat lop', 'ct scan', 'ct'],

    'mri': ['cong huong tu', 'mri']

};



window.isWordFuzzyMatch = function(qWord, tWord) {

    if (!qWord || !tWord) return false;

    if (qWord === tWord) return true;

    if (tWord.startsWith(qWord)) return true;



    // Chuẩn hóa i và y ở cuối từ tiếng Việt (ví dụ: si/sy, ky/ki, ly/li)

    const qNormIY = qWord.replace(/y$/, 'i');

    const tNormIY = tWord.replace(/y$/, 'i');

    if (qNormIY === tNormIY || tNormIY.startsWith(qNormIY)) return true;



    if (qWord.length <= 2) {

        return (qWord.length === 2 && tWord.length === 2 && window.levenshteinDistance(qWord, tWord) <= 1);

    }

    if (qWord.length === 3) return tWord === qWord || (tWord.includes(qWord) && tWord.length <= 5) || window.levenshteinDistance(qWord, tWord) <= 1;

    if (tWord.includes(qWord)) return true;



    const maxDist = qWord.length >= 6 ? 2 : 1;

    if (Math.abs(qWord.length - tWord.length) <= maxDist) {

        if (window.levenshteinDistance(qWord, tWord) <= maxDist) return true;

    }

    if (tWord.length > qWord.length) {

        const prefix = tWord.slice(0, qWord.length);

        if (window.levenshteinDistance(qWord, prefix) <= maxDist) return true;

    }

    return false;

};



// Thuật toán so khớp thông minh: không dấu, viết tắt, từ đồng nghĩa, đảo thứ tự, viết hoa thường

window.smartMatch = function(query, target) {

    if (!query || !String(query).trim()) return true;

    if (!target) return false;



    const qClean = window.removeVietnameseTones(String(query)).trim();

    const tClean = window.removeVietnameseTones(String(target)).trim();



    if (!qClean) return true;

    if (!tClean) return false;



    if (tClean.includes(qClean)) return true;



    const qDigits = qClean.replace(/\D/g, '');

    const tDigits = tClean.replace(/\D/g, '');

    if (qDigits.length >= 3 && tDigits.includes(qDigits)) return true;



    const targetWords = tClean.split(/[^a-z0-9]+/).filter(Boolean);

    const queryTokens = qClean.split(/[^a-z0-9]+/).filter(Boolean);

    if (queryTokens.length === 0) return true;



    const targetAcronym = targetWords.map(w => w[0]).join('');

    if (queryTokens.length === 1 && qClean.length >= 2 && !qClean.includes(' ')) {

        if (targetAcronym === qClean || targetAcronym.startsWith(qClean) || targetAcronym.includes(qClean)) return true;

    }



    return queryTokens.every(qToken => {

        if (targetWords.some(tWord => window.isWordFuzzyMatch(qToken, tWord))) return true;



        const synonyms = window.CLINIC_ABBREVIATIONS[qToken];

        if (synonyms) {

            for (let syn of synonyms) {

                if (tClean.includes(syn)) return true;

                const synWords = syn.split(/\s+/);

                if (synWords.every(sw => targetWords.some(tw => window.isWordFuzzyMatch(sw, tw)))) return true;

            }

        }



        for (let [abbr, list] of Object.entries(window.CLINIC_ABBREVIATIONS)) {

            if (targetWords.includes(abbr) && list.some(item => item.includes(qToken) || qToken.includes(item))) {

                return true;

            }

        }



        return false;

    });

};



// Bí danh tương thích ngược

window.fuzzyMatch = window.smartMatch;



window.smartMatchRecord = function(query, fields) {

    if (!query || !String(query).trim()) return true;

    if (!Array.isArray(fields)) return false;

    const combined = fields.filter(Boolean).map(f => String(f)).join(' ');

    return window.smartMatch(query, combined);

};



window.fuzzyMatchRecord = window.smartMatchRecord;



document.addEventListener('DOMContentLoaded', () => {
    // 1. Cập nhật thời gian và ngày tháng thực trên Dashboard
    const updateDateTime = () => {
        const timeElement = document.getElementById('current-time');
        const dateElement = document.getElementById('current-date');

        if (timeElement || dateElement) {
            const now = new Date();
            if (timeElement) {
                timeElement.textContent = now.toLocaleTimeString('vi-VN', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                }).toUpperCase();
            }
            if (dateElement) {
                dateElement.textContent = now.toLocaleDateString('vi-VN', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                });
            }
        }
    };

    updateDateTime();
    setInterval(updateDateTime, 30000);

    // 2. Quản lý trạng thái Ghim và Giữ mở khi chuyển trang cho Sidebar
    const sidebar = document.getElementById('app-sidebar');
    const pinBtn = document.getElementById('sidebar-pin-btn');

    if (sidebar) {
        let isNavigating = false;

        const isPinned = localStorage.getItem('h2t_sidebar_pinned') === 'true';
        if (isPinned) {
            sidebar.classList.add('is-pinned');
            updatePinIcon(true);
        }

        // Bỏ class no-transition và sidebar-keep-open ngay sau khi browser đã render khung hình đầu tiên
        requestAnimationFrame(() => {
            setTimeout(() => {
                document.documentElement.classList.remove('sidebar-keep-open');
                sidebar.classList.remove('no-transition');
            }, 120);
        });

        // Kiểm tra vị trí chuột: Nếu con trỏ chuột đã ra khỏi sidebar thì mới thu gọn
        const checkCursorPosition = (e) => {
            if (isPinned) return;
            const rect = sidebar.getBoundingClientRect();
            const isInside = (
                e.clientX >= rect.left &&
                e.clientX <= rect.right &&
                e.clientY >= rect.top &&
                e.clientY <= rect.bottom
            );
            if (!isInside) {
                sidebar.classList.remove('is-hold-open');
                sessionStorage.removeItem('h2t_sidebar_open');
            }
        };

        // Khi chuột di chuyển lần đầu sau khi load trang
        window.addEventListener('mousemove', checkCursorPosition, { once: true, passive: true });

        // Khi chuột rời khỏi vùng sidebar
        sidebar.addEventListener('mouseleave', () => {
            if (isNavigating) return;
            if (!isPinned) {
                sidebar.classList.remove('is-hold-open');
                sessionStorage.removeItem('h2t_sidebar_open');
            }
        });

        // Khi chuột rê vào vùng sidebar
        sidebar.addEventListener('mouseenter', () => {
            sessionStorage.setItem('h2t_sidebar_open', '1');
        });

        // Khi click vào bất kỳ link nào trong sidebar, ghi nhớ trạng thái mở và đánh dấu đang điều hướng
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                isNavigating = true;
                sessionStorage.setItem('h2t_sidebar_open', '1');
            });
        });

        if (pinBtn) {
            pinBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const nowPinned = sidebar.classList.toggle('is-pinned');
                localStorage.setItem('h2t_sidebar_pinned', nowPinned);
                updatePinIcon(nowPinned);
                if (nowPinned) {
                    sessionStorage.setItem('h2t_sidebar_open', '1');
                }
                window.showToast(nowPinned ? 'Đã ghim cố định mở rộng menu' : 'Đã bật chế độ tự động thò thụt khi rê chuột', 'info');
            });
        }
    }

    function updatePinIcon(pinned) {
        if (!pinBtn) return;
        const icon = pinBtn.querySelector('i');
        if (icon) {
            if (pinned) {
                icon.className = 'fa-solid fa-thumbtack text-medical-400 rotate-45';
                pinBtn.title = 'Bỏ ghim (chuyển sang tự động thò thụt)';
            } else {
                icon.className = 'fa-solid fa-thumbtack text-slate-400';
                pinBtn.title = 'Ghim cố định menu mở rộng';
            }
        }
    }

    // 3. Hệ thống thông báo Toast popup với thời gian hiển thị 5 giây và nút đóng chủ động
    window.showToast = (message, type = 'success', duration = 5000) => {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 pointer-events-none';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-emerald-600' : (type === 'error' ? 'bg-rose-600' : (type === 'warning' ? 'bg-amber-600' : 'bg-slate-800'));
        const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : (type === 'warning' ? 'fa-triangle-exclamation' : 'fa-circle-info'));
        
        toast.className = `${bgColor} text-white px-4 py-3 rounded-xl shadow-2xl flex items-center justify-between gap-3 text-xs sm:text-sm font-medium transition-all duration-300 transform translate-y-4 opacity-0 pointer-events-auto max-w-md border border-white/10`;
        toast.innerHTML = `
            <div class="flex items-center gap-2.5">
                <i class="fa-solid ${icon} text-base shrink-0"></i>
                <span class="leading-snug">${message}</span>
            </div>
            <button type="button" class="ml-2 text-white/70 hover:text-white transition-colors cursor-pointer text-base leading-none p-1 rounded hover:bg-white/10" title="Đóng thông báo">&times;</button>
        `;

        const closeBtn = toast.querySelector('button');
        let removeTimer = null;

        const dismissToast = () => {
            if (removeTimer) clearTimeout(removeTimer);
            toast.classList.add('opacity-0', 'translate-y-2');
            setTimeout(() => {
                if (toast.parentElement) toast.remove();
            }, 300);
        };

        if (closeBtn) {
            closeBtn.addEventListener('click', dismissToast);
        }

        toastContainer.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-4', 'opacity-0');
        });

        removeTimer = setTimeout(dismissToast, Math.max(4500, duration));
    };

    // 4. Khởi tạo bộ chọn thẻ (tag selector) chuẩn hóa từ danh mục y tế
    window.initCatalogTagSelector = function({ containerId, hiddenInputId, catalog = [], placeholder = '', badgeClass = '', emptyLabel = 'Không có', maxSuggestions = 5 }) {
        const container = document.getElementById(containerId);
        const hiddenInput = document.getElementById(hiddenInputId);
        if (!container || !hiddenInput) return null;

        let selectedTags = [];
        const rawVal = (hiddenInput.value || '').trim();
        if (rawVal && rawVal !== 'Không có' && rawVal !== 'Không') {
            selectedTags = rawVal.split(',').map(s => s.trim()).filter(Boolean);
        }

        function syncHiddenInput() {
            hiddenInput.value = selectedTags.length > 0 ? selectedTags.join(', ') : (emptyLabel || 'Không có');
        }

        container.innerHTML = `
            <div class="relative bg-slate-50 border border-slate-200 rounded-2xl p-2.5 focus-within:bg-white focus-within:border-medical-500 focus-within:ring-2 focus-within:ring-medical-500/20 transition-all">
                <div class="tag-badges-box flex flex-wrap items-center gap-1.5 mb-2"></div>
                <div class="relative">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-magnifying-glass text-slate-400 text-xs"></i>
                        <input type="text" class="tag-search-input w-full bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none" placeholder="${placeholder}">
                    </div>
                    <div class="tag-dropdown hidden absolute left-0 right-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-xl max-h-56 overflow-y-auto z-40 p-1.5 space-y-1"></div>
                </div>
            </div>
            <div class="quick-suggestions flex flex-wrap items-center gap-1.5 pt-1.5"></div>
        `;

        const badgesBox = container.querySelector('.tag-badges-box');
        const searchInput = container.querySelector('.tag-search-input');
        const dropdown = container.querySelector('.tag-dropdown');
        const suggestionsBox = container.querySelector('.quick-suggestions');

        function renderBadges() {
            badgesBox.innerHTML = '';
            if (selectedTags.length === 0) {
                badgesBox.innerHTML = `<span class="text-[11px] text-slate-400 italic py-0.5">${emptyLabel || 'Chưa ghi nhận (Không có)'}</span>`;
                return;
            }
            selectedTags.forEach((tag, idx) => {
                const badge = document.createElement('span');
                badge.className = `inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold shadow-sm border ${badgeClass || 'bg-slate-100 text-slate-700 border-slate-200'}`;
                badge.innerHTML = `
                    <span>${tag}</span>
                    <button type="button" class="hover:opacity-70 focus:outline-none ml-0.5" title="Xóa mục này">
                        <i class="fa-solid fa-xmark text-[10px]"></i>
                    </button>
                `;
                badge.querySelector('button').addEventListener('click', () => {
                    selectedTags.splice(idx, 1);
                    syncHiddenInput();
                    renderBadges();
                    renderSuggestions();
                });
                badgesBox.appendChild(badge);
            });
        }

        function addTag(tag) {
            const clean = tag.trim();
            if (!clean || clean === 'Không có' || clean === 'Không') return;
            if (!selectedTags.includes(clean)) {
                selectedTags.push(clean);
                syncHiddenInput();
                renderBadges();
                renderSuggestions();
            }
            searchInput.value = '';
            dropdown.classList.add('hidden');
        }

        function renderDropdown(filterText = '') {
            const query = filterText.toLowerCase().trim();
            dropdown.innerHTML = '';

            const matched = (catalog || []).filter(item => 
                !selectedTags.includes(item) && (!query || window.fuzzyMatch(query, item))
            );

            if (matched.length > 0) {
                matched.forEach(item => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'w-full text-left px-3 py-2 text-xs rounded-lg text-slate-700 hover:bg-medical-50 hover:text-medical-700 flex items-center justify-between transition-colors';
                    btn.innerHTML = `<span>${item}</span><i class="fa-solid fa-plus text-[10px] text-slate-400"></i>`;
                    btn.addEventListener('mousedown', (e) => {
                        e.preventDefault();
                        addTag(item);
                    });
                    dropdown.appendChild(btn);
                });
            }

            // Chi cho phep chon dung cac muc co trong danh muc chuan (.txt)
            if (query && matched.length === 0) {
                const noteDiv = document.createElement('div');
                noteDiv.className = 'p-2.5 text-center text-xs text-amber-700 bg-amber-50 rounded-lg border border-amber-200';
                noteDiv.innerHTML = `<i class="fa-solid fa-circle-exclamation mr-1"></i>Vui lòng chọn đúng danh mục chuẩn trong hệ thống`;
                dropdown.appendChild(noteDiv);
            }

            if (dropdown.children.length === 0) {
                dropdown.innerHTML = '<div class="p-3 text-center text-xs text-slate-400">Không tìm thấy mục phù hợp</div>';
            }

            dropdown.classList.remove('hidden');
        }

        function renderSuggestions() {
            suggestionsBox.innerHTML = '<span class="text-[11px] text-slate-400 font-medium">Gợi ý nhanh:</span>';
            const unselected = (catalog || []).filter(c => !selectedTags.includes(c)).slice(0, maxSuggestions);
            if (unselected.length === 0) {
                suggestionsBox.classList.add('hidden');
                return;
            }
            suggestionsBox.classList.remove('hidden');
            unselected.forEach(c => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'text-[11px] px-2.5 py-0.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors flex items-center gap-1';
                btn.innerHTML = `<i class="fa-solid fa-plus text-[8px] text-slate-400"></i>${c.split('(')[0].trim()}`;
                btn.title = c;
                btn.addEventListener('click', () => addTag(c));
                suggestionsBox.appendChild(btn);
            });
        }

        searchInput.addEventListener('focus', () => renderDropdown(searchInput.value));
        searchInput.addEventListener('input', () => renderDropdown(searchInput.value));
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const firstBtn = dropdown.querySelector('button');
                if (firstBtn) firstBtn.dispatchEvent(new MouseEvent('mousedown'));
                // Khong cho them tu do ngoai danh muc chuan
                else { searchInput.value = ''; dropdown.classList.add('hidden'); }
            } else if (e.key === 'Backspace' && !searchInput.value && selectedTags.length > 0) {
                selectedTags.pop();
                syncHiddenInput();
                renderBadges();
                renderSuggestions();
            }
        });

        searchInput.addEventListener('blur', () => {
            setTimeout(() => dropdown.classList.add('hidden'), 200);
        });

        renderBadges();
        renderSuggestions();

        return {
            getTags: () => [...selectedTags],
            setTags: (tags) => {
                selectedTags = Array.isArray(tags) ? [...tags] : (tags ? tags.split(',').map(s=>s.trim()).filter(Boolean) : []);
                syncHiddenInput();
                renderBadges();
                renderSuggestions();
            },
            clear: () => {
                selectedTags = [];
                syncHiddenInput();
                renderBadges();
                renderSuggestions();
            }
        };
    };

    // 5. Tự động kiểm tra và đồng bộ chấm thông báo chưa đọc trên Header
    const headerBadge = document.getElementById('header-unread-badge');
    if (headerBadge) {
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if (data.success && data.unread_count > 0) {
                    headerBadge.classList.remove('hidden');
                } else {
                    headerBadge.classList.add('hidden');
                }
            })
            .catch(() => {});
    }

    // 6. Điều khiển ngăn kéo Sidebar trên thiết bị di động
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    if (mobileMenuBtn && sidebar) {
        let backdrop = document.getElementById('mobile-sidebar-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.id = 'mobile-sidebar-backdrop';
            backdrop.className = 'fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-40 hidden md:hidden transition-opacity';
            document.body.appendChild(backdrop);
        }

        const closeMobileSidebar = () => {
            sidebar.classList.remove('mobile-sidebar-open');
            backdrop.classList.add('hidden');
        };

        mobileMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = sidebar.classList.toggle('mobile-sidebar-open');
            backdrop.classList.toggle('hidden', !isOpen);
        });

        backdrop.addEventListener('click', closeMobileSidebar);
        sidebar.querySelectorAll('a').forEach(a => {
            a.addEventListener('click', () => {
                if (window.innerWidth < 768) closeMobileSidebar();
            });
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeMobileSidebar();
        });
    }

    // 7. Phím tắt thao tác nhanh cho phân hệ Quản trị và Y tế
    if (window.location.pathname.startsWith('/admin')) {
        document.addEventListener('keydown', (e) => {
            const tag = (document.activeElement && document.activeElement.tagName) || '';
            const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(tag) || (document.activeElement && document.activeElement.isContentEditable);

            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                const searchInput = document.querySelector('main input[type="search"], main input[placeholder*="Tìm"], main input[name="search"], main input[id*="search"]');
                if (searchInput) {
                    e.preventDefault();
                    searchInput.focus();
                    searchInput.select();
                }
            } else if (!isTyping && e.altKey && e.key.toLowerCase() === 'p') {
                e.preventDefault();
                window.location.href = '/admin/patients';
            } else if (!isTyping && e.key === 'F2') {
                e.preventDefault();
                window.location.href = '/admin/reception';
            } else if (e.key === 'Escape') {
                document.querySelectorAll('.fixed.inset-0:not(.hidden)').forEach(modal => {
                    if (modal.id && (modal.id.includes('modal') || modal.id.includes('Modal'))) {
                        modal.classList.add('hidden');
                        modal.classList.remove('flex');
                    }
                });
            }
        });
    }

    // 8. Hiệu ứng trượt ngang từ phải qua khi cuộn trang cho các phân vùng nội dung dài
    const revealItems = document.querySelectorAll('.reveal-slide-right');
    if (revealItems.length > 0 && 'IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.remove('reveal-pending');
                    entry.target.classList.add('reveal-visible');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

        revealItems.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.top > window.innerHeight * 0.92) {
                el.classList.add('reveal-pending');
                observer.observe(el);
            } else {
                el.classList.add('reveal-visible');
            }
        });
    }

    // 9. Khôi phục vị trí cuộn trang mượt mà sau khi reload
    try {
        const scrollKey = 'scroll_pos_' + window.location.pathname;
        const savedY = sessionStorage.getItem(scrollKey);
        if (savedY !== null) {
            sessionStorage.removeItem(scrollKey);
            setTimeout(() => {
                window.scrollTo({ top: parseFloat(savedY), behavior: 'instant' });
            }, 80);
        }
    } catch (e) {}
});

// Hàm hỗ trợ reload trang giữ nguyên vị trí cuộn và cập nhật tham số URL
window.reloadKeepingScroll = function(extraParams) {
    try {
        const scrollKey = 'scroll_pos_' + window.location.pathname;
        sessionStorage.setItem(scrollKey, window.scrollY.toString());
    } catch (e) {}
    if (extraParams && typeof extraParams === 'object') {
        const url = new URL(window.location.href);
        Object.entries(extraParams).forEach(([k, v]) => {
            if (v === null || v === undefined) url.searchParams.delete(k);
            else url.searchParams.set(k, v);
        });
        window.location.href = url.toString();
    } else {
        window.location.reload();
    }
};

// Bộ nhớ đệm Client-Side thông minh (Smart Client Cache)
window.H2TCache = {
    _memory: new Map(),
    get(key) {
        const item = this._memory.get(key);
        if (!item) return null;
        if (Date.now() > item.expiry) {
            this._memory.delete(key);
            return null;
        }
        return item.data;
    },
    set(key, data, ttlMs = 120000) {
        this._memory.set(key, { data: data, expiry: Date.now() + ttlMs });
    },
    delete(key) {
        this._memory.delete(key);
    },
    clear() {
        this._memory.clear();
    },
    async fetchCached(url, options = {}, ttlMs = 120000) {
        const key = url + JSON.stringify(options);
        const cached = this.get(key);
        if (cached) return cached;
        const res = await fetch(url, options);
        if (!res.ok) throw new Error('Yêu cầu thất bại với mã lỗi ' + res.status);
        const data = await res.json();
        this.set(key, data, ttlMs);
        return data;
    }
};

// Đồng bộ sự kiện thời gian thực liên tab (Cross-Tab Realtime Synchronizer)
window.H2TSync = {
    _channel: (typeof BroadcastChannel !== 'undefined') ? new BroadcastChannel('h2t_realtime_sync') : null,
    trigger(eventName = 'SYNC') {
        if (this._channel) {
            try { this._channel.postMessage({ event: eventName, time: Date.now() }); } catch (e) {}
        }
        try { localStorage.setItem('h2t_sync_' + eventName, Date.now().toString()); } catch (e) {}
        if (typeof window.triggerNotificationSync === 'function') {
            window.triggerNotificationSync();
        }
    },
    listen(eventName, callback) {
        if (this._channel) {
            this._channel.addEventListener('message', (e) => {
                if (e.data && e.data.event === eventName) callback(e.data);
            });
        }
        window.addEventListener('storage', (e) => {
            if (e.key === 'h2t_sync_' + eventName) callback({ time: e.newValue });
        });
    }
};




// 8. HỆ THỐNG CHUÔNG BÁO GỌI KHÁM VÀ CẢNH BÁO NGUY KỊCH (WEB AUDIO API)
let continuousChimeInterval = null;
let audioContextInstance = null;
let alertedNotificationIds = new Set();

function playMedicalChimeTone(isPanic = false) {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        if (!audioContextInstance) audioContextInstance = new AudioCtx();
        if (audioContextInstance.state === 'suspended') {
            audioContextInstance.resume();
        }
        const now = audioContextInstance.currentTime;
        const osc = audioContextInstance.createOscillator();
        const gain = audioContextInstance.createGain();
        osc.connect(gain);
        gain.connect(audioContextInstance.destination);

        if (isPanic) {
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(1100, now);
            osc.frequency.linearRampToValueAtTime(750, now + 0.25);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.45);
            osc.start(now);
            osc.stop(now + 0.45);
        } else {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.setValueAtTime(659.25, now + 0.28);
            osc.frequency.setValueAtTime(554.37, now + 0.56);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 1.4);
            osc.start(now);
            osc.stop(now + 1.4);
        }
    } catch (e) {
        console.warn('Audio chime notice:', e);
    }
}

function startContinuousAlertChime(notif) {
    if (continuousChimeInterval) return;
    const isPanic = (notif.loai_thong_bao === 'NguyKich');
    playMedicalChimeTone(isPanic);
    continuousChimeInterval = setInterval(() => playMedicalChimeTone(isPanic), isPanic ? 1600 : 2800);
    showChimeAlertModal(notif);
}

function stopContinuousAlertChime() {
    if (continuousChimeInterval) {
        clearInterval(continuousChimeInterval);
        continuousChimeInterval = null;
    }
    const modal = document.getElementById('h2t-chime-alert-modal');
    if (modal) modal.remove();
}

function showChimeAlertModal(notif) {
    let existing = document.getElementById('h2t-chime-alert-modal');
    if (existing) existing.remove();

    const isPanic = (notif.loai_thong_bao === 'NguyKich');
    const modal = document.createElement('div');
    modal.id = 'h2t-chime-alert-modal';
    modal.className = 'fixed inset-0 z-[9999] bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in';
    
    modal.innerHTML = `
        <div class="bg-white rounded-3xl max-w-md w-full p-6 text-center space-y-4 shadow-2xl border-4 ${isPanic ? 'border-rose-500' : 'border-teal-500'}">
            <div class="w-16 h-16 rounded-2xl ${isPanic ? 'bg-rose-100 text-rose-600' : 'bg-teal-100 text-teal-600'} flex items-center justify-center text-3xl mx-auto animate-bounce">
                <i class="fa-solid ${isPanic ? 'fa-triangle-exclamation' : 'fa-bell'}"></i>
            </div>
            <div>
                <span class="text-xs uppercase font-extrabold tracking-wider ${isPanic ? 'text-rose-600' : 'text-teal-600'}">
                    ${isPanic ? 'CẢNH BÁO GIÁ TRỊ NGUY KỊCH' : 'ĐÃ ĐẾN LƯỢT GỌI KHÁM BỆNH'}
                </span>
                <h3 class="text-lg font-black text-slate-900 mt-1">${notif.tieu_de || 'Thông báo khám bệnh'}</h3>
                <p class="text-xs text-slate-600 mt-2 leading-relaxed">${notif.noi_dung || ''}</p>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 flex items-center justify-center gap-2">
                <span class="w-2 h-2 rounded-full ${isPanic ? 'bg-rose-500' : 'bg-teal-500'} animate-ping"></span>
                <span>Chuông reo liên tục cho tới khi bạn nhấn vào thông báo.</span>
            </div>
            <button type="button" onclick="handleChimeAlertClick(${notif.id || 0}, '${notif.lien_ket || '/patient/appointments'}')" class="w-full py-3.5 px-6 rounded-2xl text-white font-black text-sm shadow-xl transition-all cursor-pointer ${isPanic ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-600/30' : 'bg-teal-600 hover:bg-teal-700 shadow-teal-600/30'} flex items-center justify-center gap-2">
                <i class="fa-solid fa-volume-xmark"></i>
                <span>TẮT CHUÔNG VÀ XEM CHI TIẾT</span>
            </button>
        </div>
    `;
    document.body.appendChild(modal);
}

window.handleChimeAlertClick = function(notifId, targetUrl) {
    stopContinuousAlertChime();
    if (notifId) {
        alertedNotificationIds.add(notifId);
        fetch(`/api/notifications/read/${notifId}`, { method: 'POST' }).catch(() => {});
    }
    if (targetUrl) {
        if (window.location.pathname.includes('/patient/appointments') && targetUrl.includes('/patient/appointments')) {
            try {
                const urlObj = new URL(targetUrl, window.location.origin);
                const hlId = urlObj.searchParams.get('highlight');
                if (hlId && typeof showAppointmentDetail === 'function') {
                    showAppointmentDetail(hlId);
                    const card = document.getElementById('appt-card-' + hlId) || document.querySelector(`.appointment-card[data-id="${hlId}"]`);
                    if (card) {
                        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        card.classList.add('ring-2', 'ring-teal-500', 'bg-teal-50/30');
                    }
                    return;
                }
            } catch (e) {}
        }
        window.location.href = targetUrl;
    }
};

// Polling định kỳ kiểm tra gọi khám tự động và cảnh báo nguy kịch
function checkRealtimeNotificationsAndQueue() {
    fetch('/api/queue/auto-call', { method: 'POST' }).catch(() => {});
    fetch('/api/notifications')
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('header-unread-badge');
            if (badge) {
                if (data.success && data.unread_count > 0) {
                    badge.classList.remove('hidden');
                } else {
                    badge.classList.add('hidden');
                }
            }
            if (data.success && Array.isArray(data.notifications)) {
                const urgent = data.notifications.find(n => 
                    !n.da_doc && !alertedNotificationIds.has(n.id) && 
                    (n.loai_thong_bao === 'GoiKham' || n.loai_thong_bao === 'NguyKich')
                );
                if (urgent) {
                    startContinuousAlertChime(urgent);
                }
            }
        })
        .catch(() => {});
}

// Bắt đầu chu kỳ polling tự động mỗi 10 giây
setInterval(checkRealtimeNotificationsAndQueue, 10000);
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(checkRealtimeNotificationsAndQueue, 1500);
});

// Cơ chế ngăn chặn người dùng bấm gửi nhiều lần (Double-Submit Protection)
window.applyDoubleSubmitProtection = function(btn, loadingText = 'Đang xử lý...') {
    if (!btn || btn.dataset.submitting === 'true') return false;
    btn.dataset.submitting = 'true';
    btn.dataset.originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add('opacity-75', 'cursor-not-allowed', 'pointer-events-none');
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i><span>${loadingText}</span>`;
    setTimeout(() => {
        window.resetButtonSubmitting(btn);
    }, 12000);
    return true;
};

window.resetButtonSubmitting = function(btn) {
    if (!btn || btn.dataset.submitting !== 'true') return;
    btn.dataset.submitting = 'false';
    btn.disabled = false;
    btn.classList.remove('opacity-75', 'cursor-not-allowed', 'pointer-events-none');
    if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
    }
};

// Tự động gắn Double-Submit Protection cho toàn bộ biểu mẫu gửi dữ liệu
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.tagName === 'FORM') {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], button:not([type="button"])');
        if (submitBtn && submitBtn.dataset.submitting === 'true') {
            e.preventDefault();
            return false;
        }
        if (submitBtn) {
            window.applyDoubleSubmitProtection(submitBtn, 'Đang gửi dữ liệu...');
        }
    }
});
