import io
import sys
import os
import re

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from models.user_model import UserModel
from core.database import get_db

with get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tai_khoan WHERE username = 'admin'")
    admin_id = cursor.fetchone()['id']
    admin_user = UserModel.get_session_user(admin_id)

app = create_app()
client = app.test_client()

with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = admin_user

res = client.get('/admin/staff')
html = res.data.decode('utf-8')
print(f'Total HTML length: {len(html)/1024:.1f} KB')

pattern = r'<script id="([^"]+)" type="application/json">(.*?)</script>'
for m in re.finditer(pattern, html, re.DOTALL):
    print(f'Script {m.group(1)}: {len(m.group(2))/1024:.1f} KB')

table_match = re.search(r'<tbody id="schedules-tbody">(.*?)</tbody>', html, re.DOTALL)
if table_match:
    print(f'Table tbody size: {len(table_match.group(1))/1024:.1f} KB')

# Check other large sections
lines = html.split('\n')
print(f'Total lines of HTML: {len(lines)}')
