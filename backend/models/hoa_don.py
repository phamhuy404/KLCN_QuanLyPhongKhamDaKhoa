from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from database import Base

class HoaDon(Base):
    __tablename__ = 'hoa_don'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_hoa_don = Column(String(30), unique=True, nullable=False)
    benh_nhan_id = Column(Integer, ForeignKey('benh_nhan.id'), nullable=False)
    phieu_kham_id = Column(Integer, ForeignKey('phieu_kham.id'))
    tong_tien = Column(Numeric(12, 2), nullable=False, default=0.00)
    tien_bhyt = Column(Numeric(12, 2), default=0.00)
    giam_gia = Column(Numeric(12, 2), default=0.00)
    thanh_tien = Column(Numeric(12, 2), nullable=False, default=0.00)
    hinh_thuc_thanh_toan = Column(String(50), default='Tiền mặt')
    trang_thai = Column(String(50), default='Chưa thanh toán')
    thoi_gian_thanh_toan = Column(DateTime)
    nhan_vien_thu = Column(String(100), default='Trần Thị Mai')