ALTER TABLE niche_data.customers
ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);

ALTER TABLE niche_data.articles
ADD CONSTRAINT articles_pkey PRIMARY KEY (article_id);

ALTER TABLE niche_data.orders
ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);

ALTER TABLE niche_data.order_items
ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_item_id);

ALTER TABLE niche_data.reviews
ADD CONSTRAINT reviews_pkey PRIMARY KEY (review_id);

ALTER TABLE niche_data.transactions
ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);

ALTER TABLE niche_data.articles
ADD CONSTRAINT fk_articles_category FOREIGN KEY (category_id)
REFERENCES niche_data.categories(category_id)
ON UPDATE NO ACTION
ON DELETE SET NULL;

ALTER TABLE niche_data.categories
ADD CONSTRAINT fk_parent_category FOREIGN KEY (parent_category_id)
REFERENCES niche_data.categories(category_id)
ON UPDATE NO ACTION
ON DELETE SET NULL;

ALTER TABLE niche_data.events
ADD CONSTRAINT fk_events_article FOREIGN KEY (article_id)
REFERENCES niche_data.articles(article_id)
ON UPDATE NO ACTION
ON DELETE SET NULL;

ALTER TABLE niche_data.events
ADD CONSTRAINT fk_events_customer FOREIGN KEY (customer_id)
REFERENCES niche_data.customers(customer_id)
ON UPDATE NO ACTION
ON DELETE SET NULL;

ALTER TABLE niche_data.order_items
ADD CONSTRAINT fk_oi_article FOREIGN KEY (article_id)
REFERENCES niche_data.articles(article_id)
ON UPDATE NO ACTION
ON DELETE RESTRICT;

ALTER TABLE niche_data.order_items
ADD CONSTRAINT fk_oi_order FOREIGN KEY (order_id)
REFERENCES niche_data.orders(order_id)
ON UPDATE NO ACTION
ON DELETE CASCADE;

ALTER TABLE niche_data.orders
ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
REFERENCES niche_data.customers(customer_id)
ON UPDATE NO ACTION
ON DELETE RESTRICT;

ALTER TABLE niche_data.reviews
ADD CONSTRAINT fk_review_article FOREIGN KEY (article_id)
REFERENCES niche_data.articles(article_id)
ON UPDATE NO ACTION
ON DELETE CASCADE;

ALTER TABLE niche_data.reviews
ADD CONSTRAINT fk_review_customer FOREIGN KEY (customer_id)
REFERENCES niche_data.customers(customer_id)
ON UPDATE NO ACTION
ON DELETE CASCADE;

ALTER TABLE niche_data.transactions
ADD CONSTRAINT transactions_article_id_fkey FOREIGN KEY (article_id)
REFERENCES niche_data.articles(article_id);

ALTER TABLE niche_data.transactions
ADD CONSTRAINT transactions_customer_id_fkey FOREIGN KEY (customer_id)
REFERENCES niche_data.customers(customer_id);

SELECT customer_id, COUNT(*)
FROM niche_data.customers
GROUP BY customer_id
HAVING COUNT(*) > 1;


SELECT article_id, COUNT(*)
FROM niche_data.articles
GROUP BY article_id
HAVING COUNT(*) > 1;


CREATE TABLE IF NOT EXISTS niche_data.wishlist (
    wishlist_id SERIAL PRIMARY KEY,
    customer_id VARCHAR NOT NULL REFERENCES niche_data.customers(customer_id),
    article_id VARCHAR NOT NULL REFERENCES niche_data.articles(article_id),
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(customer_id, article_id)
);


CREATE TABLE IF NOT EXISTS niche_data.cart (
    cart_id SERIAL PRIMARY KEY,
    customer_id VARCHAR NOT NULL REFERENCES niche_data.customers(customer_id),
    article_id VARCHAR NOT NULL REFERENCES niche_data.articles(article_id),
    quantity INT NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(customer_id, article_id)
);

ALTER TABLE niche_data.customers
ADD COLUMN loyalty_score NUMERIC DEFAULT 0;


UPDATE niche_data.customers c
SET loyalty_score = COALESCE(purchase_pts, 0) + COALESCE(review_pts, 0) + COALESCE(wishlist_pts, 0)
FROM (
    -- purchase points: total_amount 
    SELECT customer_id, SUM(total_amount) * 1 AS purchase_pts
    FROM niche_data.orders
    GROUP BY customer_id
) AS p
FULL JOIN (
    -- review points mapping: 5->5, 4->3, 3->1, else 0 (same weights used earlier)
    SELECT customer_id,
           SUM(
             CASE 
               WHEN rating = 5 THEN 5
               WHEN rating = 4 THEN 3
               WHEN rating = 3 THEN 1
               ELSE 0
             END
           ) AS review_pts
    FROM niche_data.reviews
    GROUP BY customer_id
) AS r ON p.customer_id = r.customer_id
FULL JOIN (
    -- wishlist points: 0.5 per wishlist item
    SELECT customer_id, COUNT(*) * 0.5 AS wishlist_pts
    FROM niche_data.wishlist
    GROUP BY customer_id
) AS w ON COALESCE(p.customer_id, r.customer_id) = w.customer_id
WHERE c.customer_id = COALESCE(p.customer_id, r.customer_id, w.customer_id);

SELECT 
  COUNT(*) AS customers_total,
  MIN(loyalty_score) AS min_score,
  MAX(loyalty_score) AS max_score,
  ROUND(AVG(loyalty_score),2) AS avg_score
FROM niche_data.customers;

-- sample top customers
SELECT customer_id, loyalty_score
FROM niche_data.customers
ORDER BY loyalty_score DESC
LIMIT 20;




SELECT * FROM niche_data.cart c
LEFT JOIN niche_data.customers cu ON c.customer_id = cu.customer_id
WHERE cu.customer_id IS NULL;

SELECT * FROM niche_data.cart c
LEFT JOIN niche_data.articles a ON c.article_id = a.article_id
WHERE a.article_id IS NULL;

SELECT * FROM niche_data.wishlist w
LEFT JOIN niche_data.customers cu ON w.customer_id = cu.customer_id
WHERE cu.customer_id IS NULL;

SELECT * FROM niche_data.wishlist w
LEFT JOIN niche_data.articles a ON w.article_id = a.article_id
WHERE a.article_id IS NULL;



