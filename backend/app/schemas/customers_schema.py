from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional

# ----- Base schema for API response -----
class CustomerBase(BaseModel):
    customer_id: str
    age: Optional[int] = None
    postal_code: Optional[str] = None
    club_member_status: Optional[str] = None
    fashion_news_frequency: Optional[str] = None
    active: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    signup_date: Optional[datetime] = None
    gender: Optional[str] = None
    loyalty_score: Optional[float] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    class Config:
        orm_mode = True

# ----- Schema for creating a customer -----
class CustomerCreate(BaseModel):
    customer_id: str
    age: int
    postal_code: str
    club_member_status: str
    fashion_news_frequency: str
    active: bool
    first_name: str
    last_name: str
    email: EmailStr
    signup_date: datetime
    gender: str
    loyalty_score: float
    password_hash: str #Optional[str]= Field(None, description="plaintext password (will be hashed)")
    phone: str
    address: str
    model_config = {"from_attributes":True}

# ----- Schema for sending customer data in responses -----
class CustomerOut(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    club_member_status: Optional[str] = None
    fashion_news_frequency: Optional[str] = None
    active: Optional[bool] = None
    model_config = {"from_attributes": True}


# -------------------------
# Response models (no password)
# -------------------------
class CustomerResponse(CustomerBase):
    # exclude password_hash on purpose
    class Config:
        pass


# -------------------------
# Views / Analytics schemas
# -------------------------
class CustomerFeaturesResponse(BaseModel):
    customer_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    active: Optional[bool] = None
    unique_products_interacted: Optional[int] = 0
    total_views: Optional[int] = 0
    total_clicks: Optional[int] = 0
    total_wishlist: Optional[int] = 0
    total_cart_adds: Optional[int] = 0
    total_purchases: Optional[int] = 0
    total_spent: Optional[Decimal] = Decimal(0)
    last_purchase_date: Optional[datetime] = None
    total_reviews: Optional[int] = 0
    avg_rating: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class PurchaseFrequencyResponse(BaseModel):
    customer_id: str
    total_orders: int
    first_month: Optional[datetime] = None
    last_month: Optional[datetime] = None
    avg_orders_per_month: Optional[Decimal] = Decimal(0)

    model_config = {"from_attributes": True}


class CLVResponse(BaseModel):
    customer_id: str
    total_orders: int
    total_spent: Decimal
    avg_order_value: Optional[Decimal] = None
    last_order_date: Optional[datetime] = None
    first_order_date: Optional[datetime] = None
    customer_lifespan_days: Optional[int] = None
    loyalty_score: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class RFMResponse(BaseModel):
    customer_id: str
    recency_days: Optional[int] = None
    frequency: Optional[int] = None
    monetary: Optional[Decimal] = None
    r_score: Optional[int] = None
    f_score: Optional[int] = None
    m_score: Optional[int] = None

    model_config = {"from_attributes": True}


# Event item schema (for timeline)
class EventItem(BaseModel):
    event_id: int
    session_id: str | None = None
    customer_id: str
    article_id: str | None = None
    event_type: str
    campaign_id: str | None = None
    event_timestamp: datetime

    model_config = {"from_attributes": True}

class CustomerOrder(BaseModel):
    order_id: int
    customer_id: str
    payment_status: str | None = None
    total_amount: float | None = None
    order_date: datetime
    shipping_address: str | None = None

    model_config = {"from_attributes": True}
