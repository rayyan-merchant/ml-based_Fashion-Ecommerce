-- Trigger to update stock automatically

CREATE OR REPLACE FUNCTION niche_data.update_stock_after_order()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE niche_data.articles
    SET stock = GREATEST(stock - NEW.quantity, 0)
    WHERE article_id = NEW.article_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_stock
AFTER INSERT ON niche_data.order_items
FOR EACH ROW
EXECUTE FUNCTION niche_data.update_stock_after_order();
