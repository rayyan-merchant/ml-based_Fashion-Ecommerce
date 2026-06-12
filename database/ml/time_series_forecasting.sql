-- Article-Level Daily
SELECT
    t.article_id,
    a.category_id,
    t.t_dat::date AS date,
    COUNT(*) AS daily_sales,
    SUM(t.price) AS daily_revenue,
    AVG(t.price) AS avg_price
FROM niche_data.transactions t
JOIN niche_data.articles a ON t.article_id = a.article_id
GROUP BY t.article_id, a.category_id, t.t_dat::date
ORDER BY t.article_id, date;


-- Category-Level Daily Sales
SELECT
    a.category_id,
    t.t_dat::date AS date,
    COUNT(*) AS daily_sales,
    SUM(t.price) AS daily_revenue
FROM niche_data.transactions t
JOIN niche_data.articles a ON t.article_id = a.article_id
GROUP BY a.category_id, t.t_dat::date
ORDER BY a.category_id, date;


