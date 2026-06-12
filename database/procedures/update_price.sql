-- Update Price

CREATE OR REPLACE FUNCTION niche_data.update_price(
    p_article_id VARCHAR,
    p_new_price NUMERIC
)
RETURNS VOID AS $$
BEGIN
    UPDATE niche_data.articles
    SET price = p_new_price,
        last_updated = NOW()
    WHERE article_id = p_article_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Article % does not exist', p_article_id;
    END IF;
END;
$$ LANGUAGE plpgsql;
