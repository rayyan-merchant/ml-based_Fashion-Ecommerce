from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import Optional, List

# Base transaction fields (incoming)
class TransactionBase(BaseModel):
    t_dat: Optional[date] = None
    customer_id: str
    article_id: str
    sales_channel_id: Optional[int] = None

    model_config = {"from_attributes": True}

# Create payload (client -> server)
class TransactionCreate(TransactionBase):
    t_dat: Optional[date] = None
    customer_id: str
    article_id: str
    sales_channel_id: Optional[int] = None

# Outgoing (DB) representation
class TransactionOut(TransactionBase):
    transaction_id: int
    price: Decimal
    model_config = {"from_attributes": True}

# Lightweight list item
class TransactionListItem(BaseModel):
    transaction_id: int
    t_dat: date
    customer_id: str
    article_id: Optional[str]
    price: Decimal
    sales_channel_id: Optional[int]

    model_config = {"from_attributes": True}

# Analytics schema
class RevenueItem(BaseModel):
    date: date
    total_revenue: Decimal
    total_transactions: int

    model_config = {"from_attributes": True}
