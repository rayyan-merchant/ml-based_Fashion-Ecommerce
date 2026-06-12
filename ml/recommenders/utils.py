"""
Utility functions for the recommendation system
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any
from datetime import datetime
import os
import pickle
import json

def load_latest_dataset(dataset_path: str) -> pd.DataFrame:
    """
    Load the latest version of a dataset from the versioned directory structure.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        DataFrame with the latest dataset
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset path {dataset_path} does not exist")
    
    # Get all version directories
    versions = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
    
    if not versions:
        raise FileNotFoundError(f"No versions found in {dataset_path}")
    
    # Sort versions and get the latest
    versions.sort(reverse=True)
    latest_version = versions[0]
    
    # Look for parquet files in the latest version
    version_path = os.path.join(dataset_path, latest_version)
    parquet_files = [f for f in os.listdir(version_path) if f.endswith('.parquet')]
    
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {version_path}")
    
    # Load the first parquet file (assuming there's only one or taking the first one)
    latest_file = os.path.join(version_path, parquet_files[0])
    return pd.read_parquet(latest_file)

def save_recommendations(df: pd.DataFrame, output_path: str, format: str = 'parquet') -> None:
    """
    Save recommendations to a file.
    
    Args:
        df: DataFrame with recommendations
        output_path: Path to save the recommendations
        format: Format to save ('parquet' or 'csv')
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Add timestamp
    df_with_timestamp = df.copy()
    df_with_timestamp['updated_at'] = datetime.now()
    
    if format == 'parquet':
        df_with_timestamp.to_parquet(f"{output_path}.parquet", index=False)
    elif format == 'csv':
        df_with_timestamp.to_csv(f"{output_path}.csv", index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    
    return dot_product / (norm_vec1 * norm_vec2)

def get_top_k_similar_items(similarity_scores: np.ndarray, k: int = 100) -> List[Tuple[int, float]]:
    """
    Get top k items with highest similarity scores.
    
    Args:
        similarity_scores: Array of similarity scores
        k: Number of top items to return
        
    Returns:
        List of (index, score) tuples for top k items
    """
    # Get indices of top k scores
    top_k_indices = np.argpartition(similarity_scores, -k)[-k:]
    # Sort by score descending
    top_k_indices = top_k_indices[np.argsort(similarity_scores[top_k_indices])[::-1]]
    
    return [(idx, similarity_scores[idx]) for idx in top_k_indices]

def calculate_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calculate weighted score from multiple recommendation scores.
    
    Args:
        scores: Dictionary of score names and values
        weights: Dictionary of score names and weights
        
    Returns:
        Weighted combined score
    """
    total_score = 0.0
    total_weight = 0.0
    
    for score_name, score_value in scores.items():
        if score_name in weights:
            total_score += score_value * weights[score_name]
            total_weight += weights[score_name]
    
    # Normalize by total weight
    if total_weight > 0:
        return total_score / total_weight
    else:
        return 0.0

def save_model(model: Any, model_path: str) -> None:
    """
    Save a trained model to disk.
    
    Args:
        model: Trained model object
        model_path: Path to save the model
    """
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

def load_model(model_path: str) -> Any:
    """
    Load a trained model from disk.
    
    Args:
        model_path: Path to the saved model
        
    Returns:
        Loaded model object
    """
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def log_evaluation_results(results: Dict[str, float], log_path: str) -> None:
    """
    Log evaluation results to a file.
    
    Args:
        results: Dictionary of metric names and values
        log_path: Path to save the log
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Add timestamp
    results_with_timestamp = results.copy()
    results_with_timestamp['timestamp'] = datetime.now().isoformat()
    
    # Append to log file
    with open(log_path, 'a') as f:
        f.write(json.dumps(results_with_timestamp) + '\n')