import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_mobile_patient_api.py')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = '"""HTTP contract/security tests using signed tokens and isolated model doubles; never SQL production."""\nimport io'
replacement = '"""HTTP contract/security tests using signed tokens and isolated model doubles; never SQL production."""\nimport os\nimport sys\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \'..\')))\nimport io'

if target in content:
    content = content.replace(target, replacement)
else:
    target_crlf = '"""HTTP contract/security tests using signed tokens and isolated model doubles; never SQL production."""\r\nimport io'
    replacement_crlf = '"""HTTP contract/security tests using signed tokens and isolated model doubles; never SQL production."""\r\nimport os\r\nimport sys\r\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \'..\')))\r\nimport io'
    if target_crlf in content:
        content = content.replace(target_crlf, replacement_crlf)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched test_mobile_patient_api.py")
