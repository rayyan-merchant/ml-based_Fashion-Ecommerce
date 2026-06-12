
-- Admin Create Article (Add New Product)

CREATE OR REPLACE FUNCTION niche_data.admin_create_article(
    p_admin_id INT,
    p_article_id TEXT,
    p_name TEXT,
    p_price NUMERIC,
    p_stock INT,
    p_category INT
) RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO niche_data.articles(article_id, prod_name, price, stock, category_id, created_at)
    VALUES (p_article_id, p_name, p_price, p_stock, p_category, NOW());

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'create_article',
        jsonb_build_object(
            'article_id', p_article_id,
            'name', p_name,
            'price', p_price,
            'stock', p_stock,
            'category_id', p_category
        )
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
