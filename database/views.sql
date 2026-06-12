-- EVENT PRE-AGGREGATION (CRITICAL LAYER)

DROP MATERIALIZED VIEW IF EXISTS niche_data.event_aggregates CASCADE;

CREATE MATERIALIZED VIEW niche_data.event_aggregates AS
SELECT 
    article_id,
    COUNT(*) FILTER (WHERE event_type = 'view') AS total_views,
    COUNT(*) FILTER (WHERE event_type = 'click') AS total_clicks,
    COUNT(*) FILTER (WHERE event_type = 'wishlist') AS total_wishlist,
    COUNT(*) FILTER (WHERE event_type = 'add_to_cart') AS total_cart_adds,
    COUNT(*) FILTER (WHERE event_type = 'purchase') AS total_purchases
FROM niche_data.events
GROUP BY article_id;

CREATE INDEX idx_event_aggregates_article_id
    ON niche_data.event_aggregates(article_id);

CREATE INDEX idx_event_aggregates_total_views
    ON niche_data.event_aggregates(total_views);



-- PRODUCT PERFORMANCE (MV)

DROP MATERIALIZED VIEW IF EXISTS niche_data.mv_product_performance CASCADE;

CREATE MATERIALIZED VIEW niche_data.mv_product_performance AS
SELECT 
    a.article_id,
    a.prod_name,
    a.product_type_name,
    a.product_group_name,
    a.section_name,
    a.colour_group_name,
    ROUND(a.price, 2) AS price,
    ea.total_views,
    ea.total_clicks,
    ea.total_wishlist,
    ea.total_cart_adds,
    ea.total_purchases,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.review_id) AS total_reviews,
    COALESCE(SUM(oi.line_total), 0) AS total_revenue
FROM niche_data.articles a
LEFT JOIN niche_data.event_aggregates ea 
    ON a.article_id = ea.article_id
LEFT JOIN niche_data.reviews r 
    ON a.article_id = r.article_id
LEFT JOIN niche_data.order_items oi 
    ON a.article_id = oi.article_id
GROUP BY 
    a.article_id,
    ea.total_views, ea.total_clicks, ea.total_wishlist,
    ea.total_cart_adds, ea.total_purchases,
    a.prod_name, a.product_type_name, 
    a.product_group_name, a.section_name,
    a.colour_group_name, a.price;


CREATE INDEX idx_mv_product_perf_article_id 
    ON niche_data.mv_product_performance(article_id);

CREATE INDEX idx_mv_product_perf_purchases 
    ON niche_data.mv_product_performance(total_purchases DESC);

CREATE INDEX idx_mv_product_perf_product_type 
    ON niche_data.mv_product_performance(product_type_name);

CREATE INDEX idx_mv_product_perf_section 
    ON niche_data.mv_product_performance(section_name);



-- CATEGORY SALES (MV)

DROP MATERIALIZED VIEW IF EXISTS niche_data.mv_category_sales CASCADE;

CREATE MATERIALIZED VIEW niche_data.mv_category_sales AS
SELECT 
    c.category_id,
    c.name AS category_name,
    COUNT(DISTINCT a.article_id) AS total_articles,
    COUNT(oi.order_item_id) AS total_items_sold,
    ROUND(SUM(oi.line_total), 2) AS total_revenue,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM niche_data.categories c
LEFT JOIN niche_data.articles a USING(category_id)
LEFT JOIN niche_data.order_items oi ON a.article_id = oi.article_id
LEFT JOIN niche_data.reviews r ON a.article_id = r.article_id
GROUP BY c.category_id, c.name;


CREATE INDEX idx_mv_category_sales_cat 
    ON niche_data.mv_category_sales(category_id);

CREATE INDEX idx_mv_category_sales_revenue 
    ON niche_data.mv_category_sales(total_revenue DESC);



-- FUNNEL METRICS (MV)
DROP MATERIALIZED VIEW IF EXISTS niche_data.mv_funnel_metrics CASCADE;

