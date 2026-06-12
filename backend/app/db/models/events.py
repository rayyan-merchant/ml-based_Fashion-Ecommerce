from sqlalchemy import Column, Integer, String,Boolean,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "niche_data"}
    event_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255))
    customer_id = Column(String(255), ForeignKey("customers.customer_id"))
    article_id = Column(String(255), ForeignKey("articles.article_id"))
    event_type = Column(String(100))
    campaign_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    order_id = Column(Integer,ForeignKey("orders.order_id"))