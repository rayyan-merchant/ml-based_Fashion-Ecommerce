from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.customer_auth import get_current_customer, CustomerResponse
from app.db.database import get_db
from app.db.models.cart import Cart
from app.dependencies import AdminResponse, get_current_admin
from app.schemas.cart import (
    CartItemBase,
    CartItemCreate,
    CartItemOut,
    CartItemUpdate,
    CartResponse,
    AddToCartRequest  # Import the new model
)

router = APIRouter()



@router.get("/")
def get_customer_cart(
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get cart for logged-in customer"""
    cart_items = db.execute(
        text("""
            SELECT
                   c.cart_id,
                   c.article_id,
                   c.quantity,
                   a.prod_name as article_name,
                   a.price AS original_price,
                   CASE
                       WHEN COALESCE(a.sale_discount_pct, 0) > 0
                            AND (a.sale_starts_at IS NULL OR a.sale_starts_at <= now())
                            AND (a.sale_ends_at IS NULL OR a.sale_ends_at >= now())
                       THEN ROUND((a.price * (100 - a.sale_discount_pct) / 100.0)::numeric, 2)
                       ELSE a.price
                   END AS price,
                   CASE
                       WHEN COALESCE(a.sale_discount_pct, 0) > 0
                            AND (a.sale_starts_at IS NULL OR a.sale_starts_at <= now())
                            AND (a.sale_ends_at IS NULL OR a.sale_ends_at >= now())
                       THEN a.sale_discount_pct
                       ELSE 0
                   END AS sale_discount_pct,
                   a.stock,
                   a.image_path
            FROM niche_data.cart c
            JOIN niche_data.articles a ON c.article_id = a.article_id
            WHERE c.customer_id = :customer_id
        """),
        {"customer_id": current_customer.customer_id}
    ).fetchall()
    
    return [
        {
            "cart_id": item[0],
            "article_id": item[1],
            "quantity": item[2],
            "article_name": item[3],
            "prod_name": item[3],
            "original_price": float(item[4]),
            "price": float(item[5]),
            "sale_discount_pct": int(item[6] or 0),
            "stock": item[7],
            "image_path": item[8]
        }
        for item in cart_items
    ]

@router.post("/add")
def add_to_cart(
    payload: AddToCartRequest,  # Accept request body instead of query params
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Add item to cart (requires authentication)"""
    
    # Extract values from payload
    article_id = payload.article_id
    quantity = payload.quantity
    
    # Check if item already in cart
    existing = db.execute(
        text("""
            SELECT cart_id, quantity 
            FROM niche_data.cart 
            WHERE customer_id = :customer_id AND article_id = :article_id
        """),
        {
            "customer_id": current_customer.customer_id,
            "article_id": article_id
        }
    ).fetchone()
    
    if existing:
        # Update quantity
        db.execute(
            text("""
                UPDATE niche_data.cart 
                SET quantity = quantity + :quantity, added_at = NOW()
                WHERE cart_id = :cart_id
            """),
            {"cart_id": existing[0], "quantity": quantity}
        )
    else:
        # Insert new item
        db.execute(
            text("""
                INSERT INTO niche_data.cart (customer_id, article_id, quantity, added_at)
                VALUES (:customer_id, :article_id, :quantity, NOW())
            """),
            {
                "customer_id": current_customer.customer_id,
                "article_id": article_id,
                "quantity": quantity
            }
        )
    
    db.commit()
    return {"message": "Item added to cart"}


# Admin-only endpoint to get all carts
@router.get("/all", response_model=List[CartItemBase])
def get_all_cart(
    skip: int = 0,
    limit: int = 100,
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all carts (Admin only)."""
    return db.query(Cart).offset(skip).limit(limit).all()

@router.get("/customer/{customer_id}", response_model=CartResponse)
def get_cart(
    customer_id: str, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Return full cart for a customer (all items).
    Customer can only view their own cart.
    """
    # Ensure customer can only view their own cart
    if str(current_customer.customer_id) != str(customer_id):
        raise HTTPException(status_code=403, detail="Cannot view another customer's cart")
    
    sql = text("""
        SELECT cart_id, customer_id, article_id, quantity, added_at
        FROM niche_data.cart
        WHERE customer_id = :cid
        ORDER BY added_at DESC, cart_id
    """)
    rows = db.execute(sql, {"cid": customer_id}).mappings().all()
    return {"customer_id": customer_id, "items": rows}


# Add item to cart (merge if exists) - Customer authenticated
# -------------------------
@router.post("/add-item", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_to_cart_authenticated(
    payload: CartItemCreate, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Add an item to cart. If the same article already exists in the customer's cart,
    the quantity will be incremented (merged). Returns the upserted cart row.
    Customer can only add items to their own cart.
    """
    # Ensure customer can only add to their own cart
    if str(payload.customer_id) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot add items to another customer's cart")
    
    try:
        with db.begin():
            # check existing
            sql_select = text("""
                SELECT cart_id, customer_id, article_id, quantity, added_at
                FROM niche_data.cart
                WHERE customer_id = :cid AND article_id = :aid
                FOR UPDATE
            """)
            existing = db.execute(sql_select, {"cid": payload.customer_id, "aid": payload.article_id}).mappings().first()

            if existing:
                # merge quantity
                new_qty = int(existing["quantity"]) + int(payload.quantity)
                sql_update = text("""
                    UPDATE niche_data.cart
                    SET quantity = :qty, added_at = NOW()
                    WHERE cart_id = :cid
                    RETURNING cart_id, customer_id, article_id, quantity, added_at
                """)
                row = db.execute(sql_update, {"qty": new_qty, "cid": existing["cart_id"]}).mappings().first()
            else:
                # insert new item
                sql_insert = text("""
                    INSERT INTO niche_data.cart (customer_id, article_id, quantity, added_at)
                    VALUES (:cid, :aid, :qty, NOW())
                    RETURNING cart_id, customer_id, article_id, quantity, added_at
                """)
                row = db.execute(sql_insert, {"cid": payload.customer_id, "aid": payload.article_id, "qty": payload.quantity}).mappings().first()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to add item to cart")

        return row

    except Exception as e:
        # keep the error message short for the client and log detailed error server-side
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------
# Update quantity for a cart item - Customer authenticated
# ------------------------- edits existing cart item
@router.put("/{cart_id}", response_model=CartItemOut)
def update_cart_item(
    cart_id: int, 
    payload: CartItemUpdate, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Update the quantity for a cart item by cart_id.
    Customer can only update their own cart items.
    """
    # Check if cart item belongs to current customer
    cart_check = db.execute(
        text("SELECT customer_id FROM niche_data.cart WHERE cart_id = :cid"),
        {"cid": cart_id}
    ).fetchone()
    
    if not cart_check:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    if str(cart_check[0]) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot update another customer's cart item")
    
    sql = text("""
        UPDATE niche_data.cart
        SET quantity = :qty, added_at = NOW()
        WHERE cart_id = :cid
        RETURNING cart_id, customer_id, article_id, quantity, added_at
    """)
    row = db.execute(sql, {"qty": int(payload.quantity), "cid": cart_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.commit()
    return row


# -------------------------
# Remove an item from cart - Customer authenticated (already has auth in earlier endpoint)
# -------------------------
# The earlier delete endpoint already has authentication, so this one is kept for compatibility
# but should use the authenticated one above

@router.delete("/{cart_id}")
def remove_from_cart(
    cart_id: int,
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Remove item from cart (requires authentication)"""
    
    # Verify cart belongs to customer
    cart = db.execute(
        text("SELECT customer_id FROM niche_data.cart WHERE cart_id = :cart_id"),
        {"cart_id": cart_id}
    ).fetchone()
    
    if not cart or cart[0] != current_customer.customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.execute(
        text("DELETE FROM niche_data.cart WHERE cart_id = :cart_id"),
        {"cart_id": cart_id}
    )
    db.commit()
    
    return {"message": "Item removed from cart"}


# -------------------------
# Clear full cart for a customer - Customer authenticated
# -------------------------
@router.delete("/clear/{customer_id}")
def clear_cart(
    customer_id: str, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Remove all items from a customer's cart.
    Customer can only clear their own cart.
    """
    # Ensure customer can only clear their own cart
    if str(current_customer.customer_id) != str(customer_id):
        raise HTTPException(status_code=403, detail="Cannot clear another customer's cart")
    
    sql = text("DELETE FROM niche_data.cart WHERE customer_id = :cid RETURNING count(*)")
    # Note: returning count(*) from DELETE is not standard; do a separate count if needed
    deleted = db.execute(text("DELETE FROM niche_data.cart WHERE customer_id = :cid"), {"cid": customer_id})
    db.commit()
    return {"detail": "Cart cleared", "customer_id": customer_id}



# -------------------------
# Cart item count quick endpoint - Customer authenticated
# -------------------------
@router.get("/{customer_id}/count")
def cart_count(
    customer_id: str, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get cart item count for a customer.
    Customer can only view their own cart count.
    """
    # Ensure customer can only view their own cart count
    if str(current_customer.customer_id) != str(customer_id):
        raise HTTPException(status_code=403, detail="Cannot view another customer's cart count")
    
    sql = text("""
        SELECT COALESCE(SUM(quantity),0) AS total_items, COUNT(*) AS rows
        FROM niche_data.cart
        WHERE customer_id = :cid
    """)
    row = db.execute(sql, {"cid": customer_id}).mappings().first()
    return {"customer_id": customer_id, "total_items": int(row["total_items"]), "rows": int(row["rows"])}















'''
@router.post("/", response_model=CartItemBase)
def add_cart(item: CartItemCreate, db: Session = Depends(get_db)):
    db_item = Cart(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{cart_id}", response_model=CartItemBase)
def update_cart(cart_id: int, item: CartItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{cart_id}")
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(db_item)
    db.commit()
    return {"detail": "Cart item deleted successfully"}
'''
