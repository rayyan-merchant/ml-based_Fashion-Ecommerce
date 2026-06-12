from typing import List, Optional

from pydantic import BaseModel, Field


ALLOWED_SECTIONS = ["men", "women", "kids", "unisex", "accessories"]
ALLOWED_CATEGORIES = ["hoodie", "jacket", "trouser", "beanie", "accessory", "other"]
ALLOWED_SORT_OPTIONS = ["price_low_high", "price_high_low", "popular", "newest", "best_rated"]


class SectionItem(BaseModel):
    id: int = Field(..., description="Internal section identifier")
    name: str = Field(..., description="Canonical section key (e.g. 'men')")
    display: str = Field(..., description="Display label for navigation")
    total_products: int = Field(..., description="Total number of products in this section")


class SectionsResponse(BaseModel):
    sections: List[SectionItem]


class SectionProduct(BaseModel):
    article_id: str
    prod_name: str
    price: float
    category: str
    section_name: str
    stock: int
    average_rating: Optional[float] = None
    total_reviews: int
    popularity_score: int
    image_path: Optional[str] = None    


class SectionProductsResponse(BaseModel):
    section: str
    total_products: int
    products: List[SectionProduct]


class SectionCategorySummary(BaseModel):
    category: str
    total_products: int


class SectionCategoriesResponse(BaseModel):
    section: str
    categories: List[SectionCategorySummary]


class CategoryProduct(BaseModel):
    article_id: str
    prod_name: str
    price: float
    stock: int
    average_rating: Optional[float] = None
    total_reviews: int
    popularity_score: int
    image_path: Optional[str] = None    


class CategoryProductsResponse(BaseModel):
    section: str
    category: str
    sorting: str
    total_products: int
    products: List[CategoryProduct]


class FilterRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class PopularityRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None


class FilterOptions(BaseModel):
    price: FilterRange
    rating: FilterRange
    popularity: PopularityRange


class FilterOptionsResponse(BaseModel):
    category: str
    filters: FilterOptions


class FilterSortRequest(BaseModel):
    price_min: float = Field(..., ge=0)
    price_max: float = Field(..., ge=0)
    sort_option: str


class FilterSortProduct(BaseModel):
    article_id: str
    prod_name: str
    price: float
    stock: int
    average_rating: Optional[float] = None
    total_reviews: int
    popularity_score: int
    image_path: Optional[str] = None    


class FilterSortResponse(BaseModel):
    products: List[FilterSortProduct]

