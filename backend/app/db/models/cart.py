from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
class Cart(Base):
    __tablename__ = "cart"
    __table_args__ = {"schema": "niche_data"}
    cart_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"))
    article_id = Column(String(255), ForeignKey("articles.article_id"))
    quantity = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)
