SELECT forecast_date,predicted_demand,safety_stock,reorder_qty,status
    FROM recommendation
    WHERE product_id = :product_id AND warehouse_id = :warehouse_id
    ORDER BY forecast_date ASC