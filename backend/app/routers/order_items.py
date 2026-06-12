from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import text
from app.db.database import get_db
from app.db.models.order_items import OrderItem
from app.schemas.order_items_schema import(
     OrderItemCreate, OrderItemOut,OrderItemBase,
     OrderItemResponse,OrderItemUpdate)
from sqlalchemy.exc import IntegrityError, DBAPIError

router = APIRouter()

@router.get("/", response_model=List[OrderItemOut])
def get_all_order_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(OrderItem).order_by().offset(skip).limit(limit).all()



@router.get("/{order_item_id}", response_model=OrderItemOut)
def get_order_item(order_item_id: str, db: Session = Depends(get_db)):
    db_order_item = db.query(OrderItem).filter(OrderItem.order_item_id == order_item_id).first()
    if not db_order_item:
        raise HTTPException(status_code=404, detail="Orfer ITem not found")
    return db_order_item

# Get items by order id
@router.get("/order/{order_id}", response_model=List[OrderItemResponse])
def get_items_by_orderID(order_id: int, db: Session = Depends(get_db)):
    sql = text("""
        SELECT order_item_id, order_id, article_id, quantity, unit_price, line_total
        FROM niche_data.order_items
        WHERE order_id = :oid
        ORDER BY order_item_id desc
    """)
    return db.execute(sql, {"oid": order_id}).mappings().all()


# Create order_item (validates article exists, checks stock if desired)
@router.post("/", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def create_order_item(payload: OrderItemCreate, db: Session = Depends(get_db)):
    # 1) Validate order exists
    order_check = db.execute(text("SELECT 1 FROM niche_data.orders WHERE order_id = :oid"), {"oid": payload.order_id}).scalar()
    if not order_check:
        raise HTTPException(status_code=400, detail="Order not found")

    # 2) Optional: validate article exists
    art = db.execute(text("SELECT article_id, stock FROM niche_data.articles WHERE article_id = :aid"), {"aid": payload.article_id}).mappings().first()
    if not art:
        raise HTTPException(status_code=400, detail="Article not found")

    # 3) Optional: check stock (uncomment if you want to block oversell)
    if art.get("stock") is not None and art.get("stock") < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    try:
        # IMPORTANT: don't insert line_total (DB generates it)
        insert_sql = text("""
            INSERT INTO niche_data.order_items (order_id, article_id, quantity, unit_price)
            VALUES (:oid, :aid, :qty, :price)
            RETURNING order_item_id, order_id, article_id, quantity, unit_price, line_total
        """)
        created = db.execute(insert_sql, {
            "oid": payload.order_id,
            "aid": payload.article_id,
            "qty": payload.quantity,
            "price": payload.unit_price
        }).mappings().first()

        # Optionally call recalc function if exists (silently ignore if not)
        try:
            db.execute(text("SELECT niche_data.recalculate_order_total(:oid)"), {"oid": payload.order_id})
        except DBAPIError:
            pass

        # Optionally update stock using DB procedure if you have one:
        # try:
        #     db.execute(text("SELECT niche_data.update_stock_after_order(:aid, :qty)"), {"aid": payload.article_id, "qty": payload.quantity})
        # except DBAPIError:
        #     pass

        db.commit()
        return created

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"DB integrity error: {str(e.orig)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Update order item (quantity/unit_price)

@router.put("/{order_item_id}", response_model=OrderItemResponse)
def update_order_item(order_item_id: int, payload: OrderItemUpdate, db: Session = Depends(get_db)):
    # fetch existing
    row = db.execute(text("SELECT order_item_id, order_id, article_id, quantity, unit_price FROM niche_data.order_items WHERE order_item_id = :oiid"), {"oiid": order_item_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Order item not found")

    # build update fields
    updates = []
    params = {"oiid": order_item_id}
    if payload.quantity is not None:
        updates.append("quantity = :qty")
        params["qty"] = payload.quantity
    if payload.unit_price is not None:
        updates.append("unit_price = :price")
        params["price"] = payload.unit_price

    if not updates:
        return db.execute(text("""
            SELECT order_item_id, order_id, article_id, quantity, unit_price, line_total
            FROM niche_data.order_items WHERE order_item_id = :oiid
        """), {"oiid": order_item_id}).mappings().first()

    sql = text(f"""
        UPDATE niche_data.order_items
        SET {', '.join(updates)}
        WHERE order_item_id = :oiid
        RETURNING order_item_id, order_id, article_id, quantity, unit_price, line_total
    """)
    try:
        updated = db.execute(sql, params).mappings().first()

        # attempt to recalc order total if function exists
        try:
            db.execute(text("SELECT niche_data.recalculate_order_total(:oid)"), {"oid": updated["order_id"]})
        except DBAPIError:
            pass

        db.commit()
        return updated
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_item_id}")
def delete_order_item(order_item_id: int, db: Session = Depends(get_db)):
    # fetch order_id first for recalc
    row = db.execute(text("SELECT order_id FROM niche_data.order_items WHERE order_item_id = :oiid"), {"oiid": order_item_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Order item not found")

    order_id = row["order_id"]
    try:
        res = db.execute(text("DELETE FROM niche_data.order_items WHERE order_item_id = :oiid"), {"oiid": order_item_id})
        db.commit()

        # recalc
        try:
            db.execute(text("SELECT niche_data.recalculate_order_total(:oid)"), {"oid": order_id})
            db.commit()
        except DBAPIError:
            pass

        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order item not found")
        return {"detail": "Order item deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



''' BASIC
@router.post("/", response_model=OrderItemOut)
def add_order_item(order_item: OrderItemCreate, db: Session = Depends(get_db)):
    db_item = OrderItem(**order_item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{order_item_id}", response_model=OrderItemOut)
def update_order_item(order_item_id: int, order_item: OrderItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(OrderItem).filter(OrderItem.order_item_id == order_item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    for key, value in order_item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{order_item_id}")
def delete_order_item(order_item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(OrderItem).filter(OrderItem.order_item_id == order_item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    db.delete(db_item)
    db.commit()
    return {"detail": "Order item deleted successfully"}
'''