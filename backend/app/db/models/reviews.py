from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from app.db.database import Base
from datetime import datetime

# ---------- REVIEWS ----------
class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = {"schema": "niche_data"}
    review_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"))
    article_id = Column(String(255), ForeignKey("articles.article_id"))
    rating = Column(Integer)
    review_text = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

