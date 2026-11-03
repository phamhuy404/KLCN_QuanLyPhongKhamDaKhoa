import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'templates', 'auth', 'register.html')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Card chính
old_card = '<div class="max-w-xl w-full bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden p-8 sm:p-10">'
new_card = '<div class="max-w-xl w-full bg-white dark:bg-slate-800 rounded-3xl shadow-2xl shadow-slate-300/50 dark:shadow-slate-900/50 border border-slate-100 dark:border-slate-700 overflow-hidden p-8 sm:p-10 animate-modal-up">'
content = content.replace(old_card, new_card)

# 2. Header
old_header = """        <div class="mt-6 mb-6">
            <h2 class="text-2xl font-bold text-slate-900">Tạo tài khoản khám bệnh</h2>
            <p class="text-slate-500 text-sm mt-1">Đăng ký nhanh tài khoản. Bạn sẽ hoàn thiện hồ sơ y tế chi tiết sau khi đăng nhập lần đầu.</p>
        </div>"""

new_header = """        <div class="mt-6 mb-6 anim-fade-up anim-delay-1">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Tạo tài khoản khám bệnh</h2>
            <p class="text-slate-500 text-sm mt-1">Đăng ký nhanh tài khoản. Bạn sẽ hoàn thiện hồ sơ y tế chi tiết sau khi đăng nhập lần đầu.</p>
        </div>"""
content = content.replace(old_header, new_header)

# 3. Banner
old_banner = '<div class="mb-5 p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start gap-2.5">'
new_banner = '<div class="mb-5 p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs flex items-start gap-2.5 anim-fade-up anim-delay-2">'
content = content.replace(old_banner, new_banner)

# 4. Form inputs
content = content.replace('<form action="{{ url_for(\'register\') }}" method="POST" class="space-y-4">', '<form action="{{ url_for(\'register\') }}" method="POST" class="space-y-4 anim-fade-up anim-delay-3">')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated register.html with modern animations successfully")
