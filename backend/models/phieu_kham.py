from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base

class PhieuKham(Base):
    __tablename__ = 'phieu_kham'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_phieu = Column(String(30), unique=True, nullable=False)
    benh_nhan_id = Column(Integer, ForeignKey('benh_nhan.id'), nullable=False)
    bac_si_id = Column(Integer, ForeignKey('bac_si.id'), nullable=False)
    phong_kham_id = Column(Integer, ForeignKey('phong_kham.id'), nullable=False)
    lich_hen_id = Column(Integer, ForeignKey('lich_hen.id'))
    thoi_gian_kham = Column(DateTime, default=datetime.utcnow)
    ly_do_kham = Column(Text)
    trieu_chung = Column(Text)
    chan_doan_so_bo = Column(Text)
    chan_doan_icd = Column(String(255))
    huong_dieu_tri = Column(Text)
    loi_dan = Column(Text)
    ngay_tai_kham = Column(Date)
    trang_thai = Column(String(50), default='Hoàn thành')