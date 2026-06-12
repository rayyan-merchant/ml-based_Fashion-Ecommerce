-- Admin Update Stock

CREATE OR REPLACE FUNCTION niche_data.admin_update_stock(
    p_admin_id INT,
    p_article_id TEXT,
    p_new_stock INT
) RETURNS BOOLEAN AS $$
DECLARE v_old_stock INT;
BEGIN
    SELECT stock INTO v_old_stock
    FROM niche_data.articles
    WHERE article_id = p_article_id;

    IF v_old_stock IS NULL THEN 
        RETURN FALSE;
    END IF;

    UPDATE niche_data.articles
    SET stock = p_new_stock,
        last_updated = NOW()
    WHERE article_id = p_article_id;

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'update_stock',
        jsonb_build_object(
            'article_id', p_article_id,
            'old_stock', v_old_stock,
            'new_stock', p_new_stock
        )
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;