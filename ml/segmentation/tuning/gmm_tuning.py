import os
import time
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
import joblib

# ============================================================
# PATH SETUP — LOCAL
# ============================================================

BASE_DIR = os.getcwd()  # Your project root if you set working directory

FEATURES_PATH = os.path.join(
    BASE_DIR, "data/ml/segmentation/features.parquet"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR, "data/ml/segmentation/tuning"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("==============================================")
print(" 🚀 GMM TUNING (Gaussian Mixture Model)")
print("==============================================")
print(f"\n Loading features from: {FEATURES_PATH}")

df = pd.read_parquet(FEATURES_PATH)
print(f"Loaded dataset with shape: {df.shape}")

# ============================================================
# NUMERIC FEATURES
# ============================================================
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
    "has_purchase",
]

df_model = df[NUMERIC_FEATURES].copy()

print("\n Using features:")
for f in NUMERIC_FEATURES:
    print("  -", f)

# ============================================================
# SCALE DATA
# ============================================================
print("\nScaling features...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_model)

joblib.dump(scaler, os.path.join(OUTPUT_DIR, "gmm_scaler.pkl"))
print(" Saved scaler → gmm_scaler.pkl")

# ============================================================
# GMM PARAMETERS — optimized for speed
# ============================================================

K_RANGE = range(3, 8)        # k = 3..7
COV_TYPES = ["diag", "tied"] # fastest and stable

results = []
best_model = None
best_silhouette = -1
best_entry = None

print("\n==============================================")
print(" Running GMM Tuning...")
print("==============================================")

for k in K_RANGE:
    for cov in COV_TYPES:
        print(f"\n Training GMM (k={k}, cov={cov}) ...")
        start = time.time()

        gmm = GaussianMixture(
            n_components=k,
            covariance_type=cov,
            max_iter=300,
            random_state=42,
            reg_covar=1e-6,
        )

        gmm.fit(X_scaled)
        labels = gmm.predict(X_scaled)

        elapsed = time.time() - start

        sil = silhouette_score(X_scaled, labels)
        db = davies_bouldin_score(X_scaled, labels)
        ch = calinski_harabasz_score(X_scaled, labels)

        print(f"   Time: {elapsed:.2f} sec")
        print(f"   Silhouette: {sil:.4f} | DB: {db:.4f} | CH: {ch:,.2f}")

        results.append([k, cov, sil, db, ch])

        if sil > best_silhouette:
            best_silhouette = sil
            best_model = gmm
            best_entry = (k, cov, sil, db, ch)

# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(
    results,
    columns=["k", "covariance_type", "silhouette", "davies_bouldin", "calinski_harabasz"]
)

csv_path = os.path.join(OUTPUT_DIR, "gmm_tuning_results.csv")
results_df.to_csv(csv_path, index=False)

print("\n Saved tuning results → gmm_tuning_results.csv")

# ============================================================
# SAVE BEST MODEL
# ============================================================

best_k, best_cov, best_sil, best_db, best_ch = best_entry

model_path = os.path.join(OUTPUT_DIR, "best_gmm_model.pkl")
joblib.dump(best_model, model_path)

print("\n==============================================")
print(" 🏆 BEST GMM MODEL SELECTED")
print("==============================================")
print(f" Best k = {best_k}")
print(f" Covariance Type = {best_cov}")
print(f" Silhouette Score = {best_sil:.4f}")
print(f" Davies–Bouldin = {best_db:.4f}")
print(f" Calinski–Harabasz = {best_ch:,.2f}")
print(f"\n Saved best model → {model_path}")

print("\n GMM Tuning Complete!")
