from flask import Flask, render_template, redirect, url_for, request, session, jsonify, abort

app = Flask(__name__)
app.secret_key = 'h2t_healthcare_clinic_secret_key_2026'

# Dữ liệu mẫu bệnh nhân đồng bộ với CSDL, loại bỏ hoàn toàn mật khẩu thô để đảm bảo an toàn thông tin y tế
PATIENTS_DATA = [
    {
        "id": 1,
        "ma_benh_nhan": "BN2609001",
        "ho_ten": "Hoàng Bảo Nam",
        "username": "0901234567",
        "password": "hashed_pwd_8",
        "ngay_sinh": "1990-05-12",
        "tuoi": 36,
        "gioi_tinh": "Nam",
        "sdt": "0901234567",
        "email": "baonam@gmail.com",
        "cccd": "079090000001",
        "bhyt": "GD4797931100001",
        "dia_chi": "Quận 1, TP.HCM",
        "nhom_mau": "O+",
        "di_ung": "Không có",
        "tien_su_benh": "Đau dạ dày nhẹ",
        "tien_su_gia_dinh": "Không có tiền sử bệnh lý di truyền",
        "nguoi_than_ho_ten": "Hoàng Tuấn Kiệt",
        "nguoi_than_sdt": "0909111222",
        "nguoi_than_quan_he": "Bố",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-01",
        "vitals": {
            "huyet_ap": "120/80 mmHg",
            "mach": "76 lần/phút",
            "nhiet_do": "36.8 °C",
            "spo2": "99 %",
            "nhip_tho": "18 lần/phút",
            "chieu_cao": "172 cm",
            "can_nang": "68 kg",
            "bmi": "23.0 (Bình thường)"
        },
        "lich_su_kham": [
            {
                "ma_phieu": "PK2609001",
                "ngay_kham": "2026-09-20 08:30",
                "bac_si": "BS. CKII. Trần Minh Quân",
                "khoa": "Khoa Tiêu Hóa - Nội Khoa",
                "phong": "Phòng khám 102",
                "ly_do_kham": "Đau âm ỉ vùng thượng vị, ợ chua, chướng bụng sau ăn",
                "trieu_chung": "Bệnh nhân tỉnh táo, tiếp xúc tốt. Ấn đau tức nhẹ vùng thượng vị, bụng mềm, không đề kháng thành bụng.",
                "chan_doan_icd": "K29.5 - Viêm dạ dày mạn tính, không xác định",
                "loi_dan": "Ăn uống đúng bữa, hạn chế đồ cay nóng và rượu bia. Tái khám theo lịch hẹn hoặc khi có dấu hiệu bất thường.",
                "can_lam_sang": [
                    {
                        "ten": "Nội soi thực quản - dạ dày - tá tràng ống mềm",
                        "loai": "Chẩn đoán hình ảnh",
                        "ket_qua": "Niêm mạc hang vị phù nề, sung huyết nhẹ. Test Clo HP: Âm tính (-)",
                        "bac_si_thuc_hien": "BS. CKI. Nguyễn Trọng Nghĩa",
                        "trang_thai": "Hoàn thành"
                    },
                    {
                        "ten": "Tổng phân tích tế bào máu ngoại vi (CBC 18 chỉ số)",
                        "loai": "Xét nghiệm huyết học",
                        "ket_qua": "Hồng cầu: 4.85 T/L, Bạch cầu: 6.8 G/L, Tiểu cầu: 235 G/L. Các chỉ số trong giới hạn bình thường.",
                        "bac_si_thuc_hien": "KTV. Lê Thị Thu",
                        "trang_thai": "Hoàn thành"
                    }
                ],
                "don_thuoc": [
                    {"ten": "Esomeprazole 40mg", "hoat_chat": "Esomeprazole", "so_luong": "28 Viên", "cach_dung": "Uống 1 viên trước ăn sáng 30 phút"},
                    {"ten": "Phosphalugel 20g", "hoat_chat": "Aluminium phosphate", "so_luong": "20 Gói", "cach_dung": "Uống 1 gói khi đau hoặc sau ăn 2 giờ"},
                    {"ten": "Domperidon 10mg", "hoat_chat": "Domperidone", "so_luong": "20 Viên", "cach_dung": "Uống 1 viên trước ăn 15 phút, ngày 2 lần"}
                ],
                "lich_tai_kham": "2026-10-04 (Sau 14 ngày)"
            }
        ]
    },
    {
        "id": 2,
        "ma_benh_nhan": "BN2609002",
        "ho_ten": "Lê Ngọc Trâm",
        "username": "0912345678",
        "password": "hashed_pwd_9",
        "ngay_sinh": "1995-08-22",
        "tuoi": 31,
        "gioi_tinh": "Nữ",
        "sdt": "0912345678",
        "email": "ngoctram@gmail.com",
        "cccd": "079095000002",
        "bhyt": "GD4797931100002",
        "dia_chi": "Quận 3, TP.HCM",
        "nhom_mau": "A+",
        "di_ung": "Dị ứng hải sản, Paracetamol",
        "tien_su_benh": "Viêm xoang dị ứng",
        "tien_su_gia_dinh": "Mẹ có tiền sử hen phế quản",
        "nguoi_than_ho_ten": "Lê Quang Liêm",
        "nguoi_than_sdt": "0919222333",
        "nguoi_than_quan_he": "Bố",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-02",
        "vitals": {
            "huyet_ap": "110/70 mmHg",
            "mach": "72 lần/phút",
            "nhiet_do": "37.0 °C",
            "spo2": "98 %",
            "nhip_tho": "17 lần/phút",
            "chieu_cao": "160 cm",
            "can_nang": "50 kg",
            "bmi": "19.5 (Bình thường)"
        },
        "lich_su_kham": [
            {
                "ma_phieu": "PK2609002",
                "ngay_kham": "2026-09-18 09:15",
                "bac_si": "BS. CKI. Phan Thu Trang",
                "khoa": "Khoa Tai Mũi Họng",
                "phong": "Phòng khám 201",
                "ly_do_kham": "Nghẹt mũi kéo dài, hắt hơi nhiều khi thay đổi thời tiết",
                "trieu_chung": "Niêm mạc cuốn mũi dưới phù nề, thoái hóa nhẹ, có dịch nhầy trong.",
                "chan_doan_icd": "J30.1 - Viêm mũi dị ứng do phấn hoa / thời tiết",
                "loi_dan": "Tránh tiếp xúc môi trường bụi bẩn, lạnh đột ngột. Rửa mũi bằng nước muối sinh lý hàng ngày.",
                "can_lam_sang": [
                    {
                        "ten": "Nội soi Tai Mũi Họng bằng optic mềm",
                        "loai": "Chẩn đoán hình ảnh",
                        "ket_qua": "Cuốn mũi hai bên phù nề, vách ngăn hơi vẹo nhẹ sang trái, họng sạch.",
                        "bac_si_thuc_hien": "BS. CKI. Phan Thu Trang",
                        "trang_thai": "Hoàn thành"
                    }
                ],
                "don_thuoc": [
                    {"ten": "Desloratadine 5mg", "hoat_chat": "Desloratadine", "so_luong": "14 Viên", "cach_dung": "Uống 1 viên buổi tối sau ăn"},
                    {"ten": "Flixonase 50mcg", "hoat_chat": "Fluticasone propionate", "so_luong": "1 Chai", "cach_dung": "Xịt mỗi bên mũi 1 nhát/ngày vào buổi sáng"}
                ],
                "lich_tai_kham": "2026-10-02"
            }
        ]
    },
    {
        "id": 3,
        "ma_benh_nhan": "BN2609003",
        "ho_ten": "Trần Văn Quyết",
        "username": "0923456789",
        "password": "hashed_pwd_10",
        "ngay_sinh": "1985-11-30",
        "tuoi": 41,
        "gioi_tinh": "Nam",
        "sdt": "0923456789",
        "email": "vanquyet@gmail.com",
        "cccd": "079085000003",
        "bhyt": "GD4797931100003",
        "dia_chi": "Quận Tân Bình, TP.HCM",
        "nhom_mau": "B+",
        "di_ung": "Không có",
        "tien_su_benh": "Tăng huyết áp độ 1, rối loạn lipid máu",
        "tien_su_gia_dinh": "Bố bị tai biến mạch máu não",
        "nguoi_than_ho_ten": "Trần Thị Hà",
        "nguoi_than_sdt": "0929333444",
        "nguoi_than_quan_he": "Vợ",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-03",
        "vitals": {
            "huyet_ap": "145/90 mmHg",
            "mach": "82 lần/phút",
            "nhiet_do": "36.7 °C",
            "spo2": "97 %",
            "nhip_tho": "19 lần/phút",
            "chieu_cao": "168 cm",
            "can_nang": "74 kg",
            "bmi": "26.2 (Thừa cân)"
        },
        "lich_su_kham": [
            {
                "ma_phieu": "PK2609003",
                "ngay_kham": "2026-09-15 14:00",
                "bac_si": "BS. CKII. Trần Minh Quân",
                "khoa": "Khoa Tim Mạch - Nội Tiết",
                "phong": "Phòng khám 103",
                "ly_do_kham": "Đau nặng đầu vùng gáy, đo huyết áp tại nhà 150/95 mmHg",
                "trieu_chung": "Nhịp tim đều, không âm thổi bệnh lý. Huyết áp đo tại phòng khám 145/90 mmHg.",
                "chan_doan_icd": "I10 - Tăng huyết áp vô căn (nguyên phát)",
                "loi_dan": "Ăn giảm mặn (<5g muối/ngày), tăng cường tập thể dục nhẹ nhàng 30 phút mỗi ngày. Đo huyết áp định kỳ sáng - tối.",
                "can_lam_sang": [
                    {
                        "ten": "Đo điện tim thường (ECG 12 chuyển đạo)",
                        "loai": "Thăm dò chức năng",
                        "ket_qua": "Nhịp xoang đều, tần số 80ck/phút, không thấy dấu hiệu dày thất trái.",
                        "bac_si_thuc_hien": "BS. Nguyễn Văn Hậu",
                        "trang_thai": "Hoàn thành"
                    },
                    {
                        "ten": "Sinh hóa máu: Bộ mỡ máu (Lipid panel)",
                        "loai": "Xét nghiệm sinh hóa",
                        "ket_qua": "Cholesterol TP: 5.8 mmol/L, Triglycerid: 2.3 mmol/L, LDL-C: 3.6 mmol/L.",
                        "bac_si_thuc_hien": "KTV. Lê Thị Thu",
                        "trang_thai": "Hoàn thành"
                    }
                ],
                "don_thuoc": [
                    {"ten": "Amlodipine 5mg", "hoat_chat": "Amlodipine", "so_luong": "30 Viên", "cach_dung": "Uống 1 viên buổi sáng"},
                    {"ten": "Atorvastatin 10mg", "hoat_chat": "Atorvastatin", "so_luong": "30 Viên", "cach_dung": "Uống 1 viên buổi tối trước khi đi ngủ"}
                ],
                "lich_tai_kham": "2026-10-15"
            }
        ]
    },
    {
        "id": 4,
        "ma_benh_nhan": "BN2609004",
        "ho_ten": "Phạm Thảo My",
        "username": "0934567890",
        "password": "hashed_pwd_11",
        "ngay_sinh": "2015-02-14",
        "tuoi": 11,
        "gioi_tinh": "Nữ",
        "sdt": "0934567890",
        "email": "thaomy@gmail.com",
        "cccd": "079115000004",
        "bhyt": "TE1797931100004",
        "dia_chi": "Quận Gò Vấp, TP.HCM",
        "nhom_mau": "AB+",
        "di_ung": "Không có",
        "tien_su_benh": "Hen phế quản (Suyễn trẻ em)",
        "tien_su_gia_dinh": "Không có",
        "nguoi_than_ho_ten": "Phạm Minh Nhật",
        "nguoi_than_sdt": "0939444555",
        "nguoi_than_quan_he": "Bố",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-05",
        "vitals": {
            "huyet_ap": "100/65 mmHg",
            "mach": "88 lần/phút",
            "nhiet_do": "36.6 °C",
            "spo2": "99 %",
            "nhip_tho": "20 lần/phút",
            "chieu_cao": "142 cm",
            "can_nang": "35 kg",
            "bmi": "17.4 (Bình thường)"
        },
        "lich_su_kham": [
            {
                "ma_phieu": "PK2609004",
                "ngay_kham": "2026-09-10 10:00",
                "bac_si": "BS. CKI. Đỗ Hoàng Yến",
                "khoa": "Khoa Nhi",
                "phong": "Phòng khám 301",
                "ly_do_kham": "Tái khám hen phế quản định kỳ",
                "trieu_chung": "Trẻ tỉnh táo, ăn ngủ tốt. Phổi thông khí tốt, không rale rít ngáy.",
                "chan_doan_icd": "J45.0 - Hen phế quản thể dị ứng",
                "loi_dan": "Duy trì thuốc xịt dự phòng đều đặn, luôn mang theo bình xịt cắt cơn khi đi học.",
                "can_lam_sang": [],
                "don_thuoc": [
                    {"ten": "Seretide Evohaler 25/50mcg", "hoat_chat": "Salmeterol / Fluticasone", "so_luong": "1 Bình", "cach_dung": "Xịt 1 nhát sáng, 1 nhát tối, súc miệng sau xịt"},
                    {"ten": "Ventolin Inhaler 100mcg", "hoat_chat": "Salbutamol", "so_luong": "1 Bình", "cach_dung": "Xịt 1-2 nhát khi khó thở hoặc lên cơn hen"}
                ],
                "lich_tai_kham": "2026-10-10"
            }
        ]
    },
    {
        "id": 5,
        "ma_benh_nhan": "BN2609005",
        "ho_ten": "Đinh Trọng Thắng",
        "username": "0945678901",
        "password": "hashed_pwd_12",
        "ngay_sinh": "1978-04-10",
        "tuoi": 48,
        "gioi_tinh": "Nam",
        "sdt": "0945678901",
        "email": "trongthang@gmail.com",
        "cccd": "079078000005",
        "bhyt": "DN4797931100005",
        "dia_chi": "Quận 10, TP.HCM",
        "nhom_mau": "O-",
        "di_ung": "Không có",
        "tien_su_benh": "Đái tháo đường type 2, Gan nhiễm mỡ",
        "tien_su_gia_dinh": "Mẹ bị đái tháo đường",
        "nguoi_than_ho_ten": "Đinh Lan Anh",
        "nguoi_than_sdt": "0949555666",
        "nguoi_than_quan_he": "Vợ",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-06",
        "vitals": {
            "huyet_ap": "125/80 mmHg",
            "mach": "78 lần/phút",
            "nhiet_do": "36.8 °C",
            "spo2": "98 %",
            "nhip_tho": "18 lần/phút",
            "chieu_cao": "165 cm",
            "can_nang": "67 kg",
            "bmi": "24.6 (Tiền béo phì nhẹ)"
        },
        "lich_su_kham": [
            {
                "ma_phieu": "PK2609005",
                "ngay_kham": "2026-09-08 08:00",
                "bac_si": "BS. CKII. Trần Minh Quân",
                "khoa": "Khoa Nội Tiết",
                "phong": "Phòng khám 104",
                "ly_do_kham": "Khám định kỳ đái tháo đường type 2",
                "trieu_chung": "Không tê bì tay chân, không tiểu đêm nhiều, mắt nhìn rõ.",
                "chan_doan_icd": "E11.9 - Đái tháo đường týp 2, không có biến chứng",
                "loi_dan": "Ăn giảm tinh bột, hạn chế đường ngọt. Tự theo dõi đường huyết mao mạch tại nhà.",
                "can_lam_sang": [
                    {
                        "ten": "Định lượng Glucose máu lúc đói",
                        "loai": "Xét nghiệm sinh hóa",
                        "ket_qua": "Glucose: 6.4 mmol/L, HbA1c: 6.8% (Kiểm soát đường huyết tốt)",
                        "bac_si_thuc_hien": "KTV. Lê Thị Thu",
                        "trang_thai": "Hoàn thành"
                    }
                ],
                "don_thuoc": [
                    {"ten": "Metformin 850mg", "hoat_chat": "Metformin", "so_luong": "60 Viên", "cach_dung": "Uống 1 viên sau bữa ăn sáng và tối"},
                    {"ten": "Gliclazide MR 30mg", "hoat_chat": "Gliclazide", "so_luong": "30 Viên", "cach_dung": "Uống 1 viên vào bữa ăn sáng"}
                ],
                "lich_tai_kham": "2026-10-08"
            }
        ]
    },
    {
        "id": 6,
        "ma_benh_nhan": "BN2609006",
        "ho_ten": "Võ Thanh Trúc",
        "username": "0956789012",
        "password": "hashed_pwd_13",
        "ngay_sinh": "1998-09-09",
        "tuoi": 28,
        "gioi_tinh": "Nữ",
        "sdt": "0956789012",
        "email": "thanhtruc@gmail.com",
        "cccd": "079098000006",
        "bhyt": "SV4797931100006",
        "dia_chi": "Quận Bình Thạnh, TP.HCM",
        "nhom_mau": "A+",
        "di_ung": "Dị ứng phấn hoa",
        "tien_su_benh": "Đau dạ dày",
        "tien_su_gia_dinh": "Không có",
        "nguoi_than_ho_ten": "Võ Hải Đăng",
        "nguoi_than_sdt": "0959666777",
        "nguoi_than_quan_he": "Anh trai",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-07",
        "vitals": {
            "huyet_ap": "115/75 mmHg",
            "mach": "74 lần/phút",
            "nhiet_do": "36.7 °C",
            "spo2": "99 %",
            "nhip_tho": "17 lần/phút",
            "chieu_cao": "162 cm",
            "can_nang": "48 kg",
            "bmi": "18.3 (Gầy nhẹ)"
        },
        "lich_su_kham": []
    },
    {
        "id": 7,
        "ma_benh_nhan": "BN2609007",
        "ho_ten": "Ngô Kiến Hào",
        "username": "0967890123",
        "password": "hashed_pwd_14",
        "ngay_sinh": "2010-12-25",
        "tuoi": 16,
        "gioi_tinh": "Nam",
        "sdt": "0967890123",
        "email": "kienhao@gmail.com",
        "cccd": "079110000007",
        "bhyt": "HS4797931100007",
        "dia_chi": "Quận 7, TP.HCM",
        "nhom_mau": "O+",
        "di_ung": "Không có",
        "tien_su_benh": "Không có",
        "tien_su_gia_dinh": "Không có",
        "nguoi_than_ho_ten": "Ngô Bảo Châu",
        "nguoi_than_sdt": "0969777888",
        "nguoi_than_quan_he": "Mẹ",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-08",
        "vitals": {
            "huyet_ap": "110/70 mmHg",
            "mach": "80 lần/phút",
            "nhiet_do": "36.9 °C",
            "spo2": "99 %",
            "nhip_tho": "18 lần/phút",
            "chieu_cao": "170 cm",
            "can_nang": "58 kg",
            "bmi": "20.1 (Bình thường)"
        },
        "lich_su_kham": []
    },
    {
        "id": 8,
        "ma_benh_nhan": "BN2609008",
        "ho_ten": "Lý Nhã Kỳ",
        "username": "0978901234",
        "password": "hashed_pwd_15",
        "ngay_sinh": "1982-07-19",
        "tuoi": 44,
        "gioi_tinh": "Nữ",
        "sdt": "0978901234",
        "email": "nhaky@gmail.com",
        "cccd": "079082000008",
        "bhyt": "DN4797931100008",
        "dia_chi": "Quận 2, TP.HCM",
        "nhom_mau": "B-",
        "di_ung": "Không có",
        "tien_su_benh": "Không có",
        "tien_su_gia_dinh": "Không có",
        "nguoi_than_ho_ten": "Lý Đại Nghĩa",
        "nguoi_than_sdt": "0979888999",
        "nguoi_than_quan_he": "Em trai",
        "co_tai_khoan": True,
        "ngay_tao": "2026-09-10",
        "vitals": {
            "huyet_ap": "120/78 mmHg",
            "mach": "75 lần/phút",
            "nhiet_do": "36.6 °C",
            "spo2": "99 %",
            "nhip_tho": "16 lần/phút",
            "chieu_cao": "165 cm",
            "can_nang": "54 kg",
            "bmi": "19.8 (Bình thường)"
        },
        "lich_su_kham": []
    },
    {
        "id": 9,
        "ma_benh_nhan": "BN2609009",
        "ho_ten": "Châu Gia Kiệt",
        "username": "",
        "password": "",
        "ngay_sinh": "1992-01-01",
        "tuoi": 34,
        "gioi_tinh": "Nam",
        "sdt": "0981234567",
        "email": "giakiet@gmail.com",
        "cccd": "079092000009",
        "bhyt": "",
        "dia_chi": "Thủ Đức, TP.HCM",
        "nhom_mau": "O+",
        "di_ung": "Không có",
        "tien_su_benh": "Viêm xoang",
        "tien_su_gia_dinh": "Không có",
        "nguoi_than_ho_ten": "Châu Ánh Nguyệt",
        "nguoi_than_sdt": "0989000111",
        "nguoi_than_quan_he": "Chị gái",
        "co_tai_khoan": False,
        "ngay_tao": "2026-09-12",
        "vitals": {
            "huyet_ap": "125/82 mmHg",
            "mach": "76 lần/phút",
            "nhiet_do": "36.8 °C",
            "spo2": "98 %",
            "nhip_tho": "18 lần/phút",
            "chieu_cao": "174 cm",
            "can_nang": "70 kg",
            "bmi": "23.1 (Bình thường)"
        },
        "lich_su_kham": []
    },
    {
        "id": 10,
        "ma_benh_nhan": "BN2609010",
        "ho_ten": "Bảo Thy",
        "username": "",
        "password": "",
        "ngay_sinh": "1999-03-03",
        "tuoi": 27,
        "gioi_tinh": "Nữ",
        "sdt": "0991234567",
        "email": "baothy@gmail.com",
        "cccd": "079099000010",
        "bhyt": "",
        "dia_chi": "Quận 5, TP.HCM",
        "nhom_mau": "A+",
        "di_ung": "Không có",
        "tien_su_benh": "Không có",
        "tien_su_gia_dinh": "Không có",
        "nguoi_than_ho_ten": "Bảo Quốc",
        "nguoi_than_sdt": "0999111222",
        "nguoi_than_quan_he": "Bố",
        "co_tai_khoan": False,
        "ngay_tao": "2026-09-15",
        "vitals": {
            "huyet_ap": "110/70 mmHg",
            "mach": "70 lần/phút",
            "nhiet_do": "36.6 °C",
            "spo2": "99 %",
            "nhip_tho": "16 lần/phút",
            "chieu_cao": "163 cm",
            "can_nang": "49 kg",
            "bmi": "18.4 (Gầy nhẹ)"
        },
        "lich_su_kham": []
    }
]

