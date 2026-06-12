"""model_xgb_articles.py
Train XGBoost per-article models (top-K) and persist models/scalers/forecasts.
"""
import os
import joblib
import numpy as np

from sklearn.preprocessing import StandardScaler
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
    rmse, mape = evaluate(y_val, pred)

    return model, scaler, rmse, mape

def train_article_models(df, top_k=100):
    import pandas as pd
    print(f"Training XGBoost for top {top_k} articles...")

    top_articles = df.groupby("article_id")["daily_sales"].sum().nlargest(top_k).index.tolist()
    article_results = []

    for aid in top_articles:
        print(f"→ Article {aid}")
        s = df[df["article_id"] == aid]
        s_feat = build_features(s)
        train_df, val_df = train_val_split(s_feat)

        if len(train_df) < 60 or len(val_df) < 7:
            print("Skipping — insufficient data.")
            continue

        model, scaler, rmse, mape = train_xgb(train_df, val_df, FEATURES)
        print(f"RMSE={rmse:.3f}, MAPE={mape:.3f}")

        joblib.dump(model, os.path.join(MODELS_DIR, f"xgb_article_{aid}.pkl"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, f"xgb_article_{aid}_scaler.pkl"))

        # Forecast using the last 30 days of history
        from forecasting_utils import recursive_forecast
        fcast = recursive_forecast(model, scaler, s_feat.tail(30), days=30, features=FEATURES)
        fcast["article_id"] = aid
        fcast.to_csv(os.path.join(FORECAST_DIR, f"forecast_article_{aid}.csv"), index=False)

        article_results.append({"article_id": aid, "rmse": rmse, "mape": mape})

    import pandas as pd
    pd.DataFrame(article_results).to_csv(os.path.join(EVALS_DIR, "top_articles_evals.csv"), index=False)
    print("Article training complete.")
