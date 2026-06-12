from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import bindparam, text
from app.utils.product_similarity import product_sim
from app.db.database import get_db

router = APIRouter(prefix="/products", tags=["Similar Products"])

# ------------------- Similar Products by ID -------------------

@router.get("/{product_id}/similar")
def get_similar_products(product_id: str, k: int = 10, db: Session = Depends(get_db)):

    k = max(1, min(k, 50))
    results = product_sim.get_similar_by_id(product_id, k)

    if results is None:
        return {"error": "product_id not found"}

    similar_ids = [r["product_id"] for r in results]
    if not similar_ids:
        return {"products": []}

    sql = text("""
        SELECT article_id, prod_name, category_id, product_group_name, product_type_name,
               colour_group_name, price, stock, image_path, detail_desc
        FROM niche_data.articles
        WHERE article_id IN :article_ids
    """).bindparams(bindparam("article_ids", expanding=True))

    rows = db.execute(sql, {"article_ids": tuple(similar_ids)}).mappings().all()
    product_info = {row["article_id"]: dict(row) for row in rows}

    enriched = []
    for r in results:
        pid = r["product_id"]
        product = product_info.get(pid)
        if product:
            enriched.append({
                **product,
                "similarity": r["similarity"],
                "similarity_score": r["similarity"],
            })

    return {"products": enriched, "source_product_id": product_id}