# Trang chủ & bài viết công khai
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/articles')
@app.route('/tin-tuc')
def articles():
    return render_template('articles.html')

# Điều hướng đặt lịch khám theo trạng thái đăng nhập
@app.route('/booking')
def booking():
    if session.get('logged_in') or session.get('user'):
        return redirect(url_for('patient_booking'))
    return redirect(url_for('login', next=url_for('patient_booking')))

# Xác thực tài khoản (Auth)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['logged_in'] = True
        session['user'] = {
            'id': 1,
            'ho_ten': 'Hoàng Bảo Nam',
            'sdt': '0901234567',
            'role': 'patient'
        }
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('patient_dashboard'))
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Phân hệ bệnh nhân (Patient Portal)
@app.route('/patient')
@app.route('/patient/dashboard')
def patient_dashboard():
    return render_template('patient/dashboard.html', active_page='dashboard')

@app.route('/patient/booking')
def patient_booking():
    return render_template('patient/booking.html', active_page='booking')

@app.route('/patient/records')
def patient_records():
    return render_template('patient/records.html', active_page='records')

@app.route('/patient/lab-results')
def patient_lab_results():
    return render_template('patient/lab_results.html', active_page='lab_results')

@app.route('/patient/billing')
def patient_billing():
    return render_template('patient/billing.html', active_page='billing')

