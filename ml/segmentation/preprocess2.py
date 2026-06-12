# ml/segmentation/preprocess_full.py
"""
Full preprocessing to implement Phase 1 of the Master Plan.

Outputs:
 - data/ml/segmentation/features_full.parquet   (rich feature table)
 - data/ml/segmentation/model_features.parquet  (selected features for modeling)
 - data/ml/segmentation/features_sample.csv

Usage:
(venv) $ python3 ml/segmentation/preprocess_full.py
"""
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- CONFIG: adjust PROJECT_ROOT if needed ---
PROJECT_ROOT = os.path.expanduser("~/Desktop/LAYR---ml_db_proj-main-2")
os.chdir(PROJECT_ROOT)
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

OUT_DIR = os.path.join("data", "ml", "segmentation")
os.makedirs(OUT_DIR, exist_ok=True)

# --- DB connection ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise RuntimeError("Missing DB credentials (DB_USER, DB_PASSWORD, DB_NAME) in .env")

CONN_STR = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(CONN_STR)

# --- Helper: safe read_sql with fallback to empty df ---
def try_sql(sql, engine, sample=0):
    try:
        return pd.read_sql(sql, engine)
    except Exception as e:
        print(f"[WARN] SQL failed: {e}")
        return pd.DataFrame()

# --- Load base data sources (detect tables) ---
print("Loading sources from DB (will adapt to missing tables)...")

# transactions (purchases)
tx_sql = "SELECT customer_id::text, article_id::text, t_dat::date AS t_date, price::numeric, sales_channel_id FROM niche_data.transactions"
tx_df = try_sql(tx_sql, engine)
if tx_df.empty:
    print("No transactions loaded (niche_data.transactions missing or empty).")

# events (views/clicks/etc)
ev_sql = """
SELECT session_id, customer_id::text, article_id::text, event_type, created_at::timestamp
FROM niche_data.events
"""
events_df = try_sql(ev_sql, engine)
if events_df.empty:
    print("No events loaded (niche_data.events missing or empty).")

# articles (category info)
art_sql = "SELECT article_id::text, COALESCE(product_group_name, index_name, 'unknown') as category FROM niche_data.articles"
articles_df = try_sql(art_sql, engine)
if articles_df.empty:
    print("No articles data loaded; category features will be limited.")

# orders / order_items (if exist) for basket-level info
orders_df = try_sql("SELECT order_id::text, customer_id::text, order_date::date, total_amount FROM niche_data.orders", engine)
order_items_df = try_sql("SELECT order_id::text, article_id::text, quantity, price FROM niche_data.order_items", engine)

# wishlist, carts, returns (optional)
wishlist_df = try_sql("SELECT customer_id::text, article_id::text, added_at::timestamp FROM niche_data.wishlist", engine)
cart_df = try_sql("SELECT customer_id::text, session_id, added_at::timestamp, cart_id::text FROM niche_data.carts", engine)
returns_df = try_sql("SELECT customer_id::text, order_id::text, returned_at::timestamp FROM niche_data.returns", engine)

# reviews (optional)
reviews_df = try_sql("SELECT customer_id::text, article_id::text, rating, review_text FROM niche_data.reviews", engine)

# Basic existence flags
has_tx = not tx_df.empty
has_events = not events_df.empty
has_articles = not articles_df.empty
has_orders = not orders_df.empty
has_order_items = not order_items_df.empty

# --- RFM and basic customer aggregates (from transactions) ---
print("Computing RFM and transaction aggregates...")
if has_tx:
    tx_df["t_date"] = pd.to_datetime(tx_df["t_date"])
    # If quantity missing, assume 1
    if "quantity" not in tx_df.columns:
        tx_df["quantity"] = 1
    rfm = tx_df.groupby("customer_id").agg(
        total_orders=("t_date", "nunique"),
        total_transactions=("t_date", "count"),
        total_items_sold=("quantity", "sum"),
        lifetime_value=("price", "sum"),
        avg_order_value=("price", "mean"),
        avg_item_price=("price", "mean"),
        first_purchase_date=("t_date", "min"),
        last_purchase_date=("t_date", "max")
    ).reset_index()
    rfm["days_since_last_purchase"] = (pd.Timestamp(datetime.utcnow().date()) - rfm["last_purchase_date"]).dt.days
else:
    rfm = pd.DataFrame(columns=[
        "customer_id", "total_orders", "total_transactions", "total_items_sold",
        "lifetime_value","avg_order_value","avg_item_price","first_purchase_date","last_purchase_date","days_since_last_purchase"
    ])

