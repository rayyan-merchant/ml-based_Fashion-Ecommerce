"""eda_reports.py
Small helpers that save EDA CSVs into a target directory.
"""
import os
import pandas as pd


def ensure_dir(d):
    os.makedirs(d, exist_ok=True)
    return d


def generate_eda(df, out_dir="data/ml/timeseries/final_xgb/eda"):
    ensure_dir(out_dir)

    df.groupby('article_id')['daily_sales'].sum().reset_index().sort_values('daily_sales', ascending=False)\
        .to_csv(os.path.join(out_dir, "article_total_sales.csv"), index=False)

    df.groupby('category_id')['daily_sales'].sum().reset_index().sort_values('daily_sales', ascending=False)\
        .to_csv(os.path.join(out_dir, "category_total_sales.csv"), index=False)

    season = df.assign(year=df['date'].dt.year, month=df['date'].dt.month)\
               .groupby(['year','month'])['daily_sales'].sum().reset_index()
    season.to_csv(os.path.join(out_dir, "monthly_sales_overview.csv"), index=False)

    zero_frac = df.groupby('article_id')['daily_sales'].apply(lambda s: (s == 0).mean()).reset_index()
    zero_frac.columns = ['article_id', 'zero_fraction']
    zero_frac.to_csv(os.path.join(out_dir, "article_zero_fraction.csv"), index=False)

    print("EDA files saved to", out_dir)
