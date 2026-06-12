from database import SessionLocal
from database_models import Articles

db = SessionLocal()
try:
    articles = db.query(Articles).all()
    for a in articles[:5]:
        print(a.__dict__)  # shows raw columns and values
finally:
    db.close()
