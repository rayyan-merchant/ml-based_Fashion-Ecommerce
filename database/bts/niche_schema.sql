CREATE SCHEMA niche_data;

SET search_path TO niche_data;

CREATE TABLE niche_data.articles AS
SELECT * FROM public.articles
WHERE product_type_name IN ('Jacket', 'Hoodie', 'Beanie')
   OR (product_type_name = 'Trousers' AND section_name IN ('Ladies Denim', 'Denim Men'));

CREATE TABLE niche_data.transactions AS
SELECT * FROM public.transactions
WHERE article_id IN (SELECT article_id FROM niche_data.articles);

CREATE TABLE niche_data.customers AS
SELECT DISTINCT c.*
FROM public.customers c
JOIN niche_data.transactions t USING(customer_id);




SELECT COUNT(*) FROM niche_data.articles;
SELECT COUNT(*) FROM niche_data.transactions;
SELECT COUNT(DISTINCT customer_id) FROM niche_data.customers;



SELECT 
    a.product_type_name,
    COUNT(*) AS transactions,
    COUNT(DISTINCT a.article_id) AS num_articles,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    ROUND(AVG(t.price), 2) AS avg_price
FROM niche_data.transactions t
JOIN niche_data.articles a ON t.article_id = a.article_id
GROUP BY a.product_type_name
ORDER BY transactions DESC;


UPDATE niche_data.articles SET stock = floor(random() * 300 + 50); 


CREATE TABLE categories AS
SELECT DISTINCT 
  CASE
    WHEN product_type_name IN ('Jacket', 'Hoodie') THEN 'Upper Body'
    WHEN product_type_name = 'Trousers' THEN 'Lower Body'
    WHEN product_type_name = 'Beanie' THEN 'Accessories'
  END AS name;


SELECT * FROM niche_data.articles;
SELECT * FROM niche_data.transactions;
SELECT * FROM niche_data.customers;
select * from niche_data.categories


CREATE TABLE niche_data.orders (LIKE public.orders INCLUDING ALL);
CREATE TABLE niche_data.order_items (LIKE public.order_items INCLUDING ALL);
CREATE TABLE niche_data.reviews (LIKE public.reviews INCLUDING ALL);
CREATE TABLE niche_data.categories (LIKE public.categories INCLUDING ALL);
CREATE TABLE niche_data.events (LIKE public.events INCLUDING ALL);


-- categories

INSERT INTO niche_data.categories (name)
SELECT DISTINCT product_type_name
FROM niche_data.articles
WHERE product_type_name IS NOT NULL;

select * from niche_data.categories

UPDATE niche_data.articles a
SET category_id = c.category_id
FROM niche_data.categories c
WHERE a.product_type_name = c.name;

SELECT COUNT(*) AS total, COUNT(category_id) AS with_category
FROM niche_data.articles;

SELECT a.product_type_name, c.name
FROM niche_data.articles a
JOIN niche_data.categories c USING(category_id)
LIMIT 10;



-- orders
select * from niche_data.orders

select COUNT(*) from niche_data.orders
where payment_status = 'Pending';

INSERT INTO niche_data.orders (customer_id, order_date, total_amount)
SELECT 
    customer_id,
    DATE(t_dat) AS order_date,
    ROUND(SUM(price), 2) AS total_amount
FROM niche_data.transactions
GROUP BY customer_id, DATE(t_dat);

SELECT COUNT(*) FROM niche_data.orders
where payment_status = 'pending';

UPDATE niche_data.orders
SET shipping_address = 
    CONCAT('Street ', (RANDOM() * 100)::INT, ', Karachi, Pakistan');

SELECT o.customer_id, SUM(o.total_amount) AS total_spent
FROM niche_data.orders o
GROUP BY o.customer_id
ORDER BY total_spent DESC
LIMIT 5;


UPDATE niche_data.orders
SET payment_status = CASE
    WHEN order_date >= ((SELECT MAX(order_date) FROM niche_data.orders) - INTERVAL '7 days')
         AND RANDOM() < 0.5 THEN 'Pending'
    WHEN order_date >= ((SELECT MAX(order_date) FROM niche_data.orders) - INTERVAL '30 days')
         AND RANDOM() < 0.15 THEN 'Pending'
    ELSE 'Paid'
END;

SELECT 
    payment_status,
    COUNT(*) AS num_orders,
    MIN(order_date) AS oldest_date,
    MAX(order_date) AS newest_date
FROM niche_data.orders
GROUP BY payment_status
ORDER BY oldest_date;


select 
	MIN(order_date) AS oldest_date,
    MAX(order_date) AS newest_date
from niche_data.orders
where payment_status = 'Pending';


-- order items

