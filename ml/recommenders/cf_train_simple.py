# ==========================================================
# 🚀 Collaborative Filtering – Optimized CPU Version
# ==========================================================

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import time
import pickle

print("="*70)
print("🚀 COLLABORATIVE FILTERING (CPU - Optimized)")
print("="*70)

# ---------------------- CONFIG ----------------------
# Get project root (2 levels up from ml/recommenders/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "hm" / "transactions_train.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "recommendations"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

print(f"📂 Project root: {PROJECT_ROOT}")
print(f"📂 Input: {INPUT_PATH}")
print(f"📂 Output: {OUTPUT_DIR}\n")

N_SAMPLE_USERS = 50000      # Users to process
N_COMPONENTS = 50           # SVD dimensions
N_NEIGHBORS = 20            # Similar users
N_RECOMMENDATIONS = 20      # Recommendations per user
N_JOBS = -1                 # Use all CPU cores

# ---------------------- LOAD CSV ----------------------
print("\n📂 Loading CSV...")
start_total = time.time()

# Verify input file exists
if not INPUT_PATH.exists():
    print(f"❌ ERROR: File not found: {INPUT_PATH}")
    print(f"   Please ensure transactions_train.csv exists in {INPUT_PATH.parent}")
    exit(1)

df = pd.read_csv(INPUT_PATH, header=None)
df.columns = [
    "transaction_id", "t_dat", "customer_id", "article_id", "price", "sales_channel_id"
]

print(f"✓ Loaded: {len(df):,} transactions")
print(f"  Columns: {list(df.columns)}")

# ---------------------- CLEANING ----------------------
print("\n🧹 Cleaning data...")
df = df[["customer_id", "article_id", "t_dat", "price"]].copy()

# Clean and convert
df["customer_id"] = df["customer_id"].astype(str).str.strip()
df["article_id"] = df["article_id"].astype(str).str.strip()
df["price"] = pd.to_numeric(df["price"], errors='coerce')
df["t_dat"] = pd.to_datetime(df["t_dat"], errors='coerce')

# Drop nulls
df = df.dropna()

print(f"✓ After cleaning: {len(df):,} transactions")
print(f"  Date range: {df['t_dat'].min().date()} to {df['t_dat'].max().date()}")

# ---------------------- TIME-WEIGHTED SCORE ----------------------
print("\n⚖️ Computing time-weighted scores...")

max_date = df["t_dat"].max()
df["days_ago"] = (max_date - df["t_dat"]).dt.days

# Recency weight: e^(-days/30)
df["recency_weight"] = np.exp(-df["days_ago"].astype(float) / 30.0)

# Aggregate by customer-item
print("  Aggregating interactions...")
interactions = (
    df.groupby(["customer_id", "article_id"])
    .agg({
        "recency_weight": "sum",
        "price": "sum"
    })
    .reset_index()
)

# Combined score
max_price = interactions["price"].max()
interactions["score"] = (
    interactions["recency_weight"] * 
    (interactions["price"] / max_price + 0.1)
)

print(f"✓ Interactions: {len(interactions):,} unique pairs")

# ============================================================
# ✅ FIX #1: ADD DATA SCALING (CRITICAL)
# ============================================================
print("\n📊 Scaling scores (FIX #1)...")

scaler = StandardScaler()
interactions["score"] = scaler.fit_transform(interactions[["score"]])

print(f"✓ After scaling:")
print(f"  Mean: {interactions['score'].mean():.6f}")
print(f"  Std: {interactions['score'].std():.6f}")
print(f"  Min: {interactions['score'].min():.6f}")
print(f"  Max: {interactions['score'].max():.6f}")

# ---------------------- SAMPLE TOP USERS ----------------------
print(f"\n🧪 Sampling top {N_SAMPLE_USERS:,} active users...")

# Get top active users
user_activity = (
    interactions.groupby("customer_id")
    .size()
    .sort_values(ascending=False)
    .head(N_SAMPLE_USERS)
)

top_users = user_activity.index.tolist()
print(f"✓ Selected {len(top_users):,} users")