@app.route('/patient/profile')
def patient_profile():
    return render_template('patient/profile.html', active_page='profile')

# Phân hệ quản trị / bác sĩ (Admin Portal)
@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html', active_page='admin_dashboard')

@app.route('/admin/patients')
def admin_patients():
    return render_template('admin/patients.html', active_page='admin_patients', patients=PATIENTS_DATA)

@app.route('/admin/patients/<int:patient_id>')
def admin_patient_detail(patient_id):
    patient = next((p for p in PATIENTS_DATA if p['id'] == patient_id), None)
    if not patient:
        abort(404)
    return render_template('admin/patient_detail.html', active_page='admin_patients', patient=patient)

@app.route('/admin/appointments')
def admin_appointments():
    return render_template('admin/appointments.html', active_page='admin_appointments', patients=PATIENTS_DATA)

@app.route('/admin/reception')
def admin_reception():
    return render_template('admin/reception.html', active_page='admin_reception', patients=PATIENTS_DATA)

@app.route('/admin/emr')
def admin_emr():
    return render_template('admin/emr.html', active_page='admin_emr', patients=PATIENTS_DATA)

@app.route('/admin/lab')
def admin_lab():
    return render_template('admin/lab.html', active_page='admin_lab', patients=PATIENTS_DATA)

@app.route('/admin/pharmacy')
def admin_pharmacy():
    return render_template('admin/pharmacy.html', active_page='admin_pharmacy')

@app.route('/admin/billing')
def admin_billing():
    return render_template('admin/billing.html', active_page='admin_billing', patients=PATIENTS_DATA)

@app.route('/admin/reports')
def admin_reports():
    return render_template('admin/reports.html', active_page='admin_reports')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
