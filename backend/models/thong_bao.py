from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base

class ThongBao(Base):
    __tablename__ = 'thong_bao'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tai_khoan_id = Column(Integer, ForeignKey('tai_khoan.id', ondelete='CASCADE'), nullable=False)
    tieu_de = Column(String(255), nullable=False)
    noi_dung = Column(Text, nullable=False)
    loai_thong_bao = Column(String(50), default='Hệ thống')
    da_doc = Column(Boolean, default=False)
    thoi_gian_tao = Column(DateTime, default=datetime.utcnow)