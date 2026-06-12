-- Admin login verification

CREATE OR REPLACE FUNCTION niche_data.admin_login(
    p_username TEXT,
    p_password TEXT
)
RETURNS TABLE (
    admin_id INT,
    username TEXT,
    email TEXT,
    last_login_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    WITH matched AS (
        SELECT 
            a.admin_id, a.username, a.email, a.last_login_at
        FROM niche_data.admins a
        WHERE a.username = p_username
          AND a.password_hash = crypt(p_password, a.password_hash)
          AND a.is_active = TRUE
    )
    UPDATE niche_data.admins 
    SET last_login_at = NOW()
    WHERE admins.admin_id = (SELECT admin_id FROM matched)
    RETURNING admin_id, username, email, NEW.last_login_at;

END;
$$ LANGUAGE plpgsql;


-- Backend simply checks: if result has a row → login successful