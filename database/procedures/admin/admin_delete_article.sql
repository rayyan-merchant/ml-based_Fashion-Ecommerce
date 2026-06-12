-- Admin Remove Article

CREATE OR REPLACE FUNCTION niche_data.admin_delete_article(
    p_admin_id INT,
    p_article_id TEXT
) RETURNS BOOLEAN AS $$
DECLARE v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM niche_data.articles WHERE article_id = p_article_id
    ) INTO v_exists;

    IF NOT v_exists THEN RETURN FALSE; END IF;

    DELETE FROM niche_data.articles WHERE article_id = p_article_id;

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'delete_article',
        jsonb_build_object('article_id', p_article_id)
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;