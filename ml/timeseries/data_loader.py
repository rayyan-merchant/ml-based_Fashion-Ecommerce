"""data_loader.py
Loads data from Postgres and provides a small helper to persist/read local parquet for faster iteration.
"""
import os
from sqlalchemy import create_engine
import pandas as pd

# CONFIG (override in runtime or via environment variables)
DB_URI = os.environ.get("TIMESERIES_DB_URI", "postgresql://postgres:rayyan123@localhost:5432/fashion_db")
SQL_DAILY_ARTICLE = """
SELECT
    t.article_id,
    a.category_id,
    t.t_dat::date AS date,
    COUNT(*) AS daily_sales,
    SUM(t.price) AS daily_revenue,
    AVG(t.price) AS avg_price
FROM niche_data.transactions t
JOIN niche_data.articles a ON t.article_id = a.article_id
GROUP BY t.article_id, a.category_id, t.t_dat::date
ORDER BY t.article_id, date;
"""

CACHE_PATH = os.environ.get("TIMESERIES_CACHE", "data/ml/timeseries/final_xgb/raw_daily_articles.parquet")


def load_data(from_cache=True):
    """Load daily article-level sales data from Postgres (or cache).

    Returns
    -------
    pd.DataFrame
    """
    if from_cache and os.path.exists(CACHE_PATH):
        print("Loading data from cache:", CACHE_PATH)
        return pd.read_parquet(CACHE_PATH)

    print("Connecting to DB and loading SQL...")
    engine = create_engine(DB_URI)
    df = pd.read_sql(SQL_DAILY_ARTICLE, engine)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values(["article_id", "date"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    df.to_parquet(CACHE_PATH, index=False)
    print("Saved cache to", CACHE_PATH)
    return df


def get_db_engine():
    return create_engine(DB_URI)
