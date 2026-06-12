from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.sentiment_loader import sentiment_models
from app.db.database import get_db

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

# ------------------- Predict sentiment -------------------

@router.post("/predict")
def predict_sentiment(payload: dict):
    text = payload.get("text")
    if not text:
        return {"error": "text is required"}

    # Get predictions from all available joblib models
    predictions = sentiment_models.predict_all(text)

    return {
        "bert_prediction": {"label": "unavailable", "scores": {}},  # Placeholder since BERT is disabled
        "tfidf_predictions": {
            "lr": predictions.get("lr", {}).get("label"),
            "svm": predictions.get("svm", {}).get("label"),
            "nb": predictions.get("nb", {}).get("label"),
            "ensemble": predictions.get("ensemble", {}).get("label")
        },
        "details": predictions
    }

# ------------------- Product sentiment summary -------------------

@router.get("/product/{product_id}/summary")
def sentiment_summary(product_id: str, db: Session = Depends(get_db)):

    sql = f"""
        SELECT sentiment_label 
        FROM niche_data.reviews 
        WHERE article_id = '{product_id}'
    """
    df = db.execute(text(sql)).fetchall()

    if not df:
        return {"message": "No reviews found"}

    labels = [row[0] for row in df]

    total = len(labels)
    pos = labels.count("positive")
    neu = labels.count("neutral")
    neg = labels.count("negative")

    return {
        "product_id": product_id,
        "total_reviews": total,
        "positive": round(pos/total*100, 2),
        "neutral": round(neu/total*100, 2),
        "negative": round(neg/total*100, 2)
    }

# ------------------- Sentiment histogram (chart) -------------------

@router.get("/product/{product_id}/distribution")
def sentiment_distribution(product_id: str, db: Session = Depends(get_db)):
    sql = f"""
        SELECT sentiment_score 
        FROM niche_data.reviews 
        WHERE article_id = '{product_id}'
    """
    df = db.execute(text(sql)).fetchall()

    scores = [float(row[0]) for row in df]

    return {
        "product_id": product_id,
        "scores": scores  # frontend will convert to histogram
    }

# ------------------- Reviews sorted by sentiment -------------------

@router.get("/product/{product_id}/reviews")
def sentiment_sorted_reviews(
    product_id: str,
    order: str = "positive",
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):

    if order == "positive":
        sort = "r.rating DESC NULLS LAST, r.created_at DESC"
    elif order == "negative":
        sort = "r.rating ASC NULLS LAST, r.created_at DESC"
    elif order == "neutral":
        sort = "ABS(COALESCE(r.rating, 3) - 3) ASC, r.created_at DESC"
    else:
        sort = "r.created_at DESC"

    limit = max(1, min(limit, 200))
    skip = max(0, skip)

    sql = text(f"""
        SELECT
            r.review_id,
            r.customer_id,
            r.article_id,
            r.rating,
            r.review_text,
            r.created_at,
            NULLIF(TRIM(CONCAT_WS(' ', c.first_name, c.last_name)), '') AS reviewer_name,
            NULLIF(TRIM(CONCAT_WS(' ', c.first_name, c.last_name)), '') AS customer_name,
            r.sentiment_label AS sentiment,
            CASE
                WHEN r.rating IS NULL THEN NULL
                ELSE r.rating::float / 5.0
            END AS sentiment_score
        FROM niche_data.reviews r
        LEFT JOIN niche_data.customers c ON c.customer_id = r.customer_id
        WHERE r.article_id = :product_id
        ORDER BY {sort}
        LIMIT :limit OFFSET :skip
    """)

    rows = db.execute(sql, {
        "product_id": product_id,
        "limit": limit,
        "skip": skip,
    }).mappings().all()

    return {"reviews": [dict(r) for r in rows], "skip": skip, "limit": limit}
