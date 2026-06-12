"""
API serving module for recommendation systems
Implements serving requirements as specified in Section 6
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
from datetime import datetime

from ..models.content_based_recommender import ContentBasedRecommender
from ..models.collaborative_filtering_recommender import CollaborativeFilteringRecommender
from ..models.event_based_recommender import EventBasedRecommender
from ..models.trending_recommender import TrendingRecommender
from ..models.hybrid_recommender import HybridRecommender
from ..config import (
    SIMILAR_ITEMS_TABLE, YOU_MAY_ALSO_LIKE_TABLE, RECOMMENDATIONS_CF_TABLE,
    RECOMMENDATIONS_FINAL_TABLE, TRENDING_ARTICLES_TABLE, CUSTOMERS_ALSO_BOUGHT_TABLE,
    PERSONALIZED_FEED_TABLE
)

app = FastAPI(title="Recommendation System API", version="1.0.0")

# Global variables for recommenders and data
recommenders = {}
trained_data = {}

# Pydantic models for API responses
class SimilarItem(BaseModel):
    article_id: str
    similar_article_id: str
    similarity_score: float
    updated_at: datetime

class Recommendation(BaseModel):
    customer_id: str
    article_id: str
    score: float
    updated_at: datetime

class TrendingArticle(BaseModel):
    article_id: str
    trend_score: float
    growth_rate: float
    updated_at: datetime

class PersonalizedRecommendation(BaseModel):
    customer_id: str
    article_id: str
    relevance_score: float
    updated_at: datetime

class FinalRecommendation(BaseModel):
    customer_id: str
    article_id: str
    final_score: float
    updated_at: datetime

# Helper functions to load precomputed recommendations
def load_precomputed_recommendations(table_path: str) -> pd.DataFrame:
    """
    Load precomputed recommendations from parquet files
    
    Args:
        table_path: Path to the recommendation table
        
    Returns:
        DataFrame with recommendations
    """
    # Check if parquet file exists
    parquet_path = f"{table_path}.parquet"
    if os.path.exists(parquet_path):
        return pd.read_parquet(parquet_path)
    
    # Check if csv file exists
    csv_path = f"{table_path}.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    
    # Return empty DataFrame if no file found
    return pd.DataFrame()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/similar-items/{article_id}", response_model=List[SimilarItem])
async def get_similar_items(article_id: str, n: int = 10):
    """
    Get similar items for a given article (Section 3.1)
    
    Args:
        article_id: Article ID to find similar items for
        n: Number of similar items to return
        
    Returns:
        List of similar items
    """
    try:
        # Try to load precomputed recommendations first
        similar_items_df = load_precomputed_recommendations(SIMILAR_ITEMS_TABLE)
        
        if not similar_items_df.empty:
            # Filter for the specific article
            filtered_df = similar_items_df[similar_items_df['article_id'] == article_id]
            if not filtered_df.empty:
                # Sort by similarity score and get top n
                filtered_df = filtered_df.nlargest(n, 'similarity_score')
                
                # Convert to response models
                results = []
                for _, row in filtered_df.iterrows():
                    results.append(SimilarItem(
                        article_id=row['article_id'],
                        similar_article_id=row['similar_article_id'],
                        similarity_score=float(row['similarity_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no precomputed recommendations, use the content-based recommender
        if 'content_based' in recommenders:
            cb_recommender = recommenders['content_based']
            if cb_recommender.is_trained:
                recommendations = cb_recommender.get_similar_items(article_id, n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(SimilarItem(
                        article_id=row['article_id'],
                        similar_article_id=row['similar_article_id'],
                        similarity_score=float(row['similarity_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting similar items: {str(e)}")

@app.get("/you-may-also-like/{article_id}", response_model=List[SimilarItem])
async def get_you_may_also_like(article_id: str, n: int = 10):
    """
    Get "You May Also Like" recommendations (Section 3.2)
    
    Args:
        article_id: Article ID to find recommendations for
        n: Number of recommendations to return
        
    Returns:
        List of "You May Also Like" recommendations
    """
    try:
        # Try to load precomputed recommendations first
        ymal_df = load_precomputed_recommendations(YOU_MAY_ALSO_LIKE_TABLE)
        
        if not ymal_df.empty:
            # Filter for the specific article
            filtered_df = ymal_df[ymal_df['article_id'] == article_id]
            if not filtered_df.empty:
                # Sort by similarity score and get top n
                filtered_df = filtered_df.nlargest(n, 'similarity_score')
                
                # Convert to response models
                results = []
                for _, row in filtered_df.iterrows():
                    results.append(SimilarItem(
                        article_id=row['article_id'],
                        similar_article_id=row['recommended_article_id'],
                        similarity_score=float(row['score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no precomputed recommendations, use the content-based recommender
        if 'content_based' in recommenders:
            cb_recommender = recommenders['content_based']
            if cb_recommender.is_trained:
                recommendations = cb_recommender.get_you_may_also_like(article_id, n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(SimilarItem(
                        article_id=row['article_id'],
                        similar_article_id=row['similar_article_id'],
                        similarity_score=float(row['similarity_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting 'You May Also Like' recommendations: {str(e)}")

@app.get("/customers-also-bought/{article_id}", response_model=List[SimilarItem])
async def get_customers_also_bought(article_id: str, n: int = 10):
    """
    Get "Customers Also Bought" recommendations (Section 3.6)
    
    Args:
        article_id: Article ID to find co-purchased items for
        n: Number of recommendations to return
        
    Returns:
        List of co-purchased items
    """
    try:
        # Try to load precomputed recommendations first
        cab_df = load_precomputed_recommendations(CUSTOMERS_ALSO_BOUGHT_TABLE)
        
        if not cab_df.empty:
            # Filter for the specific article
            filtered_df = cab_df[cab_df['base_article_id'] == article_id]
            if not filtered_df.empty:
                # Sort by score and get top n
                filtered_df = filtered_df.nlargest(n, 'score')
                
                # Convert to response models
                results = []
                for _, row in filtered_df.iterrows():
                    results.append(SimilarItem(
                        article_id=row['base_article_id'],
                        similar_article_id=row['bought_together_article_id'],
                        similarity_score=float(row['score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no precomputed recommendations, use the collaborative filtering recommender
        if 'collaborative_filtering' in recommenders:
            cf_recommender = recommenders['collaborative_filtering']
            if cf_recommender.is_trained:
                recommendations = cf_recommender.get_customers_also_bought(article_id, n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(SimilarItem(
                        article_id=row['base_article_id'],
                        similar_article_id=row['bought_together_article_id'],
                        similarity_score=float(row['score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting 'Customers Also Bought' recommendations: {str(e)}")

@app.get("/recommendations/cf/{customer_id}", response_model=List[Recommendation])
async def get_collaborative_filtering_recommendations(customer_id: str, n: int = 10):
    """
    Get collaborative filtering recommendations (Section 3.3)
    
    Args:
        customer_id: Customer ID for personalized recommendations
        n: Number of recommendations to return
        
    Returns:
        List of CF recommendations
    """
    try:
        # Try to load precomputed recommendations first
        cf_df = load_precomputed_recommendations(RECOMMENDATIONS_CF_TABLE)
        
        if not cf_df.empty:
            # Filter for the specific customer
            filtered_df = cf_df[cf_df['customer_id'] == customer_id]
            if not filtered_df.empty:
                # Sort by score and get top n
                filtered_df = filtered_df.nlargest(n, 'score')
                
                # Convert to response models
                results = []
                for _, row in filtered_df.iterrows():
                    results.append(Recommendation(
                        customer_id=row['customer_id'],
                        article_id=row['article_id'],
                        score=float(row['score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no precomputed recommendations, use the collaborative filtering recommender
        if 'collaborative_filtering' in recommenders:
            cf_recommender = recommenders['collaborative_filtering']
            if cf_recommender.is_trained:
                recommendations = cf_recommender.get_cf_recommendations(customer_id, n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(Recommendation(
                        customer_id=row['customer_id'],
                        article_id=row['article_id'],
                        score=float(row['score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting CF recommendations: {str(e)}")

@app.get("/recommendations/personalized/{customer_id}", response_model=List[PersonalizedRecommendation])
async def get_personalized_recommendations(customer_id: str, n: int = 10):
    """
    Get personalized feed recommendations (Section 3.7)
    
    Args:
        customer_id: Customer ID for personalized recommendations
        n: Number of recommendations to return
        
    Returns:
        List of personalized recommendations
    """
    try:
        # Try to load precomputed recommendations first
        pf_df = load_precomputed_recommendations(PERSONALIZED_FEED_TABLE)
        
        if not pf_df.empty:
            # Filter for the specific customer
            filtered_df = pf_df[pf_df['customer_id'] == customer_id]
            if not filtered_df.empty:
                # Sort by relevance score and get top n
                filtered_df = filtered_df.nlargest(n, 'relevance_score')
                
                # Convert to response models
                results = []
                for _, row in filtered_df.iterrows():
                    results.append(PersonalizedRecommendation(
                        customer_id=row['customer_id'],
                        article_id=row['article_id'],
                        relevance_score=float(row['relevance_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no precomputed recommendations, use the event-based recommender
        if 'event_based' in recommenders:
            eb_recommender = recommenders['event_based']
            if eb_recommender.is_trained:
                recommendations = eb_recommender.get_personalized_feed(customer_id, n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(PersonalizedRecommendation(
                        customer_id=row['customer_id'],
                        article_id=row['article_id'],
                        relevance_score=float(row['relevance_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting personalized recommendations: {str(e)}")

@app.get("/trending-articles", response_model=List[TrendingArticle])
async def get_trending_articles(n: int = 10):
    """
    Get trending articles (Section 3.5)
    
    Args:
        n: Number of trending articles to return
        
    Returns:
        List of trending articles
    """
    try:
        # Try to load precomputed recommendations first
        ta_df = load_precomputed_recommendations(TRENDING_ARTICLES_TABLE)
        
        if not ta_df.empty:
            # Sort by trend score and get top n
            filtered_df = ta_df.nlargest(n, 'trend_score')
            
            # Convert to response models
            results = []
            for _, row in filtered_df.iterrows():
                results.append(TrendingArticle(
                    article_id=row['article_id'],
                    trend_score=float(row['trend_score']),
                    growth_rate=float(row['growth_rate']),
                    updated_at=row['updated_at']
                ))
            return results
        
        # If no precomputed recommendations, use the trending recommender
        if 'trending' in recommenders:
            trending_recommender = recommenders['trending']
            if trending_recommender.is_trained:
                recommendations = trending_recommender.get_trending_articles(n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(TrendingArticle(
                        article_id=row['article_id'],
                        trend_score=float(row['trend_score']),
                        growth_rate=float(row['growth_rate']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending articles: {str(e)}")

@app.get("/recommendations/final/{customer_id}", response_model=List[FinalRecommendation])
async def get_final_recommendations(customer_id: str, n: int = 10):
    """
    Get final hybrid recommendations (Section 3.4)
    
    Args:
        customer_id: Customer ID for personalized recommendations
        n: Number of recommendations to return
        
    Returns:
        List of final hybrid recommendations
    """
    try:
        # Try to load precomputed recommendations first
        final_df = load_precomputed_recommendations(RECOMMENDATIONS_FINAL_TABLE)
        
        if not final_df.empty:
            # Filter for the specific customer
            filtered_df = final_df[final_df['customer_id'] == customer_id]
            if not filtered_df.empty:
                # Sort by final score and get top n
                filtered_df = filtered_df.nlargest(n, 'final_score')
                
                # Convert to response models
                results = []
                for _, row in filtered_df.iterrows():
                    results.append(FinalRecommendation(
                        customer_id=row['customer_id'],
                        article_id=row['article_id'],
                        final_score=float(row['final_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no precomputed recommendations, use the hybrid recommender
        if 'hybrid' in recommenders:
            hybrid_recommender = recommenders['hybrid']
            if hybrid_recommender.is_trained:
                recommendations = hybrid_recommender.get_recommendations_final(customer_id, n)
                
                # Convert to response models
                results = []
                for _, row in recommendations.iterrows():
                    results.append(FinalRecommendation(
                        customer_id=row['customer_id'],
                        article_id=row['article_id'],
                        final_score=float(row['final_score']),
                        updated_at=row['updated_at']
                    ))
                return results
        
        # If no recommender available, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting final recommendations: {str(e)}")

# Functions to initialize recommenders
def initialize_recommenders():
    """
    Initialize all recommenders with pre-trained models
    """
    global recommenders
    
    # Initialize content-based recommender
    cb_recommender = ContentBasedRecommender()
    # In a real implementation, you would load a pre-trained model here
    # cb_recommender.load_model("path/to/content_based_model.pkl")
    recommenders['content_based'] = cb_recommender
    
    # Initialize collaborative filtering recommender
    cf_recommender = CollaborativeFilteringRecommender()
    # In a real implementation, you would load a pre-trained model here
    # cf_recommender.load_model("path/to/collaborative_filtering_model.pkl")
    recommenders['collaborative_filtering'] = cf_recommender
    
    # Initialize event-based recommender
    eb_recommender = EventBasedRecommender()
    # In a real implementation, you would load a pre-trained model here
    # eb_recommender.load_model("path/to/event_based_model.pkl")
    recommenders['event_based'] = eb_recommender
    
    # Initialize trending recommender
    trending_recommender = TrendingRecommender()
    # In a real implementation, you would load a pre-trained model here
    # trending_recommender.load_model("path/to/trending_model.pkl")
    recommenders['trending'] = trending_recommender
    
    # Initialize hybrid recommender
    hybrid_recommender = HybridRecommender()
    # Add individual recommenders to the hybrid engine
    if cb_recommender.is_trained:
        hybrid_recommender.add_recommender('content_based', cb_recommender)
    if cf_recommender.is_trained:
        hybrid_recommender.add_recommender('collaborative_filtering', cf_recommender)
    if eb_recommender.is_trained:
        hybrid_recommender.add_recommender('event_based', eb_recommender)
    if trending_recommender.is_trained:
        hybrid_recommender.add_recommender('trending', trending_recommender)
    
    recommenders['hybrid'] = hybrid_recommender

# Initialize recommenders when the module is imported
initialize_recommenders()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)