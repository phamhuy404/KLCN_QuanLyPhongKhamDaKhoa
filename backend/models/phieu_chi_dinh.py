from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from database import Base

class PhieuChiDinh(Base):
    __tablename__ = 'phieu_chi_dinh'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_chi_dinh = Column(String(30), unique=True, nullable=False)
    phieu_kham_id = Column(Integer, ForeignKey('phieu_kham.id', ondelete='CASCADE'), nullable=False)
    bac_si_id = Column(Integer, ForeignKey('bac_si.id'), nullable=False)
    thoi_gian_chi_dinh = Column(DateTime, default=datetime.utcnow)
    ghi_chu = Column(String(255))
    trang_thai = Column(String(50), default='Chờ thực hiện')