import pandas as pd
from sqlalchemy import create_engine

# ---------------------------
# PostgreSQL connection setup
# ---------------------------
engine = create_engine("postgresql+psycopg2://postgres:rayyan123@localhost:5432/fashion_db")

# ---------------------------
# Load and clean customer data
# ---------------------------
base_path = "data/hm/"
customers = pd.read_csv(base_path + "customers.csv")

# Drop unwanted columns if they exist
cols_to_drop = ["FN"]
customers = customers.drop(columns=[c for c in cols_to_drop if c in customers.columns])

# Rename columns
if 'Active' in customers.columns:
    customers.rename(columns={'Active': 'active'}, inplace=True)

# Convert numeric active column → boolean
if 'active' in customers.columns:
    customers['active'] = customers['active'].apply(lambda x: True if x == 1 or x == 1.0 else False if x == 0 or x == 0.0 else None)

# ✅ Keep only the relevant columns
expected_columns = ["customer_id", "active", "age", "postal_code", "club_member_status", "fashion_news_frequency"]
customers = customers[[c for c in expected_columns if c in customers.columns]]

# ---------------------------
# Upload to PostgreSQL
# ---------------------------
print("Uploading customers table...")
customers.to_sql("customers", engine, if_exists="append", index=False)
print("✅ Customers table uploaded successfully!")
