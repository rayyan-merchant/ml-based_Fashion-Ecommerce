CREATE OR REPLACE FUNCTION niche_data.get_filter_options(
    section_name TEXT,
    category_name TEXT
)
RETURNS TABLE (
    min_price NUMERIC,
    max_price NUMERIC,
    min_rating NUMERIC,
    max_rating NUMERIC,
    min_popularity BIGINT,
    max_popularity BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        MIN(price),
        MAX(price),
        MIN(average_rating),
        MAX(average_rating),
        MIN(popularity_score),
        MAX(popularity_score)
    FROM niche_data.get_category_products(section_name, category_name, 'popular');
END;
$$ LANGUAGE plpgsql STABLE;
