-- Add to Wishlist
CREATE OR REPLACE FUNCTION niche_data.add_to_wishlist(
    p_customer_id VARCHAR,
    p_article_id VARCHAR
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO niche_data.wishlist (customer_id, article_id)
    VALUES (p_customer_id, p_article_id)
    ON CONFLICT (customer_id, article_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql;
