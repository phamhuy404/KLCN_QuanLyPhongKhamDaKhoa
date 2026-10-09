from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base

class BaiViet(Base):
    __tablename__ = 'bai_viet'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tac_gia_id = Column(Integer, ForeignKey('nhan_vien.id'))
    tieu_de = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    danh_muc = Column(String(100), default='Cẩm Nang Y Tế')
    tom_tat = Column(Text)
    noi_dung = Column(Text)
    hinh_anh = Column(String(255))
    luot_xem = Column(Integer, default=0)
    ngay_dang = Column(DateTime, default=datetime.utcnow)
    trang_thai = Column(Boolean, default=True)