from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Response schema
class EventBase(BaseModel):
    event_id: int
    session_id: Optional[str]=None
    customer_id: str
    article_id: str
    event_type: str
    campaign_id: Optional[int]=None
    created_at: datetime
    order_id: Optional[int]=None
    class Config:
        orm_mode = True

# Request schema
class EventCreate(BaseModel):
    session_id: str
    customer_id: str
    article_id: str
    event_type: str
    campaign_id: Optional[int]=None
    order_id: Optional[int]=None

class EventItem(EventBase):
    pass

class EventSearchResult(BaseModel):
    event_id: int
    session_id: str
    customer_id: Optional[str]
    article_id: Optional[str]
    event_type: str
    created_at: datetime


# ---------- Analytics ----------
class EventTypeCount(BaseModel):
    event_type: str
    count: int


class EventsPerHour(BaseModel):
    hour: int
    count: int


class EventsPerDay(BaseModel):
    date: datetime
    count: int


class EventStats(BaseModel):
    total_events: int
    unique_customers: int
    unique_articles: int
    unique_sessions: int