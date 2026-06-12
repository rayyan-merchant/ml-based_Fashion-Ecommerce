-- create_order(customer_id, article_id, quantity)

CREATE OR REPLACE FUNCTION niche_data.create_order(
    p_customer_id VARCHAR,
    p_article_id VARCHAR,
    p_quantity INT
) 
RETURNS INTEGER AS $$
DECLARE
    v_price NUMERIC;
    v_total NUMERIC;
    v_order_id INTEGER;
BEGIN
    -- Get article price
    SELECT price INTO v_price
    FROM niche_data.articles
    WHERE article_id = p_article_id;

    IF v_price IS NULL THEN
        RAISE EXCEPTION 'Invalid article_id: %', p_article_id;
    END IF;

    -- Calculate total
    v_total := v_price * p_quantity;

    -- Create order
    INSERT INTO niche_data.orders (customer_id, order_date, total_amount, payment_status, shipping_address)
    VALUES (p_customer_id, NOW(), v_total, 'Pending', 'Auto-generated address')
    RETURNING order_id INTO v_order_id;

    -- Insert order item
    INSERT INTO niche_data.order_items (order_id, article_id, quantity, unit_price, line_total)
    VALUES (v_order_id, p_article_id, p_quantity, v_price, v_total);

    -- Decrease stock
    UPDATE niche_data.articles
    SET stock = GREATEST(stock - p_quantity, 0)
    WHERE article_id = p_article_id;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;
