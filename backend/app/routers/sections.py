# app/routers/sections.py  (REPLACE EXISTING FILE)

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.sections_schema import (
    ALLOWED_SECTIONS,
    ALLOWED_SORT_OPTIONS,
    CategoryProduct,
    CategoryProductsResponse,
    FilterOptions,
    FilterOptionsResponse,
    FilterRange,
    FilterSortProduct,
    FilterSortRequest,
    FilterSortResponse,
    PopularityRange,
    SectionCategoriesResponse,
    SectionCategorySummary,
    SectionProduct,
    SectionProductsResponse,
    SectionItem,
    SectionsResponse,
)
from app.utils.cache import cache_get, cache_set

router = APIRouter()


def _normalize_section_name(raw: str) -> str:
    """
    Map various frontend section labels (e.g. 'Men Shoes', 'Womens Casual')
    onto the canonical section keys used by the SQL functions.
    """
    s = (raw or "").strip().lower()
    if s in ALLOWED_SECTIONS:
        return s

    if "men" in s and "women" not in s and "lady" not in s and "ladies" not in s and "girl" not in s and "kid" not in s:
        return "men"
    if any(x in s for x in ["women", "woman", "ladies", "lady"]):
        return "women"
    if any(x in s for x in ["kid", "girl", "boy", "baby", "teen"]):
        return "kids"
    if "accessor" in s:
        return "accessories"
    if "unisex" in s:
        return "unisex"

    raise HTTPException(status_code=404, detail="Section not found")


def _validate_section(section_name: str) -> str:
    """Normalize and validate section names."""
    return _normalize_section_name(section_name)


def _normalize_sort_option(sort_option: str | None) -> str:
    """Normalize sort option (fallback to 'popular')."""
    if not sort_option:
        return "popular"
    if sort_option not in ALLOWED_SORT_OPTIONS:
        return "popular"
    return sort_option


@router.get("/", response_model=SectionsResponse)
def get_sections(db: Session = Depends(get_db)) -> SectionsResponse:
    cache_key = "sections:v1"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    sql = text("""
        SELECT *
        FROM (
            SELECT
                1 AS section_id,
                'men' AS section_name,
                'Men' AS display_name,
                COUNT(*) AS total_products
            FROM niche_data.articles a
            WHERE a.section_name ILIKE '%Men%'
               OR a.section_name ILIKE '%Boy%'
               OR a.section_name IN ('Men Underwear','Men Shoes','Mens Outerwear','Men H&M Sport')

            UNION ALL
            SELECT
                2, 'women', 'Women',
                COUNT(*) FROM niche_data.articles a
            WHERE a.section_name ILIKE '%Women%'
               OR a.section_name ILIKE '%Ladies%'
               OR a.section_name ILIKE 'H&M+%'
               OR a.section_name = 'Mama'

            UNION ALL
            SELECT
                3, 'kids', 'Kids',
                COUNT(*) FROM niche_data.articles a
            WHERE a.section_name ILIKE '%Kids%'
               OR a.section_name ILIKE '%Baby%'
               OR a.section_name IN ('Young Girl','Young Boy','Kids Boy','Kids Girl')

            UNION ALL
            SELECT
                4, 'unisex', 'Unisex',
                COUNT(*) FROM niche_data.articles a
            WHERE article_id NOT IN (
                SELECT article_id FROM niche_data.articles xa WHERE
                    xa.product_group_name = 'Accessories'
                    OR xa.section_name ILIKE '%Men%'
                    OR xa.section_name ILIKE '%Women%'
                    OR xa.section_name ILIKE '%Kids%'
                    OR xa.section_name ILIKE '%Boy%'
                    OR xa.section_name ILIKE '%Girl%'
                    OR xa.section_name ILIKE '%Baby%'
            )

            UNION ALL
            SELECT
                5, 'accessories', 'Accessories',
                COUNT(*) FROM niche_data.articles a
            WHERE a.product_group_name = 'Accessories'
        ) AS s
    """)
    rows = db.execute(sql).mappings().all()

    sections: List[SectionItem] = [
        SectionItem(
            id=row["section_id"],
            name=row["section_name"],
            display=row["display_name"],
            total_products=int(row["total_products"]),
        )
        for row in rows
    ]

    response = SectionsResponse(sections=sections)
    cache_set(cache_key, response, ttl_seconds=24 * 60 * 60)
    return response


