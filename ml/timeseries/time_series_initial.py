"""
timeseries_initial.py
------------------------------------
Initial experiment file to compare ARIMA, LSTM and XGBoost
for time-series forecasting.

Now includes forecast graphs:
 - ARIMA Forecast
 - LSTM Forecast
 - XGBoost Forecast
 - Combined Comparison Plot
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from math import sqrt

# ---------------------------------------------
# Create output directory for graphs
# ---------------------------------------------
PLOT_DIR = "plots/timeseries_initial"
os.makedirs(PLOT_DIR, exist_ok=True)

# ---------------------------------------------
# Load data
# ---------------------------------------------
df = pd.read_csv("data/ml/timeseries/clean_daily_sales.csv")

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['article_id', 'date'])

article_id = df['article_id'].iloc[0]
ts = df[df['article_id'] == article_id].reset_index(drop=True)

train = ts.iloc[:-28]
test = ts.iloc[-28:]

y_train = train['daily_sales'].values
y_test = test['daily_sales'].values

dates_test = test['date'].values

# ============================================================
# 1️⃣ ARIMA MODEL
# ============================================================
from statsmodels.tsa.arima.model import ARIMA

print("Training ARIMA...")

def train_arima(train_series):
    model = ARIMA(train_series, order=(1, 1, 1))
    model_fit = model.fit()
    return model_fit.forecast(steps=28)

arima_preds = train_arima(y_train)
arima_rmse = sqrt(mean_squared_error(y_test, arima_preds))

# ARIMA plot
plt.figure(figsize=(10, 5))
plt.plot(train['date'], y_train, label="Train")
plt.plot(test['date'], y_test, label="Actual")
plt.plot(test['date'], arima_preds, label="ARIMA Forecast")
plt.title("ARIMA Forecast")
plt.legend()
plt.savefig(f"{PLOT_DIR}/arima_forecast.png", dpi=300)
plt.close()

# ============================================================
# 2️⃣ LSTM MODEL
# ============================================================
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

print("Training LSTM...")

def create_sequences(data, window=14):
    X, y = [], []
    for i in range(len(data) - window):
        X.append(data[i:i+window])
        y.append(data[i+window])
    return np.array(X), np.array(y)

scaler = MinMaxScaler()
scaled = scaler.fit_transform(y_train.reshape(-1, 1)).flatten()

window = 14
X_train_seq, y_train_seq = create_sequences(scaled, window)
X_train_seq = X_train_seq.reshape((X_train_seq.shape[0], X_train_seq.shape[1], 1))

lstm_model = Sequential([
    LSTM(64, activation='tanh', return_sequences=False, input_shape=(window, 1)),
    Dense(1)
])

lstm_model.compile(optimizer='adam', loss='mse')
lstm_model.fit(X_train_seq, y_train_seq, epochs=20, batch_size=16, verbose=0)

# Generate 28-day forecast
last_window = scaled[-window:]
lstm_scaled_preds = []
current_input = last_window.copy()

for _ in range(28):
    inp = current_input.reshape((1, window, 1))
    pred = lstm_model.predict(inp, verbose=0)[0][0]
    lstm_scaled_preds.append(pred)
    current_input = np.append(current_input[1:], pred)

lstm_preds = scaler.inverse_transform(np.array(lstm_scaled_preds).reshape(-1, 1)).flatten()
lstm_rmse = sqrt(mean_squared_error(y_test, lstm_preds))

# LSTM plot
plt.figure(figsize=(10, 5))
plt.plot(train['date'], y_train, label="Train")
plt.plot(test['date'], y_test, label="Actual")
plt.plot(test['date'], lstm_preds, label="LSTM Forecast")
plt.title("LSTM Forecast")
plt.legend()
plt.savefig(f"{PLOT_DIR}/lstm_forecast.png", dpi=300)
plt.close()

# ============================================================
# 3️⃣ XGBOOST MODEL
# ============================================================
from xgboost import XGBRegressor

print("Training XGBoost...")

def create_xgb_features(df):
    df = df.copy()
    df['lag_1'] = df['daily_sales'].shift(1)
    df['lag_7'] = df['daily_sales'].shift(7)
    df['lag_14'] = df['daily_sales'].shift(14)
    df['rolling_7'] = df['daily_sales'].rolling(7).mean()
    df['rolling_14'] = df['daily_sales'].rolling(14).mean()
    return df.dropna()

ts_feat = create_xgb_features(ts)

train_feat = ts_feat.iloc[:-28]
test_feat = ts_feat.iloc[-28:]

X_train_xgb = train_feat[['lag_1', 'lag_7', 'lag_14', 'rolling_7', 'rolling_14']]
y_train_xgb = train_feat['daily_sales']

X_test_xgb = test_feat[['lag_1', 'lag_7', 'lag_14', 'rolling_7', 'rolling_14']]
y_test_xgb = test_feat['daily_sales']

xgb_model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='reg:squarederror'
)

xgb_model.fit(X_train_xgb, y_train_xgb)
xgb_preds = xgb_model.predict(X_test_xgb)
xgb_rmse = sqrt(mean_squared_error(y_test_xgb, xgb_preds))

# XGBoost plot
plt.figure(figsize=(10, 5))
plt.plot(train_feat['date'], train_feat['daily_sales'], label="Train")
plt.plot(test_feat['date'], y_test_xgb, label="Actual")
plt.plot(test_feat['date'], xgb_preds, label="XGBoost Forecast")
plt.title("XGBoost Forecast")
plt.legend()
plt.savefig(f"{PLOT_DIR}/xgboost_forecast.png", dpi=300)
plt.close()

# ============================================================
# 📊 Combined Comparison Plot
# ============================================================

plt.figure(figsize=(12, 6))
plt.plot(test['date'], y_test, label="Actual", linewidth=2)
plt.plot(test['date'], arima_preds, label="ARIMA", linestyle='--')
plt.plot(test['date'], lstm_preds, label="LSTM", linestyle='--')
plt.plot(test['date'], xgb_preds, label="XGBoost", linestyle='--')
plt.title("Model Comparison: Actual vs Forecasts")
plt.legend()
plt.savefig(f"{PLOT_DIR}/comparison_all_models.png", dpi=300)
plt.close()

# ============================================================
# Results
# ============================================================

print("\n==================== MODEL COMPARISON ====================")
print(f"ARIMA RMSE   : {arima_rmse:.4f}")
print(f"LSTM RMSE    : {lstm_rmse:.4f}")
print(f"XGBoost RMSE : {xgb_rmse:.4f}")
print("==========================================================")

best = min([("ARIMA", arima_rmse), ("LSTM", lstm_rmse), ("XGBOOST", xgb_rmse)], key=lambda x: x[1])
print(f"\nBEST MODEL → {best[0]}")

print(f"\nGraphs saved in: {PLOT_DIR}/")