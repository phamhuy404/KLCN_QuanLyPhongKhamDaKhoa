import os
import sys

# Dam bao import module tu thu muc goc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.backup_model import BackupModel

def main():
    backup_dir = BackupModel.get_backup_dir()
    if not os.path.exists(backup_dir):
        print(f"[LOI] Thu muc sao luu khong ton tai: {backup_dir}")
        return

    bak_files = [f for f in os.listdir(backup_dir) if f.endswith('.bak') and os.path.isfile(os.path.join(backup_dir, f))]
    if not bak_files:
        print(f"[LOI] Khong tim thay file .bak nao trong thu muc: {backup_dir}")
        return

    # Sap xep lay ban sao luu moi nhat theo thoi gian sua doi
    bak_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
    latest_bak = bak_files[0]

    print(f"[*] Tim thay ban sao luu moi nhat: {latest_bak}")
    print("[*] Dang tien hanh phuc hoi CSDL Microsoft SQL Server...")

    ok, msg = BackupModel.restore_backup(latest_bak, user_name='team_sync')
    if ok:
        print(f"[THANH CONG] {msg}")
        print("[*] Co so du lieu da duoc dong bo hoan tat. Ban co the chay: python app.py")
    else:
        print(f"[THAT BAI] {msg}")

if __name__ == '__main__':
    main()
