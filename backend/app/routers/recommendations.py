"""
Recommendations Router - API endpoints for recommendation features
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models.customers import Customer
from app.schemas.recommendations import (
    UserRecommendationsResponse,
    ItemSimilarityResponse,
    TrendingResponse,
    SimilarUsersRecommendationsResponse,
    RecommendationItemResponse
)
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instance (loaded at app startup)
_recommendation_service: RecommendationService = None


def set_recommendation_service(service: RecommendationService):
    """Set the global recommendation service (called from main.py)"""
    global _recommendation_service
    _recommendation_service = service
    logger.info("Recommendation service registered")


def get_recommendation_service() -> RecommendationService:
    """Dependency to get recommendation service"""
    if _recommendation_service is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation service not initialized"
        )
    if not _recommendation_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Recommendation service not ready"
        )
    return _recommendation_service


@router.get("/health", tags=["Recommendations"])
async def recommendations_health(
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Health check for recommendation service"""
    return service.get_service_info()


@router.get(
    "/user/{customer_id}",
    response_model=UserRecommendationsResponse,
    tags=["Recommendations"]
)
async def get_user_recommendations(
    customer_id: str,
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get 'You May Also Like' personalized recommendations for a customer.
    
    Uses collaborative filtering model trained on transaction history.
    
    **Parameters:**
    - `customer_id`: The customer ID (from URL path)
    - `limit`: Number of recommendations (1-50, default: 12)
    
    **Returns:**
    - `customer_id`: The requested customer ID
    - `recommendations`: List of recommended articles with scores and ranks
    - `count`: Number of recommendations returned
    - `recommendation_type`: "personalized"
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `404`: Customer not found
    - `503`: Service not ready
    """
    # Verify customer exists
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found"
        )
    
    # Get recommendations from service
    recs = service.get_user_recommendations(customer_id, limit=limit)
    
    # If no recommendations, return empty but valid response
    if not recs:
        logger.info(f"No recommendations found for customer {customer_id}")
        return UserRecommendationsResponse(
            customer_id=customer_id,
            recommendations=[],
            count=0,
            recommendation_type="personalized",
            generated_at=datetime.now()
        )
    
    # Convert to response format
    recommendation_items = [
        RecommendationItemResponse(**rec) for rec in recs
    ]
    
    return UserRecommendationsResponse(
        customer_id=customer_id,
        recommendations=recommendation_items,
        count=len(recommendation_items),
        recommendation_type="personalized",
        generated_at=datetime.now()
    )


@router.get(
    "/similar-users/{customer_id}",
    response_model=SimilarUsersRecommendationsResponse,
    tags=["Recommendations"]
)
async def get_customers_also_bought(
    customer_id: str,
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get 'Customers Also Bought' recommendations based on similar users.
    
    Finds customers with similar purchase patterns and recommends items
    that those similar customers purchased.
    
    **Parameters:**
    - `customer_id`: The customer ID (from URL path)
    - `limit`: Number of recommendations (1-50, default: 12)
    
    **Returns:**
    - `customer_id`: The requested customer ID
    - `recommendations`: Items purchased by similar customers
    - `count`: Number of recommendations returned
    - `recommendation_type`: "similar_users"
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `404`: Customer not found
    - `503`: Service not ready
    """
    # Verify customer exists
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found"
        )
    
    # Get recommendations from similar users
    recs = service.get_similar_users_recommendations(customer_id, limit=limit)
    
    if not recs:
        logger.info(f"No similar user recommendations for customer {customer_id}")
        return SimilarUsersRecommendationsResponse(
            customer_id=customer_id,
            recommendations=[],
            count=0,
            recommendation_type="similar_users",
            generated_at=datetime.now()
        )
    
    recommendation_items = [
        RecommendationItemResponse(**rec) for rec in recs
    ]
    
    return SimilarUsersRecommendationsResponse(
        customer_id=customer_id,
        recommendations=recommendation_items,
        count=len(recommendation_items),
        recommendation_type="similar_users",
        generated_at=datetime.now()
    )


@router.get(
    "/item-similar/{article_id}",
    response_model=ItemSimilarityResponse,
    tags=["Recommendations"]
)
async def get_item_similarity(
    article_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get 'Often Bought Together' - items similar to a given article.
    
    Uses item-item similarity matrix from collaborative filtering model
    to find articles that are frequently bought together.
    
    **Parameters:**
    - `article_id`: The article ID (from URL path)
    - `limit`: Number of similar items (1-50, default: 10)
    
    **Returns:**
    - `article_id`: The requested article ID
    - `similar_items`: List of similar articles with scores and ranks
    - `count`: Number of similar items returned
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `503`: Service not ready
    
    **Note:**
    If article is not in the model, returns empty list (no 404).
    This allows frontend to gracefully handle unknown articles.
    """
    # Get similar items from service
    recs = service.get_similar_items(article_id, limit=limit)
    
    if not recs:
        logger.debug(f"No similar items found for article {article_id}")
        return ItemSimilarityResponse(
            article_id=article_id,
            similar_items=[],
            count=0,
            generated_at=datetime.now()
        )
    
    similar_items = [
        RecommendationItemResponse(**rec) for rec in recs
    ]
    
    return ItemSimilarityResponse(
        article_id=article_id,
        similar_items=similar_items,
        count=len(similar_items),
        generated_at=datetime.now()
    )


@router.get(
    "/trending",
    response_model=TrendingResponse,
    tags=["Recommendations"]
)
async def get_trending_articles(
    limit: int = Query(20, ge=1, le=100),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get 'Trending Articles' - globally popular items.
    
    Returns the most frequently recommended articles across all customers.
    No personalization. Results are cached for 1 hour.
    
    **Parameters:**
    - `limit`: Number of trending items (1-100, default: 20)
    
    **Returns:**
    - `trending_items`: List of trending articles with scores and ranks
    - `count`: Number of trending items returned
    - `generated_at`: Timestamp of response generation (when cache was created)
    
    **Status Codes:**
    - `200`: Success
    - `503`: Service not ready
    
    **Caching:**
    Results are cached for 1 hour to avoid repeated computation.
    """
    # Get trending items (with caching)
    recs = service.get_trending_items(limit=limit)
    
    if not recs:
        logger.warning("Could not compute trending items")
        return TrendingResponse(
            trending_items=[],
            count=0,
            generated_at=datetime.now()
        )
    
    trending_items = [
        RecommendationItemResponse(**rec) for rec in recs
    ]
    
    return TrendingResponse(
        trending_items=trending_items,
        count=len(trending_items),
        generated_at=datetime.now()
    )
