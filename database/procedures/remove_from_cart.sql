-- Remove from cart

CREATE OR REPLACE FUNCTION niche_data.remove_from_cart(
    p_customer_id VARCHAR,
    p_article_id VARCHAR
)
RETURNS VOID AS $$
BEGIN
    DELETE FROM niche_data.cart
    WHERE customer_id = p_customer_id
      AND article_id = p_article_id;
END;
$$ LANGUAGE plpgsql;
