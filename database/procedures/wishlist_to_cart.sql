-- Move from Wishlist to Cart

CREATE OR REPLACE FUNCTION niche_data.wishlist_to_cart(
    p_customer_id VARCHAR,
    p_article_id VARCHAR
)
RETURNS VOID AS $$
BEGIN
    -- Insert into cart (increase qty if exists)
    INSERT INTO niche_data.cart(customer_id, article_id, quantity)
    VALUES (p_customer_id, p_article_id, 1)
    ON CONFLICT (customer_id, article_id)
    DO UPDATE SET quantity = niche_data.cart.quantity + 1;

    -- Remove from wishlist
    DELETE FROM niche_data.wishlist
    WHERE customer_id = p_customer_id
      AND article_id = p_article_id;
END;
$$ LANGUAGE plpgsql;
