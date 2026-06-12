# ============================================================
# CONTENT-BASED FILTERING MODEL GENERATOR
# Generates article_similarity_matrix.npy and related artifacts
# Adapted for local backend usage
# ============================================================

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pickle
import os
from pathlib import Path

print("=" * 60)
print(" CONTENT-BASED FILTERING MODEL GENERATOR")
print("=" * 60)

# ---- CONFIGURATION ----
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent  # layr/

# Input: articles_structured.parquet
INPUT_PATH = PROJECT_ROOT / "data" / "ml" / "Article Content Feature Dataset" / "articles_structured.parquet"
# Output: backend/data/content_based_model/
OUTPUT_DIR = BASE_DIR / "data" / "content_based_model"

# ---- STEP 1: LOAD INPUT DATA ----
print("\n[1/9] Loading article metadata...")
if not INPUT_PATH.exists():
    print(f"[ERROR] Input file not found at {INPUT_PATH}")
    print("   Please ensure articles_structured.parquet exists.")
    exit(1)

articles_df = pd.read_parquet(INPUT_PATH)
print(f"   [OK] Loaded {len(articles_df)} articles")
print(f"   Columns: {articles_df.columns.tolist()}")

# ---- STEP 2: PREPARE TEXT FEATURES ----
print("\n[2/9] Preparing text features...")
text_parts = []

# Core columns
for col in ['prod_name', 'product_type_name', 'colour_group_name']:
    if col in articles_df.columns:
        text_parts.append(articles_df[col].fillna(''))
        print(f"   Using: {col}")

# Optional columns
for col in ['product_group_name', 'section_name', 'index_group_name', 
            'garment_group_name', 'department_name', 'detail_desc']:
    if col in articles_df.columns:
        text_parts.append(articles_df[col].fillna(''))
        print(f"   Using: {col}")

# Combine all text parts
combined_text = text_parts[0]
for i in range(1, len(text_parts)):
    combined_text = combined_text + ' ' + text_parts[i]
articles_df['combined_text'] = combined_text

# ---- STEP 3: TF-IDF VECTORIZATION ----
print("\n[3/9] Computing TF-IDF embeddings...")
tfidf = TfidfVectorizer(
    max_features=500,
    stop_words='english',
    min_df=2,
    max_df=0.8,
    ngram_range=(1, 2)
)
text_embeddings = tfidf.fit_transform(articles_df['combined_text'])
text_embeddings_dense = text_embeddings.toarray()
print(f"   [OK] TF-IDF shape: {text_embeddings_dense.shape}")

# ---- STEP 4: PRICE NORMALIZATION (Optional) ----
print("\n[4/9] Processing price features...")
price_embedding = None
scaler = None

if 'price' in articles_df.columns:
    scaler = StandardScaler()
    price_values = articles_df[['price']].fillna(articles_df['price'].median())
    price_norm = scaler.fit_transform(price_values)
    price_normalized = (price_norm - price_norm.min()) / (price_norm.max() - price_norm.min() + 1e-8)
    price_embedding = price_normalized * 50  # Weight factor
    print(f"   [OK] Price normalized and weighted")
else:
    print(f"   [WARN] No price column found, using text features only")

# ---- STEP 5: COMBINE FEATURES ----
print("\n[5/9] Combining text + price features...")
if price_embedding is not None:
    combined_embeddings = np.hstack([
        text_embeddings_dense * 0.95,
        price_embedding * 0.05
    ])
else:
    combined_embeddings = text_embeddings_dense
print(f"   [OK] Combined shape: {combined_embeddings.shape}")

# ---- STEP 6: COMPUTE SIMILARITY MATRIX ----
print("\n[6/9] Computing article-article similarity matrix...")
print(f"   This may take a few minutes for {len(articles_df):,} articles...")
similarity_matrix = cosine_similarity(combined_embeddings)
print(f"   [OK] Similarity matrix: {similarity_matrix.shape}")
print(f"   Range: [{similarity_matrix.min():.3f}, {similarity_matrix.max():.3f}]")

# ---- STEP 7: CREATE ID MAPPINGS ----
print("\n[7/9] Creating ID mappings...")
article_id_to_idx = {str(aid): idx for idx, aid in enumerate(articles_df['article_id'])}
idx_to_article_id = {idx: str(aid) for aid, idx in article_id_to_idx.items()}
print(f"   [OK] Created mappings for {len(article_id_to_idx):,} articles")

# ---- STEP 8: SAVE ARTIFACTS ----
print("\n[8/9] Saving artifacts to disk...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Similarity matrix (PRIMARY)
np.save(OUTPUT_DIR / 'article_similarity_matrix.npy', similarity_matrix)
print(f"   [OK] article_similarity_matrix.npy ({similarity_matrix.nbytes / (1024*1024):.1f} MB)")

# Text embeddings
np.save(OUTPUT_DIR / 'article_text_embeddings.npy', text_embeddings_dense)
print(f"   [OK] article_text_embeddings.npy")

# Vectorizer
with open(OUTPUT_DIR / 'tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(tfidf, f)
print(f"   [OK] tfidf_vectorizer.pkl")

# Scaler
if scaler is not None:
    with open(OUTPUT_DIR / 'price_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   [OK] price_scaler.pkl")

# Mappings
with open(OUTPUT_DIR / 'article_id_to_idx.pkl', 'wb') as f:
    pickle.dump(article_id_to_idx, f)
print(f"   [OK] article_id_to_idx.pkl")

# Config
config = {
    'num_articles': len(article_id_to_idx),
    'tfidf_features': text_embeddings_dense.shape[1],
    'has_price': price_embedding is not None,
}
with open(OUTPUT_DIR / 'config.pkl', 'wb') as f:
    pickle.dump(config, f)
print(f"   [OK] config.pkl")

# ---- STEP 9: VALIDATION ----
print("\n[9/9] Validation...")
example_idx = 0
example_article_id = idx_to_article_id[example_idx]
example_name = articles_df.iloc[example_idx]['prod_name'] if 'prod_name' in articles_df.columns else 'N/A'
similarities = similarity_matrix[example_idx].copy()
similarities[example_idx] = -1  # Exclude self

top_k_indices = np.argsort(similarities)[::-1][:5]

print(f"   Example Article (Index 0):")
print(f"     ID: {example_article_id}")
print(f"     Name: {example_name}")
print(f"     Top 5 Similar:")
for rank, idx in enumerate(top_k_indices, 1):
    sim_article_id = idx_to_article_id[idx]
    sim_name = articles_df.iloc[idx]['prod_name'] if 'prod_name' in articles_df.columns else 'N/A'
    sim_score = similarities[idx]
    print(f"       {rank}. {sim_article_id} - {sim_name[:40]:40s} (score: {sim_score:.4f})")

# ---- DONE ----
print("\n" + "=" * 60)
print(" [OK] CONTENT-BASED MODEL GENERATION COMPLETE!")
print("=" * 60)
print(f"\n   Output saved to: {OUTPUT_DIR}")
print(f"   Total articles: {len(article_id_to_idx):,}")
print(f"\n   Files created:")
print(f"     - article_similarity_matrix.npy (PRIMARY)")
print(f"     - article_text_embeddings.npy")
print(f"     - tfidf_vectorizer.pkl")
print(f"     - article_id_to_idx.pkl")
print(f"     - config.pkl")
if scaler is not None:
    print(f"     - price_scaler.pkl")
print("=" * 60)

