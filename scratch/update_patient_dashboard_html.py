import os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'patient', 'dashboard.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    <!-- DASHBOARD GRID -->"""
replacement = """    <!-- THÔNG BÁO NHẮC LỊCH HOẶC TIẾP NHẬN NỔI BẬT -->
    {% if recent_notifications %}
        {% for n in recent_notifications[:1] %}
        <div class="p-4 rounded-2xl bg-gradient-to-r from-teal-50 to-emerald-50 border border-teal-200 text-teal-900 shadow-sm flex items-start gap-3.5">
            <div class="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center text-lg shrink-0 shadow-sm shadow-teal-600/20">
                <i class="fa-solid fa-bell"></i>
            </div>
            <div class="flex-1 text-xs">
                <div class="flex items-center justify-between">
                    <h4 class="font-bold text-sm text-teal-950">{{ n.tieu_de }}</h4>
                    <span class="text-[11px] text-teal-700 font-mono">{{ n.thoi_gian_tao }}</span>
                </div>
                <p class="text-teal-800 mt-1 leading-relaxed">{{ n.noi_dung }}</p>
                {% if n.lien_ket %}
                <a href="{{ n.lien_ket }}" class="inline-flex items-center gap-1 font-bold text-teal-700 hover:text-teal-900 mt-1.5 hover:underline">
                    Xem chi tiết <i class="fa-solid fa-arrow-right text-[10px]"></i>
                </a>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    {% endif %}

    <!-- DASHBOARD GRID -->"""

if target in content and "THÔNG BÁO NHẮC LỊCH HOẶC TIẾP NHẬN NỔI BẬT" not in content:
    content = content.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated templates/patient/dashboard.html successfully!")
else:
    print("Target already updated or not found!")
