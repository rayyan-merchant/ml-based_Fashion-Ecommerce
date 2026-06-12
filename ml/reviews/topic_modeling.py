# %% [markdown]
# # Phase 4 — Topic Modeling (BERTopic + LDA + NMF)
# Produces document-topic distributions and product-level topic features
# Input: data/ml/reviews/reviews_preprocessed/reviews_features_full.parquet + reviews_bert_embeddings_full.npy
# Output: data/ml/topics/ folder with all artifacts

# %%
# Install once (uncomment if needed)
# !pip install -q sentence-transformers bertopic umap-learn hdbscan gensim scikit-learn pyldavis nltk

# %%
import os
import re
import json
import nltk
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords
stoplist = set(stopwords.words('english'))

# ==============================
# CORRECT PATHS FOR YOUR PC
# ==============================
PROJECT_ROOT = Path("C:/Users/ND.COM/Desktop/ML DB Project")
DATA_DIR = PROJECT_ROOT / "data" / "ml" / "reviews" / "reviews_preprocessed"
OUT_DIR = PROJECT_ROOT / "data" / "ml" / "topics"

OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Loading from: {DATA_DIR}")
print(f"Saving to: {OUT_DIR}")

# %% [markdown]
# ## 0) Load data & embeddings
# %%
df = pd.read_parquet(DATA_DIR / "reviews_features_full.parquet")
print(f"Loaded {len(df):,} reviews")

emb_path = DATA_DIR / "reviews_bert_embeddings_full.npy"
if not emb_path.exists():
    raise FileNotFoundError(f"Embeddings not found at {emb_path}\nRun Phase 3 first!")
print("Loading precomputed embeddings...")
emb = np.load(emb_path, mmap_mode='r')
print(f"Embeddings shape: {emb.shape}")

texts = df['text_for_training'].fillna('').astype(str).tolist()
article_ids = df['article_id'].astype(str).tolist()

# %% [markdown]
# ## 1) BERTopic (Recommended)
# %%
USE_BERTOPIC = True  # Set to False if you want to skip

if USE_BERTOPIC:
    try:
        from bertopic import BERTopic
        from umap import UMAP
        from hdbscan import HDBSCAN

        print("Initializing BERTopic with custom UMAP + HDBSCAN...")
        umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)
        hdbscan_model = HDBSCAN(min_cluster_size=80, metric='euclidean', cluster_selection_method='eom', prediction_data=True)

        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            nr_topics="auto",
            calculate_probabilities=True,
            verbose=True
        )

        print("Fitting BERTopic on precomputed embeddings...")
        topics, probs = topic_model.fit_transform(texts, embeddings=emb)

        # Save model and outputs
        topic_model.save(str(OUT_DIR / "bertopic_model"), save_embedding_model=False)
        np.save(OUT_DIR / "bertopic_probs.npy", probs)
        pd.DataFrame({"topic": topics}).to_parquet(OUT_DIR / "bertopic_topics.parquet", index=False)
        
        topic_info = topic_model.get_topic_info()
        topic_info.to_parquet(OUT_DIR / "bertopic_topic_info.parquet", index=False)
        
        print(f"BERTopic SUCCESS! Found {len(topic_info)-1} topics (+1 outlier topic)")

    except Exception as e:
        print(f"BERTopic failed: {str(e)}")
        print("Falling back to LDA + NMF...")
        USE_BERTOPIC = False

