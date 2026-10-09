CREATE TABLE order_items (
    order_id VARCHAR(20),

    product_id INT,

    warehouse_id INT,

    quantity INT NOT NULL
        CHECK (quantity > 0),

    discount_percent INT
        CHECK (discount_percent BETWEEN 0 AND 100),

    total_price_usd DECIMAL(12,2)
        CHECK (total_price_usd >= 0),

    cost_usd DECIMAL(12,2)
        CHECK (cost_usd >= 0),

    profit_usd DECIMAL(12,2),

    tax_usd DECIMAL(12,2)
        CHECK (tax_usd >= 0),

    PRIMARY KEY (order_id, product_id, warehouse_id),

    CONSTRAINT fk_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT fk_items_product
        FOREIGN KEY (product_id)
        REFERENCES product(product_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT fk_items_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouse(warehouse_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE

);