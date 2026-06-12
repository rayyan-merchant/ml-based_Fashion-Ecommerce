from app.core.auth import hash_password
from app.db.database import SessionLocal
from datetime import datetime
from sqlalchemy import text

# ----------- CONFIG ------------
USERNAME = "rija"
EMAIL = "rija@gmail.com"
PASSWORD = "rija1234"
# --------------------------------

db = SessionLocal()

try:
    print("Creating clean admin...")

    hashed_pw = hash_password(PASSWORD)

    sql = text("""
        INSERT INTO niche_data.admins (username, email, password_hash, created_at, is_active)
        VALUES (:u, :e, :p, NOW(), true)
        RETURNING admin_id
    """)

    row = db.execute(sql, {"u": USERNAME, "e": EMAIL, "p": hashed_pw}).mappings().first()
    db.commit()

    print(f"SUCCESS! Admin created with ID = {row['admin_id']}")
    print("Use these credentials in Swagger:")
    print(f"Username: {USERNAME}")
    print(f"Password: {PASSWORD}")

except Exception as e:
    db.rollback()
    print("ERROR:", e)

finally:
    db.close()
