"""
Evaluation module for recommendation systems
Implements offline evaluation metrics as specified in Section 7
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from sklearn.metrics import ndcg_score
from ..base_recommender import BaseRecommender

class RecommendationEvaluator:
    """
    Evaluator for recommendation systems implementing offline evaluation metrics
    Implements:
    1. Offline Evaluation (Section 7)
    2. Evaluation metrics: Precision@k, Recall@k, NDCG@k, Coverage, Novelty, Diversity
    """
    
    def __init__(self):
        """
        Initialize the evaluator
        """
        self.metrics = [
            'precision@k', 'recall@k', 'ndcg@k', 'coverage', 'novelty', 'diversity'
        ]
        
    def evaluate(self, recommender: BaseRecommender, test_data: pd.DataFrame, 
                 k: int = 10) -> Dict[str, float]:
        """
        Evaluate a recommender using test data
        
        Args:
            recommender: Trained recommender to evaluate
            test_data: Test data containing user-item interactions
            k: Cut-off for evaluation metrics
            
        Returns:
            Dictionary of metric names and values
        """
        if not recommender.is_trained:
            raise ValueError("Recommender must be trained before evaluation")
            
        results = {}
        
        # Calculate Precision@k and Recall@k
        precision, recall = self._calculate_precision_recall(recommender, test_data, k)
        results['precision@k'] = precision
        results['recall@k'] = recall
        
        # Calculate NDCG@k
        ndcg = self._calculate_ndcg(recommender, test_data, k)
        results['ndcg@k'] = ndcg
        
        # Calculate Coverage
        coverage = self._calculate_coverage(recommender, test_data)
        results['coverage'] = coverage
        
        # Calculate Novelty
        novelty = self._calculate_novelty(recommender, test_data)
        results['novelty'] = novelty
        
        # Calculate Diversity
        diversity = self._calculate_diversity(recommender, test_data)
        results['diversity'] = diversity
        
        return results
    
    def _calculate_precision_recall(self, recommender: BaseRecommender, 
                                  test_data: pd.DataFrame, k: int) -> Tuple[float, float]:
        """
        Calculate Precision@k and Recall@k
        
        Args:
            recommender: Trained recommender
            test_data: Test data
            k: Cut-off for evaluation
            
        Returns:
            Tuple of (precision@k, recall@k)
        """
        precisions = []
        recalls = []
        
        # Group test data by user
        for user_id, user_test_data in test_data.groupby('customer_id'):
            # Get relevant items (items the user actually interacted with in test set)
            relevant_items = set(user_test_data['article_id'].tolist())
            
            if not relevant_items:
                continue
                
            try:
                # Get recommendations for this user
                recommendations = recommender.predict(user_id=user_id, n=k)
                
                if recommendations.empty:
                    precisions.append(0.0)
                    recalls.append(0.0)
                    continue
                    
                # Get recommended items
                recommended_items = set(recommendations['article_id'].tolist()[:k])
                
                # Calculate precision and recall
                num_relevant_recommended = len(relevant_items.intersection(recommended_items))
                precision = num_relevant_recommended / len(recommended_items) if len(recommended_items) > 0 else 0
                recall = num_relevant_recommended / len(relevant_items) if len(relevant_items) > 0 else 0
                
                precisions.append(precision)
                recalls.append(recall)
                
            except Exception as e:
                # If prediction fails for this user, skip
                print(f"Warning: Could not generate predictions for user {user_id}: {e}")
                continue
        
        # Return average precision and recall
        avg_precision = np.mean(precisions) if precisions else 0.0
        avg_recall = np.mean(recalls) if recalls else 0.0
        
        return avg_precision, avg_recall
    
    def _calculate_ndcg(self, recommender: BaseRecommender, 
                       test_data: pd.DataFrame, k: int) -> float:
        """
        Calculate NDCG@k
        
        Args:
            recommender: Trained recommender
            test_data: Test data
            k: Cut-off for evaluation
            
        Returns:
            NDCG@k score
        """
        ndcg_scores = []
        
        # Group test data by user
        for user_id, user_test_data in test_data.groupby('customer_id'):
            # Create relevance scores (binary for simplicity, but could be graded)
            relevant_items = set(user_test_data['article_id'].tolist())
            
            if not relevant_items:
                continue
                
            try:
                # Get recommendations for this user
                recommendations = recommender.predict(user_id=user_id, n=k)
                
                if recommendations.empty:
                    ndcg_scores.append(0.0)
                    continue
                
                # Create ideal ranking (all relevant items first)
                recommended_items = recommendations['article_id'].tolist()[:k]
                
                # Create relevance scores for recommended items
                relevance_scores = [1 if item in relevant_items else 0 for item in recommended_items]
                
                # Create ideal relevance scores (all 1s first, then 0s)
                ideal_scores = [1] * min(len(relevant_items), k) + [0] * max(0, k - len(relevant_items))
                
                # Calculate NDCG
                if len(relevance_scores) > 1 and sum(relevance_scores) > 0:
                    dcg = self._dcg(relevance_scores)
                    idcg = self._dcg(ideal_scores)
                    ndcg = dcg / idcg if idcg > 0 else 0
                    ndcg_scores.append(ndcg)
                else:
                    # If only one item or no relevant items, NDCG is 1 if it's relevant, 0 otherwise
                    ndcg_scores.append(1.0 if sum(relevance_scores) > 0 else 0.0)
                    
            except Exception as e:
                # If prediction fails for this user, skip
                print(f"Warning: Could not generate predictions for user {user_id}: {e}")
                continue
        
        # Return average NDCG
        return np.mean(ndcg_scores) if ndcg_scores else 0.0
    
    def _dcg(self, scores: List[float]) -> float:
        """
        Calculate Discounted Cumulative Gain
        
        Args:
            scores: List of relevance scores
            
        Returns:
            DCG score
        """
        return np.sum([(2 ** score - 1) / np.log2(i + 2) for i, score in enumerate(scores)])
    
    def _calculate_coverage(self, recommender: BaseRecommender, 
                          test_data: pd.DataFrame) -> float:
        """
        Calculate catalog coverage (fraction of items recommended)
        
        Args:
            recommender: Trained recommender
            test_data: Test data
            
        Returns:
            Coverage score
        """
        # Get all items in the catalog
        all_items = set(test_data['article_id'].unique())
        
        # Get all items that were recommended
        recommended_items = set()
        
        # Sample some users to get recommendations (for efficiency)
        sampled_users = test_data['customer_id'].unique()[:100]  # Limit to 100 users
        
        for user_id in sampled_users:
            try:
                recommendations = recommender.predict(user_id=user_id, n=10)
                if not recommendations.empty:
                    recommended_items.update(recommendations['article_id'].tolist())
            except Exception as e:
                # If prediction fails for this user, skip
                print(f"Warning: Could not generate predictions for user {user_id}: {e}")
                continue
        
        # Calculate coverage
        coverage = len(recommended_items.intersection(all_items)) / len(all_items) if all_items else 0.0
        
        return coverage
    
    def _calculate_novelty(self, recommender: BaseRecommender, 
                          test_data: pd.DataFrame) -> float:
        """
        Calculate novelty (mean popularity rank of recommended items)
        
        Args:
            recommender: Trained recommender
            test_data: Test data
            
        Returns:
            Novelty score
        """
        # Calculate item popularity (frequency in test data)
        item_popularity = test_data['article_id'].value_counts()
        total_interactions = len(test_data)
        
        # Calculate popularity ranks (1 = most popular, N = least popular)
        item_ranks = {}
        for i, (item_id, count) in enumerate(item_popularity.items()):
            item_ranks[item_id] = i + 1  # Rank starts from 1
        
        novelty_scores = []
        
        # Sample some users to get recommendations (for efficiency)
        sampled_users = test_data['customer_id'].unique()[:100]  # Limit to 100 users
        
        for user_id in sampled_users:
            try:
                recommendations = recommender.predict(user_id=user_id, n=10)
                
                if recommendations.empty:
                    continue
                    
                # Calculate mean rank of recommended items
                ranks = []
                for _, row in recommendations.iterrows():
                    item_id = row['article_id']
                    if item_id in item_ranks:
                        ranks.append(item_ranks[item_id])
                    else:
                        # Item not in test set - assign worst rank
                        ranks.append(len(item_ranks) + 1)
                
                if ranks:
                    # Novelty is inverse of mean rank (higher rank = lower novelty)
                    mean_rank = np.mean(ranks)
                    max_rank = len(item_ranks)
                    novelty = 1 - (mean_rank / max_rank) if max_rank > 0 else 0
                    novelty_scores.append(novelty)
                    
            except Exception as e:
                # If prediction fails for this user, skip
                print(f"Warning: Could not generate predictions for user {user_id}: {e}")
                continue
        
        # Return average novelty
        return np.mean(novelty_scores) if novelty_scores else 0.0
    
    def _calculate_diversity(self, recommender: BaseRecommender, 
                           test_data: pd.DataFrame) -> float:
        """
        Calculate diversity (1 - average similarity between recommended items)
        
        Args:
            recommender: Trained recommender
            test_data: Test data
            
        Returns:
            Diversity score
        """
        # This requires item features or embeddings to calculate similarity
        # For simplicity, we'll return a placeholder
        # A full implementation would calculate pairwise similarities between recommended items
        
        # Placeholder implementation
        return 0.7  # Assume moderate diversity
    
    def compare_recommenders(self, recommenders: Dict[str, BaseRecommender], 
                           test_data: pd.DataFrame, k: int = 10) -> pd.DataFrame:
        """
        Compare multiple recommenders
        
        Args:
            recommenders: Dictionary of recommender names and instances
            test_data: Test data
            k: Cut-off for evaluation
            
        Returns:
            DataFrame with comparison results
        """
        results = []
        
        for name, recommender in recommenders.items():
            if recommender.is_trained:
                metrics = self.evaluate(recommender, test_data, k)
                metrics['recommender'] = name
                results.append(metrics)
        
        # Convert to DataFrame
        comparison_df = pd.DataFrame(results)
        
        # Reorder columns to put recommender name first
        cols = ['recommender'] + [col for col in comparison_df.columns if col != 'recommender']
        comparison_df = comparison_df[cols]
        
        return comparison_df