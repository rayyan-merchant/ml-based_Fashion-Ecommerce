SELECT 
    e.event_id,
    e.session_id,
    e.customer_id,
    e.article_id,
    a.category_id,
    e.event_type,
    e.campaign_id,
    e.created_at,
    EXTRACT(HOUR FROM e.created_at) AS event_hour,
    EXTRACT(DOW FROM e.created_at) AS event_day
FROM nicheevents e
LEFT JOIN articles a ON e.article_id = a.article_id
ORDER BY e.customer_id, e.session_id, e.created_at;
