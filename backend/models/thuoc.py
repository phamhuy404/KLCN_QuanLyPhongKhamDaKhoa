from sqlalchemy import Column, Integer, String, Numeric, Boolean
from database import Base

class Thuoc(Base):
    __tablename__ = 'thuoc'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_thuoc = Column(String(30), unique=True, nullable=False)
    ten_thuoc = Column(String(255), nullable=False)
    hoat_chat = Column(String(255))
    ham_luong = Column(String(100))
    don_vi_tinh = Column(String(50), nullable=False)
    don_gia = Column(Numeric(12, 2), nullable=False, default=0.00)
    so_luong_ton = Column(Integer, default=0)
    hang_san_xuat = Column(String(150))
    nuoc_san_xuat = Column(String(100))
    huong_dan_su_dung = Column(String(255))
    trang_thai = Column(Boolean, default=True)