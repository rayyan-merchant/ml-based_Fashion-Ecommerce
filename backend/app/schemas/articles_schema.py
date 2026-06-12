from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArticleBase(BaseModel):
    article_id:str
    product_code: int
    prod_name: str
    product_type_name: str
    product_group_name: str
    graphical_appearance_name: str
    colour_group_name: str
    department_no: int
    department_name: str
    index_name: str
    index_group_name: str
    section_name: str
    garment_group_name: str
    detail_desc: str
    price: float
    stock: int
    category_id: int | None = None
    sale_discount_pct: int = 0
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None

class ArticleCreate(ArticleBase):
    article_id: str

class ArticleResponse(ArticleBase):
    article_id: str
    product_code: int
    prod_name: str
    product_type_name: str
    product_group_name: str
    graphical_appearance_name: str
    colour_group_name: str
    department_no: int
    department_name: str
    index_name: str
    index_group_name: str
    section_name: str
    garment_group_name: str
    detail_desc: str | None = None
    price: float
    stock: int
    category_id: int | None = None
    image_path: str | None = None
    sale_discount_pct: int = 0
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProductOut(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, article):
        # Convert image_path to image_url
        image_url = None
        if hasattr(article, 'image_path') and article.image_path:
            image_url = r"C:\Users\rija\Desktop\db-proj\backend\filtered_images{article.image_path}"
        
        return cls(
            product_id=article.article_id,
            name=article.prod_name,
            price=article.price,
            image_url=image_url
        )

class ArticleUpdate(BaseModel):
    article_id: Optional[str] = None
    product_code: Optional[int] = None
    prod_name: Optional[str] = None
    product_type_name: Optional[str] = None
    product_group_name: Optional[str] = None
    graphical_appearance_name: Optional[str] = None
    colour_group_name: Optional[str] = None
    department_no: Optional[int] = None
    department_name: Optional[str] = None
    index_name: Optional[str] = None
    index_group_name: Optional[str] = None
    section_name: Optional[str] = None
    garment_group_name: Optional[str] = None
    detail_desc: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    sale_discount_pct: Optional[int] = None
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None


# ANALYTICS SCHEMAS
class ArticlePerformanceResponse(BaseModel):
    article_id: str
    prod_name: Optional[str]
    product_type_name: Optional[str]
    product_group_name: Optional[str]
    section_name: Optional[str]
    colour_group_name: Optional[str]
    price: Optional[float]

    total_views: int
    total_clicks: int
    total_wishlist: int
    total_cart_adds: int
    total_purchases: int
    
    avg_rating: Optional[float]
    total_reviews: int
    total_revenue: float

    class Config:
        orm_mode = True


class ArticleDemandTrendResponse(BaseModel):
    article_id: str
    month: datetime
    total_quantity_sold: int
    total_revenue: float
    class Config:
        orm_mode = True


class ArticleInventoryResponse(BaseModel):
    article_id: str
    prod_name: str
    stock: int
    stock_status: str

    class Config:
        orm_mode = True


class ArticleFunnelMetricsResponse(BaseModel):
    views: int
    clicks: int
    cart_adds: int
    purchases: int
    view_to_click_rate: int
    click_to_cart_rate: int
    cart_to_purchase_rate: int

    class Config:
        orm_mode = True
