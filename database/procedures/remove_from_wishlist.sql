-- Remove from Wishlist

CREATE OR REPLACE FUNCTION niche_data.remove_from_wishlist(
    p_customer_id VARCHAR,
    p_article_id VARCHAR
)
RETURNS VOID AS $$
BEGIN
    DELETE FROM niche_data.wishlist
    WHERE customer_id = p_customer_id
      AND article_id = p_article_id;
END;
$$ LANGUAGE plpgsql;
