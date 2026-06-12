import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:1234@localhost:5432/FashionDb")
query = """
SELECT 
    customer_id,
    views,
    clicks,
    buys,
    carts,
    wishlist
FROM events;
"""

df = pd.read_sql(query, engine)
print(df.head())

