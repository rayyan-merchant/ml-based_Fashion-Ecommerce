import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine("postgresql://postgres:rija123@localhost:5432/fashion_db")
engine = sa.create_engine("postgresql://postgres:rayyan123@localhost:5432/fashion_db")

df = pd.read_sql("SELECT article_id FROM niche_data.articles", engine)
df.to_csv("article_ids.csv", index=False)
