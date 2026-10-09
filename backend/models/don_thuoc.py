from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base

class DonThuoc(Base):
    __tablename__ = 'don_thuoc'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_don_thuoc = Column(String(30), unique=True, nullable=False)
    phieu_kham_id = Column(Integer, ForeignKey('phieu_kham.id', ondelete='CASCADE'), unique=True, nullable=False)
    bac_si_id = Column(Integer, ForeignKey('bac_si.id'), nullable=False)
    thoi_gian_ke = Column(DateTime, default=datetime.utcnow)
    loi_dan = Column(Text)
    trang_thai = Column(String(50), default='Đã cấp thuốc')