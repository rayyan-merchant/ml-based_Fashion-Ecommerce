"""
Training script for all recommendation models
Demonstrates how to train each recommender with the required datasets
"""
import pandas as pd
import os
from typing import Dict
from datetime import datetime

from .models.content_based_recommender import ContentBasedRecommender
from .models.collaborative_filtering_recommender import CollaborativeFilteringRecommender
from .models.event_based_recommender import EventBasedRecommender
from .models.trending_recommender import TrendingRecommender
from .models.hybrid_recommender import HybridRecommender
from .evaluation.evaluator import RecommendationEvaluator
from .config import (
    DATASET_A_PATH, DATASET_B_PATH, DATASET_C_PATH, DATASET_D_PATH, 
    DATASET_E_PATH, DATASET_F_PATH, OUTPUT_DIR
)
from .utils import load_latest_dataset, save_recommendations, save_model, log_evaluation_results

def load_all_datasets() -> Dict[str, pd.DataFrame]:
    """
    Load all required datasets for training recommenders
    
    Returns:
        Dictionary of dataset names and DataFrames
    """
    datasets = {}
    
    try:
        print("Loading Dataset A (User-Item Interactions)...")
        datasets['dataset_a'] = load_latest_dataset(DATASET_A_PATH)
        print(f"Loaded {len(datasets['dataset_a'])} records from Dataset A")
    except Exception as e:
        print(f"Warning: Could not load Dataset A: {e}")
    
    try:
        print("Loading Dataset B (Article Features + Embeddings)...")
        datasets['dataset_b'] = load_latest_dataset(DATASET_B_PATH)
        print(f"Loaded {len(datasets['dataset_b'])} records from Dataset B")
    except Exception as e:
        print(f"Warning: Could not load Dataset B: {e}")
    
    try:
        print("Loading Dataset C (Customer Features)...")
        datasets['dataset_c'] = load_latest_dataset(DATASET_C_PATH)
        print(f"Loaded {len(datasets['dataset_c'])} records from Dataset C")
    except Exception as e:
        print(f"Warning: Could not load Dataset C: {e}")
    
    try:
        print("Loading Dataset D (Time Series)...")
        datasets['dataset_d'] = load_latest_dataset(DATASET_D_PATH)
        print(f"Loaded {len(datasets['dataset_d'])} records from Dataset D")
    except Exception as e:
        print(f"Warning: Could not load Dataset D: {e}")
    
    try:
        print("Loading Dataset E (Reviews NLP)...")
        datasets['dataset_e'] = load_latest_dataset(DATASET_E_PATH)
        print(f"Loaded {len(datasets['dataset_e'])} records from Dataset E")
    except Exception as e:
        print(f"Warning: Could not load Dataset E: {e}")
    
    try:
        print("Loading Dataset F (Events + Session Behavior)...")
        datasets['dataset_f'] = load_latest_dataset(DATASET_F_PATH)
        print(f"Loaded {len(datasets['dataset_f'])} records from Dataset F")
    except Exception as e:
        print(f"Warning: Could not load Dataset F: {e}")
    
    return datasets

def train_content_based_recommender(datasets: Dict[str, pd.DataFrame]) -> ContentBasedRecommender:
    """
    Train the content-based recommender
    
    Args:
        datasets: Dictionary of all datasets
        
    Returns:
        Trained content-based recommender
    """
    print("\n=== Training Content-Based Recommender ===")
    
    # Initialize recommender
    cb_recommender = ContentBasedRecommender()
    
    # Train with Dataset B
    required_datasets = {'dataset_b': datasets.get('dataset_b')}
    
    try:
        cb_recommender.train(required_datasets)
        print("Content-Based Recommender trained successfully")
        
        # Save model
        model_path = os.path.join(OUTPUT_DIR, "models", "content_based_recommender.pkl")
        save_model(cb_recommender, model_path)
        print(f"Content-Based Recommender model saved to {model_path}")
        
        return cb_recommender
        
    except Exception as e:
        print(f"Error training Content-Based Recommender: {e}")
        return None

def train_collaborative_filtering_recommender(datasets: Dict[str, pd.DataFrame]) -> CollaborativeFilteringRecommender:
    """
    Train the collaborative filtering recommender
    
    Args:
        datasets: Dictionary of all datasets
        
    Returns:
        Trained collaborative filtering recommender
    """
    print("\n=== Training Collaborative Filtering Recommender ===")
    
    # Initialize recommender
    cf_recommender = CollaborativeFilteringRecommender(method="svd")
    
    # Train with Dataset A
    required_datasets = {'dataset_a': datasets.get('dataset_a')}
    
    try:
        cf_recommender.train(required_datasets)
        print("Collaborative Filtering Recommender trained successfully")
        
        # Save model
        model_path = os.path.join(OUTPUT_DIR, "models", "collaborative_filtering_recommender.pkl")
        save_model(cf_recommender, model_path)
        print(f"Collaborative Filtering Recommender model saved to {model_path}")
        
        return cf_recommender
        
    except Exception as e:
        print(f"Error training Collaborative Filtering Recommender: {e}")
        return None

