-- Stock Management Trigger

-- Auto-Reduce Stock on Order Item Insert

CREATE OR REPLACE FUNCTION niche_data.fn_reduce_stock()
RETURNS TRIGGER AS $$
BEGIN
    -- Reduce stock
    UPDATE niche_data.articles
    SET stock = stock - NEW.quantity,
        last_updated = NOW()
    WHERE article_id = NEW.article_id;

    -- Check if stock <= 0 → mark out of stock
    UPDATE niche_data.articles
    SET stock = 0
    WHERE article_id = NEW.article_id AND stock < 0;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trg_reduce_stock
AFTER INSERT ON niche_data.order_items
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_reduce_stock();
