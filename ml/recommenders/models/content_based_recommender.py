"""
Content-Based Similarity Recommender
Implements "You May Also Like" and "Similar Items" recommenders
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from ..base_recommender import BaseRecommender
from ..config import DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD
from ..utils import cosine_similarity as custom_cosine_similarity

class ContentBasedRecommender(BaseRecommender):
    """
    Content-Based Recommender using article embeddings and metadata
    Implements:
    1. You May Also Like (Product Page)
    2. Similar Products (Product Page)
    """
    
    def __init__(self, name: str = "content_based_recommender"):
        """
        Initialize the content-based recommender
        """
        super().__init__(name)
        self.article_embeddings = None
        self.article_metadata = None
        self.similarity_matrix = None
        self.top_k = DEFAULT_TOP_K
        self.similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD
        
    def train(self, datasets: Dict[str, pd.DataFrame]) -> None:
        """
        Train the content-based recommender using Dataset B
        
        Args:
            datasets: Dictionary containing Dataset B (article features/embeddings)
        """
        if 'dataset_b' not in datasets:
            raise ValueError("Dataset B (article features) is required for content-based recommender")
            
        dataset_b = datasets['dataset_b']
        
        # Extract embeddings (assuming they're in a column named 'embeddings')
        # In practice, this might be multiple columns or a separate embedding file
        embedding_columns = [col for col in dataset_b.columns if 'embedding' in col.lower()]
        
        if embedding_columns:
            self.article_embeddings = dataset_b[['article_id'] + embedding_columns].copy()
        else:
            # Fallback to using textual features if embeddings aren't available
            self._generate_embeddings_from_text(dataset_b)
            
        # Store metadata for filtering
        metadata_columns = ['article_id', 'product_code', 'prod_name', 'product_type_name', 
                           'product_group_name', 'colour_group_name', 'index_group_name',
                           'section_name', 'garment_group_name', 'price']
        available_metadata = [col for col in metadata_columns if col in dataset_b.columns]
        self.article_metadata = dataset_b[available_metadata].copy()
        
        # Precompute similarity matrix for efficiency
        self._precompute_similarity_matrix()
        
        self.is_trained = True
        self.training_timestamp = datetime.now()
        
    def _generate_embeddings_from_text(self, dataset_b: pd.DataFrame) -> None:
        """
        Generate TF-IDF embeddings from text features when embeddings aren't available
        
        Args:
            dataset_b: Dataset B DataFrame
        """
        # Combine text features for embedding generation
        text_features = []
        for _, row in dataset_b.iterrows():
            text = ""
            if 'prod_name' in row:
                text += f"{row['prod_name']} "
            if 'product_type_name' in row:
                text += f"{row['product_type_name']} "
            if 'product_group_name' in row:
                text += f"{row['product_group_name']} "
            if 'detail_desc' in row:
                text += f"{row['detail_desc']} "
            text_features.append(text.strip())
        
        # Generate TF-IDF embeddings
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(text_features)
        
        # Convert to DataFrame
        embedding_df = pd.DataFrame(tfidf_matrix.toarray())
        embedding_columns = [f"tfidf_{i}" for i in range(embedding_df.shape[1])]
        embedding_df.columns = embedding_columns
        
        # Combine with article_id
        self.article_embeddings = pd.concat([
            dataset_b[['article_id']].reset_index(drop=True),
            embedding_df
        ], axis=1)
        
    def _precompute_similarity_matrix(self) -> None:
        """
        Precompute the similarity matrix for all articles
        """
        if self.article_embeddings is None:
            raise ValueError("Article embeddings must be loaded before computing similarity matrix")
            
        # Extract embedding values (excluding article_id)
        embedding_columns = [col for col in self.article_embeddings.columns if col != 'article_id']
        embedding_matrix = self.article_embeddings[embedding_columns].values
        
        # Compute cosine similarity matrix
        self.similarity_matrix = cosine_similarity(embedding_matrix)
        
    def predict(self, item_id: str = None, n: int = 10) -> pd.DataFrame:
        """
        Generate content-based recommendations for a given item
        
        Args:
            item_id: Article ID to find similar items for
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with similar items and similarity scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        if item_id is None:
            raise ValueError("Item ID must be provided for content-based recommendations")
            
        # Find the index of the given item
        item_idx = self.article_embeddings[
            self.article_embeddings['article_id'] == item_id
        ].index
        
        if len(item_idx) == 0:
            raise ValueError(f"Item ID {item_id} not found in the dataset")
            
        item_idx = item_idx[0]
        
        # Get similarity scores for this item
        similarity_scores = self.similarity_matrix[item_idx]
        
        # Get top N similar items (excluding the item itself)
        # Create a mask to exclude the item itself
        mask = np.ones(len(similarity_scores), dtype=bool)
        mask[item_idx] = False
        
        # Apply mask and get top N
        filtered_scores = similarity_scores[mask]
        article_indices = np.where(mask)[0]
        
        # Get top N indices
        top_n_indices = article_indices[np.argsort(filtered_scores)[-n:][::-1]]
        top_n_scores = filtered_scores[np.argsort(filtered_scores)[-n:][::-1]]
        
        # Get article IDs
        similar_article_ids = self.article_embeddings.iloc[top_n_indices]['article_id'].values
        
        # Create results DataFrame
        results = pd.DataFrame({
            'article_id': [item_id] * len(similar_article_ids),
            'similar_article_id': similar_article_ids,
            'similarity_score': top_n_scores
        })
        
        return results
    
    def get_you_may_also_like(self, article_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate "You May Also Like" recommendations (Section 4.1)
        
        Args:
            article_id: Article ID to find recommendations for
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with recommendations for the "You May Also Like" section
        """
        # Get basic similarity recommendations
        recommendations = self.predict(article_id, n)
        
        # Apply secondary filters (category, section, garment group)
        if self.article_metadata is not None:
            # Get metadata for the base article
            base_article_meta = self.article_metadata[
                self.article_metadata['article_id'] == article_id
            ]
            
            if not base_article_meta.empty:
                base_meta = base_article_meta.iloc[0]
                
                # Filter recommendations by same category/section/garment group
                # This is a simplified approach - in practice, you might want more sophisticated filtering
                recommendations = self._apply_secondary_filters(
                    recommendations, base_meta, n
                )
        
        # Add timestamp
        recommendations['updated_at'] = datetime.now()
        
        return recommendations
    
    def _apply_secondary_filters(self, recommendations: pd.DataFrame, 
                                base_meta: pd.Series, n: int) -> pd.DataFrame:
        """
        Apply secondary filters based on metadata
        
        Args:
            recommendations: Initial recommendations
            base_meta: Metadata for the base article
            n: Number of recommendations to return
            
        Returns:
            Filtered recommendations
        """
        # Merge with metadata to get information about recommended articles
        merged = recommendations.merge(
            self.article_metadata, 
            left_on='similar_article_id', 
            right_on='article_id',
            how='left'
        )
        
        # Apply filters based on available metadata
        filtered = merged.copy()
        
        # Filter by product group if available
        if 'product_group_name' in base_meta and 'product_group_name' in merged.columns:
            filtered = filtered[
                filtered['product_group_name'] == base_meta['product_group_name']
            ]
            
        # Filter by index group if available
        if 'index_group_name' in base_meta and 'index_group_name' in merged.columns:
            filtered = filtered[
                filtered['index_group_name'] == base_meta['index_group_name']
            ]
            
        # If we have too few results after filtering, return the original recommendations
        if len(filtered) < n // 2:
            return recommendations.head(n)
            
        # Sort by similarity score and return top n
        filtered = filtered.sort_values('similarity_score', ascending=False)
        return filtered[['article_id', 'similar_article_id', 'similarity_score']].head(n)
    
    def get_similar_items(self, article_id: str, n: int = 10) -> pd.DataFrame:
        """
        Generate "Similar Products" recommendations (Section 4.2)
        
        Args:
            article_id: Article ID to find similar items for
            n: Number of recommendations to generate
            
        Returns:
            DataFrame with similar items for the "Similar Products" section
        """
        # For similar products, we focus more on visual/textual similarity
        # This is essentially the same as the basic predict method but with
        # potentially different post-processing
        recommendations = self.predict(article_id, n)
        
        # Add timestamp
        recommendations['updated_at'] = datetime.now()
        
        return recommendations
    
    def save_model(self, path: str) -> None:
        """
        Save the trained model
        
        Args:
            path: Path to save the model
        """
        super().save_model(path)
        # In practice, you would save the embeddings and similarity matrix
        # This is a simplified implementation