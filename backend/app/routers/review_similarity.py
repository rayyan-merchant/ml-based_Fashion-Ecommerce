from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import bindparam, text
from app.utils.review_similarity import review_sim
from app.db.database import get_db

encoder = None


def get_text_encoder():
    """Load the optional text encoder lazily from local cache only."""
    global encoder
    if encoder is not None:
        return encoder

    try:
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception as e:
        print(f"SentenceTransformer unavailable locally: {e}")
        encoder = None

    return encoder

router = APIRouter(prefix="/reviews", tags=["Similar Reviews"])


def get_db_similar_reviews(review_id: int, k: int, db: Session):
    """Fallback similarity for reviews that are not present in the FAISS index yet."""
    target = db.execute(text("""
        SELECT review_id, article_id, rating, sentiment_label, created_at
        FROM niche_data.reviews
        WHERE review_id = :review_id
    """), {"review_id": review_id}).mappings().first()

    if not target:
        return {"error": "review_id not found"}

    rows = db.execute(text("""
        SELECT
            r.review_id,
            r.customer_id,
            NULLIF(TRIM(CONCAT_WS(' ', c.first_name, c.last_name)), '') AS customer_name,
            r.article_id,
            r.rating,
            r.review_text,
            r.created_at,
            r.sentiment_label,
            CASE
                WHEN r.rating IS NULL THEN NULL
                ELSE r.rating::float / 5.0
            END AS sentiment_score,
            (
                CASE WHEN r.article_id = :article_id THEN 0.45 ELSE 0 END +
                CASE WHEN r.sentiment_label IS NOT DISTINCT FROM :sentiment THEN 0.25 ELSE 0 END +
                CASE
                    WHEN r.rating IS NULL OR :rating IS NULL THEN 0.10
                    ELSE GREATEST(0, 0.30 - (ABS(r.rating - :rating) * 0.075))
                END
            ) AS similarity_score
        FROM niche_data.reviews r
        LEFT JOIN niche_data.customers c ON c.customer_id = r.customer_id
        WHERE r.review_id <> :review_id
        ORDER BY similarity_score DESC, r.created_at DESC
        LIMIT :limit
    """), {
        "review_id": review_id,
        "article_id": target["article_id"],
        "sentiment": target["sentiment_label"],
        "rating": target["rating"],
        "limit": k,
    }).mappings().all()

    return [
        {
            "review_id": row["review_id"],
            "similarity": float(row["similarity_score"] or 0),
            "similarity_score": float(row["similarity_score"] or 0),
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "reviewer_name": row["customer_name"],
            "article_id": row["article_id"],
            "rating": row["rating"],
            "review_text": row["review_text"],
            "sentiment": row["sentiment_label"],
            "sentiment_score": row["sentiment_score"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]

# ------------------- Similar by review ID -------------------

@router.get("/{review_id}/similar")
def get_similar_reviews(review_id: int, k: int = 10, db: Session = Depends(get_db)):

    k = max(1, min(k, 50))
    results = review_sim.get_similar_by_id(review_id, k)
    
    # Fallback: If not found in index (e.g. new review), use text compliance
    if results is None:
        return get_db_similar_reviews(review_id, k, db)

    # Fetch full review text for display
    similar_ids = [r["similar_review_id"] for r in results]
    if not similar_ids:
        return []

    sql = text("""
        SELECT
            r.review_id,
            r.customer_id,
            NULLIF(TRIM(CONCAT_WS(' ', c.first_name, c.last_name)), '') AS customer_name,
            r.article_id,
            r.rating,
            r.review_text,
            r.created_at,
            r.sentiment_label,
            CASE
                WHEN r.rating IS NULL THEN NULL
                ELSE r.rating::float / 5.0
            END AS sentiment_score
        FROM niche_data.reviews r
        LEFT JOIN niche_data.customers c ON c.customer_id = r.customer_id
        WHERE r.review_id IN :review_ids
    """).bindparams(bindparam("review_ids", expanding=True))

    data = db.execute(sql, {"review_ids": tuple(similar_ids)}).mappings().all()
    review_dict = {row["review_id"]: dict(row) for row in data}

    # Combine similarity score + review content
    enriched = []
    for r in results:
        rid = r["similar_review_id"]
        # Handle case where similar review might be missing from DB (rare consistency issue)
        if rid in review_dict:
            enriched.append({
                "review_id": rid,
                "similarity": r["score"],
                "similarity_score": r["score"],
                "customer_id": review_dict[rid]["customer_id"],
                "customer_name": review_dict[rid]["customer_name"],
                "reviewer_name": review_dict[rid]["customer_name"],
                "article_id": review_dict[rid]["article_id"],
                "rating": review_dict[rid]["rating"],
                "review_text": review_dict[rid]["review_text"],
                "sentiment": review_dict[rid]["sentiment_label"],
                "sentiment_score": review_dict[rid]["sentiment_score"],
                "created_at": review_dict[rid]["created_at"]
            })

    return enriched

# ------------------- Similar for new input text -------------------

@router.post("/similar-text")
def similar_text(payload: dict, k: int = 10):
    text = payload.get("text")
    if not text:
        return {"error": "text is required"}

    model = get_text_encoder()
    if model is None:
        return {"error": "Text similarity model is unavailable (transformers missing)"}

    results = review_sim.get_similar_by_text(text, model, k)
    return results
