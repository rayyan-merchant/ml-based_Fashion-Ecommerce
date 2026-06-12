-- Clear Cart After Checkout

CREATE OR REPLACE FUNCTION niche_data.clear_cart(
    p_customer_id VARCHAR
)
RETURNS VOID AS $$
BEGIN
    DELETE FROM niche_data.cart
    WHERE customer_id = p_customer_id;
END;
$$ LANGUAGE plpgsql;