# Filter to these users
subset = interactions[interactions["customer_id"].isin(top_users)].copy()
print(f"✓ Filtered to {len(subset):,} interactions")

# ---------------------- ENCODE IDs ----------------------
print("\n🔢 Encoding IDs...")

# Get unique IDs
unique_customers = subset["customer_id"].unique()
unique_items = subset["article_id"].unique()

# Create mappings
customer_to_idx = {cid: idx for idx, cid in enumerate(unique_customers)}
item_to_idx = {aid: idx for idx, aid in enumerate(unique_items)}

# Reverse mappings
idx_to_customer = {idx: cid for cid, idx in customer_to_idx.items()}
idx_to_item = {idx: aid for aid, idx in item_to_idx.items()}

# Map to indices
subset["u"] = subset["customer_id"].map(customer_to_idx)
subset["i"] = subset["article_id"].map(item_to_idx)

# Remove missing mappings
subset = subset.dropna(subset=["u", "i", "score"])
subset["u"] = subset["u"].astype(int)
subset["i"] = subset["i"].astype(int)

n_users = len(customer_to_idx)
n_items = len(item_to_idx)

print(f"✓ Matrix: {n_users:,} users × {n_items:,} items")

# ---------------------- BUILD SPARSE MATRIX ----------------------
print("\n🏗 Building sparse matrix...")

matrix = csr_matrix(
    (subset["score"].values, (subset["u"].values, subset["i"].values)),
    shape=(n_users, n_items),
    dtype=np.float32
)

sparsity = 1 - (matrix.nnz / (n_users * n_items))
print(f"✓ Matrix shape: {matrix.shape}")
print(f"  Non-zero entries: {matrix.nnz:,}")
print(f"  Sparsity: {sparsity:.4%}")
print(f"  Memory: {matrix.data.nbytes / 1e6:.1f} MB")

# ---------------------- SVD (CPU - Highly Optimized) ----------------------
print(f"\n⚙️ Computing Truncated SVD ({N_COMPONENTS} components)...")
print(f"  Algorithm: Randomized (fast for sparse matrices)")
print(f"  Using all CPU cores...")

start = time.time()

svd = TruncatedSVD(
    n_components=N_COMPONENTS,
    algorithm='randomized',  # Faster than 'arpack' for sparse
    n_iter=7,                # Good balance of speed/accuracy
    random_state=42,
    n_oversamples=10         # Improves accuracy slightly
)

user_factors = svd.fit_transform(matrix)
item_factors = svd.components_.T

svd_time = time.time() - start

print(f"✓ SVD completed in {svd_time:.1f}s")
print(f"  User factors: {user_factors.shape}")
print(f"  Item factors: {item_factors.shape}")
print(f"  Variance explained: {svd.explained_variance_ratio_.sum():.2%}")

# ============================================================
# ✅ FIX #2: ADD ITEM-ITEM SIMILARITY
# ============================================================
print(f"\n🔗 Computing item-item similarity (FIX #2)...")

item_factors_normalized = normalize(item_factors, norm='l2', axis=1)
item_item_similarity = cosine_similarity(item_factors_normalized)

print(f"✓ Item similarity matrix: {item_item_similarity.shape}")
print(f"  Avg similarity: {item_item_similarity[np.triu_indices_from(item_item_similarity, k=1)].mean():.4f}")

# ============================================================
# ✅ FIX #3: ADD COLD-START FALLBACK FUNCTION
# ============================================================
def get_popular_items(subset_data, n=20):
    """Get popular items for cold-start users"""
    popular = (
        subset_data.groupby("i")["score"]
        .sum()
        .nlargest(n)
    )
    return list(popular.index), popular.values

# ---------------------- KNN INDEX (CPU - Optimized) ----------------------
print(f"\n🤖 Building KNN index (k={N_NEIGHBORS+1})...")

start = time.time()

# Option 1: Normalize user factors for cosine similarity with euclidean metric
# (This is faster and mathematically equivalent)
from sklearn.preprocessing import normalize

