from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    customer_id: str
    article_id: str
    review_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    reviewer_name: Optional[str] = None
    customer_name: Optional[str] = None

    model_config = {"from_attributes": True}

class ReviewCreate(BaseModel):
    customer_id: str
    article_id: str
    review_text: str   # text is required for auto rating

class ReviewOut(ReviewBase):
    review_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class ReviewUpdate(BaseModel):
    review_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)

    model_config = {"from_attributes": True}
