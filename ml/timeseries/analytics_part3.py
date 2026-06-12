"""analytics_part3.py
Part 3 analytics: revenue forecast, stockout risk, trend classification, lifecycle assignment and funnel.
"""
import os
import numpy as np
import pandas as pd

OUT_BASE = "data/ml/timeseries/final_xgb"
EDA_DIR = os.path.join(OUT_BASE, "eda")
os.makedirs(EDA_DIR, exist_ok=True)

def safe_mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))

def compute_revenue_forecast(all_fc, df):
    all_fc = all_fc.copy()
    all_fc["article_id"] = all_fc["article_id"].astype(str)
    df = df.copy()
    df["article_id"] = df["article_id"].astype(str)

    price_map = df[["article_id", "avg_price"]].dropna(subset=["avg_price"]).drop_duplicates(subset=["article_id"])
    merged = all_fc.merge(price_map, on="article_id", how="left")
    if merged["avg_price"].isna().sum() > 0:
        merged["avg_price"] = merged["avg_price"].fillna(df["avg_price"].mean())

    pred_col = "predicted_sales" if "predicted_sales" in merged.columns else "y_pred"
    merged["predicted_revenue"] = merged[pred_col] * merged["avg_price"]
    merged.to_csv(os.path.join(EDA_DIR, "revenue_forecast_daily.csv"), index=False)
    print("Revenue forecast saved to", EDA_DIR)
    return merged

def compute_stockout_risk(all_fc, threshold=0.60):
    stockout_list = []
    for aid, g in all_fc.groupby("article_id"):
        if len(g) < 7:
            continue
        first = g['predicted_sales'].iloc[0]
        last = g['predicted_sales'].iloc[-1]
        if first > 0 and (last / first) < threshold:
            stockout_list.append({
                "article_id": aid,
                "first_day_sales": first,
                "last_day_sales": last,
                "drop_ratio": last / first
            })
    stock_df = pd.DataFrame(stockout_list)
    stock_df.to_csv(os.path.join(EDA_DIR, "stockout_risk_articles.csv"), index=False)
    return stock_df

def classify_trend(fcast_df):
    results = []
    for aid, g in fcast_df.groupby("article_id"):
        g = g.sort_values("date")
        slope = (g['predicted_sales'].iloc[-1] - g['predicted_sales'].iloc[0]) / max(len(g), 1)
        if slope > 0.3:
            trend = "Rising"
        elif slope < -0.3:
            trend = "Declining"
        else:
            trend = "Stable"
        results.append({"article_id": aid, "trend": trend, "slope": slope})
    trend_df = pd.DataFrame(results)
    trend_df.to_csv(os.path.join(EDA_DIR, "trend_classification.csv"), index=False)
    return trend_df

def compute_monthly_growth_rate(fcast_df):
    fcast_df = fcast_df.copy()
    fcast_df['month'] = fcast_df['date'].dt.to_period("M")
    monthly = fcast_df.groupby("month")['predicted_sales'].sum().reset_index()
    monthly['growth_rate'] = monthly['predicted_sales'].pct_change().fillna(0)
    monthly.to_csv(os.path.join(EDA_DIR, "monthly_growth_rate.csv"), index=False)
    return monthly

def assign_product_lifecycle(all_fc):
    results = []
    for aid, g in all_fc.groupby("article_id"):
        g = g.sort_values("date")
        slope = (g['predicted_sales'].iloc[-1] - g['predicted_sales'].iloc[0]) / max(len(g), 1)
        avg_sales = g['predicted_sales'].mean()
        if avg_sales < 2 and slope > 0.3:
            stage = "Launch"
        elif slope > 0.3:
            stage = "Growth"
        elif abs(slope) <= 0.3 and avg_sales >= 5:
            stage = "Mature"
        else:
            stage = "Decline"
        results.append({
            "article_id": aid,
            "avg_sales": avg_sales,
            "slope": slope,
            "lifecycle_stage": stage
        })
    life_df = pd.DataFrame(results)
    life_df.to_csv(os.path.join(EDA_DIR, "lifecycle_stage.csv"), index=False)
    return life_df

def compute_sales_funnel(engine, analytics_dir=EDA_DIR, table_hints=None):
    """
    Compute funnel metrics for articles:
      views → clicks → cart → wishlist → buys
    Uses 'customer_id' as user identifier and 'created_at' as event timestamp.
    Reads in chunks to avoid memory issues on large tables.
    """
    table_hints = table_hints or ["niche_data.events", "events"]
    found = None
    for t in table_hints:
        try:
            sample = pd.read_sql(f"SELECT * FROM {t} LIMIT 1", engine)
            found = t
            break
        except Exception:
            continue
    if not found:
        print("No events table found (checked hints). Funnel analysis skipped.")
        return None

    print("Using events table:", found)

    q = f"""
    SELECT customer_id AS user_id,
           article_id,
           event_type,
           created_at::date AS event_date
    FROM {found}
    """
    try:
        # Use chunksize for large tables
        chunks = pd.read_sql(q, engine, chunksize=500)
        events = pd.concat(chunks, ignore_index=True)
    except Exception as e:
        print("Failed to read events table:", e)
        return None

    events["event_type"] = events["event_type"].str.lower()
    pivot = events.pivot_table(
        index="article_id",
        columns="event_type",
        values="user_id",
        aggfunc="nunique",
        fill_value=0
    )
    pivot.columns = [str(c).lower() for c in pivot.columns]

    views = pivot.get("view", pivot.get("views", pd.Series(0)))
    clicks = pivot.get("click", pivot.get("clicks", pd.Series(0)))
    cart = pivot.get("add_to_cart", pd.Series(0))
    wishlist = pivot.get("wishlist", pd.Series(0))
    purchase = pivot.get("purchase", pivot.get("purchase", pd.Series(0)))

    funnel = pd.DataFrame({
        "views": views,
        "clicks": clicks,
        "cart": cart,
        "wishlist": wishlist,
        "purchase": purchase
    }).fillna(0).astype(float)

    funnel["click_rate"] = funnel["clicks"] / funnel["views"].replace(0, pd.NA)
    funnel["cart_rate"] = funnel["cart"] / funnel["clicks"].replace(0, pd.NA)
    funnel["purchase_rate"] = funnel["purchase"] / funnel["cart"].replace(0, pd.NA)
    funnel = funnel.fillna(0)

    os.makedirs(analytics_dir, exist_ok=True)
    funnel.to_csv(os.path.join(analytics_dir, "funnel_by_article.csv"))
    print("Saved funnel metrics to", analytics_dir)

    return funnel
