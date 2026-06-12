-- Admin Delete Review

CREATE OR REPLACE FUNCTION niche_data.admin_delete_review(
    p_admin_id INT,
    p_review_id INT
) RETURNS BOOLEAN AS $$
DECLARE v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM niche_data.reviews WHERE review_id = p_review_id
    ) INTO v_exists;

    IF NOT v_exists THEN RETURN FALSE; END IF;

    DELETE FROM niche_data.reviews WHERE review_id = p_review_id;

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'delete_review',
        jsonb_build_object('review_id', p_review_id)
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;