from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from database import Base

class TaiKhoan(Base):
    __tablename__ = 'tai_khoan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vai_tro_id = Column(Integer, ForeignKey('vai_tro.id'), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100))
    sdt = Column(String(15))
    trang_thai = Column(Boolean, default=True)
    ngay_tao = Column(DateTime, default=datetime.utcnow)
    lan_dang_nhap_cuoi = Column(DateTime)