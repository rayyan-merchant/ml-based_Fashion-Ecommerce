import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import scipy.sparse

# Create directories
os.makedirs("data/ml", exist_ok=True)

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
# ---- SQL queries ----
sql_article_daily = '''
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
'''

sql_category_daily = '''
SELECT
    a.category_id,
    t.t_dat::date AS date,
    COUNT(*) AS daily_sales,
    SUM(t.price) AS daily_revenue
FROM niche_data.transactions t
JOIN niche_data.articles a ON t.article_id = a.article_id
GROUP BY a.category_id, t.t_dat::date
ORDER BY a.category_id, date;
'''

# ---- read from db ----
daily_article = pd.read_sql(sql_article_daily, engine)
daily_category = pd.read_sql(sql_category_daily, engine)

# ---- Ensure date columns are datetime (coerce errors -> NaT) ----
daily_article['date'] = pd.to_datetime(daily_article['date'], errors='coerce')
daily_category['date'] = pd.to_datetime(daily_category['date'], errors='coerce')

# Optional quick checks (useful while debugging)
print("daily_article shape:", daily_article.shape)
print("daily_category shape:", daily_category.shape)
print("daily_article date dtype:", daily_article['date'].dtype)
print("daily_category date dtype:", daily_category['date'].dtype)
print("Number of NaT in article dates:", daily_article['date'].isna().sum())
print("Number of NaT in category dates:", daily_category['date'].isna().sum())

# If there are NaT dates, drop them (or handle otherwise)
if daily_article['date'].isna().any():
    print("Dropping rows with invalid article dates...")
    daily_article = daily_article.dropna(subset=['date'])
if daily_category['date'].isna().any():
    print("Dropping rows with invalid category dates...")
    daily_category = daily_category.dropna(subset=['date'])

# ---- Calendar features for articles ----
daily_article['is_weekend'] = daily_article['date'].dt.dayofweek >= 5
daily_article['weekday'] = daily_article['date'].dt.dayofweek
daily_article['month'] = daily_article['date'].dt.month
daily_article['year'] = daily_article['date'].dt.year

# ---- Rolling windows for articles ----
daily_article = daily_article.sort_values(['article_id', 'date']).reset_index(drop=True)
daily_article['rolling_7'] = (
    daily_article.groupby('article_id')['daily_sales']
                 .transform(lambda x: x.rolling(7, min_periods=1).mean())
)
daily_article['rolling_30'] = (
    daily_article.groupby('article_id')['daily_sales']
                 .transform(lambda x: x.rolling(30, min_periods=1).mean())
)

# ---- Rolling windows for categories ----
daily_category = daily_category.sort_values(['category_id', 'date']).reset_index(drop=True)
daily_category['rolling_7'] = (
    daily_category.groupby('category_id')['daily_sales']
                  .transform(lambda x: x.rolling(7, min_periods=1).mean())
)
daily_category['rolling_30'] = (
    daily_category.groupby('category_id')['daily_sales']
                  .transform(lambda x: x.rolling(30, min_periods=1).mean())
)

# ---- Weekly aggregation using resample (requires DatetimeIndex) ----
# Articles: group by article_id then resample by week
weekly_article = (
    daily_article
    .set_index('date')                       # date -> DatetimeIndex
    .groupby('article_id')
    .resample('W')                           # weekly bins (Sunday by default)
    .agg(
        weekly_sales=('daily_sales', 'sum'),
        weekly_revenue=('daily_revenue', 'sum')
    )
    .reset_index()                           # brings article_id and date back as columns
)

# Categories: group by category_id then resample by week
weekly_category = (
    daily_category
    .set_index('date')
    .groupby('category_id')
    .resample('W')
    .agg(
        weekly_sales=('daily_sales', 'sum'),
        weekly_revenue=('daily_revenue', 'sum')
    )
    .reset_index()
)

# Optional: If you prefer weeks that start on Monday use 'W-MON' instead of 'W'
# e.g. .resample('W-MON')

# ---- Output saving ----
out_dir = "data/ml/timeseries"
os.makedirs(out_dir, exist_ok=True)

daily_article_path = os.path.join(out_dir, "daily_article.parquet")
daily_category_path = os.path.join(out_dir, "daily_category.parquet")
weekly_article_path = os.path.join(out_dir, "weekly_article.parquet")
weekly_category_path = os.path.join(out_dir, "weekly_category.parquet")

daily_article.to_parquet(daily_article_path, index=False)
daily_category.to_parquet(daily_category_path, index=False)
weekly_article.to_parquet(weekly_article_path, index=False)
weekly_category.to_parquet(weekly_category_path, index=False)

print("Saved parquet files to:", out_dir)
print("daily_article example:\n", daily_article.head(3))
print("weekly_article example:\n", weekly_article.head(3))
