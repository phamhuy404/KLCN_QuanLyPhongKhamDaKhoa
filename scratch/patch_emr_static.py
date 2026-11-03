import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'templates', 'admin', 'emr.html')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = '{% block content %}\n<div class="space-y-6">'
replacement = '{% block content %}\n<!-- Cac muc kham giu tinh hoan toan khong animation de tranh roi mat bac si -->\n<div class="space-y-6 emr-static-zone">'

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully added emr-static-zone to templates/admin/emr.html")
else:
    # Thử với CRLF
    target_crlf = '{% block content %}\r\n<div class="space-y-6">'
    replacement_crlf = '{% block content %}\r\n<!-- Cac muc kham giu tinh hoan toan khong animation de tranh roi mat bac si -->\r\n<div class="space-y-6 emr-static-zone">'
    if target_crlf in content:
        content = content.replace(target_crlf, replacement_crlf)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully added emr-static-zone with CRLF to templates/admin/emr.html")
    else:
        print("Target not found in emr.html")
