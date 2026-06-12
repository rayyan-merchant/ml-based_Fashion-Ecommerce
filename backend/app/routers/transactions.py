from fastapi import APIRouter, Depends, HTTPException,status,Query
from sqlalchemy.orm import Session
from typing import List,Optional
from app.db.database import get_db
from app.db.models.transactions import Transaction
from app.schemas.transactions_schema import (
    TransactionCreate, TransactionOut,
    RevenueItem,TransactionBase,TransactionListItem)
from app.dependencies import get_current_admin, AdminResponse
from decimal import Decimal
from sqlalchemy import text
from datetime import date,datetime
router = APIRouter()
TABLE = "niche_data.transactions"

@router.get("/", response_model=List[TransactionOut])
def get_all_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Transaction).order_by(Transaction.t_dat.desc()).offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    db_transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="transaction not found")
    return db_transaction


# -------------------------
# Create a transaction (payment succeeded)
# -------------------------
@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    """
    Creates a transaction using the REAL article price from the articles table.
    The client cannot send price.
    """

    # 1. Get price from articles table
    sql_price = text("""
        SELECT price
        FROM niche_data.articles
        WHERE article_id = :aid
        LIMIT 1
    """)
    article_row = db.execute(sql_price, {"aid": payload.article_id}).mappings().first()

    if not article_row:
        raise HTTPException(404, "Article not found — cannot create transaction")

    real_price = Decimal(article_row["price"])

    # 2. Use today's date if missing
    t_dat_val = payload.t_dat or date.today()

    # 3. Insert into transactions table
    sql = text("""
        INSERT INTO niche_data.transactions (t_dat, customer_id, article_id, price, sales_channel_id)
        VALUES (:t_dat, :cid, :aid, :price, :channel)
        RETURNING transaction_id, t_dat, customer_id, article_id, price, sales_channel_id
    """)

    params = {
        "t_dat": t_dat_val,
        "cid": payload.customer_id,
        "aid": payload.article_id,
        "price": real_price,
        "channel": payload.sales_channel_id
    }

    row = db.execute(sql, params).mappings().first()
    db.commit()
    return row

# -------------------------
# List transactions for a customer
# -------------------------
@router.get("/customer/{customer_id}", response_model=List[TransactionListItem])
def transactions_for_customer(customer_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sql = text(f"""
        SELECT transaction_id, t_dat, customer_id, article_id, price, sales_channel_id
        FROM {TABLE}
        WHERE customer_id = :cid
        ORDER BY t_dat DESC, transaction_id DESC
        LIMIT :limit OFFSET :skip
    """)
    return db.execute(sql, {"cid": customer_id, "limit": limit, "skip": skip}).mappings().all()


# -------------------------
# List transactions for an article
# -------------------------
@router.get("/article/{article_id}", response_model=List[TransactionListItem])
def transactions_for_article(article_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sql = text(f"""
        SELECT transaction_id, t_dat, customer_id, article_id, price, sales_channel_id
        FROM {TABLE}
        WHERE article_id = :aid
        ORDER BY t_dat DESC, transaction_id DESC
        LIMIT :limit OFFSET :skip
    """)
    return db.execute(sql, {"aid": article_id, "limit": limit, "skip": skip}).mappings().all()


# -------------------------
# Delete a transaction (Admin only)
# -------------------------
@router.delete("/{transaction_id}", status_code=200)
def delete_transaction(
    transaction_id: int, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    result = db.execute(text(f"DELETE FROM {TABLE} WHERE transaction_id = :tid"), {"tid": transaction_id})
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"detail": f"Transaction {transaction_id} deleted"}


# -------------------------
# Analytics - revenue by date (paginated)
# -------------------------
@router.get("/analytics/revenue", response_model=List[RevenueItem])
def revenue_by_date(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    channel_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    sql = f"""
        SELECT t_dat::date AS date,
               COALESCE(SUM(price), 0) AS total_revenue,
               COUNT(*) AS total_transactions
        FROM {TABLE}
        WHERE 1=1
    """

    params = {}
    if date_from:
        sql += " AND t_dat >= :df"
        params["df"] = date_from
    if date_to:
        sql += " AND t_dat <= :dt"
        params["dt"] = date_to
    if channel_id is not None:
        sql += " AND sales_channel_id = :ch"
        params["ch"] = channel_id

    sql += " GROUP BY t_dat::date ORDER BY date DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip

    return db.execute(text(sql), params).mappings().all()







'''
@router.post("/", response_model=TransactionOut)
def add_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(transaction_id: int, transaction: TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in transaction.dict().items():
        setattr(db_transaction, key, value)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted successfully"}
'''