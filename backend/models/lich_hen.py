from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base

class LichHen(Base):
    __tablename__ = 'lich_hen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_lich_hen = Column(String(30), unique=True, nullable=False)
    benh_nhan_id = Column(Integer, ForeignKey('benh_nhan.id', ondelete='CASCADE'), nullable=False)
    bac_si_id = Column(Integer, ForeignKey('bac_si.id'))
    chuyen_khoa_id = Column(Integer, ForeignKey('chuyen_khoa.id'), nullable=False)
    phong_kham_id = Column(Integer, ForeignKey('phong_kham.id'))
    ngay_hen = Column(Date, nullable=False)
    gio_hen = Column(Time, nullable=False)
    ly_do_kham = Column(Text)
    loai_lich_hen = Column(Integer, default=1)
    trang_thai = Column(String(50), default='Chờ xác nhận')
    ngay_dat = Column(DateTime, default=datetime.utcnow)