ALTER TABLE niche_data.articles
ADD COLUMN image_path TEXT;


CREATE TABLE niche_data.ProductImagesTemp (
    article_id VARCHAR(20),
    image_path TEXT
);

select * from niche_data.ProductImagesTemp
select * from niche_data.articles

UPDATE niche_data.articles a
SET image_path = i.image_path
FROM niche_data.ProductImagesTemp i
WHERE ltrim(a.article_id::text, '0') = ltrim(i.article_id::text, '0');





TRUNCATE TABLE niche_data.reviews RESTART IDENTITY CASCADE;

ALTER TABLE niche_data.reviews
    ADD COLUMN IF NOT EXISTS verified_purchase BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS helpful_votes INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20),
    ADD COLUMN IF NOT EXISTS aspect_terms JSONB,
    ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en',
    ADD COLUMN IF NOT EXISTS review_length INT,
    ADD COLUMN IF NOT EXISTS review_source VARCHAR(20) DEFAULT 'web';


select article_id, count(*) from niche_data.reviews
group by article_id

select article_id, count(*) from niche_data.transactions
group by article_id

select * from niche_data.articles

select count(*) from niche_data.reviews
where verified_purchase = TRUE

select * from niche_data.reviews

select article_id, rating, count(*)
from niche_data.reviews
group by article_id, rating


select language, count(*) 
from niche_data.reviews
group by language



