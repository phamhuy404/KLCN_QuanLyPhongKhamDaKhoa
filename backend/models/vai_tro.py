from sqlalchemy import Column, Integer, String
from database import Base

class VaiTro(Base):
    __tablename__ = 'vai_tro'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ma_vai_tro = Column(String(30), unique=True, nullable=False)
    ten_vai_tro = Column(String(50), nullable=False)
    mo_ta = Column(String(255))