select * from niche_data.order_items;

INSERT INTO niche_data.order_items (order_id, article_id, quantity, unit_price)
SELECT 
    o.order_id,
    t.article_id,
    1 AS quantity,
    ROUND(t.price, 2) AS unit_price
FROM niche_data.transactions t
JOIN niche_data.orders o
  ON t.customer_id = o.customer_id
 AND DATE(t.t_dat) = o.order_date;

SELECT COUNT(*) FROM niche_data.order_items;

SELECT o.order_id, COUNT(*) AS num_items, SUM(oi.line_total) AS total
FROM niche_data.order_items oi
JOIN niche_data.orders o USING(order_id)
GROUP BY o.order_id
ORDER BY total DESC
LIMIT 10;


UPDATE niche_data.order_items
SET quantity = CASE
    WHEN RANDOM() < 0.7 THEN 1
    WHEN RANDOM() < 0.9 THEN 2
    ELSE 3
END;

--UPDATE niche_data.order_items
--SET line_total = quantity * unit_price;

--line_total NUMERIC(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED

/*
UPDATE niche_data.orders o
SET total_amount = (
    SELECT ROUND(SUM(line_total), 2)
    FROM niche_data.order_items oi
    WHERE oi.order_id = o.order_id
);
*/


SELECT o.order_id, c.first_name, a.prod_name, oi.quantity, oi.unit_price
FROM niche_data.orders o
JOIN niche_data.order_items oi USING(order_id)
JOIN niche_data.articles a USING(article_id)
JOIN niche_data.customers c USING(customer_id)
LIMIT 10;


CREATE INDEX idx_order_items_order_id ON niche_data.order_items(order_id);

UPDATE niche_data.orders o
SET total_amount = rounded.total_amount
FROM (
    SELECT order_id, ROUND(SUM(line_total), 2) AS total_amount
    FROM niche_data.order_items
    GROUP BY order_id
) AS rounded
WHERE o.order_id = rounded.order_id;



-- reviews

select * from niche_data.reviews;

TRUNCATE TABLE niche_data.reviews;

INSERT INTO niche_data.reviews (customer_id, article_id, rating, review_text, created_at)
SELECT 
    o.customer_id,
    oi.article_id,
    CASE
        WHEN rnd < 0.2 THEN 5
        WHEN rnd < 0.4 THEN 4
        WHEN rnd < 0.6 THEN 3
        WHEN rnd < 0.8 THEN 2
        ELSE 1
    END AS rating,
    CASE
        WHEN rnd < 0.2 THEN 'Loved it, great quality!'
        WHEN rnd < 0.4 THEN 'Good overall, fits nicely.'
        WHEN rnd < 0.6 THEN 'Average product, could be better.'
        WHEN rnd < 0.8 THEN 'Did not meet expectations.'
        ELSE 'Poor quality, would not recommend.'
    END AS review_text,
    (o.order_date + ((RANDOM() * 7)::INT || ' days')::INTERVAL)::DATE AS created_at
FROM (
    SELECT *,
           RANDOM() AS rnd  
    FROM niche_data.order_items
) oi
JOIN niche_data.orders o ON oi.order_id = o.order_id
WHERE RANDOM() < 0.15;


SELECT rating, review_text, COUNT(*)
FROM niche_data.reviews
GROUP BY rating, review_text
ORDER BY rating DESC;


-- events
select * from niche_data.events

TRUNCATE table niche_data.events 

INSERT INTO niche_data.events (session_id, customer_id, article_id, event_type, campaign_id, created_at)
SELECT 
    md5(random()::text || clock_timestamp()::text) AS session_id,
    c.customer_id,
    a.article_id,
    CASE 
        WHEN RANDOM() < 0.6 THEN 'view'
        WHEN RANDOM() < 0.8 THEN 'click'
        WHEN RANDOM() < 0.9 THEN 'wishlist'
        ELSE 'add_to_cart'
    END AS event_type,
	NULL AS campaign_id,
    (a.created_at + ((RANDOM() * 365)::INT || ' days')::INTERVAL) AS created_at
FROM niche_data.customers c
JOIN niche_data.articles a ON RANDOM() < 0.02
WHERE RANDOM() < 0.25;


INSERT INTO niche_data.events (session_id, customer_id, article_id, event_type,  campaign_id, created_at)
SELECT 
    md5(o.order_id::text || oi.article_id || clock_timestamp()::text) AS session_id,
    o.customer_id,
    oi.article_id,
    'purchase' AS event_type,
	NULL AS campaign_id,
    (o.order_date + ((RANDOM() * 2)::INT || ' days')::INTERVAL) AS created_at
FROM niche_data.orders o
JOIN niche_data.order_items oi ON o.order_id = oi.order_id;

select count(*) from niche_data.events

CREATE INDEX idx_events_customer ON niche_data.events(customer_id);
CREATE INDEX idx_events_article ON niche_data.events(article_id);
CREATE INDEX idx_events_event_type ON niche_data.events(event_type);
CREATE INDEX idx_created_at ON niche_data.events(created_at);


SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
ORDER BY schemaname, tablename, indexname;

select event_type, count(*) 
from niche_data.events
group by event_type;


SELECT event_type, COUNT(*) AS total, 
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM niche_data.events), 2) AS percentage
FROM niche_data.events
GROUP BY event_type
ORDER BY total DESC;




