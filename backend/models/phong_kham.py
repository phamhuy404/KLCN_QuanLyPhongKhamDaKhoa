from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class PhongKham(Base):
    __tablename__ = 'phong_kham'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chuyen_khoa_id = Column(Integer, ForeignKey('chuyen_khoa.id'), nullable=False)
    ma_phong = Column(String(20), unique=True, nullable=False)
    ten_phong = Column(String(100), nullable=False)
    vi_tri_tang = Column(String(50), default='Tầng 1')
    trang_thai = Column(Boolean, default=True)