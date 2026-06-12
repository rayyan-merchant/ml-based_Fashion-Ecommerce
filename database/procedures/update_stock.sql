-- Update Stock Procedure

CREATE OR REPLACE FUNCTION niche_data.update_stock(
    p_article_id VARCHAR,
    p_new_stock INTEGER
)
RETURNS VOID AS $$
BEGIN
    UPDATE niche_data.articles
    SET stock = p_new_stock,
        last_updated = NOW()
    WHERE article_id = p_article_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Article % does not exist', p_article_id;
    END IF;
END;
$$ LANGUAGE plpgsql;
