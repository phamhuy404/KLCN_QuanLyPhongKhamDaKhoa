"""Dịch vụ xuất đơn thuốc và phiếu chỉ định cận lâm sàng ra tệp PDF.
Đạt chuẩn quy định Bộ Y tế (Thông tư 04/2022/TT-BYT và Thông tư 52/2017/TT-BYT).
Tích hợp mã vạch Code128, mã QR đối soát và hỗ trợ font tiếng Việt Unicode."""

import io
import os
from datetime import datetime
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.graphics.barcode import code128
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Đăng ký phông chữ tiếng Việt Unicode từ Windows Fonts
_FONTS_REGISTERED = False

def ensure_unicode_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    font_dir = os.environ.get('WINDIR', r'C:\Windows')
    fonts_path = os.path.join(font_dir, 'Fonts')
    arial_path = os.path.join(fonts_path, 'arial.ttf')
    arial_bd_path = os.path.join(fonts_path, 'arialbd.ttf')
    arial_i_path = os.path.join(fonts_path, 'ariali.ttf')

    if os.path.exists(arial_path):
        pdfmetrics.registerFont(TTFont('AppFont', arial_path))
    if os.path.exists(arial_bd_path):
        pdfmetrics.registerFont(TTFont('AppFont-Bold', arial_bd_path))
    else:
        pdfmetrics.registerFont(TTFont('AppFont-Bold', arial_path))
    if os.path.exists(arial_i_path):
        pdfmetrics.registerFont(TTFont('AppFont-Italic', arial_i_path))
    else:
        pdfmetrics.registerFont(TTFont('AppFont-Italic', arial_path))
    _FONTS_REGISTERED = True


