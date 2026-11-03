"""Additive specialty templates; staff assignments remain explicit."""
SPECIALTIES = (
    ('TIMMACH', 'Tim mạch', 'Khám tăng huyết áp, rối loạn nhịp và nguy cơ tim mạch.', 200000),
    ('TIEUHOA', 'Tiêu hóa - Gan mật', 'Khám bệnh dạ dày, đại tràng, gan mật và rối loạn tiêu hóa.', 200000),
    ('NOITIET', 'Nội tiết - Đái tháo đường', 'Theo dõi đái tháo đường, bệnh tuyến giáp và chuyển hóa.', 200000),
    ('HOHAP', 'Hô hấp', 'Khám ho kéo dài, hen phế quản và bệnh phổi mạn tính.', 200000),
    ('CXXK', 'Cơ xương khớp', 'Khám đau khớp, thoái hóa cột sống và loãng xương.', 220000),
    ('DALIEU', 'Da liễu', 'Khám mụn, viêm da, dị ứng và bệnh da thường gặp.', 180000),
    ('THANKINH', 'Thần kinh', 'Khám đau đầu, chóng mặt và rối loạn giấc ngủ.', 220000),
    ('TIETNIEU', 'Tiết niệu', 'Khám sỏi tiết niệu, rối loạn tiểu tiện và bệnh tuyến tiền liệt.', 200000),
)


def add_specialty_templates():
    """One transaction; never move, overwrite or delete existing data."""
    from core.database import get_db
    conn = get_db()
    created = 0
    try:
        cursor = conn.cursor()
        for code, name, description, price in SPECIALTIES:
            cursor.execute('SELECT id FROM chuyen_khoa WITH (UPDLOCK, HOLDLOCK) WHERE ma_khoa=?', ('KHOA_' + code,))
            existing = cursor.fetchone()
            if existing:
                department_id = existing['id']
            else:
                cursor.execute('''INSERT INTO chuyen_khoa (ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai)
                    VALUES (?, ?, ?, 'fa-stethoscope', ?, 0)''', ('KHOA_' + code, name, description, price))
                department_id = cursor.lastrowid
                created += 1
            cursor.execute('SELECT id FROM phong_kham WITH (UPDLOCK, HOLDLOCK) WHERE ma_phong=?', ('PK_' + code,))
            if not cursor.fetchone():
                cursor.execute('''INSERT INTO phong_kham (chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai)
                    VALUES (?, ?, ?, ?, 0)''', (department_id, 'PK_' + code, 'Phòng ' + name, 'Chưa bố trí'))
            cursor.execute('SELECT id FROM dich_vu WITH (UPDLOCK, HOLDLOCK) WHERE ma_dich_vu=?', ('DV_CK_' + code,))
            if not cursor.fetchone():
                cursor.execute('''INSERT INTO dich_vu (chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai)
                    VALUES (?, ?, ?, N'Khám chuyên khoa', ?, 0, ?, 1)''', (department_id, 'DV_CK_' + code, 'Khám ' + name, price, description))
        conn.commit()
        return created
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
