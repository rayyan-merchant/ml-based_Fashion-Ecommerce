# ml/segmentation/preprocess.py
"""
Preprocessing for customer segmentation (RFM + Category preferences).
Saves cleaned features to data/ml/segmentation/features.parquet.

How to run:
(venv) $ python3 ml/segmentation/preprocess.py
"""

import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import numpy as np

# --- CONFIG ---
PROJECT_ROOT = os.path.expanduser("~/Desktop/LAYR---ml_db_proj-main-2")
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

OUT_DIR = os.path.join(PROJECT_ROOT, "data", "ml", "segmentation")
os.makedirs(OUT_DIR, exist_ok=True)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise RuntimeError(
        "Database credentials not fully provided. Fill .env with DB_USER, DB_PASSWORD, DB_NAME."
    )

CONN_STR = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print("Using connection:", CONN_STR.replace(DB_PASSWORD, "*****"))


# --- helpers ---
def load_transactions(engine):
    """
    Load transactions (purchases) for RFM & monetary.
    Adjust table/column names if your schema differs.
    """
    query = """
    SELECT
        t.customer_id::text,
        t.article_id::text,
        t.t_dat::date AS t_date,
        t.price::numeric
    FROM niche_data.transactions t
    WHERE t.t_dat IS NOT NULL
    """
    print("Querying transactions...")
    return pd.read_sql(query, engine)


def load_events_with_article_cat(engine):
    """
    Load events and join with article parent category (if exists).
    We'll use event_type semantics from your events table. If your events table encodes
    purchases differently, we only use events for behaviour (views/clicks).
    """
    query = """
    SELECT
        e.session_id,
        e.customer_id::text,
        e.article_id::text,
        e.event_type,
        e.created_at::timestamp,
        a.product_group_name::text AS parent_category_id
    FROM niche_data.events e
    LEFT JOIN niche_data.articles a ON e.article_id = a.article_id
    WHERE e.customer_id IS NOT NULL
    """
    print("Querying events + article categories...")
    return pd.read_sql(query, engine)


def compute_rfm(trans_df, reference_date=None):
    """
    Returns DataFrame with columns:
    customer_id, recency_days, frequency, monetary, last_purchase_date, first_purchase_date
    """
    if trans_df.empty:
        return pd.DataFrame(
            columns=[
                "customer_id",
                "recency_days",
                "frequency",
                "monetary",
                "last_purchase_date",
                "first_purchase_date",
            ]
        )

    if reference_date is None:
        reference_date = pd.Timestamp(datetime.utcnow().date())

    grp = trans_df.groupby("customer_id").agg(
        frequency=("t_date", "count"),
        monetary=("price", "sum"),
        last_purchase_date=("t_date", "max"),
        first_purchase_date=("t_date", "min"),
    ).reset_index()

    grp["last_purchase_date"] = pd.to_datetime(grp["last_purchase_date"])
    grp["recency_days"] = (reference_date - grp["last_purchase_date"]).dt.days
    # make sure numeric types
    grp["frequency"] = grp["frequency"].astype(int)
    grp["monetary"] = grp["monetary"].astype(float)

    return grp[
        [
            "customer_id",
            "recency_days",
            "frequency",
            "monetary",
            "last_purchase_date",
            "first_purchase_date",
        ]
    ]


def compute_category_preferences(events_df, top_n_categories=20):
    """
    Pivot event counts per parent_category_id for each customer.
    Returns pivoted dataframe: customer_id + category_count_{catid}...
    We limit to top_n_categories by global activity to keep features sane.
    """
    if events_df.empty:
        return pd.DataFrame(columns=["customer_id"])

    # use events of interest — views, clicks, purchase events. If event_type is numeric or text adjust this filter.
    # If your event_type for purchase is 'purchase' or 1, include both as necessary.
    # Here we count all event types per category as engagement signal.
    df = events_df.copy()
    # Fill missing parent_category_id as 'unknown'
    df["parent_category_id"] = df["parent_category_id"].fillna("unknown")
    # Count events per (customer, category)
    cat_counts = (
        df.groupby(["customer_id", "parent_category_id"])
        .size()
        .reset_index(name="count")
    )
    # find top categories globally
    top_cats = (
        cat_counts.groupby("parent_category_id")["count"]
        .sum()
        .nlargest(top_n_categories)
        .index.tolist()
    )
    cat_counts = cat_counts[cat_counts["parent_category_id"].isin(top_cats)]
    # pivot
    pivot = cat_counts.pivot_table(
        index="customer_id",
        columns="parent_category_id",
        values="count",
        fill_value=0,
    )
    # flatten column names
    pivot.columns = [f"cat_{str(c)}" for c in pivot.columns.astype(str)]
    pivot = pivot.reset_index()
    return pivot


