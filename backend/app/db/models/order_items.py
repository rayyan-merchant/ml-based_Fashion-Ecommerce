from sqlalchemy import Column, Integer, String,Float,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

# ---------- ORDER ITEMS ----------
class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {"schema": "niche_data"}
    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    article_id = Column(String(255), ForeignKey("articles.article_id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    line_total = Column(Float)

