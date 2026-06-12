import joblib
import numpy as np
import pandas as pd
import os

BASE_PATH = os.path.join(os.path.dirname(__file__), "tuning")


# -------------------------------------------
# Load Model + Scaler
# -------------------------------------------

def load_artifacts():
    model_path = os.path.join(BASE_PATH, "final_gmm_model.pkl")
    scaler_path = os.path.join(BASE_PATH, "final_scaler.pkl")
    profiles_path = os.path.join(BASE_PATH, "segment_profiles.csv")

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # Optional: segment interpretation
    profiles = None
    if os.path.exists(profiles_path):
        profiles = pd.read_csv(profiles_path)

    print("✓ Loaded GMM model")
    print("✓ Loaded scaler")

    return model, scaler, profiles


# -------------------------------------------
# Predict function
# -------------------------------------------

def predict_segment(model, scaler, vector):
    """
    vector: [total_spend, order_count, avg_order_value, recency_days, ...]
    """
    x = np.array(vector).reshape(1, -1)
    x_scaled = scaler.transform(x)

    label = model.predict(x_scaled)[0]
    probabilities = model.predict_proba(x_scaled)[0]

    return label, probabilities


# -------------------------------------------
# Run a full demo
# -------------------------------------------

def run_demo():
    print("\n========== CUSTOMER SEGMENTATION DEMO ==========\n")

    model, scaler, profiles = load_artifacts()

    # Example customer - modify as needed
    customer_vector = [15000, 12, 950, 18]  
    print(f"Input vector: {customer_vector}")

    label, probs = predict_segment(model, scaler, customer_vector)

    print("\n--- Prediction Output ---")
    print(f"Predicted Segment: {label}")
    print("Probabilities per segment:")
    for i, p in enumerate(probs):
        print(f"  Segment {i}: {p:.4f}")

    if profiles is not None:
        print("\n--- Segment Description ---")
        row = profiles[profiles["segment"] == label]
        if len(row) > 0:
            print(row.to_string(index=False))
        else:
            print("No profile found.")

    print("\n=================================================\n")


if __name__ == "_main_":
    run_demo()