-- PROCESS CHECKOUT

CREATE OR REPLACE FUNCTION niche_data.process_checkout(p_customer_id VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_order_id INTEGER;
    v_total NUMERIC(12,2);
BEGIN
    
	-- 1. Validate cart not empty
    IF NOT EXISTS (
        SELECT 1 FROM niche_data.cart WHERE customer_id = p_customer_id
    ) THEN
        RAISE EXCEPTION 'Cart is empty';
    END IF;

    -- 2. CREATE NEW ORDER
    INSERT INTO niche_data.orders (customer_id, order_date, payment_status, total_amount, shipping_address)
    VALUES (p_customer_id, NOW(), 'Pending', 0, 'Default Address')
    RETURNING order_id INTO v_order_id;

    -- 3. INSERT ORDER ITEMS + CHECK STOCK + DECREASE STOCK
    INSERT INTO niche_data.order_items (order_id, article_id, quantity, unit_price)
    SELECT 
        v_order_id,
        c.article_id,
        c.quantity,
        a.price
    FROM niche_data.cart c
    JOIN niche_data.articles a USING (article_id);

    -- 4. VALIDATE STOCK & REDUCE
    UPDATE niche_data.articles a
    SET stock = a.stock - c.quantity,
        last_updated = NOW()
    FROM niche_data.cart c
    WHERE a.article_id = c.article_id
      AND c.customer_id = p_customer_id
      AND a.stock >= c.quantity;

    -- If any article went negative stock → rollback
    IF EXISTS (
        SELECT 1 FROM niche_data.articles a
        JOIN niche_data.cart c USING(article_id)
        WHERE a.stock < 0 AND c.customer_id = p_customer_id
    ) THEN
        RAISE EXCEPTION 'Insufficient stock for one or more items.';
    END IF;

    -- 5. UPDATE ORDER TOTAL
    SELECT COALESCE(SUM(line_total),0)
    INTO v_total
    FROM niche_data.order_items
    WHERE order_id = v_order_id;

    UPDATE niche_data.orders
    SET total_amount = v_total
    WHERE order_id = v_order_id;

    -- 6. CLEAR CART
    DELETE FROM niche_data.cart WHERE customer_id = p_customer_id;

    -- 7. RECORD CHECKOUT EVENT
    INSERT INTO niche_data.events (customer_id, event_type, created_at)
    VALUES (p_customer_id, 'checkout', NOW());

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;
