# app/routes/timeseries.py

import os
import sys
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

# Add the ml/timeseries folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../ml/timeseries')))

# Import your existing utilities
from forecasting_utils import _load_forecast_files, aggregate_forecasts
from analytics_part3 import (
    compute_revenue_forecast, compute_stockout_risk,
    classify_trend, compute_monthly_growth_rate,
    assign_product_lifecycle, compute_sales_funnel
)
from data_loader import load_data, get_db_engine

# Import the new endpoints module
try:
    from endpoints import (
        get_all_forecasts as ep_get_all_forecasts,
        get_article_forecast as ep_get_article_forecast,
        get_category_forecast as ep_get_category_forecast,
        get_revenue_analytics as ep_get_revenue_analytics,
        get_stockout_analytics as ep_get_stockout_analytics,
        get_trend_analytics as ep_get_trend_analytics,
        get_monthly_growth_analytics as ep_get_monthly_growth_analytics,
        get_lifecycle_analytics as ep_get_lifecycle_analytics,
        get_aggregated_analytics as ep_get_aggregated_analytics,
        run_full_pipeline as ep_run_full_pipeline,
        get_forecast_by_date_range as ep_get_forecast_by_date_range,
        get_forecast_horizon as ep_get_forecast_horizon
    )
    ENDPOINTS_AVAILABLE = True
except ImportError:
    ENDPOINTS_AVAILABLE = False
    print("Warning: Could not import endpoints module")

OUT_BASE = "data/ml/timeseries/final_xgb"
FORECAST_DIR = os.path.join(OUT_BASE, "forecasts")
EDA_DIR = os.path.join(OUT_BASE, "eda")

timeseries_router = APIRouter()

# Utility function to check data availability
def check_data_availability():
    if not os.path.exists(OUT_BASE):
        raise HTTPException(503, "ML data directory not found")
    if not os.path.exists(FORECAST_DIR):
        raise HTTPException(503, "Forecast data directory not found")

# ============================================================
# FORECAST DASHBOARD ENDPOINTS
# ============================================================

