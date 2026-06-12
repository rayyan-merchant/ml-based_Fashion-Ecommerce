from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"schema": "niche_data"}
    transaction_id = Column(Integer, primary_key=True, index=True)
    t_dat = Column(Date)
    customer_id = Column(String(255), ForeignKey("customers.customer_id"))
    article_id = Column(String(255), ForeignKey("articles.article_id"))
    price = Column(Float)
    sales_channel_id = Column(Integer)