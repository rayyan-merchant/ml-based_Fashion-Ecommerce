
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rayyan123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fashion_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Setup hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_all_passwords(new_password="layr123"):
    print(f"Resetting all customer passwords to: '{new_password}'...")
    
    # create engine
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Hash password
            hashed = pwd_context.hash(new_password)
            
            # Update all customers
            sql = text("UPDATE niche_data.customers SET password_hash = :p_hash")
            result = conn.execute(sql, {"p_hash": hashed})
            conn.commit()
            
            print(f"Successfully updated passwords for {result.rowcount} customers.")
            
    except Exception as e:
        print(f"Error updating passwords: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        new_pass = sys.argv[1]
    else:
        new_pass = "layr123"
        
    reset_all_passwords(new_pass)
