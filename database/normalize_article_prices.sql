-- Normalize legacy H&M-style decimal prices into natural LAYR rupee prices.
-- Example mapping: 0.04 -> Rs 3,990, 0.05 -> Rs 4,990.
-- Idempotent guard: once prices are normalized, they are above 100 and skipped.

UPDATE niche_data.articles
SET price = GREATEST(
  990,
  ROUND((price * 100000) / 100) * 100 - 10
)
WHERE price > 0
  AND price < 100;
