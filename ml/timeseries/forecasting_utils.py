"""forecasting_utils.py
Helper utilities for recursive forecasting, loading forecast files and aggregations.
"""
import os
import glob
import numpy as np
import pandas as pd

OUT_BASE = "data/ml/timeseries/final_xgb"
EDA_DIR = os.path.join(OUT_BASE, "eda")
FORECAST_DIR = os.path.join(OUT_BASE, "forecasts")

def recursive_forecast(model, scaler, history, days, features):
    outputs = []
    hist = history.copy().reset_index(drop=True)

    for _ in range(days):
        next_date = hist["date"].iloc[-1] + pd.Timedelta(days=1)

        row = {
            "date": next_date,
            "day": next_date.day,
            "month": next_date.month,
            "year": next_date.year,
            "weekday": next_date.weekday(),
            "is_weekend": int(next_date.weekday() >= 5),
            "lag_1": hist["daily_sales"].iloc[-1],
            "lag_7": hist["daily_sales"].iloc[-7] if len(hist) >= 7 else hist["daily_sales"].iloc[-1],
            "rolling_7": hist["daily_sales"].tail(7).mean(),
            "rolling_30": hist["daily_sales"].tail(30).mean(),
            "avg_price": hist["avg_price"].iloc[-1]
        }

        X = np.array([row[f] for f in features]).reshape(1, -1)
        Xs = scaler.transform(X)
        pred = float(model.predict(Xs)[0])

        outputs.append({"date": next_date, "predicted_sales": pred})

        hist = pd.concat([hist, pd.DataFrame([{
            "date": next_date,
            "daily_sales": pred,
            "avg_price": row["avg_price"]
        }])], ignore_index=True)

    return pd.DataFrame(outputs)

def _load_forecast_files(forecast_dir=FORECAST_DIR, pattern="forecast_*_*.csv"):
    files = glob.glob(os.path.join(forecast_dir, pattern))
    dfs = []
    for f in files:
        try:
            tmp = pd.read_csv(f, parse_dates=["date"])
            if "predicted_sales" not in tmp.columns and "pred" in tmp.columns:
                tmp = tmp.rename(columns={"pred":"predicted_sales"})
            tmp["predicted_sales"] = pd.to_numeric(tmp["predicted_sales"], errors="coerce").fillna(0)
            dfs.append(tmp)
        except Exception as e:
            print("Warning: failed to read", f, e)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def aggregate_forecasts(fcasts_df, analytics_dir=EDA_DIR):
    if fcasts_df.empty:
        print("No forecast files found to aggregate.")
        return None, None

    f = fcasts_df.copy()
    f["week_start"] = f["date"].dt.to_period("W").apply(lambda r: r.start_time)
    f["month_start"] = f["date"].dt.to_period("M").apply(lambda r: r.start_time)

    id_cols = [c for c in f.columns if c.endswith("_id")]

    weekly = f.groupby(id_cols + ["week_start"])["predicted_sales"].sum().reset_index().rename(columns={"week_start":"date","predicted_sales":"weekly_pred"})
    monthly = f.groupby(id_cols + ["month_start"])["predicted_sales"].sum().reset_index().rename(columns={"month_start":"date","predicted_sales":"monthly_pred"})

    os.makedirs(analytics_dir, exist_ok=True)
    weekly.to_csv(os.path.join(analytics_dir, "forecasts_weekly.csv"), index=False)
    monthly.to_csv(os.path.join(analytics_dir, "forecasts_monthly.csv"), index=False)
    f.to_csv(os.path.join(analytics_dir, "forecasts_daily.csv"), index=False)
    print("Saved aggregated forecasts to", analytics_dir)
    return weekly, monthly
