from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class ChiTietDonThuoc(Base):
    __tablename__ = 'chi_tiet_don_thuoc'
    id = Column(Integer, primary_key=True, autoincrement=True)
    don_thuoc_id = Column(Integer, ForeignKey('don_thuoc.id', ondelete='CASCADE'), nullable=False)
    thuoc_id = Column(Integer, ForeignKey('thuoc.id'), nullable=False)
    so_luong = Column(Integer, nullable=False, default=1)
    lieu_dung = Column(String(100))
    cach_dung = Column(String(255))