from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List
from functools import lru_cache
import os

from app.db.database import get_db
from app.db.models.articles import Article
from app.schemas.articles_schema import ArticleCreate, ArticleUpdate, ArticleResponse, ProductOut, ArticlePerformanceResponse,ArticleDemandTrendResponse,ArticleInventoryResponse,ArticleFunnelMetricsResponse
from app.actions import products as product_actions
from app.dependencies import get_current_admin, AdminResponse


router = APIRouter()

IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "filtered_images"))


@lru_cache(maxsize=20000)
def _local_image_exists(path: str | None) -> bool:
    if not path:
        return False

    clean_path = str(path).replace("\\", "/").lstrip("/")
    if clean_path.startswith(("http://", "https://")):
        return True
    if clean_path.startswith("filtered_images/"):
        clean_path = clean_path.replace("filtered_images/", "", 1)
    if clean_path.startswith("images/"):
        clean_path = clean_path.replace("images/", "", 1)

    return os.path.isfile(os.path.join(IMAGES_DIR, clean_path))


def _normalize_catalog_row(row):
    data = dict(row)
    data["price"] = float(data["price"]) if data.get("price") is not None else None
    data["min_price"] = float(data["min_price"]) if data.get("min_price") is not None else data["price"]
    data["max_price"] = float(data["max_price"]) if data.get("max_price") is not None else data["price"]
    data["stock"] = int(data["total_stock"] or data.get("stock") or 0)
    data["variant_count"] = int(data.get("variant_count") or 1)
    data["color_count"] = int(data.get("color_count") or 0)
    data["average_rating"] = float(data["average_rating"]) if data.get("average_rating") is not None else None
    data["total_reviews"] = int(data.get("total_reviews") or 0)
    data["popularity_score"] = int(data.get("popularity_score") or 0)
    data["total_products"] = int(data.get("total_products") or 0)
    data["sale_discount_pct"] = int(data.get("sale_discount_pct") or 0)
    data["is_on_sale"] = bool(data.get("is_on_sale"))
    data["original_price"] = data["price"]
    data["sale_price"] = float(data["sale_price"]) if data.get("sale_price") is not None else data["price"]
    data["min_sale_price"] = float(data["min_sale_price"]) if data.get("min_sale_price") is not None else data["min_price"]
    data["max_sale_price"] = float(data["max_sale_price"]) if data.get("max_sale_price") is not None else data["max_price"]

    variants = data.get("variants") or []
    data["variants"] = [
        {
            **variant,
            "price": float(variant["price"]) if variant.get("price") is not None else None,
            "original_price": float(variant["price"]) if variant.get("price") is not None else None,
            "sale_price": float(variant["sale_price"]) if variant.get("sale_price") is not None else None,
            "sale_discount_pct": int(variant.get("sale_discount_pct") or 0),
            "is_on_sale": bool(variant.get("is_on_sale")),
            "stock": int(variant.get("stock") or 0),
        }
        for variant in variants
    ]

    image_candidates = [
        data.get("image_path"),
        *(variant.get("image_path") for variant in data["variants"]),
    ]
    for image_path in image_candidates:
        if _local_image_exists(image_path):
            data["image_path"] = image_path
            break

    return data


