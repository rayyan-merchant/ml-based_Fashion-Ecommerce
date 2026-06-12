from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import text
from app.db.database import get_db
from app.db.models.orders import Order
from app.schemas.orders_schema import (
    OrderCreate, OrderOut, OrderResponse, OrderDetailResponse, OrderUpdate,
    OrderListItem, OrderItemResponse, DailySalesItem
)
from sqlalchemy.exc import IntegrityError
from app.customer_auth import get_current_customer, CustomerResponse
from app.dependencies import get_current_admin, AdminResponse

router = APIRouter()


@router.get("/my-orders")
def get_my_orders(
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get all orders for logged-in customer"""
    try:
        orders = db.execute(
            text("""
                SELECT order_id, total_amount, payment_status, 
                       shipping_address, order_date
                FROM niche_data.orders
                WHERE customer_id = :customer_id
                ORDER BY order_date DESC
            """),
            {"customer_id": current_customer.customer_id}
        ).fetchall()
        
        return [
            {
                "order_id": order[0],
                "total_amount": float(order[1]),
                "payment_status": order[2],
                "shipping_address": order[3],
                "created_at": order[4]
            }
            for order in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve orders: {str(e)}")

@router.post("/create")
def create_order(
    shipping_address: str,
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create order from cart (requires authentication)"""
    
    try:
        # Get cart items
        cart_items = db.execute(
            text("""
                SELECT c.article_id, c.quantity, a.price
                FROM niche_data.cart c
                JOIN niche_data.articles a ON c.article_id = a.article_id
                WHERE c.customer_id = :customer_id
            """),
            {"customer_id": current_customer.customer_id}
        ).fetchall()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Calculate total
        total_amount = sum(item[2] * item[1] for item in cart_items)
        
        # Create order
        order_result = db.execute(
            text("""
                INSERT INTO niche_data.orders (
                    customer_id, total_amount, payment_status, 
                    shipping_address, order_date
                )
                VALUES (
                    :customer_id, :total_amount, 'pending', 
                    :shipping_address, NOW()
                )
                RETURNING order_id
            """),
            {
                "customer_id": current_customer.customer_id,
                "total_amount": total_amount,
                "shipping_address": shipping_address
            }
        ).fetchone()
        
        order_id = order_result[0]
        
        # Create order items
        for item in cart_items:
            db.execute(
                text("""
                    INSERT INTO niche_data.order_items (
                        order_id, article_id, quantity, 
                        unit_price
                    )
                    VALUES (
                        :order_id, :article_id, :quantity, 
                        :price
                    )
                """),
                {
                    "order_id": order_id,
                    "article_id": item[0],
                    "quantity": item[1],
                    "price": item[2]
                }
            )
        
        # Clear cart
        db.execute(
            text("DELETE FROM niche_data.cart WHERE customer_id = :customer_id"),
            {"customer_id": current_customer.customer_id}
        )
        
        db.commit()
        
        return {
            "order_id": order_id,
            "total_amount": total_amount,
            "message": "Order created successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Order creation failed: {e}")  # Add debug logging
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@router.get("/", response_model=List[OrderOut])
def get_all_orders(
    skip: int = 0, 
    limit: int = 100, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all orders (Admin only)"""
    return db.query(Order).order_by(Order.order_date.desc()).offset(skip).limit(limit).all()


@router.get("/{order_id}/details", response_model=OrderDetailResponse)
def get_order_details(
    order_id: int, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get order details.
    Customer can only view their own order details.
    """
    # -------- Order header ----------
    sql_order = text("""
        SELECT order_id, customer_id, order_date, total_amount, payment_status, shipping_address
        FROM niche_data.orders
        WHERE order_id = :oid
    """)
    order = db.execute(sql_order, {"oid": order_id}).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Ensure customer can only view their own orders
    if str(order["customer_id"]) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot view another customer's order")

    # -------- Items ----------
    sql_items = text("""
        SELECT order_item_id, order_id, article_id,
               quantity, unit_price, line_total
        FROM niche_data.order_items
        WHERE order_id = :oid
        ORDER BY order_item_id
    """)
    items = db.execute(sql_items, {"oid": order_id}).mappings().all()

    data = dict(order)
    data["items"] = items
    return data

@router.get("/customer/{customer_id}", response_model=List[OrderOut])
def get_orders_for_customer(
    customer_id: str, 
    current_admin: AdminResponse = Depends(get_current_admin),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get orders for a specific customer (Admin only).
    Admins can view any customer's orders.
    """
    sql = text("""
        SELECT *
        FROM niche_data.orders
        WHERE customer_id = :cid
        ORDER BY order_date DESC
        LIMIT :limit OFFSET :skip
    """)
    return db.execute(sql, {"cid": customer_id, "skip": skip, "limit": limit}).mappings().all()


# -------------------------------------------
#            ADVANCED FILTERS
# -------------------------------------------

from datetime import datetime

@router.get("/filter", response_model=List[OrderOut])
def filter_orders(
    payment_status: Optional[str] = None,
    min_total: Optional[Decimal] = None,
    max_total: Optional[Decimal] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Filter orders (Admin only)"""
    sql = "SELECT * FROM niche_data.orders WHERE 1=1"
    params = {}

    if payment_status:
        sql += " AND payment_status = :status"
        params["status"] = payment_status

    if min_total is not None:
        sql += " AND total_amount >= :min_total"
        params["min_total"] = Decimal(min_total)

    if max_total is not None:
        sql += " AND total_amount <= :max_total"
        params["max_total"] = Decimal(max_total)

    # parse date strings to timestamps if provided (accepts ISO format)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
        except Exception:
            raise HTTPException(status_code=400, detail="date_from must be an ISO datetime string")
        sql += " AND order_date >= :df"
        params["df"] = dt_from

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
        except Exception:
            raise HTTPException(status_code=400, detail="date_to must be an ISO datetime string")
        sql += " AND order_date <= :dt"
        params["dt"] = dt_to

    # ordering + pagination
    sql += " ORDER BY order_date DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip

    return db.execute(text(sql), params).mappings().all()

# -------------------------------------------
#              SALES ANALYTICS
# -------------------------------------------

@router.get("/analytics/daily-sales", response_model=List[DailySalesItem])
def get_daily_sales(
    skip: int = 0,
    limit: int = 50,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get daily sales analytics (Admin only)"""
    # 1) Find first order_date automatically
    min_date_sql = text("""
        SELECT MIN(order_date) AS first_date
        FROM niche_data.orders
    """)
    min_row = db.execute(min_date_sql).mappings().first()
    first_date = min_row["first_date"]

    if first_date is None:
        return []  # no orders exist

    # 2) Daily sales since first date
    sql = text("""
        SELECT DATE(order_date) AS date,
               COUNT(*) AS total_orders,
               COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM niche_data.orders
        WHERE order_date >= :first_date
        GROUP BY DATE(order_date)
        ORDER BY DATE(order_date) DESC
        LIMIT :limit OFFSET :skip
    """)

    return db.execute(sql, {
        "first_date": first_date,
        "skip": skip,
        "limit": limit
    }).mappings().all()



# -------------------------------------------
#           CREATE ORDER WITH ITEMS
#    (WILL WORK AFTER TRIGGER ISSUE FIXED)
# -------------------------------------------
#trigger func issue
@router.post("/create-with-items", response_model=OrderResponse)
def create_full_order(
    payload: OrderCreate, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Create a full order with items.
    Prices are fetched directly from articles table.
    Total amount is calculated based on quantity * price from articles table.
    Customer can only create orders for themselves.
    """
    # Ensure customer can only create orders for themselves
    if str(payload.customer_id) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot create orders for another customer")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    try:
        # 1. Fetch prices from articles table for all article_ids
        article_ids = [item.article_id for item in payload.items]
        
        sql_get_prices = text("""
            SELECT article_id, price, stock
            FROM niche_data.articles
            WHERE article_id = ANY(:article_ids)
        """)
        
        articles_result = db.execute(
            sql_get_prices,
            {"article_ids": article_ids}
        ).fetchall()
        
        # Create a dictionary mapping article_id to price and stock
        articles_dict = {row[0]: {"price": Decimal(str(row[1])), "stock": row[2]} for row in articles_result}
        
        # Validate all articles exist and check stock
        order_items_data = []
        total_amount = Decimal(0)
        
        for item in payload.items:
            if item.article_id not in articles_dict:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Article {item.article_id} not found"
                )
            
            article_info = articles_dict[item.article_id]
            article_price = article_info["price"]
            article_stock = article_info["stock"]
            
            # Check stock availability
            if article_stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for article {item.article_id}. Available: {article_stock}, Requested: {item.quantity}"
                )
            
            # Calculate line total
            line_total = article_price * item.quantity
            total_amount += line_total
            
            # Store item data with price from DB
            order_items_data.append({
                "article_id": item.article_id,
                "quantity": item.quantity,
                "unit_price": article_price
            })

        # 2. Insert order header
        sql_header = text("""
            INSERT INTO niche_data.orders (customer_id, order_date, total_amount, payment_status, shipping_address)
            VALUES (:cid, NOW(), :total, :status, :addr)
            RETURNING order_id
        """)
        order_id = db.execute(sql_header, {
            "cid": str(payload.customer_id),
            "total": total_amount,
            "status": payload.payment_status,
            "addr": payload.shipping_address
        }).scalar()

        # 3. Insert order items with prices from articles table
        sql_item = text("""
            INSERT INTO niche_data.order_items (order_id, article_id, quantity, unit_price)
            VALUES (:oid, :aid, :qty, :price)
        """)

        for item_data in order_items_data:
            db.execute(sql_item, {
                "oid": order_id,
                "aid": item_data["article_id"],
                "qty": item_data["quantity"],
                "price": item_data["unit_price"]
            })

        db.commit()

        # Return the created order
        return db.query(Order).filter(Order.order_id == order_id).first()

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(400, f"DB integrity error: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating order: {str(e)}")

# -------------------------------------------
#           UPDATE ORDER (E-COMMERCE STYLE)
# -------------------------------------------

@router.put("/{order_id}/status")
def update_order_status(
    order_id: int, 
    payment_status: str, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update order status (Admin only).
    Admins can update any order's status.
    """
    sql = text("""
        UPDATE niche_data.orders
        SET payment_status = :status
        WHERE order_id = :oid
        RETURNING order_id, customer_id, order_date, total_amount, payment_status, shipping_address
    """)
    row = db.execute(sql, {"status": payment_status, "oid": order_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    db.commit()
    return {"message": "Status updated", "order": dict(row)}



@router.put("/{order_id}/address")
def update_order_address(
    order_id: int, 
    new_address: str, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Update order shipping address.
    Customer can only update their own orders.
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    # Ensure customer can only update their own orders
    if str(order.customer_id) != str(current_customer.customer_id):
        raise HTTPException(403, "Cannot update another customer's order")

    order.shipping_address = new_address
    db.commit()
    db.refresh(order)
    return {"message": "Address updated", "order": order}

# -------------------------------------------
#         DELETE ORDER (CANCEL ORDER)
# -------------------------------------------
'''CANCEL
@router.delete("/{order_id}")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    # optional: cascade delete order items
    db.execute(text("DELETE FROM niche_data.order_items WHERE order_id = :oid"), {"oid": order_id})

    # cancel order instead of delete
    db.execute(text("""
        UPDATE niche_data.orders
        SET payment_status='cancelled'
        WHERE order_id = :oid
    """), {"oid": order_id})

    db.commit()
    return {"detail": "Order cancelled successfully"}'''
'''
# PERMANENT DEELELTE ORDER ID
@router.delete("/{order_id}", status_code=200)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    # Delete items first (FK dependency)
    db.execute(
        text("DELETE FROM niche_data.order_items WHERE order_id = :oid"),
        {"oid": order_id}
    )

    # Delete order
    result = db.execute(
        text("DELETE FROM niche_data.orders WHERE order_id = :oid"),
        {"oid": order_id}
    )

    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"detail": f"Order {order_id} permanently deleted"}

'''
'''
@router.put("/{order_id}", response_model=OrderOut)
def update_order(order_id: int, order: OrderCreate, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.order_id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    for key, value in order.dict().items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.order_id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(db_order)
    db.commit()
    return {"detail": "Order deleted successfully"}
'''
