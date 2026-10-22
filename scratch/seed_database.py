import os
import sys

# Đảm bảo import được các module từ thư mục gốc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
import config

def get_connection():
    cfg = config.SQLSERVER_CONFIG
    servers = [cfg.get('server', 'localhost'), 'localhost', r'.\SQLEXPRESS', '.']
    for srv in servers:
        try:
            if cfg.get('trusted_connection', 'yes').lower() == 'yes':
                conn_str = f"DRIVER={cfg['driver']};SERVER={srv};DATABASE={cfg['database']};Trusted_Connection=yes;"
            else:
                conn_str = f"DRIVER={cfg['driver']};SERVER={srv};DATABASE={cfg['database']};UID={cfg['uid']};PWD={cfg['pwd']};"
            return pyodbc.connect(conn_str, autocommit=False)
        except Exception:
            continue
    raise Exception("Không thể kết nối đến Microsoft SQL Server!")

def seed():
    conn = get_connection()
    cur = conn.cursor()
    print("Ket noi SQL Server thanh cong, bat dau lam sach va nap du lieu moi...")

    # Xoa du lieu theo thu tu khoa ngoai
    tables_to_clean = [
        'chi_tiet_hoa_don', 'hoa_don',
        'chi_tiet_don_thuoc', 'don_thuoc',
        'chi_tiet_chi_dinh', 'phieu_chi_dinh',
        'chi_so_sinh_ton', 'phieu_kham', 'lich_hen', 'lich_lam_viec',
        'phan_hoi', 'hom_thu_gop_y', 'thong_bao', 'lich_su_nhac_nho', 'lich_su_sao_luu',
        'audit_log', 'bai_viet', 'banner',
        'benh_nhan', 'bac_si', 'nhan_vien', 'tai_khoan',
        'thuoc', 'dich_vu', 'phong_kham', 'chuyen_khoa', 'vai_tro'
    ]

    for tbl in tables_to_clean:
        try:
            cur.execute(f"IF OBJECT_ID('{tbl}', 'U') IS NOT NULL DELETE FROM {tbl};")
        except Exception as e:
            print(f"Loi khi xoa {tbl}:", e)

    # Reset identity
    for tbl in tables_to_clean:
        try:
            cur.execute(f"IF OBJECT_ID('{tbl}', 'U') IS NOT NULL DBCC CHECKIDENT ('{tbl}', RESEED, 0);")
        except Exception:
            pass

    # Kiem tra cot da_hoan_thien_ho_so va ton_kho_toi_thieu
    cur.execute("IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tai_khoan') AND name = 'da_hoan_thien_ho_so') ALTER TABLE tai_khoan ADD da_hoan_thien_ho_so BIT DEFAULT 0;")
    cur.execute("IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('thuoc') AND name = 'ton_kho_toi_thieu') ALTER TABLE thuoc ADD ton_kho_toi_thieu INT DEFAULT 20;")

    # 1. vai_tro
    roles = [
        (1, 'ADMIN', 'Quản trị viên', 'Toàn quyền cấu hình và quản trị hệ thống phòng khám'),
        (2, 'LETAN', 'Nhân viên lễ tân / Thu ngân', 'Tiếp đón bệnh nhân, sắp xếp lịch hẹn, thu ngân viện phí'),
        (3, 'BACSI', 'Bác sĩ chuyên khoa', 'Khám bệnh, chẩn đoán, kê đơn thuốc và chỉ định cận lâm sàng'),
        (4, 'DUOCSI', 'Dược sĩ / Thủ kho dược', 'Quản lý kho thuốc, cấp phát thuốc theo toa'),
        (5, 'KTV', 'Kỹ thuật viên cận lâm sàng', 'Thực hiện xét nghiệm, X-quang, chẩn đoán hình ảnh'),
        (6, 'BENHNHAN', 'Bệnh nhân', 'Khách hàng sử dụng cổng thông tin y tế bệnh nhân')
    ]
    cur.execute("SET IDENTITY_INSERT vai_tro ON")
    cur.executemany("INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro, mo_ta) VALUES (?, ?, ?, ?)", roles)
    cur.execute("SET IDENTITY_INSERT vai_tro OFF")

    # 2. chuyen_khoa (7 khoa lam sang + 1 khoa CLS)
    depts = [
        (1, 'KHOA_NOI', 'Khoa Nội Tổng Quát', 'Khám, chẩn đoán và điều trị bệnh lý tim mạch, tiêu hóa, hô hấp, cơ xương khớp, thần kinh', 'fa-stethoscope', 150000.0, 1),
        (2, 'KHOA_NGOAI', 'Khoa Ngoại Tổng Quát', 'Khám và điều trị ngoại khoa, chấn thương chỉnh hình, phẫu thuật tiêu hóa, tiểu phẫu vết thương', 'fa-syringe', 150000.0, 1),
        (3, 'KHOA_NHI', 'Khoa Nhi', 'Chăm sóc và điều trị chuyên sâu bệnh lý trẻ em, tư vấn dinh dưỡng và theo dõi phát triển toàn diện', 'fa-baby', 120000.0, 1),
        (4, 'KHOA_RHM', 'Khoa Răng Hàm Mặt', 'Nha khoa tổng quát, phục hình răng sứ, niềng răng thẩm mỹ, cấy ghép implant, nhổ răng khôn không đau', 'fa-tooth', 150000.0, 1),
        (5, 'KHOA_SAN', 'Khoa Sản - Phụ Khoa', 'Quản lý thai kỳ, siêu âm 4D hình thái học, tầm soát ung thư cổ tử cung và điều trị bệnh phụ khoa', 'fa-person-pregnant', 180000.0, 1),
        (6, 'KHOA_TMH', 'Khoa Tai Mũi Họng', 'Nội soi tai mũi họng dải tần hẹp, điều trị viêm xoang, viêm tai giữa, khàn tiếng và amidan', 'fa-head-side-cough', 150000.0, 1),
        (7, 'KHOA_MAT', 'Khoa Mắt', 'Đo tật khúc xạ cận - viễn - loạn thị, kiểm soát cận thị Ortho-K, điều trị cườm khô, cườm nước và đáy mắt', 'fa-eye', 150000.0, 1),
        (8, 'KHOA_CLS', 'Khoa Cận Lâm Sàng & CĐHA', 'Trung tâm xét nghiệm hóa sinh - huyết học - vi sinh tự động và chẩn đoán hình ảnh kỹ thuật số', 'fa-vial', 100000.0, 1)
    ]
    cur.execute("SET IDENTITY_INSERT chuyen_khoa ON")
    cur.executemany("INSERT INTO chuyen_khoa (id, ma_khoa, ten_khoa, mo_ta, icon, gia_kham_mac_dinh, trang_thai) VALUES (?, ?, ?, ?, ?, ?, ?)", depts)
    cur.execute("SET IDENTITY_INSERT chuyen_khoa OFF")

    # 3. phong_kham: 7 khoa x 5 phong = 35 phong kham + 5 phong CLS = 40 phong
    rooms = []
    r_id = 1
    # 7 khoa lam sang
    dept_room_names = [
        (1, 'Phòng Khám Nội', 'Tầng 1 - Khu A'),
        (2, 'Phòng Khám Ngoại & Tiểu Phẫu', 'Tầng 1 - Khu B'),
        (3, 'Phòng Khám Nhi Khoa', 'Tầng 2 - Khu A'),
        (4, 'Phòng Khám Nha Khoa Kỹ Thuật Cao', 'Tầng 2 - Khu B'),
        (5, 'Phòng Khám Sản Phụ Khoa', 'Tầng 2 - Khu C'),
        (6, 'Phòng Khám Tai Mũi Họng & Nội Soi', 'Tầng 3 - Khu A'),
        (7, 'Phòng Khám Mắt & Khúc Xạ', 'Tầng 3 - Khu B')
    ]
    for k_id, k_title, floor in dept_room_names:
        for idx in range(1, 6):
            rooms.append((r_id, k_id, f"PK{k_id}0{idx}", f"{k_title} {idx}", floor, 1))
            r_id += 1

    # 5 phong CLS cho Khoa 8
    cls_rooms = [
        (r_id, 8, 'CLS_XN01', 'Phòng Xét Nghiệm Huyết Học - Hóa Sinh Tự Động', 'Tầng 1 - Khu C', 1),
        (r_id + 1, 8, 'CLS_XQ01', 'Phòng Chụp X-Quang Kỹ Thuật Số DR', 'Tầng 1 - Khu C', 1),
        (r_id + 2, 8, 'CLS_SA01', 'Phòng Siêu Âm Màu 4D & Doppler Tim Mạch', 'Tầng 1 - Khu C', 1),
        (r_id + 3, 8, 'CLS_TD01', 'Phòng Thăm Dò Chức Năng & Điện Tim ECG', 'Tầng 1 - Khu C', 1),
        (r_id + 4, 8, 'CLS_VS01', 'Phòng Xét Nghiệm Vi Sinh - Nước Tiểu', 'Tầng 1 - Khu C', 1)
    ]
    rooms.extend(cls_rooms)

    cur.execute("SET IDENTITY_INSERT phong_kham ON")
    cur.executemany("INSERT INTO phong_kham (id, chuyen_khoa_id, ma_phong, ten_phong, vi_tri_tang, trang_thai) VALUES (?, ?, ?, ?, ?, ?)", rooms)
    cur.execute("SET IDENTITY_INSERT phong_kham OFF")

    # 4. dich_vu
    services = [
        # Dich vu kham 7 khoa
        (1, 1, 'DV_KHAM_NOI', 'Khám Chuyên Khoa Nội Tổng Quát', 'Khám bệnh', 150000.0, 80, 'Khám và tư vấn toàn diện các bệnh lý nội khoa mạn tính và cấp tính', 1),
        (2, 2, 'DV_KHAM_NGOAI', 'Khám Chuyên Khoa Ngoại Tổng Quát', 'Khám bệnh', 150000.0, 80, 'Khám chấn thương, cơ xương khớp và hội chẩn ngoại khoa', 1),
        (3, 3, 'DV_KHAM_NHI', 'Khám Chuyên Khoa Nhi', 'Khám bệnh', 120000.0, 80, 'Khám sức khỏe trẻ em, dinh dưỡng và tiêm chủng', 1),
        (4, 4, 'DV_KHAM_RHM', 'Khám Nha Khoa Tổng Quát', 'Khám bệnh', 100000.0, 80, 'Khám răng hàm mặt và chụp X-quang răng cận chóp', 1),
        (5, 5, 'DV_KHAM_SAN', 'Khám Sản - Phụ Khoa', 'Khám bệnh', 180000.0, 80, 'Khám thai, tư vấn chăm sóc tiền sản và bệnh phụ khoa', 1),
        (6, 6, 'DV_KHAM_TMH', 'Khám Tai Mũi Họng & Nội Soi', 'Khám bệnh', 150000.0, 80, 'Khám nội soi tầm soát viêm tai, mũi, họng và thanh quản', 1),
        (7, 7, 'DV_KHAM_MAT', 'Khám Mắt & Đo Thị Lực Khúc Xạ', 'Khám bệnh', 150000.0, 80, 'Kiểm tra thị lực bằng máy đo khúc xạ tự động và khám đáy mắt', 1),

        # Dich vu CLS & Thu thuat
        (8, 8, 'DV_XN_MAU_CBC', 'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', 'Xét nghiệm', 150000.0, 80, 'Đánh giá số lượng hồng cầu, bạch cầu, tiểu cầu, tầm soát thiếu máu và nhiễm trùng', 1),
        (9, 8, 'DV_XN_DUONG_HUYET', 'Định lượng Glucose máu (Đường huyết lúc đói)', 'Xét nghiệm', 60000.0, 80, 'Tầm soát và theo dõi bệnh đái tháo đường', 1),
        (10, 8, 'DV_XN_MEN_GAN', 'Đo hoạt độ Men gan (AST / ALT)', 'Xét nghiệm', 100000.0, 80, 'Đánh giá chức năng và tổn thương tế bào gan', 1),
        (11, 8, 'DV_XN_THAN_URE', 'Định lượng Ure & Creatinine máu', 'Xét nghiệm', 100000.0, 80, 'Khảo sát và theo dõi chức năng lọc của cầu thận', 1),
        (12, 8, 'DV_XN_NUOCTIEU', 'Tổng phân tích nước tiểu 10 thông số tự động', 'Xét nghiệm', 80000.0, 80, 'Phát hiện sớm bệnh lý thận, đường tiết niệu và chuyển hóa', 1),
        (13, 8, 'DV_XQUANG_PHOI', 'Chụp X-Quang Ngực thẳng kỹ thuật số (DR)', 'Chẩn đoán hình ảnh', 200000.0, 70, 'Khảo sát nhu mô phổi, phế quản, màng phổi và bóng tim', 1),
        (14, 8, 'DV_XQUANG_KHOP', 'Chụp X-Quang Khớp xương (Gối/Háng/Cột sống)', 'Chẩn đoán hình ảnh', 220000.0, 70, 'Đánh giá thoái hóa khớp, gãy xương và bất thường cấu trúc xương', 1),
        (15, 8, 'DV_SIEU_AM_BUNG', 'Siêu âm Doppler màu ổ bụng tổng quát', 'Chẩn đoán hình ảnh', 250000.0, 50, 'Khảo sát chi tiết gan, mật, tụy, lách, thận, bàng quang và tiền liệt tuyến', 1),
        (16, 8, 'DV_SIEU_AM_THAI', 'Siêu âm Doppler màu thai nhi 4D hình thái học', 'Chẩn đoán hình ảnh', 350000.0, 50, 'Đánh giá sự phát triển và tầm soát dị tật thai nhi', 1),
        (17, 8, 'DV_DIEN_TIM_ECG', 'Đo điện tim đồ 12 chuyển đạo (ECG)', 'Thăm dò chức năng', 120000.0, 70, 'Phát hiện rối loạn nhịp tim, thiếu máu cục bộ cơ tim và phì đại tâm thất', 1),
        (18, 4, 'DV_CAO_VOI_RANG', 'Cạo vôi răng & Đánh bóng hai hàm bằng sóng siêu âm', 'Thủ thuật', 200000.0, 0, 'Loại bỏ mảng bám vi khuẩn, phòng ngừa viêm lợi và nha chu', 1),
        (19, 4, 'DV_NHO_RANG_KHON', 'Tiểu phẫu Nhổ răng khôn mọc lệch / ngầm', 'Thủ thuật', 1200000.0, 0, 'Phẫu thuật nhổ răng khôn bằng máy Piezotome không đau', 1),
        (20, 2, 'DV_TIEU_PHAU_VET_THUONG', 'Xử lý và khâu thẩm mỹ vết thương phần mềm', 'Thủ thuật', 300000.0, 70, 'Sát trùng, cắt lọc mô hoại tử và khâu phục hồi vết thương', 1)
    ]
    cur.execute("SET IDENTITY_INSERT dich_vu ON")
    cur.executemany("INSERT INTO dich_vu (id, chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", services)
    cur.execute("SET IDENTITY_INSERT dich_vu OFF")

    # 5. thuoc (co cac thuoc ton kho it de test canh bao: so_luong_ton <= ton_kho_toi_thieu)
    medicines = [
        # Thuoc ton kho it de test tinh nang canh bao
        (1, 'TH_CANH_BAO_1', 'Azithromycin 500mg (Kháng sinh)', 'Azithromycin dihydrat', '500mg', 'Viên', 18000.0, 8, 20, 'Pfizer', 'Mỹ', 'Kháng sinh phổ rộng: Uống 1 viên duy nhất/ngày trước ăn 1h', 1),
        (2, 'TH_CANH_BAO_2', 'Cefpodoxime 200mg', 'Cefpodoxime proxetil', '200mg', 'Viên', 22000.0, 12, 20, 'Sanofi', 'Pháp', 'Kháng sinh hô hấp: Uống 1 viên x 2 lần/ngày sau bữa ăn', 1),
        (3, 'TH_CANH_BAO_3', 'Ventolin Inhaler 100mcg (Xịt hen)', 'Salbutamol sulfat', '100mcg/liều', 'Chai', 115000.0, 5, 15, 'GSK', 'Anh', 'Cắt cơn hen phế quản: Xịt 1-2 nhát khi khó thở', 1),
        (4, 'TH_CANH_BAO_4', 'Nexium Mups 40mg', 'Esomeprazole magnesium', '40mg', 'Viên', 24000.0, 14, 25, 'AstraZeneca', 'Thụy Điển', 'Loét dạ dày tá tràng nặng: Uống 1 viên trước ăn sáng', 1),
        (5, 'TH_CANH_BAO_5', 'Insulin Mixtard 30 Penfill', 'Insulin Human', '100IU/ml 3ml', 'Bút', 165000.0, 6, 20, 'Novo Nordisk', 'Đan Mạch', 'Hạ đường huyết: Tiêm dưới da theo hướng dẫn của bác sĩ', 1),

        # Cac thuoc pho bien ton kho doi dao
        (6, 'TH_PARACETAMOL', 'Paracetamol 500mg Hậu Giang', 'Paracetamol', '500mg', 'Viên', 2000.0, 5000, 50, 'Dược Hậu Giang', 'Việt Nam', 'Giảm đau, hạ sốt: Uống 1-2 viên mỗi 4-6h khi sốt trên 38.5°C', 1),
        (7, 'TH_AMOXICILLIN', 'Amoxicillin 500mg', 'Amoxicillin trihydrat', '500mg', 'Viên', 3000.0, 2500, 50, 'Imexpharm', 'Việt Nam', 'Kháng sinh nhiễm khuẩn đường hô hấp, tiết niệu: Uống 1 viên x 3 lần/ngày', 1),
        (8, 'TH_AUGMENTIN', 'Augmentin 1g (Amoxicillin/Clavulanate)', 'Amoxicillin + Acid clavulanic', '1000mg', 'Viên', 25000.0, 1500, 30, 'GSK', 'Anh', 'Kháng sinh thế hệ mới: Uống 1 viên vào đầu bữa ăn, ngày 2 lần', 1),
        (9, 'TH_IBUPROFEN', 'Ibuprofen 400mg Stada', 'Ibuprofen', '400mg', 'Viên', 3500.0, 3000, 40, 'Stada', 'Việt Nam', 'Kháng viêm giảm đau cơ xương khớp: Uống 1 viên sau ăn no', 1),
        (10, 'TH_LORATADIN', 'Loratadin 10mg Pymepharco', 'Loratadin', '10mg', 'Viên', 4000.0, 2000, 30, 'Pymepharco', 'Việt Nam', 'Chống dị ứng, viêm mũi dị ứng, mề đay: Uống 1 viên vào buổi tối', 1),
        (11, 'TH_ESOMEPRAZOLE', 'Esomeprazole 20mg Stada', 'Esomeprazole', '20mg', 'Viên', 8000.0, 2800, 30, 'Stada', 'Việt Nam', 'Ức chế tiết acid dạ dày: Uống 1 viên trước bữa ăn sáng 30 phút', 1),
        (12, 'TH_PHOSPHALUGEL', 'Phosphalugel 20g (Thuốc dạ dày chữ P)', 'Aluminium phosphate', '20g', 'Gói', 5500.0, 3500, 50, 'Boehringer Ingelheim', 'Pháp', 'Trung hòa acid dịch vị: Uống 1 gói khi đau hoặc sau ăn 1-2 giờ', 1),
        (13, 'TH_ENTEROGERMINA', 'Men vi sinh Enterogermina 2 tỷ', 'Bacillus clausii', '2 tỷ bào tử/5ml', 'Ống', 9500.0, 1800, 40, 'Sanofi', 'Ý', 'Cân bằng hệ vi sinh đường ruột: Uống 1-2 ống/ngày sau bữa ăn', 1),
        (14, 'TH_ORESOL', 'Oresol 245 bù nước điện giải', 'Glucose, Natri clorid, Kali clorid', '245 mOsm/L', 'Gói', 5000.0, 4000, 50, 'Traphaco', 'Việt Nam', 'Pha chính xác 1 gói với 200ml nước đun sôi để nguội', 1),
        (15, 'TH_PROSPAN', 'Siro ho thảo dược Prospan 100ml', 'Cao khô lá thường xuân', '100ml', 'Chai', 78000.0, 600, 20, 'Engelhard', 'Đức', 'Trị ho viêm phế quản: Uống 5ml x 3 lần/ngày', 1),
        (16, 'TH_AMLODIPINE', 'Amlodipine 5mg', 'Amlodipine besylate', '5mg', 'Viên', 5000.0, 2200, 30, 'Dược Hậu Giang', 'Việt Nam', 'Điều trị tăng huyết áp và đau thắt ngực: Uống 1 viên mỗi sáng', 1),
        (17, 'TH_METFORMIN', 'Metformin 850mg (Glucophage)', 'Metformin hydroclorid', '850mg', 'Viên', 6000.0, 1900, 30, 'Merck', 'Đức', 'Hạ đường huyết đái tháo đường type 2: Uống 1 viên cùng bữa ăn', 1),
        (18, 'TH_ATORVASTATIN', 'Atorvastatin 20mg (Lipitor)', 'Atorvastatin calci', '20mg', 'Viên', 16000.0, 1400, 25, 'Pfizer', 'Mỹ', 'Hạ cholesterol máu: Uống 1 viên vào buổi tối trước khi đi ngủ', 1),
        (19, 'TH_BERBERIN', 'Berberin 100mg Dược Hà Tĩnh', 'Berberin clorid', '100mg', 'Viên', 1000.0, 5000, 50, 'Hadiphar', 'Việt Nam', 'Nhiễm khuẩn đường ruột, tiêu chảy: Uống 2-4 viên/lần sau ăn', 1),
        (20, 'TH_NACL_09', 'Nước muối sinh lý NaCl 0.9% 500ml', 'Natri Clorid 0.9%', '500ml', 'Chai', 10000.0, 1200, 30, 'Pharmedic', 'Việt Nam', 'Súc họng, rửa mũi hoặc sát khuẩn vết thương ngoài da', 1)
    ]
    cur.execute("SET IDENTITY_INSERT thuoc ON")
    cur.executemany("INSERT INTO thuoc (id, ma_thuoc, ten_thuoc, hoat_chat, ham_luong, don_vi_tinh, don_gia, so_luong_ton, ton_kho_toi_thieu, hang_san_xuat, nuoc_san_xuat, huong_dan_su_dung, trang_thai) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", medicines)
    cur.execute("SET IDENTITY_INSERT thuoc OFF")

    # Mật khẩu băm chuẩn
    pwd_admin = generate_password_hash('admin123')
    pwd_staff = generate_password_hash('Password@123')
    pwd_patient = generate_password_hash('123456')

    # Danh sách tài khoản
    accounts = []
    staff_records = []
    doctor_records = []
    patient_records = []

    # 1 Admin
    accounts.append((1, 1, 'admin', pwd_admin, 'admin@h2tcare.vn', '0999999999', 1, 1))
    staff_records.append((1, 1, 'NV001', 'Admin Quản Trị Hệ Thống', 1, '1985-01-01', '0999999999', 'admin@h2tcare.vn', '079085000001', '140 Lê Trọng Tấn, Tây Thạnh, Tân Phú, TP.HCM', 'Giám đốc Điều hành & Quản trị Hệ thống', 1))

    # 5 Lễ tân: letan_1 .. letan_5 (vai_tro_id = 2)
    letan_names = [
        ('letan_1', 'Nguyễn Thị Lan', 0, '1995-04-12', '0908111221', 'lan.letan@h2tcare.vn', '079195000101', 'Lễ tân trưởng - Quầy tiếp đón Tầng 1'),
        ('letan_2', 'Trần Thu Huyền', 0, '1997-08-20', '0908111222', 'huyen.letan@h2tcare.vn', '079197000102', 'Tiếp đón & Điều phối lịch hẹn - Quầy A'),
        ('letan_3', 'Lê Phương Thảo', 0, '1996-11-05', '0908111223', 'thao.letan@h2tcare.vn', '079196000103', 'Thu ngân viện phí & Tiếp nhận BHYT - Quầy B'),
        ('letan_4', 'Phạm Ngọc Bích', 0, '1998-02-14', '0908111224', 'bich.letan@h2tcare.vn', '079198000104', 'Chăm sóc khách hàng & Hướng dẫn khám'),
        ('letan_5', 'Đỗ Thu Hà', 0, '1994-06-30', '0908111225', 'ha.letan@h2tcare.vn', '079194000105', 'Lễ tân ca trực & Điều phối bệnh nhân cấp cứu')
    ]
    u_id = 2
    s_id = 2
    for uname, hten, gt, nsinh, phone, email, cccd, chucvu in letan_names:
        accounts.append((u_id, 2, uname, pwd_staff, email, phone, 1, 1))
        staff_records.append((s_id, u_id, f"NV_LT0{u_id - 1}", hten, gt, nsinh, phone, email, cccd, 'TP. Hồ Chí Minh', chucvu, 1))
        u_id += 1
        s_id += 1

    # 5 Dược sĩ: duocsi_1 .. duocsi_5 (vai_tro_id = 4)
    duocsi_names = [
        ('duocsi_1', 'Dược sĩ Phạm Hoàng Minh', 1, '1992-03-15', '0908222331', 'minh.duocsi@h2tcare.vn', '079192000201', 'Dược sĩ trưởng - Trưởng kho Dược chính'),
        ('duocsi_2', 'Dược sĩ Nguyễn Thị Kim Oanh', 0, '1994-07-19', '0908222332', 'oanh.duocsi@h2tcare.vn', '079194000202', 'Dược sĩ cấp phát thuốc ngoại trú & BHYT'),
        ('duocsi_3', 'Dược sĩ Vũ Đình Trọng', 1, '1990-10-10', '0908222333', 'trong.duocsi@h2tcare.vn', '079190000203', 'Dược sĩ quản lý tồn kho & Kiểm kê định kỳ'),
        ('duocsi_4', 'Dược sĩ Hoàng Thanh Trúc', 0, '1995-12-25', '0908222334', 'truc.duocsi@h2tcare.vn', '079195000204', 'Dược sĩ tư vấn sử dụng thuốc và tương tác thuốc'),
        ('duocsi_5', 'Dược sĩ Trần Văn Phúc', 1, '1993-05-08', '0908222335', 'phuc.duocsi@h2tcare.vn', '079193000205', 'Dược sĩ phụ trách nhà thuốc bệnh viện')
    ]
    for uname, hten, gt, nsinh, phone, email, cccd, chucvu in duocsi_names:
        accounts.append((u_id, 4, uname, pwd_staff, email, phone, 1, 1))
        staff_records.append((s_id, u_id, f"NV_DS0{u_id - 6}", hten, gt, nsinh, phone, email, cccd, 'TP. Hồ Chí Minh', chucvu, 1))
        u_id += 1
        s_id += 1

    # 5 Kỹ thuật viên CLS: ktv_1 .. ktv_5 (vai_tro_id = 5)
    ktv_names = [
        ('ktv_1', 'KTV. Võ Anh Đức', 1, '1993-07-22', '0908333441', 'duc.ktv@h2tcare.vn', '079193000301', 'KTV Trưởng Xét nghiệm Huyết học - Hóa sinh'),
        ('ktv_2', 'KTV. Hoàng Văn Cường', 1, '1991-09-18', '0908333442', 'cuong.ktv@h2tcare.vn', '079191000302', 'KTV Chẩn đoán hình ảnh - Chụp X-Quang kỹ thuật số'),
        ('ktv_3', 'KTV. Đặng Mỹ Linh', 0, '1996-03-30', '0908333443', 'linh.ktv@h2tcare.vn', '079196000303', 'KTV Siêu âm tổng quát & Doppler mạch máu'),
        ('ktv_4', 'KTV. Bùi Quốc Tuấn', 1, '1994-11-12', '0908333444', 'tuan.ktv@h2tcare.vn', '079194000304', 'KTV Thăm dò chức năng & Điện tâm đồ ECG'),
        ('ktv_5', 'KTV. Lê Thùy Trang', 0, '1997-01-25', '0908333445', 'trang.ktv@h2tcare.vn', '079197000305', 'KTV Xét nghiệm Vi sinh - Nước tiểu')
    ]
    for uname, hten, gt, nsinh, phone, email, cccd, chucvu in ktv_names:
        accounts.append((u_id, 5, uname, pwd_staff, email, phone, 1, 1))
        staff_records.append((s_id, u_id, f"NV_KTV0{u_id - 11}", hten, gt, nsinh, phone, email, cccd, 'TP. Hồ Chí Minh', chucvu, 1))
        u_id += 1
        s_id += 1

    # 35 Bác sĩ chuyên khoa (7 khoa x 5 bac si)
    # Mapping khoa: 1: Noi, 2: Ngoai, 3: Nhi, 4: RHM, 5: San, 6: TMH, 7: Mat
    doc_info_by_dept = {
        1: [ # Noi
            ('bs_noi_1', 'BS. Trần Minh Quân', 1, '1985-06-15', '0912111001', 'bs_noi_1@h2tcare.vn', '079085001001', 'ThS.BS', 150000.0, '15 năm kinh nghiệm chẩn đoán và điều trị bệnh lý tim mạch, tăng huyết áp và nội tiết tại BV Chợ Rẫy.'),
            ('bs_noi_2', 'BS. Phạm Anh Tuấn', 1, '1982-12-08', '0912111002', 'bs_noi_2@h2tcare.vn', '079082001002', 'BSCKII', 180000.0, '18 năm kinh nghiệm điều trị bệnh tim thiếu máu cục bộ, suy tim mạn và rối loạn lipid máu phức tạp.'),
            ('bs_noi_3', 'BS. Nguyễn Thu Trang', 0, '1989-03-24', '0912111003', 'bs_noi_3@h2tcare.vn', '079089001003', 'ThS.BS', 150000.0, '10 năm chuyên sâu bệnh lý tiêu hóa, trào ngược dạ dày thực quản, viêm loét HP và gan nhiễm mỡ.'),
            ('bs_noi_4', 'BS. Vũ Quốc Hưng', 1, '1988-11-17', '0912111004', 'bs_noi_4@h2tcare.vn', '079088001004', 'BSCKI', 150000.0, '9 năm kinh nghiệm điều trị viêm phế quản, hen suyễn, COPD và các bệnh lý dị ứng - miễn dịch.'),
            ('bs_noi_5', 'BS. Lê Hoài An', 1, '1987-08-05', '0912111005', 'bs_noi_5@h2tcare.vn', '079087001005', 'ThS.BS', 150000.0, '11 năm kinh nghiệm chuyên khoa Cơ xương khớp, thoái hóa khớp gối, viêm khớp dạng thấp và Gout.')
        ],
        2: [ # Ngoai
            ('bs_ngoai_1', 'BS. Nguyễn Hoàng Nam', 1, '1980-03-25', '0912222001', 'bs_ngoai_1@h2tcare.vn', '079080002001', 'BSCKII', 180000.0, '17 năm phẫu thuật ngoại khoa tổng quát, xử lý chấn thương chỉnh hình và tiểu phẫu u lành da.'),
            ('bs_ngoai_2', 'BS. Phan Thanh Phong', 1, '1984-07-12', '0912222002', 'bs_ngoai_2@h2tcare.vn', '079084002002', 'ThS.BS', 160000.0, '13 năm kinh nghiệm phẫu thuật thoát vị đĩa đệm, chấn thương thể thao và nội soi khớp gối.'),
            ('bs_ngoai_3', 'BS. Đinh Văn Hùng', 1, '1989-05-19', '0912222003', 'bs_ngoai_3@h2tcare.vn', '079089002003', 'BSCKI', 150000.0, '9 năm chuyên tiểu phẫu bướu bã, u mỡ, móng chọc thịt và khâu thẩm mỹ vết thương phức tạp.'),
            ('bs_ngoai_4', 'BS. Hoàng Đức Lâm', 1, '1986-10-30', '0912222004', 'bs_ngoai_4@h2tcare.vn', '079086002004', 'ThS.BS', 150000.0, '11 năm kinh nghiệm khám và điều trị sỏi tiết niệu, u xơ tiền liệt tuyến và nam học ngoại khoa.'),
            ('bs_ngoai_5', 'BS. Trịnh Văn Long', 1, '1990-01-14', '0912222005', 'bs_ngoai_5@h2tcare.vn', '079090002005', 'BSCKI', 150000.0, '8 năm kinh nghiệm khám bệnh lý hậu môn trực tràng, trĩ nội, trĩ ngoại và rò hậu môn.')
        ],
        3: [ # Nhi
            ('bs_nhi_1', 'BS. Lê Thị Mai', 0, '1989-09-20', '0912333001', 'bs_nhi_1@h2tcare.vn', '079089003001', 'BSCKI', 150000.0, '10 năm công tác tại BV Nhi Đồng, chuyên sâu hô hấp, tiêu hóa và nhiễm khuẩn trẻ em.'),
            ('bs_nhi_2', 'BS. Dương Diệu Linh', 0, '1991-04-18', '0912333002', 'bs_nhi_2@h2tcare.vn', '079091003002', 'ThS.BS', 140000.0, '8 năm chuyên khoa Dị ứng - Miễn dịch nhi khoa, hen phế quản trẻ em và viêm da cơ địa.'),
            ('bs_nhi_3', 'BS. Ngô Đình Quân', 1, '1987-11-23', '0912333003', 'bs_nhi_3@h2tcare.vn', '079087003003', 'BSCKI', 140000.0, '11 năm kinh nghiệm chăm sóc trẻ sơ sinh, theo dõi vàng da, rối loạn tiêu hóa và biếng ăn.'),
            ('bs_nhi_4', 'BS. Phạm Thúy Hằng', 0, '1992-06-09', '0912333004', 'bs_nhi_4@h2tcare.vn', '079092003004', 'ThS.BS', 130000.0, '7 năm tư vấn dinh dưỡng trẻ nhỏ, tầm soát còi xương, chậm lớn và phát triển thể chất.'),
            ('bs_nhi_5', 'BS. Đỗ Tuấn Nghĩa', 1, '1983-02-15', '0912333005', 'bs_nhi_5@h2tcare.vn', '079083003005', 'BSCKII', 160000.0, '16 năm chuyên gia Nhi tổng quát, tầm soát tim bẩm sinh và xử trí co giật do sốt cao.')
        ],
        4: [ # RHM
            ('bs_rhm_1', 'BS. Hoàng Đức Duy', 1, '1988-09-20', '0912444001', 'bs_rhm_1@h2tcare.vn', '079088004001', 'ThS.BS', 160000.0, 'Tốt nghiệp ThS ĐHYD TP.HCM, chuyên gia phục hình răng sứ, chỉnh nha và cấy ghép Implant.'),
            ('bs_rhm_2', 'BS. Đoàn Minh Khang', 1, '1986-04-11', '0912444002', 'bs_rhm_2@h2tcare.vn', '079086004002', 'BSCKI', 150000.0, '12 năm kinh nghiệm chỉnh nha mắc cài kim loại, sứ và niềng răng trong suốt Invisalign.'),
            ('bs_rhm_3', 'BS. Vũ Hồng Loan', 0, '1990-12-03', '0912444003', 'bs_rhm_3@h2tcare.vn', '079090004003', 'ThS.BS', 150000.0, '9 năm điều trị bệnh lý nha chu, tụt lợi, phẫu thuật cười hở lợi và làm trắng răng laser.'),
            ('bs_rhm_4', 'BS. Mai Văn Trọng', 1, '1989-08-27', '0912444004', 'bs_rhm_4@h2tcare.vn', '079089004004', 'BSCKI', 150000.0, '10 năm chuyên tiểu phẫu răng khôn mọc lệch ngầm bằng sóng siêu âm không sưng đau.'),
            ('bs_rhm_5', 'BS. Nguyễn Bích Thủy', 0, '1993-05-16', '0912444005', 'bs_rhm_5@h2tcare.vn', '079093004005', 'ThS.BS', 140000.0, '8 năm chuyên khoa Nha khoa Trẻ em, tiền chỉnh nha và điều trị tủy răng sữa nhẹ nhàng.')
        ],
        5: [ # San
            ('bs_san_1', 'BS. Đặng Thu Hương', 0, '1985-05-12', '0912555001', 'bs_san_1@h2tcare.vn', '079085005001', 'BSCKI', 180000.0, '14 năm kinh nghiệm quản lý thai kỳ nguy cơ cao, tầm soát tiền sản giật và dị tật thai nhi.'),
            ('bs_san_2', 'BS. Trần Kiều Nga', 0, '1981-10-29', '0912555002', 'bs_san_2@h2tcare.vn', '079081005002', 'BSCKII', 200000.0, '19 năm công tác tại BV Từ Dũ, chuyên sâu phẫu thuật nội soi phụ khoa và tầm soát ung thư.'),
            ('bs_san_3', 'BS. Nguyễn Thanh Huyền', 0, '1988-02-14', '0912555003', 'bs_san_3@h2tcare.vn', '079088005003', 'ThS.BS', 170000.0, '11 năm tư vấn hiếm muộn vô sinh, siêu âm canh noãn và điều trị hội chứng buồng trứng đa nang.'),
            ('bs_san_4', 'BS. Bùi Thị Minh Tâm', 0, '1990-07-07', '0912555004', 'bs_san_4@h2tcare.vn', '079090005004', 'BSCKI', 160000.0, '9 năm chuyên gia Siêu âm hình thái học thai 4D, đo độ mờ da gáy và kiểm tra doppler rốn.'),
            ('bs_san_5', 'BS. Lê Tuyết Lan', 0, '1992-09-18', '0912555005', 'bs_san_5@h2tcare.vn', '079092005005', 'ThS.BS', 150000.0, '8 năm điều trị viêm nhiễm âm đạo mạn tính, lộ tuyến cổ tử cung và tư vấn tiền hôn nhân.')
        ],
        6: [ # TMH
            ('bs_tmh_1', 'BS. Võ Thanh Bình', 1, '1984-01-20', '0912666001', 'bs_tmh_1@h2tcare.vn', '079084006001', 'BSCKII', 170000.0, '15 năm chuyên khoa Tai Mũi Họng, nội soi ống mềm NBI phát hiện sớm ung thư vòm họng.'),
            ('bs_tmh_2', 'BS. Hoàng Quốc Tuấn', 1, '1987-06-14', '0912666002', 'bs_tmh_2@h2tcare.vn', '079087006002', 'ThS.BS', 150000.0, '11 năm điều trị viêm xoang mũi mạn tính, polyp mũi và phẫu thuật nội soi xoang FESS.'),
            ('bs_tmh_3', 'BS. Nguyễn Thị Thục Anh', 0, '1989-12-05', '0912666003', 'bs_tmh_3@h2tcare.vn', '079089006003', 'BSCKI', 150000.0, '10 năm chuyên khoa Tai thính học, đo thính lực đồ, điều trị viêm tai giữa và ù tai kéo dài.'),
            ('bs_tmh_4', 'BS. Trương Hoài Nam', 1, '1991-08-30', '0912666004', 'bs_tmh_4@h2tcare.vn', '079091006004', 'ThS.BS', 140000.0, '8 năm điều trị khàn tiếng, hạt xơ dây thanh, trào ngược họng thanh quản LPR.'),
            ('bs_tmh_5', 'BS. Chu Đức Cảnh', 1, '1986-03-22', '0912666005', 'bs_tmh_5@h2tcare.vn', '079086006005', 'BSCKI', 150000.0, '12 năm chuyên Tai Mũi Họng Nhi khoa, nạo VA và cắt Amidan bằng công nghệ dao Coblator.')
        ],
        7: [ # Mat
            ('bs_mat_1', 'BS. Đỗ Viết Thắng', 1, '1982-05-18', '0912777001', 'bs_mat_1@h2tcare.vn', '079082007001', 'BSCKII', 180000.0, '18 năm phẫu thuật Phaco điều trị đục thủy tinh thể và đặt kính nội nhãn đa tiêu sắc.'),
            ('bs_mat_2', 'BS. Lê Khánh Linh', 0, '1990-10-09', '0912777002', 'bs_mat_2@h2tcare.vn', '079090007002', 'ThS.BS', 150000.0, '10 năm chuyên gia Tật khúc xạ cận - loạn thị học đường, fitting kính áp tròng Ortho-K.'),
            ('bs_mat_3', 'BS. Nguyễn Hữu Đạt', 1, '1986-07-26', '0912777003', 'bs_mat_3@h2tcare.vn', '079086007003', 'BSCKI', 150000.0, '12 năm khám và điều trị bệnh võng mạc đái tháo đường, thoái hóa hoàng điểm tuổi già.'),
            ('bs_mat_4', 'BS. Phạm Hồng Nhung', 0, '1992-02-17', '0912777004', 'bs_mat_4@h2tcare.vn', '079092007004', 'ThS.BS', 140000.0, '8 năm điều trị Glaucoma (cườm nước), kiểm soát nhãn áp và theo dõi thị trường mắt.'),
            ('bs_mat_5', 'BS. Vũ Văn Hải', 1, '1988-12-11', '0912777005', 'bs_mat_5@h2tcare.vn', '079088007005', 'BSCKI', 150000.0, '11 năm kinh nghiệm khám viêm loét giác mạc, khô mắt mạn tính và mộng thịt tái phát.')
        ]
    }

    b_id = 1
    for dept_id in range(1, 8):
        doc_list = doc_info_by_dept[dept_id]
        for idx, (uname, hten, gt, nsinh, phone, email, cccd, hocvi, giakham, exp) in enumerate(doc_list):
            accounts.append((u_id, 3, uname, pwd_staff, email, phone, 1, 1))
            staff_records.append((s_id, u_id, f"BS{str(b_id).zfill(3)}", hten, gt, nsinh, phone, email, cccd, 'TP. Hồ Chí Minh', f"Bác sĩ chuyên khoa - {depts[dept_id - 1][2]}", 1))
            # Phong kham tuong ung: 5 phong kham moi khoa
            room_id = (dept_id - 1) * 5 + (idx + 1)
            doctor_records.append((b_id, s_id, dept_id, room_id, hocvi, exp, 'default_doctor.png', giakham, 'Đang làm việc'))
            u_id += 1
            s_id += 1
            b_id += 1

    # 10 Bệnh nhân chuẩn (0901234561 .. 0901234570)
    p_info = [
        ('0901234561', 'Hoàng Bảo Nam', '1990-05-12', 'Nam', '0901234561', 'baonam@gmail.com', '079090000001', 'GD4797931100001', '120 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP.HCM', 'O+', 'ABO: O, Rh: Dương (Rh+)', 'Không có', 'Đau dạ dày nhẹ, trào ngược thực quản', 'Không', 'Hoàng Văn Bảy', '0901999881', 'Bố', '75 lần/phút', '36.8 °C', '120/80 mmHg', '99 %', '18 lần/phút', '170 cm', '65 kg', '22.5 (Bình thường)'),
        ('0901234562', 'Trần Thị Thu Hà', '1995-04-18', 'Nữ', '0901234562', 'thuha.tran95@gmail.com', '079195000301', 'DN4791950003011', '36 Tân Hương, P. Tân Quý, Q. Tân Phú, TP.HCM', 'A+', 'ABO: A, Rh: Dương (Rh+)', 'Aspirin, Tôm cua hải sản có vỏ', 'Viêm xoang mũi dị ứng mạn tính, Viêm loét dạ dày tá tràng', 'Mẹ bị đái tháo đường type 2', 'Trần Văn Cường', '0901999882', 'Bố đẻ', '80 lần/phút', '37.0 °C', '110/70 mmHg', '98 %', '19 lần/phút', '158 cm', '48 kg', '19.2 (Bình thường)'),
        ('0901234563', 'Nguyễn Văn Hùng', '1986-10-25', 'Nam', '0901234563', 'hung.nguyen86@gmail.com', '079186000302', 'GD479860003022', '128 Cộng Hòa, Phường 12, Quận Tân Bình, TP.HCM', 'O+', 'ABO: O, Rh: Dương (Rh+)', 'Không ghi nhận dị ứng thuốc', 'Tăng huyết áp độ 1, Rối loạn mỡ máu (Dyslipidemia)', 'Bố bị tai biến mạch máu não', 'Lê Thị Mai', '0901999883', 'Vợ', '85 lần/phút', '36.6 °C', '135/85 mmHg', '98 %', '18 lần/phút', '172 cm', '74 kg', '25.0 (Tiền béo phì)'),
        ('0901234564', 'Lê Minh Anh', '2001-08-14', 'Nữ', '0901234564', 'minhanh.le01@gmail.com', '079201000303', 'SV4792010003033', '45/8 Lê Trọng Tấn, P. Tây Thạnh, Q. Tân Phú, TP.HCM', 'B+', 'ABO: B, Rh: Dương (Rh+)', 'Kháng sinh Penicillin (phù Quincke)', 'Viêm da cơ địa, Thiếu máu thiếu sắt nhẹ', 'Không có bệnh lý di truyền', 'Lê Quốc Bảo', '0901999884', 'Anh trai', '72 lần/phút', '36.7 °C', '115/75 mmHg', '99 %', '17 lần/phút', '162 cm', '50 kg', '19.0 (Bình thường)'),
        ('0901234565', 'Phạm Đức Trọng', '1978-02-09', 'Nam', '0901234565', 'trong.pham78@gmail.com', '079178000305', 'GD4791780003055', '84 Sư Vạn Hạnh, Phường 12, Quận 10, TP.HCM', 'AB+', 'ABO: AB, Rh: Dương (Rh+)', 'Paracetamol (nổi mày đay nhẹ)', 'Thoái hóa đốt sống cổ C5-C6, Đau thần kinh tọa', 'Gia đình có người bị thoái hóa khớp', 'Nguyễn Thị Bích Lan', '0901999885', 'Vợ', '76 lần/phút', '36.8 °C', '125/80 mmHg', '99 %', '18 lần/phút', '168 cm', '68 kg', '24.1 (Bình thường)'),
        ('0901234566', 'Đỗ Thị Bích Ngân', '1993-11-30', 'Nữ', '0901234566', 'ngan.dobich@gmail.com', '079193000306', 'DN4791930003066', '215 Kinh Dương Vương, Phường 12, Quận 6, TP.HCM', 'A+', 'ABO: A, Rh: Dương (Rh+)', 'Không ghi nhận', 'Viêm amidan hốc mủ mạn, Trào ngược LPR', 'Không có tiền sử đặc biệt', 'Đỗ Thành Vinh', '0901999886', 'Em trai', '74 lần/phút', '36.5 °C', '110/70 mmHg', '99 %', '18 lần/phút', '160 cm', '52 kg', '20.3 (Bình thường)'),
        ('0901234567', 'Vũ Đình Khang', '1968-06-17', 'Nam', '0901234567', 'khang.vudinh@gmail.com', '079168000307', 'HT4791680003077', '92 Cách Mạng Tháng Tám, Phường 6, Quận 3, TP.HCM', 'O+', 'ABO: O, Rh: Dương (Rh+)', 'Không dị ứng thuốc', 'Đái tháo đường type 2, Gan nhiễm mỡ độ 2, Men gan cao', 'Bố mẹ đều mắc đái tháo đường', 'Vũ Đình Hoàng', '0901999887', 'Con trai', '82 lần/phút', '36.7 °C', '130/80 mmHg', '97 %', '19 lần/phút', '165 cm', '70 kg', '25.7 (Tiền béo phì)'),
        ('0901234568', 'Bùi Tuyết Mai', '1988-09-05', 'Nữ', '0901234568', 'tuyetmai.bui@gmail.com', '079188000308', 'DN4791880003088', '56 Phan Xích Long, Phường 2, Quận Phú Nhuận, TP.HCM', 'B+', 'ABO: B, Rh: Dương (Rh+)', 'Dị ứng phấn hoa và lông động vật', 'Rối loạn tiền đình, Thiếu máu não thoáng qua', 'Mẹ bị đau nửa đầu Migraine', 'Trần Văn Hoàng', '0901999888', 'Chồng', '78 lần/phút', '36.9 °C', '105/65 mmHg', '99 %', '18 lần/phút', '156 cm', '46 kg', '18.9 (Bình thường)'),
        ('0901234569', 'Đặng Quốc Bảo', '2004-12-22', 'Nam', '0901234569', 'quocbao.dang04@gmail.com', '079204000309', 'SV4792040003099', '18 Quang Trung, Phường 10, Quận Gò Vấp, TP.HCM', 'O-', 'ABO: O, Rh: Âm (Rh- cực hiếm)', 'Không có', 'Cận thị khúc xạ 3.5 độ hai mắt, Viêm lợi nhẹ', 'Không', 'Nguyễn Thị Kim Loan', '0901999889', 'Mẹ', '70 lần/phút', '36.6 °C', '118/75 mmHg', '100 %', '16 lần/phút', '175 cm', '62 kg', '20.2 (Bình thường)'),
        ('0901234570', 'Phan Mỹ Duyên', '1997-03-14', 'Nữ', '0901234570', 'myduyen.phan97@gmail.com', '079197000310', 'DN4791970003100', '78 Gò Dầu, Phường Tân Quý, Quận Tân Phú, TP.HCM', 'AB-', 'ABO: AB, Rh: Âm (Rh- hiếm)', 'Kháng sinh nhóm Sulfamid', 'Hội chứng ruột kích thích (IBS), Viêm bàng quang', 'Không có bệnh lý gia đình', 'Phan Văn Đức', '0901999890', 'Bố', '76 lần/phút', '36.8 °C', '110/70 mmHg', '99 %', '18 lần/phút', '163 cm', '51 kg', '19.2 (Bình thường)')
    ]

    pat_id = 1
    vitals = []
    for uname, hten, nsinh, gt, phone, email, cccd, bhyt, dc, nm, gcnm, diung, tsb, tsgd, ntht, ntsdt, ntqh, mach, nd, ha, spo2, nt, cc, cn, bmi in p_info:
        accounts.append((u_id, 6, uname, pwd_patient, email, phone, 1, 1)) # da_hoan_thien_ho_so = 1
        patient_records.append((pat_id, u_id, f"BN{str(pat_id).zfill(4)}", hten, nsinh, gt, phone, email, cccd, bhyt, dc, nm, gcnm, None, diung, tsb, tsgd, ntht, ntsdt, ntqh, 1))
        vitals.append((pat_id, pat_id, mach, nd, ha, spo2, nt, cc, cn, bmi))
        u_id += 1
        pat_id += 1

    # Insert tai_khoan
    cur.execute("SET IDENTITY_INSERT tai_khoan ON")
    cur.executemany("INSERT INTO tai_khoan (id, vai_tro_id, username, password, email, sdt, trang_thai, da_hoan_thien_ho_so) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", accounts)
    cur.execute("SET IDENTITY_INSERT tai_khoan OFF")

    # Insert nhan_vien
    cur.execute("SET IDENTITY_INSERT nhan_vien ON")
    cur.executemany("INSERT INTO nhan_vien (id, tai_khoan_id, ma_nhan_vien, ho_ten, gioi_tinh, ngay_sinh, sdt, email, cccd, dia_chi, chuc_vu, trang_thai) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", staff_records)
    cur.execute("SET IDENTITY_INSERT nhan_vien OFF")

    # Insert bac_si
    cur.execute("SET IDENTITY_INSERT bac_si ON")
    cur.executemany("INSERT INTO bac_si (id, nhan_vien_id, chuyen_khoa_id, phong_kham_chinh_id, hoc_vi, kinh_nghiem, avatar, gia_kham, trang_thai_lam_viec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", doctor_records)
    cur.execute("SET IDENTITY_INSERT bac_si OFF")

    # Insert benh_nhan
    cur.execute("SET IDENTITY_INSERT benh_nhan ON")
    cur.executemany("INSERT INTO benh_nhan (id, tai_khoan_id, ma_benh_nhan, ho_ten, ngay_sinh, gioi_tinh, sdt, email, cccd, bhyt, dia_chi, nhom_mau, ghi_chu_nhom_mau, avatar, di_ung, tien_su_benh, tien_su_gia_dinh, nguoi_than_ho_ten, nguoi_than_sdt, nguoi_than_quan_he, co_tai_khoan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", patient_records)
    cur.execute("SET IDENTITY_INSERT benh_nhan OFF")

    # Insert chi_so_sinh_ton
    cur.execute("SET IDENTITY_INSERT chi_so_sinh_ton ON")
    cur.executemany("INSERT INTO chi_so_sinh_ton (id, benh_nhan_id, mach, nhiet_do, huyet_ap, spo2, nhip_tho, chieu_cao, can_nang, bmi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", vitals)
    cur.execute("SET IDENTITY_INSERT chi_so_sinh_ton OFF")

    # 6. Du lieu mau lich hen, kham benh, chi dinh CLS, don thuoc, hoa don vien phi
    # Tao 1 lich hen hoan tat quy trinh cho benh nhan 1 tai Khoa Noi (BS 1)
    cur.execute("SET IDENTITY_INSERT lich_hen ON")
    cur.execute("""
        INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
        VALUES (1, 'LH26090001', 1, 1, 1, 1, CAST(GETDATE() AS DATE), '08:30:00', N'Đau âm ỉ vùng thượng vị kèm ợ chua nhiều tuần nay', 1, N'Đã hoàn thành', DATEADD(DAY, -1, GETDATE()))
    """)
    # Tao lich hen sap toi de test nhac nho tu dong
    cur.execute("""
        INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
        VALUES (2, 'LH26090002', 1, 2, 1, 2, DATEADD(DAY, 1, CAST(GETDATE() AS DATE)), '09:00:00', N'Tái khám định kỳ theo dõi chỉ số huyết áp và mỡ máu', 1, N'Đã tiếp nhận', GETDATE())
    """)
    # Tao lich hen cho tiep nhan de test le tan/admin tiep nhan
    cur.execute("""
        INSERT INTO lich_hen (id, ma_lich_hen, benh_nhan_id, bac_si_id, chuyen_khoa_id, phong_kham_id, ngay_hen, gio_hen, ly_do_kham, loai_lich_hen, trang_thai, ngay_dat)
        VALUES (3, 'LH26090003', 2, 11, 3, 11, DATEADD(DAY, 2, CAST(GETDATE() AS DATE)), '10:00:00', N'Bé sốt nhẹ về chiều và ho khan có đờm', 1, N'Chờ tiếp nhận', GETDATE())
    """)
    cur.execute("SET IDENTITY_INSERT lich_hen OFF")

    # Phieu kham cho lich hen 1
    cur.execute("SET IDENTITY_INSERT phieu_kham ON")
    cur.execute("""
        INSERT INTO phieu_kham (id, ma_phieu, benh_nhan_id, bac_si_id, phong_kham_id, lich_hen_id, thoi_gian_kham, ly_do_kham, trieu_chung, chan_doan_so_bo, chan_doan_icd, huong_dieu_tri, loi_dan, ngay_tai_kham, trang_thai)
        VALUES (1, 'PK26090001', 1, 1, 1, 1, GETDATE(), N'Đau thượng vị ợ chua', N'Đau âm ỉ vùng thượng vị sau ăn no hoặc lúc đói, ợ chua, buồn nôn nhẹ, bụng chướng hơi.', N'Theo dõi Viêm loét dạ dày tá tràng / Trào ngược dạ dày thực quản (GERD)', 'K29.7 - Viêm dạ dày không đặc hiệu', N'Chỉ định nội soi dạ dày, xét nghiệm vi khuẩn HP và công thức máu. Kê đơn thuốc giảm tiết acid.', N'Kiêng ăn đồ cay nóng chua cay, không thức khuya, uống thuốc đúng giờ trước bữa ăn 30 phút.', DATEADD(DAY, 14, CAST(GETDATE() AS DATE)), N'Hoàn thành')
    """)
    cur.execute("SET IDENTITY_INSERT phieu_kham OFF")

    # Phieu chi dinh CLS & Chi tiet chi dinh (X-Quang, Mau)
    cur.execute("SET IDENTITY_INSERT phieu_chi_dinh ON")
    cur.execute("""
        INSERT INTO phieu_chi_dinh (id, ma_chi_dinh, phieu_kham_id, bac_si_id, thoi_gian_chi_dinh, ghi_chu, trang_thai)
        VALUES (1, 'CD26090001', 1, 1, GETDATE(), N'Thực hiện gấp trong buổi sáng để chẩn đoán', N'Hoàn thành')
    """)
    cur.execute("SET IDENTITY_INSERT phieu_chi_dinh OFF")

    cur.execute("SET IDENTITY_INSERT chi_tiet_chi_dinh ON")
    cur.execute("""
        INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai, bac_si_duyet, thoi_gian_duyet, ghi_chu_duyet)
        VALUES (1, 1, 8, N'RBC: 4.8 T/L, Hb: 145 g/L, WBC: 7.2 G/L (Bình thường), PLT: 250 G/L. Kết luận: Công thức máu trong giới hạn sinh lý bình thường.', N'KTV. Võ Anh Đức', GETDATE(), N'Hoàn thành', N'BS. Trần Minh Quân', GETDATE(), N'Chỉ số bình thường, không có dấu hiệu nhiễm trùng cấp')
    """)
    cur.execute("""
        INSERT INTO chi_tiet_chi_dinh (id, phieu_chi_dinh_id, dich_vu_id, ket_qua, ktv_thuc_hien, thoi_gian_thuc_hien, trang_thai, bac_si_duyet, thoi_gian_duyet, ghi_chu_duyet)
        VALUES (2, 1, 13, N'Hình ảnh X-Quang phổi: Không thấy tổn thương thâm nhiễm nhu mô phổi hai bên. Khung sườn và bóng tim bình thường.', N'KTV. Hoàng Văn Cường', GETDATE(), N'Hoàn thành', N'BS. Trần Minh Quân', GETDATE(), N'X-quang lồng ngực bình thường')
    """)
    cur.execute("SET IDENTITY_INSERT chi_tiet_chi_dinh OFF")

    # Don thuoc cho phieu kham 1
    cur.execute("SET IDENTITY_INSERT don_thuoc ON")
    cur.execute("""
        INSERT INTO don_thuoc (id, ma_don_thuoc, phieu_kham_id, bac_si_id, thoi_gian_ke, loi_dan, trang_thai)
        VALUES (1, 'DT26090001', 1, 1, GETDATE(), N'Uống thuốc đúng theo hướng dẫn, tái khám sau 2 tuần', N'Đã cấp thuốc')
    """)
    cur.execute("SET IDENTITY_INSERT don_thuoc OFF")

    cur.execute("SET IDENTITY_INSERT chi_tiet_don_thuoc ON")
    cur.execute("""
        INSERT INTO chi_tiet_don_thuoc (id, don_thuoc_id, thuoc_id, so_luong, lieu_dung, cach_dung)
        VALUES 
        (1, 1, 11, 28, N'Uống 1 viên/lần, ngày 2 lần', N'Uống trước ăn sáng và ăn tối 30 phút'),
        (2, 1, 12, 14, N'Uống 1 gói/lần khi đau tức thượng vị', N'Uống trực tiếp sau khi ăn 1 giờ')
    """)
    cur.execute("SET IDENTITY_INSERT chi_tiet_don_thuoc OFF")

    # Hoa don vien phi tong hop
    cur.execute("SET IDENTITY_INSERT hoa_don ON")
    # Kham: 150.000 + Mau: 150.000 + XQuang: 200.000 + Thuoc: (28*8.000 + 14*5.500 = 224.000 + 77.000 = 301.000) = 801.000
    # Tien BHYT: Khám 80% (120k) + Mau 80% (120k) + XQuang 70% (140k) = 380k
    # Thanh tien = 801.000 - 380.000 = 421.000
    cur.execute("""
        INSERT INTO hoa_don (id, ma_hoa_don, benh_nhan_id, phieu_kham_id, tong_tien, tien_bhyt, giam_gia, thanh_tien, hinh_thuc_thanh_toan, trang_thai, thoi_gian_thanh_toan, nhan_vien_thu)
        VALUES (1, 'HD26090001', 1, 1, 801000.0, 380000.0, 0.0, 421000.0, N'Chuyển khoản QR Code', N'Đã thanh toán', GETDATE(), N'Lê Phương Thảo')
    """)
    cur.execute("SET IDENTITY_INSERT hoa_don OFF")

    cur.execute("SET IDENTITY_INSERT chi_tiet_hoa_don ON")
    cur.execute("""
        INSERT INTO chi_tiet_hoa_don (id, hoa_don_id, loai_khoan_thu, ten_khoan_thu, tham_chieu_id, so_luong, don_gia, thanh_tien)
        VALUES 
        (1, 1, N'Khám bệnh', N'Khám Chuyên Khoa Nội Tổng Quát', 1, 1, 150000.0, 150000.0),
        (2, 1, N'Xét nghiệm', N'Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)', 8, 1, 150000.0, 150000.0),
        (3, 1, N'Chẩn đoán hình ảnh', N'Chụp X-Quang Ngực thẳng kỹ thuật số (DR)', 13, 1, 200000.0, 200000.0),
        (4, 1, N'Thuốc', N'Esomeprazole 20mg Stada', 11, 28, 8000.0, 224000.0),
        (5, 1, N'Thuốc', N'Phosphalugel 20g (Thuốc dạ dày chữ P)', 12, 14, 5500.0, 77000.0)
    """)
    cur.execute("SET IDENTITY_INSERT chi_tiet_hoa_don OFF")

    # Thong bao mau cho benh nhan
    cur.execute("SET IDENTITY_INSERT thong_bao ON")
    cur.execute("""
        INSERT INTO thong_bao (id, tai_khoan_id, tieu_de, noi_dung, loai_thong_bao, lien_ket, da_doc, thoi_gian_tao)
        VALUES 
        (1, 48, N'Tiếp nhận lịch khám thành công!', N'Lịch hẹn khám mã LH26090002 của bạn vào ngày mai lúc 09:00 tại Chuyên khoa Nội đã được bộ phận Lễ tân tiếp nhận. Vui lòng có mặt trước 15 phút tại Quầy tiếp đón.', N'Lịch hẹn', '/patient/booking', 0, GETDATE()),
        (2, 48, N'Hoàn thành đợt khám bệnh', N'Hồ sơ khám bệnh EMR và kết quả xét nghiệm mã PK26090001 đã có kết quả đầy đủ. Bạn có thể tra cứu và tải toa thuốc trên cổng bệnh nhân.', N'Khám bệnh', '/patient/records', 0, GETDATE())
    """)
    cur.execute("SET IDENTITY_INSERT thong_bao OFF")

    # Banners
    banners = [
        (1, 'Chăm sóc bằng tài năng, y đức và sự thấu cảm', 'Tiêu chuẩn chất lượng quốc tế', 'Bệnh viện Đa khoa Quốc tế H2T Healthcare mang đến trải nghiệm khám chữa bệnh chuẩn mực với 35 bác sĩ chuyên khoa giàu kinh nghiệm và hệ thống bệnh án điện tử EMR 360°.', 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1600', '/booking', 'ĐĂNG KÝ KHÁM NGAY', 1, 1),
        (2, 'Đội ngũ 35 Bác sĩ chuyên khoa đầu ngành', 'Chuyên môn vững vàng', 'Hội tụ 35 bác sĩ chuyên khoa ThS.BS, BSCKII tại 7 chuyên khoa lâm sàng, tận tâm đồng hành vì sức khỏe toàn diện của gia đình bạn.', 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=1600', '#bac-si', 'TÌM BÁC SĨ CHUYÊN KHOA', 2, 1),
        (3, 'Hệ thống Bệnh án điện tử EMR 360°', 'Công nghệ y tế số 4.0', 'Tra cứu trực tuyến lịch sử khám bệnh, kết quả xét nghiệm, phim X-quang và đơn thuốc tiện lợi, bảo mật tuyệt đối.', 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1600', '/patient', 'CỔNG THÔNG TIN BỆNH NHÂN', 3, 1)
    ]
    cur.execute("SET IDENTITY_INSERT banner ON")
    cur.executemany("INSERT INTO banner (id, tieu_de, phu_de, mo_ta, hinh_anh, link_lien_ket, text_nut, thu_tu, trang_thai) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", banners)
    cur.execute("SET IDENTITY_INSERT banner OFF")

    # Bai viet
    articles = [
        (1, 1, 'Bệnh cảm cúm mùa giao mùa và cách phòng ngừa hiệu quả', 'benh-cam-cum-mua-giao-mua', 'Cẩm Nang Y Tế', 'Thời tiết chuyển mùa là điều kiện thuận lợi cho virus cúm phát triển. Nhận biết triệu chứng sớm và chế độ dinh dưỡng tăng cường miễn dịch là chìa khóa bảo vệ sức khỏe cả gia đình.', 'Nội dung chi tiết hướng dẫn phòng ngừa cảm cúm: giữ ấm cơ thể, rửa tay thường xuyên với xà phòng, tiêm vắc xin cúm hằng năm, bổ sung vitamin C và uống đủ nước...', 'cam-cum.jpg', 320, 1),
        (2, 1, 'Chăm sóc sức khỏe răng miệng cho trẻ đúng cách từ nhỏ', 'cham-soc-rang-mieng-cho-tre', 'Nhi Khoa', 'Sâu răng ở trẻ em diễn tiến rất nhanh và ảnh hưởng trực tiếp đến quá trình mọc răng vĩnh viễn sau này. Bố mẹ cần lưu ý hướng dẫn bé chải răng đúng cách và khám định kỳ 6 tháng/lần.', 'Nội dung chi tiết hướng dẫn phụ huynh lựa chọn bàn chải lông mềm, kem đánh răng phù hợp lứa tuổi...', 'rang-mieng-tre.jpg', 215, 1),
        (3, 1, 'Khám sức khỏe tổng quát định kỳ: Lợi ích vàng không thể bỏ qua', 'kham-suc-khoe-tong-quat-dinh-ky', 'Tin Tức Phòng Khám', 'Tầm soát sức khỏe định kỳ giúp phát hiện sớm các bệnh lý tiềm ẩn nguy hiểm như cao huyết áp, tiểu đường, gan nhiễm mỡ, gout ngay từ giai đoạn chưa có biểu hiện triệu chứng.', 'Nội dung chi tiết về các gói khám tổng quát tại H2T Healthcare...', 'kham-tong-quat.jpg', 580, 1)
    ]
    cur.execute("SET IDENTITY_INSERT bai_viet ON")
    cur.executemany("INSERT INTO bai_viet (id, tac_gia_id, tieu_de, slug, danh_muc, tom_tat, noi_dung, hinh_anh, luot_xem, trang_thai) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", articles)
    cur.execute("SET IDENTITY_INSERT bai_viet OFF")

    # Lich lam viec (ca truc) cho 35 bac si trong 14 ngay toi
    cur.execute('''
        SELECT bs.id AS bac_si_id, bs.nhan_vien_id, bs.phong_kham_chinh_id, bs.chuyen_khoa_id
        FROM bac_si bs
        ORDER BY bs.chuyen_khoa_id, bs.id
    ''')
    doc_rows = cur.fetchall()
    shifts_meta = {
        1: ('07:00:00', '11:30:00'),
        2: ('13:30:00', '17:00:00'),
        3: ('17:30:00', '20:30:00')
    }
    dept_docs = {}
    for dr in doc_rows:
        dept_docs.setdefault(dr[3], []).append(dr)

    today = date.today()
    schedules = []
    for day_offset in range(14):
        target_date = today + timedelta(days=day_offset)
        date_str = target_date.strftime('%Y-%m-%d')
        for ck_id, d_list in dept_docs.items():
            for idx, d_row in enumerate(d_list):
                shift_idx = ((idx + day_offset) % 3) + 1
                start_time, end_time = shifts_meta[shift_idx]
                schedules.append((
                    d_row[0], d_row[1], d_row[2], date_str, shift_idx,
                    start_time, end_time, 20, 0, 1, 'DA_DUYET'
                ))

    cur.executemany('''
        INSERT INTO lich_lam_viec (
            bac_si_id, nhan_vien_id, phong_kham_id, ngay_lam, ca_lam,
            gio_bat_dau, gio_ket_thuc, so_luong_kham_toi_da, so_luong_da_dang_ky,
            trang_thai, trang_thai_duyet
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', schedules)

    conn.commit()
    print("Nap du lieu SQL Server thanh cong 100%!")

    # In thong ke kiem tra
    cur.execute("SELECT COUNT(*) as c FROM tai_khoan")
    print(f"- Tong so tai khoan: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) as c FROM bac_si")
    print(f"- Tong so bac si: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) as c FROM nhan_vien")
    print(f"- Tong so nhan vien: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) as c FROM benh_nhan")
    print(f"- Tong so benh nhan: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) as c FROM phong_kham")
    print(f"- Tong so phong kham: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) as c FROM lich_lam_viec")
    print(f"- Tong so ca truc lich lam viec: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) as c FROM thuoc WHERE so_luong_ton <= ton_kho_toi_thieu")
    print(f"- So luong thuoc can canh bao ton kho thap: {cur.fetchone()[0]}")

    conn.close()

if __name__ == '__main__':
    seed()
