import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score
)
import joblib

# =======================================================
# PATHS (MATCHING YOUR CURRENT PROJECT STRUCTURE)
# =======================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

FEATURES_PATH = os.path.join(BASE_DIR, "/Users/syedarijaali/Desktop/LAYR---ml_db_proj-main-2/data/ml/segmentation/features.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "/Users/syedarijaali/Desktop/LAYR---ml_db_proj-main-2/data/ml/segmentation")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("====================================================")
print(" FINAL CUSTOMER SEGMENTATION — GMM MODEL TRAINING")
print("====================================================")
print(f" Loading dataset from:\n{FEATURES_PATH}")

# =======================================================
# LOAD DATA
# =======================================================
df = pd.read_parquet(FEATURES_PATH)
print(f" Loaded dataset shape: {df.shape}")

# =======================================================
# NUMERIC FEATURES — MUST MATCH FEATURES.PARQUET
# =======================================================
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

# =======================================================
# SCALER
# =======================================================
print("\n Scaling feature matrix...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_model)

SCALER_PATH = os.path.join(OUTPUT_DIR, "final_scaler.pkl")
joblib.dump(scaler, SCALER_PATH)

print(f" Saved scaler → {SCALER_PATH}")

# =======================================================
# TRAIN FINAL GMM MODEL
# =======================================================
BEST_K = 3
COV_TYPE = "tied"

print("\n====================================================")
print(f" Training FINAL GMM Model (k={BEST_K}, covariance='{COV_TYPE}')")
print("====================================================")

gmm = GaussianMixture(
    n_components=BEST_K,
    covariance_type=COV_TYPE,
    random_state=42
)

gmm.fit(X_scaled)
labels = gmm.predict(X_scaled)

# =======================================================
# METRICS
# =======================================================
sil = silhouette_score(X_scaled, labels)
db = davies_bouldin_score(X_scaled, labels)
ch = calinski_harabasz_score(X_scaled, labels)

print("\n FINAL MODEL METRICS")
print(f"Silhouette Score:      {sil:.4f}")
print(f"Davies–Bouldin Index:  {db:.4f}")
print(f"Calinski–Harabasz:     {ch:,.2f}")

# =======================================================
# SAVE MODEL
# =======================================================
MODEL_PATH = os.path.join(OUTPUT_DIR, "final_gmm_model.pkl")
joblib.dump(gmm, MODEL_PATH)

print(f"\n Saved FINAL GMM model → {MODEL_PATH}")

# =======================================================
# CREATE CUSTOMER SEGMENT ASSIGNMENTS
# =======================================================
df_segments = df.copy()
df_segments["segment"] = labels

SEGMENTS_PATH = os.path.join(OUTPUT_DIR, "customer_segments.parquet")
df_segments.to_parquet(SEGMENTS_PATH, index=False)

print(f" Saved customer_segments.parquet → {SEGMENTS_PATH}")

# =======================================================
# CREATE SEGMENT PROFILES
# =======================================================
segment_profiles = df_segments.groupby("segment")[NUMERIC_FEATURES].mean()

PROFILES_PATH = os.path.join(OUTPUT_DIR, "segment_profiles.csv")
segment_profiles.to_csv(PROFILES_PATH)

print("\n====================================================")
print(" FINAL CUSTOMER SEGMENTS & PROFILES CREATED")
print("====================================================")
print(f" Total customers segmented: {len(df_segments)}")
print(f" Saved segment profiles → {PROFILES_PATH}")
print("\n Training Complete!")
