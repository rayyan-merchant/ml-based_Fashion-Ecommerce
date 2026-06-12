"""
Hybrid Recommendations Router - Advanced endpoints combining CF and CB

Provides 7 endpoints for comprehensive e-commerce recommendations:
- Product Page (3): similar products, often bought together, you may also like
- Homepage (4): personalized, customers also bought, based on interactions, trending
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models.customers import Customer
from app.db.models.articles import Article
from app.schemas.recommendations import (
    UserRecommendationsResponse,
    ItemSimilarityResponse,
    TrendingResponse,
    SimilarUsersRecommendationsResponse,
    RecommendationItemResponse
)
from app.services.hybrid_recommendation_service import HybridRecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instance (loaded at app startup)
_hybrid_service: HybridRecommendationService = None


def set_hybrid_recommendation_service(service: HybridRecommendationService):
    """Set the global hybrid recommendation service"""
    global _hybrid_service
    _hybrid_service = service
    logger.info("Hybrid recommendation service registered")


def get_hybrid_service() -> HybridRecommendationService:
    """Dependency to get hybrid recommendation service"""
    if _hybrid_service is None:
        raise HTTPException(
            status_code=503,
            detail="Hybrid recommendation service not initialized"
        )
    if not _hybrid_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Hybrid recommendation service not ready"
        )
    return _hybrid_service


# ========================================
# PRODUCT PAGE ENDPOINTS (3)
# ========================================

@router.get(
    "/similar-products/{article_id}",
    response_model=ItemSimilarityResponse,
    tags=["Hybrid", "Product Page"]
)
async def get_similar_products(
    article_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'Similar Products' using content-based filtering.
    
    Recommends articles with similar attributes (text, category, price).
    Pure content-based approach - works for new items (cold start).
    
    **Parameters:**
    - `article_id`: The article ID (from URL path)
    - `limit`: Number of similar products (1-50, default: 10)
    
    **Returns:**
    - `article_id`: The requested article ID
    - `similar_items`: List of similar articles with CB scores
    - `count`: Number of recommendations returned
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success (empty list if article not found)
    - `503`: Service not ready
    
    **Signal:** Content-Based (CB) - attribute similarity
    """
    recs = service.get_similar_products_content(article_id, limit=limit)
    
    if not recs:
        logger.debug(f"No similar products found for article {article_id}")
    
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
    "/often-bought/{article_id}",
    response_model=ItemSimilarityResponse,
    tags=["Hybrid", "Product Page"]
)
async def get_often_bought_together(
    article_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'Often Bought Together' using item-item collaborative filtering.
    
    Recommends articles that are frequently co-purchased.
    Pure collaborative filtering approach based on transaction patterns.
    
    **Parameters:**
    - `article_id`: The article ID (from URL path)
    - `limit`: Number of items (1-50, default: 10)
    
    **Returns:**
    - `article_id`: The requested article ID
    - `similar_items`: List of frequently co-purchased articles
    - `count`: Number of recommendations returned
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success (empty list if article not found)
    - `503`: Service not ready
    
    **Signal:** Collaborative Filtering (CF) - co-purchase patterns
    """
    recs = service.get_often_bought_together(article_id, limit=limit)
    
    if not recs:
        logger.debug(f"No often-bought items found for article {article_id}")
    
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
    "/you-may-also-like-product/{article_id}",
    response_model=ItemSimilarityResponse,
    tags=["Hybrid", "Product Page"]
)
async def get_you_may_also_like_product(
    article_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'You May Also Like' for product page (hybrid item-based).
    
    Blends two signals:
    - 60% Item-Item CF (co-purchases)
    - 40% Content-Based (attribute similarity)
    
    Provides balanced recommendations that capture both behavioral
    and attribute-based similarity.
    
    **Parameters:**
    - `article_id`: The article ID (from URL path)
    - `limit`: Number of recommendations (1-50, default: 10)
    
    **Returns:**
    - `article_id`: The requested article ID
    - `similar_items`: Hybrid-scored recommendations
    - `count`: Number of recommendations returned
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `503`: Service not ready
    
    **Signal:** Hybrid (60% CF + 40% CB)
    """
    recs = service.get_you_may_also_like_hybrid_item(article_id, limit=limit)
    
    if not recs:
        logger.debug(f"No hybrid recommendations for article {article_id}")
    
    similar_items = [
        RecommendationItemResponse(**rec) for rec in recs
    ]
    
    return ItemSimilarityResponse(
        article_id=article_id,
        similar_items=similar_items,
        count=len(similar_items),
        generated_at=datetime.now()
    )


# ========================================
# HOMEPAGE ENDPOINTS (4)
# ========================================

@router.get(
    "/personalized/{customer_id}",
    response_model=UserRecommendationsResponse,
    tags=["Hybrid", "Homepage"]
)
async def get_personalized_recommendations(
    customer_id: str,
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'Personalized For You' using collaborative filtering.
    
    Returns items based on customer's purchase/interaction history.
    Best for warm users with purchase history.
    Falls back to trending for cold-start users.
    
    **Parameters:**
    - `customer_id`: The customer ID (from URL path)
    - `limit`: Number of recommendations (1-50, default: 12)
    
    **Returns:**
    - `customer_id`: The requested customer ID
    - `recommendations`: Personalized items with CF scores
    - `count`: Number of recommendations returned
    - `recommendation_type`: "personalized"
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `404`: Customer not found
    - `503`: Service not ready
    
    **Signal:** Collaborative Filtering (CF) - user behavior
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
    
    recs = service.get_personalized_cf(customer_id, limit=limit)
    
    if not recs:
        logger.info(f"No personalized recommendations for customer {customer_id}, returning trending")
        recs = service.get_trending_items(limit=limit)
    
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
    "/customers-also-bought/{customer_id}",
    response_model=SimilarUsersRecommendationsResponse,
    tags=["Hybrid", "Homepage"]
)
async def get_customers_also_bought(
    customer_id: str,
    limit: int = Query(12, ge=1, le=50),
    k_neighbors: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'Customers Also Bought' using user-user collaborative filtering.
    
    Finds customers with similar purchase patterns and recommends items
    that those similar customers purchased. Aggregates across k neighbors.
    
    **Parameters:**
    - `customer_id`: The customer ID (from URL path)
    - `limit`: Number of recommendations (1-50, default: 12)
    - `k_neighbors`: Number of similar users to aggregate (1-50, default: 10)
    
    **Returns:**
    - `customer_id`: The requested customer ID
    - `recommendations`: Items from similar customers' purchases
    - `count`: Number of recommendations returned
    - `recommendation_type`: "similar_users"
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `404`: Customer not found
    - `503`: Service not ready
    
    **Signal:** Collaborative Filtering (CF) - user-user similarity
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
    
    recs = service.get_customers_also_bought(customer_id, limit=limit, k_neighbors=k_neighbors)
    
    if not recs:
        logger.info(f"No similar-user recommendations for customer {customer_id}, returning trending")
        recs = service.get_trending_items(limit=limit)
    
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
    "/based-on-interactions/{customer_id}",
    response_model=UserRecommendationsResponse,
    tags=["Hybrid", "Homepage"]
)
async def get_based_on_interactions(
    customer_id: str,
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'Based on Your Interactions' using hybrid CF + CB approach.
    
    Intelligently blends signals based on user type:
    - Warm users (with history): 50% CF + 35% CB + 15% Popularity
    - Cold users (no history): 70% CB (from purchase history) + 30% Popularity
    
    Provides best coverage and quality across all user segments.
    
    **Parameters:**
    - `customer_id`: The customer ID (from URL path)
    - `limit`: Number of recommendations (1-50, default: 12)
    
    **Returns:**
    - `customer_id`: The requested customer ID
    - `recommendations`: Hybrid-scored recommendations
    - `count`: Number of recommendations returned
    - `recommendation_type`: "hybrid"
    - `generated_at`: Timestamp of response generation
    
    **Status Codes:**
    - `200`: Success
    - `404`: Customer not found
    - `503`: Service not ready
    
    **Signal:** Hybrid (intelligent blending of CF + CB + Popularity)
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
    
    recs = service.get_based_on_interactions(customer_id, limit=limit)
    
    if not recs:
        logger.info(f"No interaction-based recommendations for customer {customer_id}, returning trending")
        recs = service.get_trending_items(limit=limit)
    
    recommendation_items = [
        RecommendationItemResponse(**rec) for rec in recs
    ]
    
    return UserRecommendationsResponse(
        customer_id=customer_id,
        recommendations=recommendation_items,
        count=len(recommendation_items),
        recommendation_type="hybrid",
        generated_at=datetime.now()
    )


@router.get(
    "/trending",
    response_model=TrendingResponse,
    tags=["Hybrid", "Homepage"]
)
async def get_trending_items(
    limit: int = Query(20, ge=1, le=100),
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Get 'Trending Now' - globally popular items.
    
    Returns the most frequently recommended articles across all customers.
    No personalization. Results are cached for 1 hour to optimize performance.
    
    Perfect for new visitors or when personalization isn't available.
    
    **Parameters:**
    - `limit`: Number of trending items (1-100, default: 20)
    
    **Returns:**
    - `trending_items`: List of popular articles with scores
    - `count`: Number of trending items returned
    - `generated_at`: Timestamp of cache creation (not current request)
    
    **Status Codes:**
    - `200`: Success
    - `503`: Service not ready
    
    **Caching:**
    Results are cached for 1 hour. All requests within that hour
    return the same generated_at timestamp.
    
    **Signal:** Popularity aggregation
    """
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


# ========================================
# SERVICE HEALTH
# ========================================

@router.get("/health", tags=["Hybrid"])
async def hybrid_recommendations_health(
    service: HybridRecommendationService = Depends(get_hybrid_service)
):
    """
    Health check for hybrid recommendation service.
    
    Returns comprehensive service status including:
    - Overall readiness (cf_ready, hybrid_ready, not_ready)
    - CF model status (counts, shapes)
    - CB model status (counts, shapes)
    - Model artifact paths
    
    **Returns:**
    - `status`: Service readiness status
    - `cf_models`: Collaborative filtering model info
    - `cb_models`: Content-based model info
    - `cf_model_dir`: Path to CF artifacts
    - `cb_model_dir`: Path to CB artifacts
    
    **Status Codes:**
    - `200`: Service running (check status field for readiness)
    - `503`: Service not initialized
    """
    return service.get_service_info()
