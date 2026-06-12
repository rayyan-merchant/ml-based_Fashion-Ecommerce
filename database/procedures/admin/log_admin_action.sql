-- Admin Logging function

CREATE OR REPLACE FUNCTION niche_data.log_admin_action(
    p_admin_id INT,
    p_action TEXT,
    p_details JSONB DEFAULT '{}'::jsonb
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO niche_data.admin_activity_log(admin_id, action, details)
    VALUES (p_admin_id, p_action, p_details);
END;
$$ LANGUAGE plpgsql;