CREATE TABLE prediction_log (
    prediction_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,

    predicted_demand DECIMAL(12,2) NOT NULL,
    safety_stock INT NOT NULL,
    reorder_qty INT NOT NULL,
    status VARCHAR(30) NOT NULL,

    prediction_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_product
        FOREIGN KEY (product_id)
        REFERENCES product(product_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT fk_history_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouse(warehouse_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT chk_history_demand
        CHECK (predicted_demand >= 0),

    CONSTRAINT chk_history_safety_stock
        CHECK (safety_stock >= 0),

    CONSTRAINT chk_history_reorder_qty
        CHECK (reorder_qty >= 0),

    CONSTRAINT chk_history_status
        CHECK (status IN ('OK', 'REORDER_NOW', 'CRITICAL'))
);