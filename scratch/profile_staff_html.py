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
print('Total HTML length:', len(data))

# Check where the big chunks are:
parts = data.split('\n')
print(f"Total lines: {len(parts)}")
for idx, line in enumerate(parts):
    if len(line) > 50000:
        print(f"Line {idx} length: {len(line)} chars: {line[:80]}...")
