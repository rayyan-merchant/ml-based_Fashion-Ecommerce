-- Trigger to log order status changes

CREATE OR REPLACE FUNCTION niche_data.log_order_status()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO niche_data.events (
        session_id, customer_id, article_id, event_type, event_time
    )
    VALUES (
        md5(random()::text || clock_timestamp()::text),
        NEW.customer_id,
        NULL,
        'order_status_changed',
        NOW()
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_order_status
AFTER UPDATE OF payment_status ON niche_data.orders
FOR EACH ROW
WHEN (OLD.payment_status IS DISTINCT FROM NEW.payment_status)
EXECUTE FUNCTION niche_data.log_order_status();
