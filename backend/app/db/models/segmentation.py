from sqlalchemy import Column, String, Integer, DateTime
from app.db.database import Base

class CustomerSegment(Base):
    __tablename__ = "customer_segments"
    __table_args__ = {"schema": "niche_data"}

    customer_id = Column(String, primary_key=True)
    segment = Column(Integer)
    updated_at = Column(DateTime)
