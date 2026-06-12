-- Admin Update Product Price

CREATE OR REPLACE FUNCTION niche_data.admin_update_price(
    p_admin_id INT,
    p_article_id TEXT,
    p_new_price NUMERIC
) RETURNS BOOLEAN AS $$
DECLARE v_old_price NUMERIC;
BEGIN
    SELECT price INTO v_old_price
    FROM niche_data.articles
    WHERE article_id = p_article_id;

    IF v_old_price IS NULL THEN 
        RETURN FALSE;
    END IF;

    UPDATE niche_data.articles
    SET price = p_new_price,
        last_updated = NOW()
    WHERE article_id = p_article_id;

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'update_price',
        jsonb_build_object(
            'article_id', p_article_id,
            'old_price', v_old_price,
            'new_price', p_new_price
        )
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Includes logging & validation.