def _catalog_sql(sort: str | None = None):
    sort_map = {
        "price_low_high": "ag.min_price ASC, rep.article_id ASC",
        "price_high_low": "ag.min_price DESC, rep.article_id ASC",
        "newest": "rep.article_id DESC",
        "popular": "COALESCE(transaction_stats.popularity_score, 0) DESC, ag.total_stock DESC, rep.article_id ASC",
        "trending": "COALESCE(transaction_stats.popularity_score, 0) DESC, COALESCE(review_stats.total_reviews, 0) DESC, rep.article_id ASC",
        "relevant": "COALESCE(transaction_stats.popularity_score, 0) DESC, COALESCE(review_stats.average_rating, 0) DESC, rep.article_id ASC",
        "discount": "ag.sale_discount_pct DESC, COALESCE(transaction_stats.popularity_score, 0) DESC, rep.article_id ASC",
    }
    order_by = sort_map.get(sort or "popular", sort_map["popular"])

    return text(f"""
        WITH filtered AS (
            SELECT
                a.*,
                COALESCE(a.product_code::text, a.article_id) AS product_key,
                CASE
                    WHEN a.product_type_name ILIKE '%Hood%' THEN 'hoodie'
                    WHEN a.product_type_name ILIKE '%Jacket%' THEN 'jacket'
                    WHEN a.product_type_name ILIKE '%Beanie%' THEN 'beanie'
                    WHEN a.product_type_name ILIKE '%Trouser%' OR a.product_type_name ILIKE '%Jeans%' THEN 'trouser'
                    WHEN a.product_group_name ILIKE '%Accessories%' THEN 'accessory'
                    ELSE LOWER(COALESCE(a.product_type_name, a.product_group_name, 'other'))
                END AS catalog_category
            FROM niche_data.articles a
            WHERE
                (
                    :section_name IS NULL OR :section_name = '' OR :section_name = 'all'
                    OR (:section_name = 'men' AND (
                        a.index_group_name = 'Menswear'
                        OR a.section_name ILIKE 'Men %'
                        OR a.section_name ILIKE 'Mens %'
                        OR a.section_name ILIKE '% Men'
                        OR a.section_name = 'Men H&M Sport'
                    ))
                    OR (:section_name = 'women' AND (
                        a.index_group_name = 'Ladieswear'
                        OR a.section_name ILIKE '%Women%'
                        OR a.section_name ILIKE '%Ladies%'
                        OR a.section_name ILIKE 'H&M+%'
                        OR a.section_name = 'Mama'
                    ))
                    OR (:section_name = 'kids' AND (
                        a.section_name ILIKE '%Kids%'
                        OR a.section_name ILIKE '%Baby%'
                        OR a.section_name IN ('Young Girl','Young Boy','Kids Boy','Kids Girl')
                    ))
                    OR (:section_name = 'accessories' AND a.product_group_name = 'Accessories')
                    OR (:section_name = 'unisex' AND (
                        a.index_group_name IN ('Divided', 'Sport')
                        AND a.section_name NOT ILIKE '%Men%'
                        AND a.section_name NOT ILIKE '%Ladies%'
                        AND a.section_name NOT ILIKE '%Women%'
                        AND a.section_name NOT ILIKE '%Kids%'
                        AND a.section_name NOT ILIKE '%Baby%'
                    ))
                )
                AND (
                    :category_name IS NULL OR :category_name = '' OR :category_name = 'all'
                    OR LOWER(a.product_type_name) ILIKE '%' || :category_name || '%'
                    OR LOWER(a.product_group_name) ILIKE '%' || :category_name || '%'
                    OR LOWER(a.garment_group_name) ILIKE '%' || :category_name || '%'
                    OR (:category_name = 'jacket' AND a.product_type_name ILIKE '%Jacket%')
                    OR (:category_name = 'hoodie' AND a.product_type_name ILIKE '%Hood%')
                    OR (:category_name = 'trouser' AND (a.product_type_name ILIKE '%Trouser%' OR a.product_type_name ILIKE '%Jeans%'))
                    OR (:category_name = 'beanie' AND a.product_type_name ILIKE '%Beanie%')
                    OR (:category_name = 'accessory' AND a.product_group_name ILIKE '%Accessories%')
                )
                AND (
                    :search_query IS NULL OR :search_query = ''
                    OR a.prod_name ILIKE '%' || :search_query || '%'
                    OR a.product_type_name ILIKE '%' || :search_query || '%'
                    OR a.product_group_name ILIKE '%' || :search_query || '%'
                    OR a.detail_desc ILIKE '%' || :search_query || '%'
                )
                AND (
                    :on_sale = false
                    OR (
                        COALESCE(a.sale_discount_pct, 0) > 0
                        AND (a.sale_starts_at IS NULL OR a.sale_starts_at <= now())
                        AND (a.sale_ends_at IS NULL OR a.sale_ends_at >= now())
                    )
                )
        ),
        ranked AS (
            SELECT
                f.*,
                ROW_NUMBER() OVER (
                    PARTITION BY f.product_key
                    ORDER BY COALESCE(f.stock, 0) DESC, f.article_id ASC
                ) AS rn
            FROM filtered f
        ),
        ag AS (
            SELECT
                f.product_key,
                MIN(f.price) AS min_price,
                MAX(f.price) AS max_price,
                MIN(
                    CASE
                        WHEN COALESCE(f.sale_discount_pct, 0) > 0
                             AND (f.sale_starts_at IS NULL OR f.sale_starts_at <= now())
                             AND (f.sale_ends_at IS NULL OR f.sale_ends_at >= now())
                        THEN ROUND((f.price * (100 - f.sale_discount_pct) / 100.0)::numeric, 2)
                        ELSE f.price
                    END
                ) AS min_sale_price,
                MAX(
                    CASE
                        WHEN COALESCE(f.sale_discount_pct, 0) > 0
                             AND (f.sale_starts_at IS NULL OR f.sale_starts_at <= now())
                             AND (f.sale_ends_at IS NULL OR f.sale_ends_at >= now())
                        THEN ROUND((f.price * (100 - f.sale_discount_pct) / 100.0)::numeric, 2)
                        ELSE f.price
                    END
                ) AS max_sale_price,
                MAX(
                    CASE
                        WHEN COALESCE(f.sale_discount_pct, 0) > 0
                             AND (f.sale_starts_at IS NULL OR f.sale_starts_at <= now())
                             AND (f.sale_ends_at IS NULL OR f.sale_ends_at >= now())
                        THEN f.sale_discount_pct
                        ELSE 0
                    END
                ) AS sale_discount_pct,
                SUM(COALESCE(f.stock, 0)) AS total_stock,
                COUNT(*) AS variant_count,
                COUNT(DISTINCT f.colour_group_name) AS color_count,
                JSONB_AGG(
                    JSONB_BUILD_OBJECT(
                        'article_id', f.article_id,
                        'product_code', f.product_code,
                        'colour_group_name', f.colour_group_name,
                        'graphical_appearance_name', f.graphical_appearance_name,
                        'price', f.price,
                        'sale_price',
                            CASE
                                WHEN COALESCE(f.sale_discount_pct, 0) > 0
                                     AND (f.sale_starts_at IS NULL OR f.sale_starts_at <= now())
                                     AND (f.sale_ends_at IS NULL OR f.sale_ends_at >= now())
                                THEN ROUND((f.price * (100 - f.sale_discount_pct) / 100.0)::numeric, 2)
                                ELSE f.price
                            END,
                        'sale_discount_pct',
                            CASE
                                WHEN COALESCE(f.sale_discount_pct, 0) > 0
                                     AND (f.sale_starts_at IS NULL OR f.sale_starts_at <= now())
                                     AND (f.sale_ends_at IS NULL OR f.sale_ends_at >= now())
                                THEN f.sale_discount_pct
                                ELSE 0
                            END,
                        'is_on_sale',
                            COALESCE(f.sale_discount_pct, 0) > 0
                            AND (f.sale_starts_at IS NULL OR f.sale_starts_at <= now())
                            AND (f.sale_ends_at IS NULL OR f.sale_ends_at >= now()),
                        'stock', f.stock,
                        'image_path', COALESCE(f.image_path, '0' || f.article_id || '.jpg')
                    )
                    ORDER BY f.colour_group_name NULLS LAST, f.article_id
                ) AS variants
            FROM filtered f
            GROUP BY f.product_key
        ),
        review_stats AS (
            SELECT f.product_key, AVG(r.rating) AS average_rating, COUNT(r.review_id) AS total_reviews
            FROM filtered f
            JOIN niche_data.reviews r ON r.article_id = f.article_id
            GROUP BY f.product_key
        ),
        transaction_stats AS (
            SELECT f.product_key, COUNT(t.transaction_id) AS popularity_score
            FROM filtered f
            JOIN niche_data.transactions t ON t.article_id = f.article_id
            GROUP BY f.product_key
        )
        SELECT
            rep.article_id,
            rep.product_code,
            rep.prod_name,
            rep.product_type_name,
            rep.product_group_name,
            rep.graphical_appearance_name,
            rep.colour_group_name,
            rep.department_no,
            rep.department_name,
            rep.index_name,
            rep.index_group_name,
            rep.section_name,
            rep.garment_group_name,
            rep.detail_desc,
            rep.price,
            CASE
                WHEN COALESCE(rep.sale_discount_pct, 0) > 0
                     AND (rep.sale_starts_at IS NULL OR rep.sale_starts_at <= now())
                     AND (rep.sale_ends_at IS NULL OR rep.sale_ends_at >= now())
                THEN ROUND((rep.price * (100 - rep.sale_discount_pct) / 100.0)::numeric, 2)
                ELSE rep.price
            END AS sale_price,
            CASE
                WHEN COALESCE(rep.sale_discount_pct, 0) > 0
                     AND (rep.sale_starts_at IS NULL OR rep.sale_starts_at <= now())
                     AND (rep.sale_ends_at IS NULL OR rep.sale_ends_at >= now())
                THEN rep.sale_discount_pct
                ELSE 0
            END AS sale_discount_pct,
            COALESCE(rep.sale_discount_pct, 0) > 0
                AND (rep.sale_starts_at IS NULL OR rep.sale_starts_at <= now())
                AND (rep.sale_ends_at IS NULL OR rep.sale_ends_at >= now()) AS is_on_sale,
            rep.sale_starts_at,
            rep.sale_ends_at,
            rep.category_id,
            COALESCE(rep.image_path, '0' || rep.article_id || '.jpg') AS image_path,
            ag.min_price,
            ag.max_price,
            ag.min_sale_price,
            ag.max_sale_price,
            ag.total_stock,
            ag.variant_count,
            ag.color_count,
            ag.variants,
            review_stats.average_rating,
            COALESCE(review_stats.total_reviews, 0) AS total_reviews,
            COALESCE(transaction_stats.popularity_score, 0) AS popularity_score,
            COUNT(*) OVER() AS total_products
        FROM ranked rep
        JOIN ag ON ag.product_key = rep.product_key
        LEFT JOIN review_stats ON review_stats.product_key = rep.product_key
        LEFT JOIN transaction_stats ON transaction_stats.product_key = rep.product_key
        WHERE rep.rn = 1
        ORDER BY {order_by}
        LIMIT :limit OFFSET :skip
    """)


