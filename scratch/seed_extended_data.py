import os
import sys
from datetime import date, datetime, timedelta
import random

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from core.database import get_db
from core.security import hash_password

def seed_all():
    conn = get_db()
    cursor = conn.cursor()
    print("Bắt đầu khởi tạo dữ liệu mở rộng...")

    # 1. Thêm dịch vụ khám chuyên sâu mới vào bảng dich_vu
    new_services = [
        # Khoa 1: Nội Tổng Quát
        (1, 'DV_KHAM_NOI_DOTQUY', 'Khám và Tầm soát Nguy cơ Đột quỵ Não', 'Khám chuyên khoa', 250000, 80, 'Khám chuyên sâu tầm soát nguy cơ tai biến mạch máu não và xơ vữa động mạch'),
        (1, 'DV_KHAM_NOI_CXK_GOUT', 'Khám Chuyên sâu Thoái hóa Khớp và Bệnh Gout', 'Khám chuyên khoa', 200000, 80, 'Chẩn đoán và phác đồ điều trị viêm khớp, thoái hóa khớp, tăng acid uric'),
        # Khoa 2: Ngoại Tổng Quát
        (2, 'DV_KHAM_NGOAI_HAUMON', 'Khám Chuyên sâu Bệnh lý Hậu môn - Trực tràng và Trĩ', 'Khám chuyên khoa', 220000, 80, 'Khám đánh giá mức độ trĩ, nứt kẽ hậu môn và tư vấn phẫu thuật ít xâm lấn'),
        (2, 'DV_KHAM_NGOAI_TUYENGIAP', 'Khám Tầm soát Bướu cổ và Khối u Tuyến giáp', 'Khám chuyên khoa', 200000, 80, 'Khám ngoại khoa bướu nhân, nang tuyến giáp và chỉ định chọc hút tế bào'),
        # Khoa 3: Nhi
        (3, 'DV_KHAM_NHI_TUKY', 'Khám Sàng lọc Sớm Rối loạn Phát triển & Tự kỷ Trẻ em', 'Khám chuyên khoa', 250000, 0, 'Đánh giá hành vi, ngôn ngữ và phát triển tâm thần vận động trẻ nhỏ'),
        (3, 'DV_KHAM_NHI_SOSINH', 'Khám và Tư vấn Sơ sinh - Chăm sóc Rốn Trẻ sơ sinh', 'Khám chuyên khoa', 150000, 80, 'Khám tổng thể sơ sinh, theo dõi vàng da, chăm sóc cuống rốn và dinh dưỡng mẹ bé'),
        # Khoa 4: Răng Hàm Mặt
        (4, 'DV_KHAM_RHM_IMPLANT', 'Khám và Tư vấn Kỹ thuật Cấy ghép Implant Nha khoa', 'Khám chuyên khoa', 200000, 0, 'Khảo sát xương hàm, khớp cắn và lập kế hoạch phục hình răng Implant'),
        (4, 'DV_TT_TRAM_RANG_COMPOSITE', 'Trám răng Thẩm mỹ Composite Quang trùng hợp công nghệ cao', 'Thủ thuật', 350000, 0, 'Tái tạo thẩm mỹ răng sâu, mẻ vỡ bằng vật liệu Composite thế hệ mới'),
        # Khoa 5: Sản - Phụ Khoa
        (5, 'DV_KHAM_SAN_TIENMANKINH', 'Khám và Tư vấn Tiền mãn kinh - Mãn kinh Nữ khoa', 'Khám chuyên khoa', 220000, 80, 'Đánh giá nội tiết tố, loãng xương, rối loạn vận mạch và tư vấn liệu pháp HRT'),
        (5, 'DV_KHAM_SAN_UNGTHUVU', 'Khám Tầm soát Bệnh lý Tuyến vú và Ung thư Phụ khoa', 'Khám chuyên khoa', 280000, 80, 'Khám lâm sàng vú, tuyến giáp và tầm soát ung thư phụ khoa toàn diện'),
        # Khoa 6: Tai Mũi Họng
        (6, 'DV_KHAM_TMH_VOMHONG', 'Khám và Nội soi Tầm soát sớm Ung thư Vòm họng', 'Khám chuyên khoa', 280000, 80, 'Nội soi dải tần ánh sáng hẹp NBI quan sát niêm mạc vòm họng và hốc mũi'),
        (6, 'DV_TT_RUA_XOANG_APLUC', 'Hút rửa Xoang bằng Áp lực âm & Khí dung Mũi xoang', 'Thủ thuật', 160000, 80, 'Làm sạch dịch mủ xoang, thông thoáng đường thở và giảm phù nề niêm mạc'),
        # Khoa 7: Mắt
        (7, 'DV_KHAM_MAT_BANDO_GIACMAC', 'Đo Bản đồ Giác mạc và Khảo sát Tật khúc xạ chuyên sâu', 'Khám chuyên khoa', 250000, 80, 'Đánh giá độ cong giác mạc, phát hiện giác mạc chóp và kiểm tra chỉ số mổ cận'),
        (7, 'DV_TT_THONG_RUA_LE_DAO', 'Thông rửa Lệ đạo và Bơm thuốc điều trị Tắc lệ quản', 'Thủ thuật', 180000, 80, 'Thủ thuật giải phóng tắc nghẽn tuyến lệ, hết chảy nước mắt sống và chống nhiễm trùng'),
        # Khoa 8: Cận Lâm Sàng & CĐHA
        (8, 'DV_XN_TROPONIN_I', 'Xét nghiệm Troponin-I siêu nhạy (Chẩn đoán sớm Nhồi máu cơ tim)', 'Xét nghiệm', 260000, 80, 'Định lượng hs-Troponin I phát hiện tổn thương cơ tim cấp tính trong vòng 1-3 giờ'),
        (8, 'DV_CDHA_SA_TIM_THUCQUAN', 'Siêu âm Tim qua Thực quản chuyên sâu (Transesophageal Echo)', 'Chẩn đoán hình ảnh', 480000, 80, 'Khảo sát tổn thương van tim, huyết khối tiểu nhĩ và tim bẩm sinh độ phân giải cao')
    ]

    added_sv = 0
    for ck_id, code, name, ldv, price, bhyt, desc in new_services:
        cursor.execute("SELECT 1 FROM dich_vu WHERE ma_dich_vu = ?", (code,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO dich_vu (chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (ck_id, code, name, ldv, price, bhyt, desc))
            added_sv += 1
    print(f"-> Đã thêm {added_sv} dịch vụ khám chuyên sâu mới vào bảng dich_vu.")

    # 2. Thêm 10 bệnh nhân có thông tin cá nhân thiếu ngẫu nhiên
    hashed_pwd = hash_password('BenhNhan@123')
    now_date_str = date.today().isoformat()
    now_dt_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    patients_seed = [
        {
            'ma_bn': 'BN2609024',
            'ho_ten': 'Lê Hoàng Long',
            'sdt': '0981122334',
            'ngay_sinh': '1995-04-12',
            'gioi_tinh': 'Nam',
            'dia_chi': 'Số 45 Lê Văn Sỹ, Phường 13, Quận 3, TP. Hồ Chí Minh',
            'email': 'hoanglong.le@gmail.com',
            'cccd': '079095001234',
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609025',
            'ho_ten': 'Vũ Thị Bích Ngọc',
            'sdt': '0972233445',
            'ngay_sinh': '2001-09-25',
            'gioi_tinh': 'Nữ',
            'dia_chi': 'Đường DT743, Dĩ An, Tỉnh Bình Dương',
            'email': 'bichngoc.vu@gmail.com',
            'cccd': '074101004321',
            'bhyt': '4790112233', # Có BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': 'Đau dạ dày nhẹ khi căng thẳng'
        },
        {
            'ma_bn': 'BN2609026',
            'ho_ten': 'Đặng Quốc Bảo',
            'sdt': '0963344556',
            'ngay_sinh': '1988-11-03',
            'gioi_tinh': 'Nam',
            'dia_chi': 'Khu phố 4, Phường Tân Biên, TP. Biên Hòa, Tỉnh Đồng Nai',
            'email': None,
            'cccd': None, # Thiếu CCCD
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': 'O+', # Có nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609027',
            'ho_ten': 'Phạm Thanh Thảo',
            'sdt': '0944455667',
            'ngay_sinh': '1998-02-18',
            'gioi_tinh': 'Nữ',
            'dia_chi': 'Xã Mỹ Hạnh Bắc, Huyện Đức Hòa, Tỉnh Long An',
            'email': 'thao.pham98@outlook.com',
            'cccd': '080198007654',
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': 'Dị ứng phấn hoa',
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609028',
            'ho_ten': 'Trịnh Đình Trọng',
            'sdt': '0935566778',
            'ngay_sinh': '1975-07-30',
            'gioi_tinh': 'Nam',
            'dia_chi': '128 Trường Chinh, Phường 12, Quận Tân Bình, TP. Hồ Chí Minh',
            'email': 'trong.trinhdinh@yahoo.com',
            'cccd': '079075003322',
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': 'Nguyễn Thị Mai', # Có người thân
            'nguoi_than_sdt': '0918889999',
            'nguoi_than_quan_he': 'Vợ',
            'di_ung': None,
            'tien_su_benh': 'Tăng huyết áp vô căn 3 năm'
        },
        {
            'ma_bn': 'BN2609029',
            'ho_ten': 'Hoàng Mỹ Duyên',
            'sdt': '0926677889',
            'ngay_sinh': '2003-12-14',
            'gioi_tinh': 'Nữ',
            'dia_chi': 'Ấp Ninh Trung, Xã Ninh Sơn, TP. Tây Ninh, Tỉnh Tây Ninh',
            'email': None,
            'cccd': None, # Thiếu CCCD
            'bhyt': '4790445566', # Có BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609030',
            'ho_ten': 'Bùi Hải Đăng',
            'sdt': '0917788990',
            'ngay_sinh': '1992-06-21',
            'gioi_tinh': 'Nam',
            'dia_chi': 'Ấp 1, Xã Trung An, TP. Mỹ Tho, Tỉnh Tiền Giang',
            'email': 'haidang.bui@gmail.com',
            'cccd': '082092005566',
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': 'Bùi Văn Hùng', # Có tên người thân
            'nguoi_than_sdt': None, # Thiếu SĐT người thân
            'nguoi_than_quan_he': 'Bố',
            'di_ung': 'Dị ứng hải sản tôm cua',
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609031',
            'ho_ten': 'Nguyễn Khánh Vy',
            'sdt': '0908899001',
            'ngay_sinh': '2000-08-09',
            'gioi_tinh': 'Nữ',
            'dia_chi': 'Số 72 Thùy Vân, Phường 2, TP. Vũng Tàu, Tỉnh Bà Rịa - Vũng Tàu',
            'email': 'khanhvy.ng@gmail.com',
            'cccd': None, # Thiếu CCCD
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609032',
            'ho_ten': 'Mai Văn Khiêm',
            'sdt': '0989900112',
            'ngay_sinh': '1982-03-05',
            'gioi_tinh': 'Nam',
            'dia_chi': 'Phường Phú Tân, TP. Bến Tre, Tỉnh Bến Tre',
            'email': 'khiemmai@gmail.com',
            'cccd': '071082006677',
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': None, # Thiếu nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': None
        },
        {
            'ma_bn': 'BN2609033',
            'ho_ten': 'Đỗ Thị Kim Chi',
            'sdt': '0970011223',
            'ngay_sinh': '1996-10-27',
            'gioi_tinh': 'Nữ',
            'dia_chi': 'Đường 30/4, Phường Hưng Lợi, Quận Ninh Kiều, TP. Cần Thơ',
            'email': 'kimchi.do@gmail.com',
            'cccd': None, # Thiếu CCCD
            'bhyt': None, # Thiếu BHYT
            'nhom_mau': 'A+', # Có nhóm máu
            'nguoi_than_ho_ten': None, # Thiếu người thân
            'nguoi_than_sdt': None,
            'nguoi_than_quan_he': None,
            'di_ung': None,
            'tien_su_benh': 'Viêm mũi dị ứng thời tiết'
        }
    ]

    added_patients = 0
    patient_id_map = {}
    for p in patients_seed:
        cursor.execute("SELECT id FROM benh_nhan WHERE sdt = ?", (p['sdt'],))
        row = cursor.fetchone()
        if not row:
            # Tạo tài khoản tương ứng
            cursor.execute("""
                INSERT INTO tai_khoan (username, password, email, sdt, vai_tro_id, trang_thai, da_hoan_thien_ho_so, yeu_cau_doi_mat_khau, ngay_tao)
                VALUES (?, ?, ?, ?, 5, 1, 1, 0, ?)
            """, (p['sdt'], hashed_pwd, p['email'], p['sdt'], now_dt_str))
            cursor.execute("SELECT id FROM tai_khoan WHERE username = ?", (p['sdt'],))
            uid = int(cursor.fetchone()['id'])

            cursor.execute("""
                INSERT INTO benh_nhan (
                    tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi,
                    nhom_mau, di_ung, tien_su_benh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he,
                    co_tai_khoan, ngay_tao
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    1, ?
                )
            """, (
                uid, p['ma_bn'], p['ho_ten'], p['ngay_sinh'], p['gioi_tinh'], p['sdt'], p['email'], p['cccd'], p['bhyt'], p['dia_chi'],
                p['nhom_mau'], p['di_ung'], p['tien_su_benh'], p['nguoi_than_ho_ten'], p['nguoi_than_sdt'], p['nguoi_than_quan_he'],
                now_date_str
            ))
            cursor.execute("SELECT id FROM benh_nhan WHERE ma_benh_nhan = ?", (p['ma_bn'],))
            pid = int(cursor.fetchone()['id'])
            patient_id_map[p['ma_bn']] = pid
            added_patients += 1
        else:
            patient_id_map[p['ma_bn']] = row['id']

    print(f"-> Đã thêm {added_patients} bệnh nhân mới với các trường thông tin thiếu ngẫu nhiên hợp lệ.")

    # 3. Tạo kịch bản Lịch hẹn trùng (Conflicting Appointments)
    p1_id = patient_id_map.get('BN2609024')
    p2_id = patient_id_map.get('BN2609025')
    p3_id = patient_id_map.get('BN2609026')
    p4_id = patient_id_map.get('BN2609027')

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Tình huống 1: Trùng ngày giờ đang Chờ xét duyệt (P1 và P2 cùng đặt BS 1 lúc 09:00 ngày mai)
    # Đảm bảo BS 1 có ca sáng ngày mai
    cursor.execute("""
        SELECT id FROM lich_lam_viec WHERE bac_si_id = 1 AND ngay_lam = ? AND ca_lam = 1
    """, (tomorrow,))
    shift1 = cursor.fetchone()
    if not shift1:
        cursor.execute("""
            INSERT INTO lich_lam_viec (bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai, trang_thai_duyet)
            VALUES (1, 1, ?, 1, '07:30', '11:30', 25, 2, 1, 'DA_DUYET')
        """, (tomorrow,))

    cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = 'LH2609101'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, chuyen_khoa_id, bac_si_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai, ngay_dat)
            VALUES ('LH2609101', ?, 1, 1, 1, ?, '09:00', N'Khám đau tức ngực và tăng huyết áp cơn', N'Chờ xét duyệt', ?)
        """, (p1_id, tomorrow, now_dt_str))

    cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = 'LH2609102'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, chuyen_khoa_id, bac_si_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai, ngay_dat)
            VALUES ('LH2609102', ?, 1, 1, 1, ?, '09:00', N'Khám tầm soát tim mạch và đo huyết áp định kỳ', N'Chờ xét duyệt', ?)
        """, (p2_id, tomorrow, now_dt_str))

    # Tình huống 2: Trùng đã xử lý tự động (P3 được duyệt, P4 tự động hủy do xung đột cùng giờ 14:30 của BS 2)
    cursor.execute("""
        SELECT id FROM lich_lam_viec WHERE bac_si_id = 2 AND ngay_lam = ? AND ca_lam = 2
    """, (tomorrow,))
    shift2 = cursor.fetchone()
    if not shift2:
        cursor.execute("""
            INSERT INTO lich_lam_viec (bac_si_id, phong_kham_id, ngay_lam, ca_lam, gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky, trang_thai, trang_thai_duyet)
            VALUES (2, 2, ?, 2, '13:00', '17:00', 25, 1, 1, 'DA_DUYET')
        """, (tomorrow,))

    cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = 'LH2609103'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, chuyen_khoa_id, bac_si_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai, ngay_dat)
            VALUES ('LH2609103', ?, 1, 2, 2, ?, '14:30', N'Tái khám điều trị viêm loét dạ dày - tá tràng', N'Đã duyệt', ?)
        """, (p3_id, tomorrow, now_dt_str))

    cursor.execute("SELECT id FROM lich_hen WHERE ma_lich_hen = 'LH2609104'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO lich_hen (ma_lich_hen, benh_nhan_id, chuyen_khoa_id, bac_si_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, trang_thai, ngay_dat)
            VALUES ('LH2609104', ?, 1, 2, 2, ?, '14:30', N'Khám trào ngược dạ dày thực quản (GERD)', N'Đã hủy', ?)
        """, (p4_id, tomorrow, now_dt_str))
        # Gửi thông báo in-app hủy cho P4
        cursor.execute("SELECT tai_khoan_id FROM benh_nhan WHERE id = ?", (p4_id,))
        p4_user = cursor.fetchone()
        if p4_user and p4_user['tai_khoan_id']:
            cursor.execute("""
                INSERT INTO thong_bao (tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
                VALUES (?, N'Lịch hẹn bị hủy do trùng giờ', N'Lịch hẹn #LH2609104 ngày %s lúc 14:30 của bạn đã bị hủy tự động do khung giờ này đã có bệnh nhân được duyệt trước. Vui lòng chọn khung giờ khác.', N'Hủy lịch hẹn', '/patient/booking', 0, ?)
            """ % tomorrow, (p4_user['tai_khoan_id'], now_dt_str))

    print("-> Đã khởi tạo kịch bản Đăng ký lịch trùng (Chờ duyệt và Tự động hủy khi duyệt).")

    # 4. Thêm dữ liệu lịch đi làm cũ của bác sĩ trong 10 tuần về trước (từ 2026-08-25 đến 2026-10-21)
    cursor.execute("""
        SELECT bs.id as bs_id, bs.nhan_vien_id, bs.chuyen_khoa_id, bs.phong_kham_chinh_id
        FROM bac_si bs
        WHERE bs.id <= 35
        ORDER BY bs.id
    """)
    doc_list = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT nv.id as nv_id, v.ma_vai_tro
        FROM nhan_vien nv
        JOIN tai_khoan tk ON nv.tai_khoan_id = tk.id
        JOIN vai_tro v ON tk.vai_tro_id = v.id
        WHERE v.ma_vai_tro IN ('LETAN', 'DUOCSI', 'KTV')
    """)
    other_staff_list = [dict(r) for r in cursor.fetchall()]

    start_date = date(2026, 8, 24)
    end_date = date(2026, 10, 21)
    days_count = (end_date - start_date).days + 1

    shift_times = {
        1: ('07:30', '11:30'),
        2: ('13:00', '17:00'),
        3: ('17:30', '20:30')
    }

    shifts_to_insert = []
    for day_idx in range(days_count):
        cur_d = start_date + timedelta(days=day_idx)
        cur_d_str = cur_d.isoformat()
        weekday = cur_d.weekday()

        active_ca = [1, 2] if weekday == 6 else [1, 2, 3]

        for d in doc_list:
            doc_id = d['bs_id']
            room_id = d['phong_kham_chinh_id'] or ((doc_id % 35) + 1)
            nv_id = d['nhan_vien_id']

            for ca in active_ca:
                if (doc_id + day_idx + ca) % 4 in (0, 1):
                    gio_bd, gio_kt = shift_times[ca]
                    max_kham = 25 if ca in (1, 2) else 15
                    reg_kham = (doc_id * 3 + day_idx * 2 + ca) % max_kham + 5
                    shifts_to_insert.append((
                        nv_id, doc_id, room_id, cur_d_str, ca,
                        gio_bd, gio_kt, max_kham, reg_kham,
                        1, 'DA_DUYET', 1, f"{cur_d_str} 06:00:00"
                    ))

        for s in other_staff_list:
            s_nv_id = s['nv_id']
            for ca in active_ca:
                if (s_nv_id + day_idx + ca) % 3 == 0:
                    gio_bd, gio_kt = shift_times[ca]
                    shifts_to_insert.append((
                        s_nv_id, None, None, cur_d_str, ca,
                        gio_bd, gio_kt, 0, 0,
                        1, 'DA_DUYET', 1, f"{cur_d_str} 06:00:00"
                    ))

    print(f"Tổng số ca làm việc lịch sử chuẩn bị thêm: {len(shifts_to_insert)}")
    batch_size = 300
    added_shifts = 0
    for i in range(0, len(shifts_to_insert), batch_size):
        batch = shifts_to_insert[i:i+batch_size]
        for r in batch:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM lich_lam_viec
                    WHERE (nhan_vien_id = ? OR (? IS NULL AND nhan_vien_id IS NULL))
                      AND (bac_si_id = ? OR (? IS NULL AND bac_si_id IS NULL))
                      AND ngay_lam = ? AND ca_lam = ?
                )
                BEGIN
                    INSERT INTO lich_lam_viec (
                        nhan_vien_id, bac_si_id, phong_kham_id, ngay_lam, ca_lam,
                        gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky,
                        trang_thai, trang_thai_duyet, nguoi_duyet_id, ngay_duyet
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                END
            """, (
                r[0], r[0], r[1], r[1], r[3], r[4],
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12]
            ))
            added_shifts += 1
    print(f"-> Đã nạp thành công ca làm việc 10 tuần về trước ({added_shifts} lượt kiểm tra & nạp).")

    # 5. Thêm dữ liệu ca khám hoàn thành và hóa đơn viện phí cho các tháng 8, 9, 10
    cursor.execute("SELECT id FROM benh_nhan")
    all_pids = [r['id'] for r in cursor.fetchall()]

    diagnoses = [
        ('I10', 'Tăng huyết áp nguyên phát', 'Amlodipine 5mg x 30 viên', 'Uống thuốc đều, hạn chế ăn mặn'),
        ('K29', 'Viêm dạ dày - tá tràng mạn tính', 'Omeprazole 20mg x 28 viên', 'Ăn đúng giờ, tránh cay chua bia rượu'),
        ('E11', 'Đái tháo đường týp 2', 'Metformin 850mg x 60 viên', 'Kiểm tra đường huyết định kỳ, ăn ít tinh bột'),
        ('J00', 'Viêm mũi họng cấp tính', 'Paracetamol 500mg, Kháng histamin', 'Súc họng nước muối, giữ ấm vùng cổ'),
        ('M17', 'Thoái hóa khớp gối nguyên phát', 'Glucosamine 500mg x 60 viên', 'Tập thể dục nhẹ nhàng, tránh mang vác nặng'),
        ('H52', 'Tật khúc xạ mắt', 'Thuốc nhỏ mắt bôi trơn nhân tạo', 'Hạn chế nhìn màn hình liên tục quá 45 phút'),
        ('K05', 'Viêm nướu và bệnh nha chu', 'Nước súc miệng Chlorohexidine', 'Đánh răng đúng cách, vệ sinh kẽ răng')
    ]

    months_data = [
        ('2026-08', date(2026, 8, 25), date(2026, 8, 31)),
        ('2026-09', date(2026, 9, 1), date(2026, 9, 30)),
        ('2026-10', date(2026, 10, 1), date(2026, 10, 21))
    ]

    cursor.execute("SELECT COALESCE(MAX(id), 0) as max_pk FROM phieu_kham")
    pk_seq = int(cursor.fetchone()['max_pk']) + 100
    added_pk = 0
    for m_label, m_start, m_end in months_data:
        cur = m_start
        while cur <= m_end:
            sample_docs = random.sample(doc_list, min(4, len(doc_list)))
            for d in sample_docs:
                pk_seq += 1
                pid = random.choice(all_pids)
                icd_code, icd_diag, treatment, advice = random.choice(diagnoses)
                time_str = f"{cur.isoformat()} {random.choice(['08:45', '10:15', '14:20', '15:40', '18:15'])}:00"
                ma_phieu = f"PK260{pk_seq}"
                room_id = d['phong_kham_chinh_id'] or 1

                cursor.execute("SELECT 1 FROM phieu_kham WHERE ma_phieu = ?", (ma_phieu,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO phieu_kham (
                            ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, ly_do_kham, trieu_chung,
                            chan_doan_icd, huong_dieu_tri, loi_dan, thoi_gian_kham, trang_thai
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, N'Hoàn thành')
                    """, (
                        ma_phieu, pid, d['bs_id'], room_id,
                        icd_diag, 'Mệt mỏi, khó chịu theo cơn', f"{icd_code} - {icd_diag}",
                        treatment, advice, time_str
                    ))
                    cursor.execute("SELECT id FROM phieu_kham WHERE ma_phieu = ?", (ma_phieu,))
                    pk_id = int(cursor.fetchone()['id'])

                    # Tạo hóa đơn viện phí đã thanh toán tương ứng
                    ma_hd = f"HD260{pk_seq}"
                    cursor.execute("""
                        INSERT INTO hoa_don (
                            ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien,
                            trang_thai, hinh_thuc_thanh_toan, nhan_vien_thu, thoi_gian_thanh_toan
                        ) VALUES (?, ?, ?, 150000, 120000, 0, 30000, N'Đã thanh toán', N'Tiền mặt', N'Thu ngân Nguyễn Thị Lan', ?)
                    """, (ma_hd, pid, pk_id, time_str))
                    added_pk += 1
            cur += timedelta(days=2)

    print(f"-> Đã tạo {added_pk} hồ sơ khám bệnh và hóa đơn hoàn thành cho các tháng 8, 9, 10.")

    conn.commit()
    conn.close()
    print("HOÀN TẤT NẠP DỮ LIỆU THÀNH CÔNG!")

if __name__ == '__main__':
    seed_all()
