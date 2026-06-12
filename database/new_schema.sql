
CREATE SCHEMA IF NOT EXISTS niche_data
    AUTHORIZATION postgres;

BEGIN;


CREATE TABLE IF NOT EXISTS niche_data.articles
(
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    product_code integer,
    prod_name text COLLATE pg_catalog."default",
    product_type_name text COLLATE pg_catalog."default",
    product_group_name text COLLATE pg_catalog."default",
    graphical_appearance_name text COLLATE pg_catalog."default",
    colour_group_name text COLLATE pg_catalog."default",
    department_no integer,
    department_name text COLLATE pg_catalog."default",
    index_name text COLLATE pg_catalog."default",
    index_group_name text COLLATE pg_catalog."default",
    section_name text COLLATE pg_catalog."default",
    garment_group_name text COLLATE pg_catalog."default",
    detail_desc text COLLATE pg_catalog."default",
    price numeric(10, 2) NOT NULL,
    stock integer NOT NULL,
    category_id integer,
    image_path text COLLATE pg_catalog."default",
    created_at timestamp with time zone,
    last_updated timestamp with time zone,
    CONSTRAINT articles_pkey PRIMARY KEY (article_id)
);

CREATE TABLE IF NOT EXISTS niche_data.cart
(
    cart_id serial NOT NULL,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    quantity integer NOT NULL DEFAULT 1,
    added_at timestamp without time zone DEFAULT now(),
    CONSTRAINT cart_pkey PRIMARY KEY (cart_id),
    CONSTRAINT cart_customer_id_article_id_key UNIQUE (customer_id, article_id)
);

CREATE TABLE IF NOT EXISTS niche_data.categories
(
    category_id serial NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    parent_category_id integer,
    CONSTRAINT categories_pkey PRIMARY KEY (category_id)
);

CREATE TABLE IF NOT EXISTS niche_data.customers
(
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    age integer,
    postal_code character varying(70) COLLATE pg_catalog."default",
    club_member_status character varying(50) COLLATE pg_catalog."default",
    fashion_news_frequency character varying(50) COLLATE pg_catalog."default",
    active boolean NOT NULL,
    first_name text COLLATE pg_catalog."default" NOT NULL,
    last_name text COLLATE pg_catalog."default" NOT NULL,
    email text COLLATE pg_catalog."default" NOT NULL,
    signup_date timestamp with time zone,
    gender character varying(10) COLLATE pg_catalog."default",
    loyalty_score numeric DEFAULT 0,
    CONSTRAINT customers_pkey PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS niche_data.events
(
    event_id serial NOT NULL,
    session_id text COLLATE pg_catalog."default",
    customer_id character varying COLLATE pg_catalog."default",
    article_id character varying COLLATE pg_catalog."default",
    event_type text COLLATE pg_catalog."default",
    campaign_id integer,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT events_pkey PRIMARY KEY (event_id)
);

CREATE TABLE IF NOT EXISTS niche_data.order_items
(
    order_item_id serial NOT NULL,
    order_id integer NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(10, 2) NOT NULL,
    line_total numeric(12, 2) GENERATED ALWAYS AS (((quantity)::numeric * unit_price)) STORED,
    CONSTRAINT order_items_pkey PRIMARY KEY (order_item_id)
);

CREATE TABLE IF NOT EXISTS niche_data.orders
(
    order_id serial NOT NULL,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    order_date timestamp with time zone DEFAULT now(),
    total_amount numeric(12, 2) NOT NULL DEFAULT 0,
    payment_status text COLLATE pg_catalog."default" NOT NULL DEFAULT 'pending'::text,
    shipping_address text COLLATE pg_catalog."default",
    CONSTRAINT orders_pkey PRIMARY KEY (order_id)
);

CREATE TABLE IF NOT EXISTS niche_data.reviews
(
    review_id serial NOT NULL,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    rating smallint NOT NULL,
    review_text text COLLATE pg_catalog."default",
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT reviews_pkey PRIMARY KEY (review_id)
);

CREATE TABLE IF NOT EXISTS niche_data.transactions
(
    transaction_id integer NOT NULL,
    t_dat date,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    price numeric(10, 2),
    sales_channel_id integer,
    CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id)
);

CREATE TABLE IF NOT EXISTS niche_data.wishlist
(
    wishlist_id serial NOT NULL,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    added_at timestamp without time zone DEFAULT now(),
    CONSTRAINT wishlist_pkey PRIMARY KEY (wishlist_id),
    CONSTRAINT wishlist_customer_id_article_id_key UNIQUE (customer_id, article_id)
);

