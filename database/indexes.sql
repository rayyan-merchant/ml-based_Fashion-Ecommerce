-- Transactions
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON niche_data.transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_article_id ON niche_data.transactions(article_id);

-- Orders & Order Items
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON niche_data.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON niche_data.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_article_id ON niche_data.order_items(article_id);

-- Reviews
CREATE INDEX IF NOT EXISTS idx_reviews_customer_id ON niche_data.reviews(customer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_article_id ON niche_data.reviews(article_id);

-- Events
CREATE INDEX IF NOT EXISTS idx_events_customer_id ON niche_data.events(customer_id);
CREATE INDEX IF NOT EXISTS idx_events_article_id ON niche_data.events(article_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON niche_data.events(event_type);
CREATE INDEX IF NOT EXISTS idx_created_at ON niche_data.events(created_at);

-- Articles → Categories
CREATE INDEX IF NOT EXISTS idx_articles_category_id ON niche_data.articles(category_id);

-- Categories (self-reference)
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON niche_data.categories(parent_category_id);



-- Common filters
CREATE INDEX IF NOT EXISTS idx_articles_price ON niche_data.articles(price);
CREATE INDEX IF NOT EXISTS idx_articles_prod_name ON niche_data.articles(prod_name);

CREATE INDEX IF NOT EXISTS idx_customers_active ON niche_data.customers(active);
CREATE INDEX IF NOT EXISTS idx_customers_gender ON niche_data.customers(gender);
CREATE INDEX IF NOT EXISTS idx_customers_postal_code ON niche_data.customers(postal_code);

CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON niche_data.orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON niche_data.orders(order_date);



-- Support aggregation by month
CREATE INDEX IF NOT EXISTS idx_orders_order_month ON niche_data.orders (DATE_TRUNC('month', order_date));

-- Support article engagement metrics
CREATE INDEX IF NOT EXISTS idx_events_created_at ON niche_data.events(created_at);

-- Support rating aggregation
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON niche_data.reviews(rating);


--text search
CREATE INDEX IF NOT EXISTS idx_articles_name_search 
ON niche_data.articles USING GIN (to_tsvector('english', prod_name));

CREATE INDEX IF NOT EXISTS idx_reviews_text_search 
ON niche_data.reviews USING GIN (to_tsvector('english', review_text));

-- cart
CREATE INDEX IF NOT EXISTS idx_cart_id ON niche_data.cart(cart_id);
CREATE INDEX IF NOT EXISTS idx_cart_customer_id ON niche_data.cart(customer_id);
CREATE INDEX IF NOT EXISTS idx_cart_article_id ON niche_data.cart(article_id);

-- wishlist
CREATE INDEX IF NOT EXISTS idx_wishlist_id ON niche_data.wishlist(wishlist_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_customer_id ON niche_data.wishlist(customer_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_article_id ON niche_data.wishlist(article_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_customers_email_ci ON niche_data.customers (LOWER(email));









-- Recreate essential indexes (use explicit names)
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON niche_data.transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_article_id ON niche_data.transactions(article_id);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON niche_data.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON niche_data.orders(order_date);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON niche_data.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_article_id ON niche_data.order_items(article_id);

CREATE INDEX IF NOT EXISTS idx_reviews_customer_id ON niche_data.reviews(customer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_article_id ON niche_data.reviews(article_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON niche_data.reviews(rating);

CREATE INDEX IF NOT EXISTS idx_events_customer_id ON niche_data.events(customer_id);
CREATE INDEX IF NOT EXISTS idx_events_article_id ON niche_data.events(article_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON niche_data.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON niche_data.events(created_at);

CREATE INDEX IF NOT EXISTS idx_articles_category_id ON niche_data.articles(category_id);
CREATE INDEX IF NOT EXISTS idx_articles_price ON niche_data.articles(price);
CREATE INDEX IF NOT EXISTS idx_articles_prod_name ON niche_data.articles(prod_name);

CREATE INDEX IF NOT EXISTS idx_customers_active ON niche_data.customers(active);
CREATE INDEX IF NOT EXISTS idx_customers_gender ON niche_data.customers(gender);
CREATE INDEX IF NOT EXISTS idx_customers_postal_code ON niche_data.customers(postal_code);
CREATE INDEX IF NOT EXISTS idx_customers_loyalty_score ON niche_data.customers(loyalty_score);

CREATE INDEX IF NOT EXISTS idx_cart_customer_id ON niche_data.cart(customer_id);
CREATE INDEX IF NOT EXISTS idx_cart_article_id ON niche_data.cart(article_id);

CREATE INDEX IF NOT EXISTS idx_wishlist_customer_id ON niche_data.wishlist(customer_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_article_id ON niche_data.wishlist(article_id);

-- text search indexes
DROP INDEX IF EXISTS idx_articles_name_search;
CREATE INDEX IF NOT EXISTS idx_articles_name_search 
ON niche_data.articles USING GIN (to_tsvector('english', prod_name));

DROP INDEX IF EXISTS idx_reviews_text_search;
CREATE INDEX IF NOT EXISTS idx_reviews_text_search 
ON niche_data.reviews USING GIN (to_tsvector('english', review_text));

CREATE INDEX IF NOT EXISTS idx_customers_address
ON niche_data.customers(address);

CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_phone
ON niche_data.customers(phone);




SELECT 
    schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'niche_data'
ORDER BY tablename;


SELECT
    COUNT(DISTINCT indexname) AS TotalIndexes
FROM
    pg_indexes
WHERE
    schemaname = 'niche_data'; 