@timeseries_router.get("/forecasts/all")
def get_all_forecasts():
    """Get all forecasts for articles/categories."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_all_forecasts()
        except Exception as e:
            raise HTTPException(500, f"Error getting all forecasts: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        if df.empty:
            raise HTTPException(404, "No forecasts found.")
        return df.to_dict(orient="records")

@timeseries_router.get("/forecast/article/{article_id}")
def get_article_forecast(article_id: str):
    """Get forecast for a specific article."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            result = ep_get_article_forecast(article_id)
            if not result:
                raise HTTPException(404, "No forecast found for this article.")
            return result
        except Exception as e:
            raise HTTPException(500, f"Error getting forecast for article: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        df = df[df["article_id"].astype(str) == str(article_id)]
        if df.empty:
            raise HTTPException(404, "No forecast found for this article.")
        return df.to_dict(orient="records")

@timeseries_router.get("/forecast/category/{category_id}")
def get_category_forecast(category_id: int):
    """Get forecast for a specific category."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            result = ep_get_category_forecast(str(category_id))
            if not result:
                raise HTTPException(404, "No forecast found for this category.")
            return result
        except Exception as e:
            raise HTTPException(500, f"Error getting forecast for category: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        df = df[df["category_id"] == category_id]
        if df.empty:
            raise HTTPException(404, "No forecast found for this category.")
        return df.to_dict(orient="records")

@timeseries_router.get("/analytics/revenue")
def get_revenue_forecast():
    """Get revenue analytics for forecasts."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_revenue_analytics()
        except Exception as e:
            raise HTTPException(500, f"Error computing revenue analytics: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        if df.empty:
            raise HTTPException(404, "No forecast files found.")
        raw_df = load_data(from_cache=True)
        rev = compute_revenue_forecast(df, raw_df)
        return rev.to_dict(orient="records")

# ============================================================
# ANALYTICS DASHBOARD ENDPOINTS
# ============================================================

@timeseries_router.get("/analytics/stockout")
def get_stockout_analytics():
    """Get stockout risk analytics."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_stockout_analytics()
        except Exception as e:
            raise HTTPException(500, f"Error computing stockout analytics: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        raw_df = load_data(from_cache=True)
        rev = compute_revenue_forecast(df, raw_df)
        result = compute_stockout_risk(rev)
        return result.to_dict(orient="records")

@timeseries_router.get("/analytics/trends")
def get_trend_analytics():
    """Get trend classification analytics."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_trend_analytics()
        except Exception as e:
            raise HTTPException(500, f"Error computing trend analytics: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        raw_df = load_data(from_cache=True)
        rev = compute_revenue_forecast(df, raw_df)
        result = classify_trend(rev)
        return result.to_dict(orient="records")

@timeseries_router.get("/analytics/monthly_growth")
def get_monthly_growth_analytics():
    """Get monthly growth rate analytics."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_monthly_growth_analytics()
        except Exception as e:
            raise HTTPException(500, f"Error computing monthly growth analytics: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        raw_df = load_data(from_cache=True)
        rev = compute_revenue_forecast(df, raw_df)
        monthly = compute_monthly_growth_rate(rev)
        return monthly.to_dict(orient="records")

@timeseries_router.get("/analytics/lifecycle")
def get_lifecycle_analytics():
    """Get product lifecycle analytics."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_lifecycle_analytics()
        except Exception as e:
            raise HTTPException(500, f"Error computing lifecycle analytics: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        raw_df = load_data(from_cache=True)
        rev = compute_revenue_forecast(df, raw_df)
        result = assign_product_lifecycle(rev)
        return result.to_dict(orient="records")

# ============================================================
# AGGREGATED VIEWS ENDPOINTS
# ============================================================

@timeseries_router.get("/analytics/aggregate")
def get_aggregated_analytics(
    view_type: str = Query("weekly", description="Either 'weekly' or 'monthly'")
):
    """Get aggregated forecast analytics."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_aggregated_analytics(view_type)
        except Exception as e:
            raise HTTPException(500, f"Error computing aggregated analytics: {str(e)}")
    else:
        # Fallback to original implementation
        df = _load_forecast_files(FORECAST_DIR)
        if df.empty:
            raise HTTPException(404, "No forecasts found.")
        weekly, monthly = aggregate_forecasts(df)
        return {
            "weekly": weekly.to_dict(orient="records") if weekly is not None else [],
            "monthly": monthly.to_dict(orient="records") if monthly is not None else []
        }

# ============================================================
# ADDITIONAL HELPER ENDPOINTS FOR INTERACTIVE EXPLORATION
# ============================================================

@timeseries_router.get("/forecast/date-range")
def get_forecast_by_date_range(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """Get forecasts within a specific date range."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_forecast_by_date_range(start_date, end_date)
        except Exception as e:
            raise HTTPException(500, f"Error getting forecasts by date range: {str(e)}")
    else:
        # Fallback implementation
        try:
            df = _load_forecast_files(FORECAST_DIR)
            if df.empty:
                return []
            
            # Convert string dates to datetime
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Filter by date range
            filtered_fc = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            return filtered_fc.to_dict(orient="records") if not filtered_fc.empty else []
        except Exception as e:
            raise HTTPException(500, f"Error getting forecasts by date range: {str(e)}")

@timeseries_router.get("/forecast/horizon")
def get_forecast_horizon(
    days: int = Query(30, description="Number of days into the future")
):
    """Get forecasts for a specific horizon (next N days)."""
    check_data_availability()
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_get_forecast_horizon(days)
        except Exception as e:
            raise HTTPException(500, f"Error getting forecast horizon: {str(e)}")
    else:
        # Fallback implementation
        try:
            df = _load_forecast_files(FORECAST_DIR)
            if df.empty:
                return []
            
            # Get forecasts from today onwards for the specified number of days
            today = pd.Timestamp.now().normalize()
            end_date = today + timedelta(days=days)
            
            # Filter by date range
            filtered_fc = df[(df['date'] >= today) & (df['date'] <= end_date)]
            return filtered_fc.to_dict(orient="records") if not filtered_fc.empty else []
        except Exception as e:
            raise HTTPException(500, f"Error getting forecast horizon: {str(e)}")

# ============================================================
# PIPELINE ENDPOINT
# ============================================================

@timeseries_router.post("/pipeline/run")
def run_full_pipeline():
    """
    Run the full timeseries pipeline.
    Runs:
     - load data
     - clean + reindex
     - EDA
     - model training (article + category)
     - forecasting
     - analytics (trends, stockout, lifecycle)
     - aggregations
    """
    if ENDPOINTS_AVAILABLE:
        try:
            return ep_run_full_pipeline()
        except Exception as e:
            raise HTTPException(500, f"Error running pipeline: {str(e)}")
    else:
        # Fallback to original implementation
        try:
            os.system("python ml/timeseries/main_pipeline.py")
            return {"status": "Pipeline executed successfully."}
        except Exception as e:
            raise HTTPException(500, f"Pipeline failed: {e}")

# ============================================================
# ROOT INFO ENDPOINT
# ============================================================

@timeseries_router.get("/")
def get_timeseries_info():
    """Get information about available timeseries endpoints."""
    return {
        "message": "Timeseries ML API",
        "endpoints": {
            "forecast_dashboard": {
                "get_all_forecasts": "/forecasts/all",
                "get_article_forecast": "/forecast/article/{article_id}",
                "get_category_forecast": "/forecast/category/{category_id}",
                "get_revenue_analytics": "/analytics/revenue"
            },
            "analytics_dashboard": {
                "get_stockout_analytics": "/analytics/stockout",
                "get_trend_analytics": "/analytics/trends",
                "get_monthly_growth_analytics": "/analytics/monthly_growth",
                "get_lifecycle_analytics": "/analytics/lifecycle"
            },
            "aggregated_views": {
                "get_aggregated_analytics": "/analytics/aggregate?view_type=weekly|monthly"
            },
            "helpers": {
                "get_forecast_by_date_range": "/forecast/date-range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD",
                "get_forecast_horizon": "/forecast/horizon?days=N"
            },
            "pipeline": {
                "run_full_pipeline": "/pipeline/run (POST)"
            }
        },
        "status": "active" if os.path.exists(OUT_BASE) and os.path.exists(FORECAST_DIR) else "inactive"
    }
