-- Function: Add order item (with stock update)

CREATE OR REPLACE FUNCTION niche_data.add_order_item(
    p_order_id INT,
    p_article_id VARCHAR,
    p_qty INT
)
RETURNS VOID AS $$
DECLARE
    v_price NUMERIC;
BEGIN
    SELECT price INTO v_price
    FROM niche_data.articles
    WHERE article_id = p_article_id;

    INSERT INTO niche_data.order_items(order_id, article_id, quantity, unit_price, line_total)
    VALUES (p_order_id, p_article_id, p_qty, v_price, p_price * p_qty);

    -- Update stock
    UPDATE niche_data.articles
    SET stock = GREATEST(stock - p_qty, 0)
    WHERE article_id = p_article_id;

    -- Recalculate total
    PERFORM niche_data.recalculate_order_total(p_order_id);
END;
$$ LANGUAGE plpgsql;
