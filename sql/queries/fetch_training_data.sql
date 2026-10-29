SELECT
    o.order_date,
    oi.product_id,
    oi.warehouse_id,
    oi.quantity,
    i.stock_quantity
    FROM order_items AS oi
    INNER JOIN `orders` AS o ON oi.order_id = o.order_id
    INNER JOIN inventory AS i ON oi.product_id = i.product_id AND oi.warehouse_id = i.warehouse_id
    WHERE o.order_date >=(
        SELECT DATE_SUB(MAX(order_date), INTERVAL :weeks_back WEEK)
        FROM `orders`)
    ORDER BY
    o.order_date ASC;