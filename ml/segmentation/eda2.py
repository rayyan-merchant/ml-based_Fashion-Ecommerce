# ml/segmentation/eda_extended.py
"""
Extended EDA for segmentation. Produces PNG plots and CSV summaries in data/ml/segmentation/eda_output/.
Run after preprocess_full.py
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA

PROJECT_ROOT = os.path.expanduser("~/Desktop/LAYR---ml_db_proj-main-2")
os.chdir(PROJECT_ROOT)

IN_PATH = "data/ml/segmentation/model_features.parquet"
OUT_DIR = "data/ml/segmentation/eda_output"
os.makedirs(OUT_DIR, exist_ok=True)

print("Loading features from", IN_PATH)
df = pd.read_parquet(IN_PATH)
print("Shape:", df.shape)

# Basic distributions for RFM-like fields
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# make output folder
def savefig(fig, name):
    p = os.path.join(OUT_DIR, name)
    fig.savefig(p, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print("Saved:", p)

# 1) Histograms for key metrics
key_cols = [c for c in ["days_since_last_purchase", "total_transactions", "lifetime_value", "avg_order_value"] if c in df.columns]
for c in key_cols:
    fig, ax = plt.subplots(figsize=(6,4))
    sns.histplot(df[c].replace([np.inf, -np.inf], np.nan).dropna(), bins=100, kde=True, ax=ax)
    ax.set_title(f"Distribution: {c}")
    savefig(fig, f"hist_{c}.png")

# 2) Log-transform preview for monetary and frequency
for c in ["total_transactions", "lifetime_value"]:
    if c in df.columns:
        fig, axes = plt.subplots(1,2,figsize=(12,4))
        sns.histplot(df[c].dropna(), bins=100, ax=axes[0], kde=True)
        axes[0].set_title(c)
        sns.histplot(np.log1p(df[c].fillna(0)), bins=100, ax=axes[1], kde=True)
        axes[1].set_title(f"log1p({c})")
        savefig(fig, f"log_preview_{c}.png")

# 3) RFM pairwise scatter (colored by quantiles)
if all([c in df.columns for c in ["days_since_last_purchase","total_transactions","lifetime_value"]]):
    fig, ax = plt.subplots(figsize=(6,6))
    sc = ax.scatter(df["total_transactions"], df["lifetime_value"], c=df["days_since_last_purchase"], cmap="viridis", s=6, alpha=0.6)
    ax.set_xscale("log") if (df["total_transactions"].max()>1000) else None
    ax.set_title("Transactions vs Lifetime Value (color=recency_days)")
    plt.colorbar(sc, ax=ax)
    savefig(fig, "rfm_scatter.png")

# 4) Category affinity heatmap (top categories)
cat_cols = [c for c in df.columns if c.startswith("cat_")]
if cat_cols:
    # show sum by category and top 20
    cat_sums = df[cat_cols].sum().sort_values(ascending=False)
    top = cat_sums.head(20).index.tolist()
    fig, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(df[top].sample(min(2000, len(df))).T, cbar=False)
    ax.set_title("Category affinities (sampled customers)")
    savefig(fig, "cat_affinity_heatmap.png")
    # save category sums
    cat_sums.to_csv(os.path.join(OUT_DIR, "category_sums.csv"))
    print("Saved category_sums.csv")

# 5) Funnel-like indicators: view_to_buy ratio distribution
if all([c in df.columns for c in ["total_events","purchase_count"]]):
    df["view_to_buy"] = df["total_events"].replace(0, np.nan) / df["purchase_count"].replace(0, np.nan)
    fig, ax = plt.subplots(figsize=(6,4))
    sns.histplot(df["view_to_buy"].replace([np.inf, -np.inf], np.nan).dropna(), bins=100, kde=True, ax=ax)
    ax.set_title("view_to_buy ratio (may be NaN)")
    savefig(fig, "view_to_buy.png")

# 6) Temporal patterns: active_days distribution and weekday preference if events exist
if "active_days" in df.columns:
    fig, ax = plt.subplots(figsize=(6,4))
    sns.histplot(df["active_days"], bins=50, ax=ax)
    ax.set_title("active_days distribution")
    savefig(fig, "active_days.png")

# 7) Outlier detection summary (top 100 by lifetime_value)
if "lifetime_value" in df.columns:
    top100 = df.nlargest(100, "lifetime_value")[["customer_id","lifetime_value","total_transactions","total_events"]].reset_index(drop=True)
    top100.to_csv(os.path.join(OUT_DIR, "top100_by_ltv.csv"), index=False)
    print("Saved top100_by_ltv.csv")

# 8) Correlation heatmap for numeric features
num_small = [c for c in numeric_cols if df[c].nunique()>1][:40]
if len(num_small)>1:
    corr = df[num_small].corr().abs()
    fig, ax = plt.subplots(figsize=(10,8))
    sns.heatmap(corr, cmap="coolwarm", vmin=0, vmax=1, ax=ax)
    ax.set_title("Correlation heatmap (numeric features)")
    savefig(fig, "correlation_heatmap.png")

# 9) PCA preview for dimensionality reduction (2 components)
feats = [c for c in df.columns if c not in ["customer_id"] and df[c].dtype in [int,float]]
if len(feats)>2:
    X = df[feats].fillna(0).sample(min(100000, len(df)), random_state=42)
    pca = PCA(n_components=2)
    coords = pca.fit_transform(X)
    fig, ax = plt.subplots(figsize=(8,6))
    ax.scatter(coords[:,0], coords[:,1], s=4, alpha=0.3)
    ax.set_title("PCA 2D preview (sample)")
    savefig(fig, "pca_preview.png")
    print("PCA explained variance ratio:", pca.explained_variance_ratio_.tolist())

# 10) Save summary stats
summary = df.describe(percentiles=[0.01,0.05,0.25,0.5,0.75,0.95,0.99]).T
summary.to_csv(os.path.join(OUT_DIR, "feature_summary.csv"))
print("Saved feature_summary.csv")

print("EDA outputs written to", OUT_DIR)
