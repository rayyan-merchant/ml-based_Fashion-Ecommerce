"""features.py
Feature engineering + train/val split + evaluation metric wrapper.
"""
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error

VAL_DAYS = 28


def build_features(dfc):
    dfc = dfc.copy().sort_values("date")
    dfc["day"] = dfc["date"].dt.day
    dfc["month"] = dfc["date"].dt.month
    dfc["year"] = dfc["date"].dt.year
    dfc["weekday"] = dfc["date"].dt.weekday
    dfc["is_weekend"] = (dfc["weekday"] >= 5).astype(int)

    dfc["lag_1"] = dfc["daily_sales"].shift(1).fillna(0)
    dfc["lag_7"] = dfc["daily_sales"].shift(7).fillna(0)
    dfc["rolling_7"] = dfc["daily_sales"].rolling(7, min_periods=1).mean()
    dfc["rolling_30"] = dfc["daily_sales"].rolling(30, min_periods=1).mean()

    dfc["avg_price"] = dfc["avg_price"].fillna(0)
    return dfc


def train_val_split(dfc, val_days=VAL_DAYS):
    max_date = dfc["date"].max()
    val_start = max_date - pd.Timedelta(days=val_days-1)
    return dfc[dfc["date"] < val_start], dfc[dfc["date"] >= val_start]


def evaluate(y_true, y_pred):
    rmse = float(mean_squared_error(y_true, y_pred))
    try:
        mape = float(mean_absolute_percentage_error(y_true, y_pred))
    except Exception:
        mape = np.nan
    return rmse, mape
