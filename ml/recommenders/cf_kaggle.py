import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
import implicit
import pickle
from datetime import datetime
from pathlib import Path
import os
import time
from collections import defaultdict

# --- CONFIGURATION ---
TRANSACTIONS_PATH = "/kaggle/input/etl-data/transactions.csv"
OUTPUT_DIR = "model_output_v2"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

K_RECOMMENDATIONS = 12
FACTORS = 100
REGULARIZATION = 0.01
ITERATIONS = 50
ALPHA = 40
DAYS_FOR_TEST = 7

print("="*60)
print("1. Data Loading and Normalization ⚙️")
print("="*60)

column_names = [
    "transaction_id", "t_dat", "customer_id", "article_id", "price", "sales_channel_id"
]

df_raw = pd.read_csv(
    TRANSACTIONS_PATH,
    header=None,
    names=column_names
)

def normalize_article_id(aid):
    aid_str = str(aid).strip()
    if len(aid_str) == 10 and aid_str.startswith('0'):
        return aid_str[1:]
    return aid_str

print("  Applying ID normalization...")
df_raw["customer_id"] = df_raw["customer_id"].astype(str).str.strip()
df_raw["article_id"] = df_raw["article_id"].apply(normalize_article_id)

df_raw["t_dat"] = pd.to_datetime(df_raw["t_dat"], errors='coerce')
df_raw = df_raw.dropna(subset=['t_dat', 'customer_id', 'article_id']).copy()

print("\n2. Temporal Split ⏱️")

max_date = df_raw['t_dat'].max()
split_date = max_date - pd.Timedelta(days=DAYS_FOR_TEST)

df_train = df_raw[df_raw['t_dat'] < split_date].copy()
df_test = df_raw[df_raw['t_dat'] >= split_date].copy()

print(f"  Training rows: {len(df_train):,}")
print(f"  Testing rows: {len(df_test):,}")

df_train['days_ago'] = (max_date - df_train['t_dat']).dt.days
HALF_LIFE = 30
df_train['weight'] = np.exp(-df_train['days_ago'] / HALF_LIFE)
df_train['score'] = (df_train['price'] * 100) * df_train['weight'] * ALPHA

print("\n3. Building Sparse Matrix 📊")

df_train['customer_id'] = df_train['customer_id'].str.strip()
df_train['article_id'] = df_train['article_id'].str.strip()

unique_customers = df_train["customer_id"].unique()
unique_articles = df_train["article_id"].unique()

customer_id_to_idx = {id: i for i, id in enumerate(unique_customers)}
article_id_to_idx = {id: i for i, id in enumerate(unique_articles)}

idx_to_customer_id = {i: id for id, i in customer_id_to_idx.items()}
idx_to_article_id = {i: id for id, i in article_id_to_idx.items()}

df_train['user_idx'] = df_train['customer_id'].map(customer_id_to_idx)
df_train['item_idx'] = df_train['article_id'].map(article_id_to_idx)

user_item_matrix = csr_matrix(
    (df_train['score'].astype(np.float32),
     (df_train['user_idx'], df_train['item_idx']))
)

item_user_matrix = user_item_matrix.T.tocsr()

print("\n4. Training ALS Model 🤖")
t0 = time.time()

model = implicit.als.AlternatingLeastSquares(
    factors=FACTORS,
    regularization=REGULARIZATION,
    iterations=ITERATIONS,
    random_state=42
)

model.fit(item_user_matrix)
t1 = time.time()

print(f"  Training completed in {t1 - t0:.2f} sec.")

expected_users = len(unique_customers)
if model.user_factors.shape[0] < expected_users:
    print("⚠️ Factor Swap Applied")
    model.user_factors, model.item_factors = model.item_factors, model.user_factors

np.save(Path(OUTPUT_DIR) / 'user_latent_factors.npy', model.user_factors)
np.save(Path(OUTPUT_DIR) / 'item_latent_factors.npy', model.item_factors)

with open(Path(OUTPUT_DIR) / 'customer_mapping.pkl', 'wb') as f:
    pickle.dump(idx_to_customer_id, f)

with open(Path(OUTPUT_DIR) / 'item_mapping.pkl', 'wb') as f:
    pickle.dump(idx_to_article_id, f)

print("\n5. Generating Recommendations 🎁")

valid_item_indices = set(idx_to_article_id.keys())
df_test['customer_id'] = df_test['customer_id'].str.strip()
test_users = set(df_test['customer_id'].unique())

recs_data = []
num_users = user_item_matrix.shape[0]

for user_idx in range(num_users):
    try:
        user_id = idx_to_customer_id[user_idx]
    except KeyError:
        continue

    if user_id in test_users:
        recs, scores = model.recommend(
            userid=user_idx,
            user_items=user_item_matrix.getrow(user_idx),
            N=K_RECOMMENDATIONS + 10,
            filter_already_liked_items=False
        )

        rank = 1
        for item_idx, score in zip(recs, scores):
            if item_idx in valid_item_indices:
                recs_data.append([user_id, idx_to_article_id[item_idx], score, rank])
                rank += 1
                if rank > K_RECOMMENDATIONS:
                    break

df_recs = pd.DataFrame(
    recs_data,
    columns=['customer_id', 'article_id', 'score', 'rank']
)

output_path = Path(OUTPUT_DIR) / "recommendations.csv"
df_recs.to_csv(output_path, index=False)

print("\n==============================")
print("MODEL TRAINED & SAVED")
print("==============================")

# ---------------------------- EVALUATION ---------------------------- #

print("\nEvaluating Model (MAP@12) 📈")

df_raw["customer_id"] = df_raw["customer_id"].astype(str).str.strip()
df_raw["article_id"] = df_raw["article_id"].apply(normalize_article_id)

df_raw["t_dat"] = pd.to_datetime(df_raw["t_dat"], errors='coerce')
df_raw = df_raw.dropna(subset=['t_dat']).copy()

df_test = df_raw[df_raw['t_dat'] >= split_date].copy()
df_test_gt = df_test.groupby('customer_id')['article_id'].apply(list).to_dict()

df_recs['article_id'] = df_recs['article_id'].astype(str)
df_recs_agg = df_recs.groupby('customer_id')['article_id'].apply(list)

users_eval = set(df_recs_agg.index).intersection(df_test_gt.keys())

def apk(rec, truth, k):
    rec = rec[:k]
    truth = set(truth)

    hits = 0
    score = 0.0

    for i, r in enumerate(rec):
        if r in truth:
            hits += 1
            score += hits / (i + 1)

    return score / min(len(truth), k)

def mapk(predictions, ground_truth, k):
    return np.mean([apk(predictions[u], ground_truth[u], k) for u in users_eval])

map_score = mapk(df_recs_agg.to_dict(), df_test_gt, K_RECOMMENDATIONS)

print(f"\n📌 FINAL MAP@{K_RECOMMENDATIONS}: {map_score:.6f}")
print("Done.")

