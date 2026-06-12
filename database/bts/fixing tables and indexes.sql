-- Fix script: constraints, indexes, and data-cleaning for niche_data
-- Run in a single transaction if you prefer; parts run with NOTICE logs.

-- 0. Safety: use savepoint approach for large operations
BEGIN;

RAISE NOTICE '=== STARTING SCHEMA FIXES ===';

--------------------------------------------------------------------------------
-- 1) Create safe placeholder customer & article for orphan rows
--------------------------------------------------------------------------------

-- create placeholder customer if not exists
INSERT INTO niche_data.customers (customer_id, first_name, last_name, email, active, signup_date, gender, loyalty_score)
SELECT 'unknown_customer', 'Unknown', 'Customer', 'unknown@example.com', FALSE, now(), 'Other', 0
WHERE NOT EXISTS (SELECT 1 FROM niche_data.customers WHERE customer_id = 'unknown_customer');

-- create placeholder article if not exists
INSERT INTO niche_data.articles (article_id, prod_name, product_type_name, product_group_name, section_name, price, stock, created_at)
SELECT 'unknown_article', 'Unknown Article', 'Unknown', 'Unknown', 'Unknown', 0.01, 0
WHERE NOT EXISTS (SELECT 1 FROM niche_data.articles WHERE article_id = 'unknown_article');

RAISE NOTICE 'Placeholders ensured.';

--------------------------------------------------------------------------------
-- 2) Fix NULLs & sensible defaults before adding NOT NULL constraints
--------------------------------------------------------------------------------

-- 2.1 Transactions: replace NULL customer_id/article_id with placeholders
UPDATE niche_data.transactions
SET customer_id = 'unknown_customer'
WHERE customer_id IS NULL;

UPDATE niche_data.transactions
SET article_id = 'unknown_article'
WHERE article_id IS NULL;

RAISE NOTICE 'Transactions NULL FK values replaced.';

-- 2.2 Articles: price/stock fallback
UPDATE niche_data.articles
SET price = COALESCE(price, sub.avg_price)
FROM (
    SELECT article_id, ROUND(AVG(price)::numeric,2) AS avg_price
    FROM niche_data.transactions
    WHERE price IS NOT NULL AND price > 0
    GROUP BY article_id
) sub
WHERE niche_data.articles.article_id = sub.article_id
  AND (niche_data.articles.price IS NULL OR niche_data.articles.price = 0);

-- final fallback for any remaining
UPDATE niche_data.articles
SET price = 0.01
WHERE price IS NULL OR price = 0;

UPDATE niche_data.articles
SET stock = COALESCE(stock, 0)
WHERE stock IS NULL;

RAISE NOTICE 'Articles price/stock normalized.';

-- 2.3 Customers: active/gender/email/name defaults
UPDATE niche_data.customers
SET active = FALSE
WHERE active IS NULL;

UPDATE niche_data.customers
SET gender = COALESCE(NULLIF(TRIM(gender), ''),'Other')
WHERE gender IS NULL OR TRIM(gender) = '';

-- fill missing first/last/email if any (safe unique emails)
UPDATE niche_data.customers
SET first_name = COALESCE(first_name, 'Customer'),
    last_name = COALESCE(last_name, 'Unknown')
WHERE first_name IS NULL OR last_name IS NULL;

-- ensure emails exist; generate unique temporary emails for nulls/duplicates
-- First set null emails to a generated form
UPDATE niche_data.customers
SET email = LOWER(CONCAT(first_name, '.', last_name, '.', customer_id, '@example.com'))
WHERE email IS NULL OR TRIM(email) = '';


