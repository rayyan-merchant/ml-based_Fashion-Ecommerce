from pydantic import BaseModel
from datetime import datetime

# Response schema
class WishlistBase(BaseModel):
    wishlist_id: int
    customer_id: str
    article_id: str
    added_at: datetime

    model_config={'from_attributes':True}

# Request schema
class WishlistCreate(BaseModel):
    customer_id: str
    article_id: str

# Simple payload for adding to wishlist from frontend
class AddToWishlistRequest(BaseModel):
    article_id: str

class WishlistOut(WishlistBase):
    pass