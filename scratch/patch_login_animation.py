import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'templates', 'auth', 'login.html')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Thêm animate-modal-up vào card chính
old_card = '<div class="max-w-4xl w-full bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden grid grid-cols-1 md:grid-cols-2">'
new_card = '<div class="max-w-4xl w-full bg-white dark:bg-slate-800 rounded-3xl shadow-2xl shadow-slate-300/50 dark:shadow-slate-900/50 border border-slate-100 dark:border-slate-700 overflow-hidden grid grid-cols-1 md:grid-cols-2 animate-modal-up">'
content = content.replace(old_card, new_card)

# 2. Thêm anim-glow-float vào 2 quả cầu decor
content = content.replace('w-48 h-48 bg-white/10 rounded-full blur-2xl', 'w-48 h-48 bg-white/10 rounded-full blur-2xl anim-glow-float')
content = content.replace('w-56 h-56 bg-medical-500/20 rounded-full blur-3xl', 'w-56 h-56 bg-medical-500/20 rounded-full blur-3xl anim-glow-float')

# 3. Thêm staggered animation vào form
old_header = """            <div class="mb-6">
                <h3 class="text-2xl font-bold text-slate-900">Đăng nhập</h3>
                <p class="text-slate-400 text-sm mt-1">Chào mừng bạn trở lại với hệ thống phòng khám</p>
            </div>"""

new_header = """            <div class="mb-6 anim-fade-up anim-delay-1">
                <h3 class="text-2xl font-bold text-slate-900 dark:text-white">Đăng nhập</h3>
                <p class="text-slate-400 text-sm mt-1">Chào mừng bạn trở lại với hệ thống phòng khám</p>
            </div>"""
content = content.replace(old_header, new_header)

old_username = """                <div>
                    <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Tên đăng nhập hoặc Số điện thoại</label>"""

new_username = """                <div class="anim-fade-up anim-delay-2">
                    <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">Tên đăng nhập hoặc Số điện thoại</label>"""
content = content.replace(old_username, new_username)

old_password = """                <div>
                    <div class="flex items-center justify-between mb-2">
                        <label class="text-xs font-semibold text-slate-700 uppercase tracking-wider">Mật khẩu</label>"""

new_password = """                <div class="anim-fade-up anim-delay-3">
                    <div class="flex items-center justify-between mb-2">
                        <label class="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Mật khẩu</label>"""
content = content.replace(old_password, new_password)

old_remember = """                <div class="flex items-center justify-between py-1">"""
new_remember = """                <div class="flex items-center justify-between py-1 anim-fade-up anim-delay-4">"""
content = content.replace(old_remember, new_remember)

old_btn = """                <button type="submit" id="submit-btn" class="w-full py-3.5 px-4 bg-medical-600 hover:bg-medical-700 text-white font-bold rounded-xl shadow-lg shadow-medical-600/30 transition-all text-sm flex items-center justify-center gap-2">"""
new_btn = """                <button type="submit" id="submit-btn" class="w-full py-3.5 px-4 bg-medical-600 hover:bg-medical-700 text-white font-bold rounded-xl shadow-lg shadow-medical-600/30 transition-all text-sm flex items-center justify-center gap-2 hover:scale-[1.01] active:scale-[0.99] anim-fade-up anim-delay-4">"""
content = content.replace(old_btn, new_btn)

old_register = """            <div class="mt-6 text-center text-sm text-slate-500">"""
new_register = """            <div class="mt-6 text-center text-sm text-slate-500 anim-fade-up anim-delay-5">"""
content = content.replace(old_register, new_register)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated login.html with modern animations successfully")
