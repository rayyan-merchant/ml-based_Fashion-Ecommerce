import os
import re
import json
import pickle
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv 
from sentence_transformers import SentenceTransformer
# NLP libs
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer

# ML / vector libs
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse

# ======================================================
# Ensure Output Directory Exists
# ======================================================
out_dir = "data/ml"
os.makedirs(out_dir, exist_ok=True)

# ======================================================
# NLTK Downloads
# ======================================================
print("Downloading NLTK data...")
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)
nltk.download('vader_lexicon', quiet=True)
print("✅ NLTK downloads complete")

# ======================================================
# DB Connection
# ======================================================
load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("=" * 60)
print("Dataset E: Reviews & Sentiment (Simplified)")
print("=" * 60)

print("\n1️⃣  Querying reviews from database...")



sql_reviews = """
SELECT 
    r.review_id,
    r.customer_id,
    r.article_id,
    a.category_id,

    -- new enriched columns
    r.rating,
    r.review_text,
    r.created_at,
    r.verified_purchase,
    r.helpful_votes,
    r.sentiment_label AS synthetic_sentiment_label,
    r.aspect_terms,
    r.language,
    r.review_length,
    r.review_source,

    EXTRACT(DAY FROM (CURRENT_DATE - r.created_at)) AS review_age_days
FROM niche_data.reviews r
LEFT JOIN niche_data.articles a 
    ON r.article_id = a.article_id;
"""

df = pd.read_sql(sql_reviews, engine)
print("Loaded rows:", len(df))

# ======================================================
# Clean + Lemmatize
# ======================================================
lemmatizer = WordNetLemmatizer()

def clean_text(text, do_lemmatize=True):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www.\S+", "", text)  
    text = re.sub(r"[^a-z\s]", " ", text)         
    text = re.sub(r"\s+", " ", text).strip()

    if do_lemmatize:
        try:
            text = " ".join(lemmatizer.lemmatize(w) for w in text.split())
        except Exception:
            pass
    return text

df["clean_text"] = df["review_text"].apply(lambda x: clean_text(x))

# ======================================================
# VADER Sentiment (additional real sentiment)
# ======================================================
sia = SentimentIntensityAnalyzer()
df["vader_score"] = df["clean_text"].apply(lambda x: sia.polarity_scores(x)['compound'])
df["vader_score"] = (df["vader_score"] + 1) / 2.0     # normalize

def vader_label(score):
    if score < 0.4:
        return "negative"
    if score < 0.6:
        return "neutral"
    return "positive"

df["vader_label"] = df["vader_score"].apply(vader_label)

# ======================================================
# OPTIONAL: Toxicity (commented out intentionally)
# ======================================================
'''
try:
    tox = Detoxify('original')
    texts = df['review_text'].fillna("").tolist()
    tox_scores = tox.predict(texts)
    df['toxicity'] = tox_scores.get('toxicity')
    df['severe_toxicity'] = tox_scores.get('severe_toxicity')
except Exception as e:
    print("Detoxify failed:", e)
    df['toxicity'] = np.nan
    df['severe_toxicity'] = np.nan
'''

# ======================================================
# Process aspect_terms (JSONB → Python list)
# ======================================================
def safe_parse_json(x):
    if isinstance(x, dict) or isinstance(x, list):
        return x
    try:
        return json.loads(x)
    except:
        return []

df["aspect_terms_list"] = df["aspect_terms"].apply(safe_parse_json)

# ======================================================
# TF-IDF Vectorizer
# ======================================================
tfidf_path = os.path.join(out_dir, "reviews_tfidf_vectorizer.pkl")
tfidf_npz_path = os.path.join(out_dir, "reviews_tfidf.npz")

tfidf = TfidfVectorizer(stop_words="english", max_features=7000)
tfidf_matrix = tfidf.fit_transform(df["clean_text"].fillna(""))

scipy.sparse.save_npz(tfidf_npz_path, tfidf_matrix)
with open(tfidf_path, "wb") as f:
    pickle.dump(tfidf, f)

print("TF-IDF shape:", tfidf_matrix.shape)
print("Saved TF-IDF vectorizer and matrix to:", out_dir)

# ======================================================
# Sentence-BERT Embeddings
# ======================================================
emb_path = os.path.join(out_dir, "reviews_bert_embeddings.npy")

try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(
        df['clean_text'].fillna("").tolist(),
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    np.save(emb_path, embeddings)
    print("Saved embeddings to:", emb_path)
except Exception as e:
    print("Warning: Failed to compute embeddings:", e)

# ======================================================
# Save Final Parquet
# ======================================================
parquet_path = os.path.join(out_dir, "reviews.parquet")
df.to_parquet(parquet_path, index=False)

print("Saved final ML dataset to:", parquet_path)
print(df.head(5).T)




print(f"\n{df_final.head(3)}")
