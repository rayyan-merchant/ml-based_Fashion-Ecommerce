"""clean_reindex.py
Contains the reindexing / cleaning utilities for time series.
"""
import pandas as pd
import numpy as np


def clean_and_reindex(df, id_col="article_id"):
    clean_series = []
    eda_list = []

    for key, g in df.groupby(id_col):
        g = g.sort_values("date")
        start, end = g["date"].min(), g["date"].max()
        full_index = pd.date_range(start, end, freq="D")

        g2 = g.set_index("date").reindex(full_index).rename_axis("date").reset_index()
        g2[id_col] = key

        g2["daily_sales"] = g2["daily_sales"].fillna(0)
        g2["avg_price"] = g2["avg_price"].ffill().bfill()
        g2["avg_price"] = g2["avg_price"].ffill().bfill()
        if g2["avg_price"].isna().all():
            g2["avg_price"] = 0

        g2["daily_revenue"] = g2["daily_revenue"].fillna(g2["daily_sales"] * g2["avg_price"])

        clean_series.append(g2)

        eda_list.append({
            id_col: key,
            "start": start,
            "end": end,
            "days": len(g2),
            "missing_days": len(full_index) - len(g),
            "zero_sales_ratio": (g2["daily_sales"] == 0).mean()
        })

    if not clean_series:
        return pd.DataFrame(), pd.DataFrame()

    return pd.concat(clean_series).reset_index(drop=True), pd.DataFrame(eda_list)
