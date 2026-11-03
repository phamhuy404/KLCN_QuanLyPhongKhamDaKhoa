import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'app.py')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # Bỏ qua tài nguyên tĩnh, favicon và các route bảo trì/đăng xuất
        if request.path.startswith('/static') or request.path == '/favicon.ico':
            return None"""

replacement = """        # Bỏ qua request preflight CORS của Mobile, tài nguyên tĩnh, favicon
        if request.method == 'OPTIONS' or request.path.startswith('/static') or request.path == '/favicon.ico':
            return None"""

if target in content:
    content = content.replace(target, replacement)

target_patient = """                request.path in ('/register', '/auth/register') or
                request.path.startswith('/api/patient')
            )"""

replacement_patient = """                request.path in ('/register', '/auth/register') or
                request.path.startswith('/api/patient') or
                request.path.startswith('/api/v1/mobile/patient')
            )"""

if target_patient in content:
    content = content.replace(target_patient, replacement_patient)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py with mobile maintenance integration")