CREATE MATERIALIZED VIEW niche_data.mv_funnel_metrics AS
SELECT
    SUM(total_views) AS views,
    SUM(total_clicks) AS clicks,
    SUM(total_cart_adds) AS cart_adds,
    SUM(total_purchases) AS purchases,
    ROUND(100.0 * SUM(total_clicks) / NULLIF(SUM(total_views), 0), 2) AS view_to_click_rate,
    ROUND(100.0 * SUM(total_cart_adds) / NULLIF(SUM(total_clicks), 0), 2) AS click_to_cart_rate,
    ROUND(100.0 * SUM(total_purchases) / NULLIF(SUM(total_cart_adds), 0), 2) AS cart_to_purchase_rate
FROM niche_data.event_aggregates;



-- customer features (MV)
DROP MATERIALIZED VIEW IF EXISTS niche_data.mv_customer_features CASCADE;

CREATE MATERIALIZED VIEW niche_data.mv_customer_features AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.gender,
    c.age,
    c.active,
    COUNT(DISTINCT e.article_id) AS unique_products_interacted,
    SUM(e.total_views) AS total_views,
    SUM(e.total_clicks) AS total_clicks,
    SUM(e.total_wishlist) AS total_wishlist,
    SUM(e.total_cart_adds) AS total_cart_adds,
    SUM(e.total_purchases) AS total_purchases,
    COALESCE(SUM(o.total_amount), 0) AS total_spent,
    MAX(o.order_date) AS last_purchase_date,
    COUNT(DISTINCT r.review_id) AS total_reviews,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM niche_data.customers c
LEFT JOIN niche_data.orders o USING(customer_id)
LEFT JOIN niche_data.reviews r USING(customer_id)
LEFT JOIN niche_data.articles a ON TRUE   -- Just anchor for join
LEFT JOIN niche_data.event_aggregates e ON a.article_id = e.article_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.gender, c.age, c.active;


CREATE INDEX idx_mv_customer_features_customer 
    ON niche_data.mv_customer_features(customer_id);




-- MONTHLY SALES SUMMARY (MV)
DROP MATERIALIZED VIEW IF EXISTS niche_data.mv_monthly_sales CASCADE;

CREATE MATERIALIZED VIEW niche_data.mv_monthly_sales AS
SELECT 
    DATE_TRUNC('month', order_date) AS month,
    COUNT(order_id) AS total_orders,
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM niche_data.orders
GROUP BY 1;


CREATE INDEX idx_mv_monthly_sales_month 
    ON niche_data.mv_monthly_sales(month);



-- Customer Lifetime Value: CLV View

CREATE MATERIALIZED VIEW niche_data.mv_customer_clv AS
SELECT 
    c.customer_id,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount) AS avg_order_value,
    MAX(o.order_date) AS last_order_date,
    MIN(o.order_date) AS first_order_date,
    (DATE(MAX(o.order_date)) - DATE(MIN(o.order_date))) AS customer_lifespan_days,
    c.loyalty_score
FROM niche_data.customers c
LEFT JOIN niche_data.orders o USING(customer_id)
GROUP BY c.customer_id;


CREATE INDEX idx_mv_customer_clv_customer_id
ON niche_data.mv_customer_clv(customer_id);



-- Customer Purchase Frequency View: This shows purchases per month per customer.

CREATE OR REPLACE VIEW niche_data.v_customer_purchase_frequency AS
SELECT 
    customer_id,
    COUNT(order_id) AS total_orders,
    DATE_TRUNC('month', MIN(order_date)) AS first_month,
    DATE_TRUNC('month', MAX(order_date)) AS last_month,
    COUNT(order_id) / 
        NULLIF(EXTRACT(MONTH FROM AGE(MAX(order_date), MIN(order_date))) + 1, 0)
        AS avg_orders_per_month
FROM niche_data.orders
GROUP BY customer_id;



-- RFM Segmentation View (R = Recency, F = Frequency, M = Monetary)

