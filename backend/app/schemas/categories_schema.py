from pydantic import BaseModel
from typing import Optional,List
from decimal import Decimal

class CategoryBase(BaseModel):
    category_id: int
    name: str
    parent_category_id: Optional[int] = None  # top-level categories have no parent

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    category_id: int

    class Config:
        orm_mode = True  # Pydantic v2

class CategoryResponse(CategoryBase):
    class Config:
        from_attributes = True

class CategoryTreeResponse(BaseModel):
    category_id: int
    category_name: str
    children: List["CategoryTreeResponse"] = []

    class Config:
        from_attributes = True

CategoryTreeResponse.model_rebuild()

class CategoryPerformanceResponse(BaseModel):
    category_id: int
    category_name: str
    total_articles: int
    total_items_sold: float
    total_revenue: Decimal
    avg_rating: Decimal | None = None


    class Config:
        from_attributes = True