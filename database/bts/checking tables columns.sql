-- checking tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'transactions';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'articles';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'customers';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'articles';


SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'categories';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'orders';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'order_items';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'reviews';

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'events';



SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM transactions;


select * from customers;

select * from articles;

select * from transactions;



-- NULL CHECK
SELECT
    COUNT(*) FILTER (WHERE stock = 0) AS null_count,
    COUNT(*) AS total
FROM articles;


SELECT * FROM customers LIMIT 5;


-- CHeking BCNF

-- customers (satisfied)
select DISTINCT(COUNT(customer_id)) - COUNT(*) AS total
from customers


-- articles
select product_code
from articles
group by product_code 
having count(article_id) > 1;
