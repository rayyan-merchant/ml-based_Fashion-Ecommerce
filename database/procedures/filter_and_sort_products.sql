drop function niche_data.filter_and_sort_products

CREATE OR REPLACE FUNCTION niche_data.filter_and_sort_products(
    p_section_name TEXT,
    p_category_name TEXT,
    p_price_min NUMERIC,
    p_price_max NUMERIC,
    p_sort_option TEXT
)
RETURNS TABLE (
    article_id TEXT,
    prod_name TEXT,
    price NUMERIC,
    stock INT,
    average_rating NUMERIC,
    total_reviews INT,
    popularity_score BIGINT,
	image_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH base AS (
        SELECT *
        FROM niche_data.get_category_products(
            p_section_name,
            p_category_name,
            p_sort_option
        )
    )
    SELECT
        base.article_id,
        base.prod_name,
        base.price,
        base.stock,
        base.average_rating,
        base.total_reviews,
        base.popularity_score,
		base.image_path
    FROM base
    WHERE base.price BETWEEN p_price_min AND p_price_max
    ORDER BY
        CASE WHEN p_sort_option = 'price_low_high' THEN base.price END ASC,
        CASE WHEN p_sort_option = 'price_high_low' THEN base.price END DESC,
        CASE WHEN p_sort_option = 'popular' THEN base.popularity_score END DESC,
        CASE WHEN p_sort_option = 'newest' THEN base.article_id END DESC,
        CASE WHEN p_sort_option = 'best_rated' THEN base.average_rating END DESC;
END;
$$ LANGUAGE plpgsql STABLE;
