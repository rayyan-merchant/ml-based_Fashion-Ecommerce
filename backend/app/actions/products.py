from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.articles import Article


# -------------------------------------------------------------
# CRUD — if needed
# -------------------------------------------------------------
def get_article_by_id(article_id: int, db: Session):
    return db.query(Article).filter(Article.article_id == article_id).first()


def get_articles_by_name(prod_name: str, db: Session):
    return db.query(Article).filter(Article.prod_name == prod_name).all()


# -------------------------------------------------------------
# ANALYTICS — PERFORMANCE VIEW
# -------------------------------------------------------------
def get_article_performance(article_id: int, db: Session):
    sql = text("""
        SELECT * 
        FROM niche_data.product_performance 
        WHERE article_id = :article_id
    """)
    result = db.execute(sql, {"article_id": article_id}).mappings().first()
    return result


# -------------------------------------------------------------
# ANALYTICS — DEMAND TREND VIEW (MATERIALIZED)
# -------------------------------------------------------------
def get_demand_trend(article_id: int, db: Session):
    sql = text("""
        SELECT * 
        FROM niche_data.mv_product_demand 
        WHERE article_id = :article_id
        
    """)
    result = db.execute(sql, {"article_id": article_id}).mappings().all()
    return result


# -------------------------------------------------------------
# ANALYTICS — INVENTORY STATUS VIEW
# -------------------------------------------------------------
def get_inventory_status(article_id: int, db: Session):
    sql = text("""
        SELECT * 
        FROM niche_data.v_article_inventory 
        WHERE article_id = :article_id
    """)
    return db.execute(sql, {"article_id": article_id}).mappings().first()


# -------------------------------------------------------------
# ANALYTICS — FUNNEL METRICS VIEW (MATERIALIZED)
# -------------------------------------------------------------
def get_funnel_metrics(db: Session):
    sql = text("SELECT * FROM niche_data.funnel_metrics LIMIT 1")
    result = db.execute(sql).mappings().first()
    return result
