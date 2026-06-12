SELECT 
    r.review_id,
    r.customer_id,
    r.article_id,
    a.category_id,
    r.rating,
    r.review_text,
    r.created_at,
    EXTRACT(DAY FROM (CURRENT_DATE - r.created_at)) AS review_age_days
FROM niche_data.reviews r
LEFT JOIN articles a ON r.article_id = a.article_id;
