// Quan ly giao dien Sang va Toi (Dark Mode) cho toan bo he thong H2T Healthcare

(function initTheme() {
    try {
        const theme = localStorage.getItem('h2t_theme') || localStorage.getItem('theme');
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (theme === 'dark' || (!theme && prefersDark)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    } catch (e) {}
})();

window.toggleDarkMode = function() {
    const html = document.documentElement;
    const isDark = html.classList.toggle('dark');
    const newTheme = isDark ? 'dark' : 'light';
    try {
        localStorage.setItem('h2t_theme', newTheme);
        localStorage.setItem('theme', newTheme);
    } catch (e) {}
    window.updateThemeUI(isDark);
};

window.updateThemeUI = function(isDark) {
    if (typeof isDark === 'undefined') {
        isDark = document.documentElement.classList.contains('dark');
    }
    document.querySelectorAll('.theme-toggle-icon').forEach(function(icon) {
        if (isDark) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
};

document.addEventListener('DOMContentLoaded', function() {
    window.updateThemeUI();
});
