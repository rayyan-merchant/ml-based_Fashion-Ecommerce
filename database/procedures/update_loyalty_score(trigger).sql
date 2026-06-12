-- Update loyalty score


CREATE OR REPLACE FUNCTION niche_data.update_loyalty_score()
RETURNS trigger AS $$
DECLARE
    p_customer_id VARCHAR := NEW.customer_id;

    v_purchase_points NUMERIC;
    v_review_points NUMERIC;
    v_wishlist_points NUMERIC;
    v_total NUMERIC;
BEGIN
    -- 1. Points from purchases
    SELECT COALESCE(SUM(total_amount), 0)
    INTO v_purchase_points
    FROM niche_data.orders
    WHERE customer_id = p_customer_id;

    -- 2. Points from reviews
    SELECT COALESCE(SUM(
        CASE 
            WHEN rating = 5 THEN 5
            WHEN rating = 4 THEN 3
            WHEN rating = 3 THEN 1
            ELSE 0
        END
    ), 0)
    INTO v_review_points
    FROM niche_data.reviews
    WHERE customer_id = p_customer_id;

    -- 3. Points from wishlist
    SELECT COUNT(*) * 0.5
    INTO v_wishlist_points
    FROM niche_data.wishlist
    WHERE customer_id = p_customer_id;

    v_total := v_purchase_points + v_review_points + v_wishlist_points;

    UPDATE niche_data.customers
    SET loyalty_score = v_total
    WHERE customer_id = p_customer_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trg_loyalty_after_order
AFTER INSERT ON niche_data.orders
FOR EACH ROW
EXECUTE FUNCTION niche_data.update_loyalty_score();

CREATE TRIGGER trg_loyalty_after_review
AFTER INSERT ON niche_data.reviews
FOR EACH ROW
EXECUTE FUNCTION niche_data.update_loyalty_score();

CREATE TRIGGER trg_loyalty_after_wishlist
AFTER INSERT ON niche_data.wishlist
FOR EACH ROW
EXECUTE FUNCTION niche_data.update_loyalty_score();

