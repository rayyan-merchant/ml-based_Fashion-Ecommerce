CREATE OR REPLACE FUNCTION niche_data.get_sections()
RETURNS TABLE (
    section_id INT,
    section_name TEXT,
    display_name TEXT,
    total_products BIGINT
) AS $$
BEGIN
    RETURN QUERY
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
            COUNT(*) FROM niche_data.articles a2
        WHERE a2.section_name ILIKE '%Women%'
           OR a2.section_name ILIKE '%Ladies%'
           OR a2.section_name ILIKE 'H&M+%'
           OR a2.section_name = 'Mama'

        UNION ALL
        SELECT
            3, 'kids', 'Kids',
            COUNT(*) FROM niche_data.articles a3
        WHERE a3.section_name ILIKE '%Kids%'
           OR a3.section_name ILIKE '%Baby%'
           OR a3.section_name IN ('Young Girl','Young Boy','Kids Boy','Kids Girl')

        UNION ALL
        SELECT
            4, 'unisex', 'Unisex',
            COUNT(*) FROM niche_data.articles a4
        WHERE a4.article_id NOT IN (
            SELECT a_sub.article_id FROM niche_data.articles a_sub WHERE
                a_sub.product_group_name = 'Accessories'
                OR a_sub.section_name ILIKE '%Men%'
                OR a_sub.section_name ILIKE '%Women%'
                OR a_sub.section_name ILIKE '%Kids%'
                OR a_sub.section_name ILIKE '%Boy%'
                OR a_sub.section_name ILIKE '%Girl%'
                OR a_sub.section_name ILIKE '%Baby%'
        )

        UNION ALL
        SELECT
            5, 'accessories', 'Accessories',
            COUNT(*) FROM niche_data.articles a5
        WHERE a5.product_group_name = 'Accessories'
    ) AS s;
END;
$$ LANGUAGE plpgsql STABLE;