def train_event_based_recommender(datasets: Dict[str, pd.DataFrame]) -> EventBasedRecommender:
    """
    Train the event-based recommender
    
    Args:
        datasets: Dictionary of all datasets
        
    Returns:
        Trained event-based recommender
    """
    print("\n=== Training Event-Based Recommender ===")
    
    # Initialize recommender
    eb_recommender = EventBasedRecommender()
    
    # Train with Datasets F, C, and B
    required_datasets = {
        'dataset_f': datasets.get('dataset_f'),
        'dataset_c': datasets.get('dataset_c'),
        'dataset_b': datasets.get('dataset_b')
    }
    
    try:
        eb_recommender.train(required_datasets)
        print("Event-Based Recommender trained successfully")
        
        # Save model
        model_path = os.path.join(OUTPUT_DIR, "models", "event_based_recommender.pkl")
        save_model(eb_recommender, model_path)
        print(f"Event-Based Recommender model saved to {model_path}")
        
        return eb_recommender
        
    except Exception as e:
        print(f"Error training Event-Based Recommender: {e}")
        return None

def train_trending_recommender(datasets: Dict[str, pd.DataFrame]) -> TrendingRecommender:
    """
    Train the trending recommender
    
    Args:
        datasets: Dictionary of all datasets
        
    Returns:
        Trained trending recommender
    """
    print("\n=== Training Trending Recommender ===")
    
    # Initialize recommender
    trending_recommender = TrendingRecommender()
    
    # Train with Dataset D and optional Datasets F and B
    required_datasets = {
        'dataset_d': datasets.get('dataset_d'),
        'dataset_f': datasets.get('dataset_f'),
        'dataset_b': datasets.get('dataset_b')
    }
    
    try:
        trending_recommender.train(required_datasets)
        print("Trending Recommender trained successfully")
        
        # Save model
        model_path = os.path.join(OUTPUT_DIR, "models", "trending_recommender.pkl")
        save_model(trending_recommender, model_path)
        print(f"Trending Recommender model saved to {model_path}")
        
        return trending_recommender
        
    except Exception as e:
        print(f"Error training Trending Recommender: {e}")
        return None

def train_hybrid_recommender(trained_recommenders: Dict[str, object]) -> HybridRecommender:
    """
    Train the hybrid recommender by combining individual recommenders
    
    Args:
        trained_recommenders: Dictionary of trained recommenders
        
    Returns:
        Trained hybrid recommender
    """
    print("\n=== Training Hybrid Recommender ===")
    
    # Initialize recommender
    hybrid_recommender = HybridRecommender()
    
    # Add trained recommenders to the hybrid engine
    for name, recommender in trained_recommenders.items():
        if recommender is not None and recommender.is_trained:
            try:
                hybrid_recommender.add_recommender(name, recommender)
                print(f"Added {name} to hybrid engine")
            except Exception as e:
                print(f"Warning: Could not add {name} to hybrid engine: {e}")
    
    # Train with all datasets (for customer features, article metadata, etc.)
    # In this case, we're just marking it as trained since it uses other recommenders
    hybrid_recommender.is_trained = True
    hybrid_recommender.training_timestamp = datetime.now()
    
    print("Hybrid Recommender configured successfully")
    
    # Save model
    model_path = os.path.join(OUTPUT_DIR, "models", "hybrid_recommender.pkl")
    save_model(hybrid_recommender, model_path)
    print(f"Hybrid Recommender model saved to {model_path}")
    
    return hybrid_recommender