ALTER TABLE IF EXISTS niche_data.articles
    ADD CONSTRAINT fk_articles_category FOREIGN KEY (category_id)
    REFERENCES niche_data.categories (category_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_articles_category_id
    ON niche_data.articles(category_id);


ALTER TABLE IF EXISTS niche_data.cart
    ADD CONSTRAINT cart_article_id_fkey FOREIGN KEY (article_id)
    REFERENCES niche_data.articles (article_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_cart_article_id
    ON niche_data.cart(article_id);


ALTER TABLE IF EXISTS niche_data.cart
    ADD CONSTRAINT cart_customer_id_fkey FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers (customer_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_cart_customer_id
    ON niche_data.cart(customer_id);


ALTER TABLE IF EXISTS niche_data.categories
    ADD CONSTRAINT fk_parent_category FOREIGN KEY (parent_category_id)
    REFERENCES niche_data.categories (category_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_categories_parent_id
    ON niche_data.categories(parent_category_id);


ALTER TABLE IF EXISTS niche_data.events
    ADD CONSTRAINT fk_events_article FOREIGN KEY (article_id)
    REFERENCES niche_data.articles (article_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_events_article
    ON niche_data.events(article_id);


ALTER TABLE IF EXISTS niche_data.events
    ADD CONSTRAINT fk_events_customer FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_events_customer
    ON niche_data.events(customer_id);


ALTER TABLE IF EXISTS niche_data.order_items
    ADD CONSTRAINT fk_oi_article FOREIGN KEY (article_id)
    REFERENCES niche_data.articles (article_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS order_items_article_id_idx
    ON niche_data.order_items(article_id);


ALTER TABLE IF EXISTS niche_data.order_items
    ADD CONSTRAINT fk_oi_order FOREIGN KEY (order_id)
    REFERENCES niche_data.orders (order_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_order_items_order_id
    ON niche_data.order_items(order_id);


ALTER TABLE IF EXISTS niche_data.orders
    ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON niche_data.orders(customer_id);


ALTER TABLE IF EXISTS niche_data.reviews
    ADD CONSTRAINT fk_review_article FOREIGN KEY (article_id)
    REFERENCES niche_data.articles (article_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_reviews_article_id
    ON niche_data.reviews(article_id);


ALTER TABLE IF EXISTS niche_data.reviews
    ADD CONSTRAINT fk_review_customer FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_reviews_customer_id
    ON niche_data.reviews(customer_id);


ALTER TABLE IF EXISTS niche_data.transactions
    ADD CONSTRAINT transactions_article_id_fkey FOREIGN KEY (article_id)
    REFERENCES niche_data.articles (article_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_article_id
    ON niche_data.transactions(article_id);


ALTER TABLE IF EXISTS niche_data.transactions
    ADD CONSTRAINT transactions_customer_id_fkey FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers (customer_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id
    ON niche_data.transactions(customer_id);


ALTER TABLE IF EXISTS niche_data.wishlist
    ADD CONSTRAINT wishlist_article_id_fkey FOREIGN KEY (article_id)
    REFERENCES niche_data.articles (article_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_wishlist_article_id
    ON niche_data.wishlist(article_id);


ALTER TABLE IF EXISTS niche_data.wishlist
    ADD CONSTRAINT wishlist_customer_id_fkey FOREIGN KEY (customer_id)
    REFERENCES niche_data.customers (customer_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_wishlist_customer_id
    ON niche_data.wishlist(customer_id);


CREATE TABLE IF NOT EXISTS niche_data.admins (
    admin_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO niche_data.admins (username, email, password_hash)
VALUES
    ('rayyan', 'rayyan@example.com', crypt('admin123', gen_salt('bf'))),
    ('riya', 'riya@example.com', crypt('admin123', gen_salt('bf'))),
    ('rija', 'rija@example.com', crypt('admin123', gen_salt('bf'))),
    ('ukkashah', 'ukkashah@example.com', crypt('admin123', gen_salt('bf')));


CREATE TABLE niche_data.admin_activity_log (
    log_id SERIAL PRIMARY KEY,
    admin_id INT REFERENCES niche_data.admins(admin_id),
    action TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);


TRUNCATE TABLE niche_data.customers

ALTER TABLE niche_data.customers
ADD COLUMN password_hash TEXT,
ADD COLUMN phone TEXT,
ADD COLUMN address TEXT;

ALTER TABLE niche_data.customers
ALTER COLUMN password_hash SET NOT NULL;


ALTER TABLE niche_data.events
ADD COLUMN order_id INTEGER;


END;
