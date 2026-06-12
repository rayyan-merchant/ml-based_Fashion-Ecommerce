from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "niche_data"}
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)

    # Optional: self-referencing relationship for parent/child categories
    parent_category = relationship("Category", remote_side=[category_id])
