-- Demographic Layer
SELECT
    customer_id,
    age,
    active,
    club_member_status,
    fashion_news_frequency,
    signup_date,
    EXTRACT(DAY FROM (CURRENT_DATE - signup_date)) AS signup_age_days
FROM niche_data.customers;


-- Transaction RFM Layer
WITH tx AS (
    SELECT
        customer_id,
        COUNT(*)                     AS total_transactions,
        SUM(price)                   AS total_amount_spent,
        MIN(t_dat)                   AS first_purchase_date,
        MAX(t_dat)                   AS last_purchase_date
    FROM niche_data.transactions
    GROUP BY customer_id
),
rec AS (
    SELECT
        customer_id,
        total_transactions,
        total_amount_spent,
        first_purchase_date,
        last_purchase_date,
        (CURRENT_DATE - last_purchase_date) AS recency_days  -- integer
    FROM tx
)
SELECT * FROM rec;


-- Order Behavioral Layer
WITH orders_base AS (
    SELECT
        o.customer_id,
        COUNT(*) AS total_orders,
        SUM(oi.quantity) AS total_items_bought,
        SUM(o.total_amount) AS total_revenue_from_orders,
        AVG(o.total_amount) AS avg_order_value
    FROM niche_data.orders o
    LEFT JOIN niche_data.order_items oi ON o.order_id = oi.order_id
    GROUP BY o.customer_id
)
SELECT * FROM orders_base;


-- Event Behavioural Layer
SELECT
    customer_id,
    COUNT(*) AS total_events,
    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS views,
    SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) AS clicks,
    SUM(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS carts,
    SUM(CASE WHEN event_type = 'buy' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN event_type = 'wishlist' THEN 1 ELSE 0 END) AS wishlist_events
FROM niche_data.events
GROUP BY customer_id;



-- Category Preference Layer
WITH cat_pref AS (
    SELECT
        t.customer_id,
        a.category_id,
        COUNT(*) AS cnt
    FROM niche_data.transactions t
    JOIN niche_data.articles a ON t.article_id = a.article_id
    GROUP BY t.customer_id, a.category_id
),

ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY cnt DESC) AS rnk
    FROM cat_pref
)

SELECT
    customer_id,
    category_id AS top_category
FROM ranked
WHERE rnk = 1;

