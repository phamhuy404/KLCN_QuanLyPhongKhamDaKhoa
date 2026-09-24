/**
 * H2T Healthcare - Main Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Cập nhật thời gian & ngày tháng thực trên Dashboard
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

    // 2. Quản lý trạng thái Ghim (Pin / Unpin) Sidebar nếu người dùng muốn cố định
    const sidebar = document.getElementById('app-sidebar');
    const pinBtn = document.getElementById('sidebar-pin-btn');

    if (sidebar && pinBtn) {
        // Kiểm tra tùy chọn đã lưu trong LocalStorage
        const isPinned = localStorage.getItem('h2t_sidebar_pinned') === 'true';
        if (isPinned) {
            sidebar.classList.add('is-pinned');
            updatePinIcon(true);
        }

        pinBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const nowPinned = sidebar.classList.toggle('is-pinned');
            localStorage.setItem('h2t_sidebar_pinned', nowPinned);
            updatePinIcon(nowPinned);
            window.showToast(nowPinned ? 'Đã ghim mở rộng menu' : 'Đã bật chế độ tự động thò thụt khi rê chuột', 'info');
        });
    }

    function updatePinIcon(pinned) {
        if (!pinBtn) return;
        const icon = pinBtn.querySelector('i');
        if (icon) {
            if (pinned) {
                icon.className = 'fa-solid fa-thumbtack text-medical-600 rotate-45';
                pinBtn.title = 'Bỏ ghim (chuyển sang tự động thò thụt)';
            } else {
                icon.className = 'fa-solid fa-thumbtack text-slate-400';
                pinBtn.title = 'Ghim cố định menu mở rộng';
            }
        }
    }

    // 3. Hệ thống thông báo Toast popup mượt mà
    window.showToast = (message, type = 'success') => {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-emerald-600' : (type === 'error' ? 'bg-rose-600' : 'bg-slate-800');
        const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-info');
        
        toast.className = `${bgColor} text-white px-5 py-3.5 rounded-xl shadow-xl flex items-center gap-3 text-sm font-medium transition-all duration-300 transform translate-y-4 opacity-0 pointer-events-auto max-w-md`;
        toast.innerHTML = `
            <i class="fa-solid ${icon} text-lg"></i>
            <span>${message}</span>
        `;

        toastContainer.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-4', 'opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-2');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };
});
