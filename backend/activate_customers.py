
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rayyan123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fashion_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def activate_all_customers():
    print("Activating all customers...")
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Set active = True for ALL customers
            sql = text("UPDATE niche_data.customers SET active = true")
            result = conn.execute(sql)
            conn.commit()
            
            print(f"Successfully activated {result.rowcount} customers.")
            
    except Exception as e:
        print(f"Error activating customers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    activate_all_customers()
