SELECT
  COUNT(DISTINCT article_id) AS total_articles,
  COUNT(DISTINCT product_code) AS total_products,
  COUNT(DISTINCT product_group_name) AS num_product_groups,
  COUNT(DISTINCT product_type_name) AS num_product_types,
  COUNT(DISTINCT section_name) AS num_sections,
  COUNT(DISTINCT garment_group_name) AS num_garment_groups,
  COUNT(DISTINCT department_name) AS num_department,
  COUNT(DISTINCT index_name) AS num_index_groups,
  COUNT(DISTINCT index_group_name) AS num_index_types
FROM articles;


SELECT DISTINCT product_group_name
FROM articles
ORDER BY product_group_name;

SELECT DISTINCT product_type_name
FROM articles
ORDER BY product_type_name;

SELECT DISTINCT section_name
FROM articles
ORDER BY section_name;

SELECT DISTINCT garment_group_name
FROM articles
ORDER BY garment_group_name;

SELECT DISTINCT department_name
FROM articles
ORDER BY department_name;

SELECT DISTINCT index_name
FROM articles
ORDER BY index_name;

SELECT DISTINCT index_group_name
FROM articles
ORDER BY index_group_name;


-- Filtered by Product Group
select 
    a.product_group_name,
    COUNT(*) AS total_sales,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    COUNT(DISTINCT a.article_id) AS num_articles,
    round(AVG(t.price), 2) AS avg_price
from transactions t
join articles a ON t.article_id = a.article_id
group by a.product_group_name
order by total_sales desc;


-- Filtered by Section
SELECT 
    a.section_name,
    COUNT(*) AS total_sales,
    COUNT(DISTINCT a.article_id) AS num_articles
FROM transactions t
JOIN articles a ON t.article_id = a.article_id
GROUP BY a.section_name
ORDER BY total_sales DESC;



SELECT a.product_name
FROM transactions t
JOIN articles a ON t.article_id = a.article_id
where section_name ="Divided Collection"
ORDER BY total_sales DESC;


select min(t_dat), max(t_dat) from transactions;




SELECT 
    a.product_group_name,
    COUNT(*) AS sales_count,
    ROUND(SUM(t.price), 2) AS total_revenue,
    ROUND(AVG(t.price), 2) AS avg_price,
    COUNT(DISTINCT t.customer_id) AS unique_customers
FROM transactions t
JOIN articles a ON t.article_id = a.article_id
WHERE a.product_group_name IN ('Dresses', 'Trousers', 'Shoes', 'Accessories')
GROUP BY a.product_group_name
ORDER BY total_revenue DESC;


select prod_name
from articles 
where product_group_name = 'Accessories';


select prod_name, article_id
from articles 
where product_group_name = 'Shoes';




select 
    COUNT(*) AS total_sales,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    COUNT(DISTINCT a.article_id) AS num_articles,
    round(AVG(t.price), 2) AS avg_price
from transactions t
join articles a ON t.article_id = a.article_id
where section_name = 'Womens Tailoring';


select article_id, prod_name
from articles
where section_name = 'Womens Tailoring';


select DISTINCT prod_name
from articles
where section_name = 'Womens Tailoring';




select article_id, prod_name
from articles
where section_name = 'Ladies Denim';

select DISTINCT prod_name
from articles
where section_name = 'Ladies Denim';



SELECT 
    MIN(t_dat) AS start_date,
    MAX(t_dat) AS end_date
FROM transactions t
JOIN articles a ON t.article_id = a.article_id
WHERE a.product_type_name = 'Sweater';



select 
	product_type_name,
    COUNT(*) AS total_sales,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    COUNT(DISTINCT a.article_id) AS num_articles,
    round(AVG(t.price), 2) AS avg_price
from transactions t
join articles a ON t.article_id = a.article_id
where product_type_name IN ('Sweater', 'Trousers', 'Hoodie', 'Jacket', 'Coat', 'Beanie', 'Gloves')
group by product_type_name;



select count(*), product_type_name, section_name,
	   COUNT(DISTINCT t.customer_id) AS unique_customers,
       COUNT(DISTINCT a.article_id) AS num_articles
from articles a
join transactions t on t.article_id = a.article_id
where product_group_name = 'Garment Lower body'  AND (section_name = 'Denim Men' OR section_name = 'Ladies Denim')
group by product_type_name, section_name;





