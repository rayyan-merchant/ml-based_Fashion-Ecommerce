# ============================================================
# CONTENT-BASED FILTERING MODEL TRAINING (FIXED)
# Works with actual article metadata structure
# ============================================================

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pickle
import os

print("=" * 60)
print(" CONTENT-BASED FILTERING MODEL")
print("=" * 60)

# STEP 1: LOAD INPUT DATA
# =======================
print("\n1️ Loading article metadata...")
articles_df = pd.read_parquet('/kaggle/input/etl-data-2/articles_structured.parquet')
print(f" Loaded {len(articles_df)} articles")
print(f"  Available columns: {articles_df.columns.tolist()}")

# STEP 2: INSPECT & PREPARE DATA
# ===============================
print("\n2️ Inspecting data structure...")
print(f"  Shape: {articles_df.shape}")
print(f"  Data types:\n{articles_df.dtypes}")
print(f"\n  First row:\n{articles_df.iloc[0]}")

# STEP 3: PREPARE TEXT FEATURES (ADAPTIVE)
# ========================================
print("\n3️ Preparing text features...")

# Build combined text from available columns
text_parts = []

# Always available columns
if 'prod_name' in articles_df.columns:
    text_parts.append(articles_df['prod_name'].fillna(''))

if 'product_type_name' in articles_df.columns:
    text_parts.append(articles_df['product_type_name'].fillna(''))

if 'colour_group_name' in articles_df.columns:
    text_parts.append(articles_df['colour_group_name'].fillna(''))

# Optional columns (only if present)
optional_cols = [
    'product_group_name',
    'section_name',
    'index_group_name',
    'garment_group_name',
    'department_name',
    'detail_desc'
]

for col in optional_cols:
    if col in articles_df.columns:
        text_parts.append(articles_df[col].fillna(''))
        print(f"     Using: {col}")

# Combine all text parts
combined_text = text_parts[0]
for i in range(1, len(text_parts)):
    combined_text = combined_text + ' ' + text_parts[i]

articles_df['combined_text'] = combined_text

print(f" Created combined text features from {len(text_parts)} columns")

# STEP 4: TEXT VECTORIZATION (TF-IDF)
# ===================================
print("\n4️ Computing TF-IDF embeddings...")
tfidf = TfidfVectorizer(
    max_features=500,
    stop_words='english',
    min_df=2,
    max_df=0.8,
    ngram_range=(1, 2)
)
text_embeddings = tfidf.fit_transform(articles_df['combined_text'])
print(f" TF-IDF shape: {text_embeddings.shape}")
print(f"  (Articles × Features): {len(articles_df)} × 500")

# STEP 5: NORMALIZE PRICE FEATURE (if available)
# =============================================
print("\n5️ Processing price features...")
price_embedding = None

if 'price' in articles_df.columns:
    scaler = StandardScaler()
    price_values = articles_df[['price']].fillna(articles_df['price'].median())
    price_norm = scaler.fit_transform(price_values)
    price_normalized = (price_norm - price_norm.min()) / (price_norm.max() - price_norm.min() + 1e-8)
    
    # Scale price to match text embeddings
    price_embedding = price_normalized * 50
    print(f" Price normalized and weighted")
elif 'price_normalized' in articles_df.columns:
    price_values = articles_df[['price_normalized']].fillna(0.5)
    price_embedding = price_values.values * 50
    print(f" Using pre-normalized prices")
else:
    print(f" No price column found, using text features only")

# STEP 6: COMBINE FEATURES
# ========================
print("\n6️ Combining text + price features...")
text_embeddings_dense = text_embeddings.toarray()

if price_embedding is not None:
    # Create hybrid embeddings: 95% text, 5% price
    combined_embeddings = np.hstack([
        text_embeddings_dense * 0.95,   # 95% text features
        price_embedding * 0.05           # 5% price
    ])
    print(f" Combined embeddings (text + price)")
else:
    combined_embeddings = text_embeddings_dense
    print(f" Using text features only (no price)")

print(f"  Shape: {combined_embeddings.shape}")

# STEP 7: COMPUTE SIMILARITY MATRIX
# =================================
print("\n7️ Computing article-article similarity matrix...")
print(f"  This may take a few minutes for {len(articles_df):,} articles...")

similarity_matrix = cosine_similarity(combined_embeddings)

print(f" Similarity matrix computed")
print(f"  Shape: {similarity_matrix.shape}")
print(f"  Range: [{similarity_matrix.min():.3f}, {similarity_matrix.max():.3f}]")
print(f"  Mean: {similarity_matrix.mean():.3f}")

