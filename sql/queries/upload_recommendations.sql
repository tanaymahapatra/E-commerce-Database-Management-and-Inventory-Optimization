INSERT INTO recommendation (
    product_id,
    warehouse_id,
    forecast_date,
    predicted_demand,
    safety_stock,
    reorder_qty,
    status
)
VALUES (
    :product_id,
    :warehouse_id,
    :forecast_date,
    :predicted_demand,
    :safety_stock,
    :reorder_qty,
    :status
)
ON DUPLICATE KEY UPDATE
    predicted_demand = VALUES(predicted_demand),
    safety_stock = VALUES(safety_stock),
    reorder_qty = VALUES(reorder_qty),
    status = VALUES(status);