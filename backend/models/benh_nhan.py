from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Text
from datetime import date
from database import Base

class BenhNhan(Base):
    __tablename__ = 'benh_nhan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tai_khoan_id = Column(Integer, ForeignKey('tai_khoan.id', ondelete='SET NULL'))
    ma_benh_nhan = Column(String(20), unique=True, nullable=False)
    ho_ten = Column(String(100), nullable=False)
    ngay_sinh = Column(Date, nullable=False)
    gioi_tinh = Column(String(10), default='Nam', nullable=False)
    sdt = Column(String(15), nullable=False)
    email = Column(String(100))
    cccd = Column(String(20))
    bhyt = Column(String(30))
    dia_chi = Column(String(255))
    nhom_mau = Column(String(10), default='Chưa rõ')
    di_ung = Column(Text)
    tien_su_benh = Column(Text)
    tien_su_gia_dinh = Column(Text)
    nguoi_than_ho_ten = Column(String(100))
    nguoi_than_sdt = Column(String(15))
    nguoi_than_quan_he = Column(String(50))
    co_tai_khoan = Column(Boolean, default=False)
    ngay_tao = Column(Date, default=date.today)