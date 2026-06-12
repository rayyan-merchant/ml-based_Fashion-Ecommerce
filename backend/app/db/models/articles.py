from sqlalchemy.sql import func
from app.db.database import Base  # using the shared Base class
from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP

class Article(Base):
    __tablename__ = "articles"
    __table_args__ = {"schema": "niche_data"}
    article_id = Column(String, primary_key=True, index=True)
    product_code = Column(Integer)
    prod_name = Column(String(255))
    product_type_name = Column(String(255))
    product_group_name = Column(String(255))
    graphical_appearance_name = Column(String(255))
    colour_group_name = Column(String(255))
    department_no = Column(Integer)
    department_name = Column(String(255))
    index_name = Column(String(255))
    index_group_name = Column(String(255))
    section_name = Column(String(255))
    garment_group_name = Column(String(255))
    detail_desc = Column(String(255))
    price = Column(Float)
    stock = Column(Integer)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    image_path = Column(String(255))
    sale_discount_pct = Column(Integer, nullable=False, default=0)
    sale_starts_at = Column(TIMESTAMP(timezone=True))
    sale_ends_at = Column(TIMESTAMP(timezone=True))
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated = Column(TIMESTAMP(timezone=True), onupdate=func.now())
