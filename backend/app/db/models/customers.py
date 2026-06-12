from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": "niche_data"}
    customer_id = Column(String(255), primary_key=True, index=True)
    age = Column(Integer)
    postal_code = Column(String(20))
    club_member_status = Column(String(100))
    fashion_news_frequency = Column(String(100))
    active = Column(Boolean)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    signup_date = Column(DateTime, default=datetime.utcnow)
    gender = Column(String(10))
    loyalty_score = Column(Float)
    password_hash = Column(String(255))
    phone = Column(String(255))
    address = Column(String(255))
