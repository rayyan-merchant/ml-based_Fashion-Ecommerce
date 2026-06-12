"""main_pipeline.py
Orchestrates the full run. This file is the single entry point.
"""
import os

from data_loader import load_data, get_db_engine
from clean_reindex import clean_and_reindex
from eda_reports import generate_eda
from model_xgb_articles import train_article_models
from model_xgb_categories import train_category_models
from forecasting_utils import _load_forecast_files, aggregate_forecasts
from analytics_part3 import compute_revenue_forecast, compute_stockout_risk, classify_trend, compute_monthly_growth_rate, assign_product_lifecycle, compute_sales_funnel

OUT_BASE = "data/ml/timeseries/final_xgb"
EDA_DIR = os.path.join(OUT_BASE, "eda")

def main():
    os.makedirs(EDA_DIR, exist_ok=True)

    # 1) load
    df = load_data(from_cache=True)

    # 2) clean + reindex
    df_clean, clean_eda = clean_and_reindex(df, id_col="article_id")
    clean_eda.to_csv(os.path.join(EDA_DIR, "cleaning_overview.csv"), index=False)

    # 3) eda
    generate_eda(df_clean)

    # 4) train models and produce forecasts
    train_article_models(df_clean, top_k=100)
    train_category_models(df_clean)

    # 5) load produced forecasts and run analytics
    all_fc = _load_forecast_files()
    rev_fc = compute_revenue_forecast(all_fc, df_clean)

    stock_risk = compute_stockout_risk(rev_fc)
    trend_df = classify_trend(rev_fc)
    monthly_gr = compute_monthly_growth_rate(rev_fc)
    lifecycle_df = assign_product_lifecycle(rev_fc)

    # save funnel (reads events table from DB)
    engine = get_db_engine()
    funnel_df = compute_sales_funnel(engine, analytics_dir=EDA_DIR)

    # aggregate forecasts
    aggregate_forecasts(all_fc)

    print("Pipeline complete. Results in:", OUT_BASE)


if __name__ == "__main__":
    main()
