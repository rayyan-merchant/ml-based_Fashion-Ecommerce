WITH cat AS (
    SELECT 
        c1.category_id,
        c1.name AS category_name,
        c1.parent_category_id,
        CASE
            WHEN c1.parent_category_id IS NULL THEN 0
            WHEN c2.parent_category_id IS NULL THEN 1
            ELSE 2
        END AS category_depth
    FROM categories c1
    LEFT JOIN categories c2 ON c1.parent_category_id = c2.category_id
)

SELECT 
    a.article_id,
    a.product_code,
    a.prod_name,
    a.product_type_name,
    a.product_group_name,
    a.graphical_appearance_name,
    a.colour_group_name,
    a.department_name,
    a.index_name,
    a.section_name,
    a.garment_group_name,
    a.detail_desc,
    a.created_at,
    a.last_updated,
    a.price,
    a.stock,
    a.category_id,
    
    -- Category extra data
    cat.category_name,
    cat.parent_category_id,
    cat.category_depth,
    
    -- Lifecycle feature
    EXTRACT(DAY FROM (CURRENT_DATE - a.created_at)) AS lifecycle_days

FROM articles a
LEFT JOIN cat ON a.category_id = cat.category_id;