# %% [markdown]
# ## 2) Fallback: LDA + NMF
# %%
if not USE_BERTOPIC:
    print("Running LDA + NMF fallback...")
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.decomposition import NMF
    import gensim
    from gensim import corpora

    def tokenize(text):
        return [w for w in re.findall(r"\b[a-z]{2,}\b", text.lower()) if w not in stoplist]

    print("Tokenizing texts...")
    tokenized = [tokenize(t) for t in tqdm(texts, desc="Tokenizing")]

    # LDA
    dictionary = corpora.Dictionary(tokenized)
    dictionary.filter_extremes(no_below=10, no_above=0.5, keep_n=50000)
    corpus = [dictionary.doc2bow(t) for t in tokenized]

    NUM_TOPICS = 30
    print("Training LDA...")
    lda = gensim.models.LdaModel(corpus, num_topics=NUM_TOPICS, id2word=dictionary, passes=3, random_state=42)
    lda.save(str(OUT_DIR / "lda_model"))

    lda_dists = np.zeros((len(texts), NUM_TOPICS))
    for i, bow in enumerate(tqdm(corpus, desc="LDA inference")):
        for tid, prob in lda.get_document_topics(bow, minimum_probability=0.0):
            lda_dists[i, tid] = prob
    np.save(OUT_DIR / "lda_topic_dist.npy", lda_dists)

    # NMF
    print("Training NMF...")
    tfidf = TfidfVectorizer(max_features=20000, stop_words='english')
    X = tfidf.fit_transform(texts)
    nmf = NMF(n_components=NUM_TOPICS, random_state=42)
    W = nmf.fit_transform(X)
    np.save(OUT_DIR / "nmf_topic_dist.npy", W)

# %% [markdown]
# ## 3) Unified document-topic distribution
# %%
if USE_BERTOPIC:
    probs = np.load(OUT_DIR / "bertopic_probs.npy")
    # Handle different shapes
    if probs.ndim == 1 or (hasattr(probs, 'toarray') and probs.toarray().ndim == 1):
        # Rare edge case
        topics = pd.read_parquet(OUT_DIR / "bertopic_topics.parquet")['topic'].tolist()
        n_topics = len(topic_model.get_topic_info()) - 1
        doc_topic_dist = np.zeros((len(texts), n_topics))
        for i, t in enumerate(topics):
            if t >= 0:
                doc_topic_dist[i, t] = 1.0
    else:
        doc_topic_dist = probs if isinstance(probs, np.ndarray) else np.array(probs.toarray())
else:
    if Path(OUT_DIR / "lda_topic_dist.npy").exists():
        doc_topic_dist = np.load(OUT_DIR / "lda_topic_dist.npy")
    else:
        doc_topic_dist = np.load(OUT_DIR / "nmf_topic_dist.npy")

np.save(OUT_DIR / "doc_topic_dist.npy", doc_topic_dist)
print(f"Saved unified doc_topic_dist.npy — shape: {doc_topic_dist.shape}")

# %% [markdown]
# ## 4) Product-level aggregation
# %%
n_topics = doc_topic_dist.shape[1]
topic_cols = [f"topic_{i}" for i in range(n_topics)]

df_topics = pd.DataFrame(doc_topic_dist, columns=topic_cols)
df_topics['article_id'] = article_ids

prod_topic = df_topics.groupby('article_id')[topic_cols].mean().reset_index()
prod_topic.to_parquet(OUT_DIR / "product_topic_dist.parquet", index=False)
print(f"Saved product topic features: {OUT_DIR / 'product_topic_dist.parquet'}")

# %% [markdown]
# ## 5) Save top words per topic
# %%
if USE_BERTOPIC:
    info = topic_model.get_topic_info()
    top_words = {}
    for _, row in info.iterrows():
        tid = int(row['Topic'])
        if tid != -1:
            top_words[tid] = [w for w, _ in topic_model.get_topic(tid)[:15]]
    with open(OUT_DIR / "topic_words.json", "w") as f:
        json.dump(top_words, f, indent=2)
    print("Saved BERTopic topic words")
else:
    if Path(OUT_DIR / "lda_model").exists():
        lda = gensim.models.LdaModel.load(str(OUT_DIR / "lda_model"))
        top_words = {i: [w for w, _ in lda.show_topic(i, 15)] for i in range(lda.num_topics)}
        with open(OUT_DIR / "topic_words.json", "w") as f:
            json.dump(top_words, f, indent=2)

print("\nTOPIC MODELING COMPLETE!")
print(f"All files saved in: {OUT_DIR}")
print("\nSample product topics:")
print(prod_topic.sample(3)[['article_id'] + topic_cols[:5]].round(4))