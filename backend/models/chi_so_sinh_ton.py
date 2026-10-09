from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from database import Base

class ChiSoSinhTon(Base):
    __tablename__ = 'chi_so_sinh_ton'
    id = Column(Integer, primary_key=True, autoincrement=True)
    benh_nhan_id = Column(Integer, ForeignKey('benh_nhan.id', ondelete='CASCADE'), nullable=False)
    mach = Column(String(20), default='75 lần/phút')
    nhiet_do = Column(String(20), default='36.8 °C')
    huyet_ap = Column(String(20), default='120/80 mmHg')
    spo2 = Column(String(20), default='99 %')
    nhip_tho = Column(String(20), default='18 lần/phút')
    chieu_cao = Column(String(20), default='170 cm')
    can_nang = Column(String(20), default='65 kg')
    bmi = Column(String(50), default='22.5 (Bình thường)')
    thoi_gian_do = Column(DateTime, default=datetime.utcnow)
    ghi_chu = Column(String(255))