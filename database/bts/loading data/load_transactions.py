import pandas as pd
from sqlalchemy import create_engine

# PostgreSQL connection
engine = create_engine("postgresql+psycopg2://postgres:rayyan123@localhost:5432/fashion_db")

# File path
base_path = "data/hm/"
file_path = base_path + "transactions_train.csv"

# Load in chunks
chunksize = 100000  # Adjust as needed (try 50,000 if low memory)

print("Uploading transactions table...")

# Iterate over chunks
for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunksize)):
    # Keep only necessary columns (ignore extra ones)
    expected_columns = ["t_dat", "customer_id", "article_id", "price", "sales_channel_id"]
    chunk = chunk[[c for c in expected_columns if c in chunk.columns]]

    # Convert date properly
    chunk["t_dat"] = pd.to_datetime(chunk["t_dat"], errors="coerce")

    # Remove rows with missing required fields (optional)
    chunk.dropna(subset=["customer_id", "article_id"], inplace=True)

    # Upload to PostgreSQL
    chunk.to_sql("transactions", engine, if_exists="append", index=False)
    print(f"✅ Chunk {i+1} uploaded ({len(chunk)} rows)")

print("🎉 All transactions uploaded successfully!")
