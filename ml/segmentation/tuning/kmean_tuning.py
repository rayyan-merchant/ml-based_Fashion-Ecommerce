import os
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
import joblib

# -----------------------------------------
# PATH SETUP
# -----------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
FEATURES_PATH = os.path.join(BASE_DIR, "data/ml/segmentation/features.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "data/ml/segmentation/tuning")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("==============================================")
print(" FAST KMEANS TUNING (MiniBatchKMeans)")
print("==============================================")
print(f"\n Loading features from: {FEATURES_PATH}")

df = pd.read_parquet(FEATURES_PATH)
print(f"Loaded dataset with shape {df.shape}")

# -----------------------------------------
# NUMERIC FEATURES
# -----------------------------------------
NUMERIC_FEATURES = [
    "recency_days",
    "frequency",
    "monetary",
    "cat_Accessories",
    "cat_Garment Lower body",
    "cat_Garment Upper body",
    "total_events",
    "unique_sessions",
    "purchase_count",
    "avg_price",
    "conversion",
    "has_purchase"
]

df_model = df[NUMERIC_FEATURES].copy()
print("\n Using features:")
for f in NUMERIC_FEATURES:
    print("   -", f)

# -----------------------------------------
# SCALE DATA
# -----------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_model)
joblib.dump(scaler, os.path.join(OUTPUT_DIR, "kmeans_fast_scaler.pkl"))

print("\n Saved scaler → kmeans_fast_scaler.pkl")

# -----------------------------------------
# MINI-BATCH KMEANS PARAMETERS
# -----------------------------------------
K_RANGE = range(3, 13)   # Try k = 3 to 12
BATCH_SIZE = 2000        # Very efficient for 500k+ data
INIT_SIZE = 10000        # Initial sample size for seeding

results = []
best_model = None
best_silhouette = -1
best_entry = None

print("\n==============================================")
print(" Running MiniBatchKMeans Tuning...")
print("==============================================")

for k in K_RANGE:
    print(f"\n Training MiniBatchKMeans (k={k}) ...")

    kmeans = MiniBatchKMeans(
        n_clusters=k,
        batch_size=BATCH_SIZE,
        init_size=INIT_SIZE,
        n_init="auto",
        random_state=42,
        max_iter=100
    )

    kmeans.fit(X_scaled)
    labels = kmeans.predict(X_scaled)

    sil = silhouette_score(X_scaled, labels)
    db = davies_bouldin_score(X_scaled, labels)
    ch = calinski_harabasz_score(X_scaled, labels)

    print(f"   Silhouette: {sil:.4f} | DB: {db:.4f} | CH: {ch:,.2f}")

    results.append([k, sil, db, ch])

    # Silhouette-first selection (Option A)
    if sil > best_silhouette:
        best_silhouette = sil
        best_model = kmeans
        best_entry = (k, sil, db, ch)

# -----------------------------------------
# SAVE RESULTS
# -----------------------------------------
results_df = pd.DataFrame(results, columns=["k", "silhouette", "davies_bouldin", "calinski_harabasz"])

csv_path = os.path.join(OUTPUT_DIR, "kmeans_fast_tuning_results.csv")
results_df.to_csv(csv_path, index=False)

print("\n Saved tuning results → kmeans_fast_tuning_results.csv")

# -----------------------------------------
# SAVE BEST MODEL
# -----------------------------------------
best_k, best_sil, best_db, best_ch = best_entry

model_path = os.path.join(OUTPUT_DIR, "best_kmeans_fast_model.pkl")
joblib.dump(best_model, model_path)

print("\n==============================================")
print(" BEST MINI-BATCH KMEANS MODEL")
print("==============================================")
print(f" Best k = {best_k}")
print(f" Silhouette Score = {best_sil:.4f}")
print(f" Davies–Bouldin = {best_db:.4f}")
print(f" Calinski–Harabasz = {best_ch:,.2f}")
print(f"\n Saved best model → {model_path}")

print("\n Fast KMeans Tuning Complete!")
