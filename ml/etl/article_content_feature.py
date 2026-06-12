import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import scipy.sparse

# Create directories
os.makedirs("data/ml", exist_ok=True)

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("=" * 60)
print("Dataset B: Article Content Features (Simplified)")
print("=" * 60)

# Extract articles
print("\n1️⃣  Querying articles...")
query = """
SELECT 
    article_id,
    prod_name,
    product_type_name,
    colour_group_name,
    COALESCE(price, 0) as price
FROM niche_data.articles
LIMIT 100000
"""

df = pd.read_sql(query, engine)
print(f"   Loaded {len(df)} articles")

# Normalize price
print("\n2️⃣  Normalizing price...")
df['price_normalized'] = (df['price'] - df['price'].min()) / (df['price'].max() - df['price'].min() + 0.0001)

# Create text features
print("\n3️⃣  Creating text features...")
df['product_text'] = (
    df['prod_name'].fillna('') + ' ' +
    df['product_type_name'].fillna('') + ' ' +
    df['colour_group_name'].fillna('')
)

# TF-IDF on product text
print("   Creating TF-IDF vectors...")
tfidf = TfidfVectorizer(max_features=500, stop_words='english')
tfidf_vectors = tfidf.fit_transform(df['product_text'])

print(f"   TF-IDF shape: {tfidf_vectors.shape}")

# Simple embeddings using TF-IDF (no sentence-transformers needed)
print("\n4️⃣  Creating embeddings from TF-IDF...")
embeddings = tfidf_vectors.toarray()  # Convert sparse to dense
print(f"   Embeddings shape: {embeddings.shape}")

# Save files
print("\n5️⃣  Saving files...")

# Save structured data
df[['article_id', 'prod_name', 'product_type_name', 'colour_group_name', 'price', 'price_normalized']].to_parquet(
    'data/ml/articles_structured.parquet',
    index=False
)
print("   ✅ articles_structured.parquet")

# Save TF-IDF vectors
scipy.sparse.save_npz('data/ml/tfidf_detail_desc.npz', tfidf_vectors)
print("   ✅ tfidf_detail_desc.npz")

# Save embeddings as numpy array
np.save('data/ml/article_embeddings.npy', embeddings)
print("   ✅ article_embeddings.npy")

# Save TF-IDF vectorizer
with open('data/ml/tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(tfidf, f)
print("   ✅ tfidf_vectorizer.pkl")

print("\n" + "=" * 60)
print("✅ Dataset B Created Successfully!")
print("=" * 60)
print(f"\nFiles created:")
print(f"  - data/ml/articles_structured.parquet")
print(f"  - data/ml/tfidf_detail_desc.npz (sparse)")
print(f"  - data/ml/article_embeddings.npy (dense)")
print(f"  - data/ml/tfidf_vectorizer.pkl")