"""model_xgb_categories.py
Train XGBoost aggregated at category level.
"""
import os
import joblib

from features import build_features, train_val_split, evaluate

OUT_BASE = "data/ml/timeseries/final_xgb"
MODELS_DIR = os.path.join(OUT_BASE, "models")
FORECAST_DIR = os.path.join(OUT_BASE, "forecasts")
EVALS_DIR = os.path.join(OUT_BASE, "evals")

for d in [MODELS_DIR, FORECAST_DIR, EVALS_DIR]:
    os.makedirs(d, exist_ok=True)

FEATURES = ["day","month","year","weekday","is_weekend","lag_1","lag_7","rolling_7","rolling_30","avg_price"]

def train_xgb(train_df, val_df, features):
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error

    X_train = train_df[features].values
    y_train = train_df["daily_sales"].values
    X_val = val_df[features].values
    y_val = val_df["daily_sales"].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)

    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        colsample_bytree=0.9,
        subsample=0.9,
        verbosity=0
    )

    model.fit(X_train_s, y_train)
    pred = model.predict(X_val_s)
    try:
        rmse = float(mean_squared_error(y_val, pred))
    except Exception:
        rmse = None
    try:
        mape = float(mean_absolute_percentage_error(y_val, pred))
    except Exception:
        mape = None

    return model, scaler, rmse, mape

def train_category_models(df):
    import pandas as pd
    print("Training XGBoost for all categories...")

    category_results = []

    for cid in sorted(df["category_id"].unique()):
        print(f"→ Category {cid}")

        s = df[df["category_id"] == cid].groupby("date", as_index=False).agg({
            "daily_sales": "sum",
            "avg_price": "mean"
        })

        s_feat = build_features(s)
        train_df, val_df = train_val_split(s_feat)

        if len(train_df) < 60 or len(val_df) < 7:
            print("Skipping — insufficient data.")
            continue

        model, scaler, rmse, mape = train_xgb(train_df, val_df, FEATURES)
        print(f"RMSE={rmse:.3f}, MAPE={mape:.3f}")

        joblib.dump(model, os.path.join(MODELS_DIR, f"xgb_category_{cid}.pkl"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, f"xgb_category_{cid}_scaler.pkl"))

        from forecasting_utils import recursive_forecast
        fcast = recursive_forecast(model, scaler, s_feat.tail(30), days=30, features=FEATURES)
        fcast["category_id"] = cid
        fcast.to_csv(os.path.join(FORECAST_DIR, f"forecast_category_{cid}.csv"), index=False)

        category_results.append({"category_id": cid, "rmse": rmse, "mape": mape})

    import pandas as pd
    pd.DataFrame(category_results).to_csv(os.path.join(EVALS_DIR, "category_evals.csv"), index=False)
    print("Category training complete.")