UPDATE niche_data.articles a
SET price = sub.avg_price
FROM (
    SELECT article_id, ROUND(AVG(price), 2) AS avg_price
    FROM niche_data.transactions
    WHERE price > 0
    GROUP BY article_id
) AS sub
WHERE a.article_id = sub.article_id
  AND (a.price IS NULL OR a.price = 0);


UPDATE niche_data.articles
SET price = ROUND((0.01 + random() * 0.25)::numeric, 2)
WHERE price IS NULL OR price = 0;




WITH recent_tx AS (
    SELECT DISTINCT customer_id
    FROM niche_data.transactions
    WHERE t_dat >= (
        (SELECT MAX(t_dat) FROM niche_data.transactions) - INTERVAL '90 days'
    )
)
UPDATE niche_data.customers c
SET active = TRUE
FROM recent_tx r
WHERE c.customer_id = r.customer_id
  AND c.active IS NULL;

-- Set the rest to FALSE
UPDATE niche_data.customers
SET active = FALSE
WHERE active IS NULL;


CREATE INDEX IF NOT EXISTS idx_transactions_tdat ON niche_data.transactions (t_dat);
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON niche_data.transactions (customer_id);


UPDATE niche_data.customers
SET signup_date = (
    (SELECT MAX(t_dat) FROM niche_data.transactions)
    - (INTERVAL '730 days' * RANDOM())
);


UPDATE niche_data.customers
SET first_name = INITCAP(
        (ARRAY[
            'Ali','Sara','Ayesha','Hassan','Fatima','Bilal','Zara','Usman','Maham','Ahmed',
            'Omar','Noor','Amna','Hamza','Iqra','Daniyal','Maryam','Nimra','Huzaifa','Laiba',
            'Zain','Emaan','Taha','Hiba','Hassan','Mariam','Hania','Rehan','Areeba','Faris', 'Rayyan', 'Riya', 'Rija'
        ])[FLOOR(RANDOM()*30 + 1)]
    ),
    last_name = INITCAP(
        (ARRAY[
            'Khan','Malik','Sheikh','Butt','Mirza','Raza','Rehman','Iqbal','Chaudhry','Nawaz',
            'Syed','Tariq','Qureshi','Ali','Anwar','Saleem','Hassan','Abbas','Naeem','Hameed',
            'Ashraf','Mughal','Zahid','Farooq','Mehmood','Akhtar','Ahmed','Hussain','Khalid','Baig'
        ])[FLOOR(RANDOM()*30 + 1)]
    )
WHERE first_name IS NULL OR last_name IS NULL;


UPDATE niche_data.customers
SET email = LOWER(
    CASE 
        WHEN RANDOM() < 0.4 THEN first_name || '.' || last_name || customer_id || '@gmail.com'
        WHEN RANDOM() < 0.7 THEN first_name || last_name || (100 + FLOOR(RANDOM()*900))::TEXT || '@yahoo.com'
        ELSE first_name || '_' || last_name || (FLOOR(RANDOM()*1000))::TEXT || '@hotmail.com'
    END
)
WHERE email IS NULL OR email = '';


ALTER TABLE niche_data.customers
ADD COLUMN IF NOT EXISTS gender VARCHAR(10);

UPDATE niche_data.customers
SET gender = CASE
    WHEN LOWER(first_name) IN (
        'ali','hassan','bilal','usman','ahmed','omar','hamza','daniyal','huzaifa','zain',
        'taha','rehan','faris','hassan','fahad','asim','ammar','waleed','arsalan','salman'
    ) THEN 'Male'
    WHEN LOWER(first_name) IN (
        'sara','ayesha','fatima','zara','maham','noor','amna','iqra','maryam','nimra',
        'laiba','emaan','hiba','mariam','hania','areeba','maira','hiba','hina','maheen'
    ) THEN 'Female'
    ELSE CASE WHEN RANDOM() < 0.5 THEN 'Male' ELSE 'Female' END
END
WHERE gender IS NULL;




