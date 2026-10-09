from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class HomThuGopY(Base):
    __tablename__ = 'hom_thu_gop_y'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ho_ten = Column(String(100), nullable=False)
    email = Column(String(100))
    sdt = Column(String(15))
    chu_de = Column(String(200))
    noi_dung = Column(Text, nullable=False)
    ngay_gui = Column(DateTime, default=datetime.utcnow)
    trang_thai = Column(String(50), default='Chưa xử lý')