from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.database import get_db
from app.db.models.customers import Customer
from app.dependencies import AdminResponse, get_current_admin
from app.schemas.customers_schema import (
    CLVResponse,
    CustomerCreate,
    CustomerFeaturesResponse,
    CustomerOrder,
    CustomerOut,
    CustomerResponse,
    EventItem,
    PurchaseFrequencyResponse,
    RFMResponse,
)

router = APIRouter()


def _assert_admin_or_owner(target_customer_id: str, current_user: dict) -> None:
    """
    Helper to ensure that the caller is either an admin or the owner of the customer profile.
    """
    if current_user["type"] == "admin":
        return

    customer = current_user.get("customer")
    if current_user["type"] == "customer" and customer and str(customer.customer_id) == str(target_customer_id):
        return

    raise HTTPException(status_code=403, detail="Not authorized for this customer")


@router.get("/", response_model=List[CustomerOut])
def get_all_customers(
    skip: int = 0,
    limit: int = 100,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(Customer)
        .order_by(Customer.customer_id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)

    db_customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.post("/", response_model=CustomerResponse)
def create_customer(
    payload: CustomerCreate,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # NOTE: password hashing / validation should be handled here in real system.
    # For now assume password (if provided) will be hashed by a service or DB trigger.
    data = payload.dict(exclude_none=True)
    # if password present -> hash & store in password_hash (implementation left for auth portion)
    db_customer = Customer(**data)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    customer: CustomerCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update customer profile.
    Admins can update any profile, customers can only update their own.
    """
    _assert_admin_or_owner(customer_id, current_user)

    db_customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, value in customer.dict().items():
        setattr(db_customer, key, value)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete customer (Admin only)"""
    db_customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(db_customer)
    db.commit()
    return {"detail": "Customer deleted successfully"}



# ------------------------
# Activate / Deactivate (Admin only)
# ------------------------
@router.put("/{customer_id}/active")
def set_customer_active(
    customer_id: str, 
    active: bool, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Activate/deactivate customer (Admin only)"""
    c = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    c.active = bool(active)
    db.commit()
    return {"detail": f"Customer {'activated' if c.active else 'deactivated'}"}


# ------------------------
# Analytics endpoints (views + materialized views)
# ------------------------

# Customer features (from customer_features view)
@router.get("/{customer_id}/features", response_model=CustomerFeaturesResponse)
def get_customer_features(
    customer_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)
    sql = text("""
        SELECT *
        FROM niche_data.customer_features
        WHERE customer_id = :cid
        LIMIT 1
    """)
    row = db.execute(sql, {"cid": customer_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer features not found")
    return row


# Purchase frequency view
@router.get("/{customer_id}/purchase-frequency", response_model=PurchaseFrequencyResponse)
def get_purchase_frequency(
    customer_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)
    sql = text("""
        SELECT *
        FROM niche_data.v_customer_purchase_frequency
        WHERE customer_id = :cid
        LIMIT 1
    """)
    row = db.execute(sql, {"cid": customer_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Purchase frequency not found")
    return row


# CLV materialized view
@router.get("/{customer_id}/clv", response_model=CLVResponse)
def get_customer_clv(
    customer_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)
    sql = text("""
        SELECT *
        FROM niche_data.mv_customer_clv
        WHERE customer_id = :cid
        LIMIT 1
    """)
    row = db.execute(sql, {"cid": customer_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="CLV not found")
    return row


# RFM materialized view
@router.get("/{customer_id}/rfm", response_model=RFMResponse)
def get_customer_rfm(
    customer_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)
    sql = text("""
        SELECT *
        FROM niche_data.mv_rfm
        WHERE customer_id = :cid
        LIMIT 1
    """)
    row = db.execute(sql, {"cid": customer_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="RFM not found")
    return row


# Events timeline (paginated)
@router.get("/{customer_id}/events", response_model=List[EventItem])
def get_customer_events(
    customer_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)
    sql = text("""
        SELECT 
            event_id,
            session_id,
            customer_id,
            article_id,
            event_type,
            campaign_id,
            created_at AT TIME ZONE 'UTC' AS event_timestamp
        FROM niche_data.events
        WHERE customer_id = :customer_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    rows = db.execute(sql, {
        "customer_id": customer_id,
        "limit": limit,
        "skip": skip
    }).mappings().all()

    return rows


# Orders summary for a customer (lightweight)
@router.get("/{customer_id}/orders", response_model=List[CustomerOrder])
def get_customer_orders(
    customer_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_admin_or_owner(customer_id, current_user)
    # Simplified order summary — adjust field names if your orders table differs
    sql = text("""
        SELECT order_id, customer_id, payment_status, total_amount, order_date,shipping_address
        FROM niche_data.orders
        WHERE customer_id = :cid
        ORDER BY order_date DESC
        LIMIT :limit OFFSET :skip
    """)
    rows = db.execute(sql, {"cid": customer_id, "skip": skip, "limit": limit}).mappings().all()
    return rows
