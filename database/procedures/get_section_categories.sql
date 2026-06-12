CREATE OR REPLACE FUNCTION niche_data.get_section_categories(p_section_name TEXT)
RETURNS TABLE (
    category_name TEXT,
    total_products BIGINT
) AS $$
BEGIN
    /*
      Derive high-level categories for a given section by delegating to
      niche_data.get_section_products(p_section_name) and aggregating on the
      already-computed "category" column.
    */
    RETURN QUERY
    SELECT
        category AS category_name,
        COUNT(*) AS total_products
    FROM niche_data.get_section_products(p_section_name)
    WHERE category IS NOT NULL
      AND category <> 'other'
    GROUP BY category;
END;
$$ LANGUAGE plpgsql STABLE;
