from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional,List
from decimal import Decimal



class OrderBase(BaseModel):
    #order_id: int
    customer_id: str
    order_date: Optional[datetime]=None
    total_amount: float
    payment_status: str
    shipping_address: str

    model_config={
        "from_attributes":True
    }

# ---------------- Order Item ----------------
class OrderItemCreate(BaseModel):
    article_id: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)

class OrderItemOut(BaseModel):
    order_item_id: int
    order_id: int
    article_id: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}

# Request schema
class OrderCreate(BaseModel):
    customer_id: str
    total_amount: float
    payment_status: str = "pending"
    shipping_address: str
    items: Optional[List[OrderItemCreate]] = Field(default_factory=list)

class OrderOut(OrderBase):
    order_id: int
    customer_id: str
    order_date: datetime
    total_amount: Decimal
    payment_status: str
    shipping_address: str

    model_config={"from_attributes":True}



# ---------------- Order Detail (with items) ----------------
class OrderDetailOut(OrderOut):
    items: List[OrderItemOut] = Field(default_factory=list)

# ---------- Order Item schemas ----------
class OrderItemBase(BaseModel):
    article_id: Optional[str] = None
    quantity: int
    unit_price: Decimal


class OrderItemResponse(OrderItemBase):
    order_item_id: int
    order_id: int
    line_total: Decimal

    model_config = {"from_attributes": True}


# ---------- Order header schemas ----------

class OrderUpdate(BaseModel):
    shipping_address: Optional[str] = None
    payment_status: Optional[str] = None

class OrderResponse(OrderBase):
    order_id: int
    order_date: datetime
    total_amount: Decimal

    model_config = {"from_attributes": True}


# ---------- Detailed order (header + items + optional customer) ----------
class OrderDetailResponse(OrderResponse):
    items: List[OrderItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ---------- Lightweight order summary for lists ----------
class OrderListItem(BaseModel):
    order_id: int
    customer_id: str
    order_date: datetime
    total_amount: Decimal
    payment_status: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------- Analytics schema (example) ----------
class DailySalesItem(BaseModel):
    date: datetime
    total_orders: int
    total_revenue: Decimal

    model_config = {"from_attributes": True}

class TopProductItem(BaseModel):
    article_id: str
    prod_name: Optional[str] = None
    total_quantity: int
    total_revenue: Decimal

    model_config = {"from_attributes": True}


class ItemUpdate(BaseModel):
    order_item_id: int
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None

class ItemsPatchRequest(BaseModel):
    update_items: Optional[List[ItemUpdate]] = []
    remove_item_ids: Optional[List[int]] = []