# STEP 8: CREATE ID MAPPINGS
# ==========================
print("\n8️ Creating ID mappings...")
article_id_to_idx = {str(aid): idx for idx, aid in enumerate(articles_df['article_id'])}
idx_to_article_id = {idx: str(aid) for aid, idx in article_id_to_idx.items()}
print(f"✓ Created mappings for {len(article_id_to_idx):,} articles")

# STEP 9: SAVE ARTIFACTS
# ======================
print("\n9️ Saving artifacts to disk...")
output_dir = '/kaggle/working/content_based_output'
os.makedirs(output_dir, exist_ok=True)

# Save similarity matrix (PRIMARY ARTIFACT)
np.save(f'{output_dir}/article_similarity_matrix.npy', similarity_matrix)
matrix_size_mb = similarity_matrix.nbytes / (1024*1024)
print(f"   article_similarity_matrix.npy ({matrix_size_mb:.1f} MB)")

# Save text embeddings
np.save(f'{output_dir}/article_text_embeddings.npy', text_embeddings_dense)
embed_size_mb = text_embeddings_dense.nbytes / (1024*1024)
print(f"   article_text_embeddings.npy ({embed_size_mb:.1f} MB)")

# Save vectorizer
with open(f'{output_dir}/tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(tfidf, f)
print(f"   tfidf_vectorizer.pkl")

# Save scaler (if exists)
if 'price' in articles_df.columns:
    with open(f'{output_dir}/price_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   price_scaler.pkl")

# Save mappings
with open(f'{output_dir}/article_id_to_idx.pkl', 'wb') as f:
    pickle.dump(article_id_to_idx, f)
with open(f'{output_dir}/idx_to_article_id.pkl', 'wb') as f:
    pickle.dump(idx_to_article_id, f)
print(f"   article_id_to_idx.pkl, idx_to_article_id.pkl")

# Save metadata for reference
metadata_cols = ['article_id', 'prod_name']
if 'price' in articles_df.columns:
    metadata_cols.append('price')
if 'product_type_name' in articles_df.columns:
    metadata_cols.append('product_type_name')
if 'colour_group_name' in articles_df.columns:
    metadata_cols.append('colour_group_name')

articles_df[metadata_cols].to_parquet(
    f'{output_dir}/articles_metadata.parquet',
    index=False
)
print(f"   articles_metadata.parquet")

# Save configuration
config = {
    'num_articles': len(article_id_to_idx),
    'tfidf_features': text_embeddings_dense.shape[1],
    'has_price': price_embedding is not None,
    'columns_used': text_parts
}
with open(f'{output_dir}/config.pkl', 'wb') as f:
    pickle.dump(config, f)
print(f"   config.pkl")

# STEP 10: VALIDATION & EXAMPLES
# =============================
print("\n Validation & Examples...")
print(f"  Total articles: {len(article_id_to_idx):,}")
print(f"  Similarity matrix: {similarity_matrix.shape}")
print(f"  Range: [{similarity_matrix.min():.3f}, {similarity_matrix.max():.3f}]")

# Show example recommendations
example_idx = 0
example_article_id = idx_to_article_id[example_idx]
example_name = articles_df.iloc[example_idx]['prod_name']
similarities = similarity_matrix[example_idx].copy()
similarities[example_idx] = -1  # Exclude self

top_k_indices = np.argsort(similarities)[::-1][:5]

print(f"\n  Example Article (Index 0):")
print(f"    ID: {example_article_id}")
print(f"    Name: {example_name}")
print(f"    Top 5 Similar:")
for rank, idx in enumerate(top_k_indices, 1):
    sim_article_id = idx_to_article_id[idx]
    sim_name = articles_df.iloc[idx]['prod_name']
    sim_score = similarities[idx]
    print(f"      {rank}. {sim_article_id} - {sim_name[:40]:40s} (score: {sim_score:.4f})")

# STEP 11: SUMMARY
# ================
print("\n" + "=" * 60)
print(" CONTENT-BASED MODEL TRAINING COMPLETE!")
print("=" * 60)
print(f"\n Output files saved to: {output_dir}")
total_size = matrix_size_mb + embed_size_mb
print(f"   Total output size: {total_size:.1f} MB")
print(f"\n Download from Kaggle Output tab:")
print(f"   - article_similarity_matrix.npy (PRIMARY) - {matrix_size_mb:.1f} MB")
print(f"   - article_text_embeddings.npy - {embed_size_mb:.1f} MB")
print(f"   - tfidf_vectorizer.pkl")
print(f"   - article_id_to_idx.pkl")
print(f"   - idx_to_article_id.pkl")
print(f"   - articles_metadata.parquet")
print(f"   - config.pkl")
if 'price' in articles_df.columns:
    print(f"   - price_scaler.pkl")
print(f"\n Place all files in: data/content_based_model/")
print("=" * 60)