WITH dupes AS (
    SELECT LOWER(email) AS e
    FROM niche_data.customers
    GROUP BY LOWER(email)
    HAVING COUNT(*) > 1
),
cte AS (
    SELECT 
        customer_id,
        ROW_NUMBER() OVER (PARTITION BY LOWER(email) ORDER BY customer_id) AS rn,
        LOWER(email) AS le
    FROM niche_data.customers
    WHERE LOWER(email) IN (SELECT e FROM dupes)
)
UPDATE niche_data.customers t
SET email = CONCAT(
        SPLIT_PART(cte.le, '@', 1), 
        '+', 
        cte.rn::text, 
        '@', 
        SPLIT_PART(cte.le, '@', 2)
    )
FROM cte
WHERE t.customer_id = cte.customer_id
RETURNING t.customer_id;


RAISE NOTICE 'Customers fields normalized (active, gender, names, emails).';



-- 2.4 Orders: payment_status normalization, order_date & total_amount defaults
UPDATE niche_data.orders
SET payment_status = COALESCE(NULLIF(LOWER(payment_status), ''), 'pending')
WHERE payment_status IS NULL OR TRIM(payment_status) = '';

UPDATE niche_data.orders
SET order_date = COALESCE(order_date, NOW())
WHERE order_date IS NULL;

UPDATE niche_data.orders
SET total_amount = COALESCE(total_amount, 0)
WHERE total_amount IS NULL;

RAISE NOTICE 'Orders default values applied.';

-- 2.5 Reviews: rating defaults and text defaults & created_at
UPDATE niche_data.reviews
SET rating = COALESCE(rating, 3)
WHERE rating IS NULL;

UPDATE niche_data.reviews
SET review_text = COALESCE(review_text, '')
WHERE review_text IS NULL;

UPDATE niche_data.reviews
SET created_at = COALESCE(created_at, NOW())
WHERE created_at IS NULL;

RAISE NOTICE 'Reviews normalized.';

--------------------------------------------------------------------------------
-- 3) Drop / recreate foreign keys that need ON DELETE CASCADE or SET NULL
--------------------------------------------------------------------------------

-- Cart & Wishlist: drop existing fk constraints (if exist) then recreate with ON DELETE CASCADE
ALTER TABLE IF EXISTS niche_data.cart DROP CONSTRAINT IF EXISTS cart_customer_id_fkey;
ALTER TABLE IF EXISTS niche_data.cart DROP CONSTRAINT IF EXISTS cart_article_id_fkey;

