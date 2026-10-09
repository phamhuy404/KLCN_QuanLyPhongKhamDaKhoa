from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from database import Base

class DichVu(Base):
    __tablename__ = 'dich_vu'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chuyen_khoa_id = Column(Integer, ForeignKey('chuyen_khoa.id'))
    ma_dich_vu = Column(String(30), unique=True, nullable=False)
    ten_dich_vu = Column(String(255), nullable=False)
    loai_dich_vu = Column(String(50), default='Khám bệnh')
    don_gia = Column(Numeric(12, 2), nullable=False, default=0.00)
    bhyt_chi_tra_pt = Column(Integer, default=0)
    mo_ta = Column(String(255))