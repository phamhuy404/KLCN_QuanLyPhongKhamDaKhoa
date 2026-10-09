from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from database import Base

class ChiTietChiDinh(Base):
    __tablename__ = 'chi_tiet_chi_dinh'
    id = Column(Integer, primary_key=True, autoincrement=True)
    phieu_chi_dinh_id = Column(Integer, ForeignKey('phieu_chi_dinh.id', ondelete='CASCADE'), nullable=False)
    dich_vu_id = Column(Integer, ForeignKey('dich_vu.id'), nullable=False)
    ket_qua = Column(Text)
    file_ket_qua = Column(String(255))
    ktv_thuc_hien = Column(String(100))
    thoi_gian_thuc_hien = Column(DateTime)
    trang_thai = Column(String(50), default='Chờ làm')