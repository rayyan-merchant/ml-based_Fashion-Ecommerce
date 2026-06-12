CREATE SCHEMA IF NOT EXISTS public
    AUTHORIZATION pg_database_owner;

BEGIN;


CREATE TABLE IF NOT EXISTS public.articles
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
    price numeric(10, 2),
    stock integer DEFAULT 0,
    category_id integer,
    created_at timestamp with time zone DEFAULT now(),
    last_updated timestamp with time zone DEFAULT now(),
    CONSTRAINT articles_pkey PRIMARY KEY (article_id)
);

CREATE TABLE IF NOT EXISTS public.categories
(
    category_id serial NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    parent_category_id integer,
    CONSTRAINT categories_pkey PRIMARY KEY (category_id)
);

CREATE TABLE IF NOT EXISTS public.customers
(
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    age integer,
    postal_code character varying(70) COLLATE pg_catalog."default",
    club_member_status character varying(50) COLLATE pg_catalog."default",
    fashion_news_frequency character varying(50) COLLATE pg_catalog."default",
    active boolean DEFAULT true,
    first_name text COLLATE pg_catalog."default",
    last_name text COLLATE pg_catalog."default",
    email text COLLATE pg_catalog."default",
    signup_date timestamp with time zone DEFAULT now(),
    CONSTRAINT customers_pkey PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS public.events
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

CREATE TABLE IF NOT EXISTS public.order_items
(
    order_item_id serial NOT NULL,
    order_id integer NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(10, 2) NOT NULL,
    line_total numeric(12, 2) GENERATED ALWAYS AS (((quantity)::numeric * unit_price)) STORED,
    CONSTRAINT order_items_pkey PRIMARY KEY (order_item_id)
);

CREATE TABLE IF NOT EXISTS public.orders
(
    order_id serial NOT NULL,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    order_date timestamp with time zone DEFAULT now(),
    total_amount numeric(12, 2) DEFAULT 0,
    payment_status text COLLATE pg_catalog."default" DEFAULT 'pending'::text,
    shipping_address text COLLATE pg_catalog."default",
    CONSTRAINT orders_pkey PRIMARY KEY (order_id)
);

CREATE TABLE IF NOT EXISTS public.reviews
(
    review_id serial NOT NULL,
    customer_id character varying COLLATE pg_catalog."default" NOT NULL,
    article_id character varying COLLATE pg_catalog."default" NOT NULL,
    rating smallint,
    review_text text COLLATE pg_catalog."default",
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT reviews_pkey PRIMARY KEY (review_id)
);

CREATE TABLE IF NOT EXISTS public.transactions
(
    transaction_id serial NOT NULL,
    t_dat date,
    customer_id character varying COLLATE pg_catalog."default",
    article_id character varying COLLATE pg_catalog."default",
    price numeric(10, 2),
    sales_channel_id integer,
    CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id)
);

ALTER TABLE IF EXISTS public.articles
    ADD CONSTRAINT fk_articles_category FOREIGN KEY (category_id)
    REFERENCES public.categories (category_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_articles_category_id
    ON public.articles(category_id);


ALTER TABLE IF EXISTS public.categories
    ADD CONSTRAINT fk_parent_category FOREIGN KEY (parent_category_id)
    REFERENCES public.categories (category_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS public.events
    ADD CONSTRAINT fk_events_article FOREIGN KEY (article_id)
    REFERENCES public.articles (article_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS public.events
    ADD CONSTRAINT fk_events_customer FOREIGN KEY (customer_id)
    REFERENCES public.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS public.order_items
    ADD CONSTRAINT fk_oi_article FOREIGN KEY (article_id)
    REFERENCES public.articles (article_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS idx_order_items_article
    ON public.order_items(article_id);


ALTER TABLE IF EXISTS public.order_items
    ADD CONSTRAINT fk_oi_order FOREIGN KEY (order_id)
    REFERENCES public.orders (order_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS public.orders
    ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
    REFERENCES public.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS public.reviews
    ADD CONSTRAINT fk_review_article FOREIGN KEY (article_id)
    REFERENCES public.articles (article_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS public.reviews
    ADD CONSTRAINT fk_review_customer FOREIGN KEY (customer_id)
    REFERENCES public.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS public.transactions
    ADD CONSTRAINT transactions_article_id_fkey FOREIGN KEY (article_id)
    REFERENCES public.articles (article_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS public.transactions
    ADD CONSTRAINT transactions_customer_id_fkey FOREIGN KEY (customer_id)
    REFERENCES public.customers (customer_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

END;