def generate_recommendations(recommenders: Dict[str, object], datasets: Dict[str, pd.DataFrame]):
    """
    Generate recommendations using trained recommenders and save to output tables
    
    Args:
        recommenders: Dictionary of trained recommenders
        datasets: Dictionary of all datasets
    """
    print("\n=== Generating Recommendations ===")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "models"), exist_ok=True)
    
    # Generate sample recommendations for demonstration
    # In a real implementation, you would iterate through all users/items
    
    # Example: Generate recommendations for a sample user and article
    sample_user_id = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    sample_article_id = "123456789"
    
    # 1. Similar Items
    if 'content_based' in recommenders and recommenders['content_based'] is not None:
        try:
            similar_items = recommenders['content_based'].get_similar_items(sample_article_id, 10)
            save_recommendations(similar_items, os.path.join(OUTPUT_DIR, "similar_items"))
            print(f"Generated {len(similar_items)} similar items recommendations")
        except Exception as e:
            print(f"Warning: Could not generate similar items recommendations: {e}")
    
    # 2. You May Also Like
    if 'content_based' in recommenders and recommenders['content_based'] is not None:
        try:
            ymal = recommenders['content_based'].get_you_may_also_like(sample_article_id, 10)
            save_recommendations(ymal, os.path.join(OUTPUT_DIR, "you_may_also_like"))
            print(f"Generated {len(ymal)} 'You May Also Like' recommendations")
        except Exception as e:
            print(f"Warning: Could not generate 'You May Also Like' recommendations: {e}")
    
    # 3. Customers Also Bought
    if 'collaborative_filtering' in recommenders and recommenders['collaborative_filtering'] is not None:
        try:
            cab = recommenders['collaborative_filtering'].get_customers_also_bought(sample_article_id, 10)
            save_recommendations(cab, os.path.join(OUTPUT_DIR, "customers_also_bought"))
            print(f"Generated {len(cab)} 'Customers Also Bought' recommendations")
        except Exception as e:
            print(f"Warning: Could not generate 'Customers Also Bought' recommendations: {e}")
    
    # 4. Collaborative Filtering Recommendations
    if 'collaborative_filtering' in recommenders and recommenders['collaborative_filtering'] is not None:
        try:
            cf_recs = recommenders['collaborative_filtering'].get_cf_recommendations(sample_user_id, 10)
            save_recommendations(cf_recs, os.path.join(OUTPUT_DIR, "recommendations_cf"))
            print(f"Generated {len(cf_recs)} CF recommendations")
        except Exception as e:
            print(f"Warning: Could not generate CF recommendations: {e}")
    
    # 5. Personalized Feed
    if 'event_based' in recommenders and recommenders['event_based'] is not None:
        try:
            pf = recommenders['event_based'].get_personalized_feed(sample_user_id, 10)
            save_recommendations(pf, os.path.join(OUTPUT_DIR, "personalized_feed"))
            print(f"Generated {len(pf)} personalized feed recommendations")
        except Exception as e:
            print(f"Warning: Could not generate personalized feed recommendations: {e}")
    
    # 6. Trending Articles
    if 'trending' in recommenders and recommenders['trending'] is not None:
        try:
            ta = recommenders['trending'].get_trending_articles(10)
            save_recommendations(ta, os.path.join(OUTPUT_DIR, "trending_articles"))
            print(f"Generated {len(ta)} trending articles recommendations")
        except Exception as e:
            print(f"Warning: Could not generate trending articles recommendations: {e}")
    
    # 7. Final Hybrid Recommendations
    if 'hybrid' in recommenders and recommenders['hybrid'] is not None:
        try:
            final_recs = recommenders['hybrid'].get_recommendations_final(sample_user_id, 10)
            save_recommendations(final_recs, os.path.join(OUTPUT_DIR, "recommendations_final"))
            print(f"Generated {len(final_recs)} final hybrid recommendations")
        except Exception as e:
            print(f"Warning: Could not generate final hybrid recommendations: {e}")

def evaluate_recommenders(trained_recommenders: Dict[str, object], test_data: pd.DataFrame):
    """
    Evaluate all trained recommenders
    
    Args:
        trained_recommenders: Dictionary of trained recommenders
        test_data: Test data for evaluation
    """
    print("\n=== Evaluating Recommenders ===")
    
    evaluator = RecommendationEvaluator()
    evaluation_log_path = os.path.join(OUTPUT_DIR, "evaluation", "results.log")
    os.makedirs(os.path.join(OUTPUT_DIR, "evaluation"), exist_ok=True)
    
    for name, recommender in trained_recommenders.items():
        if recommender is not None and recommender.is_trained:
            try:
                print(f"\nEvaluating {name}...")
                metrics = evaluator.evaluate(recommender, test_data, k=10)
                
                # Print results
                print(f"{name} Evaluation Results:")
                for metric, value in metrics.items():
                    print(f"  {metric}: {value:.4f}")
                
                # Log results
                metrics['recommender'] = name
                log_evaluation_results(metrics, evaluation_log_path)
                print(f"Evaluation results logged to {evaluation_log_path}")
                
            except Exception as e:
                print(f"Warning: Could not evaluate {name}: {e}")

def main():
    """
    Main training function
    """
    print("Starting Recommendation System Training")
    print("=" * 50)
    
    # Load all datasets
    datasets = load_all_datasets()
    
    if not datasets:
        print("Error: No datasets loaded. Cannot proceed with training.")
        return
    
    # Train individual recommenders
    trained_recommenders = {}
    
    # Train Content-Based Recommender
    trained_recommenders['content_based'] = train_content_based_recommender(datasets)
    
    # Train Collaborative Filtering Recommender
    trained_recommenders['collaborative_filtering'] = train_collaborative_filtering_recommender(datasets)
    
    # Train Event-Based Recommender
    trained_recommenders['event_based'] = train_event_based_recommender(datasets)
    
    # Train Trending Recommender
    trained_recommenders['trending'] = train_trending_recommender(datasets)
    
    # Train Hybrid Recommender
    trained_recommenders['hybrid'] = train_hybrid_recommender(trained_recommenders)
    
    # Generate recommendations
    generate_recommendations(trained_recommenders, datasets)
    
    # Evaluate recommenders (if test data is available)
    # In a real implementation, you would load actual test data
    # For demonstration, we'll create dummy test data
    if 'dataset_a' in datasets and not datasets['dataset_a'].empty:
        # Use a sample of the dataset as test data
        test_data = datasets['dataset_a'].sample(min(1000, len(datasets['dataset_a'])))
        evaluate_recommenders(trained_recommenders, test_data)
    
    print("\n" + "=" * 50)
    print("Recommendation System Training Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()