from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import text

from app.db.database import get_db
from app.db.models.categories import Category
from app.db.models.articles import Article
from app.schemas.categories_schema import (
    CategoryCreate,
    CategoryOut,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryPerformanceResponse
)
from app.schemas.articles_schema import ArticleResponse
from app.dependencies import get_current_admin, AdminResponse


router = APIRouter()


# Category Tree --working
@router.get("/tree", response_model=List[CategoryTreeResponse])
def get_category_tree(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.category_id).all()

    lookup = {
        c.category_id: {
            "category_id": c.category_id,
            "category_name": c.name,
            "children": []
        }
        for c in categories
    }

    roots = []
    for c in categories:
        if c.parent_category_id:
            parent = lookup.get(c.parent_category_id)
            if parent:
                parent["children"].append(lookup[c.category_id])
        else:
            roots.append(lookup[c.category_id])

    return roots


# All Category Performance (VIEW) -- keeps loading
@router.get("/performance", response_model=List[CategoryPerformanceResponse])
def get_all_category_performance(skip: int = 0, limit: int = 100,db: Session = Depends(get_db)):
    sql = text("""
    SELECT *
    FROM niche_data.category_sales_summary
    ORDER BY category_id
    LIMIT :limit OFFSET :skip""")
    return db.execute(sql, {"skip": skip, "limit": limit}).mappings().all()



# Single Category Performance (VIEW) -- keeps loading
@router.get("/{category_id}/performance", response_model=CategoryPerformanceResponse)
def get_category_performance(category_id: int, db: Session = Depends(get_db)):
    sql = text("""
        SELECT *
        FROM niche_data.category_sales_summary
        WHERE category_id = :cid
        LIMIT 1
    """)
    row = db.execute(sql, {"cid": category_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Category performance not found")

    return row


# Articles Under Category -- internal server error
@router.get("/{category_id}/articles", response_model=List[ArticleResponse])
def get_articles_by_category(category_id: int, db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .filter(Article.category_id == category_id)
        .order_by(Article.article_id.asc())
        .all()
    )

    if not articles:
        raise HTTPException(status_code=404, detail="No articles found for this category")

    return articles


# ----------------------------------------------------
# CRUD + BASIC FETCH (static above dynamic)
# ----------------------------------------------------

# Flat list of categories -- working
@router.get("/", response_model=List[CategoryOut])
def get_all_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(Category)
        .order_by(Category.category_id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# Get category by name -- not working
@router.get("/by-name/{name}", response_model=CategoryOut)
def get_category_by_name(Name: str, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.name == Name).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


# CREATE (Admin only)
@router.post("/", response_model=CategoryOut)
def add_category(
    category: CategoryCreate, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if category.parent_category_id:
        parent = db.query(Category).filter(
            Category.category_id == category.parent_category_id
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category does not exist")

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# UPDATE (Admin only)
@router.put("/{id}", response_model=CategoryOut)
def update_category(
    id: int, 
    category: CategoryCreate, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.category_id == id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.parent_category_id:
        parent = db.query(Category).filter(
            Category.category_id == category.parent_category_id
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category does not exist")

    data = category.dict()

    if data.get("parent_category_id") == 0:
        data["parent_category_id"] = None

    for key, value in data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


# DELETE (Admin only)
@router.delete("/{id}")
def delete_category(
    id: int, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.category_id == id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted successfully"}