# --- order-level features if order_items present (avg_basket_size, avg_basket_value) ---
if has_order_items and has_orders:
    print("Computing basket-level features from order_items/orders...")
    # compute per order: items and total
    oi = order_items_df.copy()
    oi["quantity"] = oi.get("quantity", 1)
    order_agg = oi.groupby("order_id").agg(order_items_count=("quantity", "sum"), order_value=("price", "sum")).reset_index()
    orders_local = orders_df.merge(order_agg, on="order_id", how="left")
    orders_local["order_value"] = orders_local["order_value"].fillna(orders_local["total_amount"])
    cust_basket = orders_local.groupby("customer_id").agg(
        avg_basket_size=("order_items_count", "mean"),
        avg_basket_value=("order_value", "mean"),
        total_orders_orders=("order_id", "nunique")
    ).reset_index()
    # merge with rfm
    rfm = rfm.merge(cust_basket, on="customer_id", how="left")
else:
    rfm["avg_basket_size"] = np.nan
    rfm["avg_basket_value"] = np.nan

# --- Category affinity from events + articles (views/purchases by category) ---
print("Computing category affinity features...")
if has_events and has_articles:
    ev = events_df.merge(articles_df, left_on="article_id", right_on="article_id", how="left")
    ev["category"] = ev["category"].fillna("unknown")
    # count views/purchases by category per customer
    cat_counts = ev.groupby(["customer_id", "category"]).size().reset_index(name="count")
    # top categories overall
    top_cats = cat_counts.groupby("category")["count"].sum().nlargest(20).index.tolist()
    cat_counts = cat_counts[cat_counts["category"].isin(top_cats)]
    pivot = cat_counts.pivot_table(index="customer_id", columns="category", values="count", fill_value=0)
    pivot.columns = [f"cat_{str(c).replace(' ','_')}" for c in pivot.columns]
    cat_pref = pivot.reset_index()
else:
    cat_pref = pd.DataFrame(columns=["customer_id"])

# --- Engagement features: sessions, total_events, view_to_buy ratio, session_count ---
print("Computing engagement features...")
eng = pd.DataFrame({"customer_id": []})
if has_events:
    events_df["created_at"] = pd.to_datetime(events_df["created_at"])
    ev_agg = events_df.groupby("customer_id").agg(
        total_events=("event_type", "count"),
        unique_sessions=("session_id", "nunique")
    ).reset_index()
    eng = ev_agg
else:
    eng = pd.DataFrame(columns=["customer_id", "total_events", "unique_sessions"])

# purchases_count and conversion proxy (from transactions & events)
purchases = pd.DataFrame({"customer_id": [], "purchase_count": []})
if has_tx:
    purchases = tx_df.groupby("customer_id").size().reset_index(name="purchase_count")
else:
    purchases = pd.DataFrame(columns=["customer_id", "purchase_count"])

# join everything
print("Assembling feature table...")
all_customers = pd.Series(
    pd.concat([rfm["customer_id"] if not rfm.empty else pd.Series(dtype=str),
               cat_pref["customer_id"] if not cat_pref.empty else pd.Series(dtype=str),
               eng["customer_id"] if not eng.empty else pd.Series(dtype=str),
               purchases["customer_id"] if not purchases.empty else pd.Series(dtype=str)]).unique()
).astype(str)

base = pd.DataFrame({"customer_id": all_customers})

feat = base.merge(rfm, on="customer_id", how="left")
feat = feat.merge(cat_pref, on="customer_id", how="left")
feat = feat.merge(eng, on="customer_id", how="left")
feat = feat.merge(purchases, on="customer_id", how="left")

# fill numeric NA with sensible defaults
num_cols = feat.select_dtypes(include=[np.number]).columns.tolist()
feat[num_cols] = feat[num_cols].fillna(0)

# conversion proxy
feat["conversion"] = feat.apply(lambda r: (r["purchase_count"] / r["total_events"]) if r["total_events"]>0 else 0.0, axis=1)

# discount usage ratio (if discount info exists in transactions or orders)
if "discount" in tx_df.columns:
    disc = tx_df.groupby("customer_id").agg(discount_usage_ratio=("discount", lambda s: (s>0).mean()))
    feat = feat.merge(disc, left_on="customer_id", right_index=True, how="left")
    feat["discount_usage_ratio"] = feat["discount_usage_ratio"].fillna(0)
else:
    feat["discount_usage_ratio"] = 0.0

