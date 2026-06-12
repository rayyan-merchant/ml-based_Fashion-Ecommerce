WITH base AS (
    SELECT 
        customer_id,
        article_id,
        COUNT(*) AS purchase_count,
        SUM(price) AS total_spent,
        MIN(t_dat) AS first_purchase_date,
        MAX(t_dat) AS last_purchase_date
    FROM niche_data.transactions
    GROUP BY customer_id, article_id
),

rec AS (
    SELECT 
        customer_id,
        article_id,
        purchase_count,
        total_spent,
        first_purchase_date,
        last_purchase_date,
        DATE_PART('day', (CURRENT_DATE - last_purchase_date) * INTERVAL '1 day') AS recency_days
    FROM base
),

weighted AS (
    SELECT
        customer_id,
        article_id,
        purchase_count,
        total_spent,
        first_purchase_date,
        last_purchase_date,
        recency_days,
        purchase_count * EXP(- recency_days / 30.0) AS time_weighted_score
    FROM rec
)

SELECT * FROM weighted;

