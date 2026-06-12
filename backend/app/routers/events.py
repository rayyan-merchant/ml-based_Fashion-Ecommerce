from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.events import Event
from app.dependencies import AdminResponse, get_current_admin
from app.schemas.events_schema import (
    EventBase,
    EventCreate,
    EventItem,
    EventSearchResult,
    EventStats,
    EventTypeCount,
    EventsPerDay,
    EventsPerHour,
)
router = APIRouter()

# ---------------------------------------------------
# 1. GET All Events (with filters)
# ---------------------------------------------------
@router.get("/", response_model=List[EventBase])
def get_all_events(
    skip: int = 0,
    limit: int = 100,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(Event).offset(skip).limit(limit).all()


# ---------------------------------------------------
# 2. Events By Customer
# ---------------------------------------------------
@router.get("/customer/{customer_id}", response_model=List[EventItem])
def get_events_by_customer(
    customer_id: str,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT *
        FROM niche_data.events
        WHERE customer_id = :cid
        ORDER BY created_at DESC
    """)
    return db.execute(sql, {"cid": customer_id}).mappings().all()


# ---------------------------------------------------
# 3. Events By Article
# ---------------------------------------------------
@router.get("/article/{article_id}", response_model=List[EventItem])
def get_events_by_article(
    article_id: str,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT *
        FROM niche_data.events
        WHERE article_id = :aid
        ORDER BY created_at DESC
    """)
    return db.execute(sql, {"aid": article_id}).mappings().all()


# ---------------------------------------------------
# 4. Events By Session
# ---------------------------------------------------
@router.get("/session/{session_id}", response_model=List[EventItem])
def get_events_by_session(
    session_id: str,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT *
        FROM niche_data.events
        WHERE session_id = :sid
        ORDER BY created_at DESC
    """)
    return db.execute(sql, {"sid": session_id}).mappings().all()


# ---------------------------------------------------
# 5. Recent Events
# ---------------------------------------------------
@router.get("/recent", response_model=List[EventItem])
def get_recent_events(
    limit: int = 50,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT *
        FROM niche_data.events
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    return db.execute(sql, {"limit": limit}).mappings().all()


# ---------------------------------------------------
# 6. Events by Type
# ---------------------------------------------------
@router.get("/type/{event_type}", response_model=List[EventItem])
def get_events_by_type(
    event_type: str,
    limit: int = 50,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT *
        FROM niche_data.events
        WHERE event_type = :etype
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    return db.execute(sql, {"etype": event_type, "limit": limit}).mappings().all()


# ---------------------------------------------------
# 7. Event Type Count Analytics
# ---------------------------------------------------
@router.get("/analytics/type-count", response_model=List[EventTypeCount])
def type_count(
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT event_type, COUNT(*) AS count
        FROM niche_data.events
        GROUP BY event_type
    """)
    return db.execute(sql).mappings().all()


# ---------------------------------------------------
# 8. Events Per Hour (traffic)
# ---------------------------------------------------
@router.get("/analytics/per-hour", response_model=List[EventsPerHour])
def events_per_hour(
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT EXTRACT(HOUR FROM created_at) AS hour,
               COUNT(*) AS count
        FROM niche_data.events
        GROUP BY hour
        ORDER BY hour
    """)
    return db.execute(sql).mappings().all()


# ---------------------------------------------------
# 9. Events Per Day
# ---------------------------------------------------
@router.get("/analytics/per-day", response_model=List[EventsPerDay])
def events_per_day(
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT DATE(created_at) AS date,
               COUNT(*) AS count
        FROM niche_data.events
        GROUP BY date
        ORDER BY date DESC
    """)
    return db.execute(sql).mappings().all()


# ---------------------------------------------------
# 10. Overall Stats
# ---------------------------------------------------
@router.get("/analytics/stats", response_model=EventStats)
def events_stats(
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT
            (SELECT COUNT(*) FROM niche_data.events) AS total_events,
            (SELECT COUNT(DISTINCT customer_id) FROM niche_data.events) AS unique_customers,
            (SELECT COUNT(DISTINCT article_id) FROM niche_data.events) AS unique_articles,
            (SELECT COUNT(DISTINCT session_id) FROM niche_data.events) AS unique_sessions
    """)
    return db.execute(sql).mappings().first()


# ---------------------------------------------------
# 11. Search
# ---------------------------------------------------
@router.get("/search", response_model=List[EventSearchResult])
def search_events(
    q: str,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT event_id, session_id, customer_id, article_id, event_type, created_at
        FROM niche_data.events
        WHERE event_id ILIKE :q
           OR session_id ILIKE :q
           OR customer_id ILIKE :q
           OR article_id ILIKE :q
           OR event_type ILIKE :q
        ORDER BY created_at DESC
        LIMIT 200
    """)
    return db.execute(sql, {"q": f"%{q}%"}).mappings().all()

@router.post("/", response_model=EventBase)
def add_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.put("/{event_id}", response_model=EventBase)
def update_event(
    event_id: int,
    event: EventCreate,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    db_event = db.query(Event).filter(Event.event_id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.dict().items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    db_event = db.query(Event).filter(Event.event_id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(db_event)
    db.commit()
    return {"detail": "Event deleted successfully"}

