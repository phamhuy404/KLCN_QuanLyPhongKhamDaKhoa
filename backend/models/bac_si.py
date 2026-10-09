from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Text
from database import Base

class BacSi(Base):
    __tablename__ = 'bac_si'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nhan_vien_id = Column(Integer, ForeignKey('nhan_vien.id', ondelete='CASCADE'), unique=True, nullable=False)
    chuyen_khoa_id = Column(Integer, ForeignKey('chuyen_khoa.id'), nullable=False)
    phong_kham_chinh_id = Column(Integer, ForeignKey('phong_kham.id'))
    hoc_vi = Column(String(50), default='Bác sĩ')
    kinh_nghiem = Column(Text)
    avatar = Column(String(255), default='default_doctor.png')
    gia_kham = Column(Numeric(12, 2), default=150000.00)
    trang_thai_lam_viec = Column(String(50), default='Đang làm việc')