user_factors_normalized = normalize(user_factors, norm='l2', axis=1)

knn = NearestNeighbors(
    n_neighbors=min(N_NEIGHBORS + 1, n_users),
    algorithm='ball_tree',   # Fast tree-based search
    metric='euclidean',      # On normalized vectors = cosine similarity
    n_jobs=N_JOBS
)

knn.fit(user_factors_normalized)

knn_time = time.time() - start
print(f"✓ KNN index built in {knn_time:.1f}s")

# Query all users
print("  Finding similar users...")
start = time.time()

distances, indices = knn.kneighbors(user_factors_normalized)

query_time = time.time() - start
print(f"✓ Similar users found in {query_time:.1f}s")

# ---------------------- GENERATE RECOMMENDATIONS ----------------------
print(f"\n📦 Generating recommendations...")

start = time.time()
recs = []
users_with_recs = 0

# Batch processing for efficiency
batch_size = 1000
n_batches = (n_users + batch_size - 1) // batch_size

for batch_idx in range(n_batches):
    batch_start = batch_idx * batch_size
    batch_end = min(batch_start + batch_size, n_users)
    
    if batch_idx % 5 == 0:
        progress = 100 * batch_end / n_users
        print(f"  Progress: {progress:.0f}% ({batch_end:,}/{n_users:,})...", end='\r')
    
    for user_idx in range(batch_start, batch_end):
        # Get similar users (skip self)
        similar_indices = indices[user_idx][1:N_NEIGHBORS+1]
        
        # Get user's items
        user_items = set(subset[subset["u"] == user_idx]["i"].tolist())
        
        # Strategy 1: User-based CF (similar users)
        similar_purchases = subset[subset["u"].isin(similar_indices)][["i", "score"]]
        candidates = similar_purchases[~similar_purchases["i"].isin(user_items)]
        
        # Strategy 2: Item-based CF (add to candidates)
        for owned_item in list(user_items)[:3]:  # Use up to 3 owned items
            similar_items = item_item_similarity[owned_item].argsort()[-10:][::-1]
            for sim_idx in similar_items:
                if sim_idx not in user_items:
                    score = float(item_item_similarity[owned_item, sim_idx])
                    candidates = pd.concat([
                        candidates,
                        pd.DataFrame({"i": [sim_idx], "score": [score]})
                    ], ignore_index=True)
        
        # ============================================================
        # ✅ FIX #3: COLD-START FALLBACK
        # ============================================================
        if len(candidates) == 0:
            # User has no collaborative recommendations → Use popular items
            popular_items, popular_scores = get_popular_items(subset, N_RECOMMENDATIONS)
            top_items = pd.Series(popular_scores, index=popular_items)
        else:
            # Aggregate and rank
            top_items = (
                candidates.groupby("i")["score"]
                .sum()
                .nlargest(N_RECOMMENDATIONS)
            )
        
        # ============================================================
        # ✅ FIX #4: NORMALIZE SCORES TO 0-1 RANGE
        # ============================================================
        min_score = top_items.min()
        max_score = top_items.max()
        
        if max_score > min_score:
            normalized_scores = (top_items - min_score) / (max_score - min_score)
        else:
            normalized_scores = top_items / (max_score + 1e-10)
        
        # Add recommendations
        customer_id = idx_to_customer[user_idx]
        for rank, (item_idx, score) in enumerate(normalized_scores.items(), 1):
            article_id = idx_to_item[item_idx]
            recs.append({
                'customer_id': customer_id,
                'article_id': article_id,
                'score': float(score),
                'rank': rank
            })
        
        users_with_recs += 1

print()
rec_time = time.time() - start
print(f"✓ Recommendations generated in {rec_time:.1f}s")
print(f"  Users with recs: {users_with_recs:,}")
print(f"  Total recs: {len(recs):,}")

# ---------------------- SAVE RESULTS ----------------------
print("\n💾 Saving results...")

