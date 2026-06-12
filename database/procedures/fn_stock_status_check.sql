-- Trigger: Mark Out-of-Stock When Updated

CREATE OR REPLACE FUNCTION niche_data.fn_stock_status_check()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.stock <= 0 THEN
        NEW.stock := 0;  -- prevent negative stock
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_stock_status_check
BEFORE UPDATE ON niche_data.articles
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_stock_status_check();
