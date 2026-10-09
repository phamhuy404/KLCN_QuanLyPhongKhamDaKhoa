from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from database import Base

class ChiTietHoaDon(Base):
    __tablename__ = 'chi_tiet_hoa_don'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hoa_don_id = Column(Integer, ForeignKey('hoa_don.id', ondelete='CASCADE'), nullable=False)
    loai_khoan_thu = Column(String(50), nullable=False)
    ten_khoan_thu = Column(String(255), nullable=False)
    tham_chieu_id = Column(Integer)
    so_luong = Column(Integer, nullable=False, default=1)
    don_gia = Column(Numeric(12, 2), nullable=False, default=0.00)
    thanh_tien = Column(Numeric(12, 2), nullable=False, default=0.00)