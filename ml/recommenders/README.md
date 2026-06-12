# Recommendation System

This directory contains the implementation of all recommendation algorithms for the Fashion E-Commerce ML system.

## Directory Structure

```
recommenders/
├── models/                 # Individual recommender implementations
├── evaluation/             # Evaluation metrics and comparison tools
├── serving/                # API serving layer
├── config.py              # Configuration settings
├── utils.py               # Utility functions
├── base_recommender.py    # Abstract base class for recommenders
├── train_recommenders.py  # Training script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Implemented Recommenders

### 1. Content-Based Recommender (`content_based_recommender.py`)
- Implements "You May Also Like" (Product Page) - Section 4.1
- Implements "Similar Products" (Product Page) - Section 4.2
- Uses article embeddings and metadata from Dataset B

### 2. Collaborative Filtering Recommender (`collaborative_filtering_recommender.py`)
- Implements "Customers Also Bought" (Home Page) - Section 4.3
- Provides CF scores for the Hybrid Engine - Section 5
- Uses user-item interactions from Dataset A

### 3. Event-Based Recommender (`event_based_recommender.py`)
- Implements "Based on Your Interactions" (Home Page) - Section 4.4
- Provides event-based relevance scores for the Hybrid Engine - Section 5
- Uses events and customer features from Datasets F and C

### 4. Trending Recommender (`trending_recommender.py`)
- Implements "Trending Articles" (Home Page) - Section 4.5
- Provides trend scores for the Hybrid Engine - Section 5
- Uses time series data from Dataset D

### 5. Hybrid Recommender (`hybrid_recommender.py`)
- Implements the Hybrid Recommendation Engine (Global Layer) - Section 5
- Combines all individual recommenders with weighted ensemble
- Produces final recommendations for `recommendations_final` table

## Output Tables

All recommenders write their results to dedicated materialized tables or Parquet artifacts as specified in Section 3:

1. `similar_items` - Content-based similarity outputs
2. `you_may_also_like` - You May Also Like recommendations
3. `recommendations_cf` - Collaborative filtering recommendations
4. `recommendations_final` - Final hybrid recommendations
5. `trending_articles` - Trending articles
6. `customers_also_bought` - Co-purchase recommendations
7. `personalized_feed` - Personalized recommendations

## Evaluation

The system implements comprehensive offline evaluation metrics as specified in Section 7:

- Precision@k
- Recall@k
- NDCG@k
- Coverage
- Novelty
- Diversity

## Serving

Recommendations are served via a FastAPI-based REST API that implements the serving requirements from Section 6.

## Training

To train all recommenders, run:

```bash
python train_recommenders.py
```

This script will:
1. Load all required datasets (A-F)
2. Train each individual recommender
3. Configure the hybrid recommender
4. Generate sample recommendations
5. Evaluate all recommenders

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Architecture Compliance

This implementation fully complies with the requirements specified in `context.md`:

- **Modular**: Each recommender is implemented as a separate class
- **Reproducible**: All models can be saved/loaded, with versioned outputs
- **Scalable**: Designed for distributed training and serving
- **Production-ready**: Includes error handling, logging, and monitoring
- **Testable**: Comprehensive evaluation framework included

## Next Steps

1. Integrate with the existing Airflow ETL pipeline
2. Add online evaluation capabilities (A/B testing)
3. Implement real-time recommendation serving
4. Add more sophisticated models (deep learning, reinforcement learning)
5. Implement monitoring and alerting for recommendation quality