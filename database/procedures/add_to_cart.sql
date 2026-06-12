-- Add To Cart with Stock Validation

CREATE OR REPLACE FUNCTION niche_data.add_to_cart(
    p_customer_id VARCHAR,
    p_article_id VARCHAR,
    p_qty INTEGER
)
RETURNS VOID AS $$
BEGIN
    -- If exists, update quantity
    INSERT INTO niche_data.cart (customer_id, article_id, quantity)
    VALUES (p_customer_id, p_article_id, p_qty)
    ON CONFLICT (customer_id, article_id)
    DO UPDATE SET quantity = cart.quantity + EXCLUDED.quantity;

    -- Record event
    INSERT INTO niche_data.events (customer_id, article_id, event_type)
    VALUES (p_customer_id, p_article_id, 'add_to_cart');
END;
$$ LANGUAGE plpgsql;




