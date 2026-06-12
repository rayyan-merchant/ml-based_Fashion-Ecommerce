drop function niche_data.get_section_products

CREATE OR REPLACE FUNCTION niche_data.get_section_products(p_section_name TEXT)
RETURNS TABLE (
    article_id TEXT,
    prod_name TEXT,
    price NUMERIC,
    category TEXT,
    final_section TEXT,
    stock INT,
    average_rating NUMERIC,
    total_reviews INT,
    popularity_score BIGINT,
    image_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.article_id::TEXT,
        a.prod_name::TEXT,
        a.price::NUMERIC,

        CASE 
            WHEN a.product_type_name = 'Hoodie' THEN 'hoodie'
            WHEN a.product_type_name = 'Jacket' THEN 'jacket'
            WHEN a.product_type_name = 'Beanie' THEN 'beanie'
            WHEN a.product_type_name = 'Trousers'
                 AND (a.section_name ILIKE '%Men%' 
                  OR a.section_name ILIKE '%Women%' 
                  OR a.section_name ILIKE '%Ladies%' 
                  OR a.section_name ILIKE '%Boy%' 
                  OR a.section_name ILIKE '%Girl%' 
                  OR a.section_name ILIKE '%Baby%' 
                  OR a.section_name ILIKE '%Kids%')
                 THEN 'trouser'
            WHEN a.product_group_name = 'Accessories' THEN 'accessory'
            ELSE 'other'
        END AS category,

        p_section_name AS final_section,

        a.stock::INT,

        (SELECT AVG(r.rating)::NUMERIC 
         FROM niche_data.reviews r 
         WHERE r.article_id = a.article_id) AS average_rating,

        (SELECT COUNT(*)::INT 
         FROM niche_data.reviews r 
         WHERE r.article_id = a.article_id) AS total_reviews,

        (SELECT COUNT(*) 
         FROM niche_data.transactions t
         WHERE t.article_id = a.article_id) AS popularity_score,

        a.image_path::TEXT

    FROM niche_data.articles a
    WHERE 
        (p_section_name = 'men' AND (
            a.section_name ILIKE '%Men%'
            OR a.section_name ILIKE '%Boy%'
            OR a.section_name IN ('Men Underwear','Men Shoes','Mens Outerwear','Men H&M Sport')
        ))
        OR (p_section_name = 'women' AND (
            a.section_name ILIKE '%Women%'
            OR a.section_name ILIKE '%Ladies%'
            OR a.section_name ILIKE 'H&M+%'
            OR a.section_name = 'Mama'
        ))
        OR (p_section_name = 'kids' AND (
            a.section_name ILIKE '%Kids%'
            OR a.section_name ILIKE '%Baby%'
            OR a.section_name IN ('Young Girl','Young Boy','Kids Boy','Kids Girl')
        ))
        OR (p_section_name = 'accessories' AND a.product_group_name = 'Accessories')
        OR (p_section_name = 'unisex' AND a.product_group_name <> 'Accessories');
END;
$$ LANGUAGE plpgsql STABLE;