def build_feature_table(rfm_df, cat_pref_df, events_df, trans_df):
    """
    Merge RFM + category prefs + interaction features into single table.
    """
    # ensure customer_id is string
    for df in (rfm_df, cat_pref_df):
        if "customer_id" in df.columns:
            df["customer_id"] = df["customer_id"].astype(str)

    # base: unique customers from either transactions or events
    cust_ids = pd.Series(
        pd.concat([rfm_df["customer_id"], events_df["customer_id"]]).unique()
    ).astype(str)
    base = pd.DataFrame({"customer_id": cust_ids})

    # merge rfm
    feat = base.merge(rfm_df, on="customer_id", how="left")

    # merge category prefs
    feat = feat.merge(cat_pref_df, on="customer_id", how="left")

    # fill missing numeric columns with zeros/defaults
    numeric_cols = feat.select_dtypes(include=[np.number]).columns.tolist()
    feat[numeric_cols] = feat[numeric_cols].fillna(0)

    # interaction features from events
    events_agg = (
        events_df.groupby("customer_id")
        .agg(total_events=("event_type", "count"), unique_sessions=("session_id", "nunique"))
        .reset_index()
    )
    feat = feat.merge(events_agg, on="customer_id", how="left")
    feat["total_events"] = feat["total_events"].fillna(0).astype(int)
    feat["unique_sessions"] = feat["unique_sessions"].fillna(0).astype(int)

    # purchases count and avg price from transactions
    trans_agg = (
        trans_df.groupby("customer_id")
        .agg(purchase_count=("t_date", "count"), avg_price=("price", "mean"))
        .reset_index()
    )
    feat = feat.merge(trans_agg, on="customer_id", how="left")
    feat["purchase_count"] = feat["purchase_count"].fillna(0).astype(int)
    feat["avg_price"] = feat["avg_price"].fillna(0.0).astype(float)

    # conversion proxy: purchases / events (guard divide by zero)
    feat["conversion"] = feat.apply(
        lambda r: (r["purchase_count"] / r["total_events"]) if r["total_events"] > 0 else 0.0,
        axis=1,
    )

    # fill RFM missing values with sensible defaults: recency large, frequency 0, monetary 0
    feat["recency_days"] = feat["recency_days"].fillna(9999).astype(int)
    feat["frequency"] = feat["frequency"].fillna(0).astype(int)
    feat["monetary"] = feat["monetary"].fillna(0.0).astype(float)

    # add flags
    feat["has_purchase"] = (feat["purchase_count"] > 0).astype(int)

    return feat


def main():
    engine = create_engine(CONN_STR)
    # Load data
    trans_df = load_transactions(engine)
    events_df = load_events_with_article_cat(engine)

    print(f"Loaded {len(trans_df):,} transactions and {len(events_df):,} events")

    # RFM
    rfm_df = compute_rfm(trans_df)
    print(f"Computed RFM for {len(rfm_df):,} customers")

    # Category prefs
    cat_pref_df = compute_category_preferences(events_df, top_n_categories=30)
    print(f"Computed category-pref features with {len(cat_pref_df.columns)-1} categories")

    # Build features
    feature_df = build_feature_table(rfm_df, cat_pref_df, events_df, trans_df)
    print(f"Final feature table shape: {feature_df.shape}")

    # Save to parquet and a CSV sample for quick inspection
    features_file = os.path.join(OUT_DIR, "features.parquet")
    sample_file = os.path.join(OUT_DIR, "features_sample.csv")

    feature_df.to_parquet(features_file, index=False)
    feature_df.head(200).to_csv(sample_file, index=False)
    print(f"Saved features to {features_file}")
    print(f"Saved sample to {sample_file}")

    # Quick summary stats (basic EDA-ready output)
    print("\nBasic summary:")
    print("Total customers:", feature_df["customer_id"].nunique())
    print("Customers with purchases:", feature_df["has_purchase"].sum())
    print("Recency (median):", int(feature_df["recency_days"].median()))
    print("Frequency (median):", int(feature_df["frequency"].median()))
    print("Monetary (median):", float(feature_df["monetary"].median()))


if __name__ == "__main__":
    main()
