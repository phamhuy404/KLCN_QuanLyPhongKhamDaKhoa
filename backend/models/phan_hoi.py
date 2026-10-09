from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base

class PhanHoi(Base):
    __tablename__ = 'phan_hoi'
    id = Column(Integer, primary_key=True, autoincrement=True)
    benh_nhan_id = Column(Integer, ForeignKey('benh_nhan.id', ondelete='CASCADE'), nullable=False)
    phieu_kham_id = Column(Integer, ForeignKey('phieu_kham.id'))
    diem_danh_gia = Column(Integer, nullable=False) # Check constraint BETWEEN 1 AND 5 can be handled in application logic or via CheckConstraint
    noi_dung = Column(Text)
    thoi_gian = Column(DateTime, default=datetime.utcnow)