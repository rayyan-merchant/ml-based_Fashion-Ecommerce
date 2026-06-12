-- Admin Refresh Materialized Views

CREATE OR REPLACE FUNCTION niche_data.admin_refresh_matviews(
    p_admin_id INT
)
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW niche_data.mv_customer_clv;
    REFRESH MATERIALIZED VIEW niche_data.mv_rfm;
    REFRESH MATERIALIZED VIEW niche_data.mv_product_demand;
    REFRESH MATERIALIZED VIEW niche_data.mv_daily_sales;
    REFRESH MATERIALIZED VIEW niche_data.mv_monthly_sales;

    PERFORM niche_data.log_admin_action(
        p_admin_id,
        'refresh_materialized_views',
        '{"status":"completed"}'::jsonb
    );
END;
$$ LANGUAGE plpgsql;