import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('controllers/api_controller.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'reexam_date = ' in l:
        print(f"Line {i+1}: {l.strip()}")