ALTER TABLE IF EXISTS niche_data.cart
    ADD CONSTRAINT cart_customer_id_fkey
    FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers(customer_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

ALTER TABLE IF EXISTS niche_data.cart
    ADD CONSTRAINT cart_article_id_fkey
    FOREIGN KEY (article_id)
    REFERENCES niche_data.articles(article_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- Wishlist
ALTER TABLE IF EXISTS niche_data.wishlist DROP CONSTRAINT IF EXISTS wishlist_customer_id_fkey;
ALTER TABLE IF EXISTS niche_data.wishlist DROP CONSTRAINT IF EXISTS wishlist_article_id_fkey;

ALTER TABLE IF EXISTS niche_data.wishlist
    ADD CONSTRAINT wishlist_customer_id_fkey
    FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers(customer_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

ALTER TABLE IF EXISTS niche_data.wishlist
    ADD CONSTRAINT wishlist_article_id_fkey
    FOREIGN KEY (article_id)
    REFERENCES niche_data.articles(article_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

RAISE NOTICE 'Cart & wishlist foreign keys recreated with CASCADE.';

--------------------------------------------------------------------------------
-- 4) Add CHECK constraints and safe NOT NULLs (do this AFTER cleaning)
--------------------------------------------------------------------------------

-- 4.1 Reviews.rating between 1 and 5
ALTER TABLE niche_data.reviews
    ADD CONSTRAINT chk_reviews_rating_range CHECK (rating BETWEEN 1 AND 5);

-- 4.2 Orders.payment_status allowed values
ALTER TABLE niche_data.orders
    ADD CONSTRAINT chk_orders_payment_status CHECK (LOWER(payment_status) IN ('pending','paid','failed','refunded'));

-- 4.3 Customers.gender allowed values
ALTER TABLE niche_data.customers
    ADD CONSTRAINT chk_customers_gender CHECK (gender IN ('Male','Female','Other'));

-- 4.4 Categories no self-parent
ALTER TABLE niche_data.categories
    ADD CONSTRAINT chk_categories_no_self_parent CHECK (parent_category_id IS NULL OR parent_category_id <> category_id);

RAISE NOTICE 'Check constraints added.';

--------------------------------------------------------------------------------
-- 5) Make important columns NOT NULL (after ensuring default values)
--------------------------------------------------------------------------------

-- 5.1 Transactions: ensure not null and fks exist
ALTER TABLE niche_data.transactions
    ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE niche_data.transactions
    ALTER COLUMN article_id SET NOT NULL;

-- ensure FK constraints exist and are correct (recreate to enforce ON DELETE SET NULL not desired here)
ALTER TABLE IF EXISTS niche_data.transactions DROP CONSTRAINT IF EXISTS transactions_customer_id_fkey;
ALTER TABLE IF EXISTS niche_data.transactions DROP CONSTRAINT IF EXISTS transactions_article_id_fkey;

ALTER TABLE niche_data.transactions
    ADD CONSTRAINT transactions_customer_id_fkey
    FOREIGN KEY (customer_id) REFERENCES niche_data.customers(customer_id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE niche_data.transactions
    ADD CONSTRAINT transactions_article_id_fkey
    FOREIGN KEY (article_id) REFERENCES niche_data.articles(article_id) ON DELETE SET NULL ON UPDATE CASCADE;

-- 5.2 Articles: critical fields
ALTER TABLE niche_data.articles
    ALTER COLUMN article_id SET NOT NULL;
-- make price and stock NOT NULL (we set defaults earlier)
ALTER TABLE niche_data.articles
    ALTER COLUMN price SET NOT NULL;
ALTER TABLE niche_data.articles
    ALTER COLUMN stock SET NOT NULL;

-- 5.3 Customers: critical fields
ALTER TABLE niche_data.customers
    ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE niche_data.customers
    ALTER COLUMN active SET NOT NULL;
ALTER TABLE niche_data.customers
    ALTER COLUMN email SET NOT NULL;
ALTER TABLE niche_data.customers
    ALTER COLUMN first_name SET NOT NULL;
ALTER TABLE niche_data.customers
    ALTER COLUMN last_name SET NOT NULL;

-- 5.4 Orders: key columns
ALTER TABLE niche_data.orders
    ALTER COLUMN order_id SET NOT NULL;
ALTER TABLE niche_data.orders
    ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE niche_data.orders
    ALTER COLUMN total_amount SET NOT NULL;
ALTER TABLE niche_data.orders
    ALTER COLUMN payment_status SET NOT NULL;

-- 5.5 Reviews: key columns
ALTER TABLE niche_data.reviews
    ALTER COLUMN review_id SET NOT NULL;
ALTER TABLE niche_data.reviews
    ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE niche_data.reviews
    ALTER COLUMN article_id SET NOT NULL;
ALTER TABLE niche_data.reviews
    ALTER COLUMN rating SET NOT NULL;

RAISE NOTICE 'NOT NULL constraints applied (where safe).';

--------------------------------------------------------------------------------
-- 6) Email uniqueness: create case-insensitive unique constraint
--------------------------------------------------------------------------------

-- Fix email duplicates that still might exist by appending suffix numbers
WITH dup AS (
    SELECT LOWER(email) AS le, ARRAY_AGG(customer_id ORDER BY customer_id) AS cids
    FROM niche_data.customers
    GROUP BY LOWER(email)
    HAVING COUNT(*) > 1
),
unnested AS (
    SELECT le, unnest(cids) AS cid, ROW_NUMBER() OVER (PARTITION BY le ORDER BY unnest(cids)) AS rn
    FROM dup
)
UPDATE niche_data.customers c
SET email = CONCAT(
        SPLIT_PART(unnested.le, '@', 1), 
        '+', 
        unnested.rn::text, 
        '@', 
        SPLIT_PART(unnested.le, '@', 2)
    )
FROM unnested
WHERE c.customer_id = unnested.cid
  AND unnested.rn > 1  -- only update the second+ occurrences
RETURNING c.customer_id;


-- now create unique index on lower(email)
CREATE UNIQUE INDEX IF NOT EXISTS ux_customers_email_ci ON niche_data.customers (LOWER(email));

RAISE NOTICE 'Email uniqueness enforced (case-insensitive).';

--------------------------------------------------------------------------------
-- 7) Fix / recreate important foreign keys to recommended behaviors
--------------------------------------------------------------------------------

-- order_items -> article: allow RESTRICT (keep) or SET NULL; choose RESTRICT to preserve historical
ALTER TABLE IF EXISTS niche_data.order_items DROP CONSTRAINT IF EXISTS fk_oi_article;
ALTER TABLE IF EXISTS niche_data.order_items DROP CONSTRAINT IF EXISTS fk_oi_order;

ALTER TABLE niche_data.order_items
    ADD CONSTRAINT fk_oi_article FOREIGN KEY (article_id)
    REFERENCES niche_data.articles(article_id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE niche_data.order_items
    ADD CONSTRAINT fk_oi_order FOREIGN KEY (order_id)
    REFERENCES niche_data.orders(order_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

RAISE NOTICE 'Order_items FKs fixed.';

--------------------------------------------------------------------------------
-- 8) Index cleanup / recreation (drop possibly duplicate indexes then recreate essential ones)
--------------------------------------------------------------------------------

-- Drop indexes that might be duplicates (safe to attempt)
DROP INDEX IF EXISTS idx_events_event_type;
DROP INDEX IF EXISTS idx_events_event_type; -- attempt twice harmless
DROP INDEX IF EXISTS idx_created_at;
DROP INDEX IF EXISTS idx_events_created_at;
DROP INDEX IF EXISTS idx_orders_order_month;
DROP INDEX IF EXISTS idx_articles_category_id;

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

RAISE NOTICE 'Indexes refreshed.';

--------------------------------------------------------------------------------
-- 9) Final data integrity checks: report counts of leftover NULLs in critical columns
--------------------------------------------------------------------------------

SELECT 
  (SELECT COUNT(*) FROM niche_data.transactions WHERE customer_id IS NULL) AS transactions_null_customer,
  (SELECT COUNT(*) FROM niche_data.transactions WHERE article_id IS NULL) AS transactions_null_article,
  (SELECT COUNT(*) FROM niche_data.articles WHERE price IS NULL) AS articles_null_price,
  (SELECT COUNT(*) FROM niche_data.articles WHERE stock IS NULL) AS articles_null_stock,
  (SELECT COUNT(*) FROM niche_data.customers WHERE email IS NULL) AS customers_null_email,
  (SELECT COUNT(*) FROM niche_data.reviews WHERE rating IS NULL) AS reviews_null_rating
\gexec

RAISE NOTICE 'Null-checks executed (see previous SELECT results).';

--------------------------------------------------------------------------------
-- 10) Commit
--------------------------------------------------------------------------------
COMMIT;

RAISE NOTICE '=== SCHEMA FIX SCRIPT COMPLETE ===';

-- quick verification samples
SELECT table_name, column_name, is_nullable
FROM information_schema.columns
WHERE table_schema = 'niche_data'
  AND column_name IN ('email','price','stock','customer_id','article_id','rating','active')
ORDER BY table_name;

-- sample top customers by loyalty
SELECT customer_id, loyalty_score FROM niche_data.customers ORDER BY loyalty_score DESC LIMIT 10;

