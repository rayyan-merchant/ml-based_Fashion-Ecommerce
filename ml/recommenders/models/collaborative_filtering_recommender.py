"""
Collaborative Filtering Recommender
Implements User-Item collaborative filtering for recommendations
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from ..base_recommender import BaseRecommender
from ..config import DEFAULT_TOP_K

class CollaborativeFilteringRecommender(BaseRecommender):
    """
    Collaborative Filtering Recommender using User-Item interactions
    Implements:
    1. Customers Also Bought (Home Page) - Section 4.3
    2. CF-based recommendations in Hybrid Engine - Section 5
    """
    
    def __init__(self, name: str = "collaborative_filtering_recommender", 
                 n_components: int = 50, method: str = "svd"):
        """
        Initialize the collaborative filtering recommender
        
        Args:
            name: Name of the recommender
            n_components: Number of latent factors for matrix factorization
            method: CF method to use ('svd', 'item_based', 'user_based')
        """
        super().__init__(name)
        self.n_components = n_components
        self.method = method
        self.user_item_matrix = None
        self.item_item_similarity = None
        self.user_user_similarity = None
        self.svd_model = None
        self.user_mapping = None
        self.item_mapping = None
        self.reverse_user_mapping = None
        self.reverse_item_mapping = None
        
    def train(self, datasets: Dict[str, pd.DataFrame]) -> None:
        """
        Train the collaborative filtering recommender using Dataset A
        
        Args:
            datasets: Dictionary containing Dataset A (user-item interactions)
        """
        if 'dataset_a' not in datasets:
            raise ValueError("Dataset A (user-item interactions) is required for CF recommender")
            
        dataset_a = datasets['dataset_a']
        
        # Create user-item matrix
        self._create_user_item_matrix(dataset_a)
        
        # Train based on selected method
        if self.method == "svd":
            self._train_svd()
        elif self.method == "item_based":
            self._train_item_based()
        elif self.method == "user_based":
            self._train_user_based()
        else:
            raise ValueError(f"Unknown method: {self.method}")
            
        self.is_trained = True
        self.training_timestamp = datetime.now()
        
    def _create_user_item_matrix(self, dataset_a: pd.DataFrame) -> None:
        """
        Create user-item interaction matrix
        
        Args:
            dataset_a: Dataset A DataFrame
        """
        # Create mappings for users and items
        unique_users = dataset_a['customer_id'].unique()
        unique_items = dataset_a['article_id'].unique()
        
        self.user_mapping = {user: idx for idx, user in enumerate(unique_users)}
        self.item_mapping = {item: idx for idx, item in enumerate(unique_items)}
        self.reverse_user_mapping = {idx: user for user, idx in self.user_mapping.items()}
        self.reverse_item_mapping = {idx: item for item, idx in self.item_mapping.items()}
        
        # Create user-item matrix
        self.user_item_matrix = np.zeros((len(unique_users), len(unique_items)))
        
        for _, row in dataset_a.iterrows():
            user_idx = self.user_mapping[row['customer_id']]
            item_idx = self.item_mapping[row['article_id']]
            # Use interaction count or weighted score if available
            interaction_value = row.get('interaction_count', 1) if 'interaction_count' in row else 1
            self.user_item_matrix[user_idx, item_idx] = interaction_value
            
    def _train_svd(self) -> None:
        """
        Train SVD model for matrix factorization
        """
        # Apply SVD
        self.svd_model = TruncatedSVD(n_components=self.n_components, random_state=42)
        self.user_factors = self.svd_model.fit_transform(self.user_item_matrix)
        self.item_factors = self.svd_model.components_.T
        
    def _train_item_based(self) -> None:
        """
        Train item-based collaborative filtering
        """
        # Compute item-item similarity using cosine similarity
        self.item_item_similarity = cosine_similarity(self.user_item_matrix.T)
        
    def _train_user_based(self) -> None:
        """
        Train user-based collaborative filtering
        """
        # Compute user-user similarity using cosine similarity
        self.user_user_similarity = cosine_similarity(self.user_item_matrix)
        
    def predict(self, user_id: str = None, n: int = 10) -> pd.DataFrame:
        """
        Generate collaborative filtering recommendations
        
        Args:
            user_id: User ID for personalized recommendations
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with recommendations
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        if user_id is None:
            raise ValueError("User ID must be provided for CF recommendations")
            
        if user_id not in self.user_mapping:
            # New user - fallback to popular items
            return self._get_popular_items(n)
            
        user_idx = self.user_mapping[user_id]
        
        if self.method == "svd":
            recommendations = self._predict_svd(user_idx, n)
        elif self.method == "item_based":
            recommendations = self._predict_item_based(user_idx, n)
        elif self.method == "user_based":
            recommendations = self._predict_user_based(user_idx, n)
        else:
            raise ValueError(f"Unknown method: {self.method}")
            
        return recommendations
    
    def _predict_svd(self, user_idx: int, n: int) -> pd.DataFrame:
        """
        Generate recommendations using SVD model
        
        Args:
            user_idx: Index of the user
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with recommendations
        """
        # Predict ratings for all items
        user_vector = self.user_factors[user_idx:user_idx+1]
        predicted_ratings = np.dot(user_vector, self.item_factors.T).flatten()
        
        # Get top N items that the user hasn't interacted with
        user_interactions = self.user_item_matrix[user_idx]
        # Mask items the user has already interacted with
        mask = user_interactions == 0
        filtered_ratings = predicted_ratings[mask]
        
        # Get item indices
        item_indices = np.where(mask)[0]
        
        # Get top N
        top_n_indices = item_indices[np.argsort(filtered_ratings)[-n:][::-1]]
        top_n_scores = filtered_ratings[np.argsort(filtered_ratings)[-n:][::-1]]
        
        # Map back to article IDs
        article_ids = [self.reverse_item_mapping[idx] for idx in top_n_indices]
        
        # Create results DataFrame
        results = pd.DataFrame({
            'customer_id': [self.reverse_user_mapping[user_idx]] * len(article_ids),
            'article_id': article_ids,
            'score': top_n_scores
        })
        
        return results
    
    def _predict_item_based(self, user_idx: int, n: int) -> pd.DataFrame:
        """
        Generate recommendations using item-based CF
        
        Args:
            user_idx: Index of the user
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with recommendations
        """
        # Get items the user has interacted with
        user_interactions = self.user_item_matrix[user_idx]
        interacted_items = np.where(user_interactions > 0)[0]
        
        if len(interacted_items) == 0:
            return self._get_popular_items(n)
        
        # Calculate weighted average of similar items
        scores = np.zeros(self.user_item_matrix.shape[1])
        
        for item_idx in interacted_items:
            # Get similarity scores for this item with all other items
            similarity_scores = self.item_item_similarity[item_idx]
            # Weight by user's interaction strength
            weight = user_interactions[item_idx]
            scores += similarity_scores * weight
            
        # Mask items the user has already interacted with
        mask = user_interactions == 0
        filtered_scores = scores[mask]
        
        # Get item indices
        item_indices = np.where(mask)[0]
        
        # Get top N
        top_n_indices = item_indices[np.argsort(filtered_scores)[-n:][::-1]]
        top_n_scores = filtered_scores[np.argsort(filtered_scores)[-n:][::-1]]
        
        # Map back to article IDs
        article_ids = [self.reverse_item_mapping[idx] for idx in top_n_indices]
        
        # Create results DataFrame
        results = pd.DataFrame({
            'customer_id': [self.reverse_user_mapping[user_idx]] * len(article_ids),
            'article_id': article_ids,
            'score': top_n_scores
        })
        
        return results
    
    def _predict_user_based(self, user_idx: int, n: int) -> pd.DataFrame:
        """
        Generate recommendations using user-based CF
        
        Args:
            user_idx: Index of the user
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with recommendations
        """
        # Get similarity scores for this user with all other users
        similarity_scores = self.user_user_similarity[user_idx]
        
        # Get weighted ratings from similar users
        weighted_ratings = np.zeros(self.user_item_matrix.shape[1])
        similarity_sum = np.zeros(self.user_item_matrix.shape[1])
        
        for other_user_idx, sim_score in enumerate(similarity_scores):
            if other_user_idx != user_idx and sim_score > 0:
                # Get ratings from similar user
                other_user_ratings = self.user_item_matrix[other_user_idx]
                # Only consider items the target user hasn't interacted with
                target_user_interactions = self.user_item_matrix[user_idx]
                mask = target_user_interactions == 0
                weighted_ratings[mask] += other_user_ratings[mask] * sim_score
                similarity_sum[mask] += sim_score
                
        # Calculate final scores
        scores = np.divide(weighted_ratings, similarity_sum, 
                          out=np.zeros_like(weighted_ratings), where=similarity_sum!=0)
        
        # Get items the user hasn't interacted with
        user_interactions = self.user_item_matrix[user_idx]
        mask = user_interactions == 0
        filtered_scores = scores[mask]
        
        # Get item indices
        item_indices = np.where(mask)[0]
        
        # Get top N
        top_n_indices = item_indices[np.argsort(filtered_scores)[-n:][::-1]]
        top_n_scores = filtered_scores[np.argsort(filtered_scores)[-n:][::-1]]
        
        # Map back to article IDs
        article_ids = [self.reverse_item_mapping[idx] for idx in top_n_indices]
        
        # Create results DataFrame
        results = pd.DataFrame({
            'customer_id': [self.reverse_user_mapping[user_idx]] * len(article_ids),
            'article_id': article_ids,
            'score': top_n_scores
        })
        
        return results
    
    def _get_popular_items(self, n: int) -> pd.DataFrame:
        """
        Get popular items as fallback for new users
        
        Args:
            n: Number of items to return
            
        Returns:
            DataFrame with popular items
        """
        # Calculate item popularity (total interactions)
        item_popularity = np.sum(self.user_item_matrix, axis=0)
        
        # Get top N items
        top_n_indices = np.argsort(item_popularity)[-n:][::-1]
        top_n_scores = item_popularity[top_n_indices]
        
        # Map back to article IDs
        article_ids = [self.reverse_item_mapping[idx] for idx in top_n_indices]
        
        # Create results DataFrame (using a placeholder customer_id)
        results = pd.DataFrame({
            'customer_id': ['NEW_USER'] * len(article_ids),
            'article_id': article_ids,
            'score': top_n_scores
        })
        
        return results
    
    def get_customers_also_bought(self, article_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate "Customers Also Bought" recommendations (Section 4.3)
        
        Args:
            article_id: Article ID to find co-purchased items for
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with co-purchase recommendations
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        if article_id not in self.item_mapping:
            # Item not found - return empty DataFrame
            return pd.DataFrame(columns=['base_article_id', 'bought_together_article_id', 'score'])
            
        item_idx = self.item_mapping[article_id]
        
        if self.method == "item_based" and self.item_item_similarity is not None:
            # Use precomputed item-item similarity
            similarity_scores = self.item_item_similarity[item_idx]
            
            # Mask the item itself
            mask = np.ones(len(similarity_scores), dtype=bool)
            mask[item_idx] = False
            
            # Apply mask and get top N
            filtered_scores = similarity_scores[mask]
            item_indices = np.where(mask)[0]
            
            # Get top N indices
            top_n_indices = item_indices[np.argsort(filtered_scores)[-n:][::-1]]
            top_n_scores = filtered_scores[np.argsort(filtered_scores)[-n:][::-1]]
            
            # Map back to article IDs
            bought_together_ids = [self.reverse_item_mapping[idx] for idx in top_n_indices]
            
            # Create results DataFrame
            results = pd.DataFrame({
                'base_article_id': [article_id] * len(bought_together_ids),
                'bought_together_article_id': bought_together_ids,
                'score': top_n_scores
            })
            
            return results
        else:
            # Fallback to using user-item matrix for co-purchase analysis
            return self._compute_co_purchase_from_matrix(article_id, n)
    
    def _compute_co_purchase_from_matrix(self, article_id: str, n: int) -> pd.DataFrame:
        """
        Compute co-purchase relationships directly from user-item matrix
        
        Args:
            article_id: Article ID to find co-purchased items for
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with co-purchase recommendations
        """
        item_idx = self.item_mapping[article_id]
        
        # Get users who bought this item
        users_who_bought = np.where(self.user_item_matrix[:, item_idx] > 0)[0]
        
        if len(users_who_bought) == 0:
            return pd.DataFrame(columns=['base_article_id', 'bought_together_article_id', 'score'])
        
        # Count co-occurrences with other items
        co_occurrence_counts = np.zeros(self.user_item_matrix.shape[1])
        
        for user_idx in users_who_bought:
            # Get items this user bought
            user_items = np.where(self.user_item_matrix[user_idx] > 0)[0]
            # Increment co-occurrence count for each item (except the base item)
            for other_item_idx in user_items:
                if other_item_idx != item_idx:
                    co_occurrence_counts[other_item_idx] += 1
                    
        # Normalize by total number of users who bought the base item
        co_occurrence_scores = co_occurrence_counts / len(users_who_bought)
        
        # Mask the base item itself
        mask = np.ones(len(co_occurrence_scores), dtype=bool)
        mask[item_idx] = False
        
        # Apply mask and get top N
        filtered_scores = co_occurrence_scores[mask]
        item_indices = np.where(mask)[0]
        
        # Get top N indices
        top_n_indices = item_indices[np.argsort(filtered_scores)[-n:][::-1]]
        top_n_scores = filtered_scores[np.argsort(filtered_scores)[-n:][::-1]]
        
        # Map back to article IDs
        bought_together_ids = [self.reverse_item_mapping[idx] for idx in top_n_indices]
        
        # Create results DataFrame
        results = pd.DataFrame({
            'base_article_id': [article_id] * len(bought_together_ids),
            'bought_together_article_id': bought_together_ids,
            'score': top_n_scores
        })
        
        return results
    
    def get_cf_recommendations(self, user_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate collaborative filtering recommendations for the final output table
        
        Args:
            user_id: User ID for personalized recommendations
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with CF recommendations for the recommendations_cf table
        """
        recommendations = self.predict(user_id, n)
        
        # Rename columns to match the required output format
        recommendations.rename(columns={
            'customer_id': 'customer_id',
            'article_id': 'article_id',
            'score': 'score'
        }, inplace=True)
        
        # Add timestamp
        recommendations['updated_at'] = datetime.now()
        
        return recommendations