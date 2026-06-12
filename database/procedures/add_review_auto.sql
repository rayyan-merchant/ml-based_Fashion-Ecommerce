-- Insert Review Function (auto-rating)

CREATE OR REPLACE FUNCTION niche_data.add_review(
    p_customer_id VARCHAR,
    p_article_id VARCHAR,
    p_review_text TEXT
)
RETURNS VOID AS $$
DECLARE
    v_rating INT;
BEGIN
    -- Generate rating
    v_rating := niche_data.generate_rating_from_text(p_review_text);

    INSERT INTO niche_data.reviews (customer_id, article_id, rating, review_text, created_at)
    VALUES (p_customer_id, p_article_id, v_rating, p_review_text, NOW());
END;
$$ LANGUAGE plpgsql;
