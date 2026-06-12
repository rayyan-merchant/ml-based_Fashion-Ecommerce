"""
Recommendation Service - Load and serve pre-trained CF model artifacts
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service for loading and serving recommendations from trained model artifacts.
    
    Loads from data/recommendations/:
    - recommendations.csv: Pre-computed user-item recommendations
    - user_latent_factors.npy: User embeddings (N_users × N_factors)
    - item_latent_factors.npy: Item embeddings (N_items × N_factors)
    - item_similarity.npy: Item-item similarity matrix
    - customer_mapping.pkl: customer_id ↔ index mapping
    - item_mapping.pkl: article_id ↔ index mapping
    """

    def __init__(self, model_dir: str = "data/recommendations"):
        # Convert to absolute path if relative
        model_path = Path(model_dir)
        if not model_path.is_absolute():
            # Try to find from backend directory going up
            current = Path.cwd()
            # Check if we're in backend dir
            if (current / model_dir).exists():
                model_path = current / model_dir
            else:
                # Try going up to project root
                project_root = current.parent if current.name == "backend" else current
                model_path = project_root / model_dir
        
        self.model_dir = model_path
        
        # Model artifacts
        self.recs_df: Optional[pd.DataFrame] = None
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None
        self.item_similarity: Optional[np.ndarray] = None
        
        # Mappings
        self.customer_mapping: Optional[Dict[str, int]] = None
        self.item_mapping: Optional[Dict[str, int]] = None
        self.idx_to_customer: Optional[Dict[int, str]] = None
        self.idx_to_item: Optional[Dict[int, str]] = None
        
        # Trending cache (with timestamp)
        self._trending_cache: Optional[List[Dict]] = None
        self._trending_cache_time: Optional[datetime] = None
        self._trending_cache_ttl_minutes = 60
        
        # Load models on init
        self._load_models()

    def _load_models(self) -> None:
        """Load all model artifacts from disk"""
        try:
            logger.info(f"Loading recommendation models from {self.model_dir}...")
            
            # Load recommendations CSV
            recs_path = self.model_dir / "recommendations.csv"
            if recs_path.exists():
                self.recs_df = pd.read_csv(recs_path)
                logger.info(f"Loaded recommendations.csv ({len(self.recs_df):,} records)")
            else:
                logger.warning(f"recommendations.csv not found at {recs_path}")
            
            # Load embeddings
            user_factors_path = self.model_dir / "user_latent_factors.npy"
            if user_factors_path.exists():
                self.user_factors = np.load(user_factors_path)
                logger.info(f"Loaded user_latent_factors.npy (shape: {self.user_factors.shape})")
            
            item_factors_path = self.model_dir / "item_latent_factors.npy"
            if item_factors_path.exists():
                self.item_factors = np.load(item_factors_path)
                logger.info(f"Loaded item_latent_factors.npy (shape: {self.item_factors.shape})")
            
            # Load similarity matrix
            item_sim_path = self.model_dir / "item_similarity.npy"
            if item_sim_path.exists():
                self.item_similarity = np.load(item_sim_path)
                logger.info(f"Loaded item_similarity.npy (shape: {self.item_similarity.shape})")
            
            # Load mappings
            customer_mapping_path = self.model_dir / "customer_mapping.pkl"
            if customer_mapping_path.exists():
                with open(customer_mapping_path, 'rb') as f:
                    self.customer_mapping = pickle.load(f)
                self.idx_to_customer = {v: k for k, v in self.customer_mapping.items()}
                logger.info(f"Loaded customer_mapping.pkl ({len(self.customer_mapping):,} customers)")
            
            item_mapping_path = self.model_dir / "item_mapping.pkl"
            if item_mapping_path.exists():
                with open(item_mapping_path, 'rb') as f:
                    self.item_mapping = pickle.load(f)
                self.idx_to_item = {v: k for k, v in self.item_mapping.items()}
                logger.info(f"Loaded item_mapping.pkl ({len(self.item_mapping):,} items)")
            
            logger.info("All recommendation models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading recommendation models: {e}")
            raise

    def get_user_recommendations(self, customer_id: str, limit: int = 12) -> List[Dict]:
        """
        Get pre-computed recommendations for a user.
        
        Args:
            customer_id: Customer ID
            limit: Max number of recommendations (default: 12)
            
        Returns:
            List of recommendations: [{'article_id': str, 'score': float, 'rank': int}, ...]
            Empty list if customer not found
        """
        if self.recs_df is None:
            logger.warning("Recommendations CSV not loaded")
            return []
        
        try:
            user_recs = self.recs_df[
                self.recs_df['customer_id'] == customer_id
            ].head(limit)
            
            if len(user_recs) == 0:
                logger.info(f"No recommendations found for customer {customer_id}, falling back to trending")
                return self.get_trending_items(limit)
            
            # Convert to list of dicts
            recs = [
                {
                    'article_id': str(row['article_id']),
                    'score': float(row['score']),
                    'rank': int(row['rank'])
                }
                for _, row in user_recs.iterrows()
            ]
            
            return recs
            
        except Exception as e:
            logger.error(f"Error getting recommendations for {customer_id}: {e}")
            return []

    def get_similar_items(self, article_id: str, limit: int = 10) -> List[Dict]:
        """
        Get items similar to the given article using item-item similarity matrix.
        
        Args:
            article_id: Article ID
            limit: Max number of similar items (default: 10)
            
        Returns:
            List of similar items: [{'article_id': str, 'score': float, 'rank': int}, ...]
        """
        if self.item_similarity is None or self.idx_to_item is None:
            logger.warning("Item similarity matrix not loaded")
            return []
        
        try:
            # Map article_id to index
            if article_id not in self.item_mapping:
                logger.warning(f"Article {article_id} not in item mapping")
                return []
            
            item_idx = self.item_mapping[article_id]
            
            # Get similarity scores for this item (excluding itself)
            similarities = self.item_similarity[item_idx].copy()
            similarities[item_idx] = -1  # Exclude self
            
            # Get top-K similar items
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            recs = []
            for rank, idx in enumerate(top_indices, 1):
                if idx in self.idx_to_item:
                    recs.append({
                        'article_id': str(self.idx_to_item[idx]),
                        'score': float(similarities[idx]),
                        'rank': rank
                    })
            
            return recs
            
        except Exception as e:
            logger.error(f"Error getting similar items for {article_id}: {e}")
            return []

    def get_trending_items(self, limit: int = 20) -> List[Dict]:
        """
        Get trending items (most frequently recommended globally).
        Uses caching to avoid repeated computation.
        
        Args:
            limit: Max number of trending items (default: 20)
            
        Returns:
            List of trending items: [{'article_id': str, 'score': float, 'rank': int}, ...]
        """
        if self.recs_df is None:
            logger.warning("Recommendations CSV not loaded")
            return []
        
        # Check cache validity
        now = datetime.now()
        if (self._trending_cache is not None and 
            self._trending_cache_time is not None and
            (now - self._trending_cache_time).total_seconds() < self._trending_cache_ttl_minutes * 60):
            logger.debug("Returning cached trending items")
            return self._trending_cache[:limit]
        
        try:
            # Count frequency of each article across all recommendations
            trending = (
                self.recs_df.groupby('article_id')['score']
                .sum()  # Sum scores (popularity measure)
                .nlargest(limit)
            )
            
            recs = [
                {
                    'article_id': str(article_id),
                    'score': float(score),
                    'rank': rank
                }
                for rank, (article_id, score) in enumerate(trending.items(), 1)
            ]
            
            # Cache the result
            self._trending_cache = recs
            self._trending_cache_time = now
            
            logger.debug(f"Computed trending items: {len(recs)} items")
            return recs
            
        except Exception as e:
            logger.error(f"Error computing trending items: {e}")
            return []

    def get_similar_users_recommendations(self, customer_id: str, limit: int = 12) -> List[Dict]:
        """
        Get recommendations from similar users using user embeddings.
        Uses KNN on user factors to find similar users, then aggregates their purchases.
        
        Note: This is a simplified version using the pre-computed recommendations.
        For full similar-users functionality, embeddings would need to be in memory.
        
        Args:
            customer_id: Customer ID
            limit: Max recommendations (default: 12)
            
        Returns:
            List of recommendations from similar users
        """
        # For now, return user's own recommendations as fallback
        # In production with embeddings in memory, compute actual KNN
        recs = self.get_user_recommendations(customer_id, limit)
        
        if len(recs) == 0:
            # Fallback to trending if no personal recs
            return self.get_trending_items(limit)
        
        return recs

    def is_ready(self) -> bool:
        """Check if service is ready to serve requests"""
        return (
            self.recs_df is not None and
            self.customer_mapping is not None and
            self.item_mapping is not None
        )

    def get_service_info(self) -> Dict:
        """Get service status and model information"""
        return {
            'status': 'ready' if self.is_ready() else 'not_ready',
            'recommendations_loaded': self.recs_df is not None,
            'n_recommendations': len(self.recs_df) if self.recs_df is not None else 0,
            'n_customers': len(self.customer_mapping) if self.customer_mapping else 0,
            'n_items': len(self.item_mapping) if self.item_mapping else 0,
            'user_factors_shape': tuple(self.user_factors.shape) if self.user_factors is not None else None,
            'item_factors_shape': tuple(self.item_factors.shape) if self.item_factors is not None else None,
        }
