-- Function: Update Order Total --> If you ever modify order_items later.

CREATE OR REPLACE FUNCTION niche_data.recalculate_order_total(p_order_id INT)
RETURNS VOID AS $$
BEGIN
    UPDATE niche_data.orders
    SET total_amount = (
        SELECT SUM(line_total)
        FROM niche_data.order_items
        WHERE order_id = p_order_id
    )
    WHERE order_id = p_order_id;
END;
$$ LANGUAGE plpgsql;
