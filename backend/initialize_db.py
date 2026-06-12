from app.db.database import engine, Base, metadata
from app.db.models import (
    admins, articles, cart, categories, customers, events, 
    order_items, orders, reviews, segmentation, transactions, wishlist
)

print("Creating database tables...")
try:
    # Ensure schema exists (Postgres specific)
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS niche_data"))
        connection.commit()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")
except Exception as e:
    print(f"❌ Error creating tables: {e}")
