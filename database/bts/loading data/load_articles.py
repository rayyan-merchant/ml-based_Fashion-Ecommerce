import pandas as pd
from sqlalchemy import create_engine, text

# PostgreSQL connection
engine = create_engine("postgresql+psycopg2://postgres:rayyan123@localhost:5432/fashion_db")

# Path to your dataset
base_path = "data/hm/"
file_path = base_path + "articles.csv"

# Columns to load
selected_cols = [
    "article_id",
    "product_code",
    "prod_name",
    "product_type_name",
    "product_group_name",
    "graphical_appearance_name",
    "colour_group_name",
    "department_no",
    "department_name",
    "index_name",
    "index_group_name",
    "section_name",
    "garment_group_name",
    "detail_desc"
]

print("🔄 Starting upload of articles...")

# Load and upload in chunks (large file handling)
chunksize = 50000
for i, chunk in enumerate(pd.read_csv(file_path, usecols=selected_cols, chunksize=chunksize)):
    print(f"Processing chunk {i+1}...")

    # Clean and transform data
    chunk["article_id"] = chunk["article_id"].astype(str)
    chunk["product_code"] = pd.to_numeric(chunk["product_code"], errors="coerce")
    chunk["department_no"] = pd.to_numeric(chunk["department_no"], errors="coerce")
    
    # Optional: remove duplicates if article_id already exists
    chunk.drop_duplicates(subset=["article_id"], inplace=True)

    # Upload to PostgreSQL
    chunk.to_sql("articles", engine, if_exists="append", index=False)
    print(f"✅ Uploaded chunk {i+1}")

print("🎉 All article data successfully uploaded!")
