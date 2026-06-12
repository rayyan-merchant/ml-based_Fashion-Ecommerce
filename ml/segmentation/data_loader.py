import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}"
    f"@127.0.0.1:{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

df = pd.read_parquet("data/ml/segmentation/customer_segments.parquet")
df["updated_at"] = datetime.utcnow()

engine = create_engine(DB_URL)

df.to_sql(
    "customer_segments",
    engine,
    schema="niche_data",
    if_exists="replace",
    index=False
)
