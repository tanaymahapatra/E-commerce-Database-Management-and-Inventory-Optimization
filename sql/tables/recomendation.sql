CREATE TABLE recommendation (
    product_id INT,

    warehouse_id INT,

    predicted_demand DECIMAL(12,2) NOT NULL
        CHECK (predicted_demand >= 0),

    safety_stock INT NOT NULL
        CHECK (safety_stock >= 0),

    reorder_qty INT NOT NULL
        CHECK (reorder_qty >= 0),

    status VARCHAR(30) NOT NULL
        CHECK (status IN ('OK', 'REORDER_NOW', 'CRITICAL')),

    PRIMARY KEY (product_id, warehouse_id),

    CONSTRAINT fk_recommendation_product
        FOREIGN KEY (product_id)
        REFERENCES product(product_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT fk_recommendation_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouse(warehouse_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE
);