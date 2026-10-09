from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from datetime import date
from database import Base

class NhanVien(Base):
    __tablename__ = 'nhan_vien'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tai_khoan_id = Column(Integer, ForeignKey('tai_khoan.id', ondelete='CASCADE'), unique=True, nullable=False)
    ma_nhan_vien = Column(String(20), unique=True, nullable=False)
    ho_ten = Column(String(100), nullable=False)
    gioi_tinh = Column(Boolean, default=True)
    ngay_sinh = Column(Date)
    sdt = Column(String(15), unique=True, nullable=False)
    email = Column(String(100))
    cccd = Column(String(20), unique=True)
    dia_chi = Column(String(255))
    chuc_vu = Column(String(100), nullable=False)
    ngay_vao_lam = Column(Date, default=date.today)
    trang_thai = Column(Boolean, default=True)