from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base
from datetime import datetime

class Wishlist(Base):
    __tablename__ = "wishlist"
    __table_args__ = {"schema": "niche_data"}
    wishlist_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"))
    article_id = Column(String(255), ForeignKey("articles.article_id"))
    added_at = Column(DateTime, default=datetime.utcnow)
