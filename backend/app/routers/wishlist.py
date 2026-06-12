from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.customer_auth import get_current_customer, CustomerResponse
from app.db.database import get_db
from app.db.models.wishlist import Wishlist
from app.dependencies import AdminResponse, get_current_admin
from app.schemas.wishlist import (
    WishlistBase,
    WishlistCreate,
    WishlistOut,
    AddToWishlistRequest  # Import the new model
)

router = APIRouter()


@router.get("/")
def get_customer_wishlist(
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get wishlist for logged-in customer"""
    wishlist_items = db.execute(
        text("""
            SELECT w.wishlist_id, w.article_id, 
                   a.prod_name as name , a.price, a.stock,a.image_path
            FROM niche_data.wishlist w
            JOIN niche_data.articles a ON w.article_id = a.article_id
            WHERE w.customer_id = :customer_id
        """),
        {"customer_id": current_customer.customer_id}
    ).fetchall()
    
    return [
        {
            "wishlist_id": item[0],
            "article_id": item[1],
            "article_name": item[2],
            "price": float(item[3]),
            "stock": item[4],
            "image_path": item[5] 
        }
        for item in wishlist_items
    ]


@router.post("/add")
def add_to_wishlist(
    payload: AddToWishlistRequest,  # Accept request body instead of query params
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Add item to wishlist (requires authentication)"""
    
    # Extract article_id from payload
    article_id = payload.article_id
    
    # Check if already in wishlist
    existing = db.execute(
        text("""
            SELECT wishlist_id 
            FROM niche_data.wishlist 
            WHERE customer_id = :customer_id AND article_id = :article_id
        """),
        {
            "customer_id": current_customer.customer_id,
            "article_id": article_id
        }
    ).fetchone()
    
    if existing:
        raise HTTPException(status_code=400, detail="Item already in wishlist")
    
    db.execute(
        text("""
            INSERT INTO niche_data.wishlist (customer_id, article_id, added_at)
            VALUES (:customer_id, :article_id, NOW())
        """),
        {
            "customer_id": current_customer.customer_id,
            "article_id": article_id
        }
    )
    db.commit()
    
    return {"message": "Item added to wishlist"}


# ---------------- Get wishlist for 1 customer - Customer authenticated ----------------
@router.get("/customer/{customer_id}", response_model=List[WishlistOut])
def get_customer_wishlist_by_id(
    customer_id: str, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get wishlist for a specific customer.
    Customer can only view their own wishlist.
    """
    # Ensure customer can only view their own wishlist
    if str(current_customer.customer_id) != str(customer_id):
        raise HTTPException(status_code=403, detail="Cannot view another customer's wishlist")
    
    sql = text("""
        SELECT wishlist_id, customer_id, article_id, added_at
        FROM niche_data.wishlist
        WHERE customer_id = :cid
        ORDER BY added_at DESC
    """)
    return db.execute(sql, {"cid": customer_id}).mappings().all()


# ---------------- Add item to wishlist - Customer authenticated ----------------
@router.post("/add-item", response_model=WishlistOut)
def add_to_wishlist_authenticated(
    payload: WishlistCreate, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Add item to wishlist.
    Customer can only add items to their own wishlist.
    """
    # Ensure customer can only add to their own wishlist
    if str(payload.customer_id) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot add items to another customer's wishlist")
    
    # 1. Check if already exists
    existing = db.execute(text("""
        SELECT wishlist_id, customer_id, article_id, added_at
        FROM niche_data.wishlist
        WHERE customer_id = :cid AND article_id = :aid
    """), {"cid": payload.customer_id, "aid": payload.article_id}).mappings().first()

    if existing:
        # OPTIONAL: Update timestamp if user clicks wishlist again
        updated = db.execute(text("""
            UPDATE niche_data.wishlist
            SET added_at = NOW()
            WHERE wishlist_id = :wid
            RETURNING wishlist_id, customer_id, article_id, added_at
        """), {"wid": existing["wishlist_id"]}).mappings().first()
        db.commit()
        return updated

    # 2. Insert new wishlist entry
    inserted = db.execute(text("""
        INSERT INTO niche_data.wishlist (customer_id, article_id, added_at)
        VALUES (:cid, :aid, NOW())
        RETURNING wishlist_id, customer_id, article_id, added_at
    """), {"cid": payload.customer_id, "aid": payload.article_id}).mappings().first()

    db.commit()
    return inserted


@router.post("/move-to-cart/{wishlist_id}")
def move_wishlist_to_cart(
    wishlist_id: int, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Move wishlist item to cart.
    Customer can only move their own wishlist items.
    """
    # 1. Get wishlist item
    wl = db.execute(
        text("""
            SELECT wishlist_id, customer_id, article_id
            FROM niche_data.wishlist
            WHERE wishlist_id = :wid
        """),
        {"wid": wishlist_id}
    ).mappings().first()

    if not wl:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    # Ensure customer can only move their own wishlist items
    if str(wl["customer_id"]) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot move another customer's wishlist item")

    customer_id = wl["customer_id"]
    article_id = wl["article_id"]

    # 2. Check if same article is already in cart
    existing = db.execute(
        text("""
            SELECT cart_id, quantity
            FROM niche_data.cart
            WHERE customer_id = :cid AND article_id = :aid
        """),
        {"cid": customer_id, "aid": article_id}
    ).mappings().first()

    if existing:
        # 3A. Update quantity (+1)
        new_qty = existing["quantity"] + 1
        db.execute(
            text("""
                UPDATE niche_data.cart
                SET quantity = :q
                WHERE cart_id = :cart_id
            """),
            {"q": new_qty, "cart_id": existing["cart_id"]}
        )
    else:
        # 3B. Insert new cart row
        db.execute(
            text("""
                INSERT INTO niche_data.cart (customer_id, article_id, quantity, added_at)
                VALUES (:cid, :aid, 1, NOW())
            """),
            {"cid": customer_id, "aid": article_id}
        )

    # 4. Delete from wishlist
    db.execute(
        text("DELETE FROM niche_data.wishlist WHERE wishlist_id = :wid"),
        {"wid": wishlist_id}
    )

    db.commit()

    return {"detail": "Item moved from wishlist to cart successfully"}


# ---------------- Delete specific wishlist item - Customer authenticated ----------------
@router.delete("/item/{wishlist_id}")
def delete_wishlist_item(
    wishlist_id: int, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Delete a specific wishlist item.
    Customer can only delete their own wishlist items.
    """
    # Check if wishlist item belongs to current customer
    wishlist_check = db.execute(
        text("SELECT customer_id FROM niche_data.wishlist WHERE wishlist_id = :wid"),
        {"wid": wishlist_id}
    ).fetchone()
    
    if not wishlist_check:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    if str(wishlist_check[0]) != str(current_customer.customer_id):
        raise HTTPException(status_code=403, detail="Cannot delete another customer's wishlist item")
    
    row = db.execute(text("""
        DELETE FROM niche_data.wishlist
        WHERE wishlist_id = :wid
        RETURNING wishlist_id
    """), {"wid": wishlist_id}).fetchone()

    db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    return {"detail": "Wishlist item deleted"}


# ---------------- Clear entire wishlist for customer - Customer authenticated ----------------
@router.delete("/customer/{customer_id}")
def clear_customer_wishlist(
    customer_id: str, 
    current_customer: CustomerResponse = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Clear entire wishlist for a customer.
    Customer can only clear their own wishlist.
    """
    # Ensure customer can only clear their own wishlist
    if str(current_customer.customer_id) != str(customer_id):
        raise HTTPException(status_code=403, detail="Cannot clear another customer's wishlist")
    
    db.execute(text("""
        DELETE FROM niche_data.wishlist
        WHERE customer_id = :cid
    """), {"cid": customer_id})
    
    db.commit()
    return {"detail": "Wishlist cleared"}
