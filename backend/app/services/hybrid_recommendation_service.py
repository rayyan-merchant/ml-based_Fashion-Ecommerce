"""
Hybrid Recommendation Service - Combines CF and Content-Based Filtering

This service implements a 3-signal hybrid approach:
- Collaborative Filtering (CF) ~ 50-60%: User-item interactions, behavioral patterns
- Content-Based (CB) ~ 30-40%: Article attributes, similarity
- Popularity (Pop) ~ 10-15%: Fallback for cold start

Smart routing by user/item type with graceful fallback chains.
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class HybridRecommendationService:
    """
    Hybrid service combining CF and CB approaches with smart routing.
    
    Loads from:
    - data/recommendations/: CF artifacts (user/item factors, similarity matrices)
    - data/content_based_model/: CB artifacts (similarity matrix, embeddings, vectorizers)
    """

    def __init__(self, cf_model_dir: str = "app/models/recommendations", 
                 cb_model_dir: str = "data/content_based_model"):
        """
        Initialize hybrid service with both CF and CB models.
        
        Args:
            cf_model_dir: Path to CF model artifacts
            cb_model_dir: Path to CB model artifacts
        """
        # Convert to absolute paths
        self.cf_model_dir = self._resolve_path(cf_model_dir)
        self.cb_model_dir = self._resolve_path(cb_model_dir)
        
        # CF Artifacts
        self.recs_df: Optional[pd.DataFrame] = None
        self.recs_customer_ids: set = set()
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None
        self.item_similarity_cf: Optional[np.ndarray] = None
        self.customer_mapping: Optional[Dict[str, int]] = None
        self.item_mapping: Optional[Dict[str, int]] = None
        self.idx_to_customer: Optional[Dict[int, str]] = None
        self.idx_to_item: Optional[Dict[int, str]] = None
        
        # CB Artifacts
        self.article_similarity_cb: Optional[np.ndarray] = None
        self.article_embeddings_cb: Optional[np.ndarray] = None
        self.tfidf_vectorizer: Optional[object] = None
        self.price_scaler: Optional[object] = None
        self.article_id_to_idx_cb: Optional[Dict[str, int]] = None
        self.idx_to_article_id_cb: Optional[Dict[int, str]] = None
        self.cb_config: Optional[Dict] = None
        
        # Trending cache
        self._trending_cache: Optional[List[Dict]] = None
        self._trending_cache_time: Optional[datetime] = None
        self._trending_cache_ttl_minutes = 60
        
        # Load both models
        self._load_cf_models()
        self._load_cb_models()
        self._log_service_status()

    def _resolve_path(self, model_dir: str) -> Path:
        """Resolve relative paths to absolute paths"""
        model_path = Path(model_dir)
        if model_path.is_absolute():
            return model_path
        
        current = Path.cwd()
        if (current / model_dir).exists():
            return current / model_dir
        
        # Try going up to project root
        project_root = current.parent if current.name == "backend" else current
        resolved = project_root / model_dir
        return resolved

    def _load_cf_models(self) -> None:
        """Load collaborative filtering model artifacts"""
        try:
            logger.info(f"Loading CF models from {self.cf_model_dir}...")
            
            # Load recommendations CSV
            recs_path = self.cf_model_dir / "recommendations.csv"
            if recs_path.exists():
                self.recs_df = pd.read_csv(recs_path)
                if 'customer_id' in self.recs_df.columns:
                    self.recs_df['customer_id'] = self.recs_df['customer_id'].astype(str)
                    self.recs_customer_ids = set(self.recs_df['customer_id'].unique())
                if 'article_id' in self.recs_df.columns:
                    self.recs_df['article_id'] = self.recs_df['article_id'].astype(str)
                logger.info(f"CF recommendations.csv ({len(self.recs_df):,} records)")
            
            # Load embeddings
            user_factors_path = self.cf_model_dir / "user_latent_factors.npy"
            if user_factors_path.exists():
                self.user_factors = np.load(user_factors_path)
                logger.info(f"CF user_latent_factors (shape: {self.user_factors.shape})")
            
            item_factors_path = self.cf_model_dir / "item_latent_factors.npy"
            if item_factors_path.exists():
                self.item_factors = np.load(item_factors_path)
                logger.info(f"CF item_latent_factors (shape: {self.item_factors.shape})")
            
            # Load similarity matrix
            item_sim_path = self.cf_model_dir / "item_similarity.npy"
            if item_sim_path.exists():
                self.item_similarity_cf = np.load(item_sim_path)
                logger.info(f"CF item_similarity (shape: {self.item_similarity_cf.shape})")
            
            # Load mappings
            customer_mapping_path = self.cf_model_dir / "customer_mapping.pkl"
            if customer_mapping_path.exists():
                with open(customer_mapping_path, 'rb') as f:
                    raw_customer_mapping = pickle.load(f)
                first_key = next(iter(raw_customer_mapping), None)
                if isinstance(first_key, (int, np.integer)):
                    self.idx_to_customer = {int(k): str(v) for k, v in raw_customer_mapping.items()}
                    self.customer_mapping = {str(v): int(k) for k, v in raw_customer_mapping.items()}
                else:
                    self.customer_mapping = {str(k): int(v) for k, v in raw_customer_mapping.items()}
                    self.idx_to_customer = {int(v): str(k) for k, v in raw_customer_mapping.items()}
                logger.info(f"CF customer_mapping ({len(self.customer_mapping):,} customers)")
            
            item_mapping_path = self.cf_model_dir / "item_mapping.pkl"
            if item_mapping_path.exists():
                with open(item_mapping_path, 'rb') as f:
                    raw_item_mapping = pickle.load(f)
                first_key = next(iter(raw_item_mapping), None)
                if isinstance(first_key, (int, np.integer)):
                    self.idx_to_item = {int(k): str(v) for k, v in raw_item_mapping.items()}
                    self.item_mapping = {str(v): int(k) for k, v in raw_item_mapping.items()}
                else:
                    self.item_mapping = {str(k): int(v) for k, v in raw_item_mapping.items()}
                    self.idx_to_item = {int(v): str(k) for k, v in raw_item_mapping.items()}
                logger.info(f"CF item_mapping ({len(self.item_mapping):,} items)")
            
        except Exception as e:
            logger.error(f"Error loading CF models: {e}")

    def _load_cb_models(self) -> None:
        """Load content-based model artifacts"""
        try:
            logger.info(f"Loading CB models from {self.cb_model_dir}...")
            
            # Load CB similarity matrix
            cb_sim_path = self.cb_model_dir / "article_similarity_matrix.npy"
            if cb_sim_path.exists():
                self.article_similarity_cb = np.load(cb_sim_path)
                logger.info(f"CB article_similarity_matrix (shape: {self.article_similarity_cb.shape})")
            else:
                logger.warning(f"CB similarity matrix not found at {cb_sim_path}")
            
            # Load embeddings
            embeddings_path = self.cb_model_dir / "article_text_embeddings.npy"
            if embeddings_path.exists():
                self.article_embeddings_cb = np.load(embeddings_path)
                logger.info(f"CB article_text_embeddings (shape: {self.article_embeddings_cb.shape})")
            
            # Load vectorizers
            tfidf_path = self.cb_model_dir / "tfidf_vectorizer.pkl"
            if tfidf_path.exists():
                with open(tfidf_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
                logger.info("CB tfidf_vectorizer loaded")
            
            price_scaler_path = self.cb_model_dir / "price_scaler.pkl"
            if price_scaler_path.exists():
                with open(price_scaler_path, 'rb') as f:
                    self.price_scaler = pickle.load(f)
                logger.info("CB price_scaler loaded")
            
            # Load ID mappings
            id_to_idx_path = self.cb_model_dir / "article_id_to_idx.pkl"
            if id_to_idx_path.exists():
                with open(id_to_idx_path, 'rb') as f:
                    self.article_id_to_idx_cb = pickle.load(f)
                self.idx_to_article_id_cb = {v: k for k, v in self.article_id_to_idx_cb.items()}
                logger.info(f"CB article_id_to_idx ({len(self.article_id_to_idx_cb):,} articles)")
            
            # Load config
            config_path = self.cb_model_dir / "config.pkl"
            if config_path.exists():
                with open(config_path, 'rb') as f:
                    self.cb_config = pickle.load(f)
                logger.info(f"CB config loaded: {self.cb_config}")
            
        except Exception as e:
            logger.error(f"Error loading CB models: {e}")

    def _log_service_status(self) -> None:
        """Log overall service readiness status"""
        cf_ready = self.recs_df is not None and self.item_mapping is not None
        cb_ready = self.article_similarity_cb is not None and self.article_id_to_idx_cb is not None
        
        logger.info(f"Service Status - CF: {'ready' if cf_ready else 'not ready'}, CB: {'ready' if cb_ready else 'not ready'}")

    # ===== COLD START HANDLING =====
    
    def _is_warm_user(self, customer_id: str) -> bool:
        """Check if user has recommendation history (warm user)"""
        if self.recs_df is None:
            return False
        return str(customer_id) in self.recs_customer_ids
    
    def _is_new_item(self, article_id: str) -> bool:
        """Check if item is new (not in CF training data)"""
        if self.item_mapping is None:
            return True
        return article_id not in self.item_mapping
    
    def _get_user_purchase_history(self, customer_id: str, limit: int = 5) -> List[str]:
        """Get customer's past purchases for CB similarity lookup"""
        if self.recs_df is None:
            return []
        
        try:
            history = self.recs_df[
                self.recs_df['customer_id'] == customer_id
            ]['article_id'].unique()[:limit].tolist()
            return [str(aid) for aid in history]
        except:
            return []

    # ===== CORE HYBRID METHODS =====

    def get_personalized_cf(self, customer_id: str, limit: int = 12) -> List[Dict]:
        """
        Get personalized recommendations using pure CF.
        Returns empty list if user is cold start (no history).
        
        Args:
            customer_id: Customer ID
            limit: Max recommendations
            
        Returns:
            List of recommendations with CF signal
        """
        if self.recs_df is None:
            return []
        
        try:
            user_recs = self.recs_df[
                self.recs_df['customer_id'] == customer_id
            ].head(limit)
            
            if len(user_recs) == 0:
                return []
            
            return [
                {
                    'article_id': str(row['article_id']),
                    'score': float(row['score']),
                    'rank': int(row['rank']),
                    'signal': 'cf'
                }
                for _, row in user_recs.iterrows()
            ]
        except Exception as e:
            logger.error(f"Error in get_personalized_cf: {e}")
            return []

    def get_hybrid_personalized(self, customer_id: str, limit: int = 12, 
                                weights: Optional[Dict] = None) -> List[Dict]:
        """
        Get personalized hybrid recommendations (CF + CB + Popularity).
        Smart routing: uses CF for warm users, CB for cold users.
        
        Args:
            customer_id: Customer ID
            limit: Max recommendations
            weights: Weight distribution {'cf': 0.5, 'cb': 0.35, 'pop': 0.15}
            
        Returns:
            List of hybrid recommendations with signal attribution
        """
        if weights is None:
            weights = {'cf': 0.5, 'cb': 0.35, 'pop': 0.15}
        
        is_warm = self._is_warm_user(customer_id)
        
        if is_warm:
            # Warm user: CF is primary signal
            cf_recs = self.get_personalized_cf(customer_id, limit * 2)
            cb_recs = self.get_trending_items(limit * 2)  # Use trending as secondary
            
            # Blend CF (70%) + Trending (30%)
            blended = self._blend_recommendations(
                cf_recs, cb_recs,
                weights={'primary': 0.7, 'secondary': 0.3}
            )
        else:
            # Cold user: CB is primary signal, use purchase history
            history = self._get_user_purchase_history(customer_id, limit=5)
            if history:
                cb_recs = self._get_similar_products_batch(history)
                pop_recs = self.get_trending_items(limit)
                blended = self._blend_recommendations(
                    cb_recs, pop_recs,
                    weights={'primary': 0.7, 'secondary': 0.3}
                )
            else:
                # Ultimate fallback: trending
                blended = self.get_trending_items(limit)
        
        return blended[:limit]

    def get_often_bought_together(self, article_id: str, limit: int = 10) -> List[Dict]:
        """
        Get items often bought together (item-item CF).
        Uses CF similarity matrix to find co-purchased items.
        
        Args:
            article_id: Article ID
            limit: Max recommendations
            
        Returns:
            List of frequently co-purchased items
        """
        if self.item_similarity_cf is None or self.idx_to_item is None:
            # Fallback to CB similarity
            return self.get_similar_products_content(article_id, limit)
        
        try:
            if article_id not in self.item_mapping:
                return []
            
            item_idx = self.item_mapping[article_id]
            similarities = self.item_similarity_cf[item_idx].copy()
            similarities[item_idx] = -1  # Exclude self
            
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            return [
                {
                    'article_id': str(self.idx_to_item[idx]),
                    'score': float(similarities[idx]),
                    'rank': rank + 1,
                    'signal': 'cf'
                }
                for rank, idx in enumerate(top_indices)
                if idx in self.idx_to_item and similarities[idx] > 0
            ]
        except Exception as e:
            logger.error(f"Error in get_often_bought_together: {e}")
            return self.get_similar_products_content(article_id, limit)

    def get_similar_products_content(self, article_id: str, limit: int = 10) -> List[Dict]:
        """
        Get similar products using pure CB (TF-IDF + price similarity).
        
        Args:
            article_id: Article ID
            limit: Max recommendations
            
        Returns:
            List of similar products from CB signal
        """
        if self.article_similarity_cb is None or self.article_id_to_idx_cb is None:
            return []
        
        try:
            if article_id not in self.article_id_to_idx_cb:
                return []
            
            item_idx = self.article_id_to_idx_cb[article_id]
            similarities = self.article_similarity_cb[item_idx].copy()
            similarities[item_idx] = -1  # Exclude self
            
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            return [
                {
                    'article_id': str(self.idx_to_article_id_cb[idx]),
                    'score': float(similarities[idx]),
                    'rank': rank + 1,
                    'signal': 'cb'
                }
                for rank, idx in enumerate(top_indices)
                if idx in self.idx_to_article_id_cb and similarities[idx] > 0
            ]
        except Exception as e:
            logger.error(f"Error in get_similar_products_content: {e}")
            return []

    def get_you_may_also_like_hybrid_item(self, article_id: str, limit: int = 10,
                                          weights: Optional[Dict] = None) -> List[Dict]:
        """
        Hybrid "You May Also Like" for product page.
        Blends item-item CF (co-purchases) + CB (attribute similarity).
        
        Args:
            article_id: Article ID
            limit: Max recommendations
            weights: Weight distribution, default {'cf': 0.6, 'cb': 0.4}
            
        Returns:
            Hybrid recommendations for product page
        """
        if weights is None:
            weights = {'cf': 0.6, 'cb': 0.4}
        
        cf_recs = self.get_often_bought_together(article_id, limit * 2)
        cb_recs = self.get_similar_products_content(article_id, limit * 2)
        
        blended = self._blend_recommendations(
            cf_recs, cb_recs,
            weights={'primary': weights['cf'], 'secondary': weights['cb']}
        )
        
        return blended[:limit]

    def get_personalized_cf_simple(self, customer_id: str, limit: int = 12) -> List[Dict]:
        """
        Simple CF recommendations (often bought together by similar users).
        Alias for get_personalized_cf for endpoint mapping.
        """
        return self.get_personalized_cf(customer_id, limit)

    def get_customers_also_bought(self, customer_id: str, limit: int = 12, 
                                  k_neighbors: int = 10) -> List[Dict]:
        """
        Get recommendations from similar customers (user-user CF).
        Uses user embeddings to find k-nearest neighbors.
        
        Args:
            customer_id: Customer ID
            limit: Max recommendations
            k_neighbors: Number of similar users to aggregate
            
        Returns:
            Items bought by similar customers
        """
        if self.user_factors is None or self.customer_mapping is None or self.idx_to_customer is None:
            return self.get_trending_items(limit)
        
        try:
            # Use idx_to_customer which maps customer_id → index
            if customer_id not in self.customer_mapping:
                return self.get_trending_items(limit)
            
            user_idx = int(self.customer_mapping[customer_id])
            user_vector = self.user_factors[user_idx]
            
            # Compute similarities to all users
            similarities = cosine_similarity([user_vector], self.user_factors)[0]
            similarities[user_idx] = -1  # Exclude self
            
            # Search beyond k_neighbors because the factor matrix can include
            # customers that do not have precomputed recommendation rows.
            candidate_count = min(len(similarities), max(k_neighbors * 50, 500))
            similar_indices = np.argsort(similarities)[::-1][:candidate_count]
            
            # Aggregate their recommendations
            aggregated_scores = {}
            for sim_idx in similar_indices:
                sim_idx_int = int(sim_idx)  # Convert numpy int to Python int
                similar_user_id = self.idx_to_customer.get(sim_idx_int)
                if not similar_user_id:
                    continue

                similar_user_recs = self.get_personalized_cf(similar_user_id, limit * 2)
                weight = float(similarities[sim_idx_int])

                for rec in similar_user_recs:
                    article_id = rec['article_id']
                    aggregated_scores[article_id] = aggregated_scores.get(article_id, 0) + weight * rec['score']

                if len(aggregated_scores) >= limit * 3:
                    break
            
            if not aggregated_scores:
                return self.get_trending_items(limit)
            
            # Sort by aggregated score
            sorted_recs = sorted(aggregated_scores.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {
                    'article_id': article_id,
                    'score': float(score),
                    'rank': rank + 1,
                    'signal': 'cf_user'
                }
                for rank, (article_id, score) in enumerate(sorted_recs[:limit])
            ]
        except Exception as e:
            logger.error(f"Error in get_customers_also_bought: {e}")
            return self.get_trending_items(limit)

    def get_based_on_interactions(self, customer_id: str, limit: int = 12) -> List[Dict]:
        """
        Hybrid "Based on Your Interactions" for homepage.
        Uses CF primarily, falls back to CB for cold users.
        
        Args:
            customer_id: Customer ID
            limit: Max recommendations
            
        Returns:
            Hybrid recommendations based on user interactions
        """
        return self.get_hybrid_personalized(customer_id, limit)

    def get_trending_items(self, limit: int = 20) -> List[Dict]:
        """
        Get trending items (most frequently recommended globally).
        Uses 1-hour cache to avoid recomputation.
        
        Args:
            limit: Max trending items
            
        Returns:
            List of popular/trending items
        """
        if self.recs_df is None:
            return []
        
        # Check cache
        now = datetime.now()
        if (self._trending_cache is not None and 
            self._trending_cache_time is not None and
            (now - self._trending_cache_time).total_seconds() < self._trending_cache_ttl_minutes * 60):
            return self._trending_cache[:limit]
        
        try:
            trending = self.recs_df.groupby('article_id')['score'].sum().nlargest(limit)
            
            recs = [
                {
                    'article_id': str(article_id),
                    'score': float(score),
                    'rank': rank + 1,
                    'signal': 'popularity'
                }
                for rank, (article_id, score) in enumerate(trending.items())
            ]
            
            self._trending_cache = recs
            self._trending_cache_time = now
            return recs
        except Exception as e:
            logger.error(f"Error in get_trending_items: {e}")
            return []

    # ===== HELPER METHODS =====

    def _get_similar_products_batch(self, article_ids: List[str], limit: int = 10) -> List[Dict]:
        """
        Get similar products for a batch of articles, aggregated.
        Used for cold-start user CB-based recommendations.
        """
        all_similar = {}
        
        for article_id in article_ids:
            similar = self.get_similar_products_content(article_id, limit * 2)
            for rec in similar:
                aid = rec['article_id']
                all_similar[aid] = all_similar.get(aid, 0) + rec['score']
        
        # Sort and convert to list
        sorted_items = sorted(all_similar.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'article_id': article_id,
                'score': float(score),
                'rank': rank + 1,
                'signal': 'cb'
            }
            for rank, (article_id, score) in enumerate(sorted_items[:limit])
        ]

    def _blend_recommendations(self, primary_recs: List[Dict], secondary_recs: List[Dict],
                               weights: Optional[Dict] = None) -> List[Dict]:
        """
        Blend two recommendation lists with weighted scoring.
        
        Args:
            primary_recs: Primary recommendation list
            secondary_recs: Secondary (fallback) recommendation list
            weights: {'primary': 0.7, 'secondary': 0.3}
            
        Returns:
            Merged and ranked recommendations
        """
        if weights is None:
            weights = {'primary': 0.7, 'secondary': 0.3}
        
        blended_scores = {}
        signal_map = {}

        def normalized_score(rec: Dict, recs: List[Dict]) -> float:
            scores = [abs(float(item.get('score', 0) or 0)) for item in recs]
            max_score = max(scores) if scores else 0
            if max_score <= 0:
                rank = int(rec.get('rank', 1) or 1)
                return 1.0 / max(rank, 1)
            return float(rec.get('score', 0) or 0) / max_score
        
        # Primary recommendations
        for rec in primary_recs:
            aid = rec['article_id']
            score = normalized_score(rec, primary_recs) * weights['primary']
            blended_scores[aid] = blended_scores.get(aid, 0) + score
            signal_map[aid] = rec.get('signal', 'unknown')
        
        # Secondary recommendations
        for rec in secondary_recs:
            aid = rec['article_id']
            if aid not in blended_scores:  # Don't double-count
                score = normalized_score(rec, secondary_recs) * weights['secondary']
                blended_scores[aid] = score
                signal_map[aid] = rec.get('signal', 'unknown')
        
        # Sort and format
        sorted_recs = sorted(blended_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'article_id': article_id,
                'score': float(score),
                'rank': rank + 1,
                'signal': signal_map.get(article_id, 'hybrid')
            }
            for rank, (article_id, score) in enumerate(sorted_recs)
        ]

    def is_ready(self) -> bool:
        """Check if service is ready (at least CF available)"""
        return self.recs_df is not None and self.item_mapping is not None

    def is_hybrid_ready(self) -> bool:
        """Check if both CF and CB are available for full hybrid"""
        return self.is_ready() and self.article_similarity_cb is not None

    def get_service_info(self) -> Dict:
        """Get comprehensive service status"""
        return {
            'status': 'hybrid_ready' if self.is_hybrid_ready() else ('cf_ready' if self.is_ready() else 'not_ready'),
            'cf_models': {
                'recommendations_loaded': self.recs_df is not None,
                'n_recommendations': len(self.recs_df) if self.recs_df is not None else 0,
                'n_customers': len(self.customer_mapping) if self.customer_mapping else 0,
                'n_items': len(self.item_mapping) if self.item_mapping else 0,
                'user_factors_shape': tuple(self.user_factors.shape) if self.user_factors is not None else None,
                'item_factors_shape': tuple(self.item_factors.shape) if self.item_factors is not None else None,
            },
            'cb_models': {
                'similarity_matrix_loaded': self.article_similarity_cb is not None,
                'similarity_matrix_shape': tuple(self.article_similarity_cb.shape) if self.article_similarity_cb is not None else None,
                'n_articles': len(self.article_id_to_idx_cb) if self.article_id_to_idx_cb else 0,
                'embeddings_shape': tuple(self.article_embeddings_cb.shape) if self.article_embeddings_cb is not None else None,
            },
            'cf_model_dir': str(self.cf_model_dir),
            'cb_model_dir': str(self.cb_model_dir),
        }