# wishlist/cart features
if not wishlist_df.empty:
    ws = wishlist_df.groupby("customer_id").size().reset_index(name="wishlist_count")
    feat = feat.merge(ws, on="customer_id", how="left")
    feat["wishlist_count"] = feat["wishlist_count"].fillna(0).astype(int)
else:
    feat["wishlist_count"] = 0

if not cart_df.empty:
    cart_agg = cart_df.groupby("customer_id").agg(cart_sessions=("session_id","nunique")).reset_index()
    feat = feat.merge(cart_agg, on="customer_id", how="left")
    feat["cart_sessions"] = feat["cart_sessions"].fillna(0).astype(int)
else:
    feat["cart_sessions"] = 0

# returns
if not returns_df.empty:
    ret = returns_df.groupby("customer_id").size().reset_index(name="return_count")
    feat = feat.merge(ret, on="customer_id", how="left")
    feat["return_rate"] = feat["return_count"] / feat["total_orders"].replace(0, np.nan)
    feat["return_rate"] = feat["return_rate"].fillna(0)
else:
    feat["return_rate"] = 0.0

# temporal features: weekday preferences, active_days
if has_events:
    events_df["date"] = events_df["created_at"].dt.date
    active_days = events_df.groupby("customer_id")["date"].nunique().reset_index(name="active_days")
    feat = feat.merge(active_days, on="customer_id", how="left")
    feat["active_days"] = feat["active_days"].fillna(0).astype(int)
else:
    feat["active_days"] = 0

# top categories as strings for interpretation
if not cat_pref.empty:
    cat_cols = [c for c in feat.columns if str(c).startswith("cat_")]
    def top_k_cats(row, k=3):
        vals = row[cat_cols].values
        if vals.sum()==0:
            return []
        top_idx = np.argsort(vals)[-k:][::-1]
        return [cat_cols[i].replace("cat_","") for i in top_idx if vals[i]>0]
    feat["top_categories"] = feat.apply(lambda r: top_k_cats(r,3), axis=1)
else:
    feat["top_categories"] = feat["top_categories"] = [[] for _ in range(len(feat))]

# time_on_platform: if customer signup table exists else 0
users_df = try_sql("SELECT customer_id::text, created_at::date as signup_date FROM niche_data.customers", engine)
if not users_df.empty:
    users_df["signup_date"] = pd.to_datetime(users_df["signup_date"])
    users_df["time_on_platform_days"] = (pd.Timestamp(datetime.utcnow().date()) - users_df["signup_date"]).dt.days
    feat = feat.merge(users_df[["customer_id", "time_on_platform_days"]], on="customer_id", how="left")
    feat["time_on_platform_days"] = feat["time_on_platform_days"].fillna(0).astype(int)
else:
    feat["time_on_platform_days"] = 0

# final consistency: ensure types
feat["customer_id"] = feat["customer_id"].astype(str)
# reorder columns: customer_id first
cols = [c for c in feat.columns if c!="customer_id"]
feat = feat[["customer_id"] + cols]

# save full features
full_path = os.path.join(OUT_DIR, "features_full.parquet")
feat.to_parquet(full_path, index=False)
print("Saved full feature table to", full_path)

# derive model features: choose a subset (RFM + engagement + top category counts + conversion)
model_cols = [
    "customer_id",
    "days_since_last_purchase", "total_transactions", "lifetime_value", "avg_order_value",
    "total_events", "unique_sessions", "purchase_count", "avg_basket_size",
    "conversion", "active_days", "time_on_platform_days", "discount_usage_ratio",
    "wishlist_count", "cart_sessions", "return_rate"
]
# include top N category columns if present
cat_columns = [c for c in feat.columns if c.startswith("cat_")]
model_cols = model_cols + cat_columns[:20]  # at most 20 category features

model_df = feat[[c for c in model_cols if c in feat.columns]].copy()

# save model features and a sample
model_path = os.path.join(OUT_DIR, "model_features.parquet")
sample_path = os.path.join(OUT_DIR, "features_sample.csv")
model_df.to_parquet(model_path, index=False)
model_df.head(200).to_csv(sample_path, index=False)
print("Saved model features to", model_path)
print("Saved sample to", sample_path)

# quick summaries (EDA-friendly)
print("\nQuick summary:")
print("Total customers:", feat["customer_id"].nunique())
print("Customers with purchases:", (feat["purchase_count"]>0).sum() if "purchase_count" in feat.columns else 0)
print("Median recency (days):", int(feat["days_since_last_purchase"].median()) if "days_since_last_purchase" in feat.columns else "NA")
print("Median monetary:", float(feat["lifetime_value"].median()) if "lifetime_value" in feat.columns else "NA")