@router.get("/{section_name}/products", response_model=SectionProductsResponse)
def get_section_products(
    section_name: str,
    db: Session = Depends(get_db),
    limit: int = Query(24, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> SectionProductsResponse:
    section = _validate_section(section_name)

    cache_key = f"section_products:v1:{section}:{limit}:{offset}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Replaced stored procedure with direct SQL to fix ambiguous column error
    sql = text("""
        SELECT
            a.article_id,
            a.prod_name,
            a.price,
            CASE
                WHEN a.product_type_name = 'Hoodie' THEN 'hoodie'
                WHEN a.product_type_name = 'Jacket' THEN 'jacket'
                WHEN a.product_type_name = 'Beanie' THEN 'beanie'
                WHEN a.product_type_name = 'Trousers'
                     AND a.section_name IN ('Denim Men','Ladies Denim')
                     THEN 'trouser'
                WHEN a.product_group_name = 'Accessories' THEN 'accessory'
                ELSE 'other'
            END AS category,
            a.section_name,
            a.stock,
            (SELECT AVG(r.rating)::NUMERIC
             FROM niche_data.reviews r
             WHERE r.article_id = a.article_id) AS average_rating,
            (SELECT COUNT(*) FROM niche_data.reviews r
             WHERE r.article_id = a.article_id) AS total_reviews,
            (SELECT COUNT(*) FROM niche_data.transactions t
             WHERE t.article_id = a.article_id) AS popularity_score
        FROM niche_data.articles a
        WHERE
            (:section_name = 'men' AND (
                a.section_name ILIKE '%Men%'
                OR a.section_name ILIKE '%Boy%'
                OR a.section_name IN ('Men Underwear','Men Shoes','Mens Outerwear','Men H&M Sport')
            ))
            OR (:section_name = 'women' AND (
                a.section_name ILIKE '%Women%'
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
            OR (:section_name = 'unisex' AND a.product_group_name <> 'Accessories')
        LIMIT :limit OFFSET :offset
    """)
    
    rows = db.execute(sql, {"section_name": section, "limit": limit, "offset": offset}).mappings().all()

    # Calculate total for pagination (separate count query)
    count_sql = text("""
        SELECT COUNT(*) 
        FROM niche_data.articles a
        WHERE
            (:section_name = 'men' AND (
                a.section_name ILIKE '%Men%'
                OR a.section_name ILIKE '%Boy%'
                OR a.section_name IN ('Men Underwear','Men Shoes','Mens Outerwear','Men H&M Sport')
            ))
            OR (:section_name = 'women' AND (
                a.section_name ILIKE '%Women%'
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
            OR (:section_name = 'unisex' AND a.product_group_name <> 'Accessories')
    """)
    total_products = db.execute(count_sql, {"section_name": section}).scalar()

    products: List[SectionProduct] = [
        SectionProduct(
            article_id=row["article_id"],
            prod_name=row["prod_name"],
            price=float(row["price"]),
            category=row.get("category"),
            section_name=row.get("section_name"), # Accessing the aliased column
            stock=row.get("stock"),
            average_rating=float(row["average_rating"]) if row["average_rating"] is not None else None,
            total_reviews=row.get("total_reviews", 0),
            popularity_score=row.get("popularity_score", 0),
            image_path=f"0{row['article_id']}.jpg"  # Generate image path from article_id
        )
        for row in rows
    ]

    response = SectionProductsResponse(
        section=section,
        total_products=total_products,
        products=products,
    )
    cache_set(cache_key, response, ttl_seconds=30)
    return response


@router.get("/{section_name}/categories", response_model=SectionCategoriesResponse)
def get_section_categories(
    section_name: str,
    db: Session = Depends(get_db),
) -> SectionCategoriesResponse:
    section = _validate_section(section_name)

    cache_key = f"section_categories:v1:{section}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    sql = text("SELECT * FROM niche_data.get_section_categories(:section_name)")
    rows = db.execute(sql, {"section_name": section}).mappings().all()

    categories: List[SectionCategorySummary] = [
        SectionCategorySummary(
            category=row["category_name"],
            total_products=int(row["total_products"]),
        )
        for row in rows
    ]

    response = SectionCategoriesResponse(section=section, categories=categories)
    cache_set(cache_key, response, ttl_seconds=60 * 60)
    return response


@router.get("/{section_name}/{category_name}/products", response_model=CategoryProductsResponse)
def get_category_products(
    section_name: str,
    category_name: str,
    sort: str | None = Query("popular"),
    db: Session = Depends(get_db),
    limit: int = Query(24, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> CategoryProductsResponse:
    """
    Accept ANY category_name (no static whitelist). The DB function will return rows
    or an empty list if none exist for that (section, category).
    """
    section = _validate_section(section_name)
    sort_option = _normalize_sort_option(sort)

    cache_key = f"category_products:v1:{section}:{category_name}:{sort_option}:{limit}:{offset}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    sql = text(
        """
        SELECT * 
        FROM niche_data.get_category_products(:section_name, :category_name, :sort_option)
        """
    )
    rows = db.execute(
        sql,
        {"section_name": section, "category_name": category_name, "sort_option": sort_option},
    ).mappings().all()

    total = len(rows)
    window = rows[offset : offset + limit]

    products: List[CategoryProduct] = [
        CategoryProduct(
            article_id=row["article_id"],
            prod_name=row["prod_name"],
            price=float(row["price"]),
            stock=row.get("stock", 0),
            average_rating=float(row["average_rating"]) if row["average_rating"] is not None else None,
            total_reviews=row.get("total_reviews", 0),
            popularity_score=row.get("popularity_score", 0),
            image_path=f"0{row['article_id']}.jpg"  # Generate image path from article_id
        )
        for row in window
    ]

    response = CategoryProductsResponse(
        section=section,
        category=category_name,
        sorting=sort_option,
        total_products=total,
        products=products,
    )
    cache_set(cache_key, response, ttl_seconds=20)
    return response


@router.get("/{section_name}/{category_name}/filters", response_model=FilterOptionsResponse)
def get_filter_options(
    section_name: str,
    category_name: str,
    db: Session = Depends(get_db),
) -> FilterOptionsResponse:
    section = _validate_section(section_name)

    cache_key = f"filter_options:v1:{section}:{category_name}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    sql = text(
        """
        SELECT * 
        FROM niche_data.get_filter_options(:section_name, :category_name)
        """
    )
    row = db.execute(
        sql, {"section_name": section, "category_name": category_name}
    ).mappings().first()

    if not row:
        filters = FilterOptions(
            price=FilterRange(min=None, max=None),
            rating=FilterRange(min=None, max=None),
            popularity=PopularityRange(min=None, max=None),
        )
    else:
        filters = FilterOptions(
            price=FilterRange(
                min=float(row["min_price"]) if row["min_price"] is not None else None,
                max=float(row["max_price"]) if row["max_price"] is not None else None,
            ),
            rating=FilterRange(
                min=float(row["min_rating"]) if row["min_rating"] is not None else None,
                max=float(row["max_rating"]) if row["max_rating"] is not None else None,
            ),
            popularity=PopularityRange(
                min=int(row["min_popularity"]) if row["min_popularity"] is not None else None,
                max=int(row["max_popularity"]) if row["max_popularity"] is not None else None,
            ),
        )

    response = FilterOptionsResponse(category=category_name, filters=filters)
    cache_set(cache_key, response, ttl_seconds=5 * 60)
    return response


@router.post("/{section_name}/{category_name}/filter-sort", response_model=FilterSortResponse)
def filter_and_sort_products(
    section_name: str,
    category_name: str,
    payload: FilterSortRequest,
    db: Session = Depends(get_db),
) -> FilterSortResponse:
    section = _validate_section(section_name)

    if payload.price_max < payload.price_min:
        raise HTTPException(status_code=400, detail="price_max must be >= price_min")

    sort_option = _normalize_sort_option(payload.sort_option)

    sql = text(
        """
        SELECT *
        FROM niche_data.filter_and_sort_products(
            :section_name,
            :category_name,
            :price_min,
            :price_max,
            :sort_option
        )
        """
    )
    rows = db.execute(
        sql,
        {
            "section_name": section,
            "category_name": category_name,
            "price_min": payload.price_min,
            "price_max": payload.price_max,
            "sort_option": sort_option,
        },
    ).mappings().all()

    products: List[FilterSortProduct] = [
        FilterSortProduct(
            article_id=row["article_id"],
            prod_name=row["prod_name"],
            price=float(row["price"]),
            stock=row.get("stock", 0),
            average_rating=float(row["average_rating"]) if row["average_rating"] is not None else None,
            total_reviews=row.get("total_reviews", 0),
            popularity_score=row.get("popularity_score", 0),
            image_path=f"0{row['article_id']}.jpg"  # Generate image path from article_id
        )
        for row in rows
    ]

    return FilterSortResponse(products=products)
