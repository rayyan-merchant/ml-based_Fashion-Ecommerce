-- Log customer activity into event table

CREATE OR REPLACE FUNCTION niche_data.fn_log_customer_event()
RETURNS TRIGGER AS $$
DECLARE
    event_customer_id TEXT;
    event_article_id TEXT;
BEGIN
    IF TG_TABLE_NAME = 'order_items' THEN
        SELECT customer_id
        INTO event_customer_id
        FROM niche_data.orders
        WHERE order_id = NEW.order_id;

        event_article_id := NEW.article_id;
    ELSE
        event_customer_id := NEW.customer_id;
        event_article_id := COALESCE(NEW.article_id, NULL);
    END IF;

    INSERT INTO niche_data.events (customer_id, article_id, event_type, created_at)
    VALUES (
        event_customer_id,
        event_article_id,
        TG_ARGV[0],     -- event type passed in trigger
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION niche_data.fn_log_customer_event()
RETURNS TRIGGER AS $$
DECLARE
    event_customer_id TEXT;
    event_article_id TEXT;
BEGIN
    IF TG_TABLE_NAME = 'order_items' THEN
        SELECT customer_id
        INTO event_customer_id
        FROM niche_data.orders
        WHERE order_id = NEW.order_id;

        event_article_id := NEW.article_id;
    ELSE
        event_customer_id := NEW.customer_id;
        event_article_id := COALESCE(NEW.article_id, NULL);
    END IF;

    INSERT INTO niche_data.events (customer_id, article_id, event_type, created_at)
    VALUES (
        event_customer_id,
        event_article_id,
        TG_ARGV[0],     -- event type passed in trigger
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_event_review
AFTER INSERT ON niche_data.reviews
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_log_customer_event('review');


CREATE TRIGGER trg_event_wishlist
AFTER INSERT ON niche_data.wishlist
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_log_customer_event('wishlist');


CREATE TRIGGER trg_event_add_to_cart
AFTER INSERT OR UPDATE ON niche_data.cart
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_log_customer_event('add_to_cart');



CREATE TRIGGER trg_event_order_item
AFTER INSERT ON niche_data.order_items
FOR EACH ROW
EXECUTE FUNCTION niche_data.fn_log_customer_event('order_item');
