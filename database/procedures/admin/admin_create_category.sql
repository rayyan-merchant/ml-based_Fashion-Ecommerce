-- Admin Create Category

CREATE OR REPLACE FUNCTION niche_data.admin_create_category(
    p_admin_id INT,
    p_name TEXT,
    p_parent INT DEFAULT NULL
) RETURNS INT AS $$
DECLARE v_new_id INT;
BEGIN
    INSERT INTO niche_data.categories(name, parent_category_id)
    VALUES (p_name, p_parent)
    RETURNING category_id INTO v_new_id;

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'create_category',
        jsonb_build_object(
            'category_id', v_new_id,
            'name', p_name,
            'parent', p_parent
        )
    );

    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;