def make_qr_image(data_text, size=65):
    """Tạo đối tượng Image của reportlab từ chuỗi QR."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return Image(buf, width=size, height=size)


def generate_prescription_pdf(prescription_id_or_code):
    """Xuất đơn thuốc điện tử chuẩn Bộ Y tế ra định dạng PDF bytes."""
    ensure_unicode_fonts()
    from models.pharmacy_model import PharmacyModel
    from models.medical_record_model import MedicalRecordModel

    dt = PharmacyModel.get_prescription_detail(prescription_id_or_code)
    if not dt:
        return None

    # Lấy thêm thông tin chi tiết khám bệnh và bệnh nhân
    pk = MedicalRecordModel.get_examination_by_id(dt.get('phieu_kham_id')) if dt.get('phieu_kham_id') else {}

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()
    normal_font = 'AppFont'
    bold_font = 'AppFont-Bold'
    italic_font = 'AppFont-Italic'

    style_header_org = ParagraphStyle('HeaderOrg', parent=styles['Normal'], fontName=bold_font, fontSize=9.5, leading=13, textTransform='uppercase', textColor=colors.HexColor('#0f766e'))
    style_header_addr = ParagraphStyle('HeaderAddr', parent=styles['Normal'], fontName=normal_font, fontSize=8, leading=11, textColor=colors.HexColor('#475569'))
    style_title = ParagraphStyle('Title', parent=styles['Normal'], fontName=bold_font, fontSize=15, leading=19, alignment=1, textColor=colors.HexColor('#0f172a'))
    style_sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName=italic_font, fontSize=8.5, leading=12, alignment=1, textColor=colors.HexColor('#64748b'))
    style_field_label = ParagraphStyle('FieldLabel', parent=styles['Normal'], fontName=bold_font, fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'))
    style_field_val = ParagraphStyle('FieldVal', parent=styles['Normal'], fontName=normal_font, fontSize=8.5, leading=12, textColor=colors.HexColor('#0f172a'))
    style_tbl_header = ParagraphStyle('TblH', parent=styles['Normal'], fontName=bold_font, fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor('#0f172a'))
    style_tbl_cell = ParagraphStyle('TblC', parent=styles['Normal'], fontName=normal_font, fontSize=8, leading=11, textColor=colors.HexColor('#1e293b'))
    style_tbl_cell_bold = ParagraphStyle('TblCB', parent=styles['Normal'], fontName=bold_font, fontSize=8, leading=11, textColor=colors.HexColor('#0f172a'))
    style_note = ParagraphStyle('Note', parent=styles['Normal'], fontName=italic_font, fontSize=8, leading=11, textColor=colors.HexColor('#475569'))

    elements = []

    # 1. Header cơ sở y tế và Barcode / QR Code
    org_text = Paragraph(
        "<b>PHÒNG KHÁM ĐA KHOA QUỐC TẾ H2T CARE+</b><br/>"
        "Địa chỉ: 140 Lê Trọng Tấn, P. Tây Thạnh, Q. Tân Phú, TP. Hồ Chí Minh<br/>"
        "Điện thoại: (028) 3816 1111 - Cấp cứu: 1900 8888<br/>"
        "Mã định danh liên thông Bộ Y Tế: <b>79032/SYT-GPHĐ</b>",
        style_header_addr
    )

    ma_don = dt.get('ma_don_thuoc') or f"DT{dt.get('id')}"
    bc = code128.Code128(ma_don, barHeight=22, barWidth=1.0)
    qr_img = make_qr_image(f"https://h2tcare.vn/don-thuoc/{ma_don}", size=52)

    code_block = [
        bc,
        Paragraph(f"<b>Mã đơn:</b> {ma_don}", style_field_label)
    ]

    header_table_data = [
        [org_text, qr_img, code_block]
    ]
    header_table = Table(header_table_data, colWidths=[280, 65, 175])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # 2. Tiêu đề đơn thuốc
    elements.append(Paragraph("ĐƠN THUỐC ĐIỆN TỬ", style_title))
    elements.append(Paragraph("(Bản chính thức theo Thông tư 04/2022/TT-BYT của Bộ Y tế)", style_sub_title))
    elements.append(Spacer(1, 12))

    # 3. Thông tin người bệnh và chẩn đoán
    ngay_sinh_str = str(pk.get('ngay_sinh') or '')[:10]
    nam_sinh = ngay_sinh_str[:4] if len(ngay_sinh_str) >= 4 else "----"
    tuoi_str = ""
    if nam_sinh != "----":
        try:
            tuoi_str = f"({datetime.now().year - int(nam_sinh)} tuổi)"
        except Exception:
            pass

    patient_info_rows = [
        [
            Paragraph("<b>Họ và tên:</b>", style_field_label),
            Paragraph(f"<b>{str(dt.get('ten_benh_nhan') or pk.get('ho_ten_benh_nhan') or '').upper()}</b>", style_field_val),
            Paragraph("<b>Năm sinh:</b>", style_field_label),
            Paragraph(f"{nam_sinh} {tuoi_str}", style_field_val),
            Paragraph("<b>Giới tính:</b>", style_field_label),
            Paragraph(str(pk.get('gioi_tinh') or 'Không rõ'), style_field_val),
        ],
        [
            Paragraph("<b>Mã người bệnh:</b>", style_field_label),
            Paragraph(str(dt.get('ma_benh_nhan') or pk.get('ma_benh_nhan') or '---'), style_field_val),
            Paragraph("<b>Thẻ BHYT:</b>", style_field_label),
            Paragraph(str(pk.get('so_bhyt') or 'Không có'), style_field_val),
            Paragraph("<b>Điện thoại:</b>", style_field_label),
            Paragraph(str(dt.get('sdt_benh_nhan') or pk.get('sdt') or '---'), style_field_val),
        ],
        [
            Paragraph("<b>Địa chỉ:</b>", style_field_label),
            Paragraph(str(pk.get('dia_chi') or '---'), style_field_val),
            "", "", "", ""
        ],
        [
            Paragraph("<b>Chẩn đoán:</b>", style_field_label),
            Paragraph(str(pk.get('chan_doan_icd') or pk.get('chan_doan_so_bo') or dt.get('chan_doan') or 'Khám bệnh đa khoa tổng quát'), style_field_val),
            "", "", "", ""
        ],
    ]

    p_table = Table(patient_info_rows, colWidths=[80, 160, 65, 80, 60, 75])
    p_table.setStyle(TableStyle([
        ('SPAN', (1, 2), (5, 2)),
        ('SPAN', (1, 3), (5, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 10))

    # 4. Bảng danh sách thuốc
    elements.append(Paragraph("<b>DANH SÁCH THUỐC ĐIỀU TRỊ:</b>", style_field_label))
    elements.append(Spacer(1, 5))

    items = dt.get('items', [])
    tbl_data = [
        [
            Paragraph("STT", style_tbl_header),
            Paragraph("Tên thuốc, nồng độ / hàm lượng", style_tbl_header),
            Paragraph("Số lượng", style_tbl_header),
            Paragraph("Đơn vị", style_tbl_header),
            Paragraph("Hướng dẫn sử dụng và liều dùng", style_tbl_header)
        ]
    ]

    for idx, item in enumerate(items, start=1):
        ten_t = item.get('ten_thuoc') or f"Thuốc #{item.get('thuoc_id')}"
        sl = item.get('so_luong') or 1
        dvt = item.get('don_vi_tinh') or 'Viên'
        lieu = item.get('lieu_dung') or item.get('cach_dung') or 'Theo chỉ dẫn của bác sĩ'
        tbl_data.append([
            Paragraph(str(idx), style_tbl_cell),
            Paragraph(f"<b>{ten_t}</b>", style_tbl_cell_bold),
            Paragraph(str(sl), style_tbl_cell_bold),
            Paragraph(str(dvt), style_tbl_cell),
            Paragraph(str(lieu), style_tbl_cell)
        ])

    drug_table = Table(tbl_data, colWidths=[30, 185, 48, 48, 209])
    drug_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'CENTER'),
    ]))
    elements.append(drug_table)
    elements.append(Spacer(1, 10))

    # 5. Lời dặn của bác sĩ và Ngày tái khám
    loi_dan = pk.get('loi_dan') or dt.get('ghi_chu') or "Uống thuốc đúng giờ, kiêng các chất kích thích và uống đủ 2 lít nước mỗi ngày."
    tai_kham = pk.get('ngay_tai_kham')
    tai_kham_text = f"Tái khám ngày: <b>{str(tai_kham)[:10]}</b> (hoặc khi có dấu hiệu bất thường)." if tai_kham else "Tái khám khi hết thuốc hoặc có dấu hiệu bất thường."

    note_rows = [
        [Paragraph(f"<b>Lời dặn bác sĩ:</b> {loi_dan}", style_field_val)],
        [Paragraph(f"<b>Lịch hẹn tái khám:</b> {tai_kham_text}", style_field_val)],
        [Paragraph("<i>Lưu ý: Đơn thuốc có giá trị mua/nhận thuốc trong thời hạn 05 ngày kể từ ngày kê đơn. Khám lại xin mang theo đơn này.</i>", style_note)]
    ]
    note_tbl = Table(note_rows, colWidths=[520])
    note_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(note_tbl)
    elements.append(Spacer(1, 15))

    # 6. Chữ ký bác sĩ kê đơn
    created_date = dt.get('ngay_tao') or datetime.now()
    if isinstance(created_date, str):
        try:
            created_dt = datetime.fromisoformat(created_date.replace('Z', ''))
        except Exception:
            created_dt = datetime.now()
    else:
        created_dt = created_date

    date_str = f"TP. Hồ Chí Minh, ngày {created_dt.day:02d} tháng {created_dt.month:02d} năm {created_dt.year}"
    doc_name = dt.get('ten_bac_si') or pk.get('ho_ten_bac_si') or "Bác sĩ điều trị"

    sign_data = [
        [
            Paragraph("<b>Người bệnh / Người giám hộ</b><br/><i>(Ký và ghi rõ họ tên)</i>", ParagraphStyle('SignP', parent=styles['Normal'], fontName=normal_font, fontSize=8.5, leading=12, alignment=1)),
            Paragraph(f"<i>{date_str}</i><br/><b>Bác sĩ khám bệnh</b><br/><i>(Ký, ghi rõ họ tên và đóng dấu)</i><br/><br/><br/><br/><b>{doc_name}</b>", ParagraphStyle('SignD', parent=styles['Normal'], fontName=normal_font, fontSize=8.5, leading=12, alignment=1))
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(KeepTogether(sign_table))

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


def generate_lab_order_pdf(order_id_or_code):
    """Xuất phiếu chỉ định Cận lâm sàng chuẩn Bộ Y tế ra định dạng PDF bytes."""
    ensure_unicode_fonts()
    from models.medical_record_model import MedicalRecordModel

    order = MedicalRecordModel.get_lab_order_detail(order_id_or_code)
    if not order:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()
    normal_font = 'AppFont'
    bold_font = 'AppFont-Bold'
    italic_font = 'AppFont-Italic'

    style_header_addr = ParagraphStyle('HeaderAddr2', parent=styles['Normal'], fontName=normal_font, fontSize=8, leading=11, textColor=colors.HexColor('#475569'))
    style_title = ParagraphStyle('Title2', parent=styles['Normal'], fontName=bold_font, fontSize=15, leading=19, alignment=1, textColor=colors.HexColor('#0f766e'))
    style_sub_title = ParagraphStyle('SubTitle2', parent=styles['Normal'], fontName=italic_font, fontSize=8.5, leading=12, alignment=1, textColor=colors.HexColor('#64748b'))
    style_field_label = ParagraphStyle('FieldLabel2', parent=styles['Normal'], fontName=bold_font, fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'))
    style_field_val = ParagraphStyle('FieldVal2', parent=styles['Normal'], fontName=normal_font, fontSize=8.5, leading=12, textColor=colors.HexColor('#0f172a'))
    style_tbl_header = ParagraphStyle('TblH2', parent=styles['Normal'], fontName=bold_font, fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor('#0f172a'))
    style_tbl_cell = ParagraphStyle('TblC2', parent=styles['Normal'], fontName=normal_font, fontSize=8, leading=11, textColor=colors.HexColor('#1e293b'))
    style_tbl_cell_bold = ParagraphStyle('TblCB2', parent=styles['Normal'], fontName=bold_font, fontSize=8, leading=11, textColor=colors.HexColor('#0f172a'))

    elements = []

    # 1. Header cơ sở y tế và Barcode / QR Code
    org_text = Paragraph(
        "<b>PHÒNG KHÁM ĐA KHOA QUỐC TẾ H2T CARE+</b><br/>"
        "Khoa Xét Nghiệm và Chẩn Đoán Hình Ảnh Y Khoa<br/>"
        "Địa chỉ: 140 Lê Trọng Tấn, P. Tây Thạnh, Q. Tân Phú, TP. Hồ Chí Minh<br/>"
        "Hotline CLS: (028) 3816 2222 - Bộ phận tiếp nhận mẫu 24/7",
        style_header_addr
    )

    ma_cd = order.get('ma_chi_dinh') or f"CD{order.get('id')}"
    bc = code128.Code128(ma_cd, barHeight=22, barWidth=1.0)
    qr_img = make_qr_image(f"https://h2tcare.vn/chi-dinh/{ma_cd}", size=52)

    code_block = [
        bc,
        Paragraph(f"<b>Mã chỉ định:</b> {ma_cd}", style_field_label)
    ]

    header_table = Table([[org_text, qr_img, code_block]], colWidths=[280, 65, 175])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # 2. Tiêu đề phiếu chỉ định
    elements.append(Paragraph("PHIẾU CHỈ ĐỊNH CẬN LÂM SÀNG", style_title))
    elements.append(Paragraph("(Xét nghiệm - Chẩn đoán hình ảnh - Thăm dò chức năng)", style_sub_title))
    elements.append(Spacer(1, 12))

    # 3. Thông tin người bệnh và chẩn đoán ban đầu
    ngay_sinh_str = str(order.get('ngay_sinh') or '')[:10]
    nam_sinh = ngay_sinh_str[:4] if len(ngay_sinh_str) >= 4 else "----"
    tuoi_str = ""
    if nam_sinh != "----":
        try:
            tuoi_str = f"({datetime.now().year - int(nam_sinh)} tuổi)"
        except Exception:
            pass

    patient_info_rows = [
        [
            Paragraph("<b>Họ và tên:</b>", style_field_label),
            Paragraph(f"<b>{str(order.get('ten_benh_nhan') or '').upper()}</b>", style_field_val),
            Paragraph("<b>Năm sinh:</b>", style_field_label),
            Paragraph(f"{nam_sinh} {tuoi_str}", style_field_val),
            Paragraph("<b>Giới tính:</b>", style_field_label),
            Paragraph(str(order.get('gioi_tinh') or 'Không rõ'), style_field_val),
        ],
        [
            Paragraph("<b>Mã người bệnh:</b>", style_field_label),
            Paragraph(str(order.get('ma_benh_nhan') or '---'), style_field_val),
            Paragraph("<b>Thẻ BHYT:</b>", style_field_label),
            Paragraph(str(order.get('so_bhyt') or 'Không có'), style_field_val),
            Paragraph("<b>Điện thoại:</b>", style_field_label),
            Paragraph(str(order.get('sdt_benh_nhan') or '---'), style_field_val),
        ],
        [
            Paragraph("<b>Địa chỉ:</b>", style_field_label),
            Paragraph(str(order.get('dia_chi') or '---'), style_field_val),
            "", "", "", ""
        ],
        [
            Paragraph("<b>Bác sĩ chỉ định:</b>", style_field_label),
            Paragraph(str(order.get('ten_bac_si') or 'Bác sĩ điều trị'), style_field_val),
            Paragraph("<b>Phòng chỉ định:</b>", style_field_label),
            Paragraph(str(order.get('phong_kham_bs') or 'Phòng khám chuyên khoa'), style_field_val),
            "", ""
        ],
        [
            Paragraph("<b>Chẩn đoán sơ bộ:</b>", style_field_label),
            Paragraph(str(order.get('chan_doan_icd') or order.get('chan_doan_so_bo') or 'Theo dõi lâm sàng'), style_field_val),
            "", "", "", ""
        ],
    ]

    p_table = Table(patient_info_rows, colWidths=[80, 160, 65, 80, 60, 75])
    p_table.setStyle(TableStyle([
        ('SPAN', (1, 2), (5, 2)),
        ('SPAN', (3, 3), (5, 3)),
        ('SPAN', (1, 4), (5, 4)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 10))

    # 4. Danh sách kỹ thuật chỉ định
    elements.append(Paragraph("<b>DANH SÁCH DỊCH VỤ KỸ THUẬT CẬN LÂM SÀNG CHỈ ĐỊNH:</b>", style_field_label))
    elements.append(Spacer(1, 5))

    items = order.get('items', [])
    tbl_data = [
        [
            Paragraph("STT", style_tbl_header),
            Paragraph("Tên kỹ thuật / dịch vụ", style_tbl_header),
            Paragraph("Loại dịch vụ", style_tbl_header),
            Paragraph("Phòng thực hiện", style_tbl_header),
            Paragraph("KTV phụ trách", style_tbl_header),
            Paragraph("Đơn giá", style_tbl_header)
        ]
    ]

    total_fee = 0
    for idx, it in enumerate(items, start=1):
        ten_dv = it.get('ten_dich_vu') or f"Dịch vụ #{it.get('dich_vu_id')}"
        loai = it.get('loai_dich_vu') or 'Cận lâm sàng'
        phong = it.get('ten_phong_ktv') or 'Phòng Kỹ thuật'
        ktv = it.get('ten_ktv_thuc_hien') or 'Theo phân bổ KTV'
        dg = float(it.get('don_gia') or 0)
        total_fee += dg
        tbl_data.append([
            Paragraph(str(idx), style_tbl_cell),
            Paragraph(f"<b>{ten_dv}</b>", style_tbl_cell_bold),
            Paragraph(str(loai), style_tbl_cell),
            Paragraph(str(phong), style_tbl_cell),
            Paragraph(str(ktv), style_tbl_cell),
            Paragraph(f"{dg:,.0f} đ", style_tbl_cell)
        ])

    tbl_data.append([
        Paragraph("<b>TỔNG CỘNG</b>", style_tbl_cell_bold),
        Paragraph("", style_tbl_cell),
        Paragraph("", style_tbl_cell),
        Paragraph("", style_tbl_cell),
        Paragraph("", style_tbl_cell),
        Paragraph(f"<b>{total_fee:,.0f} đ</b>", style_tbl_cell_bold)
    ])

    service_table = Table(tbl_data, colWidths=[28, 175, 75, 95, 85, 62])
    service_table.setStyle(TableStyle([
        ('SPAN', (0, -1), (4, -1)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
    ]))
    elements.append(service_table)
    elements.append(Spacer(1, 15))

    # 5. Chữ ký bác sĩ chỉ định và tiếp nhận KTV
    created_date = order.get('thoi_gian_chi_dinh') or datetime.now()
    if isinstance(created_date, str):
        try:
            created_dt = datetime.fromisoformat(created_date.replace('Z', ''))
        except Exception:
            created_dt = datetime.now()
    else:
        created_dt = created_date

    date_str = f"TP. Hồ Chí Minh, ngày {created_dt.day:02d} tháng {created_dt.month:02d} năm {created_dt.year}"
    doc_name = order.get('ten_bac_si') or "Bác sĩ điều trị"

    sign_data = [
        [
            Paragraph("<b>Kỹ thuật viên tiếp nhận mẫu</b><br/><i>(Ký và ghi rõ họ tên)</i>", ParagraphStyle('SignKTV', parent=styles['Normal'], fontName=normal_font, fontSize=8.5, leading=12, alignment=1)),
            Paragraph(f"<i>{date_str}</i><br/><b>Bác sĩ chỉ định</b><br/><i>(Ký, ghi rõ họ tên và đóng dấu)</i><br/><br/><br/><br/><b>{doc_name}</b>", ParagraphStyle('SignDoc', parent=styles['Normal'], fontName=normal_font, fontSize=8.5, leading=12, alignment=1))
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(KeepTogether(sign_table))

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
