"""
Event-Based Personalization Recommender
Implements personalized recommendations based on user events and interactions
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
from ..base_recommender import BaseRecommender
from ..config import PERSONALIZED_FEED_WEIGHTS

class EventBasedRecommender(BaseRecommender):
    """
    Event-Based Personalization Recommender using user events and interactions
    Implements:
    1. Based on Your Interactions (Home Page) - Section 4.4
    2. Event-based relevance in Hybrid Engine - Section 5
    """
    
    def __init__(self, name: str = "event_based_recommender"):
        """
        Initialize the event-based recommender
        
        Args:
            name: Name of the recommender
        """
        super().__init__(name)
        self.events_data = None
        self.customer_features = None
        self.article_features = None
        self.short_term_weights = PERSONALIZED_FEED_WEIGHTS
        
    def train(self, datasets: Dict[str, pd.DataFrame]) -> None:
        """
        Train the event-based recommender using Datasets F, C, and B
        
        Args:
            datasets: Dictionary containing:
                - dataset_f: Events + Session Behavior
                - dataset_c: Customer Features
                - dataset_b: Article Features + Embeddings
        """
        required_datasets = ['dataset_f', 'dataset_c', 'dataset_b']
        for dataset in required_datasets:
            if dataset not in datasets:
                raise ValueError(f"{dataset} is required for event-based recommender")
                
        self.events_data = datasets['dataset_f']
        self.customer_features = datasets['dataset_c']
        self.article_features = datasets['dataset_b']
        
        self.is_trained = True
        self.training_timestamp = datetime.now()
        
    def predict(self, user_id: str = None, n: int = 10) -> pd.DataFrame:
        """
        Generate event-based personalized recommendations
        
        Args:
            user_id: User ID for personalized recommendations
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with personalized recommendations
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        if user_id is None:
            raise ValueError("User ID must be provided for personalized recommendations")
            
        # Generate personalized feed
        recommendations = self.get_personalized_feed(user_id, n)
        
        return recommendations
    
    def get_personalized_feed(self, user_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate personalized feed based on user interactions (Section 4.4)
        
        Args:
            user_id: User ID for personalized recommendations
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with personalized feed recommendations
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Get user events
        user_events = self.events_data[self.events_data['customer_id'] == user_id].copy()
        
        if user_events.empty:
            # No events for this user - fallback to popular items
            return self._get_popular_items(n)
        
        # Calculate short-term user vector (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_events = user_events[
            pd.to_datetime(user_events['event_datetime']) >= thirty_days_ago
        ] if 'event_datetime' in user_events.columns else user_events
        
        # Calculate relevance scores based on different event types
        article_scores = self._calculate_event_based_scores(recent_events, user_id)
        
        # Get top N articles
        top_articles = article_scores.nlargest(n, 'relevance_score')
        
        # Create results DataFrame
        results = top_articles[['article_id', 'relevance_score']].copy()
        results['customer_id'] = user_id
        results['updated_at'] = datetime.now()
        
        return results
    
    def _calculate_event_based_scores(self, user_events: pd.DataFrame, user_id: str) -> pd.DataFrame:
        """
        Calculate event-based relevance scores for articles
        
        Args:
            user_events: DataFrame with user events
            user_id: User ID
            
        Returns:
            DataFrame with article IDs and relevance scores
        """
        # Group events by article and calculate weighted scores
        event_scores = []
        
        for article_id, article_events in user_events.groupby('article_id'):
            # Calculate different types of scores
            view_score = len(article_events[article_events['event_type'] == 'view']) * 1.0
            click_score = len(article_events[article_events['event_type'] == 'click']) * 2.0
            wishlist_score = len(article_events[article_events['event_type'] == 'wishlist']) * 3.0
            cart_score = len(article_events[article_events['event_type'] == 'add_to_cart']) * 4.0
            
            # Apply recency weighting (more recent events have higher weight)
            recency_weight = self._calculate_recency_weight(article_events)
            
            # Combined score
            total_score = (view_score + click_score + wishlist_score + cart_score) * recency_weight
            
            event_scores.append({
                'article_id': article_id,
                'relevance_score': total_score
            })
        
        # Convert to DataFrame
        scores_df = pd.DataFrame(event_scores)
        
        # Apply long-term preferences from customer features
        if self.customer_features is not None:
            scores_df = self._apply_long_term_preferences(scores_df, user_id)
            
        return scores_df
    
    def _calculate_recency_weight(self, article_events: pd.DataFrame) -> float:
        """
        Calculate recency weight based on event timestamps
        
        Args:
            article_events: DataFrame with events for a specific article
            
        Returns:
            Recency weight (1.0 for recent events, decaying for older events)
        """
        if 'event_datetime' not in article_events.columns:
            return 1.0
            
        # Convert to datetime
        article_events['event_datetime'] = pd.to_datetime(article_events['event_datetime'])
        
        # Calculate days since each event
        now = datetime.now()
        article_events['days_since'] = (now - article_events['event_datetime']).dt.days
        
        # Apply exponential decay (more recent = higher weight)
        decay_factor = 0.95  # Decay factor per day
        weights = decay_factor ** article_events['days_since']
        
        # Return average weight
        return weights.mean() if len(weights) > 0 else 1.0
    
    def _apply_long_term_preferences(self, scores_df: pd.DataFrame, user_id: str) -> pd.DataFrame:
        """
        Apply long-term preferences from customer features
        
        Args:
            scores_df: DataFrame with article scores
            user_id: User ID
            
        Returns:
            Updated scores DataFrame with long-term preferences applied
        """
        # Get customer features
        customer_row = self.customer_features[self.customer_features['customer_id'] == user_id]
        
        if customer_row.empty:
            return scores_df
            
        customer_data = customer_row.iloc[0]
        
        # Apply category preferences if available
        if 'preferred_category' in customer_data and 'index_group_name' in self.article_features.columns:
            preferred_category = customer_data['preferred_category']
            # Boost scores for articles in preferred category
            scores_df = scores_df.merge(
                self.article_features[['article_id', 'index_group_name']],
                on='article_id',
                how='left'
            )
            
            # Apply boost for preferred category
            category_boost = 1.2
            scores_df['relevance_score'] = np.where(
                scores_df['index_group_name'] == preferred_category,
                scores_df['relevance_score'] * category_boost,
                scores_df['relevance_score']
            )
            
            # Drop the temporary column
            scores_df = scores_df.drop('index_group_name', axis=1)
            
        return scores_df
    
    def _get_popular_items(self, n: int) -> pd.DataFrame:
        """
        Get popular items as fallback for users with no events
        
        Args:
            n: Number of items to return
            
        Returns:
            DataFrame with popular items
        """
        if self.events_data is None or self.events_data.empty:
            return pd.DataFrame(columns=['customer_id', 'article_id', 'relevance_score'])
        
        # Count events per article
        article_popularity = self.events_data['article_id'].value_counts().head(n)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'article_id': article_popularity.index,
            'relevance_score': article_popularity.values,
            'customer_id': 'NEW_USER'
        })
        
        return results
    
    def get_event_based_relevance(self, user_id: str, n: int = 10) -> pd.DataFrame:
        """
        Get event-based relevance scores for the hybrid recommendation engine
        
        Args:
            user_id: User ID
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with event-based relevance scores
        """
        # This is essentially the same as the personalized feed but formatted for the hybrid engine
        recommendations = self.get_personalized_feed(user_id, n)
        
        # Rename columns to match expected format
        recommendations.rename(columns={
            'relevance_score': 'event_based_relevance'
        }, inplace=True)
        
        return recommendations[['customer_id', 'article_id', 'event_based_relevance']]