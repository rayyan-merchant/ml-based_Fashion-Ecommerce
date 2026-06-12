from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional,List

# Response schema
class CartItemBase(BaseModel):
    cart_id: int
    customer_id: str
    article_id: str
    quantity: int = Field(...,gt=0)
    added_at: datetime

    model_config={'from_attributes':True}

# Payload to add an item
class CartItemCreate(BaseModel):
    customer_id: str
    article_id: str
    quantity: int = Field(1, gt=0)

# Simple payload for adding to cart from frontend
class AddToCartRequest(BaseModel):
    article_id: str
    quantity: int = Field(1, gt=0)

# Response when creating/updating an item (single item)
class CartItemOut(CartItemBase):
    pass

# Payload for updating quantity
class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

# Response for a full cart
class CartResponse(BaseModel):
    customer_id: str
    items: List[CartItemOut] = []

    model_config = {"from_attributes": True}