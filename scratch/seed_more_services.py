import io
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database import get_db

new_services = [
    # Khoa Nội (ID 1)
    (1, 'DV_KHAM_NOI_THAN', 'Khám chuyên sâu Nội Thận - Tiết niệu & Suy thận mạn', 'Khám chuyên khoa', 200000, 80, 'Thăm khám, chẩn đoán hội chứng thận hư, viêm cầu thận, suy thận mạn và sỏi tiết niệu'),
    (1, 'DV_KHAM_NOI_TK_NGU', 'Khám chuyên sâu Thần kinh & Rối loạn Giấc ngủ', 'Khám chuyên khoa', 220000, 80, 'Khám đau đầu mạn tính, chóng mặt tiền đình, suy nhược thần kinh và mất ngủ kéo dài'),
    (1, 'DV_KHAM_NOI_LOANGXUONG', 'Khám & Đo mật độ xương tầm soát Loãng xương', 'Khám chuyên khoa', 220000, 80, 'Tầm soát loãng xương, đo mật độ khoáng xương DEXA và dự phòng gãy xương người cao tuổi'),

    # Khoa Ngoại (ID 2)
    (2, 'DV_KHAM_NGOAI_CHINH_HINH', 'Khám Chấn thương chỉnh hình và Cột sống', 'Khám chuyên khoa', 200000, 80, 'Khám và tư vấn bệnh lý thoái hóa cột sống, thoát vị đĩa đệm, tổn thương dây chằng'),
    (2, 'DV_KHAM_NGOAI_MACH_MAU', 'Khám Tầm soát Suy giãn Tĩnh mạch chi dưới', 'Khám chuyên khoa', 220000, 80, 'Khám chuyên sâu phù chân, chuột rút về đêm, suy van tĩnh mạch nông và sâu chi dưới'),
    (2, 'DV_KHAM_NGOAI_U_PHAN_MEM', 'Khám & Sinh thiết Chẩn đoán U phần mềm - Hạch', 'Khám chuyên khoa', 250000, 80, 'Khám u mỡ, u bã đậu, u nang bao hoạt dịch và chọc hút sinh thiết tế bào hạch cổ/nách'),

    # Khoa Nhi (ID 3)
    (3, 'DV_KHAM_NHI_DAYTHISOM', 'Khám & Đánh giá Dậy thì sớm ở Trẻ em', 'Khám chuyên khoa', 250000, 0, 'Đánh giá tuổi xương, nội tiết tố tăng trưởng và sàng lọc dậy thì sớm ở trẻ gái dưới 8 tuổi, trẻ trai dưới 9 tuổi'),
    (3, 'DV_KHAM_NHI_THIEUMAU', 'Khám Sàng lọc Thiếu máu và Vi chất dinh dưỡng Trẻ em', 'Khám chuyên khoa', 180000, 80, 'Tầm soát thiếu máu thiếu sắt, còi xương, thiếu vitamin D, kẽm, canxi và tư vấn bổ sung vi chất'),
    (3, 'DV_KHAM_NHI_HEN', 'Khám Quản lý Hen suyễn & Dị ứng thời tiết Nhi khoa', 'Khám chuyên khoa', 200000, 80, 'Theo dõi, lập kế hoạch quản lý cơn hen phế quản và điều trị viêm da dị ứng ở trẻ nhỏ'),

    # Khoa Răng Hàm Mặt (ID 4)
    (4, 'DV_KHAM_RHM_RANGKHON', 'Khám Tầm soát & Đánh giá Nhổ răng khôn mọc ngầm', 'Khám chuyên khoa', 180000, 80, 'Đánh giá nguy cơ xô lệch hàm, viêm lợi trùm và chụp phim kiểm tra vị trí dây thần kinh quanh răng số 8'),
    (4, 'DV_TT_TRAM_RANG_COMPOSITE', 'Trám răng thẩm mỹ Composite công nghệ Nano', 'Thủ thuật', 250000, 70, 'Phục hồi răng sâu, răng sứt mẻ với vật liệu Composite trùng màu răng tự nhiên'),
    (4, 'DV_KHAM_RHM_UNGTHUKHOANGMIENG', 'Khám Sàng lọc sớm Tổn thương tiền ung thư Khoang miệng', 'Khám chuyên khoa', 220000, 80, 'Soi phát hiện bạch sản, hồng sản và các ổ loét niêm mạc miệng mạn tính không lành'),

    # Khoa Sản - Phụ Khoa (ID 5)
    (5, 'DV_KHAM_SAN_TAMSOAT_CTC', 'Khám & Tầm soát Ung thư Cổ tử cung (Pap Smear & HPV)', 'Khám chuyên khoa', 280000, 80, 'Khám phụ khoa kết hợp lấy mẫu tế bào học Pap smear và định type HPV nguy cơ cao'),
    (5, 'DV_KHAM_SAN_TIENHONNHAN', 'Khám & Tư vấn Sức khỏe Tiền hôn nhân', 'Khám chuyên khoa', 300000, 0, 'Đánh giá chức năng sinh sản nam nữ, sàng lọc gen bệnh Thalassemia và tư vấn di truyền trước hôn nhân'),
    (5, 'DV_KHAM_SAN_PCOS', 'Khám & Điều trị Hội chứng Buồng trứng đa nang (PCOS)', 'Khám chuyên khoa', 220000, 80, 'Khám rối loạn phóng noãn, kinh nguyệt không đều, rậm lông và phác đồ điều trị hiếm muộn do PCOS'),

    # Khoa Tai Mũi Họng (ID 6)
    (6, 'DV_KHAM_TMH_NGUNG_THO', 'Khám & Tầm soát Hội chứng Ngủ ngáy và Ngưng thở khi ngủ', 'Khám chuyên khoa', 250000, 80, 'Nội soi đường thở trên, đánh giá khẩu cái mềm, lưỡi gà và amidan ở người ngủ ngáy'),
    (6, 'DV_KHAM_TMH_VIEM_TAI_GIUA', 'Khám Chuyên sâu Viêm tai giữa & Đo chức năng vòi nhĩ', 'Khám chuyên khoa', 200000, 80, 'Nội soi màng nhĩ độ phóng đại cao, đánh giá ứ dịch tai giữa và thông vòi nhĩ'),
    (6, 'DV_TT_LAY_DI_VAT_TMH', 'Gắp lấy dị vật Tai - Mũi - Họng phức tạp dưới nội soi', 'Thủ thuật', 220000, 80, 'Kỹ thuật gắp dị vật xương cá, hạt thực phẩm, dị vật tai bằng kẹp vi phẫu dưới hướng dẫn nội soi'),

    # Khoa Mắt (ID 7)
    (7, 'DV_KHAM_MAT_DUC_TTT', 'Khám Sàng lọc & Đánh giá Đục thủy tinh thể (Cườm khô)', 'Khám chuyên khoa', 200000, 80, 'Khám đèn khe sinh hiển vi, đo công suất thể thủy tinh nhân tạo và tư vấn phẫu thuật Phaco'),
    (7, 'DV_KHAM_MAT_KHO_MAT', 'Khám & Xét nghiệm Đánh giá Hội chứng Khô mắt mạn tính', 'Khám chuyên khoa', 180000, 80, 'Test Schirmer kiểm tra lượng nước mắt, nhuộm Fluorescein và đo thời gian vỡ phim nước mắt (TBUT)'),
    (7, 'DV_KHAM_MAT_DAU_HIEU_DTĐ', 'Khám Soi đáy mắt chuyên sâu theo dõi biến chứng Đái tháo đường', 'Khám chuyên khoa', 220000, 80, 'Soi đáy mắt trực tiếp đồng tử giãn, đánh giá xuất huyết võng mạc, phù hoàng điểm do tiểu đường'),

    # Khoa Cận Lâm Sàng & CĐHA (ID 8)
    (8, 'DV_CDHA_CT_SCANNER', 'Chụp Cắt lớp vi tính đa dãy CT-Scanner sọ não / lồng ngực', 'Chẩn đoán hình ảnh', 850000, 80, 'Chụp CT Scanner 128 lát cắt độ phân giải cao dựng hình 3D sọ não, xoang, lồng ngực'),
    (8, 'DV_TDCN_DIEN_NAO_DO', 'Đo Điện não đồ vi tính đa kênh (EEG)', 'Thăm dò chức năng', 250000, 80, 'Ghi nhận sóng điện não đồ 32 kênh đánh giá động kinh, rối loạn tri giác, đau đầu'),
    (8, 'DV_XN_D_DIMER', 'Xét nghiệm định lượng D-Dimer (Tầm soát Huyết khối tắc mạch)', 'Xét nghiệm', 280000, 80, 'Định lượng D-Dimer huyết tương chẩn đoán thuyên tắc phổi, huyết khối tĩnh mạch sâu'),
    (8, 'DV_XN_HORMON_TUYEN_GIAP', 'Bộ xét nghiệm Định lượng Hormon Tuyến giáp (FT3, FT4, TSH)', 'Xét nghiệm', 260000, 80, 'Miễn dịch hóa phát quang đánh giá chức năng tuyến giáp, Basedow, suy giáp và bướu cổ nhân')
]

with get_db() as conn:
    cur = conn.cursor()
    inserted = 0
    for ck_id, ma, ten, loai, gia, bhyt, mota in new_services:
        cur.execute("SELECT id FROM dich_vu WHERE ma_dich_vu = ?", (ma,))
        exists = cur.fetchone()
        if not exists:
            cur.execute("""
                INSERT INTO dich_vu (chuyen_khoa_id, ma_dich_vu, ten_dich_vu, loai_dich_vu, don_gia, bhyt_chi_tra_pt, mo_ta, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (ck_id, ma, ten, loai, gia, bhyt, mota))
            inserted += 1
            print(f"Đã thêm: {ma} - {ten}")
        else:
            print(f"Đã tồn tại: {ma}")
    conn.commit()
    print(f"\n=> Tổng cộng đã thêm mới {inserted} dịch vụ khám chuyên khoa!")
