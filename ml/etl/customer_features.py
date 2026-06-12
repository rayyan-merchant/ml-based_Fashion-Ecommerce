import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import numpy as np

os.makedirs("data/ml", exist_ok=True)
load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("=" * 60)
print("Dataset C: Customer Features (RFM Analysis)")
print("=" * 60)

# RFM Analysis
print("\n1️⃣  Querying customer transactions...")

# ==============================================================
# 1. SQL QUERIES — CLEANED TO MATCH EXACT DATA DICTIONARY
# ==============================================================

sql_customers = """
SELECT 
    customer_id,
    age,
    club_member_status,
    fashion_news_frequency,
    active,
    signup_date,
    (DATE '2020-09-22' - signup_date) AS signup_age_days
FROM niche_data.customers;
"""

sql_rfm = """
SELECT
    customer_id,
    MIN(t_dat) AS first_purchase_date,
    MAX(t_dat) AS last_purchase_date,
    COUNT(*) AS total_transactions,
    SUM(price) AS total_amount_spent,
    (DATE '2020-09-22' - MAX(t_dat)) AS recency_days
FROM niche_data.transactions
GROUP BY customer_id;
"""

# --- 6-month frequency + spend
sql_6m = """
SELECT
    customer_id,
    COUNT(*) AS frequency_6m,
    SUM(price) AS monetary_6m
FROM niche_data.transactions
WHERE t_dat BETWEEN DATE '2020-03-22' AND DATE '2020-09-22'
GROUP BY customer_id;
"""

# --- 12-month frequency + spend
sql_12m = """
SELECT
    customer_id,
    COUNT(*) AS frequency_12m,
    SUM(price) AS monetary_12m
FROM niche_data.transactions
WHERE t_dat BETWEEN DATE '2019-09-22' AND DATE '2020-09-22'
GROUP BY customer_id;
"""

# --- Orders + Basket + Items Bought
sql_orders = """
SELECT
    o.customer_id,
    COUNT(o.order_id) AS total_orders,
    SUM(oi.quantity) AS total_items_bought,
    SUM(o.total_amount) AS total_revenue,
    AVG(o.total_amount) AS avg_order_value
FROM niche_data.orders o
LEFT JOIN niche_data.order_items oi ON o.order_id = oi.order_id
GROUP BY o.customer_id;
"""

# --- Wishlist (count of wishlist items)
sql_wishlist = """
SELECT
    customer_id,
    COUNT(*) AS wishlist_size
FROM niche_data.wishlist
GROUP BY customer_id;
"""

# --- Events (Dataset F3 compatible)
sql_events = """
SELECT
    customer_id,
    COUNT(*) AS session_events,
    SUM(CASE WHEN event_type='view' THEN 1 ELSE 0 END) AS views,
    SUM(CASE WHEN event_type='click' THEN 1 ELSE 0 END) AS clicks,
    SUM(CASE WHEN event_type='cart' THEN 1 ELSE 0 END) AS carts,
    SUM(CASE WHEN event_type='buy' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN event_type='wishlist' THEN 1 ELSE 0 END) AS wishlist_events
FROM niche_data.events
GROUP BY customer_id;
"""

# --- Sales channel preference
sql_channels = """
SELECT
    customer_id,
    SUM(CASE WHEN sales_channel_id = 1 THEN 1 ELSE 0 END) AS ch1,
    SUM(CASE WHEN sales_channel_id = 2 THEN 1 ELSE 0 END) AS ch2,
    SUM(CASE WHEN sales_channel_id = 3 THEN 1 ELSE 0 END) AS ch3
FROM niche_data.transactions
GROUP BY customer_id;
"""

# --- Top Category
sql_top_category = """
SELECT customer_id, category_id AS top_category
FROM (
    SELECT 
        t.customer_id,
        a.category_id,
        ROW_NUMBER() OVER (PARTITION BY t.customer_id ORDER BY COUNT(*) DESC) AS rn
    FROM niche_data.transactions t
    JOIN niche_data.articles a ON t.article_id = a.article_id
    GROUP BY t.customer_id, a.category_id
) x
WHERE rn = 1;
"""

# ==============================================================
# 2. LOAD ALL TABLES
# ==============================================================

print("Loading customers...")
customers = pd.read_sql(sql_customers, engine)
print(f"   → {len(customers):,} customers loaded")

print("Loading RFM...")
rfm = pd.read_sql(sql_rfm, engine)
print(f"   → {len(rfm):,} customers in RFM")
print("   RFM columns:", rfm.columns.tolist())   # ← THIS WILL TELL YOU THE TRUTH

print("Loading 6m...")
sixm = pd.read_sql(sql_6m, engine)
print(f"   → {len(sixm):,} in 6m")

print("Loading 12m...")
twelvem = pd.read_sql(sql_12m, engine)

print("Loading orders...")
orders = pd.read_sql(sql_orders, engine)

print("Loading wishlist...")
wishlist = pd.read_sql(sql_wishlist, engine)

print("Loading events...")
events = pd.read_sql(sql_events, engine)

print("Loading channels...")
channels = pd.read_sql(sql_channels, engine)

print("Loading top_category...")
top_category = pd.read_sql(sql_top_category, engine)

# ==============================================================
# 3. MERGE INTO DATASET C
# ==============================================================

df = (
    customers
    .merge(rfm, on="customer_id", how="left")
    .merge(sixm, on="customer_id", how="left")
    .merge(twelvem, on="customer_id", how="left")
    .merge(orders, on="customer_id", how="left")
    .merge(wishlist, on="customer_id", how="left")
    .merge(events, on="customer_id", how="left")
    .merge(channels, on="customer_id", how="left")
    .merge(top_category, on="customer_id", how="left")
)

# ==============================================================
# 4. FEATURE ENGINEERING (STRICTLY MATCHING DICTIONARY)
# ==============================================================

# --- avg_transaction_value
df["avg_transaction_value"] = df["total_amount_spent"] / df["total_transactions"]

# --- avg_basket_size
df["avg_basket_size"] = df["total_items_bought"] / df["total_orders"]

# --- cart additions & abandon rate
df["cart_additions"] = df["carts"].fillna(0)
df["cart_abandon_rate"] = np.where(df["carts"] > 0,
                                   1 - (df["buys"] / df["carts"]),
                                   np.nan)

# --- channel choice
df["most_used_sales_channel"] = df[["ch1", "ch2", "ch3"]].idxmax(axis=1)

# --- conversion & CTR metrics
df["conversion_rate"] = df["buys"] / df["views"]
df["click_through_rate"] = df["clicks"] / df["views"]
df["add_to_cart_rate"] = df["carts"] / df["clicks"]
df["view_to_buy_rate"] = df["buys"] / df["views"]

# --- dominant event type
df["dominant_event_type"] = df[["views", "clicks", "carts", "buys"]].idxmax(axis=1)

# --- RFM scoring
df["R_score"] = pd.qcut(df["recency_days"], q=5, labels=False, duplicates="drop")
df["F_score"] = pd.qcut(df["total_transactions"], q=5, labels=False, duplicates="drop")
df["M_score"] = pd.qcut(df["total_amount_spent"], q=5, labels=False, duplicates="drop")
df["RFM_score"] = df["R_score"] + df["F_score"] + df["M_score"]

# ==============================================================
# 5. SAVE
# ==============================================================

df.to_parquet("data/ml/customer_features.parquet", index=False)

print("Dataset C created successfully!")
