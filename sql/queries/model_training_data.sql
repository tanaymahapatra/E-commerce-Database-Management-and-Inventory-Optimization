SELECT o.order_date,oi.order_id,oi.product_id,p.product_name,oi.warehouse_id,i.inventory_id,oi.quantity
    FROM order_items AS oi
    INNER JOIN `orders` AS o ON oi.order_id = o.order_id
    INNER JOIN product AS p ON oi.product_id = p.product_id 
    INNER JOIN warehouse AS w ON oi.warehouse_id = w.warehouse_id
    INNER JOIN inventory AS i ON oi.product_id = i.product_id AND oi.warehouse_id = i.warehouse_id
    ORDER BY o.order_date,oi.warehouse_id,oi.product_id;