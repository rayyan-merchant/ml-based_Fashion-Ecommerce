"""
Hybrid Recommendation Engine
Combines multiple recommenders into a single final ranking
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from ..base_recommender import BaseRecommender
from ..config import HYBRID_RECOMMENDER_WEIGHTS
from .content_based_recommender import ContentBasedRecommender
from .collaborative_filtering_recommender import CollaborativeFilteringRecommender
from .event_based_recommender import EventBasedRecommender
from .trending_recommender import TrendingRecommender

class HybridRecommender(BaseRecommender):
    """
    Hybrid Recommendation Engine that combines multiple recommendation approaches
    Implements:
    1. Hybrid Recommendation Engine (Global Layer) - Section 5
    2. Final recommendations output - Section 3.4
    """
    
    def __init__(self, name: str = "hybrid_recommender"):
        """
        Initialize the hybrid recommender
        
        Args:
            name: Name of the recommender
        """
        super().__init__(name)
        self.recommenders = {}
        self.weights = HYBRID_RECOMMENDER_WEIGHTS
        self.customer_features = None
        self.article_metadata = None
        
    def add_recommender(self, name: str, recommender: BaseRecommender) -> None:
        """
        Add a trained recommender to the hybrid engine
        
        Args:
            name: Name of the recommender
            recommender: Trained recommender instance
        """
        if not recommender.is_trained:
            raise ValueError(f"Recommender {name} must be trained before adding to hybrid engine")
            
        self.recommenders[name] = recommender
        
    def train(self, datasets: Dict[str, pd.DataFrame]) -> None:
        """
        Train the hybrid recommender (actually trains individual recommenders)
        
        Args:
            datasets: Dictionary of all datasets
        """
        # Store datasets for use in prediction
        self.customer_features = datasets.get('dataset_c')
        self.article_metadata = datasets.get('dataset_b')
        
        # Note: Individual recommenders should be trained separately and added
        # using add_recommender method
        
        self.is_trained = True
        self.training_timestamp = datetime.now()
        
    def predict(self, user_id: str = None, n: int = 10) -> pd.DataFrame:
        """
        Generate hybrid recommendations by combining multiple recommenders
        
        Args:
            user_id: User ID for personalized recommendations
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with final hybrid recommendations
        """
        if not self.is_trained:
            raise ValueError("Hybrid engine must be trained/configured before making predictions")
            
        # Generate final recommendations
        recommendations = self.get_final_recommendations(user_id, n)
        
        return recommendations
    
    def get_final_recommendations(self, user_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate final hybrid recommendations (Section 5)
        
        Args:
            user_id: User ID for personalized recommendations
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with final recommendations for the recommendations_final table
        """
        if not self.is_trained:
            raise ValueError("Hybrid engine must be trained/configured before making predictions")
            
        # Collect recommendations from all recommenders
        all_recommendations = self._collect_recommendations(user_id)
        
        # Combine scores using weighted ensemble
        final_recommendations = self._combine_recommendations(all_recommendations, user_id)
        
        # Apply customer-specific adjustments
        final_recommendations = self._apply_customer_adjustments(final_recommendations, user_id)
        
        # Sort by final score and get top N
        final_recommendations = final_recommendations.nlargest(n, 'final_score')
        
        # Add timestamp
        final_recommendations['updated_at'] = datetime.now()
        
        return final_recommendations
    
    def _collect_recommendations(self, user_id: str) -> Dict[str, pd.DataFrame]:
        """
        Collect recommendations from all individual recommenders
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of recommender names and their recommendations
        """
        recommendations = {}
        
        # Get CF recommendations
        if 'collaborative_filtering' in self.recommenders:
            cf_recommender = self.recommenders['collaborative_filtering']
            try:
                cf_recommendations = cf_recommender.get_cf_recommendations(user_id, 100)
                recommendations['cf'] = cf_recommendations
            except Exception as e:
                print(f"Warning: Could not get CF recommendations: {e}")
        
        # Get event-based recommendations
        if 'event_based' in self.recommenders:
            event_recommender = self.recommenders['event_based']
            try:
                event_recommendations = event_recommender.get_event_based_relevance(user_id, 100)
                recommendations['event_based'] = event_recommendations
            except Exception as e:
                print(f"Warning: Could not get event-based recommendations: {e}")
        
        # Get trending articles
        if 'trending' in self.recommenders:
            trending_recommender = self.recommenders['trending']
            try:
                trending_scores = trending_recommender.get_trend_scores_for_hybrid(100)
                recommendations['trending'] = trending_scores
            except Exception as e:
                print(f"Warning: Could not get trending recommendations: {e}")
        
        # Get content-based similarities (for items the user has interacted with)
        if 'content_based' in self.recommenders:
            content_recommender = self.recommenders['content_based']
            try:
                # Get user's recent interactions to find similar items
                similar_items = self._get_content_based_recommendations(content_recommender, user_id)
                recommendations['content_based'] = similar_items
            except Exception as e:
                print(f"Warning: Could not get content-based recommendations: {e}")
        
        # Get co-purchase recommendations
        if 'collaborative_filtering' in self.recommenders:
            cf_recommender = self.recommenders['collaborative_filtering']
            try:
                co_purchase_recs = self._get_co_purchase_recommendations(cf_recommender, user_id)
                recommendations['co_purchase'] = co_purchase_recs
            except Exception as e:
                print(f"Warning: Could not get co-purchase recommendations: {e}")
        
        return recommendations
    
    def _get_content_based_recommendations(self, content_recommender: ContentBasedRecommender, 
                                         user_id: str) -> pd.DataFrame:
        """
        Get content-based recommendations for items similar to user's interactions
        
        Args:
            content_recommender: Trained content-based recommender
            user_id: User ID
            
        Returns:
            DataFrame with content-based similarity scores
        """
        # This is a simplified approach - in practice, you'd get the user's
        # recently interacted items and find similar items for each
        
        # For demonstration, we'll return an empty DataFrame
        # A real implementation would collect similar items for user's interactions
        return pd.DataFrame(columns=['article_id', 'content_similarity'])
    
    def _get_co_purchase_recommendations(self, cf_recommender: CollaborativeFilteringRecommender,
                                       user_id: str) -> pd.DataFrame:
        """
        Get co-purchase recommendations for items frequently bought together
        with user's purchases
        
        Args:
            cf_recommender: Trained collaborative filtering recommender
            user_id: User ID
            
        Returns:
            DataFrame with co-purchase scores
        """
        # This is a simplified approach - in practice, you'd get the user's
        # purchased items and find co-purchased items for each
        
        # For demonstration, we'll return an empty DataFrame
        # A real implementation would collect co-purchased items for user's purchases
        return pd.DataFrame(columns=['article_id', 'co_purchase_score'])
    
    def _combine_recommendations(self, all_recommendations: Dict[str, pd.DataFrame],
                               user_id: str) -> pd.DataFrame:
        """
        Combine recommendations from all recommenders using weighted ensemble
        
        Args:
            all_recommendations: Dictionary of recommender names and recommendations
            user_id: User ID
            
        Returns:
            DataFrame with combined recommendations and final scores
        """
        # Create a master list of all recommended articles
        all_articles = set()
        
        # Collect all article IDs from recommendations
        for rec_name, recommendations in all_recommendations.items():
            if 'article_id' in recommendations.columns:
                all_articles.update(recommendations['article_id'].tolist())
        
        if not all_articles:
            # Return empty DataFrame if no recommendations
            return pd.DataFrame(columns=['customer_id', 'article_id', 'final_score'])
        
        # Create DataFrame with all articles
        combined_df = pd.DataFrame({'article_id': list(all_articles)})
        combined_df['customer_id'] = user_id
        
        # Add scores from each recommender
        for rec_name, recommendations in all_recommendations.items():
            if recommendations.empty:
                continue
                
            # Merge scores based on recommender type
            if rec_name == 'cf':
                score_col = 'score'
                new_col_name = 'cf_score'
            elif rec_name == 'event_based':
                score_col = 'event_based_relevance'
                new_col_name = 'event_based_relevance'
            elif rec_name == 'trending':
                score_col = 'trend_score'
                new_col_name = 'trend_score'
            elif rec_name == 'content_based':
                score_col = 'content_similarity'
                new_col_name = 'content_similarity'
            elif rec_name == 'co_purchase':
                score_col = 'co_purchase_score'
                new_col_name = 'co_purchase_score'
            else:
                continue
                
            if score_col in recommendations.columns:
                # Merge scores
                score_df = recommendations[['article_id', score_col]].rename(
                    columns={score_col: new_col_name}
                )
                combined_df = combined_df.merge(score_df, on='article_id', how='left')
        
        # Fill NaN values with 0
        score_columns = [col for col in combined_df.columns if col not in ['article_id', 'customer_id']]
        combined_df[score_columns] = combined_df[score_columns].fillna(0)
        
        # Calculate final weighted score
        combined_df['final_score'] = 0.0
        
        for score_col in score_columns:
            weight_key = score_col  # Use column name as weight key
            # Handle special cases where column names don't match weight keys exactly
            if score_col == 'event_based_relevance':
                weight_key = 'event_based_relevance'
            elif score_col == 'content_similarity':
                weight_key = 'content_similarity'
            elif score_col == 'co_purchase_score':
                weight_key = 'co_purchase_score'
                
            if weight_key in self.weights:
                combined_df['final_score'] += combined_df[score_col] * self.weights[weight_key]
        
        return combined_df[['customer_id', 'article_id', 'final_score']]
    
    def _apply_customer_adjustments(self, recommendations: pd.DataFrame, 
                                  user_id: str) -> pd.DataFrame:
        """
        Apply customer-specific adjustments to recommendations
        
        Args:
            recommendations: DataFrame with recommendations
            user_id: User ID
            
        Returns:
            Adjusted recommendations DataFrame
        """
        if self.customer_features is None:
            return recommendations
            
        # Get customer features
        customer_row = self.customer_features[self.customer_features['customer_id'] == user_id]
        
        if customer_row.empty:
            return recommendations
            
        customer_data = customer_row.iloc[0]
        
        # Apply category preferences if available
        if 'preferred_category' in customer_data and self.article_metadata is not None:
            preferred_category = customer_data['preferred_category']
            
            # Merge with article metadata to get category information
            recommendations = recommendations.merge(
                self.article_metadata[['article_id', 'index_group_name']],
                on='article_id',
                how='left'
            )
            
            # Apply boost for preferred category
            category_boost = 1.2
            recommendations['final_score'] = np.where(
                recommendations['index_group_name'] == preferred_category,
                recommendations['final_score'] * category_boost,
                recommendations['final_score']
            )
            
            # Drop the temporary column
            recommendations = recommendations.drop('index_group_name', axis=1)
        
        # Apply other customer-specific adjustments here
        # For example, adjusting for customer segment, price sensitivity, etc.
        
        return recommendations
    
    def get_recommendations_final(self, user_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate final recommendations for the recommendations_final table
        
        Args:
            user_id: User ID
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with final recommendations
        """
        # This is the same as get_final_recommendations but with proper column names
        recommendations = self.get_final_recommendations(user_id, n)
        
        # Ensure proper column names
        recommendations.rename(columns={
            'final_score': 'final_score'
        }, inplace=True)
        
        return recommendations[['customer_id', 'article_id', 'final_score']]