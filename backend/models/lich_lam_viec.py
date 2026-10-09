from sqlalchemy import Column, Integer, Date, Time, ForeignKey
from database import Base

class LichLamViec(Base):
    __tablename__ = 'lich_lam_viec'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bac_si_id = Column(Integer, ForeignKey('bac_si.id', ondelete='CASCADE'), nullable=False)
    phong_kham_id = Column(Integer, ForeignKey('phong_kham.id'), nullable=False)
    ngay_lam = Column(Date, nullable=False)
    ca_lam = Column(Integer, nullable=False)
    gio_bat_dau = Column(Time)
    gio_ket_thuc = Column(Time)
    so_luong_kham_toi_da = Column(Integer, default=20)
    so_luong_da_dang_ky = Column(Integer, default=0)