from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

# ---------- Request Schema (POST) ----------
class OrderItemCreate(BaseModel):
    order_id: int
    article_id: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal


# ---------- Update Schema (PUT/PATCH) ----------
class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[Decimal] = None


# ---------- Base Response Schema ----------
class OrderItemBase(BaseModel):
    order_item_id: int
    order_id: int
    article_id: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


# ---------- Response for GET endpoints ----------
class OrderItemOut(OrderItemBase):
    pass


# ---------- Response for nested use (orders/details) ----------
class OrderItemResponse(OrderItemBase):
    pass