CREATE MATERIALIZED VIEW niche_data.mv_rfm AS
WITH base AS (
    SELECT 
        o.customer_id,
        MAX(o.order_date) AS last_purchase_date,
        COUNT(o.order_id) AS frequency,
        SUM(o.total_amount) AS monetary
    FROM niche_data.orders o
    GROUP BY o.customer_id
)
SELECT 
    customer_id,
    (CURRENT_DATE - DATE(last_purchase_date)) AS recency_days,
    frequency,
    monetary,
    NTILE(4) OVER (ORDER BY (CURRENT_DATE - DATE(last_purchase_date))) AS r_score,
    NTILE(4) OVER (ORDER BY frequency) AS f_score,
    NTILE(4) OVER (ORDER BY monetary) AS m_score
FROM base;


CREATE INDEX idx_mv_rfm_customer 
    ON niche_data.mv_rfm(customer_id);

CREATE INDEX idx_mv_rfm_scores 
    ON niche_data.mv_rfm(r_score, f_score, m_score);



-- Product Demand Trend View: Shows weekly/monthly demand from orders.

CREATE MATERIALIZED VIEW niche_data.mv_product_demand AS
SELECT 
    oi.article_id,
    DATE_TRUNC('month', o.order_date) AS month,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.line_total) AS total_revenue
FROM niche_data.order_items oi
JOIN niche_data.orders o ON oi.order_id = o.order_id
GROUP BY 1, 2
ORDER BY 1, 2;

CREATE INDEX idx_mv_product_demand_article_month
    ON niche_data.mv_product_demand(article_id, month);

CREATE INDEX idx_mv_product_demand_revenue
    ON niche_data.mv_product_demand(total_revenue DESC);


-- Article Inventory Status View: Shows availability, stock levels, restock flags.
CREATE OR REPLACE VIEW niche_data.v_article_inventory AS
SELECT 
    article_id,
    prod_name,
    stock,
    CASE 
        WHEN stock = 0 THEN 'Out of Stock'
        WHEN stock < 5 THEN 'Low Stock'
        ELSE 'In Stock'
    END AS stock_status
FROM niche_data.articles;




-- Daily Sales View

CREATE MATERIALIZED VIEW niche_data.mv_daily_sales AS
SELECT 
    DATE(order_date) AS day,
    COUNT(order_id) AS total_orders,
    SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM niche_data.orders
GROUP BY 1;

CREATE INDEX idx_mv_daily_sales_day ON niche_data.mv_daily_sales(day);




-- Funnel Conversion Metric: Shows product funnel performance: views → cart → wishlist → purchase.

CREATE MATERIALIZED VIEW niche_data.mv_funnel AS
SELECT 
    a.article_id,
    COUNT(*) FILTER (WHERE e.event_type='view') AS views,
    COUNT(*) FILTER (WHERE e.event_type='add_to_cart') AS add_to_cart,
    COUNT(*) FILTER (WHERE e.event_type='wishlist') AS wishlist,
    COUNT(oi.order_item_id) AS purchases
FROM niche_data.articles a
LEFT JOIN niche_data.events e ON a.article_id = e.article_id
LEFT JOIN niche_data.order_items oi ON a.article_id = oi.article_id
GROUP BY a.article_id;


-- INVENTORY STATUS (NORMAL VIEW)
CREATE OR REPLACE VIEW niche_data.v_article_inventory AS
SELECT 
    article_id,
    prod_name,
    stock,
    CASE 
        WHEN stock = 0 THEN 'Out of Stock'
        WHEN stock < 5 THEN 'Low Stock'
        ELSE 'In Stock'
    END AS stock_status
FROM niche_data.articles;





REFRESH MATERIALIZED VIEW niche_data.event_aggregates;
REFRESH MATERIALIZED VIEW niche_data.mv_product_performance;
REFRESH MATERIALIZED VIEW niche_data.mv_category_sales;
REFRESH MATERIALIZED VIEW niche_data.mv_funnel_metrics;
REFRESH MATERIALIZED VIEW niche_data.mv_customer_features;
REFRESH MATERIALIZED VIEW niche_data.mv_customer_clv;
REFRESH MATERIALIZED VIEW niche_data.mv_rfm;
REFRESH MATERIALIZED VIEW niche_data.mv_product_demand;
REFRESH MATERIALIZED VIEW niche_data.mv_daily_sales;
REFRESH MATERIALIZED VIEW niche_data.mv_monthly_sales;