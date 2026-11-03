import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'controllers', 'admin_controller.py')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """def backups():
    \"\"\"Quản lý sao lưu và phục hồi cơ sở dữ liệu an toàn (Dành riêng cho Quản trị viên).\"\"\"
    from models.backup_model import BackupModel
    backup_data = BackupModel.list_backups()
    return render_template('admin/backups.html', active_page='admin_backups', backup_data=backup_data)"""

replacement = """def backups():
    \"\"\"Quản lý sao lưu và phục hồi cơ sở dữ liệu an toàn (Dành riêng cho Quản trị viên).\"\"\"
    from models.backup_model import BackupModel
    from models.system_setting_model import SystemSettingModel
    backup_data = BackupModel.list_backups()
    system_settings = SystemSettingModel.get_settings()
    return render_template('admin/backups.html', active_page='admin_backups', backup_data=backup_data, system_settings=system_settings)"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched admin_controller.py backups()")
else:
    print("Target not found in admin_controller.py")
