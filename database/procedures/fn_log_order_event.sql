
CREATE OR REPLACE FUNCTION niche_data.fn_log_order_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO niche_data.events (customer_id, order_id, event_type, created_at)
    VALUES (
        NEW.customer_id,
        NEW.order_id,
        'order',
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_event_order
AFTER INSERT ON niche_data.orders
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_log_order_event();
