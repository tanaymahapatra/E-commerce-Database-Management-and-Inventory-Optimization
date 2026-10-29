-- ============================================================
-- Fetch rolling training window for the ML pipeline.
-- :weeks_back -> how many weeks of history to pull (e.g. 52)
--
-- Dynamically finds the latest available order date in the database:
--   MAX(order_date)
-- and pulls the 52 weeks prior to that date.
--
-- This works seamlessly for BOTH:
--   1. Historical / static dataset (uses latest date in DB)
--   2. Live running data (as new orders arrive, MAX(order_date) is today)
-- ============================================================

SELECT
    o.order_date,
    oi.product_id,
    oi.warehouse_id,
    oi.quantity,
    i.stock_quantity
FROM order_items AS oi
INNER JOIN `orders`    AS o  ON oi.order_id    = o.order_id
INNER JOIN inventory   AS i  ON oi.product_id  = i.product_id
                             AND oi.warehouse_id = i.warehouse_id
WHERE
    o.order_date >= (
        SELECT DATE_SUB(MAX(order_date), INTERVAL :weeks_back WEEK)
        FROM `orders`
    )
ORDER BY
    o.order_date ASC;
