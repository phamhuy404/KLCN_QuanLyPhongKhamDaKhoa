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

    // 2. Quản lý trạng thái thu gọn / mở rộng Sidebar & hiệu ứng Hover
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebarTexts = document.querySelectorAll('.sidebar-text');
    const brandText = document.getElementById('sidebar-brand-text');
    const supportBox = document.getElementById('sidebar-support-box');

    let isCollapsed = false;

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            isCollapsed = !isCollapsed;
            applySidebarState();
        });

        // Tự động bung rộng khi rê chuột vào nếu đang ở trạng thái thu gọn
        sidebar.addEventListener('mouseenter', () => {
            if (isCollapsed) {
                sidebar.classList.remove('w-20');
                sidebar.classList.add('w-64');
                sidebarTexts.forEach(el => el.classList.remove('hidden'));
                if (brandText) brandText.classList.remove('hidden');
                if (supportBox) supportBox.classList.remove('hidden');
            }
        });

        sidebar.addEventListener('mouseleave', () => {
            if (isCollapsed) {
                sidebar.classList.remove('w-64');
                sidebar.classList.add('w-20');
                sidebarTexts.forEach(el => el.classList.add('hidden'));
                if (brandText) brandText.classList.add('hidden');
                if (supportBox) supportBox.classList.add('hidden');
            }
        });
    }

    function applySidebarState() {
        if (isCollapsed) {
            sidebar.classList.remove('w-64');
            sidebar.classList.add('w-20');
            sidebarTexts.forEach(el => el.classList.add('hidden'));
            if (brandText) brandText.classList.add('hidden');
            if (supportBox) supportBox.classList.add('hidden');
        } else {
            sidebar.classList.remove('w-20');
            sidebar.classList.add('w-64');
            sidebarTexts.forEach(el => el.classList.remove('hidden'));
            if (brandText) brandText.classList.remove('hidden');
            if (supportBox) supportBox.classList.remove('hidden');
        }
    }

    // 3. Giả lập thông báo / Toast popup
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
