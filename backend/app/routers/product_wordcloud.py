from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from app.utils.wordcloud_generator import wordcloud_gen

router = APIRouter(prefix="/products", tags=["Wordcloud"])

# ----------------- Wordcloud as image file -----------------

@router.get("/{product_id}/wordcloud")
def product_wordcloud(product_id: str):
    filepath = wordcloud_gen.generate_for_product(product_id)

    if filepath is None:
        return JSONResponse({"error": "No reviews found for this product"}, status_code=404)

    return FileResponse(filepath, media_type="image/png")


# ----------------- Wordcloud as base64 (good for React/Flutter) -----------------

@router.get("/{product_id}/wordcloud/base64")
def product_wordcloud_base64(product_id: str):
    img_b64 = wordcloud_gen.generate_base64(product_id)

    if img_b64 is None:
        return {"error": "No reviews found for this product"}

    return {
        "product_id": product_id,
        "wordcloud": img_b64
    }
