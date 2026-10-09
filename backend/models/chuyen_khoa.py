from sqlalchemy import Column, Integer, String, Numeric, Text
from database import Base

class ChuyenKhoa(Base):
    __tablename__ = 'chuyen_khoa'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_khoa = Column(String(20), unique=True, nullable=False)
    ten_khoa = Column(String(100), nullable=False)
    mo_ta = Column(Text)
    icon = Column(String(100), default='fa-stethoscope')
    gia_kham_mac_dinh = Column(Numeric(12, 2), default=150000.00)