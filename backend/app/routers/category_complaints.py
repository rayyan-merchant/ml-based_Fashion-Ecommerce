from fastapi import APIRouter
from app.utils.complaint_extractor import complaint_extractor

router = APIRouter(prefix="/categories", tags=["Top Complaints"])

@router.get("/{category_id}/top-complaints")
def top_complaints(category_id: int, top_n: int = 15):

    data = complaint_extractor.get_top_complaints(category_id, top_n)

    if data is None:
        return {"error": "Category not found or has no reviews"}
    
    complaints, examples = data

    return {
        "category_id": category_id,
        "top_complaints": complaints,
        "example_reviews": examples
    }
