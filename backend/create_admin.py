import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from sqlalchemy import text
from passlib.hash import bcrypt

def create_admin():
    # Get username and password from command line arguments
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        return
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    # Hash the password using bcrypt (same as the backend)
    hashed_password = bcrypt.hash(password)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing = db.execute(
            text("SELECT 1 FROM niche_data.admins WHERE username = :u"),
            {"u": username}
        ).scalar()
        
        if existing:
            print(f"Admin '{username}' already exists")
            return
        
        # Insert new admin
        db.execute(
            text("""
                INSERT INTO niche_data.admins (username, email, password_hash, created_at, is_active)
                VALUES (:u, :e, :ph, NOW(), TRUE)
            """),
            {
                "u": username,
                "e": f"{username}@example.com",
                "ph": hashed_password
            }
        )
        db.commit()
        print(f"Admin '{username}' created successfully")
        
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()