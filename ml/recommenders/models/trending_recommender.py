"""
Trending Articles Recommender
Implements trending articles recommendation based on time series data
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
from ..base_recommender import BaseRecommender

class TrendingRecommender(BaseRecommender):
    """
    Trending Articles Recommender using time series and event data
    Implements:
    1. Trending Articles (Home Page) - Section 4.5
    2. Trend scores in Hybrid Engine - Section 5
    """
    
    def __init__(self, name: str = "trending_recommender"):
        """
        Initialize the trending recommender
        
        Args:
            name: Name of the recommender
        """
        super().__init__(name)
        self.timeseries_data = None
        self.events_data = None
        self.article_metadata = None
        
    def train(self, datasets: Dict[str, pd.DataFrame]) -> None:
        """
        Train the trending recommender using Datasets D and F
        
        Args:
            datasets: Dictionary containing:
                - dataset_d: Time Series data
                - dataset_f: Events + Session Behavior (optional)
                - dataset_b: Article Features (for metadata)
        """
        if 'dataset_d' not in datasets:
            raise ValueError("Dataset D (time series) is required for trending recommender")
            
        self.timeseries_data = datasets['dataset_d']
        
        # Optional datasets
        self.events_data = datasets.get('dataset_f')
        self.article_metadata = datasets.get('dataset_b')
        
        self.is_trained = True
        self.training_timestamp = datetime.now()
        
    def predict(self, n: int = 10) -> pd.DataFrame:
        """
        Generate trending articles recommendations
        
        Args:
            n: Number of trending articles to generate
            
        Returns:
            DataFrame with trending articles
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Generate trending articles
        recommendations = self.get_trending_articles(n)
        
        return recommendations
    
    def get_trending_articles(self, n: int = 10) -> pd.DataFrame:
        """
        Generate trending articles (Section 4.5)
        
        Args:
            n: Number of trending articles to generate
            
        Returns:
            DataFrame with trending articles and scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Calculate trend scores using time series data
        trend_scores = self._calculate_trend_scores()
        
        # Apply additional filters (e.g., exclude out-of-stock items)
        trend_scores = self._apply_filters(trend_scores)
        
        # Get top N trending articles
        top_trending = trend_scores.nlargest(n, 'trend_score')
        
        # Add growth rate information
        results = top_trending[['article_id', 'trend_score', 'growth_rate']].copy()
        results['updated_at'] = datetime.now()
        
        return results
    
    def _calculate_trend_scores(self) -> pd.DataFrame:
        """
        Calculate trend scores using time series data
        
        Returns:
            DataFrame with article IDs and trend scores
        """
        if self.timeseries_data is None or self.timeseries_data.empty:
            return pd.DataFrame(columns=['article_id', 'trend_score', 'growth_rate'])
        
        # Group by article and calculate trend metrics
        article_trends = []
        
        for article_id, article_data in self.timeseries_data.groupby('article_id'):
            # Sort by date
            article_data = article_data.sort_values('date')
            
            # Calculate 7-day and 30-day rolling windows
            article_data['sales_7d'] = article_data['total_sales'].rolling(window=7, min_periods=1).sum()
            article_data['sales_30d'] = article_data['total_sales'].rolling(window=30, min_periods=1).sum()
            
            # Get the most recent values
            recent_7d = article_data['sales_7d'].iloc[-1] if len(article_data) > 0 else 0
            recent_30d = article_data['sales_30d'].iloc[-1] if len(article_data) > 0 else 0
            
            # Calculate growth rate (comparing recent period to previous period)
            if len(article_data) >= 14:
                prev_7d = article_data['sales_7d'].iloc[-8:-1].mean() if len(article_data) >= 8 else 0
                growth_rate = (recent_7d - prev_7d) / prev_7d if prev_7d > 0 else 0
            else:
                growth_rate = 0
            
            # Calculate weighted trend score
            # More weight on recent performance and growth
            trend_score = (recent_7d * 0.6) + (recent_30d * 0.3) + (max(growth_rate, 0) * 0.1)
            
            article_trends.append({
                'article_id': article_id,
                'trend_score': trend_score,
                'growth_rate': growth_rate
            })
        
        # Convert to DataFrame
        trend_df = pd.DataFrame(article_trends)
        
        # Incorporate event data if available
        if self.events_data is not None:
            trend_df = self._incorporate_event_data(trend_df)
            
        return trend_df
    
    def _incorporate_event_data(self, trend_df: pd.DataFrame) -> pd.DataFrame:
        """
        Incorporate event data (views, clicks) into trend scores
        
        Args:
            trend_df: DataFrame with trend scores
            
        Returns:
            Updated trend DataFrame with event data incorporated
        """
        if self.events_data is None or self.events_data.empty:
            return trend_df
            
        # Calculate event-based popularity scores
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_events = self.events_data[
            pd.to_datetime(self.events_data['event_datetime']) >= seven_days_ago
        ] if 'event_datetime' in self.events_data.columns else self.events_data
        
        # Count different types of events
        event_counts = recent_events.groupby('article_id').agg({
            'event_type': lambda x: {
                'views': sum(x == 'view'),
                'clicks': sum(x == 'click'),
                'adds_to_cart': sum(x == 'add_to_cart')
            }
        }).reset_index()
        
        # Calculate weighted event score
        event_scores = []
        for _, row in event_counts.iterrows():
            event_types = row['event_type']
            weighted_score = (
                event_types['views'] * 1.0 +
                event_types['clicks'] * 2.0 +
                event_types['adds_to_cart'] * 3.0
            )
            event_scores.append({
                'article_id': row['article_id'],
                'event_score': weighted_score
            })
        
        # Merge with trend scores
        event_df = pd.DataFrame(event_scores)
        trend_df = trend_df.merge(event_df, on='article_id', how='left')
        
        # Normalize event scores
        if 'event_score' in trend_df.columns:
            max_event_score = trend_df['event_score'].max()
            if max_event_score > 0:
                trend_df['event_score_normalized'] = trend_df['event_score'] / max_event_score
            else:
                trend_df['event_score_normalized'] = 0
            
            # Combine trend score with event score (70% trend, 30% events)
            trend_df['trend_score'] = (
                trend_df['trend_score'] * 0.7 + 
                trend_df['event_score_normalized'] * 0.3
            )
            
            # Drop temporary columns
            trend_df = trend_df.drop(['event_score', 'event_score_normalized'], axis=1)
        
        return trend_df
    
    def _apply_filters(self, trend_scores: pd.DataFrame) -> pd.DataFrame:
        """
        Apply filters to trend scores (e.g., exclude out-of-stock items)
        
        Args:
            trend_scores: DataFrame with trend scores
            
        Returns:
            Filtered trend scores DataFrame
        """
        # In a real implementation, you would check inventory status
        # For now, we'll just return the scores as-is
        # You could integrate with inventory data here
        
        # Example: Exclude articles with very low sales
        # trend_scores = trend_scores[trend_scores['trend_score'] > 0.1]
        
        return trend_scores
    
    def get_trend_scores_for_hybrid(self, n: int = 100) -> pd.DataFrame:
        """
        Get trend scores for the hybrid recommendation engine
        
        Args:
            n: Number of articles to return trend scores for
            
        Returns:
            DataFrame with article IDs and trend scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        # Calculate trend scores
        trend_scores = self._calculate_trend_scores()
        
        # Get top N articles
        top_trending = trend_scores.nlargest(n, 'trend_score')
        
        # Rename column for hybrid engine
        top_trending.rename(columns={'trend_score': 'trend_score'}, inplace=True)
        
        return top_trending[['article_id', 'trend_score']]