from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.sql import func
from app.db.database import Base

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "niche_data"}

    order_id = Column(Integer, primary_key=True, autoincrement=True)

    customer_id = Column(String, nullable=False)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(Text, nullable=False)
    shipping_address = Column(Text, nullable=False)