# --------------------------------------------------------
# GET all articles
# --------------------------------------------------------
@router.get("/", response_model=List[ArticleResponse])
def get_articles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(Article)
        .order_by(Article.article_id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# --------------------------------------------------------
# GET articles by product name (returns LIST)
# --------------------------------------------------------
@router.get("/by-name/{prod_name}", response_model=List[ArticleResponse])
def get_articles_by_name(prod_name: str, db: Session = Depends(get_db)):
    articles = db.query(Article).filter(Article.prod_name == prod_name).all()

    if not articles:
        raise HTTPException(status_code=404, detail="No articles found")

    return articles


# --------------------------------------------------------
# SEARCH articles by partial product name (returns LIST)
# --------------------------------------------------------
@router.get("/search/{query}", response_model=List[ArticleResponse])
def search_articles(query: str, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    articles = db.query(Article).filter(
        Article.prod_name.ilike(f"%{query}%")
    ).offset(skip).limit(limit).all()

    return articles


@router.get("/catalog/")
def get_product_catalog(
    skip: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=200),
    section: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    on_sale: bool = Query(False),
    sort: str | None = Query("popular"),
    db: Session = Depends(get_db),
):
    params = {
        "skip": skip,
        "limit": limit,
        "section_name": (section or "").lower(),
        "category_name": (category or "").lower(),
        "search_query": search or "",
        "on_sale": on_sale,
    }
    rows = db.execute(_catalog_sql(sort), params).mappings().all()
    products = [_normalize_catalog_row(row) for row in rows]
    total = products[0]["total_products"] if products else 0
    for product in products:
        product.pop("total_products", None)
    return jsonable_encoder({"products": products, "total_products": total})


@router.get("/{article_id}/variants")
def get_article_variants(article_id: str, db: Session = Depends(get_db)):
    target = db.execute(
        text("""
            SELECT COALESCE(product_code::text, article_id) AS product_key
            FROM niche_data.articles
            WHERE article_id = :article_id
        """),
        {"article_id": article_id},
    ).mappings().first()

    if not target:
        raise HTTPException(status_code=404, detail="Article not found")

    rows = db.execute(
        text("""
            SELECT
                article_id,
                product_code,
                prod_name,
                product_type_name,
                product_group_name,
                graphical_appearance_name,
                colour_group_name,
                department_no,
                department_name,
                index_name,
                index_group_name,
                section_name,
                garment_group_name,
                detail_desc,
                price,
                CASE
                    WHEN COALESCE(sale_discount_pct, 0) > 0
                         AND (sale_starts_at IS NULL OR sale_starts_at <= now())
                         AND (sale_ends_at IS NULL OR sale_ends_at >= now())
                    THEN ROUND((price * (100 - sale_discount_pct) / 100.0)::numeric, 2)
                    ELSE price
                END AS sale_price,
                CASE
                    WHEN COALESCE(sale_discount_pct, 0) > 0
                         AND (sale_starts_at IS NULL OR sale_starts_at <= now())
                         AND (sale_ends_at IS NULL OR sale_ends_at >= now())
                    THEN sale_discount_pct
                    ELSE 0
                END AS sale_discount_pct,
                COALESCE(sale_discount_pct, 0) > 0
                    AND (sale_starts_at IS NULL OR sale_starts_at <= now())
                    AND (sale_ends_at IS NULL OR sale_ends_at >= now()) AS is_on_sale,
                sale_starts_at,
                sale_ends_at,
                stock,
                category_id,
                COALESCE(image_path, '0' || article_id || '.jpg') AS image_path
            FROM niche_data.articles
            WHERE COALESCE(product_code::text, article_id) = :product_key
            ORDER BY colour_group_name NULLS LAST, article_id
        """),
        {"product_key": target["product_key"]},
    ).mappings().all()

    variants = []
    for row in rows:
        variant = dict(row)
        variant["price"] = float(variant["price"]) if variant.get("price") is not None else None
        variant["original_price"] = variant["price"]
        variant["sale_price"] = float(variant["sale_price"]) if variant.get("sale_price") is not None else variant["price"]
        variant["sale_discount_pct"] = int(variant.get("sale_discount_pct") or 0)
        variant["is_on_sale"] = bool(variant.get("is_on_sale"))
        variant["stock"] = int(variant.get("stock") or 0)
        variants.append(variant)

    return jsonable_encoder({"article_id": article_id, "variants": variants})


# --------------------------------------------------------
# GET single article by article_id
# --------------------------------------------------------
@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.article_id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


# --------------------------------------------------------
# GET all products with image URLs
# --------------------------------------------------------
@router.get("/products/", response_model=List[ProductOut])
def get_products_with_images(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .order_by(Article.article_id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert articles to ProductOut objects with image URLs
    products = [ProductOut.from_orm(article) for article in articles]
    return products


# --------------------------------------------------------
# GET single product with image URL
# --------------------------------------------------------
@router.get("/products/{product_id}", response_model=ProductOut)
def get_product_with_image(product_id: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.article_id == product_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductOut.from_orm(article)


# --------------------------------------------------------
# CREATE article (Admin only)
# --------------------------------------------------------
@router.post("/", response_model=ArticleResponse)
def create_article(
    payload: ArticleCreate, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    article = Article(**payload.dict())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


# --------------------------------------------------------
# UPDATE article (Admin only)
# --------------------------------------------------------
@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: str, 
    payload: ArticleUpdate, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.article_id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(article, key, value)

    db.commit()
    db.refresh(article)
    return article


# --------------------------------------------------------
# DELETE article (Admin only)
# --------------------------------------------------------
@router.delete("/{article_id}")
def delete_article(
    article_id: str, 
    current_admin: AdminResponse = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.article_id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.delete(article)
    db.commit()
    return {"message": "Article deleted successfully"}


# -----------------------------------------------------------------
# PERFORMANCE VIEW
# -----------------------------------------------------------------
@router.get("/{article_id}/performance", response_model=ArticlePerformanceResponse)
def get_performance(article_id: str, db: Session = Depends(get_db)):
    data = product_actions.get_article_performance(article_id, db)
    if not data:
        raise HTTPException(404, "Performance data not found")
    return data
#performance working

# -----------------------------------------------------------------
# DEMAND TREND VIEW
# -----------------------------------------------------------------
@router.get("/{article_id}/demand-trend", response_model=List[ArticleDemandTrendResponse])
def get_demand(article_id: str, db: Session = Depends(get_db)):
    return product_actions.get_demand_trend(article_id, db)

#demand is empty 

# -----------------------------------------------------------------
# INVENTORY STATUS VIEW
# -----------------------------------------------------------------
@router.get("/{article_id}/inventory", response_model=ArticleInventoryResponse)
def get_inventory(article_id: str, db: Session = Depends(get_db)):
    data = product_actions.get_inventory_status(article_id, db)
    if not data:
        raise HTTPException(404, "Inventory data not found")
    return data
#working correct

# -----------------------------------------------------------------
# FUNNEL METRICS VIEW
# -----------------------------------------------------------------
@router.get("/funnel-metrics", response_model=ArticleFunnelMetricsResponse)
def get_funnel_metrics(db: Session = Depends(get_db)):
    data = product_actions.get_funnel_metrics(db)

    if not data:
        raise HTTPException(status_code=404, detail="Funnel metrics not found")

    return data #not working 404 not found
