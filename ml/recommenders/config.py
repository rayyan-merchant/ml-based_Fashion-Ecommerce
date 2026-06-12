"""
Configuration for the recommendation system
"""
import os
from typing import Dict, Any

# Base paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'ml')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'recommendations')

# Dataset paths
DATASET_A_PATH = os.path.join(DATA_DIR, 'A_user_item_interactions')
DATASET_B_PATH = os.path.join(DATA_DIR, 'B_articles_structured')
DATASET_C_PATH = os.path.join(DATA_DIR, 'C_customer_features')
DATASET_D_PATH = os.path.join(DATA_DIR, 'D_timeseries')
DATASET_E_PATH = os.path.join(DATA_DIR, 'E_reviews_nlp')
DATASET_F_PATH = os.path.join(DATA_DIR, 'F_events_funnels')

# Output table paths
SIMILAR_ITEMS_TABLE = os.path.join(OUTPUT_DIR, 'similar_items')
YOU_MAY_ALSO_LIKE_TABLE = os.path.join(OUTPUT_DIR, 'you_may_also_like')
RECOMMENDATIONS_CF_TABLE = os.path.join(OUTPUT_DIR, 'recommendations_cf')
RECOMMENDATIONS_FINAL_TABLE = os.path.join(OUTPUT_DIR, 'recommendations_final')
TRENDING_ARTICLES_TABLE = os.path.join(OUTPUT_DIR, 'trending_articles')
CUSTOMERS_ALSO_BOUGHT_TABLE = os.path.join(OUTPUT_DIR, 'customers_also_bought')
PERSONALIZED_FEED_TABLE = os.path.join(OUTPUT_DIR, 'personalized_feed')

# Model parameters
HYBRID_RECOMMENDER_WEIGHTS: Dict[str, float] = {
    'cf_score': 0.3,
    'content_similarity': 0.2,
    'event_based_relevance': 0.2,
    'trend_score': 0.15,
    'co_purchase_score': 0.15
}

# Evaluation parameters
EVALUATION_METRICS = ['precision@k', 'recall@k', 'ndcg@k', 'coverage', 'novelty', 'diversity']

# Default values
DEFAULT_TOP_K = 100
DEFAULT_SIMILARITY_THRESHOLD = 0.5

# Database connection (for materialized tables)
DB_CONNECTION_STRING = "postgresql://user:password@localhost:5432/ecommerce"

# Feature weights for personalized feed
PERSONALIZED_FEED_WEIGHTS: Dict[str, float] = {
    'short_term_behavior': 0.4,
    'long_term_preferences': 0.3,
    'content_matching': 0.2,
    'session_progression': 0.1
}