if recs:
    recs_df = pd.DataFrame(recs)
    
    # Save both formats
    recs_df.to_csv(OUTPUT_DIR / "recommendations.csv", index=False)
    recs_df.to_parquet(OUTPUT_DIR / "recommendations.parquet", index=False)
    
    print(f"✓ Saved {len(recs_df):,} recommendations")
    
    # Sample output
    print("\n📊 Sample recommendations:")
    print(recs_df.head(10).to_string(index=False))
    
    # Statistics
    print("\n📈 Statistics:")
    print(f"  Unique users: {recs_df['customer_id'].nunique():,}")
    print(f"  Unique items: {recs_df['article_id'].nunique():,}")
    print(f"  Avg per user: {len(recs_df)/users_with_recs:.1f}")
    print(f"  Score range: {recs_df['score'].min():.2f} - {recs_df['score'].max():.2f}")

print()
rec_time = time.time() - start
print(f"✓ Recommendations generated in {rec_time:.1f}s")
print(f"  Users with recs: {users_with_recs:,}")
print(f"  Total recs: {len(recs):,}")

# ---------------------- SAVE RESULTS ----------------------
print("\n💾 Saving results...")

if recs:
    recs_df = pd.DataFrame(recs)
    
    # Save both formats
    recs_df.to_csv(OUTPUT_DIR / "recommendations.csv", index=False)
    recs_df.to_parquet(OUTPUT_DIR / "recommendations.parquet", index=False)
    
    print(f"✓ Saved {len(recs_df):,} recommendations")
    
    # Sample output
    print("\n📊 Sample recommendations:")
    print(recs_df.head(10).to_string(index=False))
    
    # Statistics
    print("\n📈 Statistics:")
    print(f"  Unique users: {recs_df['customer_id'].nunique():,}")
    print(f"  Unique items: {recs_df['article_id'].nunique():,}")
    print(f"  Avg per user: {len(recs_df)/users_with_recs:.1f}")
    print(f"  Score range: {recs_df['score'].min():.2f} - {recs_df['score'].max():.2f}")

# Save mappings (using pickle for efficiency)
with open(OUTPUT_DIR / "customer_mapping.pkl", 'wb') as f:
    pickle.dump(customer_to_idx, f)

with open(OUTPUT_DIR / "item_mapping.pkl", 'wb') as f:
    pickle.dump(item_to_idx, f)

# Save embeddings
np.save(OUTPUT_DIR / "user_latent_factors.npy", user_factors)
np.save(OUTPUT_DIR / "item_latent_factors.npy", item_factors)
np.save(OUTPUT_DIR / "item_similarity.npy", item_item_similarity)

print(f"✓ Saved embeddings and mappings")

# ---------------------- PERFORMANCE SUMMARY ----------------------
total_time = time.time() - start_total

print("\n" + "="*70)
print("✅ COLLABORATIVE FILTERING COMPLETE!")
print("="*70)

print(f"\n⏱️ Performance Breakdown:")
print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
print(f"  SVD:        {svd_time:.1f}s ({100*svd_time/total_time:.0f}%)")
print(f"  KNN build:  {knn_time:.1f}s ({100*knn_time/total_time:.0f}%)")
print(f"  KNN query:  {query_time:.1f}s ({100*query_time/total_time:.0f}%)")
print(f"  Recs:       {rec_time:.1f}s ({100*rec_time/total_time:.0f}%)")

print(f"\n✨ ALL 4 FIXES APPLIED:")
print(f"  ✅ Fix #1: Data scaling (StandardScaler)")
print(f"  ✅ Fix #2: Item-item similarity (cosine_similarity)")
print(f"  ✅ Fix #3: Cold-start fallback (popular items)")
print(f"  ✅ Fix #4: Score normalization (0-1 range)")

print(f"\n📁 Output files ({OUTPUT_DIR}):")
print(f"  • recommendations.csv")
print(f"  • recommendations.parquet")
print(f"  • user_latent_factors.npy")
print(f"  • item_latent_factors.npy")
print(f"  • item_similarity.npy")
print(f"  • customer_mapping.pkl")
print(f"  • item_mapping.pkl")

print("\n" + "="*70 + "\n")