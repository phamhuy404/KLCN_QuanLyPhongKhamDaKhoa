with open('core/image_service.py', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = """CATEGORY_DIRS = {
    'benh_nhan': 'benh_nhan',
    'bac_si': 'bac_si',
    'bai_viet': 'bai_viet',
    'banners': 'banners'
}"""

repl1 = """CATEGORY_DIRS = {
    'benh_nhan': 'benh_nhan',
    'bac_si': 'bac_si',
    'bai_viet': 'bai_viet',
    'banners': 'banners',
    'can_lam_sang': 'can_lam_sang'
}"""

target2 = """DIMENSION_LIMITS = {
    'benh_nhan': (400, 400),
    'bac_si': (500, 500),
    'bai_viet': (1200, 800),
    'banners': (1920, 800)
}"""

repl2 = """DIMENSION_LIMITS = {
    'benh_nhan': (400, 400),
    'bac_si': (500, 500),
    'bai_viet': (1200, 800),
    'banners': (1920, 800),
    'can_lam_sang': (1600, 1200)
}"""

c = c.replace(target1, repl1).replace(target1.replace('\n', '\r\n'), repl1.replace('\n', '\r\n'))
c = c.replace(target2, repl2).replace(target2.replace('\n', '\r\n'), repl2.replace('\n', '\r\n'))

with open('core/image_service.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated core/image_service.py successfully!')
