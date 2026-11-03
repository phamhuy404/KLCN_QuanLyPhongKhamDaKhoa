import sys, os, io
sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
app = create_app()
client = app.test_client()

with client.session_transaction() as sess:
    sess['logged_in'] = True
    sess['user'] = {'id': 1, 'username': 'admin', 'vai_tro': 'ADMIN', 'staff_id': 1}

res = client.get('/admin/staff')
data = res.data.decode('utf-8')
print('Total len:', len(data))

import re
matches = re.findall(r'<script id="([^"]+)"[^>]*>(.*?)</script>', data, re.DOTALL)
for m in matches:
    print(f"id={m[0]}: {len(m[1])//1024} KB")

# Also check for other big loops in staff.html
tr_count = data.count('<tr')
print(f"Total <tr tags: {tr_count}")
