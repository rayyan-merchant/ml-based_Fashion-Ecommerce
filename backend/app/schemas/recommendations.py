from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RecommendationItemResponse(BaseModel):
    """Single recommendation item with score and rank"""
    article_id: str
    score: float
    rank: int

    class Config:
        from_attributes = True


class UserRecommendationsResponse(BaseModel):
    """User-specific recommendations response"""
    customer_id: str
    recommendations: List[RecommendationItemResponse]
    count: int
    recommendation_type: str
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ItemSimilarityResponse(BaseModel):
    """Similar items for a given article"""
    article_id: str
    similar_items: List[RecommendationItemResponse]
    count: int
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrendingResponse(BaseModel):
    """Global trending articles"""
    trending_items: List[RecommendationItemResponse]
    count: int
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SimilarUsersRecommendationsResponse(BaseModel):
    """Recommendations from similar users"""
    customer_id: str
    recommendations: List[RecommendationItemResponse]
    count: int
    recommendation_type: str
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
